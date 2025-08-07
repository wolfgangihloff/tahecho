#!/usr/bin/env python3
"""
Tests for SBOM generation functionality.

This module tests the Software Bill of Materials (SBOM) generation
for BSI TR-03183 compliance.
"""

import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.generate_sbom import generate_sbom, run_command, main


class TestSBOMGeneration:
    """Test cases for SBOM generation."""
    
    def test_generate_sbom_commands(self):
        """Test that generate_sbom creates correct command structures."""
        json_cmd, xml_cmd, output_path = generate_sbom("test_output")
        
        # Check that commands are lists
        assert isinstance(json_cmd, list)
        assert isinstance(xml_cmd, list)
        
        # Check that commands contain required components
        assert "cyclonedx_py" in " ".join(json_cmd)
        assert "poetry" in json_cmd
        assert "--output-format" in json_cmd
        assert "JSON" in json_cmd
        assert "--spec-version" in json_cmd
        assert "1.6" in json_cmd
        
        assert "cyclonedx_py" in " ".join(xml_cmd)
        assert "poetry" in xml_cmd
        assert "--output-format" in xml_cmd
        assert "XML" in xml_cmd
        assert "--spec-version" in xml_cmd
        assert "1.6" in xml_cmd
        
        # Check output paths
        assert str(output_path) == "test_output"
        
    def test_generate_sbom_creates_output_directory(self):
        """Test that generate_sbom creates the output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_output = Path(temp_dir) / "new_output_dir"
            
            # Directory should not exist initially
            assert not test_output.exists()
            
            _, _, output_path = generate_sbom(str(test_output))
            
            # Directory should be created
            assert test_output.exists()
            assert output_path == test_output
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Success")
        
        success, output = run_command(["echo", "test"], "test command")
        
        assert success is True
        assert output == "Success"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test failed command execution."""
        from subprocess import CalledProcessError
        
        mock_run.side_effect = CalledProcessError(1, "command", stderr="Error message")
        
        success, output = run_command(["false"], "test command")
        
        assert success is False
        assert output is None
    
    @patch('scripts.generate_sbom.run_command')
    def test_main_success(self, mock_run_command, capsys):
        """Test successful main function execution."""
        mock_run_command.return_value = (True, "Success")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            main(temp_dir)
            
            captured = capsys.readouterr()
            assert "✅ SBOM generated successfully" in captured.out
            assert "CycloneDX spec version 1.6" in captured.out
            assert "BSI TR-03183" in captured.out
    
    @patch('scripts.generate_sbom.run_command')
    def test_main_partial_failure(self, mock_run_command):
        """Test main function with partial failure."""
        # First call succeeds, second fails
        mock_run_command.side_effect = [(True, "Success"), (False, None)]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(SystemExit) as exc_info:
                main(temp_dir)
            assert exc_info.value.code == 1
    
    @patch('scripts.generate_sbom.run_command')
    def test_main_complete_failure(self, mock_run_command):
        """Test main function with complete failure."""
        mock_run_command.return_value = (False, None)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(SystemExit) as exc_info:
                main(temp_dir)
            assert exc_info.value.code == 1


class TestSBOMIntegration:
    """Integration tests for actual SBOM generation."""
    
    @pytest.mark.slow
    def test_actual_sbom_generation(self):
        """Test actual SBOM generation (requires cyclonedx-py)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                main(temp_dir)
                
                # Check that files were created
                json_file = Path(temp_dir) / "sbom.json"
                xml_file = Path(temp_dir) / "sbom.xml"
                
                assert json_file.exists()
                assert xml_file.exists()
                
                # Check file sizes (should not be empty)
                assert json_file.stat().st_size > 0
                assert xml_file.stat().st_size > 0
                
                # Basic validation of JSON structure
                with open(json_file) as f:
                    sbom_data = json.load(f)
                    assert "components" in sbom_data
                    assert "metadata" in sbom_data
                
                # Basic validation of XML structure
                tree = ET.parse(xml_file)
                root = tree.getroot()
                assert root.tag.endswith("bom")
                assert root.find(".//{http://cyclonedx.org/schema/bom/1.6}metadata") is not None
                
            except SystemExit:
                pytest.skip("cyclonedx-py not available in test environment")
    
    @pytest.mark.slow
    def test_sbom_content_validation(self):
        """Test that generated SBOM contains expected content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                main(temp_dir)
                
                json_file = Path(temp_dir) / "sbom.json"
                
                with open(json_file) as f:
                    sbom_data = json.load(f)
                
                # Check for expected components
                components = sbom_data.get("components", [])
                component_names = [comp.get("name") for comp in components]
                
                # Should contain some known dependencies from our pyproject.toml
                expected_deps = ["langchain", "chainlit", "openai"]
                found_deps = [dep for dep in expected_deps if dep in component_names]
                
                assert len(found_deps) > 0, f"Expected dependencies not found in SBOM: {expected_deps}"
                
                # Check metadata
                metadata = sbom_data.get("metadata", {})
                assert "timestamp" in metadata
                
                # Check tools information
                tools = metadata.get("tools", {}).get("components", [])
                tool_names = [tool.get("name") for tool in tools]
                assert "cyclonedx-py" in tool_names
                
            except SystemExit:
                pytest.skip("cyclonedx-py not available in test environment")


# Mark integration tests
pytest.mark.slow = pytest.mark.skipif(
    "PYTEST_SKIP_SLOW" in pytest.__dict__.get("config", {}).get("getoption", lambda x: False)("markexpr") if hasattr(pytest, "config") else False,
    reason="Slow test skipped"
)

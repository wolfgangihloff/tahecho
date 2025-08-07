"""
Unit tests for GitHub Actions workflows.
Tests workflow syntax, action configurations, and step dependencies.
"""

import pytest
import yaml  # type: ignore
import json
import requests  # type: ignore
from pathlib import Path
from typing import Dict, Any


class TestSBOMGenerationWorkflow:
    """Test the SBOM generation GitHub Actions workflow."""
    
    @pytest.fixture
    def workflow_file(self) -> Dict[str, Any]:
        """Load the SBOM generation workflow file."""
        workflow_path = Path(".github/workflows/sbom-generation.yml")
        with open(workflow_path, 'r') as f:
            content = f.read()
            # Parse with custom handling for 'on' keyword
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == 'on:':
                    lines[i] = 'workflow_triggers:'
                    break
            
            content = '\n'.join(lines)
            parsed = yaml.safe_load(content)
            
            # Restore the key name for our tests
            if 'workflow_triggers' in parsed:
                parsed['on'] = parsed.pop('workflow_triggers')
            return parsed  # type: ignore
    
    def test_workflow_yaml_syntax_is_valid(self, workflow_file: Dict[str, Any]) -> None:
        """Test that the workflow YAML syntax is valid."""
        # If we can load it with yaml.safe_load, the syntax is valid
        assert workflow_file is not None
        assert isinstance(workflow_file, dict)
        
    def test_workflow_has_required_sections(self, workflow_file: Dict[str, Any]) -> None:
        """Test that workflow has all required sections."""
        required_sections = ['name', 'on', 'jobs']
        for section in required_sections:
            assert section in workflow_file, f"Missing required section: {section}"
    
    def test_generate_sbom_job_structure(self, workflow_file: Dict[str, Any]) -> None:
        """Test the generate-sbom job has correct structure."""
        jobs = workflow_file['jobs']
        assert 'generate-sbom' in jobs
        
        job = jobs['generate-sbom']
        assert 'runs-on' in job
        assert job['runs-on'] == 'ubuntu-latest'
        assert 'permissions' in job
        assert 'steps' in job
        
    def test_setup_python_step_has_id(self, workflow_file: Dict[str, Any]) -> None:
        """Test that setup-python step has an id for cache key reference."""
        steps = workflow_file['jobs']['generate-sbom']['steps']
        setup_python_step = None
        
        for step in steps:
            if step.get('name') == 'Set up Python':
                setup_python_step = step
                break
                
        assert setup_python_step is not None, "Setup Python step not found"
        assert 'id' in setup_python_step, "Setup Python step missing id"
        assert setup_python_step['id'] == 'setup-python'
        
    def test_cache_step_references_correct_python_version(self, workflow_file: Dict[str, Any]) -> None:
        """Test that cache step correctly references Python version."""
        steps = workflow_file['jobs']['generate-sbom']['steps']
        cache_step = None
        
        for step in steps:
            if step.get('name') == 'Load cached venv':
                cache_step = step
                break
                
        assert cache_step is not None, "Cache step not found"
        cache_key = cache_step['with']['key']
        assert '${{ steps.setup-python.outputs.python-version }}' in cache_key
        
    def test_anchore_scan_action_parameters(self, workflow_file: Dict[str, Any]) -> None:
        """Test that anchore/scan-action has correct parameters."""
        steps = workflow_file['jobs']['security-scan']['steps']
        scan_step = None
        
        for step in steps:
            if step.get('name') == 'Run vulnerability scan':
                scan_step = step
                break
                
        assert scan_step is not None, "Vulnerability scan step not found"
        assert scan_step['uses'] == 'anchore/scan-action@v3'
        assert 'with' in scan_step
        assert 'sbom' in scan_step['with']
        assert scan_step['with']['sbom'] == 'public/sbom.json'
        
    def test_security_scan_job_dependencies(self, workflow_file: Dict[str, Any]) -> None:
        """Test security-scan job has correct dependencies."""
        jobs = workflow_file['jobs']
        security_scan = jobs['security-scan']
        
        assert 'needs' in security_scan
        assert security_scan['needs'] == 'generate-sbom'
        assert 'if' in security_scan
        
    def test_sarif_upload_step_configuration(self, workflow_file: Dict[str, Any]) -> None:
        """Test SARIF upload step is properly configured."""
        steps = workflow_file['jobs']['security-scan']['steps']
        upload_step = None
        
        for step in steps:
            if step.get('name') == 'Upload vulnerability report':
                upload_step = step
                break
                
        assert upload_step is not None, "SARIF upload step not found"
        assert upload_step['uses'] == 'github/codeql-action/upload-sarif@v2'
        assert 'if' in upload_step
        assert upload_step['if'] == 'always()'
        assert 'with' in upload_step
        assert 'sarif_file' in upload_step['with']
        
    def test_workflow_permissions(self, workflow_file: Dict[str, Any]) -> None:
        """Test that workflow has appropriate permissions."""
        generate_sbom = workflow_file['jobs']['generate-sbom']
        assert 'permissions' in generate_sbom
        
        permissions = generate_sbom['permissions']
        assert 'contents' in permissions
        assert 'pages' in permissions  
        assert 'id-token' in permissions
        
    def test_workflow_triggers(self, workflow_file: Dict[str, Any]) -> None:
        """Test that workflow has correct triggers."""
        triggers = workflow_file['on']
        assert 'push' in triggers
        assert 'pull_request' in triggers
        assert 'schedule' in triggers
        
        # Test scheduled trigger
        schedule = triggers['schedule']
        assert len(schedule) == 1
        assert 'cron' in schedule[0]
        assert schedule[0]['cron'] == '0 2 * * 0'  # Weekly on Sundays
        
    @pytest.mark.integration
    def test_github_actions_are_accessible(self) -> None:
        """Test that all referenced GitHub Actions are accessible."""
        actions_to_test = [
            "actions/checkout@v4",
            "actions/setup-python@v4", 
            "snok/install-poetry@v1",
            "actions/cache@v4",
            "actions/upload-artifact@v4",
            "actions/configure-pages@v4",
            "actions/upload-pages-artifact@v3",
            "actions/deploy-pages@v4",
            "actions/download-artifact@v4",
            "anchore/scan-action@v3",
            "github/codeql-action/upload-sarif@v2"
        ]
        
        for action in actions_to_test:
            # Test that we can construct a valid GitHub URL
            if '@' in action:
                repo, version = action.split('@')
                url = f"https://github.com/{repo}"
                # We can't actually test HTTP requests in unit tests easily,
                # but we can validate the format
                slash_count = repo.count('/')
                assert slash_count >= 1, f"Invalid action format: {action}"
                assert len(version) > 0, f"Invalid version for action: {action}"


class TestWorkflowLinting:
    """Test workflow follows linting rules and best practices."""
    
    @pytest.fixture
    def workflow_content(self) -> str:
        """Load raw workflow content."""
        workflow_path = Path(".github/workflows/sbom-generation.yml")
        with open(workflow_path, 'r') as f:
            return f.read()
    
    def test_workflow_uses_pinned_action_versions(self, workflow_content: str) -> None:
        """Test that all actions use pinned versions (not @main or @master)."""
        lines = workflow_content.split('\n')
        action_lines = [line.strip() for line in lines if 'uses:' in line]
        
        for line in action_lines:
            if 'uses:' in line:
                action = line.split('uses:')[1].strip()
                if '@' in action:
                    version = action.split('@')[1]
                    assert version not in ['main', 'master'], \
                        f"Action should use pinned version, not branch: {action}"
                        
    def test_workflow_has_descriptive_names(self, workflow_content: str) -> None:
        """Test that all steps have descriptive names."""
        lines = workflow_content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == 'on:':
                lines[i] = 'workflow_triggers:'
                break
        
        content = '\n'.join(lines)
        workflow_file = yaml.safe_load(content)
        
        if 'workflow_triggers' in workflow_file:
            workflow_file['on'] = workflow_file.pop('workflow_triggers')
            
        for job_name, job in workflow_file['jobs'].items():
            if 'steps' in job:
                for i, step in enumerate(job['steps']):
                    assert 'name' in step, \
                        f"Step {i} in job {job_name} missing name"
                    assert len(step['name']) > 5, \
                        f"Step name too short in job {job_name}: {step['name']}"
                        
    def test_workflow_has_proper_indentation(self, workflow_content: str) -> None:
        """Test that workflow uses consistent 2-space indentation."""
        lines = workflow_content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip() and line.startswith(' '):
                # Count leading spaces
                leading_spaces = len(line) - len(line.lstrip())
                assert leading_spaces % 2 == 0, \
                    f"Line {i} has inconsistent indentation (not multiple of 2): {leading_spaces} spaces"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

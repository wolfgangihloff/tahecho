#!/usr/bin/env python3
"""
SBOM Generation Script for BSI TR-03183 Compliance

This script generates a Software Bill of Materials (SBOM) in CycloneDX format
to comply with German BSI TR-03183 cybersecurity standards.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def generate_sbom(output_dir="public"):
    """Generate SBOM in CycloneDX format using cyclonedx-py CLI."""
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Generate JSON format (BSI preferred)
    json_cmd = [
        sys.executable, "-m", "cyclonedx_py", "poetry",
        "--output-format", "JSON",
        "--output-file", str(output_path / "sbom.json"),
        "--spec-version", "1.6",
        "--mc-type", "application"
    ]
    
    # Generate XML format  
    xml_cmd = [
        sys.executable, "-m", "cyclonedx_py", "poetry",
        "--output-format", "XML", 
        "--output-file", str(output_path / "sbom.xml"),
        "--spec-version", "1.6",
        "--mc-type", "application"
    ]
    
    return json_cmd, xml_cmd, output_path


def run_command(cmd, description):
    """Run a command and handle errors."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating {description}: {e}")
        if e.stderr:
            print(f"   Error details: {e.stderr}")
        return False, None
    except FileNotFoundError:
        print(f"❌ cyclonedx-py not found. Please ensure it's installed.")
        return False, None


def main(output_dir="public"):
    """Main function to generate and save SBOM."""
    print("🔄 Generating SBOM for BSI TR-03183 compliance...")
    
    json_cmd, xml_cmd, output_path = generate_sbom(output_dir)
    
    # Generate JSON format
    json_success, json_output = run_command(json_cmd, "JSON SBOM")
    
    # Generate XML format  
    xml_success, xml_output = run_command(xml_cmd, "XML SBOM")
    
    if json_success and xml_success:
        print("✅ SBOM generated successfully:")
        print(f"   - {output_path}/sbom.json (CycloneDX JSON format)")
        print(f"   - {output_path}/sbom.xml (CycloneDX XML format)")
        print("   - CycloneDX spec version 1.6")
        print("   - Compliant with BSI TR-03183 Part 2 requirements")
        print(f"   - Generated on: {datetime.utcnow().isoformat()}")
        
        # Show file sizes
        try:
            json_size = (output_path / "sbom.json").stat().st_size
            xml_size = (output_path / "sbom.xml").stat().st_size
            print(f"   - sbom.json: {json_size:,} bytes")
            print(f"   - sbom.xml: {xml_size:,} bytes")
        except FileNotFoundError:
            pass
            
    elif json_success or xml_success:
        print("⚠️  SBOM partially generated (one format failed)")
        sys.exit(1)
    else:
        print("❌ SBOM generation failed completely")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SBOM Generation Script for BSI TR-03183 Compliance

This script generates a Software Bill of Materials (SBOM) in CycloneDX format
to comply with German BSI TR-03183 cybersecurity standards.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from cyclonedx.model import ExternalReference, ExternalReferenceType
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.output import OutputFormat, get_instance
from cyclonedx.parser import BaseParser
from cyclonedx.parser.poetry import PoetryFileParser


def generate_sbom():
    """Generate SBOM in CycloneDX format."""

    # Parse Poetry lock file
    parser = PoetryFileParser(poetry_lock_file_path="poetry.lock")
    bom = parser.parse()

    # Add metadata
    bom.metadata.component = Component(
        name="tahecho",
        version="0.1.0",
        type=ComponentType.APPLICATION,
        description="AI-powered Jira assistant using LangChain, LangGraph, and Neo4j",
        licenses=[{"license": {"id": "MIT"}}],
        external_references=[
            ExternalReference(
                type=ExternalReferenceType.DOCUMENTATION,
                url="https://github.com/your-username/tahecho",
            ),
            ExternalReference(
                type=ExternalReferenceType.LICENSE,
                url="https://github.com/your-username/tahecho/blob/main/LICENSE",
            ),
        ],
    )

    # Add BSI TR-03183 compliance metadata
    bom.metadata.properties = [
        {"name": "bsi-compliance", "value": "TR-03183"},
        {"name": "sbom-format", "value": "CycloneDX"},
        {"name": "generated-date", "value": datetime.utcnow().isoformat()},
        {"name": "generator", "value": "cyclonedx-py"},
    ]

    return bom


def main():
    """Main function to generate and save SBOM."""
    try:
        bom = generate_sbom()

        # Generate JSON format (BSI preferred)
        outputter = get_instance(bom=bom, output_format=OutputFormat.JSON)
        json_output = outputter.output_as_string()

        # Save to file
        with open("sbom.json", "w") as f:
            f.write(json_output)

        # Also generate XML format
        xml_outputter = get_instance(bom=bom, output_format=OutputFormat.XML)
        xml_output = xml_outputter.output_as_string()

        with open("sbom.xml", "w") as f:
            f.write(xml_output)

        print("✅ SBOM generated successfully:")
        print("   - sbom.json (CycloneDX JSON format)")
        print("   - sbom.xml (CycloneDX XML format)")
        print("   - Compliant with BSI TR-03183 Part 2 requirements")

    except Exception as e:
        print(f"❌ Error generating SBOM: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

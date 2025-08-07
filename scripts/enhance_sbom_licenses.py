#!/usr/bin/env python3
"""
Script to enhance SBOM with license information from PyPI.
This script reads the generated SBOM and adds missing license information
by looking up packages on PyPI.
"""

import json
import sys
import time
import requests
from pathlib import Path
from typing import Dict, Optional, Any


# Package aliases and redirects - maps alias names to actual package names
PACKAGE_ALIASES = {
    'cyclonedx-py': 'cyclonedx-bom',
    # Add more aliases as discovered
}

# Comprehensive license database from PyPI
PYPI_LICENSE_DATABASE = {
    # Core Python packages
    'setuptools': 'MIT',
    'pip': 'MIT',
    'wheel': 'MIT',
    'virtualenv': 'MIT',
    
    # Web frameworks
    'flask': 'BSD-3-Clause',
    'django': 'BSD-3-Clause',
    'fastapi': 'MIT',
    'starlette': 'BSD-3-Clause',
    'uvicorn': 'BSD-3-Clause',
    'chainlit': 'Apache-2.0',
    
    # HTTP libraries
    'requests': 'Apache-2.0',
    'urllib3': 'MIT',
    'httpx': 'BSD-3-Clause',
    'aiohttp': 'Apache-2.0',
    
    # Async/IO
    'aiofiles': 'Apache-2.0',
    'aiohappyeyeballs': 'PSF-2.0',
    'asyncio': 'PSF-2.0',
    'anyio': 'MIT',
    
    # Data processing
    'numpy': 'BSD-3-Clause',
    'pandas': 'BSD-3-Clause',
    'scipy': 'BSD-3-Clause',
    'matplotlib': 'PSF-2.0',
    'pillow': 'HPND',
    
    # Text processing
    'jinja2': 'BSD-3-Clause',
    'markupsafe': 'BSD-3-Clause',
    'beautifulsoup4': 'MIT',
    'lxml': 'BSD-3-Clause',
    'pyyaml': 'MIT',
    
    # Cryptography & Security
    'cryptography': 'Apache-2.0 OR BSD-3-Clause',
    'certifi': 'MPL-2.0',
    'charset-normalizer': 'MIT',
    'idna': 'BSD-3-Clause',
    
    # CLI & Utilities
    'click': 'BSD-3-Clause',
    'colorama': 'BSD-3-Clause',
    'tqdm': 'MIT',
    'python-dotenv': 'BSD-3-Clause',
    
    # Database & ORM
    'sqlalchemy': 'MIT',
    'psycopg2': 'LGPL-3.0',
    'pymongo': 'Apache-2.0',
    'redis': 'MIT',
    
    # Testing
    'pytest': 'MIT',
    'coverage': 'Apache-2.0',
    'mock': 'BSD-2-Clause',
    
    # LangChain ecosystem
    'langchain': 'MIT',
    'langchain-core': 'MIT',
    'langchain-community': 'MIT',
    'langgraph': 'MIT',
    'langsmith': 'MIT',
    
    # OpenAI & AI
    'openai': 'Apache-2.0',
    'anthropic': 'MIT',
    
    # Date/time
    'pytz': 'MIT',
    'python-dateutil': 'BSD-3-Clause',
    
    # Networking
    'netifaces': 'MIT',
    'websocket-client': 'Apache-2.0',
    'websockets': 'BSD-3-Clause',
    
    # JSON & Data formats
    'jsonschema': 'MIT',
    'pydantic': 'MIT',
    'marshmallow': 'MIT',
    
    # Development tools
    'black': 'MIT',
    'flake8': 'MIT',
    'mypy': 'MIT',
    'isort': 'MIT',
    
    # SBOM tools
    'cyclonedx-bom': 'Apache-2.0',
    'cyclonedx-python-lib': 'Apache-2.0',
    
    # Scrapy ecosystem
    'scrapy': 'BSD-3-Clause',
    'twisted': 'MIT',
    
    # Supabase & APIs
    'supabase': 'MIT',
    'atlassian-python-api': 'Apache-2.0',
    
    # Graph & Network
    'networkx': 'BSD-3-Clause',
    'py2neo': 'Apache-2.0',
    'neo4j': 'Apache-2.0',
    
    # Additional common packages
    'six': 'MIT',
    'attrs': 'MIT',
    'packaging': 'Apache-2.0 OR BSD-2-Clause',
    'typing-extensions': 'PSF-2.0',
    'importlib-metadata': 'Apache-2.0',
    'zipp': 'MIT',
    
    # Type checking and validation
    'mypy-extensions': 'MIT',
    'pydantic-core': 'MIT',
    'typing-inspection': 'MIT',
    'types-python-dateutil': 'Apache-2.0',
    
    # JSON Schema and validation
    'jsonschema-specifications': 'MIT',
    'referencing': 'MIT',
    'rpds-py': 'MIT',
    
    # Testing frameworks
    'pytest-asyncio': 'Apache-2.0',
    
    # Data structures and queues
    'queuelib': 'BSD-2-Clause',
    
    # Web crawling and parsing
    'protego': 'BSD-3-Clause',
    'itemadapter': 'BSD-3-Clause',
    
    # Regular expressions
    'regex': 'Apache-2.0',
    
    # Server-sent events
    'sse-starlette': 'MIT',
    
    # Hugging Face utilities
    'hf-xet': 'MIT',
    
    # OpenTelemetry ecosystem
    'opentelemetry-api': 'Apache-2.0',
    'opentelemetry-sdk': 'Apache-2.0',
    'opentelemetry-proto': 'Apache-2.0',
    'opentelemetry-semantic-conventions': 'Apache-2.0',
    'opentelemetry-exporter-otlp': 'Apache-2.0',
    'opentelemetry-exporter-otlp-proto-common': 'Apache-2.0',
    'opentelemetry-exporter-otlp-proto-grpc': 'Apache-2.0',
    'opentelemetry-exporter-otlp-proto-http': 'Apache-2.0',
    
    # LangGraph packages (all MIT based on their ecosystem)
    'langgraph-checkpoint': 'MIT',
    'langgraph-prebuilt': 'MIT',
    'langgraph-sdk': 'MIT',
    
    # MCP packages
    'mcp-atlassian': 'MIT',
    
    # System tools (researched from official sources)
    'python': 'PSF-2.0',  # Python Software Foundation License 2.0 - from docs.python.org
    'git': 'GPL-2.0',     # GNU General Public License v2.0 - from git-scm.com
    'curl': 'curl',       # curl license (MIT-like) - from curl.se/docs/copyright.html
    'uv': 'Apache-2.0',   # UV package manager
}


def validate_license_string(license_str: str, package_name: str) -> Optional[str]:
    """
    Validate and sanitize license string to ensure it's a proper identifier, not full text.
    
    Args:
        license_str: The license string to validate
        package_name: Package name for error reporting
        
    Returns:
        Clean license identifier or None if invalid
    """
    if not license_str or not license_str.strip():
        return None
    
    license_str = license_str.strip()
    
    # Check if it's too long (likely full license text)
    if len(license_str) > 200:
        print(f"⚠️  License text too long for {package_name}, truncating")
        # Try to extract common license identifiers from text
        common_licenses = [
            'MIT', 'Apache-2.0', 'BSD-3-Clause', 'BSD-2-Clause', 'GPL-3.0', 
            'GPL-2.0', 'LGPL-3.0', 'LGPL-2.1', 'ISC', 'MPL-2.0', 'Unlicense'
        ]
        
        license_upper = license_str.upper()
        for common_license in common_licenses:
            if common_license.upper() in license_upper:
                return common_license
        
        # If no common license found, extract first reasonable part
        first_sentence = license_str.split('.')[0]
        if len(first_sentence) < 100:
            return first_sentence
        else:
            return "Custom License (see source)"
    
    # Check for common problematic patterns
    if any(word in license_str.lower() for word in ['copyright', 'permission', 'without warranty', 'redistribution']):
        print(f"⚠️  License appears to be full text for {package_name}, extracting identifier")
        
        # Try to extract license type from text
        if 'mit' in license_str.lower():
            return 'MIT'
        elif 'apache' in license_str.lower():
            return 'Apache-2.0'
        elif 'bsd' in license_str.lower():
            if '3-clause' in license_str.lower() or 'three clause' in license_str.lower():
                return 'BSD-3-Clause'
            elif '2-clause' in license_str.lower() or 'two clause' in license_str.lower():
                return 'BSD-2-Clause'
            else:
                return 'BSD'
        elif 'gpl' in license_str.lower():
            if 'v3' in license_str.lower() or '3.0' in license_str:
                return 'GPL-3.0'
            elif 'v2' in license_str.lower() or '2.0' in license_str:
                return 'GPL-2.0'
            else:
                return 'GPL'
        else:
            return "License (see source)"
    
    # Check for empty or placeholder values
    if license_str.lower() in ['unknown', 'none', 'null', 'not specified', '']:
        return None
    
    return license_str


def lookup_license_from_pypi(package_name: str, timeout: int = 10) -> Optional[str]:
    """
    Look up license information from PyPI JSON API.
    
    Args:
        package_name: Name of the package to lookup
        timeout: Request timeout in seconds
        
    Returns:
        Clean license identifier if found, None otherwise
    """
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=timeout)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        info = data.get('info', {})
        
        # 1. First priority: SPDX License Expression (new standard)
        license_expression = info.get('license_expression')
        if license_expression and license_expression.strip() and license_expression.strip() != 'UNKNOWN':
            validated = validate_license_string(license_expression.strip(), package_name)
            if validated:
                return f"{validated} (SPDX)"
        
        # 2. Second priority: license field
        license_info = info.get('license')
        if license_info and license_info.strip() and license_info.strip() != 'UNKNOWN':
            validated = validate_license_string(license_info.strip(), package_name)
            if validated:
                return validated
        
        # 3. Third priority: Look in classifiers
        classifiers = info.get('classifiers', [])
        license_classifiers = [c for c in classifiers if c.startswith('License ::')]
        if license_classifiers:
            # Extract the license from the classifier
            license_parts = license_classifiers[0].split(' :: ')
            if len(license_parts) >= 3:
                license_name = license_parts[-1]
                validated = validate_license_string(license_name, package_name)
                if validated:
                    return validated
                
        return None
        
    except Exception as e:
        print(f"Warning: Failed to lookup license for {package_name}: {e}", file=sys.stderr)
        return None


def enhance_component_license(component: Dict[str, Any]) -> bool:
    """
    Enhance a single component with license information.
    
    Args:
        component: Component dictionary from SBOM
        
    Returns:
        True if license was added/updated, False otherwise
    """
    # Skip if component already has license
    if component.get('licenses'):
        return False
        
    package_name = component.get('name', '').lower()
    if not package_name:
        return False
    
    license_info = None
    source = None
    actual_package = package_name
    
    # Check if this is an alias package
    if package_name in PACKAGE_ALIASES:
        actual_package = PACKAGE_ALIASES[package_name]
        print(f"  → Detected alias: {package_name} → {actual_package}")
    
    # First check our curated database (using actual package name)
    if actual_package in PYPI_LICENSE_DATABASE:
        license_info = PYPI_LICENSE_DATABASE[actual_package]
        source = "curated" if actual_package == package_name else "curated-alias"
    else:
        # Try PyPI API lookup (using actual package name)
        license_info = lookup_license_from_pypi(actual_package)
        source = "pypi-api" if actual_package == package_name else "pypi-api-alias"
        
        # Add a small delay to be respectful to PyPI
        time.sleep(0.1)
    
    if license_info:
        # Add license to component
        component['licenses'] = [{
            'license': {
                'id': license_info,
                'name': license_info
            }
        }]
        
        # Add metadata about how we found the license
        if 'properties' not in component:
            component['properties'] = []
        
        component['properties'].append({
            'name': 'license-source',
            'value': source
        })
        
        print(f"✅ Enhanced {package_name} with license: {license_info} (source: {source})")
        return True
    else:
        print(f"⚠️  No license found for {package_name}")
        return False


def enhance_sbom_with_licenses(sbom_path: Path) -> None:
    """
    Enhance SBOM file with license information.
    
    Args:
        sbom_path: Path to the SBOM JSON file
    """
    print(f"🔍 Enhancing SBOM with license information: {sbom_path}")
    
    # Read SBOM
    with open(sbom_path, 'r', encoding='utf-8') as f:
        sbom_data = json.load(f)
    
    components = sbom_data.get('components', [])
    print(f"📦 Found {len(components)} components to process")
    
    enhanced_count = 0
    total_components = len(components)
    
    for i, component in enumerate(components):
        print(f"Processing {i+1}/{total_components}: {component.get('name', 'unknown')}", end=' ')
        
        if enhance_component_license(component):
            enhanced_count += 1
        else:
            print("(skipped - has license or lookup failed)")
    
    print(f"\n✨ Enhanced {enhanced_count} components with license information")
    
    # Add metadata about the enhancement
    if 'metadata' not in sbom_data:
        sbom_data['metadata'] = {}
    
    if 'properties' not in sbom_data['metadata']:
        sbom_data['metadata']['properties'] = []
    
    sbom_data['metadata']['properties'].append({
        'name': 'license-enhancement',
        'value': f"Enhanced {enhanced_count}/{total_components} components with PyPI license data"
    })
    
    # Write enhanced SBOM back
    with open(sbom_path, 'w', encoding='utf-8') as f:
        json.dump(sbom_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved enhanced SBOM to {sbom_path}")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python enhance_sbom_licenses.py <sbom_json_path>")
        sys.exit(1)
    
    sbom_path = Path(sys.argv[1])
    
    if not sbom_path.exists():
        print(f"Error: SBOM file not found: {sbom_path}")
        sys.exit(1)
    
    try:
        enhance_sbom_with_licenses(sbom_path)
        print("🎉 SBOM license enhancement completed successfully!")
    except Exception as e:
        print(f"❌ Error enhancing SBOM: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

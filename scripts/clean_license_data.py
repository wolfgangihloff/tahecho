#!/usr/bin/env python3
"""
Clean up problematic license data in SBOM.

This script fixes components that have full license text instead of proper identifiers.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def validate_and_clean_license(license_str: str, package_name: str) -> Optional[str]:
    """
    Clean and validate license string to ensure it's a proper identifier.
    
    Args:
        license_str: The license string to clean
        package_name: Package name for context
        
    Returns:
        Clean license identifier or None if invalid
    """
    if not license_str or not license_str.strip():
        return None
    
    license_str = license_str.strip()
    
    # Check if it's too long (likely full license text)
    if len(license_str) > 200:
        print(f"🔧 Cleaning license text for {package_name}")
        
        # Extract license type from text
        license_lower = license_str.lower()
        
        if 'mit license' in license_lower or (
            'mit' in license_lower and 'permission is hereby granted' in license_lower
        ):
            return 'MIT'
        elif 'apache' in license_lower:
            if '2.0' in license_str:
                return 'Apache-2.0'
            else:
                return 'Apache-2.0'
        elif 'bsd' in license_lower and 'redistribution and use' in license_lower:
            if '3-clause' in license_lower or 'three clause' in license_lower or (
                'redistributions of source code must retain' in license_lower and
                'redistributions in binary form must reproduce' in license_lower and
                'neither the name' in license_lower
            ):
                return 'BSD-3-Clause'
            elif '2-clause' in license_lower or 'two clause' in license_lower:
                return 'BSD-2-Clause'
            else:
                return 'BSD-3-Clause'  # Default for BSD
        elif 'gnu general public license' in license_lower or 'gpl' in license_lower:
            if 'v3' in license_lower or '3.0' in license_str:
                return 'GPL-3.0'
            elif 'v2' in license_lower or '2.0' in license_str:
                return 'GPL-2.0'
            else:
                return 'GPL'
        elif 'mozilla public license' in license_lower or 'mpl' in license_lower:
            return 'MPL-2.0'
        elif 'isc license' in license_lower:
            return 'ISC'
        else:
            # Extract first meaningful part
            first_line = license_str.split('\n')[0].strip()
            if len(first_line) < 100:
                return first_line
            else:
                return "Custom License"
    
    # Check for other problematic patterns
    if any(phrase in license_str.lower() for phrase in [
        'permission is hereby granted',
        'redistribution and use',
        'without warranty',
        'copyright (c)',
        'all rights reserved'
    ]):
        print(f"🔧 Extracting license identifier from text for {package_name}")
        
        # Try to extract license type
        if 'mit' in license_str.lower():
            return 'MIT'
        elif 'apache' in license_str.lower():
            return 'Apache-2.0'
        elif 'bsd' in license_str.lower():
            return 'BSD-3-Clause'
        elif 'gpl' in license_str.lower():
            return 'GPL-3.0'
        else:
            return 'Custom License'
    
    return license_str


def clean_sbom_licenses(sbom_path: str) -> bool:
    """
    Clean problematic license data in SBOM.
    
    Args:
        sbom_path: Path to SBOM JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load SBOM
        with open(sbom_path, 'r', encoding='utf-8') as f:
            sbom_data = json.load(f)
        
        components = sbom_data.get('components', [])
        cleaned_count = 0
        
        print(f"🔍 Cleaning license data for {len(components)} components...")
        
        for component in components:
            name = component.get('name', 'unknown')
            licenses = component.get('licenses', [])
            
            if not licenses:
                continue
            
            for license_entry in licenses:
                license_info = license_entry.get('license', {})
                license_id = license_info.get('id', '')
                license_name = license_info.get('name', '')
                
                # Check if license ID needs cleaning
                if license_id and len(license_id) > 100:
                    cleaned_id = validate_and_clean_license(license_id, name)
                    if cleaned_id and cleaned_id != license_id:
                        license_info['id'] = cleaned_id
                        # Also update name to match
                        license_info['name'] = cleaned_id
                        cleaned_count += 1
                        print(f"  ✅ Cleaned {name}: {cleaned_id}")
                
                # Check if license name needs cleaning (and ID is empty/short)
                elif license_name and len(license_name) > 100 and len(license_id) < 50:
                    cleaned_name = validate_and_clean_license(license_name, name)
                    if cleaned_name and cleaned_name != license_name:
                        license_info['name'] = cleaned_name
                        # Set ID to match if it was empty
                        if not license_id:
                            license_info['id'] = cleaned_name
                        cleaned_count += 1
                        print(f"  ✅ Cleaned {name}: {cleaned_name}")
        
        # Add metadata about cleaning
        metadata = sbom_data.setdefault('metadata', {})
        properties = metadata.setdefault('properties', [])
        
        # Remove old cleaning metadata
        properties = [p for p in properties if p.get('name') != 'license-cleaning']
        
        if cleaned_count > 0:
            properties.append({
                'name': 'license-cleaning',
                'value': f'Cleaned {cleaned_count} components with problematic license data'
            })
        
        metadata['properties'] = properties
        
        # Save cleaned SBOM
        with open(sbom_path, 'w', encoding='utf-8') as f:
            json.dump(sbom_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Cleaned {cleaned_count} license entries")
        print(f"💾 Saved cleaned SBOM to {sbom_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning SBOM licenses: {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python clean_license_data.py <sbom_json_path>")
        sys.exit(1)
    
    sbom_path = sys.argv[1]
    
    if not Path(sbom_path).exists():
        print(f"❌ SBOM file not found: {sbom_path}")
        sys.exit(1)
    
    success = clean_sbom_licenses(sbom_path)
    
    if not success:
        print("❌ License cleaning failed")
        sys.exit(1)
    
    print("🎉 License cleaning completed successfully!")


if __name__ == "__main__":
    main()

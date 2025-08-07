#!/usr/bin/env python3
"""
SBOM Quality Validation Script

This script validates that the generated SBOM meets all BSI TR-03183 requirements
and has high-quality data for all components.

Validation checks:
- 📦 Package Versions & Licenses
- 🔗 Dependency Relationships  
- 📍 Source Code Locations
- 🏷️ Component Metadata
- 🔐 Security Checksums
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str
    component_name: str = ""
    severity: str = "error"  # error, warning, info


class SBOMQualityValidator:
    """Validates SBOM quality and completeness."""
    
    def __init__(self, sbom_path: str):
        self.sbom_path = Path(sbom_path)
        self.sbom_data = None
        self.results: List[ValidationResult] = []
        self.stats = {
            'total_components': 0,
            'components_with_licenses': 0,
            'components_with_versions': 0,
            'components_with_dependencies': 0,
            'components_with_sources': 0,
            'components_with_checksums': 0,
            'errors': 0,
            'warnings': 0
        }
    
    def load_sbom(self) -> bool:
        """Load and parse the SBOM file."""
        try:
            with open(self.sbom_path, 'r', encoding='utf-8') as f:
                self.sbom_data = json.load(f)
            return True
        except FileNotFoundError:
            self.add_result(ValidationResult(
                False, f"SBOM file not found: {self.sbom_path}", severity="error"
            ))
            return False
        except json.JSONDecodeError as e:
            self.add_result(ValidationResult(
                False, f"Invalid JSON in SBOM file: {e}", severity="error"
            ))
            return False
        except Exception as e:
            self.add_result(ValidationResult(
                False, f"Error loading SBOM: {e}", severity="error"
            ))
            return False
    
    def add_result(self, result: ValidationResult):
        """Add a validation result."""
        self.results.append(result)
        if result.severity == "error":
            self.stats['errors'] += 1
        elif result.severity == "warning":
            self.stats['warnings'] += 1
    
    def validate_basic_structure(self) -> bool:
        """Validate basic SBOM structure."""
        if not self.sbom_data:
            return False
        
        # Check required top-level fields
        required_fields = ['bomFormat', 'specVersion', 'serialNumber', 'version', 'metadata', 'components']
        
        for field in required_fields:
            if field not in self.sbom_data:
                self.add_result(ValidationResult(
                    False, f"Missing required field: {field}", severity="error"
                ))
                return False
        
        # Check CycloneDX format
        if self.sbom_data.get('bomFormat') != 'CycloneDX':
            self.add_result(ValidationResult(
                False, f"Invalid bomFormat: {self.sbom_data.get('bomFormat')}, expected 'CycloneDX'", 
                severity="error"
            ))
            return False
        
        self.add_result(ValidationResult(
            True, f"Basic SBOM structure valid (CycloneDX {self.sbom_data.get('specVersion')})", 
            severity="info"
        ))
        return True
    
    def validate_component_versions(self) -> bool:
        """Validate that all components have proper versions."""
        components = self.sbom_data.get('components', [])
        self.stats['total_components'] = len(components)
        
        missing_versions = []
        invalid_versions = []
        
        for component in components:
            name = component.get('name', 'unknown')
            version = component.get('version')
            
            if not version:
                missing_versions.append(name)
            elif version in ['unknown', 'latest', 'dev', '']:
                invalid_versions.append(f"{name}@{version}")
            else:
                self.stats['components_with_versions'] += 1
        
        if missing_versions:
            self.add_result(ValidationResult(
                False, 
                f"📦 {len(missing_versions)} components missing versions: {', '.join(missing_versions[:5])}" +
                ("..." if len(missing_versions) > 5 else ""),
                severity="error"
            ))
        
        if invalid_versions:
            self.add_result(ValidationResult(
                False,
                f"📦 {len(invalid_versions)} components with invalid versions: {', '.join(invalid_versions[:5])}" +
                ("..." if len(invalid_versions) > 5 else ""),
                severity="warning"
            ))
        
        coverage = (self.stats['components_with_versions'] / max(1, self.stats['total_components'])) * 100
        self.add_result(ValidationResult(
            coverage >= 95,
            f"📦 Version coverage: {coverage:.1f}% ({self.stats['components_with_versions']}/{self.stats['total_components']})",
            severity="error" if coverage < 95 else "info"
        ))
        
        return coverage >= 95
    
    def validate_component_licenses(self) -> bool:
        """Validate that components have proper license information."""
        components = self.sbom_data.get('components', [])
        
        missing_licenses = []
        invalid_licenses = []
        problematic_licenses = []
        
        for component in components:
            name = component.get('name', 'unknown')
            licenses = component.get('licenses', [])
            
            if not licenses:
                missing_licenses.append(name)
                continue
            
            # Check license quality
            for license_entry in licenses:
                license_info = license_entry.get('license', {})
                license_id = license_info.get('id', '')
                license_name = license_info.get('name', '')
                
                # Check for problematic license text
                if any(len(text) > 200 for text in [license_id, license_name] if text):
                    problematic_licenses.append(f"{name} (license text too long)")
                elif any(word in (license_id + license_name).lower() 
                        for word in ['copyright', 'permission', 'redistribution', 'warranty']):
                    problematic_licenses.append(f"{name} (full license text instead of identifier)")
                elif not license_id and not license_name:
                    invalid_licenses.append(name)
                else:
                    self.stats['components_with_licenses'] += 1
        
        # Report issues (but be lenient with system components)
        non_system_missing = []
        for component_name in missing_licenses:
            # Find the component to check its ecosystem
            for component in components:
                if component.get('name') == component_name:
                    ecosystem = None
                    for prop in component.get('properties', []):
                        if prop.get('name') == 'ecosystem':
                            ecosystem = prop.get('value')
                            break
                    
                    # Only report as error if not a system component
                    if ecosystem != 'system':
                        non_system_missing.append(component_name)
                    break
        
        if non_system_missing:
            self.add_result(ValidationResult(
                False,
                f"🏷️ {len(non_system_missing)} non-system components missing licenses: {', '.join(non_system_missing[:5])}" +
                ("..." if len(non_system_missing) > 5 else ""),
                severity="error"
            ))
        elif missing_licenses:
            self.add_result(ValidationResult(
                True,
                f"🏷️ {len(missing_licenses)} system components missing licenses (acceptable): {', '.join(missing_licenses[:5])}" +
                ("..." if len(missing_licenses) > 5 else ""),
                severity="info"
            ))
        
        if problematic_licenses:
            self.add_result(ValidationResult(
                False,
                f"🏷️ {len(problematic_licenses)} components with problematic license data: {', '.join(problematic_licenses[:3])}" +
                ("..." if len(problematic_licenses) > 3 else ""),
                severity="error"
            ))
        
        coverage = (self.stats['components_with_licenses'] / max(1, self.stats['total_components'])) * 100
        self.add_result(ValidationResult(
            coverage >= 90,
            f"🏷️ License coverage: {coverage:.1f}% ({self.stats['components_with_licenses']}/{self.stats['total_components']})",
            severity="error" if coverage < 90 else "info"
        ))
        
        return coverage >= 90 and not problematic_licenses
    
    def validate_dependency_relationships(self) -> bool:
        """Validate dependency relationship information."""
        dependencies = self.sbom_data.get('dependencies', [])
        components = self.sbom_data.get('components', [])
        
        if not dependencies:
            self.add_result(ValidationResult(
                False,
                "🔗 No dependency relationships found in SBOM",
                severity="warning"
            ))
            return False
        
        # Count components with dependencies
        components_with_deps = 0
        for dep in dependencies:
            if dep.get('dependsOn'):
                components_with_deps += 1
        
        self.stats['components_with_dependencies'] = components_with_deps
        
        coverage = (components_with_deps / max(1, len(components))) * 100
        self.add_result(ValidationResult(
            coverage >= 70,
            f"🔗 Dependency coverage: {coverage:.1f}% ({components_with_deps}/{len(components)} components have dependencies)",
            severity="warning" if coverage < 70 else "info"
        ))
        
        return coverage >= 70
    
    def validate_source_locations(self) -> bool:
        """Validate source code location information."""
        components = self.sbom_data.get('components', [])
        
        components_with_sources = 0
        missing_sources = []
        
        for component in components:
            name = component.get('name', 'unknown')
            external_refs = component.get('externalReferences', [])
            purl = component.get('purl', '')
            
            has_source = False
            
            # Check for source references
            for ref in external_refs:
                if ref.get('type') in ['website', 'vcs', 'distribution']:
                    has_source = True
                    break
            
            # Check for package URL
            if purl and purl.startswith('pkg:'):
                has_source = True
            
            if has_source:
                components_with_sources += 1
            else:
                missing_sources.append(name)
        
        self.stats['components_with_sources'] = components_with_sources
        
        if missing_sources and len(missing_sources) > 10:
            self.add_result(ValidationResult(
                False,
                f"📍 {len(missing_sources)} components missing source locations: {', '.join(missing_sources[:5])}" +
                ("..." if len(missing_sources) > 5 else ""),
                severity="warning"
            ))
        
        coverage = (components_with_sources / max(1, self.stats['total_components'])) * 100
        self.add_result(ValidationResult(
            coverage >= 80,
            f"📍 Source location coverage: {coverage:.1f}% ({components_with_sources}/{self.stats['total_components']})",
            severity="warning" if coverage < 80 else "info"
        ))
        
        return coverage >= 80
    
    def validate_security_checksums(self) -> bool:
        """Validate security checksum information."""
        components = self.sbom_data.get('components', [])
        
        components_with_checksums = 0
        missing_checksums = []
        
        for component in components:
            name = component.get('name', 'unknown')
            external_refs = component.get('externalReferences', [])
            
            has_checksum = False
            
            # Check for hashes in external references
            for ref in external_refs:
                if ref.get('hashes'):
                    has_checksum = True
                    break
            
            if has_checksum:
                components_with_checksums += 1
            else:
                # System components may not have checksums
                component_type = component.get('type', '')
                ecosystem = None
                for prop in component.get('properties', []):
                    if prop.get('name') == 'ecosystem':
                        ecosystem = prop.get('value')
                        break
                
                if ecosystem not in ['system']:
                    missing_checksums.append(name)
        
        self.stats['components_with_checksums'] = components_with_checksums
        
        if missing_checksums and len(missing_checksums) > 20:
            self.add_result(ValidationResult(
                False,
                f"🔐 {len(missing_checksums)} components missing security checksums: {', '.join(missing_checksums[:5])}" +
                ("..." if len(missing_checksums) > 5 else ""),
                severity="warning"
            ))
        
        coverage = (components_with_checksums / max(1, self.stats['total_components'])) * 100
        self.add_result(ValidationResult(
            coverage >= 60,
            f"🔐 Security checksum coverage: {coverage:.1f}% ({components_with_checksums}/{self.stats['total_components']})",
            severity="warning" if coverage < 60 else "info"
        ))
        
        return coverage >= 60
    
    def validate_component_metadata(self) -> bool:
        """Validate component metadata quality."""
        components = self.sbom_data.get('components', [])
        
        missing_descriptions = []
        missing_types = []
        missing_purls = []
        
        for component in components:
            name = component.get('name', 'unknown')
            
            # Check description
            description = component.get('description', '')
            if not description or len(description.strip()) < 5:
                missing_descriptions.append(name)
            
            # Check type
            if not component.get('type'):
                missing_types.append(name)
            
            # Check PURL (Package URL)
            if not component.get('purl'):
                missing_purls.append(name)
        
        # Report issues
        if missing_descriptions and len(missing_descriptions) > 50:
            self.add_result(ValidationResult(
                False,
                f"🏷️ {len(missing_descriptions)} components missing descriptions",
                severity="warning"
            ))
        
        if missing_types:
            self.add_result(ValidationResult(
                False,
                f"🏷️ {len(missing_types)} components missing type information: {', '.join(missing_types[:5])}" +
                ("..." if len(missing_types) > 5 else ""),
                severity="error"
            ))
        
        if missing_purls and len(missing_purls) > 10:
            self.add_result(ValidationResult(
                False,
                f"🏷️ {len(missing_purls)} components missing Package URLs",
                severity="warning"
            ))
        
        return len(missing_types) == 0
    
    def run_validation(self) -> bool:
        """Run complete SBOM validation."""
        print(f"🔍 Validating SBOM quality: {self.sbom_path}")
        
        if not self.load_sbom():
            return False
        
        # Run all validation checks
        checks = [
            ("Basic Structure", self.validate_basic_structure),
            ("Component Versions", self.validate_component_versions),
            ("Component Licenses", self.validate_component_licenses),
            ("Dependency Relationships", self.validate_dependency_relationships),
            ("Source Locations", self.validate_source_locations),
            ("Security Checksums", self.validate_security_checksums),
            ("Component Metadata", self.validate_component_metadata),
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                if not result:
                    all_passed = False
                print(f"{'✅' if result else '❌'} {check_name}")
            except Exception as e:
                self.add_result(ValidationResult(
                    False, f"Error in {check_name}: {e}", severity="error"
                ))
                all_passed = False
                print(f"❌ {check_name} (Error: {e})")
        
        return all_passed
    
    def print_summary(self):
        """Print validation summary."""
        print(f"\n📊 SBOM Quality Summary:")
        print(f"   Total components: {self.stats['total_components']}")
        print(f"   📦 With versions: {self.stats['components_with_versions']}")
        print(f"   🏷️ With licenses: {self.stats['components_with_licenses']}")
        print(f"   🔗 With dependencies: {self.stats['components_with_dependencies']}")
        print(f"   📍 With sources: {self.stats['components_with_sources']}")
        print(f"   🔐 With checksums: {self.stats['components_with_checksums']}")
        
        print(f"\n📋 Validation Results:")
        print(f"   ❌ Errors: {self.stats['errors']}")
        print(f"   ⚠️  Warnings: {self.stats['warnings']}")
        
        if self.stats['errors'] == 0:
            print(f"\n✅ SBOM passes quality validation!")
        else:
            print(f"\n❌ SBOM has quality issues that need to be fixed!")
        
        # Print detailed results
        if self.results:
            print(f"\n🔍 Detailed Results:")
            for result in self.results:
                icon = "✅" if result.passed else ("⚠️" if result.severity == "warning" else "❌")
                print(f"   {icon} {result.message}")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python validate_sbom_quality.py <sbom_json_path>")
        sys.exit(1)
    
    sbom_path = sys.argv[1]
    
    validator = SBOMQualityValidator(sbom_path)
    success = validator.run_validation()
    validator.print_summary()
    
    if not success:
        print("\n💡 Recommendations:")
        print("   1. Ensure all components have proper version numbers")
        print("   2. Fix license data quality (no full license text)")
        print("   3. Add missing component metadata")
        print("   4. Include source code locations and checksums")
        
        sys.exit(1)
    
    print("\n🎉 SBOM quality validation passed!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Validate GitHub Actions workflow syntax and configuration.
This script provides a comprehensive validation of the SBOM generation workflow.
"""

import sys
import yaml  # type: ignore
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any


def validate_yaml_syntax(workflow_path: Path) -> bool:
    """Validate that the workflow YAML syntax is correct."""
    try:
        with open(workflow_path, 'r') as f:
            content = f.read()
            # Handle 'on' keyword issue in YAML
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == 'on:':
                    lines[i] = 'workflow_triggers:'
                    break
            
            content = '\n'.join(lines)
            parsed = yaml.safe_load(content)
            
            if 'workflow_triggers' in parsed:
                parsed['on'] = parsed.pop('workflow_triggers')
                
        print("✅ YAML syntax is valid")
        return True
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating YAML: {e}")
        return False


def validate_workflow_structure(workflow_path: Path) -> bool:
    """Validate workflow structure and required sections."""
    try:
        with open(workflow_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == 'on:':
                    lines[i] = 'workflow_triggers:'
                    break
            
            content = '\n'.join(lines)
            workflow = yaml.safe_load(content)
            
            if 'workflow_triggers' in workflow:
                workflow['on'] = workflow.pop('workflow_triggers')
        
        required_sections = ['name', 'on', 'jobs']
        missing_sections = []
        
        for section in required_sections:
            if section not in workflow:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing required sections: {missing_sections}")
            return False
        
        print("✅ Workflow structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error validating workflow structure: {e}")
        return False


def validate_action_versions(workflow_path: Path) -> bool:
    """Validate that all GitHub Actions use pinned versions."""
    try:
        with open(workflow_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        action_lines = [line.strip() for line in lines if 'uses:' in line]
        
        issues = []
        for line in action_lines:
            if 'uses:' in line:
                action = line.split('uses:')[1].strip()
                if '@' in action:
                    version = action.split('@')[1]
                    if version in ['main', 'master']:
                        issues.append(f"Action uses unpinned version: {action}")
                else:
                    issues.append(f"Action missing version: {action}")
        
        if issues:
            print("❌ Action version issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        
        print("✅ All actions use pinned versions")
        return True
        
    except Exception as e:
        print(f"❌ Error validating action versions: {e}")
        return False


def validate_job_dependencies(workflow_path: Path) -> bool:
    """Validate job dependencies and step references."""
    try:
        with open(workflow_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == 'on:':
                    lines[i] = 'workflow_triggers:'
                    break
            
            content = '\n'.join(lines)
            workflow = yaml.safe_load(content)
            
            if 'workflow_triggers' in workflow:
                workflow['on'] = workflow.pop('workflow_triggers')
        
        jobs = workflow.get('jobs', {})
        job_names = set(jobs.keys())
        
        # Check job dependencies
        for job_name, job_config in jobs.items():
            if 'needs' in job_config:
                needs = job_config['needs']
                if isinstance(needs, str):
                    needs = [needs]
                
                for dependency in needs:
                    if dependency not in job_names:
                        print(f"❌ Job '{job_name}' depends on non-existent job '{dependency}'")
                        return False
        
        print("✅ Job dependencies are valid")
        return True
        
    except Exception as e:
        print(f"❌ Error validating job dependencies: {e}")
        return False


def check_linter_compliance(workflow_path: Path) -> bool:
    """Check if workflow passes linter requirements."""
    try:
        # Run our pytest tests as a linter check
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/unit/test_github_workflows.py', 
            '-v', '--tb=short'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Workflow passes all linter tests")
            return True
        else:
            print("❌ Workflow fails linter tests:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running linter checks: {e}")
        return False


def validate_specific_fixes() -> bool:
    """Validate the specific fixes we made for linter issues."""
    try:
        with open('.github/workflows/sbom-generation.yml', 'r') as f:
            content = f.read()
        
        checks = []
        
        # Check 1: setup-python step has an id
        if 'id: setup-python' in content:
            checks.append("✅ setup-python step has correct id")
        else:
            checks.append("❌ setup-python step missing id")
        
        # Check 2: cache key references correct python version
        if 'steps.setup-python.outputs.python-version' in content:
            checks.append("✅ cache key references correct python version")
        else:
            checks.append("❌ cache key doesn't reference python version correctly")
        
        # Check 3: anchore scan action uses sbom parameter
        if 'anchore/scan-action@v3' in content and 'sbom: public/sbom.json' in content:
            checks.append("✅ anchore scan action configured correctly")
        else:
            checks.append("❌ anchore scan action not configured correctly")
        
        all_passed = all('✅' in check for check in checks)
        
        print("\nSpecific fix validation:")
        for check in checks:
            print(f"  {check}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error validating specific fixes: {e}")
        return False


def main() -> None:
    """Run all workflow validations."""
    workflow_path = Path('.github/workflows/sbom-generation.yml')
    
    if not workflow_path.exists():
        print(f"❌ Workflow file not found: {workflow_path}")
        sys.exit(1)
    
    print("🔍 Validating GitHub Actions workflow...")
    print("=" * 50)
    
    validations = [
        ("YAML Syntax", lambda: validate_yaml_syntax(workflow_path)),
        ("Workflow Structure", lambda: validate_workflow_structure(workflow_path)),
        ("Action Versions", lambda: validate_action_versions(workflow_path)),
        ("Job Dependencies", lambda: validate_job_dependencies(workflow_path)),
        ("Specific Fixes", validate_specific_fixes),
        ("Linter Compliance", lambda: check_linter_compliance(workflow_path)),
    ]
    
    results = []
    for name, validation_func in validations:
        print(f"\n📋 {name}:")
        try:
            result = validation_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (name, _) in enumerate(validations):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nOverall: {passed}/{total} validations passed")
    
    if passed == total:
        print("🎉 All validations passed! Workflow is ready.")
        sys.exit(0)
    else:
        print("💥 Some validations failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

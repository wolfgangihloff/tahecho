#!/usr/bin/env python3
"""
Test runner script for Tahecho TDD workflow.
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description} completed successfully")
        return True


def main():
    parser = argparse.ArgumentParser(description="Tahecho Test Runner")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "all", "coverage", "quality"],
        default="unit",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--watch", 
        action="store_true",
        help="Run tests in watch mode"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    success = True
    
    if args.type == "quality":
        # Run code quality checks
        print("🔍 Running code quality checks...")
        
        quality_checks = [
            (["black", "--check", "."], "Code formatting (Black)"),
            (["isort", "--check-only", "."], "Import sorting (isort)"),
            (["flake8", "."], "Linting (flake8)"),
            (["mypy", "."], "Type checking (mypy)"),
        ]
        
        for cmd, description in quality_checks:
            if not run_command(cmd, description):
                success = False
        
        if success:
            print("\n🎉 All quality checks passed!")
        else:
            print("\n❌ Some quality checks failed!")
            sys.exit(1)
    
    elif args.type == "coverage":
        # Run tests with coverage
        print("📊 Running tests with coverage...")
        
        coverage_cmd = [
            "pytest", 
            "--cov=agents", 
            "--cov=utils", 
            "--cov=jira_integration",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml"
        ]
        
        if args.verbose:
            coverage_cmd.append("-v")
        
        if not run_command(coverage_cmd, "Test coverage"):
            success = False
    
    else:
        # Run tests
        print("🧪 Running tests...")
        
        if args.watch:
            test_cmd = ["ptw", "--", "-v"]
        else:
            test_cmd = ["pytest"]
            
            if args.type == "unit":
                test_cmd.extend(["tests/unit/"])
            elif args.type == "integration":
                test_cmd.extend(["tests/integration/"])
            # else "all" - run all tests
            
            if args.verbose:
                test_cmd.append("-v")
        
        if not run_command(test_cmd, f"Tests ({args.type})"):
            success = False
    
    if success:
        print("\n🎉 All checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    import os
    main() 
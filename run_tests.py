"""
Run TDD tests for qualitative coding project.

This follows proper TDD methodology:
1. Run tests (RED)
2. Write minimal code to pass (GREEN)  
3. Refactor while keeping tests green
"""
import sys
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_unit_tests():
    """Run unit tests only (no integration tests)."""
    print("=" * 60)
    print("Running Unit Tests")
    print("=" * 60)
    
    exit_code = pytest.main([
        "tests/",
        "-v",
        "-k", "not integration",
        "--tb=short"
    ])
    
    return exit_code


def run_integration_tests():
    """Run integration tests with real files."""
    print("\n" + "=" * 60)
    print("Running Integration Tests")
    print("=" * 60)
    
    exit_code = pytest.main([
        "tests/",
        "-v", 
        "-k", "integration",
        "--tb=short"
    ])
    
    return exit_code


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running All Tests")
    print("=" * 60)
    
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--cov=qc",
        "--cov-report=term-missing"
    ])
    
    return exit_code


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests for qualitative coding project")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="unit",
        help="Type of tests to run"
    )
    
    args = parser.parse_args()
    
    if args.type == "unit":
        exit_code = run_unit_tests()
    elif args.type == "integration":
        exit_code = run_integration_tests()
    else:
        exit_code = run_all_tests()
    
    sys.exit(exit_code)
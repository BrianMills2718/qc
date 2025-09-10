"""
Test runner for integration and end-to-end validation system tests.

This script provides a convenient way to run the comprehensive test suite
for the validation system with proper environment setup and reporting.
"""

import subprocess
import sys
import os
import argparse
import time
from pathlib import Path


def setup_test_environment():
    """Setup environment for testing"""
    # Ensure we're in the right directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Add project to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    print(f"[OK] Set up test environment in {project_root}")


def check_dependencies():
    """Check that required dependencies are available"""
    required_packages = [
        'pytest',
        'neo4j'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"[ERROR] Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("[OK] All required dependencies available")
    return True


def run_test_suite(test_type="all", verbose=False, markers=None):
    """Run the specified test suite with detailed reporting"""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.extend(["-v", "-s"])
    
    # Add test selection based on type
    if test_type == "integration":
        cmd.append("tests/test_integration_validation.py")
        if markers:
            cmd.extend(["-m", "integration"])
    elif test_type == "e2e":
        cmd.append("tests/test_end_to_end_validation.py")
        if markers:
            cmd.extend(["-m", "e2e"])
    elif test_type == "neo4j":
        cmd.append("tests/test_neo4j_schema_compatibility.py")
    elif test_type == "gemini":
        cmd.append("tests/test_gemini_integration.py")
    elif test_type == "config":
        cmd.append("tests/test_config_loading_simple.py")
    elif test_type == "infrastructure":
        cmd.append("tests/test_validation_infrastructure.py")
    elif test_type == "all":
        # Run all test suites individually for detailed reporting
        return run_all_test_suites(verbose)
    else:
        cmd.append(f"tests/test_{test_type}.py")
    
    # Add additional pytest options for detailed output
    cmd.extend([
        "--tb=short",           # Shorter traceback format
        "--disable-warnings",   # Disable pytest warnings
        "--asyncio-mode=auto",  # Auto async mode
        "-v"                    # Always verbose for detailed output
    ])
    
    print(f"[START] Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
        duration = time.time() - start_time
        
        # Parse test results for detailed reporting
        passed, failed, total = parse_test_results(result.stdout)
        
        print("-" * 60)
        print(f"[RESULTS] {test_type.title()} Test Results:")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Total:  {total}")
        print(f"   Duration: {duration:.1f}s")
        
        if result.returncode == 0:
            print(f"[PASS] All {test_type} tests passed")
        else:
            print(f"[FAIL] {failed}/{total} {test_type} tests failed")
            if verbose and result.stdout:
                print("\nTest output:")
                print(result.stdout)
            if result.stderr:
                print("\nErrors:")
                print(result.stderr)
        
        return result.returncode == 0, passed, failed, total
        
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {test_type.title()} tests timed out after 30 minutes")
        return False, 0, 0, 0
    except Exception as e:
        print(f"[ERROR] Error running {test_type} tests: {e}")
        return False, 0, 0, 0


def run_all_test_suites(verbose=False):
    """Run all test suites with comprehensive reporting"""
    test_suites = [
        ("infrastructure", "tests/test_validation_infrastructure.py"),
        ("config", "tests/test_config_loading_simple.py"),
        ("integration", "tests/test_integration_validation.py"),
        ("neo4j", "tests/test_neo4j_schema_compatibility.py"),
        ("gemini", "tests/test_gemini_integration.py"),
        ("e2e", "tests/test_end_to_end_validation.py")
    ]
    
    total_passed = 0
    total_failed = 0
    total_tests = 0
    failed_suites = []
    
    print("[START] Running comprehensive test suite")
    print("=" * 60)
    
    for suite_name, suite_path in test_suites:
        success, passed, failed, total = run_test_suite(suite_name, verbose)
        total_passed += passed
        total_failed += failed
        total_tests += total
        
        if not success:
            failed_suites.append(suite_name)
        
        print()  # Spacing between suites
    
    # Final comprehensive report
    print("=" * 60)
    print("[COMPREHENSIVE RESULTS]")
    print(f"Total Tests: {total_tests}/50 (expected 50)")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "0%")
    
    # Break down by category
    print("\nResults by Category:")
    for suite_name, _ in test_suites:
        print(f"  {suite_name.capitalize()}: See results above")
    
    if failed_suites:
        print(f"\nFailed Test Suites: {', '.join(failed_suites)}")
        print("\nTroubleshooting Guide:")
        for suite in failed_suites:
            print(f"  {suite}: Run with --verbose for detailed failure analysis")
    
    # Success criteria: ALL 50 tests must pass
    if total_tests == 50 and total_failed == 0:
        print("\n[SUCCESS] All 50/50 tests passed! Integration testing complete.")
        return True
    else:
        print(f"\n[FAILED] {total_failed}/{total_tests} tests failed. Fix failing tests before declaring success.")
        print("Expected: 50/50 tests passing")
        print("Run individual test suites with --verbose for detailed failure analysis")
        return False


def parse_test_results(output):
    """Parse pytest output to extract passed/failed counts"""
    if not output:
        return 0, 0, 0
    
    # Look for summary line like "===== 8 passed, 2 failed in 10.5s ====="
    lines = output.split('\n')
    for line in lines:
        if 'passed' in line and ('failed' in line or 'error' in line):
            # Parse line like "8 passed, 2 failed"
            parts = line.split()
            passed = 0
            failed = 0
            
            for i, part in enumerate(parts):
                if part == 'passed' and i > 0:
                    try:
                        passed = int(parts[i-1])
                    except ValueError:
                        pass
                elif part == 'failed' and i > 0:
                    try:
                        failed = int(parts[i-1])
                    except ValueError:
                        pass
                elif part == 'error' and i > 0:
                    try:
                        failed += int(parts[i-1])
                    except ValueError:
                        pass
            
            return passed, failed, passed + failed
        
        elif 'passed' in line and ('failed' not in line and 'error' not in line):
            # Parse line like "8 passed"
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'passed' and i > 0:
                    try:
                        passed = int(parts[i-1])
                        return passed, 0, passed
                    except ValueError:
                        pass
    
    return 0, 0, 0


def run_quick_validation():
    """Run a quick validation test to check basic functionality"""
    print("[CHECK] Running quick validation check...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_integration_validation.py::TestValidationIntegration::test_validation_config_loading",
        "-v"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("[PASS] Quick validation passed")
            return True
        else:
            print("[FAIL] Quick validation failed")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"[ERROR] Quick validation error: {e}")
        return False


def generate_test_report():
    """Generate a comprehensive test report"""
    print("[REPORT] Generating test report...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--tb=short",
        "--disable-warnings",
        "--asyncio-mode=auto",
        "-v",
        "--collect-only"  # Just collect, don't run
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            test_files = [line for line in lines if 'test_' in line and '.py::' in line]
            
            print(f"[SUMMARY] Test Report Summary:")
            print(f"   Total test files: {len(set(line.split('::')[0] for line in test_files))}")
            print(f"   Total test cases: {len(test_files)}")
            print()
            
            # Group by test file
            by_file = {}
            for line in test_files:
                if '::' in line:
                    file_part = line.split('::')[0].split('/')[-1]
                    if file_part not in by_file:
                        by_file[file_part] = 0
                    by_file[file_part] += 1
            
            for file, count in sorted(by_file.items()):
                print(f"   {file}: {count} tests")
            
            return True
        else:
            print("[ERROR] Failed to generate test report")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error generating report: {e}")
        return False


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run validation system integration tests")
    parser.add_argument(
        "test_type", 
        choices=["all", "integration", "e2e", "neo4j", "gemini", "quick", "report"],
        default="all",
        nargs="?",
        help="Type of tests to run"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-m", "--markers", help="Pytest markers to filter tests")
    parser.add_argument("--no-deps-check", action="store_true", help="Skip dependency check")
    
    args = parser.parse_args()
    
    print("*** Validation System Test Runner ***")
    print("=" * 40)
    
    # Setup environment
    setup_test_environment()
    
    # Check dependencies unless skipped
    if not args.no_deps_check and not check_dependencies():
        sys.exit(1)
    
    success = True
    
    # Run requested tests
    if args.test_type == "quick":
        success = run_quick_validation()
    elif args.test_type == "report":
        success = generate_test_report()
    elif args.test_type == "all":
        success = run_all_test_suites(args.verbose)
    else:
        # For individual test suites, just check if they pass
        result = run_test_suite(args.test_type, args.verbose, args.markers)
        success = result[0] if isinstance(result, tuple) else result
    
    print("=" * 40)
    if success:
        if args.test_type == "all":
            print("[SUCCESS] All 50/50 tests passed! Integration testing complete!")
        else:
            print(f"[SUCCESS] {args.test_type.title()} tests completed successfully!")
        sys.exit(0)
    else:
        if args.test_type == "all":
            print("[FAILED] Integration testing incomplete. Fix failing tests before declaring success.")
            print("Requirement: All 50 tests must pass")
        else:
            print(f"[FAILED] {args.test_type.title()} tests failed or encountered errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
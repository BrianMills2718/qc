#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Validation Script
Validates system configuration and dependencies for the qualitative coding analysis tool
"""

import os
import sys
import subprocess
import platform
import json
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import importlib
import logging

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise during validation


class HealthCheckResult:
    def __init__(self, name: str, status: str, message: str, details: Dict[str, Any] = None):
        self.name = name
        self.status = status  # "PASS", "WARN", "FAIL"
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()


class SetupValidator:
    """Comprehensive setup validation for the qualitative coding analysis tool"""
    
    def __init__(self):
        self.results = []
        self.project_root = Path(__file__).parent.parent
        self.required_python_version = (3, 8)
        self.required_packages = [
            'aiosqlite', 'google-generativeai', 'fastapi', 'uvicorn',
            'python-docx', 'pydantic', 'pyyaml', 'neo4j', 'pandas', 'openpyxl'
        ]
        self.optional_packages = [
            'pytest', 'black', 'flake8', 'mypy'
        ]
    
    def log_result(self, name: str, status: str, message: str, details: Dict[str, Any] = None):
        """Log a health check result"""
        result = HealthCheckResult(name, status, message, details)
        self.results.append(result)
        
        # Print status with color coding (basic)
        status_symbol = "✓" if status == "PASS" else "!" if status == "WARN" else "✗"
        print(f"[{status_symbol}] {name}: {message}")
        
        if details and status != "PASS":
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def check_python_version(self):
        """Check Python version compatibility"""
        current_version = sys.version_info[:2]
        required_version = self.required_python_version
        
        if current_version >= required_version:
            self.log_result(
                "Python Version",
                "PASS",
                f"Python {'.'.join(map(str, current_version))} (required: {'.'.join(map(str, required_version))}+)",
                {"version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"}
            )
        else:
            self.log_result(
                "Python Version",
                "FAIL",
                f"Python {'.'.join(map(str, current_version))} is too old (required: {'.'.join(map(str, required_version))}+)",
                {"current": f"{current_version[0]}.{current_version[1]}", 
                 "required": f"{required_version[0]}.{required_version[1]}"}
            )
    
    def check_project_structure(self):
        """Verify project directory structure"""
        required_dirs = [
            "src/qc",
            "config",
            "data",
            "outputs",
            "scripts",
            "tests"
        ]
        
        required_files = [
            "requirements.txt",
            "README.md",
            "src/qc/__init__.py",
            "src/qc/cli.py"
        ]
        
        missing_dirs = []
        missing_files = []
        
        # Check directories
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        # Check files
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if not missing_dirs and not missing_files:
            self.log_result(
                "Project Structure",
                "PASS",
                "All required directories and files present"
            )
        else:
            status = "WARN" if not missing_files else "FAIL"
            message = "Missing project components"
            details = {}
            if missing_dirs:
                details["missing_directories"] = missing_dirs
            if missing_files:
                details["missing_files"] = missing_files
            
            self.log_result("Project Structure", status, message, details)
    
    def check_dependencies(self):
        """Check Python package dependencies"""
        installed_packages = {}
        missing_packages = []
        version_issues = []
        
        # Check required packages
        for package in self.required_packages:
            try:
                # Handle special cases for imports
                if package == 'google-generativeai':
                    module = importlib.import_module('google.generativeai')
                elif package == 'python-docx':
                    module = importlib.import_module('docx')
                elif package == 'pyyaml':
                    module = importlib.import_module('yaml')
                else:
                    module = importlib.import_module(package.replace('-', '_'))
                    
                version = getattr(module, '__version__', 'unknown')
                installed_packages[package] = version
            except ImportError:
                missing_packages.append(package)
        
        # Check optional packages
        optional_installed = {}
        for package in self.optional_packages:
            try:
                module = importlib.import_module(package.replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
                optional_installed[package] = version
            except ImportError:
                pass  # Optional packages are okay to miss
        
        if not missing_packages:
            self.log_result(
                "Required Dependencies",
                "PASS",
                f"All {len(self.required_packages)} required packages installed",
                {"installed": installed_packages}
            )
        else:
            self.log_result(
                "Required Dependencies",
                "FAIL",
                f"Missing {len(missing_packages)} required packages",
                {"missing": missing_packages, "installed": installed_packages}
            )
        
        if optional_installed:
            self.log_result(
                "Optional Dependencies",
                "PASS",
                f"{len(optional_installed)} optional packages installed",
                {"installed": optional_installed}
            )
        else:
            self.log_result(
                "Optional Dependencies",
                "WARN",
                "No optional development packages installed",
                {"available": self.optional_packages}
            )
    
    def check_environment_variables(self):
        """Check environment configuration"""
        required_env_vars = []  # None absolutely required
        recommended_env_vars = [
            "GEMINI_API_KEY",
            "NEO4J_URI",
            "NEO4J_USERNAME",
            "NEO4J_PASSWORD"
        ]
        
        missing_recommended = []
        configured_vars = {}
        
        for var in recommended_env_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if "KEY" in var or "PASSWORD" in var or "TOKEN" in var:
                    configured_vars[var] = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                else:
                    configured_vars[var] = value
            else:
                missing_recommended.append(var)
        
        if len(configured_vars) >= 1:  # At least one configured
            self.log_result(
                "Environment Variables",
                "PASS",
                f"{len(configured_vars)} environment variables configured",
                {"configured": configured_vars}
            )
        else:
            self.log_result(
                "Environment Variables",
                "WARN",
                "No recommended environment variables configured",
                {"missing": missing_recommended, "info": "System can use defaults"}
            )
        
        if missing_recommended:
            self.log_result(
                "Environment Setup",
                "WARN", 
                f"{len(missing_recommended)} recommended variables not set",
                {"missing": missing_recommended, "note": "See .env.example for guidance"}
            )
    
    def check_file_permissions(self):
        """Check file and directory permissions"""
        permission_issues = []
        
        # Check write permissions for key directories
        write_dirs = ["data", "outputs", "data/exports", "logs"]
        
        for dir_name in write_dirs:
            dir_path = self.project_root / dir_name
            
            # Create directory if it doesn't exist
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                permission_issues.append(f"Cannot create {dir_name}: {e}")
                continue
            
            # Test write permission
            test_file = dir_path / "permission_test.tmp"
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                test_file.unlink()  # Delete test file
            except Exception as e:
                permission_issues.append(f"Cannot write to {dir_name}: {e}")
        
        if not permission_issues:
            self.log_result(
                "File Permissions",
                "PASS",
                "All required directories writable"
            )
        else:
            self.log_result(
                "File Permissions",
                "FAIL",
                f"{len(permission_issues)} permission issues found",
                {"issues": permission_issues}
            )
    
    async def check_system_connectivity(self):
        """Test system connectivity and external services"""
        connectivity_results = {}
        
        # Test Neo4j connectivity (if configured)
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        try:
            # Basic connection test without full setup
            import neo4j
            driver = neo4j.AsyncGraphDatabase.driver(
                neo4j_uri,
                auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
                if os.getenv("NEO4J_USERNAME") else None
            )
            
            async with driver.session() as session:
                result = await session.run("RETURN 1 as test")
                await result.single()
            
            await driver.close()
            connectivity_results["neo4j"] = "PASS"
            
        except Exception as e:
            connectivity_results["neo4j"] = f"FAIL: {str(e)[:100]}"
        
        # Test Gemini API (if configured)
        if os.getenv("GEMINI_API_KEY"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                
                # Simple test - just initialize, don't make actual API call
                model = genai.GenerativeModel('gemini-pro')
                connectivity_results["gemini"] = "CONFIGURED"
                
            except Exception as e:
                connectivity_results["gemini"] = f"FAIL: {str(e)[:100]}"
        else:
            connectivity_results["gemini"] = "NOT_CONFIGURED"
        
        # Evaluate results
        if connectivity_results.get("neo4j") == "PASS":
            self.log_result(
                "Neo4j Connectivity",
                "PASS",
                "Successfully connected to Neo4j database"
            )
        else:
            self.log_result(
                "Neo4j Connectivity",
                "WARN",
                "Cannot connect to Neo4j database",
                {"details": connectivity_results.get("neo4j", "Not tested"),
                 "info": "Demo mode and file-based operations will still work"}
            )
        
        if connectivity_results.get("gemini") == "CONFIGURED":
            self.log_result(
                "LLM API Configuration",
                "PASS",
                "Gemini API key configured"
            )
        else:
            self.log_result(
                "LLM API Configuration",
                "WARN",
                "Gemini API not configured",
                {"info": "Set GEMINI_API_KEY environment variable for full functionality"}
            )
    
    def check_sample_data(self):
        """Check if sample data is available for testing"""
        sample_paths = [
            "outputs/current/README.md",
            "outputs/current/taxonomy.json",
            "outputs/current/interviews"
        ]
        
        available_samples = []
        missing_samples = []
        
        for sample_path in sample_paths:
            full_path = self.project_root / sample_path
            if full_path.exists():
                if full_path.is_dir():
                    # Count files in directory
                    file_count = len(list(full_path.glob("*.json")))
                    available_samples.append(f"{sample_path} ({file_count} files)")
                else:
                    available_samples.append(sample_path)
            else:
                missing_samples.append(sample_path)
        
        if available_samples:
            self.log_result(
                "Sample Data",
                "PASS",
                "Sample analysis data available for testing",
                {"available": available_samples}
            )
        else:
            self.log_result(
                "Sample Data",
                "WARN",
                "No sample data found",
                {"missing": missing_samples, 
                 "info": "Run analysis or demo setup to generate sample data"}
            )
    
    def test_basic_functionality(self):
        """Test basic system functionality"""
        try:
            # Test CLI import
            sys.path.insert(0, str(self.project_root))
            from src.qc.cli import QualitativeCodingCLI
            
            # Test basic initialization
            cli = QualitativeCodingCLI()
            
            # Test export functionality (doesn't need database)
            from src.qc.export.data_exporter import DataExporter
            exporter = DataExporter()
            
            self.log_result(
                "Basic Functionality",
                "PASS",
                "Core system components can be imported and initialized"
            )
            
        except Exception as e:
            self.log_result(
                "Basic Functionality",
                "FAIL",
                f"Core system initialization failed: {str(e)[:200]}",
                {"error": str(e)}
            )
    
    def generate_system_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        passed = sum(1 for r in self.results if r.status == "PASS")
        warned = sum(1 for r in self.results if r.status == "WARN")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        
        system_info = {
            "platform": platform.platform(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "timestamp": datetime.now().isoformat()
        }
        
        report = {
            "summary": {
                "total_checks": len(self.results),
                "passed": passed,
                "warnings": warned,
                "failed": failed,
                "overall_status": "READY" if failed == 0 else "ISSUES" if warned > 0 else "NOT_READY"
            },
            "system_info": system_info,
            "check_results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp
                }
                for r in self.results
            ]
        }
        
        return report
    
    async def run_all_checks(self, save_report: bool = True) -> Dict[str, Any]:
        """Run all health checks"""
        print("Running qualitative coding analysis tool setup validation...\n")
        
        # Core system checks
        self.check_python_version()
        self.check_project_structure()
        self.check_dependencies()
        self.check_environment_variables()
        self.check_file_permissions()
        
        # Connectivity and functionality checks
        await self.check_system_connectivity()
        self.check_sample_data()
        self.test_basic_functionality()
        
        # Generate report
        report = self.generate_system_report()
        
        # Print summary
        print(f"\n{'='*60}")
        print("SETUP VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Checks: {report['summary']['total_checks']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Warnings: {report['summary']['warnings']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Overall Status: {report['summary']['overall_status']}")
        
        # Recommendations
        if report['summary']['failed'] > 0:
            print(f"\n⚠️  SETUP ISSUES DETECTED")
            print("Fix the failed checks before using the system.")
        elif report['summary']['warnings'] > 0:
            print(f"\n✓ SYSTEM READY (with warnings)")
            print("System is functional but some features may be limited.")
        else:
            print(f"\n✅ SYSTEM READY")
            print("All checks passed - system is fully functional.")
        
        # Save report
        if save_report:
            report_dir = self.project_root / "logs"
            report_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = report_dir / f"setup_validation_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\nDetailed report saved to: {report_file}")
        
        return report


async def main():
    """Main entry point for setup validation"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate setup for Qualitative Coding Analysis Tool"
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Don't save validation report to file"
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Run only essential checks (faster)"
    )
    
    args = parser.parse_args()
    
    validator = SetupValidator()
    
    try:
        report = await validator.run_all_checks(save_report=not args.no_save)
        
        # Exit with appropriate code
        if report['summary']['failed'] > 0:
            sys.exit(1)  # Issues that prevent functionality
        elif report['summary']['warnings'] > 0:
            sys.exit(2)  # Warnings but system functional
        else:
            sys.exit(0)  # All good
    
    except KeyboardInterrupt:
        print("\nValidation interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nValidation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
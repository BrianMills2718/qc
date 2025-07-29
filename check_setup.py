"""
Check setup and environment for qualitative coding project.
"""
import os
import sys
from pathlib import Path

def check_environment():
    """Check all required environment variables and dependencies."""
    print("=== Qualitative Coding Setup Check ===\n")
    
    issues = []
    
    # Check Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        issues.append("Python 3.8+ required")
    
    # Check environment variables
    print("\nEnvironment Variables:")
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        print(f"✓ GEMINI_API_KEY: Set ({len(gemini_key)} chars)")
    else:
        print("✗ GEMINI_API_KEY: Not set")
        issues.append("GEMINI_API_KEY not set")
    
    # Check optional env vars
    optional_vars = {
        'GEMINI_MODEL': 'gemini-2.5-flash',
        'GEMINI_TEMPERATURE': '0.3',
        'GEMINI_MAX_OUTPUT_TOKENS': '60000',
        'RESEARCH_QUESTION': 'How are AI methods being integrated into qualitative research practices?'
    }
    
    print("\nOptional Settings:")
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        print(f"  {var}: {value}")
    
    # Check dependencies
    print("\nDependencies:")
    required_packages = [
        'google-genai',
        'pydantic',
        'python-docx',
        'tiktoken',
        'numpy',
        'pandas'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}: Installed")
        except ImportError:
            print(f"✗ {package}: Not installed")
            issues.append(f"{package} not installed")
    
    # Check data directory
    print("\nData Directory:")
    data_dir = Path(__file__).parent / "data" / "interviews"
    if data_dir.exists():
        # Count DOCX files
        docx_files = list(data_dir.rglob("*.docx"))
        print(f"✓ Interview directory exists: {data_dir}")
        print(f"✓ Interview files found: {len(docx_files)}")
        
        if len(docx_files) == 103:
            print("✓ Expected 103 interviews: Confirmed")
        else:
            print(f"⚠ Expected 103 interviews, found {len(docx_files)}")
    else:
        print(f"✗ Interview directory not found: {data_dir}")
        issues.append("Interview data directory not found")
    
    # Check output directory
    print("\nOutput Directory:")
    output_dir = Path(__file__).parent / "output"
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        print(f"✓ Created output directory: {output_dir}")
    else:
        print(f"✓ Output directory exists: {output_dir}")
    
    # Summary
    print("\n" + "=" * 50)
    if issues:
        print("✗ Setup Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease fix these issues before running the analysis.")
    else:
        print("✓ All checks passed! Ready to run analysis.")
        print("\nNext steps:")
        print("1. Run sample test: python test_global_analysis.py")
        print("2. Or run directly: python -m qc.core.global_qualitative_analyzer")
    
    return len(issues) == 0


if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)
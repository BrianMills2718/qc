#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Setup Script
Quickly sets up the qualitative coding analysis tool with pre-loaded sample data
"""
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class DemoSetup:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.demo_data_dir = self.root_dir / "outputs" / "current"
        self.required_files = [
            "taxonomy.json",
            "speaker_schema.json", 
            "entity_schema.json",
            "extraction_results.json"
        ]
        
    def check_prerequisites(self) -> bool:
        """Check if demo data exists"""
        print("🔍 Checking demo prerequisites...")
        
        if not self.demo_data_dir.exists():
            print(f"❌ Demo data directory not found: {self.demo_data_dir}")
            return False
            
        missing_files = []
        for file_name in self.required_files:
            if not (self.demo_data_dir / file_name).exists():
                missing_files.append(file_name)
                
        if missing_files:
            print(f"❌ Missing demo files: {', '.join(missing_files)}")
            return False
            
        interviews_dir = self.demo_data_dir / "interviews"
        if not interviews_dir.exists() or not list(interviews_dir.glob("*.json")):
            print("❌ No interview analysis files found")
            return False
            
        print("✅ All demo prerequisites satisfied")
        return True
    
    def install_dependencies(self) -> bool:
        """Install required Python packages"""
        print("📦 Installing dependencies...")
        
        try:
            requirements_file = self.root_dir / "requirements.txt"
            if not requirements_file.exists():
                print("❌ requirements.txt not found")
                return False
                
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Failed to install dependencies: {result.stderr}")
                return False
                
            print("✅ Dependencies installed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def setup_environment(self) -> bool:
        """Set up environment variables"""
        print("🔧 Setting up environment...")
        
        env_example = self.root_dir / ".env.example"
        env_file = self.root_dir / ".env"
        
        if env_example.exists() and not env_file.exists():
            # Copy example env for demo
            shutil.copy2(env_example, env_file)
            print("✅ Environment file created from example")
        
        # Set demo-specific environment
        os.environ["QC_ENVIRONMENT"] = "demo"
        os.environ["QC_LOG_LEVEL"] = "INFO"
        os.environ["QC_WEB_HOST"] = "127.0.0.1"
        os.environ["QC_WEB_PORT"] = "8000"
        
        print("✅ Environment configured for demo")
        return True
    
    def display_demo_info(self) -> None:
        """Display information about the demo dataset"""
        try:
            # Load demo data
            taxonomy_file = self.demo_data_dir / "taxonomy.json"
            readme_file = self.demo_data_dir / "README.md"
            interviews_dir = self.demo_data_dir / "interviews"
            
            with open(taxonomy_file, "r") as f:
                taxonomy = json.load(f)
                
            interview_files = list(interviews_dir.glob("*.json"))
            
            print("\n" + "="*80)
            print("🎯 QUALITATIVE CODING ANALYSIS TOOL - DEMO SETUP COMPLETE")
            print("="*80)
            
            print("\n📊 PRE-LOADED ANALYSIS: AI Research Methods Investigation")
            print(f"   • {len(interview_files)} analyzed interviews")
            print(f"   • {len(taxonomy.get('codes', []))} discovered thematic codes")
            print("   • Complete entity relationship networks")
            print("   • Focus group dialogue analysis")
            
            print("\n🔍 Research Question:")
            print("   How are researchers experiencing and adapting to AI integration")
            print("   in qualitative research methods?")
            
            print("\n💡 Key Themes Discovered:")
            for code in taxonomy.get('codes', [])[:8]:  # Show first 8 themes
                print(f"   • {code.get('name', 'Unknown')}")
            if len(taxonomy.get('codes', [])) > 8:
                print(f"   • ... and {len(taxonomy['codes']) - 8} more themes")
            
            print("\n🌐 Next Steps:")
            print("   1. Start the demo server: python -m qc.cli serve")
            print("   2. Open your browser: http://localhost:8000")
            print("   3. Explore the pre-analyzed interview data")
            print("   4. Try the API at: http://localhost:8000/docs")
            
            print("\n📖 Demo Guide:")
            print("   • Full demo walkthrough: DEMO.md")
            print("   • User documentation: docs/user-guides/")
            print("   • Configuration help: docs/user-guides/CONFIGURATION_GUIDE.md")
            
            print("\n" + "="*80)
            print("🚀 Ready to launch! Run: python -m qc.cli serve")
            print("="*80)
            
        except Exception as e:
            print(f"⚠️  Could not load complete demo info: {e}")
            print("✅ Demo setup complete - start with: python -m qc.cli serve")
    
    def run_setup(self) -> bool:
        """Run complete demo setup"""
        print("🚀 Setting up Qualitative Coding Analysis Tool Demo...")
        print("="*60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Demo setup failed - missing required data")
            print("💡 Ensure you have run the full extraction pipeline first")
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            print("\n❌ Demo setup failed - dependency installation error")
            return False
            
        # Setup environment
        if not self.setup_environment():
            print("\n❌ Demo setup failed - environment configuration error")
            return False
        
        # Display info
        self.display_demo_info()
        
        return True


def main():
    """Main entry point"""
    demo = DemoSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check-only":
        # Just check prerequisites
        if demo.check_prerequisites():
            print("✅ Demo environment ready")
            sys.exit(0)
        else:
            print("❌ Demo environment not ready")
            sys.exit(1)
    
    success = demo.run_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
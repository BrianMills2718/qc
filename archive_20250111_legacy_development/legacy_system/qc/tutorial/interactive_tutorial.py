#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Tutorial System
Provides guided tutorials for new users of the qualitative coding analysis tool
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import tempfile

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class TutorialStep:
    """Represents a single step in the tutorial"""
    
    def __init__(self, 
                 title: str,
                 description: str,
                 action_type: str,
                 action_params: Dict[str, Any] = None,
                 validation_func: Callable = None,
                 expected_output: str = None,
                 help_text: str = None):
        self.title = title
        self.description = description
        self.action_type = action_type  # 'command', 'demo', 'explanation', 'validation'
        self.action_params = action_params or {}
        self.validation_func = validation_func
        self.expected_output = expected_output
        self.help_text = help_text
        self.completed = False
        self.start_time = None
        self.end_time = None


class InteractiveTutorial:
    """Main tutorial system with guided walkthroughs"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.tutorial_data_dir = self.project_root / "data" / "tutorial"
        self.tutorial_data_dir.mkdir(parents=True, exist_ok=True)
        self.current_tutorial = None
        self.current_step_index = 0
        self.progress = {}
        self.user_input_handler = self.default_input_handler
        self.auto_yes = False
    
    def default_input_handler(self, prompt: str) -> str:
        """Default input handler - can be overridden for testing"""
        if self.auto_yes:
            if "continue" in prompt.lower() or "ready" in prompt.lower():
                print("Auto-continuing...")
                return ""
            elif "(y/n)" in prompt.lower():
                print("Auto-answering: y")
                return "y"
            elif "skip" in prompt.lower():
                print("Auto-answering: <enter>")
                return ""
            else:
                print("Auto-continuing...")
                return ""
        return input(prompt)
    
    def display_welcome(self):
        """Display tutorial welcome message"""
        print("=" * 70)
        print("   Welcome to the Qualitative Coding Analysis Tool Tutorial!")
        print("=" * 70)
        print()
        print("This interactive tutorial will guide you through:")
        print("  * Setting up your environment")
        print("  * Running your first analysis") 
        print("  * Exploring the analysis results")
        print("  * Exporting data for further use")
        print("  * Using advanced features")
        print()
        print("Each step includes hands-on practice with real examples.")
        print("You can exit at any time by pressing Ctrl+C.")
        print()
    
    def display_step(self, step: TutorialStep, step_number: int, total_steps: int):
        """Display a tutorial step"""
        print(f"\n{'='*70}")
        print(f"Step {step_number}/{total_steps}: {step.title}")
        print(f"{'='*70}")
        print(f"\n{step.description}")
        
        if step.help_text:
            print(f"\n💡 Tip: {step.help_text}")
    
    def wait_for_user_ready(self, prompt: str = "Press Enter when ready to continue..."):
        """Wait for user to indicate they're ready"""
        self.user_input_handler(f"\n{prompt}")
    
    def execute_command_step(self, step: TutorialStep) -> bool:
        """Execute a command-based tutorial step"""
        command = step.action_params.get('command', '')
        working_dir = step.action_params.get('working_dir', str(self.project_root))
        show_command = step.action_params.get('show_command', True)
        auto_run = step.action_params.get('auto_run', False)
        
        if show_command:
            print(f"\n📋 Command to run:")
            print(f"   {command}")
            print(f"   (in directory: {working_dir})")
        
        if not auto_run:
            user_input = self.user_input_handler(
                "\nPress Enter to run this command, or type 'skip' to skip: "
            ).strip().lower()
            
            if user_input == 'skip':
                print("   ⏭️  Skipped this step")
                return True
        
        try:
            print(f"\n🚀 Running command...")
            print("-" * 50)
            
            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=False,  # Show output in real time
                text=True
            )
            
            print("-" * 50)
            
            if result.returncode == 0:
                print("✅ Command completed successfully!")
                return True
            else:
                print(f"❌ Command failed with exit code {result.returncode}")
                
                retry = self.user_input_handler(
                    "Would you like to retry this step? (y/n): "
                ).strip().lower()
                
                return retry != 'y'  # Return True if not retrying
                
        except Exception as e:
            print(f"❌ Error running command: {e}")
            return False
    
    def execute_demo_step(self, step: TutorialStep) -> bool:
        """Execute a demonstration step"""
        demo_type = step.action_params.get('demo_type', 'explanation')
        
        if demo_type == 'file_exploration':
            return self.demo_file_exploration(step)
        elif demo_type == 'result_analysis':
            return self.demo_result_analysis(step)
        elif demo_type == 'export_demonstration':
            return self.demo_export_functionality(step)
        else:
            print(f"\n{step.description}")
            self.wait_for_user_ready()
            return True
    
    def demo_file_exploration(self, step: TutorialStep) -> bool:
        """Demonstrate file exploration"""
        target_dir = self.project_root / step.action_params.get('target_dir', 'outputs/current')
        
        if not target_dir.exists():
            print(f"❌ Directory {target_dir} does not exist.")
            print("💡 You may need to run the demo setup first.")
            return False
        
        print(f"\n🔍 Let's explore the analysis results in: {target_dir}")
        print(f"\nDirectory contents:")
        
        for item in sorted(target_dir.iterdir()):
            if item.is_dir():
                file_count = len(list(item.glob("*")))
                print(f"   📁 {item.name}/ ({file_count} files)")
            else:
                size_kb = item.stat().st_size // 1024
                print(f"   📄 {item.name} ({size_kb} KB)")
        
        # Show a sample file if available
        sample_file = step.action_params.get('sample_file')
        if sample_file:
            sample_path = target_dir / sample_file
            if sample_path.exists():
                print(f"\n📖 Let's examine {sample_file}:")
                
                if sample_file.endswith('.json'):
                    try:
                        with open(sample_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        if isinstance(data, dict):
                            print(f"   📊 JSON file with {len(data)} top-level keys:")
                            for key in list(data.keys())[:5]:  # Show first 5 keys
                                print(f"      • {key}")
                            if len(data) > 5:
                                print(f"      • ... and {len(data) - 5} more")
                        elif isinstance(data, list):
                            print(f"   📊 JSON array with {len(data)} items")
                            
                    except Exception as e:
                        print(f"   ❌ Could not read JSON file: {e}")
                else:
                    # Show first few lines for text files
                    try:
                        with open(sample_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()[:10]
                        
                        print(f"   📄 First {len(lines)} lines:")
                        for i, line in enumerate(lines, 1):
                            print(f"   {i:2}: {line.rstrip()}")
                            
                        if len(lines) == 10:
                            print("   ...")
                            
                    except Exception as e:
                        print(f"   ❌ Could not read file: {e}")
        
        self.wait_for_user_ready()
        return True
    
    def demo_result_analysis(self, step: TutorialStep) -> bool:
        """Demonstrate analysis results"""
        results_dir = self.project_root / "outputs" / "current"
        
        if not results_dir.exists():
            print("❌ No analysis results found. Please run the demo setup first.")
            return False
        
        # Load and display taxonomy
        taxonomy_file = results_dir / "taxonomy.json"
        if taxonomy_file.exists():
            try:
                with open(taxonomy_file, 'r', encoding='utf-8') as f:
                    taxonomy = json.load(f)
                
                codes = taxonomy.get('codes', [])
                print(f"\n📊 Discovered {len(codes)} thematic codes:")
                
                # Show top-level codes
                top_level_codes = [c for c in codes if c.get('level', 0) == 0]
                
                for code in top_level_codes[:8]:  # Show first 8
                    name = code.get('name', 'Unknown')
                    description = code.get('description', 'No description')
                    confidence = code.get('discovery_confidence', 0)
                    
                    print(f"   • {name}")
                    print(f"     {description[:80]}{'...' if len(description) > 80 else ''}")
                    print(f"     (Confidence: {confidence:.2f})")
                    print()
                
                if len(top_level_codes) > 8:
                    print(f"   ... and {len(top_level_codes) - 8} more top-level codes")
                
            except Exception as e:
                print(f"❌ Could not analyze taxonomy: {e}")
        
        # Show interview summary
        interviews_dir = results_dir / "interviews"
        if interviews_dir.exists():
            interview_files = list(interviews_dir.glob("*.json"))
            print(f"\n📝 Analysis includes {len(interview_files)} interviews:")
            
            for interview_file in interview_files:
                try:
                    with open(interview_file, 'r', encoding='utf-8') as f:
                        interview_data = json.load(f)
                    
                    interview_id = interview_data.get('interview_id', interview_file.stem)
                    quotes_count = len(interview_data.get('quotes', []))
                    
                    print(f"   • {interview_id}: {quotes_count} coded quotes")
                    
                except Exception as e:
                    print(f"   • {interview_file.name}: (could not read)")
        
        self.wait_for_user_ready()
        return True
    
    def demo_export_functionality(self, step: TutorialStep) -> bool:
        """Demonstrate export functionality"""
        export_dir = self.project_root / "data" / "exports"
        
        print(f"\n📤 Export functionality allows you to save analysis results in various formats:")
        print(f"   • CSV files (compatible with Excel, R, SPSS)")
        print(f"   • Excel workbooks (multiple sheets)")
        print(f"   • Separate files for quotes, codes, speakers, entities")
        
        if export_dir.exists():
            export_files = list(export_dir.glob("*"))
            if export_files:
                print(f"\n📁 Current export files ({len(export_files)} found):")
                for export_file in sorted(export_files)[-5:]:  # Show last 5
                    size_kb = export_file.stat().st_size // 1024
                    print(f"   • {export_file.name} ({size_kb} KB)")
        
        demo_export = self.user_input_handler(
            "\nWould you like to run a quick export demo? (y/n): "
        ).strip().lower()
        
        if demo_export == 'y':
            print("\n🚀 Running demo export...")
            
            try:
                result = subprocess.run([
                    sys.executable, "-m", "src.qc.cli", "export", "csv",
                    "--input", "outputs/current",
                    "--output", "tutorial_demo",
                    "--components", "quotes", "codes"
                ], 
                cwd=str(self.project_root),
                capture_output=True,
                text=True
                )
                
                if result.returncode == 0:
                    print("✅ Export completed successfully!")
                    print("   Files created in data/exports/")
                else:
                    print(f"❌ Export failed: {result.stderr}")
                    
            except Exception as e:
                print(f"❌ Export error: {e}")
        
        self.wait_for_user_ready()
        return True
    
    def create_beginner_tutorial(self) -> List[TutorialStep]:
        """Create the beginner tutorial sequence"""
        return [
            TutorialStep(
                title="System Health Check",
                description="Let's start by checking that your system is properly configured.",
                action_type="command",
                action_params={
                    'command': f"{sys.executable} scripts/validate_setup.py --no-save",
                    'show_command': True,
                    'auto_run': False
                },
                help_text="This validates dependencies, file permissions, and system configuration."
            ),
            
            TutorialStep(
                title="Demo Environment Setup",
                description="Now let's set up the demo environment with pre-analyzed sample data.",
                action_type="command",
                action_params={
                    'command': f"{sys.executable} scripts/demo_setup.py",
                    'show_command': True,
                    'auto_run': False
                },
                help_text="This creates sample analysis results that you can explore and export."
            ),
            
            TutorialStep(
                title="Explore Analysis Results",
                description="Let's examine the structure and contents of analysis results.",
                action_type="demo",
                action_params={
                    'demo_type': 'file_exploration',
                    'target_dir': 'outputs/current',
                    'sample_file': 'taxonomy.json'
                },
                help_text="Understanding the file structure helps you navigate results effectively."
            ),
            
            TutorialStep(
                title="Understanding Discovered Themes",
                description="Now let's explore the thematic codes and patterns discovered in the analysis.",
                action_type="demo",
                action_params={
                    'demo_type': 'result_analysis'
                },
                help_text="These codes represent the key themes and patterns found in your interview data."
            ),
            
            TutorialStep(
                title="Export Data for External Analysis",
                description="Learn how to export analysis results to CSV and Excel formats.",
                action_type="demo",
                action_params={
                    'demo_type': 'export_demonstration'
                },
                help_text="Exported data can be used in Excel, R, SPSS, or other analysis tools."
            ),
            
            TutorialStep(
                title="Web Interface Introduction",
                description="Finally, let's explore the web interface for interactive analysis.",
                action_type="command",
                action_params={
                    'command': f"{sys.executable} -m src.qc.cli serve --host 127.0.0.1 --port 8000",
                    'show_command': True,
                    'auto_run': False
                },
                help_text="The web interface provides interactive browsing and visualization. Access at http://localhost:8000"
            )
        ]
    
    def create_advanced_tutorial(self) -> List[TutorialStep]:
        """Create the advanced tutorial sequence"""
        return [
            TutorialStep(
                title="Custom Analysis Configuration",
                description="Learn how to configure the analysis for your specific research needs.",
                action_type="explanation",
                help_text="Configuration files allow you to customize code discovery, validation rules, and output formats."
            ),
            
            TutorialStep(
                title="Processing Your Own Data",
                description="Walk through analyzing your own interview files.",
                action_type="explanation",
                help_text="The system supports Word documents, text files, and various interview formats."
            ),
            
            TutorialStep(
                title="Quality Assurance and Validation",
                description="Understand validation options and quality control features.",
                action_type="explanation",
                help_text="Quality controls ensure reliable and reproducible analysis results."
            ),
            
            TutorialStep(
                title="Integration with External Tools",
                description="Learn how to integrate with R, MAXQDA, NVivo, and other research tools.",
                action_type="explanation",
                help_text="Export formats are designed for seamless integration with your existing workflow."
            )
        ]
    
    def run_tutorial(self, tutorial_type: str = "beginner"):
        """Run a complete tutorial"""
        try:
            self.display_welcome()
            
            if tutorial_type == "beginner":
                steps = self.create_beginner_tutorial()
                tutorial_name = "Beginner Tutorial"
            elif tutorial_type == "advanced":
                steps = self.create_advanced_tutorial()
                tutorial_name = "Advanced Tutorial"
            else:
                print(f"❌ Unknown tutorial type: {tutorial_type}")
                return False
            
            print(f"Starting: {tutorial_name}")
            print(f"Total steps: {len(steps)}")
            
            # Run tutorial steps
            for i, step in enumerate(steps, 1):
                step.start_time = datetime.now()
                
                self.display_step(step, i, len(steps))
                
                success = False
                if step.action_type == "command":
                    success = self.execute_command_step(step)
                elif step.action_type == "demo":
                    success = self.execute_demo_step(step)
                elif step.action_type == "explanation":
                    print(f"\n{step.description}")
                    if step.help_text:
                        print(f"\n💡 {step.help_text}")
                    self.wait_for_user_ready()
                    success = True
                
                step.end_time = datetime.now()
                step.completed = success
                
                if not success:
                    retry = self.user_input_handler(
                        f"\nStep {i} encountered issues. Continue anyway? (y/n): "
                    ).strip().lower()
                    
                    if retry != 'y':
                        print("Tutorial stopped by user.")
                        return False
            
            # Tutorial completion
            completed_steps = sum(1 for step in steps if step.completed)
            print(f"\n{'='*70}")
            print(f"🎉 Tutorial Complete!")
            print(f"{'='*70}")
            print(f"Completed: {completed_steps}/{len(steps)} steps")
            
            if completed_steps == len(steps):
                print("✅ Congratulations! You've successfully completed the tutorial.")
                print("   You're ready to start using the Qualitative Coding Analysis Tool.")
            else:
                print("⚠️  Some steps had issues, but you can still use the system.")
                print("   Review the setup validation if you encounter problems.")
            
            print(f"\n📚 Next steps:")
            print(f"   • Check the README.md for detailed documentation")
            print(f"   • Run health_check.bat (Windows) or health_check.sh (Unix) anytime")
            print(f"   • Use 'python -m src.qc.cli --help' for command reference")
            print(f"   • Visit http://localhost:8000 for the web interface")
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n\nTutorial interrupted by user.")
            print(f"You can restart anytime with: python scripts/tutorial.py")
            return False
        except Exception as e:
            print(f"\n❌ Tutorial error: {e}")
            return False
    
    def run_beginner_tutorial(self):
        """Run the beginner tutorial"""
        return self.run_tutorial("beginner")
    
    def run_advanced_tutorial(self):
        """Run the advanced tutorial"""
        return self.run_tutorial("advanced")
    
    def run_demo_tutorial(self):
        """Run a quick demo tutorial focusing on setup and exploration"""
        print("🎮 Demo Tutorial - Quick Start")
        print("=" * 40)
        print()
        
        steps = [
            TutorialStep(
                title="Demo Environment Setup",
                description="Set up the demo environment with sample data.",
                action_type="command",
                action_params={
                    'command': f"{sys.executable} scripts/demo_setup.py",
                    'auto_run': self.auto_yes
                }
            ),
            TutorialStep(
                title="Explore Results",
                description="Explore the demo analysis results.",
                action_type="demo",
                action_params={
                    'demo_type': 'file_exploration',
                    'target_dir': 'outputs/current',
                    'sample_file': 'taxonomy.json'
                }
            )
        ]
        
        return self._run_tutorial_steps(steps, "Demo Tutorial")
    
    def run_export_tutorial(self):
        """Run tutorial focused on export functionality"""
        print("📊 Export Tutorial - Data Export and Analysis")
        print("=" * 50)
        print()
        
        steps = [
            TutorialStep(
                title="Export Functionality Demo",
                description="Learn about data export capabilities.",
                action_type="demo",
                action_params={
                    'demo_type': 'export_demonstration'
                }
            ),
            TutorialStep(
                title="Export Sample Data",
                description="Export sample data to CSV format.",
                action_type="command",
                action_params={
                    'command': f"{sys.executable} -m src.qc.cli export csv --input outputs/current --output tutorial_export --components quotes codes",
                    'auto_run': self.auto_yes
                }
            )
        ]
        
        return self._run_tutorial_steps(steps, "Export Tutorial")
    
    def run_setup_tutorial(self):
        """Run tutorial focused on system setup and validation"""
        print("⚙️ Setup Tutorial - System Configuration")
        print("=" * 45)
        print()
        
        steps = [
            TutorialStep(
                title="System Health Check",
                description="Validate system configuration and dependencies.",
                action_type="command",
                action_params={
                    'command': f"{sys.executable} scripts/validate_setup.py --no-save",
                    'auto_run': self.auto_yes
                }
            )
        ]
        
        return self._run_tutorial_steps(steps, "Setup Tutorial")
    
    def _run_tutorial_steps(self, steps: List[TutorialStep], tutorial_name: str):
        """Helper method to run a list of tutorial steps"""
        try:
            print(f"Starting: {tutorial_name}")
            print(f"Total steps: {len(steps)}")
            print()
            
            for i, step in enumerate(steps, 1):
                step.start_time = datetime.now()
                
                self.display_step(step, i, len(steps))
                
                success = False
                if step.action_type == "command":
                    success = self.execute_command_step(step)
                elif step.action_type == "demo":
                    success = self.execute_demo_step(step)
                elif step.action_type == "explanation":
                    print(f"\n{step.description}")
                    if step.help_text:
                        print(f"\n💡 {step.help_text}")
                    self.wait_for_user_ready()
                    success = True
                
                step.end_time = datetime.now()
                step.completed = success
                
                if not success and not self.auto_yes:
                    retry = self.user_input_handler(
                        f"\nStep {i} encountered issues. Continue anyway? (y/n): "
                    ).strip().lower()
                    
                    if retry != 'y':
                        print("Tutorial stopped by user.")
                        return False
            
            # Tutorial completion
            completed_steps = sum(1 for step in steps if step.completed)
            print(f"\n{'='*50}")
            print(f"🎉 {tutorial_name} Complete!")
            print(f"{'='*50}")
            print(f"Completed: {completed_steps}/{len(steps)} steps")
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n\n{tutorial_name} interrupted by user.")
            return False
        except Exception as e:
            print(f"\n❌ {tutorial_name} error: {e}")
            return False


def main():
    """Main entry point for the tutorial system"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Interactive Tutorial for Qualitative Coding Analysis Tool"
    )
    parser.add_argument(
        "tutorial_type", 
        nargs="?", 
        default="beginner",
        choices=["beginner", "advanced"],
        help="Type of tutorial to run (default: beginner)"
    )
    
    args = parser.parse_args()
    
    tutorial = InteractiveTutorial()
    success = tutorial.run_tutorial(args.tutorial_type)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
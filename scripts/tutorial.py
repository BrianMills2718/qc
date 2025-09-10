#!/usr/bin/env python3
"""
Interactive Tutorial Entry Point
Entry script for the comprehensive qualitative coding tutorial system.
"""

import sys
import os
import argparse
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

try:
    from qc.tutorial.interactive_tutorial import InteractiveTutorial
except ImportError as e:
    print("Error: Could not import tutorial system.")
    print("Please ensure you're running from the project root directory.")
    print(f"Import error: {e}")
    sys.exit(1)


def main():
    """Main tutorial entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive Qualitative Coding Analysis Tutorial",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Tutorial Options:
  beginner    - Complete beginner walkthrough with system setup
  advanced    - Advanced features and analysis techniques
  demo        - Quick demo environment setup and exploration
  export      - Export functionality and data formats
  setup       - System setup and validation only

Examples:
  python scripts/tutorial.py                 # Interactive menu selection
  python scripts/tutorial.py beginner        # Beginner tutorial
  python scripts/tutorial.py --skip-intro    # Skip introduction
        """
    )
    
    parser.add_argument(
        'tutorial_type',
        nargs='?',
        choices=['beginner', 'advanced', 'demo', 'export', 'setup'],
        help='Type of tutorial to run (if not specified, shows interactive menu)'
    )
    
    parser.add_argument(
        '--skip-intro',
        action='store_true',
        help='Skip the introduction and jump directly to tutorial'
    )
    
    parser.add_argument(
        '--auto-yes',
        action='store_true',
        help='Automatically answer yes to all prompts (for automated testing)'
    )
    
    args = parser.parse_args()
    
    # Initialize tutorial system
    tutorial = InteractiveTutorial()
    
    if not args.skip_intro:
        print_introduction()
    
    try:
        if args.tutorial_type:
            # Run specific tutorial type
            run_specific_tutorial(tutorial, args.tutorial_type, args.auto_yes)
        else:
            # Show interactive menu
            run_interactive_menu(tutorial, args.auto_yes)
            
    except KeyboardInterrupt:
        print("\n\nTutorial interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError during tutorial: {e}")
        print("Please check the system setup and try again.")
        sys.exit(1)


def print_introduction():
    """Print tutorial introduction."""
    print("=" * 70)
    print("🎓 QUALITATIVE CODING ANALYSIS TUTORIAL")
    print("=" * 70)
    print()
    print("Welcome to the comprehensive tutorial for the Qualitative Coding")
    print("Analysis system. This tutorial will guide you through:")
    print()
    print("• System setup and validation")
    print("• Demo environment creation")
    print("• Analysis workflows")
    print("• Export and visualization options")
    print("• Advanced features and customization")
    print()
    print("Choose your learning path below, or press Ctrl+C to exit.")
    print()


def run_interactive_menu(tutorial, auto_yes=False):
    """Run interactive menu for tutorial selection."""
    while True:
        print("📚 TUTORIAL MENU")
        print("-" * 20)
        print("1. 🚀 Beginner Tutorial (complete walkthrough)")
        print("2. 🔬 Advanced Tutorial (expert features)")
        print("3. 🎮 Demo Environment (quick start)")
        print("4. 📊 Export Tutorial (data export options)")
        print("5. ⚙️  System Setup (validation only)")
        print("6. ❌ Exit")
        print()
        
        if auto_yes:
            choice = "1"
            print(f"Auto-selecting option {choice}")
        else:
            choice = input("Select an option (1-6): ").strip()
        
        if choice == "1":
            tutorial.run_beginner_tutorial()
            break
        elif choice == "2":
            tutorial.run_advanced_tutorial()
            break
        elif choice == "3":
            tutorial.run_demo_tutorial()
            break
        elif choice == "4":
            tutorial.run_export_tutorial()
            break
        elif choice == "5":
            tutorial.run_setup_tutorial()
            break
        elif choice == "6":
            print("Goodbye! 👋")
            break
        else:
            print("Invalid choice. Please select 1-6.")
            print()


def run_specific_tutorial(tutorial, tutorial_type, auto_yes=False):
    """Run a specific tutorial type."""
    tutorial_map = {
        'beginner': tutorial.run_beginner_tutorial,
        'advanced': tutorial.run_advanced_tutorial,
        'demo': tutorial.run_demo_tutorial,
        'export': tutorial.run_export_tutorial,
        'setup': tutorial.run_setup_tutorial
    }
    
    if auto_yes:
        # Set auto-yes mode for automated testing
        tutorial.auto_yes = True
    
    print(f"🎯 Running {tutorial_type.title()} Tutorial")
    print("=" * 50)
    print()
    
    tutorial_map[tutorial_type]()


if __name__ == "__main__":
    main()
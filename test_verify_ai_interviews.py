#!/usr/bin/env python3
"""
Quick test to verify we're loading AI interviews
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.global_qualitative_analyzer import GlobalQualitativeAnalyzer

def main():
    analyzer = GlobalQualitativeAnalyzer()
    
    print(f"Research question: {analyzer.research_question}")
    print(f"\nNumber of interview files found: {len(analyzer.interview_files)}")
    
    if analyzer.interview_files:
        print("\nFirst 5 interview files:")
        for i, file in enumerate(analyzer.interview_files[:5]):
            print(f"{i+1}. {file.name}")
        
        # Check if these are AI interviews
        ai_count = sum(1 for f in analyzer.interview_files if 'AI' in f.name or 'Methods' in f.name)
        africa_count = sum(1 for f in analyzer.interview_files if 'africa' in str(f).lower())
        
        print(f"\nAI/Methods interviews: {ai_count}")
        print(f"Africa interviews: {africa_count}")
        
        if ai_count > 0 and africa_count == 0:
            print("\n✅ SUCCESS: Loading AI interviews only!")
        else:
            print("\n❌ ERROR: Wrong interviews loaded!")
    else:
        print("\n❌ ERROR: No interview files found!")

if __name__ == "__main__":
    main()
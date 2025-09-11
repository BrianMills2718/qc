#!/usr/bin/env python3
"""
QCA Analysis Entry Point
Post-processing pipeline for Qualitative Comparative Analysis

Usage:
    python run_qca_analysis.py qca_config.yaml
    python run_qca_analysis.py --help

This script runs QCA post-processing on completed qualitative coding extraction results.

Phases:
    QCA-1: Code to Set Membership Calibration
    QCA-2: Truth Table Construction  
    QCA-3: Boolean Minimization Integration
"""
import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def setup_logging(verbose: bool = False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # QCA module logger
    qca_logger = logging.getLogger('src.qc.qca')
    qca_logger.setLevel(level)

def print_banner():
    """Print QCA analysis banner"""
    print("=" * 80)
    print("QCA (Qualitative Comparative Analysis) Post-Processing Pipeline")
    print("Converting qualitative coding results to configurational analysis")
    print("=" * 80)
    print()

def validate_config_file(config_file: str) -> Path:
    """Validate configuration file exists"""
    config_path = Path(config_file)
    
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)
    
    if not config_path.suffix.lower() in ['.yaml', '.yml']:
        print(f"Error: Configuration file must be YAML format (.yaml or .yml)")
        sys.exit(1)
    
    return config_path

def create_example_config():
    """Create an example QCA configuration file"""
    example_config = """# QCA Analysis Configuration Example
# Post-processing configuration for Qualitative Comparative Analysis

# Input/Output Settings
input_dir: "output_production"  # Directory with coded interview JSON files
output_dir: "qca_analysis"      # Output directory for QCA results

# Conditions Definition (based on your extracted codes)
conditions:
  - condition_id: "ai_adoption"
    name: "AI Adoption"
    description: "High adoption of AI tools in research workflow"
    source_type: "code"  # Options: code, speaker_property, entity, relationship
    source_id: "AI_ADOPTION_AND_INTEGRATION"  # Must match your taxonomy
    calibration:
      method: "frequency"  # Options: binary, frequency, fuzzy, percentile
      frequency_breakpoints: [1, 3, 5]  # Occurrence thresholds
      frequency_thresholds:
        rare: 0.2
        moderate: 0.5
        frequent: 0.8

  - condition_id: "efficiency_focus"
    name: "Efficiency Focus"
    description: "Focus on AI for efficiency gains"
    source_type: "code"
    source_id: "EFFICIENCY_AND_PRODUCTIVITY_GAINS"
    calibration:
      method: "binary"
      binary_threshold: 2  # Present if >= 2 occurrences

  - condition_id: "concerns"
    name: "AI Concerns"
    description: "Concerns about AI limitations or risks"
    source_type: "code"
    source_id: "CHALLENGES_AND_LIMITATIONS"
    calibration:
      method: "fuzzy"
      fuzzy_function: "min(count / 5, 1.0)"  # Fuzzy membership based on count

# Outcomes Definition
outcomes:
  - outcome_id: "positive_ai_experience"
    name: "Positive AI Experience"
    description: "Overall positive experience with AI integration"
    source_conditions: ["ai_adoption", "efficiency_focus"]
    combination_rule: "any"  # Options: any, all, or Python expression
    calibration:
      method: "binary"
      binary_threshold: 1

# Phase Control
enable_calibration: true    # Phase QCA-1
enable_truth_table: true    # Phase QCA-2  
enable_minimization: true   # Phase QCA-3

# Advanced Settings
minimum_membership_threshold: 0.5
case_id_field: "interview_id"

# External Tool Integration
r_qca_package: true      # Generate R scripts for QCA package
python_qca: true         # Generate Python analysis scripts
neo4j_export: true       # Generate Neo4j Cypher queries
"""
    
    with open("qca_config_example.yaml", "w") as f:
        f.write(example_config)
    
    print("Created example configuration file: qca_config_example.yaml")
    print("Edit this file to match your extraction results and research questions.")

def main():
    parser = argparse.ArgumentParser(
        description="QCA Post-Processing Pipeline for Qualitative Coding Results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_qca_analysis.py qca_config.yaml
  python run_qca_analysis.py --create-example
  python run_qca_analysis.py qca_config.yaml --verbose

Phases:
  QCA-1: Calibrates codes/entities to set membership scores (0-1)
  QCA-2: Constructs truth tables showing condition-outcome configurations
  QCA-3: Generates scripts for external Boolean minimization tools

Output:
  - calibrated_cases.json: Cases with membership scores
  - truth_table_*.csv: Truth tables for each outcome
  - qca_analysis_*.R: R scripts for QCA package
  - qca_analysis_*.py: Python minimization scripts
  - qca_analysis_*.cypher: Neo4j graph queries
        """
    )
    
    parser.add_argument(
        "config_file",
        nargs="?",
        help="Path to QCA configuration YAML file"
    )
    
    parser.add_argument(
        "--create-example",
        action="store_true",
        help="Create an example QCA configuration file"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Handle create example
    if args.create_example:
        create_example_config()
        return
    
    # Validate arguments
    if not args.config_file:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Print banner
    print_banner()
    
    # Validate config file
    config_path = validate_config_file(args.config_file)
    
    try:
        # Import QCA pipeline (after logging is set up)
        from qc.qca.qca_pipeline import run_qca_from_config_file
        
        # Run QCA analysis
        print(f"Loading configuration: {config_path}")
        results = run_qca_from_config_file(str(config_path))
        
        # Print summary
        print()
        print("=" * 80)
        print("QCA ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"Cases analyzed: {results.total_cases_analyzed}")
        print(f"Conditions: {results.conditions_analyzed}")
        print(f"Outcomes: {results.outcomes_analyzed}")
        print(f"Truth tables generated: {len(results.truth_tables)}")
        print(f"Output files created: {len(results.csv_files) + len(results.json_files) + len(results.r_scripts)}")
        print()
        print("Generated files:")
        for file_path in results.csv_files[:5]:  # Show first 5 CSV files
            print(f"  CSV: {Path(file_path).name}")
        for file_path in results.r_scripts[:3]:  # Show first 3 R scripts
            print(f"  R Script: {Path(file_path).name}")
        print(f"  Results: {Path(results.configuration.output_dir) / 'qca_analysis_results.json'}")
        print()
        print("Next steps:")
        print("1. Review truth tables in CSV files")
        print("2. Run R scripts for Boolean minimization (requires R + QCA package)")
        print("3. Analyze configurational patterns for theoretical insights")
        print("=" * 80)
        
    except Exception as e:
        logging.error(f"QCA analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
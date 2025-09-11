#!/usr/bin/env python
"""
Main entry point for Code-First Extraction Pipeline
Run with: python run_code_first_extraction.py config.yaml
"""
import asyncio
import sys
import yaml
import argparse
from pathlib import Path

# Add src to path - resolve relative to script location
script_dir = Path(__file__).parent
project_root = script_dir.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from qc.extraction.code_first_extractor import CodeFirstExtractor
from qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach

def load_config(config_path: str) -> ExtractionConfig:
    """Load configuration from YAML file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    # Convert string to enum if needed
    for field in ['coding_approach', 'speaker_approach', 'entity_approach']:
        if field in config_data and isinstance(config_data[field], str):
            config_data[field] = ExtractionApproach[config_data[field].upper()]
    
    return ExtractionConfig(**config_data)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Code-First Extraction Pipeline for Qualitative Coding"
    )
    
    parser.add_argument('config', help='Path to configuration YAML file')
    parser.add_argument('--output', help='Override output directory')
    parser.add_argument('--no-neo4j', action='store_true', help='Disable Neo4j import')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
        
        # Override settings from command line
        if args.output:
            config.output_dir = args.output
        if args.no_neo4j:
            config.auto_import_neo4j = False
            
        print("=" * 80)
        print("CODE-FIRST EXTRACTION PIPELINE")
        print("=" * 80)
        print(f"Configuration loaded from: {args.config}")
        print(f"Output directory: {config.output_dir}")
        print()
        
        # Run extraction
        extractor = CodeFirstExtractor(config)
        results = await extractor.run_extraction()
        
        # Print results summary
        print("\n" + "=" * 80)
        print("EXTRACTION COMPLETE")
        print("=" * 80)
        
        total_quotes = sum(i.total_quotes for i in results.coded_interviews)
        print(f"Total Quotes Extracted: {total_quotes}")
        print(f"Results saved to: {config.output_dir}/")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
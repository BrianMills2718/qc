#!/usr/bin/env python3
"""
Command-line interface for Qualitative Coding Analysis Tool
"""

import asyncio
import argparse
import logging
from pathlib import Path
import sys
import time
from typing import List, Optional
import uuid

from .core.llm_client import UniversalModelClient
from .core.neo4j_manager import EnhancedNeo4jManager
from .core.schema_config import create_research_schema
from .extraction.multi_pass_extractor import MultiPassExtractor, InterviewContext
from .query.cypher_builder import CypherQueryBuilder, NaturalLanguageParser
from .utils.markdown_exporter import MarkdownExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QualitativeCodingCLI:
    """Main CLI application"""
    
    def __init__(self):
        self.neo4j = None
        self.schema = create_research_schema()
        self.exporter = MarkdownExporter()
    
    async def setup(self):
        """Initialize database connections"""
        self.neo4j = EnhancedNeo4jManager()
        await self.neo4j.connect()
    
    async def cleanup(self):
        """Clean up resources"""
        if self.neo4j:
            await self.neo4j.close()
    
    async def analyze_interviews(self, files: List[str], output: Optional[str] = None):
        """
        Analyze interview files.
        
        Args:
            files: List of interview file paths
            output: Output markdown file path
        """
        session_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Initialize extractor
        extractor = MultiPassExtractor(self.neo4j, self.schema)
        
        all_entities = []
        all_relationships = []
        all_codes = []
        
        for file_path in files:
            logger.info(f"Processing {file_path}...")
            
            try:
                # Read interview text
                text = Path(file_path).read_text(encoding='utf-8')
                
                # Create context
                context = InterviewContext(
                    interview_id=str(uuid.uuid4()),
                    interview_text=text,
                    session_id=session_id,
                    filename=file_path
                )
                
                # Run extraction
                results = await extractor.extract_from_interview(context)
                
                # Aggregate results
                for result in results:
                    all_entities.extend(result.entities_found)
                    all_relationships.extend(result.relationships_found)
                    all_codes.extend(result.codes_found)
                
                logger.info(f"Extracted {len(result.entities_found)} entities, "
                          f"{len(result.relationships_found)} relationships, "
                          f"{len(result.codes_found)} codes from {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Export results
        metadata = {
            "Session ID": session_id,
            "Files processed": len(files),
            "Processing time": f"{processing_time:.2f} seconds"
        }
        
        output_path = self.exporter.export_analysis(
            all_entities, all_relationships, all_codes,
            filename=output,
            metadata=metadata
        )
        
        # Also export session summary
        self.exporter.export_session_summary(
            session_id,
            len(files),
            len(all_entities),
            len(all_relationships),
            len(all_codes),
            processing_time
        )
        
        logger.info(f"Analysis complete! Results saved to {output_path}")
    
    async def query_data(self, query: str, output: Optional[str] = None):
        """
        Query the extracted data using natural language.
        
        Args:
            query: Natural language query
            output: Output file for results
        """
        # Initialize query builder
        parser = NaturalLanguageParser(self.schema)
        builder = CypherQueryBuilder(self.neo4j, parser)
        
        try:
            # Execute query
            result = await builder.execute_natural_language_query(query)
            
            if result.success:
                logger.info(f"Query returned {result.result_count} results")
                
                # Export results if requested
                if output:
                    output_path = self.exporter.export_query_results(
                        query, result.results, filename=output
                    )
                    logger.info(f"Results saved to {output_path}")
                else:
                    # Print results to console
                    print(f"\nQuery: {query}")
                    print(f"Results: {result.result_count}\n")
                    
                    for i, res in enumerate(result.results[:10], 1):
                        print(f"{i}. {res}")
                    
                    if result.result_count > 10:
                        print(f"\n... and {result.result_count - 10} more results")
            else:
                logger.error(f"Query failed: {result.error}")
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
    
    async def clear_database(self):
        """Clear all data from the database"""
        confirm = input("Are you sure you want to clear all data? (yes/no): ")
        if confirm.lower() == 'yes':
            await self.neo4j.clear_database()
            logger.info("Database cleared")
        else:
            logger.info("Operation cancelled")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Qualitative Coding Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze interview files
  qc analyze interviews/*.txt --output analysis.md
  
  # Query the data
  qc query "What do senior people say about AI?"
  
  # Export query results
  qc query "Show all organizations" --output organizations.md
  
  # Clear the database
  qc clear --confirm
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze interview files')
    analyze_parser.add_argument('files', nargs='+', help='Interview files to analyze')
    analyze_parser.add_argument('--output', '-o', help='Output markdown file')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query extracted data')
    query_parser.add_argument('query', help='Natural language query')
    query_parser.add_argument('--output', '-o', help='Output file for results')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear database')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize CLI
    cli = QualitativeCodingCLI()
    
    try:
        await cli.setup()
        
        if args.command == 'analyze':
            await cli.analyze_interviews(args.files, args.output)
        elif args.command == 'query':
            await cli.query_data(args.query, args.output)
        elif args.command == 'clear':
            await cli.clear_database()
        
    finally:
        await cli.cleanup()


def run():
    """Entry point for console script"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
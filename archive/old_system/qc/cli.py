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
from typing import List, Optional, Dict
import uuid

from .core.native_gemini_client import NativeGeminiClient
from .core.neo4j_manager import EnhancedNeo4jManager
from .core.schema_config import create_research_schema
from .extraction.multi_pass_extractor import MultiPassExtractor, InterviewContext
from .extraction.validated_extractor import ValidatedExtractor, ValidationStats
from .validation.validation_config import ValidationConfig, ValidationMode
from .validation.config_manager import ValidationConfigManager
from .analysis.cross_interview_analyzer import CrossInterviewAnalyzer, CrossInterviewQueryBuilder
from .query.cypher_builder import CypherQueryBuilder, NaturalLanguageParser
from .utils.markdown_exporter import MarkdownExporter
from .utils.error_handler import ProcessingError
from .consolidation.llm_consolidator import LLMConsolidator
from .consolidation.consolidation_schemas import ConsolidationRequest, TypeDefinition
from .export.data_exporter import DataExporter

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
        self.data_exporter = DataExporter()
        self.config_manager = ValidationConfigManager()
        self.consolidator = None
    
    async def setup(self):
        """Initialize database connections"""
        self.neo4j = EnhancedNeo4jManager()
        await self.neo4j.connect()
        
        # Initialize LLM consolidator
        gemini_client = NativeGeminiClient()
        self.consolidator = LLMConsolidator(gemini_client)
    
    async def cleanup(self):
        """Clean up resources"""
        if self.neo4j:
            await self.neo4j.close()
    
    async def analyze_interviews(self, files: List[str], 
                               output: Optional[str] = None,
                               validation_mode: str = "hybrid",
                               enable_validation: bool = True,
                               config_file: Optional[str] = None):
        """
        Analyze interview files.
        
        Args:
            files: List of interview file paths
            output: Output markdown file path
            validation_mode: Validation mode (open/closed/hybrid)
            enable_validation: Whether to use validation system
        """
        session_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Initialize extractor
        base_extractor = MultiPassExtractor(self.neo4j, self.schema)
        
        if enable_validation:
            # Configure validation based on mode or config file
            if config_file:
                try:
                    validation_config = self.config_manager.load_config(config_file)
                    logger.info(f"Loaded validation config from file: {config_file}")
                except Exception as e:
                    logger.error(f"Failed to load config file '{config_file}': {e}")
                    raise ProcessingError(f"CLI failed to load config file '{config_file}': {e}") from e
            elif validation_mode == "academic":
                validation_config = ValidationConfig.academic_research_config()
            elif validation_mode == "exploratory":
                validation_config = ValidationConfig.exploratory_research_config()
            elif validation_mode == "production":
                validation_config = ValidationConfig.production_research_config()
            else:
                # Custom hybrid configuration
                validation_config = ValidationConfig(
                    entities=ValidationMode(validation_mode),
                    relationships=ValidationMode(validation_mode)
                )
            
            extractor = ValidatedExtractor(base_extractor, validation_config)
            logger.info(f"Using validated extraction with {validation_mode} mode")
        else:
            extractor = base_extractor
            logger.info("Using basic extraction (no validation)")
        
        all_entities = []
        all_relationships = []
        all_codes = []
        total_validation_stats = ValidationStats()
        
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
                if enable_validation:
                    results, validation_stats = await extractor.extract_from_interview(context)
                    # Aggregate validation stats
                    total_validation_stats.entities_processed += validation_stats.entities_processed
                    total_validation_stats.entities_merged += validation_stats.entities_merged
                    total_validation_stats.entities_rejected += validation_stats.entities_rejected
                    total_validation_stats.relationships_processed += validation_stats.relationships_processed
                    total_validation_stats.relationships_standardized += validation_stats.relationships_standardized
                    total_validation_stats.relationships_rejected += validation_stats.relationships_rejected
                    total_validation_stats.quality_issues_found += validation_stats.quality_issues_found
                    total_validation_stats.validation_time_ms += validation_stats.validation_time_ms
                else:
                    results = await extractor.extract_from_interview(context)
                
                # Aggregate results
                for result in results:
                    all_entities.extend(result.entities_found.values())
                    all_relationships.extend(result.relationships_found)
                    all_codes.extend(result.codes_found.values())
                
                logger.info(f"Extracted {len(result.entities_found)} entities, "
                          f"{len(result.relationships_found)} relationships, "
                          f"{len(result.codes_found)} codes from {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                raise ProcessingError(f"CLI failed to process file '{file_path}': {e}") from e
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Export results
        metadata = {
            "Session ID": session_id,
            "Files processed": len(files),
            "Processing time": f"{processing_time:.2f} seconds"
        }
        
        # Add validation statistics if enabled
        if enable_validation:
            metadata.update({
                "Validation mode": validation_mode,
                "Entities processed": total_validation_stats.entities_processed,
                "Entities merged": total_validation_stats.entities_merged,
                "Entities rejected": total_validation_stats.entities_rejected,
                "Relationships processed": total_validation_stats.relationships_processed,
                "Relationships standardized": total_validation_stats.relationships_standardized,
                "Relationships rejected": total_validation_stats.relationships_rejected,
                "Quality issues found": total_validation_stats.quality_issues_found,
                "Validation time": f"{total_validation_stats.validation_time_ms}ms"
            })
            
            logger.info(f"Validation stats: {total_validation_stats.entities_processed} entities processed, "
                       f"{total_validation_stats.entities_merged} merged, "
                       f"{total_validation_stats.entities_rejected} rejected")
        
        # Store extracted data in Neo4j (SKIP - already stored by extraction pipeline)
        # await self._store_extraction_results(all_entities, all_relationships, session_id)
        logger.info(f"Skipping CLI Neo4j storage - entities already stored by extraction pipeline")
        
        # NEW: Perform LLM-based type consolidation if validation enabled
        if enable_validation and self.consolidator:
            logger.info("Performing LLM-based type consolidation...")
            
            # Collect all discovered types from session
            discovered_types = self._collect_session_types(all_entities, all_relationships)
            
            # Build consolidation request
            consolidation_request = self._build_consolidation_request(
                discovered_types, validation_mode
            )
            
            # Perform consolidation
            consolidation_response = await self.consolidator.consolidate_session_types(
                consolidation_request
            )
            
            # Apply consolidations to stored data
            await self._apply_consolidations_to_data(consolidation_response, session_id)
            
            # Update entities and relationships with consolidated types
            all_entities, all_relationships = await self._fetch_consolidated_data(session_id)
            
            logger.info(f"Consolidation complete: {consolidation_response.summary}")
        
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
        return output_path
    
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
            raise ProcessingError(f"CLI query execution failed: {e}") from e
    
    async def clear_database(self):
        """Clear all data from the database"""
        confirm = input("Are you sure you want to clear all data? (yes/no): ")
        if confirm.lower() == 'yes':
            await self.neo4j.clear_database()
            logger.info("Database cleared")
        else:
            logger.info("Operation cancelled")
    
    async def start_api_server(self, host: str, port: int, workers: int, reload: bool):
        """Start the FastAPI REST server"""
        try:
            import uvicorn
            from qc.api.main import app
            
            logger.info(f"Starting API server on {host}:{port}")
            logger.info(f"Workers: {workers}, Reload: {reload}")
            
            # Close CLI database connection as API will manage its own
            if self.neo4j:
                await self.neo4j.close()
            
            # Start server
            uvicorn.run(
                "src.qc.api.main:app",
                host=host,
                port=port,
                workers=workers if not reload else 1,
                reload=reload,
                log_level="info"
            )
            
        except ImportError:
            logger.error("FastAPI/Uvicorn not installed. Install with: pip install fastapi uvicorn")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            sys.exit(1)
    
    def list_validation_configs(self):
        """List all available validation configurations"""
        configs = self.config_manager.list_configs()
        
        if not configs:
            print("No validation configurations found.")
            print("\nCreate default configurations with:")
            print("  qc config create-defaults")
            return
        
        print(f"Available validation configurations ({len(configs)}):")
        print()
        
        for config_name in sorted(configs):
            try:
                info = self.config_manager.get_config_info(config_name)
                print(f"  {config_name}:")
                print(f"    Entities: {info['entities_mode']}")
                print(f"    Relationships: {info['relationships_mode']}")
                print(f"    Quality threshold: {info['quality_threshold']}")
                print()
            except Exception as e:
                logger.error(f"Failed to process config {config_name}: {e}")
                raise ProcessingError(f"CLI failed to process config '{config_name}': {e}") from e
    
    def show_validation_config(self, name: str):
        """Show details of a specific validation configuration"""
        try:
            info = self.config_manager.get_config_info(name)
            
            print(f"Validation Configuration: {name}")
            print("=" * (len(name) + 25))
            print(f"File path: {info['file_path']}")
            print()
            print("Settings:")
            print(f"  Entities mode: {info['entities_mode']}")
            print(f"  Relationships mode: {info['relationships_mode']}")
            print(f"  Entity matching: {info['entity_matching']}")
            print(f"  Consolidation threshold: {info['consolidation_threshold']}")
            print(f"  Quality threshold: {info['quality_threshold']}")
            print(f"  Auto merge similar: {info['auto_merge_similar']}")
            
            if 'metadata' in info and info['metadata']:
                print()
                print("Metadata:")
                for key, value in info['metadata'].items():
                    print(f"  {key}: {value}")
                    
        except FileNotFoundError:
            print(f"Configuration '{name}' not found.")
            print("\nAvailable configurations:")
            self.list_validation_configs()
        except Exception as e:
            logger.error(f"Error loading configuration '{name}': {e}")
            raise ProcessingError(f"CLI failed to load configuration '{name}': {e}") from e
    
    def create_default_configs(self):
        """Create default validation configurations"""
        self.config_manager.create_default_configs()
        print("Default validation configurations created.")
        print("\nAvailable configurations:")
        self.list_validation_configs()
    
    def validate_config(self, name: str):
        """Validate a configuration file"""
        try:
            result = self.config_manager.validate_config_file(name)
            
            print(f"Validation result for '{name}': ", end="")
            if result['valid']:
                print("VALID")
            else:
                print("INVALID")
            
            if result['errors']:
                print("\nErrors:")
                for error in result['errors']:
                    print(f"  - {error}")
            
            if result['warnings']:
                print("\nWarnings:")
                for warning in result['warnings']:
                    print(f"  - {warning}")
            
            if result['suggestions']:
                print("\nSuggestions:")
                for suggestion in result['suggestions']:
                    print(f"  - {suggestion}")
                    
        except FileNotFoundError:
            print(f"Configuration '{name}' not found.")
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
            raise ProcessingError(f"CLI failed to validate configuration: {e}") from e
    
    async def analyze_consensus_patterns(self, 
                                       interview_ids: Optional[List[str]] = None,
                                       threshold: float = 0.6):
        """Analyze consensus patterns across interviews"""
        analyzer = CrossInterviewAnalyzer(self.neo4j)
        
        try:
            patterns = await analyzer.analyze_consensus_patterns(interview_ids, threshold)
            
            print(f"Consensus Pattern Analysis")
            print("=" * 30)
            print(f"Found {len(patterns)} consensus patterns")
            print()
            
            for pattern in patterns:
                print(f"Pattern: {pattern.description}")
                print(f"Type: {pattern.pattern_type}")
                print(f"Consensus strength: {pattern.consensus_strength:.2%}")
                print(f"Supporting interviews: {pattern.supporting_count}/{pattern.total_interviews}")
                print(f"Interviews: {', '.join(pattern.supporting_interviews[:3])}...")
                print()
                
        except Exception as e:
            logger.error(f"Consensus analysis failed: {e}")
            raise ProcessingError(f"CLI consensus analysis failed: {e}") from e
    
    async def analyze_divergence_patterns(self, interview_ids: Optional[List[str]] = None):
        """Analyze divergence patterns across interviews"""
        analyzer = CrossInterviewAnalyzer(self.neo4j)
        
        try:
            patterns = await analyzer.analyze_divergence_patterns(interview_ids)
            
            print(f"Divergence Pattern Analysis")
            print("=" * 30)
            print(f"Found {len(patterns)} divergence patterns")
            print()
            
            for pattern in patterns:
                print(f"Pattern: {pattern.description}")
                print(f"Type: {pattern.pattern_type}")
                print(f"Conflicting perspectives: {len(pattern.conflicting_perspectives)}")
                
                for perspective in pattern.conflicting_perspectives:
                    print(f"  - {perspective['perspective']}: {perspective['evidence_count']} mentions")
                print()
                
        except Exception as e:
            logger.error(f"Divergence analysis failed: {e}")
            raise ProcessingError(f"CLI divergence analysis failed: {e}") from e
    
    async def analyze_evolution_patterns(self, interview_ids: Optional[List[str]] = None):
        """Analyze evolution patterns across interviews"""
        analyzer = CrossInterviewAnalyzer(self.neo4j)
        
        try:
            patterns = await analyzer.analyze_evolution_patterns(interview_ids)
            
            print(f"Evolution Pattern Analysis")
            print("=" * 30)
            print(f"Found {len(patterns)} evolution patterns")
            print()
            
            for pattern in patterns:
                print(f"Pattern: {pattern.description}")
                print(f"Trend: {pattern.trend_direction}")
                print(f"Data points: {len(pattern.timeline)}")
                print()
                
        except Exception as e:
            logger.error(f"Evolution analysis failed: {e}")
            raise ProcessingError(f"CLI evolution analysis failed: {e}") from e
    
    async def analyze_knowledge_gaps(self, interview_ids: Optional[List[str]] = None):
        """Analyze knowledge gaps across interviews"""
        analyzer = CrossInterviewAnalyzer(self.neo4j)
        query_builder = CrossInterviewQueryBuilder(analyzer)
        
        try:
            gaps = await query_builder.find_knowledge_gaps(interview_ids)
            
            print(f"Knowledge Gap Analysis")
            print("=" * 25)
            print()
            
            print("Tool Knowledge Gaps:")
            for gap in gaps['tool_knowledge_gaps'][:10]:  # Show top 10
                print(f"  - {gap['tool_name']}: mentioned by {gap['mention_count']} person(s)")
            
            print()
            print("Method Knowledge Gaps:")
            for gap in gaps['method_knowledge_gaps'][:10]:  # Show top 10
                print(f"  - {gap['method_name']}: mentioned by {gap['mention_count']} person(s)")
                
        except Exception as e:
            logger.error(f"Knowledge gap analysis failed: {e}")
            raise ProcessingError(f"CLI knowledge gap analysis failed: {e}") from e
    
    async def analyze_innovation_diffusion(self, interview_ids: Optional[List[str]] = None):
        """Analyze innovation diffusion patterns"""
        analyzer = CrossInterviewAnalyzer(self.neo4j)
        query_builder = CrossInterviewQueryBuilder(analyzer)
        
        try:
            diffusion = await query_builder.analyze_innovation_diffusion(interview_ids)
            
            print(f"Innovation Diffusion Analysis")
            print("=" * 30)
            print()
            
            for item in diffusion['innovation_diffusion'][:5]:  # Show top 5
                tool_name = item['tool_name']
                timeline = item['adoption_timeline']
                
                print(f"Tool: {tool_name}")
                print(f"Adoption timeline:")
                for adoption in timeline[:3]:  # Show first 3 adopters
                    print(f"  - {adoption['person']} ({adoption['role']}) on {adoption['date']}")
                print()
                
        except Exception as e:
            logger.error(f"Innovation diffusion analysis failed: {e}")
            raise ProcessingError(f"CLI innovation diffusion analysis failed: {e}") from e
    
    async def _store_extraction_results(self, entities: List[Dict], relationships: List[Dict], session_id: str):
        """Store extracted entities and relationships in Neo4j"""
        try:
            # Store entities
            entities_stored = 0
            for entity_data in entities:
                try:
                    # Create EntityNode object
                    from .core.neo4j_manager import EntityNode
                    entity_node = EntityNode(
                        id=entity_data.get('id', f"entity_{entity_data.get('name', 'unknown').replace(' ', '_').lower()}"),
                        name=entity_data.get('name', ''),
                        entity_type=entity_data.get('type', 'Unknown'),
                        properties={
                            'confidence': entity_data.get('confidence', 0.8),
                            'context': entity_data.get('context', ''),
                            'session_id': session_id,
                            'interview_id': session_id,  # Add for backward compatibility
                            'quotes': ', '.join(entity_data.get('quotes', []))
                        }
                    )
                    await self.neo4j.create_entity(entity_node)
                    entities_stored += 1
                except Exception as e:
                    logger.error(f"Failed to store entity {entity_data.get('name', 'unknown')}: {e}")
                    raise ProcessingError(f"CLI failed to store entity '{entity_data.get('name', 'unknown')}': {e}") from e
            
            # Store relationships  
            relationships_stored = 0
            for rel_data in relationships:
                try:
                    # Create RelationshipEdge object
                    from .core.neo4j_manager import RelationshipEdge
                    rel_edge = RelationshipEdge(
                        source_id=rel_data.get('source_entity', ''),
                        target_id=rel_data.get('target_entity', ''),
                        relationship_type=rel_data.get('relationship_type', rel_data.get('type', '')),
                        properties={
                            'confidence': rel_data.get('confidence', 0.8),
                            'context': rel_data.get('context', ''),
                            'session_id': session_id,
                            'quotes': ', '.join(rel_data.get('quotes', []))
                        }
                    )
                    await self.neo4j.create_relationship(rel_edge)
                    relationships_stored += 1
                except Exception as e:
                    logger.error(f"Failed to store relationship {rel_data.get('source_entity', 'unknown')} -> {rel_data.get('target_entity', 'unknown')}: {e}")
                    raise ProcessingError(f"CLI failed to store relationship '{rel_data.get('source_entity', 'unknown')} -> {rel_data.get('target_entity', 'unknown')}': {e}") from e
            
            logger.info(f"Stored {entities_stored} entities and {relationships_stored} relationships in Neo4j")
            
        except Exception as e:
            logger.error(f"Failed to store extraction results in Neo4j: {e}")
            raise ProcessingError(f"CLI failed to store extraction results in Neo4j: {e}") from e
    
    def _collect_session_types(self, entities: List[Dict], relationships: List[Dict]) -> Dict:
        """Collect and count all discovered types from session"""
        entity_type_counts = {}
        relationship_type_counts = {}
        
        # Count entity types
        for entity in entities:
            entity_type = entity.get('type', 'Unknown')
            if entity_type not in entity_type_counts:
                entity_type_counts[entity_type] = {
                    'count': 0,
                    'definition': entity.get('type_definition', '')
                }
            entity_type_counts[entity_type]['count'] += 1
        
        # Count relationship types  
        for relationship in relationships:
            rel_type = relationship.get('relationship_type', 'RELATED_TO')
            if rel_type not in relationship_type_counts:
                relationship_type_counts[rel_type] = {
                    'count': 0,
                    'definition': relationship.get('relationship_definition', '')
                }
            relationship_type_counts[rel_type]['count'] += 1
        
        return {
            'entity_types': entity_type_counts,
            'relationship_types': relationship_type_counts
        }
    
    def _build_consolidation_request(self, discovered_types: Dict, validation_mode: str) -> ConsolidationRequest:
        """Build consolidation request from discovered types"""
        
        # Convert to TypeDefinition objects
        entity_types = [
            TypeDefinition(
                type_name=type_name,
                definition=type_data['definition'],
                frequency=type_data['count']
            )
            for type_name, type_data in discovered_types['entity_types'].items()
        ]
        
        relationship_types = [
            TypeDefinition(
                type_name=type_name,
                definition=type_data['definition'], 
                frequency=type_data['count']
            )
            for type_name, type_data in discovered_types['relationship_types'].items()
        ]
        
        # Add predefined types for hybrid/closed modes
        predefined_entities = []
        predefined_relationships = []
        
        if validation_mode in ['hybrid', 'closed']:
            predefined_entities = self._get_predefined_entity_types()
            predefined_relationships = self._get_predefined_relationship_types()
        
        return ConsolidationRequest(
            entity_types=entity_types,
            relationship_types=relationship_types,
            predefined_entity_types=predefined_entities,
            predefined_relationship_types=predefined_relationships,
            validation_mode=validation_mode
        )
    
    async def _apply_consolidations_to_data(self, consolidation, session_id: str):
        """Apply consolidation mappings to Neo4j data"""
        
        # Create type mappings
        entity_mappings = {}
        relationship_mappings = {}
        
        for consolidated in consolidation.consolidated_entities:
            for variant in consolidated.variants:
                entity_mappings[variant] = {
                    'canonical_type': consolidated.canonical_name,
                    'definition': consolidated.definition
                }
        
        for consolidated in consolidation.consolidated_relationships:
            for variant in consolidated.variants:
                relationship_mappings[variant] = {
                    'canonical_type': consolidated.canonical_name,
                    'definition': consolidated.definition
                }
        
        # Update Neo4j data
        await self._update_neo4j_types(entity_mappings, relationship_mappings, session_id)
    
    async def _update_neo4j_types(self, entity_mappings: Dict, relationship_mappings: Dict, session_id: str):
        """Update Neo4j with consolidated types and definitions"""
        
        # Update entity types and add definitions
        for original_type, mapping in entity_mappings.items():
            query = """
            MATCH (e:Entity)
            WHERE e.entity_type = $original_type 
              AND (e.interview_id = $session_id OR e.session_id = $session_id)
            SET e.entity_type = $canonical_type,
                e.type_definition = $definition,
                e.original_type = $original_type,
                e.consolidated = true
            RETURN count(e) as updated_count
            """
            
            result = await self.neo4j.execute_cypher(query, {
                'original_type': original_type,
                'canonical_type': mapping['canonical_type'],
                'definition': mapping['definition'],
                'session_id': session_id
            })
            
            count = result[0]['updated_count'] if result else 0
            logger.info(f"Updated {count} entities: '{original_type}' → '{mapping['canonical_type']}'")
        
        # Update relationship types and add definitions
        for original_type, mapping in relationship_mappings.items():
            canonical_type = mapping['canonical_type']
            definition = mapping['definition']
            
            # Check if this relationship needs direction flipping
            if (original_type == "used_by" and canonical_type == "USES") or \
               (original_type == "employs" and canonical_type == "WORKS_AT"):
                # Direction flip: Tool -used_by-> Person becomes Person -USES-> Tool
                #                Organization -employs-> Person becomes Person -WORKS_AT-> Organization
                # First collect the relationship data, then delete and recreate
                rel_type = "USES" if canonical_type == "USES" else canonical_type
                flip_query = f"""
                MATCH (source:Entity)-[r]->(target:Entity)
                WHERE type(r) = $original_type
                  AND (source.session_id = $session_id OR source.interview_id = $session_id)
                WITH source, target, r,
                     COALESCE(r.confidence, 0.8) as confidence,
                     COALESCE(r.context, '') as context,
                     COALESCE(r.interview_id, $session_id) as interview_id,
                     COALESCE(r.session_id, $session_id) as session_id,
                     COALESCE(r.created_at, datetime()) as created_at
                DELETE r
                CREATE (target)-[new_r:{rel_type} {{
                    canonical_relationship_type: $canonical_type,
                    relationship_definition: $definition,
                    original_type: $original_type,
                    consolidated: true,
                    confidence: confidence,
                    context: context,
                    interview_id: interview_id,
                    session_id: session_id,
                    created_at: created_at
                }}]->(source)
                RETURN count(new_r) as updated_count
                """
                
                result = await self.neo4j.execute_cypher(flip_query, {
                    'original_type': original_type,
                    'canonical_type': canonical_type,
                    'definition': definition,
                    'session_id': session_id
                })
                
                count = result[0]['updated_count'] if result else 0
                logger.info(f"Direction-flipped {count} relationships: '{original_type}' → '{canonical_type}' (direction reversed)")
                
            else:
                # Standard relationship consolidation (no direction change)
                query = """
                MATCH (source:Entity)-[r]->(target:Entity)
                WHERE type(r) = $original_type
                  AND (source.interview_id = $session_id OR source.session_id = $session_id)
                SET r.canonical_relationship_type = $canonical_type,
                    r.relationship_definition = $definition,
                    r.original_type = $original_type,
                    r.consolidated = true
                RETURN count(r) as updated_count
                """
                
                result = await self.neo4j.execute_cypher(query, {
                    'original_type': original_type,
                    'canonical_type': canonical_type,
                    'definition': definition,
                    'session_id': session_id
                })
                
                count = result[0]['updated_count'] if result else 0
                logger.info(f"Updated {count} relationships: '{original_type}' → '{canonical_type}'")
    
    async def _fetch_consolidated_data(self, session_id: str):
        """Fetch consolidated data from Neo4j"""
        
        # Fetch entities with consolidated types
        entity_query = """
        MATCH (e:Entity)
        WHERE e.interview_id = $session_id OR e.session_id = $session_id
        RETURN e.name as name, 
               COALESCE(e.entity_type, 'Unknown') as type,
               COALESCE(e.type_definition, '') as type_definition,
               COALESCE(e.confidence, 0.8) as confidence,
               COALESCE(e.context, '') as context,
               COALESCE(e.quotes, '') as quotes,
               e.consolidated as consolidated,
               e.original_type as original_type
        """
        
        entity_results = await self.neo4j.execute_cypher(entity_query, {'session_id': session_id})
        entities = [dict(result) for result in entity_results]
        
        # Fetch relationships with consolidated types
        relationship_query = """
        MATCH (source)-[r]->(target)
        WHERE (source.interview_id = $session_id OR source.session_id = $session_id)
        RETURN source.name as source_entity,
               target.name as target_entity,
               COALESCE(r.canonical_relationship_type, type(r)) as relationship_type,
               COALESCE(r.relationship_definition, '') as relationship_definition,
               COALESCE(r.confidence, 0.8) as confidence,
               COALESCE(r.context, '') as context,
               COALESCE(r.quotes, '') as quotes,
               r.consolidated as consolidated,
               r.original_type as original_type
        """
        
        relationship_results = await self.neo4j.execute_cypher(relationship_query, {'session_id': session_id})
        relationships = [dict(result) for result in relationship_results]
        
        return entities, relationships
    
    def _get_predefined_entity_types(self) -> List[TypeDefinition]:
        """Get predefined entity types with definitions"""
        return [
            TypeDefinition(
                type_name="Person",
                definition="Individual human beings mentioned in interviews",
                frequency=0
            ),
            TypeDefinition(
                type_name="Organization", 
                definition="Companies, institutions, universities, or formal groups",
                frequency=0
            ),
            TypeDefinition(
                type_name="Tool",
                definition="Software applications, platforms, or technical tools",
                frequency=0
            ),
            TypeDefinition(
                type_name="Method",
                definition="Approaches, methodologies, practices, or processes",
                frequency=0
            )
        ]
    
    def _get_predefined_relationship_types(self) -> List[TypeDefinition]:
        """Get predefined relationship types with definitions"""
        return [
            TypeDefinition(
                type_name="WORKS_AT",
                definition="Employment or institutional affiliation relationship",
                frequency=0
            ),
            TypeDefinition(
                type_name="USES",
                definition="Utilizes, employs, or operates a tool, method, or technology",
                frequency=0
            ),
            TypeDefinition(
                type_name="ADVOCATES_FOR",
                definition="Supports, promotes, or champions something positively",
                frequency=0
            ),
            TypeDefinition(
                type_name="SKEPTICAL_OF",
                definition="Doubts, questions, or has concerns about something",
                frequency=0
            ),
            TypeDefinition(
                type_name="COLLABORATES_WITH",
                definition="Works together or partners with on projects or activities",
                frequency=0
            ),
            TypeDefinition(
                type_name="MANAGES",
                definition="Supervises, oversees, leads, or directs",
                frequency=0
            )
        ]

    async def export_analysis_data(self, format_type: str, input_dir: Optional[str] = None, 
                                 output_path: Optional[str] = None, 
                                 components: List[str] = ['all']):
        """
        Export analysis results to CSV or Excel formats
        
        Args:
            format_type: 'csv', 'excel', or 'both'
            input_dir: Input directory with analysis results (default: outputs/current)
            output_path: Output filename or directory 
            components: List of components to export
        """
        try:
            import json
            
            # Default input directory
            if not input_dir:
                input_dir = Path("outputs/current")
            else:
                input_dir = Path(input_dir)
            
            if not input_dir.exists():
                raise ProcessingError(f"Input directory not found: {input_dir}")
            
            # Load analysis data
            print(f"Loading analysis data from: {input_dir}")
            
            analysis_data = {}
            
            # Load interviews
            interviews_dir = input_dir / "interviews"
            if interviews_dir.exists():
                interviews = []
                for interview_file in interviews_dir.glob("*.json"):
                    with open(interview_file, 'r', encoding='utf-8') as f:
                        interviews.append(json.load(f))
                analysis_data['interviews'] = interviews
                print(f"   * Loaded {len(interviews)} interviews")
            
            # Load taxonomy
            taxonomy_file = input_dir / "taxonomy.json"
            if taxonomy_file.exists():
                with open(taxonomy_file, 'r', encoding='utf-8') as f:
                    analysis_data['taxonomy'] = json.load(f)
                print(f"   * Loaded taxonomy with {len(analysis_data['taxonomy'].get('codes', []))} codes")
            
            # Load speaker schema
            speaker_file = input_dir / "speaker_schema.json"
            if speaker_file.exists():
                with open(speaker_file, 'r', encoding='utf-8') as f:
                    analysis_data['speaker_schema'] = json.load(f)
                print(f"   * Loaded speaker schema")
            
            # Load entity schema
            entity_file = input_dir / "entity_schema.json"
            if entity_file.exists():
                with open(entity_file, 'r', encoding='utf-8') as f:
                    analysis_data['entity_schema'] = json.load(f)
                print(f"   * Loaded entity schema")
            
            if not analysis_data:
                raise ProcessingError("No analysis data found in input directory")
            
            # Export based on format
            export_results = {}
            
            if format_type in ['csv', 'both']:
                print("\nExporting to CSV format...")
                
                if 'all' in components:
                    # Export all components to separate CSV files
                    csv_results = self.data_exporter.export_complete_analysis_csv(
                        analysis_data, output_path
                    )
                    export_results.update(csv_results)
                    print(f"   * Exported {len(csv_results)} CSV files")
                else:
                    # Export specific components
                    for component in components:
                        if component == 'quotes' and 'interviews' in analysis_data:
                            filename = f"{output_path}_quotes.csv" if output_path else None
                            csv_path = self.data_exporter.export_quotes_csv(
                                analysis_data['interviews'], filename
                            )
                            export_results['quotes'] = csv_path
                        elif component == 'codes' and 'taxonomy' in analysis_data:
                            filename = f"{output_path}_codes.csv" if output_path else None
                            csv_path = self.data_exporter.export_codes_csv(
                                analysis_data['taxonomy'], filename
                            )
                            export_results['codes'] = csv_path
                        # Add other components as needed
                    
                    print(f"   * Exported {len(export_results)} CSV files")
            
            if format_type in ['excel', 'both']:
                print("\nExporting to Excel format...")
                
                excel_filename = output_path if output_path and output_path.endswith('.xlsx') else None
                excel_path = self.data_exporter.export_excel_workbook(
                    analysis_data, excel_filename
                )
                export_results['excel'] = excel_path
                print(f"   * Exported Excel workbook: {excel_path}")
            
            # Display results
            print(f"\nExport completed successfully!")
            print("Generated files:")
            for export_type, file_path in export_results.items():
                print(f"   * {export_type}: {file_path}")
            
            return export_results
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise ProcessingError(f"Export failed: {e}") from e


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Qualitative Coding Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze interview files with hybrid validation (default)
  qc analyze interviews/*.txt --output analysis.md
  
  # Use academic research validation (strict schema)
  qc analyze interviews/*.txt --validation-mode academic
  
  # Use exploratory validation (maximum discovery flexibility)
  qc analyze interviews/*.txt --validation-mode exploratory
  
  # Disable validation (basic extraction only)
  qc analyze interviews/*.txt --no-validation
  
  # Use custom configuration file
  qc analyze interviews/*.txt --config-file my_config
  
  # Query the data
  qc query "What do senior people say about AI?"
  
  # Export query results
  qc query "Show all organizations" --output organizations.md
  
  # Configuration management
  qc config list
  qc config show academic_research
  qc config create-defaults
  qc config validate my_config
  
  # Cross-interview pattern analysis
  qc analyze-patterns consensus --threshold 0.7
  qc analyze-patterns divergence
  qc analyze-patterns gaps
  qc analyze-patterns diffusion
  
  # Clear the database
  qc clear
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze interview files')
    analyze_parser.add_argument('files', nargs='+', help='Interview files to analyze')
    analyze_parser.add_argument('--output', '-o', help='Output markdown file')
    analyze_parser.add_argument('--validation-mode', '-v', 
                              choices=['open', 'closed', 'hybrid', 'academic', 'exploratory', 'production'],
                              default='hybrid',
                              help='Validation mode (default: hybrid)')
    analyze_parser.add_argument('--no-validation', action='store_true',
                              help='Disable validation system (use basic extraction only)')
    analyze_parser.add_argument('--config-file', '-c',
                              help='Load validation configuration from file')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query extracted data')
    query_parser.add_argument('query', help='Natural language query')
    query_parser.add_argument('--output', '-o', help='Output file for results')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear database')
    
    # Serve command (API server)
    serve_parser = subparsers.add_parser('serve', help='Start REST API server')
    serve_parser.add_argument('--host', default='0.0.0.0', help='Server host (default: 0.0.0.0)')
    serve_parser.add_argument('--port', type=int, default=8000, help='Server port (default: 8000)')
    serve_parser.add_argument('--workers', type=int, default=1, help='Number of workers (default: 1)')
    serve_parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage validation configurations')
    config_subparsers = config_parser.add_subparsers(dest='config_action', help='Configuration actions')
    
    # Config list
    config_list_parser = config_subparsers.add_parser('list', help='List available configurations')
    
    # Config show
    config_show_parser = config_subparsers.add_parser('show', help='Show configuration details')
    config_show_parser.add_argument('config_name', help='Configuration name to show')
    
    # Config create-defaults
    config_defaults_parser = config_subparsers.add_parser('create-defaults', help='Create default configurations')
    
    # Config validate
    config_validate_parser = config_subparsers.add_parser('validate', help='Validate configuration file')
    config_validate_parser.add_argument('config_name', help='Configuration name to validate')
    
    # Pattern analysis command
    pattern_parser = subparsers.add_parser('analyze-patterns', help='Analyze patterns across interviews')
    pattern_parser.add_argument('pattern_type', 
                              choices=['consensus', 'divergence', 'evolution', 'gaps', 'diffusion'],
                              help='Type of pattern analysis to perform')
    pattern_parser.add_argument('--interviews', nargs='*', 
                              help='Specific interview IDs to analyze (default: all)')
    pattern_parser.add_argument('--threshold', type=float, default=0.6,
                              help='Consensus threshold (0.0-1.0, default: 0.6)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export analysis results to CSV/Excel')
    export_parser.add_argument('format', choices=['csv', 'excel', 'both'], 
                             help='Export format')
    export_parser.add_argument('--input', '-i', 
                             help='Input directory with analysis results (default: outputs/current)')
    export_parser.add_argument('--output', '-o', 
                             help='Output filename or directory (auto-generated if not provided)')
    export_parser.add_argument('--components', '-c', nargs='*',
                             choices=['quotes', 'codes', 'speakers', 'entities', 'all'],
                             default=['all'],
                             help='Components to export (default: all)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize CLI
    cli = QualitativeCodingCLI()
    
    try:
        # Some commands don't need database connection
        if args.command not in ['export']:
            await cli.setup()
        
        if args.command == 'analyze':
            await cli.analyze_interviews(
                args.files, 
                args.output, 
                getattr(args, 'validation_mode', 'hybrid'),
                not getattr(args, 'no_validation', False),
                getattr(args, 'config_file', None)
            )
        elif args.command == 'query':
            await cli.query_data(args.query, args.output)
        elif args.command == 'clear':
            await cli.clear_database()
        elif args.command == 'serve':
            await cli.start_api_server(args.host, args.port, args.workers, args.reload)
        elif args.command == 'config':
            # Config commands don't need database connection
            if args.config_action == 'list':
                cli.list_validation_configs()
            elif args.config_action == 'show':
                cli.show_validation_config(args.config_name)
            elif args.config_action == 'create-defaults':
                cli.create_default_configs()
            elif args.config_action == 'validate':
                cli.validate_config(args.config_name)
        elif args.command == 'analyze-patterns':
            # Cross-interview analysis commands
            if args.pattern_type == 'consensus':
                await cli.analyze_consensus_patterns(getattr(args, 'interviews', None), 
                                                   getattr(args, 'threshold', 0.6))
            elif args.pattern_type == 'divergence':
                await cli.analyze_divergence_patterns(getattr(args, 'interviews', None))
            elif args.pattern_type == 'evolution':
                await cli.analyze_evolution_patterns(getattr(args, 'interviews', None))
            elif args.pattern_type == 'gaps':
                await cli.analyze_knowledge_gaps(getattr(args, 'interviews', None))
            elif args.pattern_type == 'diffusion':
                await cli.analyze_innovation_diffusion(getattr(args, 'interviews', None))
        elif args.command == 'export':
            # Export doesn't need database connection
            await cli.export_analysis_data(
                args.format,
                getattr(args, 'input', None),
                getattr(args, 'output', None),
                getattr(args, 'components', ['all'])
            )
        
    finally:
        await cli.cleanup()


def run():
    """Entry point for console script"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
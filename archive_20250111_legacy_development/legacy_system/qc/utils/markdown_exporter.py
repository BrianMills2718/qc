"""
Markdown Export for Analysis Results

Converts extraction results into readable markdown reports.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class MarkdownExporter:
    """Export analysis results to markdown format"""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize markdown exporter.
        
        Args:
            output_dir: Directory to save markdown files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_analysis(self, 
                       entities: List[Dict[str, Any]],
                       relationships: List[Dict[str, Any]],
                       codes: List[Dict[str, Any]],
                       filename: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Export complete analysis to markdown.
        
        Args:
            entities: List of extracted entities
            relationships: List of relationships
            codes: List of thematic codes
            filename: Output filename (auto-generated if not provided)
            metadata: Additional metadata to include
            
        Returns:
            Path to the generated markdown file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{timestamp}.md"
        
        filepath = self.output_dir / filename
        
        content = self._generate_markdown(entities, relationships, codes, metadata)
        filepath.write_text(content, encoding='utf-8')
        
        logger.info(f"Exported analysis to {filepath}")
        return str(filepath)
    
    def _generate_markdown(self,
                          entities: List[Dict[str, Any]],
                          relationships: List[Dict[str, Any]],
                          codes: List[Dict[str, Any]],
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Generate the markdown content"""
        
        lines = []
        
        # Header
        lines.append("# Qualitative Coding Analysis Report")
        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Metadata section
        if metadata:
            lines.append("## Analysis Metadata")
            lines.append("")
            for key, value in metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")
        
        # Summary section
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Entities found**: {len(entities)}")
        lines.append(f"- **Relationships**: {len(relationships)}")
        lines.append(f"- **Thematic codes**: {len(codes)}")
        lines.append("")
        
        # Entities section
        lines.append("## Entities by Type")
        lines.append("")
        lines.extend(self._format_entities(entities))
        lines.append("")
        
        # Relationship network
        lines.append("## Relationship Network")
        lines.append("")
        lines.extend(self._format_relationships(relationships))
        lines.append("")
        
        # Thematic codes
        lines.append("## Thematic Codes")
        lines.append("")
        lines.extend(self._format_codes(codes))
        lines.append("")
        
        # Entity-Code connections
        lines.append("## Entity-Code Connections")
        lines.append("")
        lines.extend(self._format_entity_code_connections(entities, codes))
        
        return "\n".join(lines)
    
    def _format_entities(self, entities: List[Dict[str, Any]]) -> List[str]:
        """Format entities by type"""
        lines = []
        
        # Group entities by type and collect definitions
        entities_by_type = defaultdict(list)
        type_definitions = {}
        
        for entity in entities:
            entity_type = entity.get('entity_type', entity.get('type', 'Unknown'))
            entities_by_type[entity_type].append(entity)
            
            # Collect type definition
            if 'type_definition' in entity and entity['type_definition']:
                type_definitions[entity_type] = entity['type_definition']
        
        # Format each type
        for entity_type, type_entities in sorted(entities_by_type.items()):
            lines.append(f"### {entity_type} ({len(type_entities)})")
            
            # Add type definition if available
            if entity_type in type_definitions:
                lines.append(f"**Definition**: {type_definitions[entity_type]}")
            
            lines.append("")
            
            for entity in sorted(type_entities, key=lambda x: x.get('name', '')):
                name = entity.get('name', 'Unnamed')
                lines.append(f"#### {name}")
                
                # Add consolidated info if available
                if entity.get('consolidated') and entity.get('original_type'):
                    lines.append(f"*Originally*: {entity['original_type']}")
                
                # Add context if available
                context = entity.get('context', '')
                if context:
                    lines.append(f"*Context*: {context[:100]}{'...' if len(context) > 100 else ''}")
                
                # Add properties
                properties = entity.get('properties', {})
                if properties:
                    for prop_name, prop_value in properties.items():
                        if prop_value:
                            lines.append(f"- **{prop_name}**: {prop_value}")
                
                # Add quotes if available
                quotes = entity.get('source_quotes', [])
                if quotes:
                    lines.append("- **Supporting quotes**:")
                    for quote in quotes[:2]:  # Limit to 2 quotes
                        lines.append(f"  - \"{quote[:150]}...\"" if len(quote) > 150 else f"  - \"{quote}\"")
                
                lines.append("")
        
        return lines
    
    def _format_relationships(self, relationships: List[Dict[str, Any]]) -> List[str]:
        """Format relationships"""
        lines = []
        
        if not relationships:
            lines.append("*No relationships found*")
            return lines
        
        # Group by relationship type and collect definitions
        rels_by_type = defaultdict(list)
        type_definitions = {}
        
        for rel in relationships:
            # Handle both direct type and canonical type properties
            rel_type = (rel.get('canonical_relationship_type') or 
                       rel.get('relationship_type') or 
                       rel.get('type', 'RELATED_TO'))
            
            rels_by_type[rel_type].append(rel)
            
            # Collect type definition
            if 'relationship_definition' in rel and rel['relationship_definition']:
                type_definitions[rel_type] = rel['relationship_definition']
        
        for rel_type, type_rels in sorted(rels_by_type.items()):
            lines.append(f"### {rel_type} ({len(type_rels)})")
            
            # Add type definition if available
            if rel_type in type_definitions:
                lines.append(f"**Definition**: {type_definitions[rel_type]}")
            
            
            for rel in type_rels:
                source = rel.get('source_entity') or rel.get('source_name', 'Unknown')
                target = rel.get('target_entity') or rel.get('target_name', 'Unknown')
                confidence = rel.get('confidence', 1.0)
                
                lines.append(f"- **{source}** → **{target}** (confidence: {confidence:.2f})")
                
                # Add context if available
                context = rel.get('context', '')
                if context:
                    lines.append(f"  - Context: \"{context[:100]}...\"" if len(context) > 100 else f"  - Context: \"{context}\"")
                
                # Show if this was consolidated
                if rel.get('consolidated') and rel.get('original_type'):
                    lines.append(f"  - *Originally*: {rel['original_type']}")
            
            lines.append("")
        
        return lines
    
    def _format_codes(self, codes: List[Dict[str, Any]]) -> List[str]:
        """Format thematic codes"""
        lines = []
        
        if not codes:
            lines.append("*No codes found*")
            return lines
        
        for code in sorted(codes, key=lambda x: x.get('name', '')):
            name = code.get('name', 'Unnamed')
            definition = code.get('definition', 'No definition provided')
            quotes = code.get('quotes', [])
            confidence = code.get('confidence', 1.0)
            
            lines.append(f"### {name}")
            lines.append(f"**Definition**: {definition}")
            lines.append(f"**Confidence**: {confidence:.2f}")
            
            if quotes:
                lines.append(f"**Supporting quotes** ({len(quotes)}):")
                for i, quote in enumerate(quotes[:3], 1):  # Show first 3 quotes
                    quote_text = quote if isinstance(quote, str) else quote.get('text', '')
                    if len(quote_text) > 200:
                        quote_text = quote_text[:200] + "..."
                    lines.append(f"{i}. \"{quote_text}\"")
            
            lines.append("")
        
        return lines
    
    def _format_entity_code_connections(self, entities: List[Dict[str, Any]], codes: List[Dict[str, Any]]) -> List[str]:
        """Format connections between entities and codes"""
        lines = []
        
        # This would need actual connection data from the graph
        # For now, we'll note that this requires querying Neo4j
        lines.append("*Note: Entity-code connections require querying the Neo4j database*")
        lines.append("")
        lines.append("To view entity-code connections, use the query interface:")
        lines.append("```")
        lines.append('qc query "What do senior people say about AI?"')
        lines.append("```")
        
        return lines
    
    def export_query_results(self, 
                           query: str,
                           results: List[Dict[str, Any]],
                           filename: Optional[str] = None) -> str:
        """
        Export query results to markdown.
        
        Args:
            query: The original query
            results: Query results
            filename: Output filename
            
        Returns:
            Path to the generated file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"query_results_{timestamp}.md"
        
        filepath = self.output_dir / filename
        
        lines = []
        lines.append("# Query Results")
        lines.append("")
        lines.append(f"**Query**: {query}")
        lines.append(f"**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Results**: {len(results)}")
        lines.append("")
        
        if not results:
            lines.append("*No results found*")
        else:
            lines.append("## Results")
            lines.append("")
            
            for i, result in enumerate(results, 1):
                lines.append(f"### Result {i}")
                lines.append("")
                
                # Format based on result type
                if 'entity' in result and 'code' in result:
                    # Entity-code relationship
                    entity = result['entity']
                    code = result['code']
                    lines.append(f"**{entity.get('name', 'Unknown')}** mentions **{code.get('name', 'Unknown')}**")
                    
                    context = result.get('context', '')
                    if context:
                        lines.append(f"- Context: \"{context}\"")
                
                elif 'source' in result and 'target' in result:
                    # Entity-entity relationship
                    lines.append(f"**{result['source']}** → **{result['target']}**")
                    lines.append(f"- Relationship: {result.get('relationship', 'RELATED_TO')}")
                
                else:
                    # Generic result
                    for key, value in result.items():
                        lines.append(f"- **{key}**: {value}")
                
                lines.append("")
        
        filepath.write_text("\n".join(lines), encoding='utf-8')
        logger.info(f"Exported query results to {filepath}")
        return str(filepath)
    
    def export_session_summary(self,
                             session_id: str,
                             interviews_processed: int,
                             total_entities: int,
                             total_relationships: int,
                             total_codes: int,
                             processing_time: float,
                             filename: Optional[str] = None) -> str:
        """
        Export a session summary to markdown.
        
        Args:
            session_id: Session identifier
            interviews_processed: Number of interviews processed
            total_entities: Total entities extracted
            total_relationships: Total relationships found
            total_codes: Total codes identified
            processing_time: Total processing time in seconds
            filename: Output filename
            
        Returns:
            Path to the generated file
        """
        if not filename:
            filename = f"session_{session_id}_summary.md"
        
        filepath = self.output_dir / filename
        
        lines = []
        lines.append("# Session Summary")
        lines.append("")
        lines.append(f"**Session ID**: {session_id}")
        lines.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        
        lines.append("## Processing Statistics")
        lines.append("")
        lines.append(f"- **Interviews processed**: {interviews_processed}")
        lines.append(f"- **Total entities**: {total_entities}")
        lines.append(f"- **Total relationships**: {total_relationships}")
        lines.append(f"- **Total codes**: {total_codes}")
        lines.append(f"- **Processing time**: {processing_time:.2f} seconds")
        lines.append(f"- **Average time per interview**: {processing_time / interviews_processed:.2f} seconds")
        lines.append("")
        
        lines.append("## Extraction Efficiency")
        lines.append("")
        lines.append(f"- **Entities per interview**: {total_entities / interviews_processed:.1f}")
        lines.append(f"- **Relationships per interview**: {total_relationships / interviews_processed:.1f}")
        lines.append(f"- **Codes per interview**: {total_codes / interviews_processed:.1f}")
        
        filepath.write_text("\n".join(lines), encoding='utf-8')
        logger.info(f"Exported session summary to {filepath}")
        return str(filepath)
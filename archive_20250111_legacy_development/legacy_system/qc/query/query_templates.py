#!/usr/bin/env python3
"""
Neo4j Query Templates for Qualitative Coding Analysis

Provides pre-built Cypher query templates for common network analyses, including:
- Code co-occurrence patterns
- Entity relationship analysis  
- Quote-code-entity networks
- Centrality measures
- Thematic clustering

These templates complement the natural language query builder with optimized,
ready-to-use queries for academic research workflows.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TemplateCategory(Enum):
    """Categories of query templates"""
    # Existing categories
    NETWORK_ANALYSIS = "network_analysis"
    CODE_ANALYSIS = "code_analysis"  
    ENTITY_ANALYSIS = "entity_analysis"
    QUOTE_ANALYSIS = "quote_analysis"
    RELATIONSHIP_ANALYSIS = "relationship_analysis"
    CENTRALITY_ANALYSIS = "centrality_analysis"
    CLUSTERING_ANALYSIS = "clustering_analysis"
    
    # New research-focused categories
    LONGITUDINAL_ANALYSIS = "longitudinal_analysis"
    COMPARATIVE_ANALYSIS = "comparative_analysis" 
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CONCEPTUAL_RELATIONSHIPS = "conceptual_relationships"


@dataclass
class QueryTemplate:
    """A reusable Cypher query template"""
    id: str
    name: str
    description: str
    category: TemplateCategory
    cypher_template: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    parameter_descriptions: Dict[str, str] = field(default_factory=dict)
    expected_columns: List[str] = field(default_factory=list)
    complexity: str = "medium"  # "low", "medium", "high"
    use_cases: List[str] = field(default_factory=list)
    example_parameters: Dict[str, Any] = field(default_factory=dict)


class QueryTemplateLibrary:
    """Library of pre-built query templates for common network analyses"""
    
    def __init__(self):
        self.templates: Dict[str, QueryTemplate] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize all query templates"""
        # Existing template categories
        self._add_network_analysis_templates()
        self._add_code_analysis_templates()
        self._add_entity_analysis_templates()
        self._add_quote_analysis_templates()
        self._add_relationship_analysis_templates()
        self._add_centrality_analysis_templates()
        self._add_clustering_analysis_templates()
        
        # New research-focused template categories
        self._add_longitudinal_analysis_templates()
        self._add_comparative_analysis_templates()
        self._add_sentiment_analysis_templates()
        self._add_conceptual_relationships_templates()
        
        logger.info(f"Initialized {len(self.templates)} query templates")
    
    def _add_network_analysis_templates(self):
        """Add network analysis templates"""
        
        # Code co-occurrence network
        self.templates["code_cooccurrence"] = QueryTemplate(
            id="code_cooccurrence",
            name="Code Co-occurrence Network",
            description="Find codes that frequently appear together in the same quotes",
            category=TemplateCategory.NETWORK_ANALYSIS,
            cypher_template="""
            MATCH (c1:Code)<-[:SUPPORTS]-(q:Quote)-[:SUPPORTS]->(c2:Code)
            WHERE c1.name <> c2.name
            {where_clause}
            WITH c1, c2, count(q) as cooccurrence_count
            WHERE cooccurrence_count >= $min_cooccurrence
            RETURN c1.name as code1,
                   c2.name as code2,
                   cooccurrence_count,
                   c1.definition as code1_definition,
                   c2.definition as code2_definition
            ORDER BY cooccurrence_count DESC
            {limit_clause}
            """,
            parameters={"min_cooccurrence": 2},
            parameter_descriptions={
                "min_cooccurrence": "Minimum number of co-occurrences to include",
                "entity_filter": "Optional: Filter by entity type (e.g., 'Person')",
                "limit": "Maximum number of results (default: 50)"
            },
            expected_columns=["code1", "code2", "cooccurrence_count", "code1_definition", "code2_definition"],
            complexity="medium",
            use_cases=[
                "Identify thematic relationships",
                "Build code networks for visualization",
                "Find frequently connected concepts"
            ],
            example_parameters={
                "min_cooccurrence": 3,
                "limit": 20
            }
        )
        
        # Entity-code network
        self.templates["entity_code_network"] = QueryTemplate(
            id="entity_code_network",
            name="Entity-Code Network",
            description="Show relationships between entities and codes through quotes",
            category=TemplateCategory.NETWORK_ANALYSIS,
            cypher_template="""
            MATCH (e:Entity)<-[:MENTIONS]-(q:Quote)-[:SUPPORTS]->(c:Code)
            {where_clause}
            RETURN e.name as entity_name,
                   e.entity_type as entity_type,
                   c.name as code_name,
                   c.definition as code_definition,
                   count(q) as connection_strength,
                   avg(q.confidence) as avg_quote_confidence,
                   collect(q.text)[0..3] as sample_quotes
            ORDER BY connection_strength DESC
            {limit_clause}
            """,
            parameters={},
            parameter_descriptions={
                "entity_type": "Filter by entity type (e.g., 'Person', 'Organization')",
                "code_filter": "Filter by specific codes",
                "min_connections": "Minimum connection strength",
                "limit": "Maximum number of results (default: 100)"
            },
            expected_columns=[
                "entity_name", "entity_type", "code_name", "code_definition", 
                "connection_strength", "avg_quote_confidence", "sample_quotes"
            ],
            complexity="medium",
            use_cases=[
                "Analyze entity-theme relationships",
                "Create bipartite networks",
                "Identify entity expertise areas"
            ]
        )
        
        # Quote connectivity analysis
        self.templates["quote_connectivity"] = QueryTemplate(
            id="quote_connectivity",
            name="Quote Connectivity Analysis", 
            description="Analyze how quotes connect entities and codes in the network",
            category=TemplateCategory.NETWORK_ANALYSIS,
            cypher_template="""
            MATCH (q:Quote)
            OPTIONAL MATCH (q)-[:MENTIONS]->(e:Entity)
            OPTIONAL MATCH (q)-[:SUPPORTS]->(c:Code)
            WITH q, 
                 count(DISTINCT e) as entity_connections,
                 count(DISTINCT c) as code_connections,
                 collect(DISTINCT e.name) as connected_entities,
                 collect(DISTINCT c.name) as connected_codes
            WHERE entity_connections >= $min_entities AND code_connections >= $min_codes
            RETURN q.text as quote_text,
                   q.interview_id as interview,
                   q.line_start as line_start,
                   entity_connections,
                   code_connections,
                   entity_connections + code_connections as total_connectivity,
                   connected_entities,
                   connected_codes
            ORDER BY total_connectivity DESC
            {limit_clause}
            """,
            parameters={"min_entities": 1, "min_codes": 1},
            parameter_descriptions={
                "min_entities": "Minimum number of entity connections",
                "min_codes": "Minimum number of code connections",
                "limit": "Maximum number of results (default: 50)"
            },
            expected_columns=[
                "quote_text", "interview", "line_start", "entity_connections", 
                "code_connections", "total_connectivity", "connected_entities", "connected_codes"
            ],
            complexity="high",
            use_cases=[
                "Find highly connected quotes",
                "Identify key narrative moments",
                "Analyze quote bridging patterns"
            ]
        )
    
    def _add_code_analysis_templates(self):
        """Add code analysis templates"""
        
        # Code frequency analysis
        self.templates["code_frequency"] = QueryTemplate(
            id="code_frequency",
            name="Code Frequency Analysis",
            description="Analyze code usage frequency and confidence metrics",
            category=TemplateCategory.CODE_ANALYSIS,
            cypher_template="""
            MATCH (c:Code)
            OPTIONAL MATCH (c)<-[:SUPPORTS]-(q:Quote)
            WITH c, count(q) as quote_count, avg(c.confidence) as avg_confidence
            WHERE quote_count >= $min_quotes
            RETURN c.name as code_name,
                   c.definition as definition,
                   quote_count,
                   avg_confidence,
                   c.id as code_id
            ORDER BY quote_count DESC, avg_confidence DESC
            {limit_clause}
            """,
            parameters={"min_quotes": 1},
            parameter_descriptions={
                "min_quotes": "Minimum number of quotes supporting the code",
                "limit": "Maximum number of results (default: all)"
            },
            expected_columns=["code_name", "definition", "quote_count", "avg_confidence", "code_id"],
            complexity="low",
            use_cases=[
                "Identify most important themes",
                "Quality control for coding",
                "Generate frequency reports"
            ]
        )
        
        # Code hierarchy analysis
        self.templates["code_hierarchy"] = QueryTemplate(
            id="code_hierarchy",
            name="Code Hierarchy Analysis",
            description="Analyze hierarchical relationships between codes",
            category=TemplateCategory.CODE_ANALYSIS,
            cypher_template="""
            MATCH (parent:Code)-[:CONTAINS]->(child:Code)
            OPTIONAL MATCH (child)<-[:SUPPORTS]-(q:Quote)
            WITH parent, child, count(q) as child_quotes
            RETURN parent.name as parent_code,
                   parent.definition as parent_definition,
                   collect({
                       name: child.name,
                       definition: child.definition,
                       quote_count: child_quotes
                   }) as child_codes,
                   sum(child_quotes) as total_child_quotes
            ORDER BY total_child_quotes DESC
            """,
            parameters={},
            parameter_descriptions={
                "parent_filter": "Optional: Filter by specific parent code",
                "min_child_quotes": "Minimum quotes for child codes"
            },
            expected_columns=["parent_code", "parent_definition", "child_codes", "total_child_quotes"],
            complexity="medium",
            use_cases=[
                "Analyze thematic structure",
                "Validate code hierarchy",
                "Generate theme reports"
            ]
        )
        
    def _add_entity_analysis_templates(self):
        """Add entity analysis templates"""
        
        # Entity influence analysis
        self.templates["entity_influence"] = QueryTemplate(
            id="entity_influence",
            name="Entity Influence Analysis",
            description="Measure entity influence based on quote frequency and code diversity",
            category=TemplateCategory.ENTITY_ANALYSIS,
            cypher_template="""
            MATCH (e:Entity)<-[:MENTIONS]-(q:Quote)-[:SUPPORTS]->(c:Code)
            {where_clause}
            WITH e,
                 count(DISTINCT q) as quote_count,
                 count(DISTINCT c) as unique_codes,
                 collect(DISTINCT c.name) as codes_mentioned,
                 avg(q.confidence) as avg_quote_confidence
            RETURN e.name as entity_name,
                   e.entity_type as entity_type,
                   e as entity_properties,
                   quote_count,
                   unique_codes,
                   quote_count * unique_codes as influence_score,
                   codes_mentioned,
                   avg_quote_confidence
            ORDER BY influence_score DESC
            {limit_clause}
            """,
            parameters={},
            parameter_descriptions={
                "entity_type": "Filter by entity type",
                "min_quotes": "Minimum number of quotes",
                "limit": "Maximum number of results (default: 50)"
            },
            expected_columns=[
                "entity_name", "entity_type", "entity_properties", "quote_count",
                "unique_codes", "influence_score", "codes_mentioned", "avg_quote_confidence"
            ],
            complexity="medium",
            use_cases=[
                "Identify key stakeholders",
                "Measure entity importance",
                "Rank entities by thematic diversity"
            ]
        )
        
        # Entity collaboration network
        self.templates["entity_collaboration"] = QueryTemplate(
            id="entity_collaboration",
            name="Entity Collaboration Network",
            description="Find entities that appear together in quotes or share similar themes",
            category=TemplateCategory.ENTITY_ANALYSIS,
            cypher_template="""
            MATCH (e1:Entity)<-[:MENTIONS]-(q:Quote)-[:MENTIONS]->(e2:Entity)
            WHERE e1.name < e2.name  // Avoid duplicates
            {where_clause}
            WITH e1, e2, count(q) as shared_quotes,
                 collect(q.text)[0..2] as sample_quotes
            WHERE shared_quotes >= $min_shared_quotes
            RETURN e1.name as entity1,
                   e1.entity_type as type1,
                   e2.name as entity2, 
                   e2.entity_type as type2,
                   shared_quotes,
                   sample_quotes
            ORDER BY shared_quotes DESC
            {limit_clause}
            """,
            parameters={"min_shared_quotes": 1},
            parameter_descriptions={
                "min_shared_quotes": "Minimum number of shared quotes",
                "entity_type_filter": "Filter by specific entity types",
                "limit": "Maximum number of results (default: 100)"
            },
            expected_columns=["entity1", "type1", "entity2", "type2", "shared_quotes", "sample_quotes"],
            complexity="medium",
            use_cases=[
                "Find collaboration patterns",
                "Identify entity clusters",
                "Build entity networks"
            ]
        )
    
    def _add_quote_analysis_templates(self):
        """Add quote analysis templates"""
        
        # High-impact quotes
        self.templates["high_impact_quotes"] = QueryTemplate(
            id="high_impact_quotes",
            name="High-Impact Quotes Analysis",
            description="Find quotes with high connectivity and confidence scores",
            category=TemplateCategory.QUOTE_ANALYSIS,
            cypher_template="""
            MATCH (q:Quote)
            OPTIONAL MATCH (q)-[:MENTIONS]->(e:Entity)
            OPTIONAL MATCH (q)-[:SUPPORTS]->(c:Code)
            WITH q,
                 count(DISTINCT e) as entity_mentions,
                 count(DISTINCT c) as code_supports,
                 avg(c.confidence) as avg_code_confidence
            WHERE entity_mentions >= $min_entities OR code_supports >= $min_codes
            RETURN q.text as quote_text,
                   q.interview_id as interview,
                   q.line_start as line_start,
                   q.confidence as quote_confidence,
                   entity_mentions,
                   code_supports,
                   entity_mentions + code_supports as total_connections,
                   avg_code_confidence,
                   (entity_mentions + code_supports) * coalesce(q.confidence, 0.5) as impact_score
            ORDER BY impact_score DESC
            {limit_clause}
            """,
            parameters={"min_entities": 1, "min_codes": 1},
            parameter_descriptions={
                "min_entities": "Minimum entity mentions",
                "min_codes": "Minimum code supports", 
                "limit": "Maximum number of results (default: 25)"
            },
            expected_columns=[
                "quote_text", "interview", "line_start", "quote_confidence",
                "entity_mentions", "code_supports", "total_connections", 
                "avg_code_confidence", "impact_score"
            ],
            complexity="medium",
            use_cases=[
                "Find key quotes for analysis",
                "Identify representative examples",
                "Select quotes for presentations"
            ]
        )
        
        # Quote sentiment analysis
        self.templates["quote_context_analysis"] = QueryTemplate(
            id="quote_context_analysis", 
            name="Quote Context Analysis",
            description="Analyze quotes within their interview and speaker context",
            category=TemplateCategory.QUOTE_ANALYSIS,
            cypher_template="""
            MATCH (q:Quote)
            OPTIONAL MATCH (q)-[:MENTIONS]->(e:Entity)
            WITH q, collect(e.name) as mentioned_entities
            WHERE size(mentioned_entities) >= $min_entity_mentions
            RETURN q.text as quote_text,
                   q.interview_id as interview,
                   q.speaker_name as speaker,
                   q.line_start as line_start,
                   q.line_end as line_end,
                   size(mentioned_entities) as entity_count,
                   mentioned_entities,
                   q.confidence as confidence
            ORDER BY entity_count DESC, confidence DESC
            {limit_clause}
            """,
            parameters={"min_entity_mentions": 1},
            parameter_descriptions={
                "min_entity_mentions": "Minimum number of entity mentions",
                "interview_filter": "Filter by specific interview",
                "speaker_filter": "Filter by speaker name",
                "limit": "Maximum number of results (default: 100)"
            },
            expected_columns=[
                "quote_text", "interview", "speaker", "line_start", "line_end",
                "entity_count", "mentioned_entities", "confidence"
            ],
            complexity="low",
            use_cases=[
                "Contextual quote analysis",
                "Speaker-specific insights",
                "Interview narrative flow"
            ]
        )
    
    def _add_relationship_analysis_templates(self):
        """Add relationship analysis templates"""
        
        # Entity relationship patterns
        self.templates["relationship_patterns"] = QueryTemplate(
            id="relationship_patterns",
            name="Entity Relationship Patterns",
            description="Analyze patterns in direct entity relationships",
            category=TemplateCategory.RELATIONSHIP_ANALYSIS,
            cypher_template="""
            MATCH (e1:Entity)-[r]->(e2:Entity)
            {where_clause}
            WITH type(r) as relationship_type,
                 e1.entity_type as source_type,
                 e2.entity_type as target_type,
                 count(*) as frequency
            WHERE frequency >= $min_frequency
            RETURN relationship_type,
                   source_type,
                   target_type,
                   frequency,
                   source_type + ' -> ' + target_type as pattern
            ORDER BY frequency DESC
            {limit_clause}
            """,
            parameters={"min_frequency": 1},
            parameter_descriptions={
                "min_frequency": "Minimum frequency for relationship patterns",
                "relationship_filter": "Filter by relationship type",
                "entity_type_filter": "Filter by entity types",
                "limit": "Maximum number of results (default: 50)"
            },
            expected_columns=["relationship_type", "source_type", "target_type", "frequency", "pattern"],
            complexity="low",
            use_cases=[
                "Understand relationship structures",
                "Identify common patterns",
                "Network analysis preparation"
            ]
        )
        
    def _add_centrality_analysis_templates(self):
        """Add centrality analysis templates"""
        
        # Node centrality analysis  
        self.templates["node_centrality"] = QueryTemplate(
            id="node_centrality",
            name="Node Centrality Analysis",
            description="Calculate centrality measures for entities in the network",
            category=TemplateCategory.CENTRALITY_ANALYSIS,
            cypher_template="""
            MATCH (e:Entity)
            {where_clause}
            OPTIONAL MATCH (e)-[r]-()
            WITH e, count(r) as degree
            OPTIONAL MATCH (e)<-[:MENTIONS]-(q:Quote)
            WITH e, degree, count(q) as quote_mentions
            RETURN e.name as entity_name,
                   e.entity_type as entity_type,
                   e as entity_properties,
                   degree as degree_centrality,
                   quote_mentions,
                   degree + quote_mentions as combined_centrality
            ORDER BY combined_centrality DESC
            {limit_clause}
            """,
            parameters={},
            parameter_descriptions={
                "entity_type": "Filter by entity type",
                "min_degree": "Minimum degree centrality",
                "limit": "Maximum number of results (default: 50)"
            },
            expected_columns=[
                "entity_name", "entity_type", "entity_properties", 
                "degree_centrality", "quote_mentions", "combined_centrality"
            ],
            complexity="medium",
            use_cases=[
                "Identify central entities",
                "Network importance ranking",
                "Key player analysis"
            ]
        )
        
    def _add_clustering_analysis_templates(self):
        """Add clustering analysis templates"""
        
        # Thematic clustering
        self.templates["thematic_clusters"] = QueryTemplate(
            id="thematic_clusters",
            name="Thematic Clustering Analysis",
            description="Find clusters of related codes and entities",
            category=TemplateCategory.CLUSTERING_ANALYSIS,
            cypher_template="""
            MATCH (c1:Code)<-[:SUPPORTS]-(q:Quote)-[:SUPPORTS]->(c2:Code)
            WHERE c1.name < c2.name
            WITH c1, c2, count(q) as shared_quotes
            WHERE shared_quotes >= $min_shared_quotes
            MATCH (c1)<-[:SUPPORTS]-(q1:Quote)-[:MENTIONS]->(e:Entity)
            MATCH (c2)<-[:SUPPORTS]-(q2:Quote)-[:MENTIONS]->(same_e:Entity)
            WHERE e = same_e
            WITH c1, c2, shared_quotes, count(DISTINCT e) as shared_entities
            RETURN c1.name as code1,
                   c2.name as code2,
                   shared_quotes,
                   shared_entities,
                   shared_quotes + shared_entities as cluster_strength
            ORDER BY cluster_strength DESC
            {limit_clause}
            """,
            parameters={"min_shared_quotes": 2},
            parameter_descriptions={
                "min_shared_quotes": "Minimum shared quotes for clustering",
                "min_shared_entities": "Minimum shared entities",
                "limit": "Maximum number of results (default: 100)"
            },
            expected_columns=["code1", "code2", "shared_quotes", "shared_entities", "cluster_strength"],
            complexity="high",
            use_cases=[
                "Identify theme clusters",
                "Group related concepts",
                "Simplify code structures"
            ]
        )
    
    def _add_longitudinal_analysis_templates(self):
        """Add longitudinal analysis templates for time-series pattern identification"""
        
        # Temporal theme evolution
        self.templates["temporal_theme_evolution"] = QueryTemplate(
            id="temporal_theme_evolution",
            name="Temporal Theme Evolution",
            description="Track how themes and codes change over time periods in interviews",
            category=TemplateCategory.LONGITUDINAL_ANALYSIS,
            cypher_template="""
            MATCH (q:Quote)-[:SUPPORTS]->(c:Code)
            MATCH (q)-[:FROM_INTERVIEW]->(i:Interview)
            WHERE c.name IN $theme_codes
            AND i.date_collected IS NOT NULL
            WITH i.date_collected as interview_date, c.name as theme, count(q) as frequency
            ORDER BY interview_date, frequency DESC
            RETURN interview_date, theme, frequency, 
                   collect({theme: theme, frequency: frequency})[..5] as top_themes_by_date
            """,
            parameters={"theme_codes": ["required_list"]},
            parameter_descriptions={
                "theme_codes": "List of theme/code names to track over time",
                "start_date": "Optional start date for analysis",
                "end_date": "Optional end date for analysis"
            },
            expected_columns=["interview_date", "theme", "frequency", "top_themes_by_date"],
            complexity="medium",
            use_cases=[
                "Track theme development over time",
                "Identify emerging or declining patterns",
                "Analyze longitudinal research data"
            ]
        )
        
        # Code frequency timeline
        self.templates["code_frequency_timeline"] = QueryTemplate(
            id="code_frequency_timeline",
            name="Code Frequency Timeline",
            description="Show frequency changes of codes across interview timeline",
            category=TemplateCategory.LONGITUDINAL_ANALYSIS,
            cypher_template="""
            MATCH (q:Quote)-[:SUPPORTS]->(c:Code)
            MATCH (q)-[:FROM_INTERVIEW]->(i:Interview)
            WHERE i.date_collected IS NOT NULL
            WITH date(i.date_collected) as interview_date, c.name as code_name, count(q) as mentions
            ORDER BY interview_date
            RETURN interview_date, code_name, mentions,
                   sum(mentions) OVER (PARTITION BY code_name ORDER BY interview_date) as cumulative_mentions
            """,
            parameters={},
            parameter_descriptions={
                "code_filter": "Optional list of specific codes to analyze",
                "date_grouping": "Group by day/week/month (default: day)"
            },
            expected_columns=["interview_date", "code_name", "mentions", "cumulative_mentions"],
            complexity="medium",
            use_cases=[
                "Visualize code usage patterns",
                "Identify saturation points",
                "Track conceptual development"
            ]
        )
        
        # Relationship changes over time
        self.templates["relationship_temporal_changes"] = QueryTemplate(
            id="relationship_temporal_changes",
            name="Relationship Temporal Changes",
            description="Track how relationships between entities change over interview periods",
            category=TemplateCategory.LONGITUDINAL_ANALYSIS,
            cypher_template="""
            MATCH (e1:Entity)<-[:MENTIONS]-(q:Quote)-[:MENTIONS]->(e2:Entity)
            MATCH (q)-[:FROM_INTERVIEW]->(i:Interview)
            WHERE e1.name < e2.name AND i.date_collected IS NOT NULL
            WITH date(i.date_collected) as interview_date, e1.name as entity1, e2.name as entity2, 
                 count(q) as co_mentions
            ORDER BY interview_date
            RETURN interview_date, entity1, entity2, co_mentions,
                   lag(co_mentions, 1) OVER (PARTITION BY entity1, entity2 ORDER BY interview_date) as previous_mentions,
                   co_mentions - lag(co_mentions, 1) OVER (PARTITION BY entity1, entity2 ORDER BY interview_date) as change
            """,
            parameters={},
            parameter_descriptions={
                "entity_types": "Optional filter for specific entity types",
                "min_mentions": "Minimum co-mentions to include relationship"
            },
            expected_columns=["interview_date", "entity1", "entity2", "co_mentions", "previous_mentions", "change"],
            complexity="high",
            use_cases=[
                "Track relationship strength changes",
                "Identify relationship emergence/decline",
                "Analyze social network evolution"
            ]
        )
    
    def _add_comparative_analysis_templates(self):
        """Add comparative analysis templates for cross-case and demographic comparisons"""
        
        # Cross-case theme comparison
        self.templates["cross_case_theme_comparison"] = QueryTemplate(
            id="cross_case_theme_comparison",
            name="Cross-Case Theme Comparison",
            description="Compare theme prevalence across different interviews or cases",
            category=TemplateCategory.COMPARATIVE_ANALYSIS,
            cypher_template="""
            MATCH (q:Quote)-[:SUPPORTS]->(c:Code)
            MATCH (q)-[:FROM_INTERVIEW]->(i:Interview)
            WHERE c.name IN $comparison_themes
            WITH i.interview_id as case_id, c.name as theme, count(q) as frequency
            ORDER BY case_id, frequency DESC
            RETURN case_id, theme, frequency,
                   frequency * 100.0 / sum(frequency) OVER (PARTITION BY case_id) as percentage_within_case,
                   rank() OVER (PARTITION BY case_id ORDER BY frequency DESC) as theme_rank_in_case
            """,
            parameters={"comparison_themes": ["required_list"]},
            parameter_descriptions={
                "comparison_themes": "List of themes/codes to compare across cases",
                "case_filter": "Optional filter for specific cases/interviews"
            },
            expected_columns=["case_id", "theme", "frequency", "percentage_within_case", "theme_rank_in_case"],
            complexity="medium",
            use_cases=[
                "Compare themes across participants",
                "Identify case-specific patterns",
                "Cross-case analysis in multiple case studies"
            ]
        )
        
        # Demographic pattern comparison
        self.templates["demographic_pattern_comparison"] = QueryTemplate(
            id="demographic_pattern_comparison", 
            name="Demographic Pattern Comparison",
            description="Compare coding patterns across different demographic groups",
            category=TemplateCategory.COMPARATIVE_ANALYSIS,
            cypher_template="""
            MATCH (s:Speaker)-[:SPOKE]->(q:Quote)-[:SUPPORTS]->(c:Code)
            WHERE s.demographic_group IS NOT NULL
            WITH s.demographic_group as group, c.name as code, count(q) as frequency
            ORDER BY group, frequency DESC
            RETURN group, code, frequency,
                   frequency * 100.0 / sum(frequency) OVER (PARTITION BY group) as percentage_within_group,
                   frequency * 100.0 / sum(frequency) OVER (PARTITION BY code) as percentage_of_code
            """,
            parameters={},
            parameter_descriptions={
                "demographic_field": "Speaker field to group by (default: demographic_group)",
                "code_filter": "Optional filter for specific codes"
            },
            expected_columns=["group", "code", "frequency", "percentage_within_group", "percentage_of_code"],
            complexity="medium",
            use_cases=[
                "Analyze demographic differences in responses",
                "Compare patterns across participant groups",
                "Identity-based qualitative analysis"
            ]
        )
        
        # Interview depth comparison
        self.templates["interview_depth_comparison"] = QueryTemplate(
            id="interview_depth_comparison",
            name="Interview Depth Comparison", 
            description="Compare depth and richness of different interviews",
            category=TemplateCategory.COMPARATIVE_ANALYSIS,
            cypher_template="""
            MATCH (i:Interview)<-[:FROM_INTERVIEW]-(q:Quote)
            WITH i.interview_id as interview_id,
                 count(q) as total_quotes,
                 count(DISTINCT (q)-[:SUPPORTS]->(:Code)) as unique_codes,
                 count(DISTINCT (q)-[:MENTIONS]->(:Entity)) as unique_entities,
                 avg(size(q.text)) as avg_quote_length
            RETURN interview_id, total_quotes, unique_codes, unique_entities, avg_quote_length,
                   unique_codes * 1.0 / total_quotes as code_diversity_ratio,
                   unique_entities * 1.0 / total_quotes as entity_diversity_ratio,
                   (unique_codes + unique_entities) * avg_quote_length / 1000.0 as richness_score
            ORDER BY richness_score DESC
            """,
            parameters={},
            parameter_descriptions={
                "interview_filter": "Optional filter for specific interviews",
                "richness_weights": "Custom weights for richness calculation"
            },
            expected_columns=["interview_id", "total_quotes", "unique_codes", "unique_entities", 
                            "avg_quote_length", "code_diversity_ratio", "entity_diversity_ratio", "richness_score"],
            complexity="medium",
            use_cases=[
                "Assess interview quality and depth",
                "Compare data saturation across interviews", 
                "Guide additional data collection"
            ]
        )
    
    def _add_sentiment_analysis_templates(self):
        """Add sentiment analysis templates for emotional and attitude analysis"""
        
        # Sentiment distribution by theme
        self.templates["sentiment_by_theme"] = QueryTemplate(
            id="sentiment_by_theme",
            name="Sentiment Distribution by Theme",
            description="Analyze sentiment patterns associated with different themes and codes",
            category=TemplateCategory.SENTIMENT_ANALYSIS,
            cypher_template="""
            MATCH (q:Quote)-[:SUPPORTS]->(c:Code)
            WHERE q.sentiment_score IS NOT NULL
            WITH c.name as theme, q.sentiment_score as sentiment,
                 CASE 
                     WHEN q.sentiment_score > 0.1 THEN 'positive'
                     WHEN q.sentiment_score < -0.1 THEN 'negative'
                     ELSE 'neutral'
                 END as sentiment_category
            RETURN theme, sentiment_category, count(*) as frequency,
                   avg(sentiment) as average_sentiment,
                   stdev(sentiment) as sentiment_deviation,
                   min(sentiment) as min_sentiment,
                   max(sentiment) as max_sentiment
            ORDER BY theme, sentiment_category
            """,
            parameters={},
            parameter_descriptions={
                "sentiment_field": "Field containing sentiment scores (default: sentiment_score)",
                "theme_filter": "Optional filter for specific themes",
                "threshold_positive": "Threshold for positive sentiment (default: 0.1)",
                "threshold_negative": "Threshold for negative sentiment (default: -0.1)"
            },
            expected_columns=["theme", "sentiment_category", "frequency", "average_sentiment", 
                            "sentiment_deviation", "min_sentiment", "max_sentiment"],
            complexity="medium",
            use_cases=[
                "Understand emotional associations with themes",
                "Identify polarizing topics",
                "Analyze stakeholder attitudes"
            ]
        )
        
        # Sentiment evolution over interview
        self.templates["sentiment_evolution"] = QueryTemplate(
            id="sentiment_evolution",
            name="Sentiment Evolution Pattern",
            description="Track how sentiment changes throughout individual interviews or across time",
            category=TemplateCategory.SENTIMENT_ANALYSIS,
            cypher_template="""
            MATCH (q:Quote)-[:FROM_INTERVIEW]->(i:Interview)
            WHERE q.sentiment_score IS NOT NULL AND q.sequence_position IS NOT NULL
            WITH i.interview_id as interview_id, q.sequence_position as position, q.sentiment_score as sentiment
            ORDER BY interview_id, position
            RETURN interview_id, position, sentiment,
                   avg(sentiment) OVER (PARTITION BY interview_id ORDER BY position ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING) as smoothed_sentiment,
                   sentiment - lag(sentiment, 1) OVER (PARTITION BY interview_id ORDER BY position) as sentiment_change
            """,
            parameters={},
            parameter_descriptions={
                "window_size": "Size of smoothing window (default: 5)",
                "interview_filter": "Optional filter for specific interviews"
            },
            expected_columns=["interview_id", "position", "sentiment", "smoothed_sentiment", "sentiment_change"],
            complexity="medium",
            use_cases=[
                "Track emotional journey in narratives",
                "Identify sentiment turning points",
                "Analyze interview dynamics"
            ]
        )
        
        # Entity sentiment associations
        self.templates["entity_sentiment_profile"] = QueryTemplate(
            id="entity_sentiment_profile",
            name="Entity Sentiment Profile",
            description="Analyze sentiment patterns associated with specific entities or people",
            category=TemplateCategory.SENTIMENT_ANALYSIS,
            cypher_template="""
            MATCH (q:Quote)-[:MENTIONS]->(e:Entity)
            WHERE q.sentiment_score IS NOT NULL
            WITH e.name as entity, e.entity_type as entity_type, 
                 collect(q.sentiment_score) as sentiments
            RETURN entity, entity_type,
                   size(sentiments) as mention_count,
                   avg(sentiments) as average_sentiment,
                   stdev(sentiments) as sentiment_variability,
                   percentileCont(sentiments, 0.25) as q1_sentiment,
                   percentileCont(sentiments, 0.50) as median_sentiment,
                   percentileCont(sentiments, 0.75) as q3_sentiment
            ORDER BY average_sentiment DESC
            """,
            parameters={},
            parameter_descriptions={
                "entity_type_filter": "Optional filter for specific entity types",
                "min_mentions": "Minimum mentions required (default: 3)"
            },
            expected_columns=["entity", "entity_type", "mention_count", "average_sentiment",
                            "sentiment_variability", "q1_sentiment", "median_sentiment", "q3_sentiment"],
            complexity="medium",
            use_cases=[
                "Understand attitudes toward specific entities",
                "Identify most/least favorably mentioned entities",
                "Analyze stakeholder perceptions"
            ]
        )
    
    def _add_conceptual_relationships_templates(self):
        """Add templates for analyzing conceptual relationships and theoretical connections"""
        
        # Hierarchical code relationships
        self.templates["hierarchical_code_structure"] = QueryTemplate(
            id="hierarchical_code_structure",
            name="Hierarchical Code Structure Analysis",
            description="Identify hierarchical relationships and code clustering patterns",
            category=TemplateCategory.CONCEPTUAL_RELATIONSHIPS,
            cypher_template="""
            MATCH (c1:Code)<-[:SUPPORTS]-(q:Quote)-[:SUPPORTS]->(c2:Code)
            WHERE c1 <> c2
            WITH c1, c2, count(q) as co_occurrence_count
            WHERE co_occurrence_count >= $min_cooccurrence
            MATCH (c1)<-[:SUPPORTS]-(all_q1:Quote)
            MATCH (c2)<-[:SUPPORTS]-(all_q2:Quote)
            WITH c1, c2, co_occurrence_count, 
                 count(DISTINCT all_q1) as c1_total,
                 count(DISTINCT all_q2) as c2_total
            WITH c1, c2, co_occurrence_count, c1_total, c2_total,
                 co_occurrence_count * 1.0 / c1_total as c1_conditional_prob,
                 co_occurrence_count * 1.0 / c2_total as c2_conditional_prob
            RETURN c1.name as parent_code, c2.name as child_code,
                   co_occurrence_count, c1_total, c2_total,
                   c1_conditional_prob, c2_conditional_prob,
                   CASE 
                       WHEN c1_conditional_prob > 0.7 THEN 'c2_subset_of_c1'
                       WHEN c2_conditional_prob > 0.7 THEN 'c1_subset_of_c2'
                       WHEN c1_conditional_prob > 0.4 AND c2_conditional_prob > 0.4 THEN 'strongly_related'
                       ELSE 'moderately_related'
                   END as relationship_type
            ORDER BY co_occurrence_count DESC
            """,
            parameters={"min_cooccurrence": 3},
            parameter_descriptions={
                "min_cooccurrence": "Minimum co-occurrences to consider relationship",
                "subset_threshold": "Threshold for subset relationship (default: 0.7)",
                "related_threshold": "Threshold for strong relationship (default: 0.4)"
            },
            expected_columns=["parent_code", "child_code", "co_occurrence_count", "c1_total", "c2_total",
                            "c1_conditional_prob", "c2_conditional_prob", "relationship_type"],
            complexity="high",
            use_cases=[
                "Build conceptual hierarchies",
                "Identify parent-child code relationships",
                "Develop theoretical frameworks"
            ]
        )
        
        # Theoretical connection patterns
        self.templates["theoretical_connection_patterns"] = QueryTemplate(
            id="theoretical_connection_patterns",
            name="Theoretical Connection Patterns",
            description="Identify patterns that suggest theoretical connections between concepts",
            category=TemplateCategory.CONCEPTUAL_RELATIONSHIPS,
            cypher_template="""
            MATCH path = (c1:Code)<-[:SUPPORTS]-(q1:Quote)-[:FROM_INTERVIEW]->(i:Interview)<-[:FROM_INTERVIEW]-(q2:Quote)-[:SUPPORTS]->(c2:Code)
            WHERE c1 <> c2
            MATCH (q1)-[:MENTIONS]->(e1:Entity)<-[:MENTIONS]-(q2)
            WITH c1, c2, count(DISTINCT i) as shared_interviews,
                 count(DISTINCT e1) as shared_entities,
                 collect(DISTINCT i.interview_id) as interview_list
            WHERE shared_interviews >= $min_shared_contexts
            MATCH (c1)<-[:SUPPORTS]-(all_q1:Quote)
            MATCH (c2)<-[:SUPPORTS]-(all_q2:Quote)
            WITH c1, c2, shared_interviews, shared_entities, interview_list,
                 count(DISTINCT all_q1) as c1_frequency,
                 count(DISTINCT all_q2) as c2_frequency
            RETURN c1.name as concept1, c2.name as concept2,
                   shared_interviews, shared_entities, c1_frequency, c2_frequency,
                   shared_interviews * 1.0 / (c1_frequency + c2_frequency) as connection_strength,
                   interview_list[..3] as sample_contexts
            ORDER BY connection_strength DESC
            """,
            parameters={"min_shared_contexts": 2},
            parameter_descriptions={
                "min_shared_contexts": "Minimum shared interview contexts for connection",
                "connection_strength_threshold": "Minimum strength for theoretical connection"
            },
            expected_columns=["concept1", "concept2", "shared_interviews", "shared_entities", 
                            "c1_frequency", "c2_frequency", "connection_strength", "sample_contexts"],
            complexity="high",
            use_cases=[
                "Identify theoretical relationships",
                "Build conceptual models",
                "Develop grounded theory connections"
            ]
        )
        
        # Concept evolution patterns
        self.templates["concept_evolution_patterns"] = QueryTemplate(
            id="concept_evolution_patterns",
            name="Concept Evolution Patterns",
            description="Track how concepts evolve and relate to each other across data collection",
            category=TemplateCategory.CONCEPTUAL_RELATIONSHIPS,
            cypher_template="""
            MATCH (c:Code)<-[:SUPPORTS]-(q:Quote)-[:FROM_INTERVIEW]->(i:Interview)
            WHERE i.date_collected IS NOT NULL
            WITH c.name as concept, date(i.date_collected) as collection_date, count(q) as mentions
            ORDER BY concept, collection_date
            WITH concept, collect({date: collection_date, mentions: mentions}) as evolution_data
            UNWIND range(0, size(evolution_data)-2) as idx
            WITH concept, evolution_data[idx] as current, evolution_data[idx+1] as next
            RETURN concept,
                   current.date as from_date,
                   next.date as to_date,
                   current.mentions as from_mentions,
                   next.mentions as to_mentions,
                   next.mentions - current.mentions as change,
                   (next.mentions - current.mentions) * 1.0 / current.mentions as growth_rate
            ORDER BY concept, from_date
            """,
            parameters={},
            parameter_descriptions={
                "concept_filter": "Optional filter for specific concepts",
                "date_range": "Optional date range for analysis"
            },
            expected_columns=["concept", "from_date", "to_date", "from_mentions", "to_mentions", "change", "growth_rate"],
            complexity="medium",
            use_cases=[
                "Track concept development over time",
                "Identify emerging vs declining concepts",
                "Analyze theoretical saturation"
            ]
        )
    
    def get_template(self, template_id: str) -> Optional[QueryTemplate]:
        """Get a specific query template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[TemplateCategory] = None) -> List[QueryTemplate]:
        """List all templates, optionally filtered by category"""
        if category is None:
            return list(self.templates.values())
        return [t for t in self.templates.values() if t.category == category]
    
    def get_template_categories(self) -> List[str]:
        """Get all available template categories"""
        return [cat.value for cat in TemplateCategory]
    
    def list_templates_by_category(self, category: str) -> List[QueryTemplate]:
        """List templates filtered by category string (backward compatibility method)"""
        # Convert string to TemplateCategory enum
        try:
            category_enum = TemplateCategory(category)
            return self.list_templates(category=category_enum)
        except ValueError:
            # If invalid category string, return empty list
            logger.warning(f"Invalid template category: {category}")
            return []
    
    def build_query(self, template_id: str, parameters: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """Build a complete Cypher query from a template"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")
        
        # Merge default parameters with provided ones
        final_params = {**template.parameters}
        if parameters:
            final_params.update(parameters)
        
        # Build WHERE clause if entity/code filters provided
        where_conditions = []
        if 'entity_type' in final_params:
            where_conditions.append("e.entity_type = $entity_type")
        if 'entity_filter' in final_params:
            where_conditions.append("e.name CONTAINS $entity_filter")
        if 'code_filter' in final_params:
            where_conditions.append("c.name IN $code_filter")
        if 'interview_filter' in final_params:
            where_conditions.append("q.interview_id = $interview_filter")
        if 'speaker_filter' in final_params:
            where_conditions.append("q.speaker_name = $speaker_filter")
        if 'min_degree' in final_params:
            where_conditions.append("degree >= $min_degree")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Build LIMIT clause
        limit_clause = ""
        if 'limit' in final_params:
            limit_clause = f"LIMIT {final_params['limit']}"
        
        # Format the template
        cypher = template.cypher_template.format(
            where_clause=where_clause,
            limit_clause=limit_clause
        ).strip()
        
        # Clean up multiple newlines and spaces
        cypher = '\n'.join(line.strip() for line in cypher.split('\n') if line.strip())
        
        return cypher, final_params


class QueryTemplateExecutor:
    """Executes query templates against Neo4j database"""
    
    def __init__(self, neo4j_manager):
        self.neo4j = neo4j_manager
        self.library = QueryTemplateLibrary()
    
    async def execute_template(self, template_id: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a query template and return results"""
        try:
            template = self.library.get_template(template_id)
            if not template:
                raise ValueError(f"Template '{template_id}' not found")
            
            # Build the query
            cypher, final_params = self.library.build_query(template_id, parameters)
            
            # Execute query
            import time
            start_time = time.time()
            results = await self.neo4j.execute_cypher(cypher, final_params)
            query_time_ms = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "template_id": template_id,
                "template_name": template.name,
                "description": template.description,
                "category": template.category.value,
                "cypher": cypher,
                "parameters": final_params,
                "results": results,
                "result_count": len(results),
                "query_time_ms": query_time_ms,
                "complexity": template.complexity,
                "expected_columns": template.expected_columns
            }
            
        except Exception as e:
            logger.error(f"Template execution failed: {e}")
            return {
                "success": False,
                "template_id": template_id,
                "error": str(e),
                "results": [],
                "result_count": 0
            }
    
    def list_available_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all available templates grouped by category"""
        templates_by_category = {}
        
        for category in TemplateCategory:
            templates = self.library.list_templates(category)
            templates_by_category[category.value] = [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "complexity": t.complexity,
                    "use_cases": t.use_cases,
                    "expected_columns": t.expected_columns,
                    "parameters": t.parameter_descriptions
                }
                for t in templates
            ]
        
        return templates_by_category
    
    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific template"""
        template = self.library.get_template(template_id)
        if not template:
            return None
        
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category.value,
            "complexity": template.complexity,
            "use_cases": template.use_cases,
            "parameters": template.parameter_descriptions,
            "example_parameters": template.example_parameters,
            "expected_columns": template.expected_columns,
            "cypher_template": template.cypher_template
        }


# Example usage and testing
async def demo_query_templates():
    """Demonstrate query template usage"""
    print("🎯 Neo4j Query Templates Demo")
    print("=" * 50)
    
    # Initialize the library
    library = QueryTemplateLibrary()
    
    print(f"\n📋 Available Templates: {len(library.templates)}")
    
    # List templates by category
    for category in TemplateCategory:
        templates = library.list_templates(category)
        print(f"\n{category.value.upper()}:")
        for template in templates:
            print(f"  • {template.name} ({template.complexity})")
            print(f"    {template.description}")
    
    # Show example query building
    print(f"\n🔧 Example Query Building:")
    
    # Build code co-occurrence query
    cypher, params = library.build_query("code_cooccurrence", {
        "min_cooccurrence": 3,
        "limit": 10
    })
    
    print(f"\nTemplate: Code Co-occurrence Network")
    print(f"Parameters: {params}")
    print(f"Generated Cypher:")
    print(cypher)
    
    # Show template details
    print(f"\n📊 Template Details:")
    template = library.get_template("entity_influence")
    if template:
        print(f"Name: {template.name}")
        print(f"Category: {template.category.value}")
        print(f"Use Cases: {', '.join(template.use_cases)}")
        print(f"Expected Columns: {', '.join(template.expected_columns)}")
    
    print(f"\n✅ Query Templates Demo Complete!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_query_templates())
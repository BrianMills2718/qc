# Quote-Centric Architecture Implementation Plan

## Overview

**Current State**: Property-based quote storage where quotes are stored as arrays in entity/code properties
**Target State**: Quote-centric architecture with quotes as first-class nodes connected via relationships
**Location Identifier**: Line numbers (not timestamps) for all quote references

## Architecture Comparison

### Current Architecture (Property-Based)
```
Entity {
  name: "Gen Mouho", 
  source_quotes: ["Mouho was the force behind...", "Gen Mouho is the DCG..."]
}

Code {
  name: "military_leadership",
  quotes: ["Mouho was the force behind...", "Leadership structures vary..."]
}
```

### Target Architecture (Quote-Centric)
```
(:Quote {text: "Mouho was the force behind...", line_number: 45, interview_id: "africa_1"})
  -[:MENTIONS]-> (:Entity {name: "Gen Mouho"})
  -[:SUPPORTS]-> (:Code {name: "military_leadership"})
  -[:EVIDENCES]-> (:Relationship {type: "LEADS"})
```

## Implementation Strategy

### Phase 1: Schema Extension (Week 1)

#### 1.1 Quote Node Definition
```python
# qc/core/schema_config.py - Add Quote entity
"Quote": EntityDefinition(
    description="Individual quotes from interviews with line-based location tracking",
    properties={
        "text": PropertyDefinition(
            type=PropertyType.STRING,
            description="Full text of the quote",
            required=True
        ),
        "line_start": PropertyDefinition(
            type=PropertyType.INTEGER, 
            description="Starting line number of quote in source interview file",
            required=True
        ),
        "line_end": PropertyDefinition(
            type=PropertyType.INTEGER, 
            description="Ending line number of quote in source interview file",
            required=True
        ),
        "line_number": PropertyDefinition(
            type=PropertyType.INTEGER, 
            description="Primary line number (line_start) for backward compatibility",
            required=True
        ),
        "semantic_type": PropertyDefinition(
            type=PropertyType.STRING,
            description="Type of semantic unit: sentence, paragraph, line",
            required=False,
            default="paragraph"
        ),
        "interview_id": PropertyDefinition(
            type=PropertyType.STRING,
            description="Source interview identifier", 
            required=True
        ),
        "speaker": PropertyDefinition(
            type=PropertyType.STRING,
            description="Person speaking (if identifiable)",
            required=False
        ),
        "context": PropertyDefinition(
            type=PropertyType.STRING,
            description="Surrounding context for quote",
            required=False
        ),
        "confidence": PropertyDefinition(
            type=PropertyType.FLOAT,
            description="Extraction confidence score",
            required=False,
            default=0.0
        )
    },
    relationships={
        "mentions_entity": RelationshipDefinition(
            target_entity="Entity",
            relationship_type="MENTIONS",
            description="Quote mentions this entity"
        ),
        "supports_code": RelationshipDefinition(
            target_entity="Code", 
            relationship_type="SUPPORTS",
            description="Quote provides evidence for this code"
        ),
        "evidences_relationship": RelationshipDefinition(
            target_entity="Relationship",
            relationship_type="EVIDENCES", 
            description="Quote provides evidence for this relationship"
        )
    }
)
```

#### 1.2 Relationship Types
```python
# New relationship types for quote connections
QUOTE_RELATIONSHIPS = {
    "MENTIONS": "Quote explicitly mentions entity",
    "SUPPORTS": "Quote provides evidence for code/theme", 
    "EVIDENCES": "Quote supports relationship between entities",
    "CONTRADICTS": "Quote contradicts another quote/claim",
    "ELABORATES": "Quote provides additional detail"
}
```

#### 1.3 Neo4j Manager Extensions
```python
# qc/core/neo4j_manager.py - Add quote operations
async def create_quote_node(self, quote_data: Dict[str, Any]) -> str:
    """Create a quote node with line number location"""
    
async def link_quote_to_entity(self, quote_id: str, entity_id: str, 
                              relationship_type: str = "MENTIONS") -> bool:
    """Create relationship between quote and entity"""
    
async def link_quote_to_code(self, quote_id: str, code_id: str,
                            relationship_type: str = "SUPPORTS") -> bool:
    """Create relationship between quote and code"""

async def find_quotes_by_line_range(self, interview_id: str, 
                                   start_line: int, end_line: int) -> List[Dict]:
    """Find quotes within specific line range"""
    
async def create_quote_indexes(self):
    """Create optimized indexes for quote-centric queries"""
    indexes = [
        "CREATE INDEX quote_interview_line IF NOT EXISTS FOR (q:Quote) ON (q.interview_id, q.line_start)",
        "CREATE INDEX quote_text_search IF NOT EXISTS FOR (q:Quote) ON q.text",
        "CREATE INDEX quote_line_range IF NOT EXISTS FOR (q:Quote) ON (q.line_start, q.line_end)",
        "CREATE CONSTRAINT quote_unique IF NOT EXISTS FOR (q:Quote) REQUIRE (q.interview_id, q.line_start, q.text) IS UNIQUE"
    ]
    
    for index_query in indexes:
        try:
            await self.execute_cypher(index_query)
        except Exception as e:
            logger.warning(f"Index creation failed (may already exist): {e}")

async def optimize_quote_storage(self, relevance_threshold: float = 0.5):
    """Optimize quote storage by filtering low-relevance quotes"""
    # Only store quotes that have entity or code relationships
    cleanup_query = """
    MATCH (q:Quote)
    WHERE NOT (q)-[:MENTIONS|SUPPORTS]->()
    AND q.confidence < $threshold
    DELETE q
    """
    await self.execute_cypher(cleanup_query, {"threshold": relevance_threshold})
```

### Phase 2: Extraction Pipeline Modification (Week 2)

#### 2.1 Line Number Extraction
```python
# qc/extraction/semantic_quote_extractor.py - NEW MODULE
class SemanticQuoteExtractor:
    """Extract semantically meaningful quotes with line range tracking"""
    
    def extract_semantic_quotes(self, text: str, interview_id: str) -> List[Dict]:
        """
        Extract semantic quote units (sentences/paragraphs) with line range precision
        
        Returns:
            List of quote dictionaries with line_start, line_end fields
        """
        quotes = []
        lines = text.split('\n')
        
        # Group lines into semantic units (paragraphs)
        paragraphs = self._group_into_paragraphs(lines)
        
        for paragraph_info in paragraphs:
            # Skip empty paragraphs and metadata
            if not paragraph_info['text'].strip() or paragraph_info['text'].startswith('#'):
                continue
            
            # For long paragraphs, extract individual sentences
            semantic_units = self._extract_sentences_if_needed(paragraph_info)
            
            for unit in semantic_units:
                quotes.append({
                    'text': unit['text'].strip(),
                    'line_start': unit['line_start'],
                    'line_end': unit['line_end'],
                    'line_number': unit['line_start'],  # For backward compatibility
                    'interview_id': interview_id,
                    'context': self._get_surrounding_context(lines, unit['line_start'], unit['line_end']),
                    'semantic_type': unit['type']  # 'sentence', 'paragraph', 'line'
                })
                
        return quotes
    
    def _group_into_paragraphs(self, lines: List[str]) -> List[Dict]:
        """Group consecutive non-empty lines into paragraphs"""
        paragraphs = []
        current_paragraph = []
        start_line = 1
        
        for line_num, line in enumerate(lines, 1):
            if line.strip():  # Non-empty line
                if not current_paragraph:
                    start_line = line_num
                current_paragraph.append(line.strip())
            else:  # Empty line - end current paragraph
                if current_paragraph:
                    paragraphs.append({
                        'text': ' '.join(current_paragraph),
                        'line_start': start_line,
                        'line_end': line_num - 1,
                        'type': 'paragraph'
                    })
                    current_paragraph = []
        
        # Handle final paragraph
        if current_paragraph:
            paragraphs.append({
                'text': ' '.join(current_paragraph),
                'line_start': start_line,
                'line_end': len(lines),
                'type': 'paragraph'
            })
        
        return paragraphs
    
    def _extract_sentences_if_needed(self, paragraph_info: Dict) -> List[Dict]:
        """Split long paragraphs into sentences for better granularity"""
        text = paragraph_info['text']
        
        # If paragraph is short enough, return as-is
        if len(text) <= 300:  # ~50 words
            return [paragraph_info]
        
        # Simple sentence splitting (can be enhanced with spaCy/NLTK)
        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            return [paragraph_info]
        
        # Estimate line ranges for sentences
        total_chars = len(text)
        line_range = paragraph_info['line_end'] - paragraph_info['line_start'] + 1
        
        sentence_units = []
        char_offset = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Estimate line position based on character position
            char_progress = char_offset / total_chars if total_chars > 0 else 0
            estimated_line_start = paragraph_info['line_start'] + int(char_progress * line_range)
            
            char_offset += len(sentence)
            char_progress_end = char_offset / total_chars if total_chars > 0 else 1
            estimated_line_end = paragraph_info['line_start'] + int(char_progress_end * line_range)
            
            sentence_units.append({
                'text': sentence,
                'line_start': estimated_line_start,
                'line_end': max(estimated_line_end, estimated_line_start),
                'type': 'sentence'
            })
        
        return sentence_units
    
    def _split_sentences(self, text: str) -> List[str]:
        """Simple sentence splitting (can be enhanced with NLP libraries)"""
        import re
        # Simple regex-based sentence splitting
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_surrounding_context(self, lines: List[str], 
                               target_line: int, context_size: int = 2) -> str:
        """Get surrounding lines for context"""
        start = max(0, target_line - context_size - 1)
        end = min(len(lines), target_line + context_size)
        context_lines = lines[start:end]
        return '\n'.join(context_lines)
```

#### 2.2 Modified Multi-Pass Extractor
```python
# qc/extraction/multi_pass_extractor.py - MODIFICATIONS
class SemanticCodeMatcher:
    """LLM-based semantic matching for quote-code relationships"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def evaluate_code_support(self, quote_text: str, code: Dict) -> Tuple[bool, float]:
        """
        Use LLM to determine if quote semantically supports a code
        
        Returns:
            Tuple[bool, float]: (supports_code, confidence_score)
        """
        prompt = f"""
        Analyze if this quote provides evidence for the given thematic code.
        
        QUOTE: "{quote_text}"
        
        CODE: {code['name']}
        DEFINITION: {code.get('definition', 'No definition provided')}
        
        Consider:
        1. Does the quote content semantically relate to the code theme?
        2. Does the quote provide evidence, examples, or discussion of the code concept?
        3. Is the relationship meaningful (not just coincidental word overlap)?
        
        Respond with JSON:
        {{
            "supports": true/false,
            "confidence": 0.0-1.0,
            "reasoning": "Brief explanation"
        }}
        """
        
        try:
            response = await self.llm.generate_structured(
                prompt, 
                response_schema={
                    "type": "object",
                    "properties": {
                        "supports": {"type": "boolean"},
                        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "reasoning": {"type": "string"}
                    },
                    "required": ["supports", "confidence", "reasoning"]
                }
            )
            
            return response["supports"], response["confidence"]
            
        except Exception as e:
            logger.warning(f"LLM semantic matching failed: {e}")
            # Fallback to conservative entity name matching
            return code['name'].lower() in quote_text.lower(), 0.5


class QuoteCentricMultiPassExtractor:
    """Modified extractor for quote-centric architecture with semantic analysis"""
    
    def __init__(self, neo4j_manager, schema, llm_client):
        self.neo4j = neo4j_manager
        self.schema = schema
        self.semantic_matcher = SemanticCodeMatcher(llm_client)
    
    async def extract_with_quotes(self, text: str, interview_id: str) -> Dict[str, Any]:
        """Extract entities, codes, relationships AND create quote nodes"""
        
        # Step 1: Extract semantic quotes with line range tracking
        quote_extractor = SemanticQuoteExtractor()
        raw_quotes = quote_extractor.extract_semantic_quotes(text, interview_id)
        
        # Step 2: Traditional extraction (entities, codes, relationships)
        extraction_result = await self.extract(text, interview_id)
        
        # Step 3: Create quote nodes
        quote_nodes = []
        for quote_data in raw_quotes:
            quote_id = await self.neo4j.create_quote_node(quote_data)
            quote_nodes.append({**quote_data, 'id': quote_id})
        
        # Step 4: Link quotes to extracted entities/codes/relationships
        await self._link_quotes_to_extractions(
            quote_nodes, 
            extraction_result['entities'],
            extraction_result['codes'], 
            extraction_result['relationships']
        )
        
        return {
            **extraction_result,
            'quotes': quote_nodes,
            'quote_entity_links': len(quote_nodes) * 2,  # Estimate
            'quote_code_links': len(quote_nodes) * 1.5   # Estimate  
        }
    
    async def _link_quotes_to_extractions(self, quotes: List[Dict], 
                                        entities: List[Dict],
                                        codes: List[Dict],
                                        relationships: List[Dict]):
        """Create relationships between quotes and extracted elements"""
        
        for quote in quotes:
            quote_text = quote['text'].lower()
            
            # Link to entities mentioned in quote
            for entity in entities:
                if entity['name'].lower() in quote_text:
                    await self.neo4j.link_quote_to_entity(
                        quote['id'], entity['id'], "MENTIONS"
                    )
            
            # Link to codes supported by quote using semantic analysis
            for code in codes:
                # Use LLM-based semantic analysis for accurate code support detection
                supports_code, confidence = await self._quote_supports_code(quote_text, code)
                if supports_code and confidence >= 0.7:  # High confidence threshold
                    await self.neo4j.link_quote_to_code(
                        quote['id'], code['id'], "SUPPORTS", properties={'confidence': confidence}
                    )
    
    async def _quote_supports_code(self, quote_text: str, code: Dict) -> Tuple[bool, float]:
        """Determine if quote provides evidence for code using LLM semantic analysis"""
        return await self.semantic_matcher.evaluate_code_support(quote_text, code)
```

### Phase 3: Query System Enhancement (Week 3)

#### 3.1 Quote-Aware Query Builder
```python
# qc/query/quote_aware_cypher_builder.py - NEW MODULE
class QuoteAwareCypherBuilder(CypherQueryBuilder):
    """Enhanced query builder with quote-centric capabilities"""
    
    def _build_entity_code_with_quotes_query(self, intent: QueryIntent) -> CypherQuery:
        """Build query that includes supporting quotes"""
        
        cypher = """
        MATCH (e:Entity)<-[:MENTIONS]-(q:Quote)-[:SUPPORTS]->(c:Code)
        WHERE ($entity_types IS NULL OR e.entity_type IN $entity_types)
          AND ($codes IS NULL OR c.name IN $codes)
        RETURN e.name as entity_name,
               e.entity_type as entity_type, 
               c.name as code_name,
               c.definition as code_definition,
               collect({
                   quote_text: q.text,
                   line_number: q.line_number,
                   interview_id: q.interview_id,
                   speaker: q.speaker,
                   context: q.context
               }) as supporting_quotes
        ORDER BY e.name, c.name
        """
        
        return CypherQuery(
            cypher=cypher,
            parameters={
                'entity_types': intent.target_entities if intent.target_entities else None,
                'codes': intent.codes if intent.codes else None
            },
            description=f"Find entity-code relationships with supporting quotes",
            estimated_complexity="medium",
            expected_result_type="entity-code-quotes"
        )
    
    def build_quote_search_query(self, search_text: str, 
                                interview_id: str = None,
                                line_range: Tuple[int, int] = None) -> CypherQuery:
        """Search quotes by text content, interview, or line range"""
        
        where_clauses = []
        params = {}
        
        if search_text:
            where_clauses.append("q.text CONTAINS $search_text")
            params['search_text'] = search_text
            
        if interview_id:
            where_clauses.append("q.interview_id = $interview_id")  
            params['interview_id'] = interview_id
            
        if line_range:
            where_clauses.append("q.line_number >= $start_line AND q.line_number <= $end_line")
            params['start_line'] = line_range[0]
            params['end_line'] = line_range[1]
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        cypher = f"""
        MATCH (q:Quote)
        {where_clause}
        OPTIONAL MATCH (q)-[:MENTIONS]->(e:Entity)
        OPTIONAL MATCH (q)-[:SUPPORTS]->(c:Code)
        RETURN q.text as quote_text,
               q.line_number as line_number,
               q.interview_id as interview_id,
               q.speaker as speaker,
               q.context as context,
               collect(DISTINCT e.name) as mentioned_entities,
               collect(DISTINCT c.name) as supported_codes
        ORDER BY q.interview_id, q.line_number
        """
        
        return CypherQuery(
            cypher=cypher,
            parameters=params,
            description=f"Search quotes with entity/code connections",
            estimated_complexity="low",
            expected_result_type="quote-search"
        )
```

#### 3.2 Cross-Analysis Enhancement
```python
# qc/analysis/cross_interview_analyzer.py - ENHANCEMENTS
class QuoteCentricCrossAnalyzer(CrossInterviewAnalyzer):
    """Enhanced cross-interview analysis with quote evidence"""
    
    async def analyze_consensus_with_evidence(self, 
                                           interview_ids: Optional[List[str]] = None,
                                           min_consensus_threshold: float = 0.6) -> List[ConsensusPattern]:
        """Find consensus patterns with supporting quote evidence"""
        
        # Enhanced query that includes quote evidence
        query = """
        MATCH (e:Entity)<-[:MENTIONS]-(q:Quote)-[:SUPPORTS]->(c:Code)
        WHERE ($interview_ids IS NULL OR q.interview_id IN $interview_ids)
        WITH c.name as code_name,
             e.entity_type as entity_type,
             collect(DISTINCT q.interview_id) as supporting_interviews,
             collect({
                 quote: q.text,
                 line: q.line_number, 
                 interview: q.interview_id,
                 entity: e.name
             }) as quote_evidence
        WITH code_name, entity_type, supporting_interviews, quote_evidence,
             size(supporting_interviews) as interview_count
        WHERE interview_count >= 2
        RETURN code_name, entity_type, supporting_interviews, 
               quote_evidence, interview_count
        ORDER BY interview_count DESC
        """
        
        result = await self.neo4j.execute_cypher(query, {"interview_ids": interview_ids})
        total_interviews = await self._get_total_interview_count(interview_ids)
        
        patterns = []
        for record in result:
            consensus_strength = record['interview_count'] / total_interviews
            
            if consensus_strength >= min_consensus_threshold:
                patterns.append(ConsensusPattern(
                    pattern_type="entity_code_consensus_with_quotes",
                    description=f"Consensus: {record['entity_type']} entities discuss {record['code_name']}",
                    supporting_interviews=record['supporting_interviews'],
                    supporting_count=record['interview_count'], 
                    total_interviews=total_interviews,
                    consensus_strength=consensus_strength,
                    evidence=record['quote_evidence'],  # Now includes actual quotes with line numbers
                    metadata={
                        'code_name': record['code_name'],
                        'entity_type': record['entity_type'],
                        'evidence_quotes': len(record['quote_evidence'])
                    }
                ))
        
        return patterns
    
    async def find_contradictory_quotes(self, topic: str, 
                                      interview_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Find quotes that contradict each other on same topic"""
        
        # Find quotes supporting different codes on same topic
        query = """
        MATCH (q1:Quote)-[:SUPPORTS]->(c1:Code),
              (q2:Quote)-[:SUPPORTS]->(c2:Code)
        WHERE c1.name CONTAINS $topic 
          AND c2.name CONTAINS $topic
          AND c1 <> c2
          AND ($interview_ids IS NULL OR q1.interview_id IN $interview_ids)
          AND ($interview_ids IS NULL OR q2.interview_id IN $interview_ids)
        RETURN q1.text as quote1,
               q1.line_number as line1,
               q1.interview_id as interview1,
               c1.name as code1,
               q2.text as quote2, 
               q2.line_number as line2,
               q2.interview_id as interview2,
               c2.name as code2
        """
        
        result = await self.neo4j.execute_cypher(query, {
            "topic": topic,
            "interview_ids": interview_ids
        })
        
        return {
            'contradictions': [dict(record) for record in result],
            'topic': topic,
            'contradiction_count': len(result)
        }
```

### Phase 4: Migration Strategy (Week 4)

#### 4.1 Dual-System Migration with Safety
```python
# qc/migration/safe_quote_migration.py - NEW MODULE
class HybridQuoteStorage:
    """Dual-system support for gradual quote-centric migration"""
    
    def __init__(self, neo4j_manager):
        self.neo4j = neo4j_manager
        self.quote_centric_enabled = False
        self.migration_status = None
    
    async def get_quotes_for_entity(self, entity_id: str) -> List[Dict]:
        """Get quotes with fallback from quote nodes to properties"""
        if self.quote_centric_enabled:
            # Try quote nodes first
            quote_nodes = await self._get_quote_nodes_for_entity(entity_id)
            if quote_nodes:
                return quote_nodes
        
        # Fallback to property-based quotes
        return await self._get_property_quotes_for_entity(entity_id)
    
    async def get_quotes_for_code(self, code_id: str) -> List[Dict]:
        """Get quotes with fallback from quote nodes to properties"""
        if self.quote_centric_enabled:
            # Try quote nodes first
            quote_nodes = await self._get_quote_nodes_for_code(code_id)
            if quote_nodes:
                return quote_nodes
        
        # Fallback to property-based quotes
        return await self._get_property_quotes_for_code(code_id)
    
    async def _get_quote_nodes_for_entity(self, entity_id: str) -> List[Dict]:
        """Get quotes from quote nodes linked to entity"""
        query = """
        MATCH (e:Entity {id: $entity_id})<-[:MENTIONS]-(q:Quote)
        RETURN q.text as text, q.line_start as line_start, q.line_end as line_end,
               q.interview_id as interview_id, q.context as context
        ORDER BY q.line_start
        """
        return await self.neo4j.execute_cypher(query, {"entity_id": entity_id})
    
    async def _get_property_quotes_for_entity(self, entity_id: str) -> List[Dict]:
        """Get quotes from entity source_quotes property"""
        query = """
        MATCH (e:Entity {id: $entity_id})
        WHERE exists(e.source_quotes)
        RETURN e.source_quotes as quotes, e.interview_id as interview_id
        """
        result = await self.neo4j.execute_cypher(query, {"entity_id": entity_id})
        if not result:
            return []
        
        # Convert property quotes to standard format
        quotes = []
        for i, quote_text in enumerate(result[0]['quotes']):
            quotes.append({
                'text': quote_text,
                'line_start': (i + 1) * 10,  # Estimated
                'line_end': (i + 1) * 10,
                'interview_id': result[0]['interview_id'],
                'context': None
            })
        return quotes


class SafeQuoteCentricMigration:
    """Migration with rollback support and validation"""
    
    def __init__(self, neo4j_manager, hybrid_storage):
        self.neo4j = neo4j_manager
        self.hybrid = hybrid_storage
        self.migration_log = []
    
    async def migrate_with_validation(self, batch_size: int = 100, enable_rollback: bool = True):
        """Migrate existing quote arrays to quote nodes with safety measures"""
        
        try:
            # Step 1: Create backup point
            if enable_rollback:
                print("💾 Creating migration backup...")
                backup_id = await self._create_migration_backup()
                self.migration_log.append({"action": "backup_created", "id": backup_id})
            
            # Step 2: Extract and validate existing data
            print("📊 Analyzing existing quote data...")
            validation_result = await self._validate_existing_data()
            if not validation_result['can_migrate']:
                raise MigrationError(f"Pre-migration validation failed: {validation_result['issues']}")
            
            # Step 3: Enable dual-system mode
            print("🔄 Enabling dual-system mode...")
            self.hybrid.quote_centric_enabled = False  # Start with fallback mode
            
            # Step 4: Migrate in batches with validation
            print("📦 Migrating data in batches...")
            await self._migrate_in_batches(batch_size)
            
            # Step 5: Validate migration results
            print("✅ Validating migration results...")
            migration_validation = await self._validate_migration_results()
            
            if migration_validation['success']:
                # Step 6: Enable quote-centric mode
                print("🚀 Switching to quote-centric mode...")
                self.hybrid.quote_centric_enabled = True
                
                # Step 7: Final validation
                final_validation = await self._final_system_validation()
                if final_validation['success']:
                    print("✅ Migration completed successfully!")
                    return {"success": True, "migrated_quotes": migration_validation['quote_count']}
                else:
                    raise MigrationError("Final validation failed")
            else:
                raise MigrationError("Migration validation failed")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            if enable_rollback:
                print("🔄 Rolling back migration...")
                await self._rollback_migration()
            raise
    
    async def _create_migration_backup(self) -> str:
        """Create backup of current quote data"""
        # Implementation for creating backup
        backup_id = f"migration_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        # Store current state in backup tables/files
        return backup_id
    
    async def _rollback_migration(self):
        """Rollback migration to previous state"""
        print("🔄 Performing rollback...")
        # Disable quote-centric mode
        self.hybrid.quote_centric_enabled = False
        # Remove created quote nodes
        await self.neo4j.execute_cypher("MATCH (q:Quote) DELETE q")
        # Restore from backup if needed
        print("✅ Rollback completed")
    
    async def _extract_entity_quotes(self) -> List[Dict]:
        """Extract all quotes from entity source_quotes arrays"""
        query = """
        MATCH (e:Entity)
        WHERE exists(e.source_quotes) AND size(e.source_quotes) > 0
        RETURN e.id as entity_id, 
               e.name as entity_name,
               e.source_quotes as quotes,
               e.interview_id as interview_id
        """
        return await self.neo4j.execute_cypher(query)
    
    async def _extract_code_quotes(self) -> List[Dict]:
        """Extract all quotes from code quotes arrays"""
        query = """
        MATCH (c:Code)
        WHERE exists(c.quotes) AND size(c.quotes) > 0
        RETURN c.id as code_id,
               c.name as code_name, 
               c.quotes as quotes,
               c.session_id as session_id
        """
        return await self.neo4j.execute_cypher(query)
    
    async def _create_quote_nodes(self, entity_quotes: List[Dict], 
                                code_quotes: List[Dict], batch_size: int):
        """Create quote nodes from extracted quotes"""
        
        all_quotes = set()  # Deduplicate quotes
        
        # Process entity quotes
        for entity_data in entity_quotes:
            for i, quote_text in enumerate(entity_data['quotes']):
                # Estimate line number based on position
                estimated_line = (i + 1) * 10  # Rough estimate
                
                quote_key = (quote_text, entity_data['interview_id'])
                if quote_key not in all_quotes:
                    all_quotes.add(quote_key)
                    
                    await self.neo4j.create_quote_node({
                        'text': quote_text,
                        'line_number': estimated_line,
                        'interview_id': entity_data['interview_id'],
                        'migration_source': 'entity',
                        'original_entity': entity_data['entity_name']
                    })
        
        # Process code quotes similarly...
    
    async def _create_quote_relationships(self, entity_quotes: List[Dict], 
                                        code_quotes: List[Dict]):
        """Create relationships between quotes and entities/codes"""
        
        # Link quotes to entities that originally contained them
        for entity_data in entity_quotes:
            for quote_text in entity_data['quotes']:
                # Find the quote node we created
                find_quote_query = """
                MATCH (q:Quote), (e:Entity)
                WHERE q.text = $quote_text 
                  AND q.interview_id = $interview_id
                  AND e.id = $entity_id
                CREATE (q)-[:MENTIONS]->(e)
                """
                
                await self.neo4j.execute_cypher(find_quote_query, {
                    'quote_text': quote_text,
                    'interview_id': entity_data['interview_id'],
                    'entity_id': entity_data['entity_id']
                })
        
        # Link quotes to codes similarly...
```

#### 4.2 Validation and Testing
```python
# qc/migration/migration_validator.py - NEW MODULE
class MigrationValidator:
    """Validate quote-centric migration results"""
    
    async def validate_migration(self) -> Dict[str, Any]:
        """Comprehensive validation of migration results"""
        
        validation_results = {
            'quote_node_count': await self._count_quote_nodes(),
            'entity_quote_links': await self._count_entity_quote_links(),
            'code_quote_links': await self._count_code_quote_links(),
            'line_number_coverage': await self._validate_line_numbers(),
            'data_consistency': await self._check_data_consistency(),
            'cross_analysis_functionality': await self._test_cross_analysis()
        }
        
        validation_results['overall_success'] = all([
            validation_results['quote_node_count'] > 0,
            validation_results['entity_quote_links'] > 0,
            validation_results['code_quote_links'] > 0,
            validation_results['data_consistency']['consistent'],
            validation_results['cross_analysis_functionality']['working']
        ])
        
        return validation_results
    
    async def _test_cross_analysis(self) -> Dict[str, Any]:
        """Test that cross-analysis still works with new architecture"""
        
        # Test basic cross-analysis query
        test_query = """
        MATCH (e:Entity)<-[:MENTIONS]-(q:Quote)-[:SUPPORTS]->(c:Code)
        RETURN count(*) as cross_links,
               collect(DISTINCT e.entity_type) as entity_types,
               collect(DISTINCT c.name)[0..5] as sample_codes
        """
        
        result = await self.neo4j.execute_cypher(test_query)
        
        return {
            'working': len(result) > 0 and result[0]['cross_links'] > 0,
            'cross_links_found': result[0]['cross_links'] if result else 0,
            'entity_types_connected': result[0]['entity_types'] if result else [],
            'sample_codes_connected': result[0]['sample_codes'] if result else []
        }
```

### Phase 5: CLI and API Updates (Week 5)

#### 5.1 Enhanced CLI Commands
```python
# qc/cli.py - NEW COMMANDS
@click.command()
@click.option('--search-text', help='Search quotes by text content')
@click.option('--interview-id', help='Filter by interview ID')
@click.option('--line-start', type=int, help='Start line number for range search')
@click.option('--line-end', type=int, help='End line number for range search')
@click.option('--show-context', is_flag=True, help='Show surrounding context')
async def search_quotes(search_text, interview_id, line_start, line_end, show_context):
    """Search quotes with line number precision"""
    
    neo4j = get_neo4j_manager()
    await neo4j.connect()
    
    try:
        schema = create_research_schema()
        parser = NaturalLanguageParser(schema)
        query_builder = QuoteAwareCypherBuilder(neo4j, parser)
        
        line_range = (line_start, line_end) if line_start and line_end else None
        
        cypher_query = query_builder.build_quote_search_query(
            search_text=search_text,
            interview_id=interview_id, 
            line_range=line_range
        )
        
        results = await neo4j.execute_cypher(
            cypher_query.cypher,
            cypher_query.parameters
        )
        
        # Format and display results
        click.echo(f"\n🔍 Found {len(results)} quotes")
        for result in results:
            click.echo(f"\n📝 Quote (Line {result['line_number']}):")
            click.echo(f"   \"{result['quote_text']}\"")
            click.echo(f"   📍 {result['interview_id']}")
            
            if result['mentioned_entities']:
                click.echo(f"   🏷️  Entities: {', '.join(result['mentioned_entities'])}")
            if result['supported_codes']:
                click.echo(f"   📊 Codes: {', '.join(result['supported_codes'])}")
            
            if show_context and result['context']:
                click.echo(f"   📖 Context:\n{result['context']}")
    
    finally:
        await neo4j.close()

@click.command()
@click.option('--topic', required=True, help='Topic to analyze for contradictions')
@click.option('--interview-ids', help='Comma-separated interview IDs to analyze')
async def find_contradictions(topic, interview_ids):
    """Find contradictory quotes on the same topic"""
    
    neo4j = get_neo4j_manager()
    await neo4j.connect()
    
    try:
        analyzer = QuoteCentricCrossAnalyzer(neo4j)
        
        interview_list = interview_ids.split(',') if interview_ids else None
        contradictions = await analyzer.find_contradictory_quotes(topic, interview_list)
        
        click.echo(f"\n🔍 Found {contradictions['contradiction_count']} contradictions on '{topic}'")
        
        for contradiction in contradictions['contradictions']:
            click.echo(f"\n❗ Contradiction:")
            click.echo(f"   Quote 1 (Line {contradiction['line1']}, {contradiction['interview1']}):")
            click.echo(f"     \"{contradiction['quote1']}\"")
            click.echo(f"     Supports: {contradiction['code1']}")
            
            click.echo(f"   Quote 2 (Line {contradiction['line2']}, {contradiction['interview2']}):")
            click.echo(f"     \"{contradiction['quote2']}\"") 
            click.echo(f"     Supports: {contradiction['code2']}")
    
    finally:
        await neo4j.close()
```

## Implementation Timeline

| Week | Phase | Focus | Deliverables |
|------|-------|-------|--------------|
| 1 | Schema Extension | Quote node definition, relationship types | Quote schema, Neo4j manager extensions |
| 2 | Extraction Pipeline | Line-based extraction, quote-entity linking | Modified multi-pass extractor |
| 3 | Query Enhancement | Quote-aware queries, cross-analysis with evidence | Enhanced query builders |
| 4 | Migration | Data migration, validation | Migration scripts, validation tools |
| 5 | Interface Updates | CLI commands, API endpoints | User-facing quote search tools |

## Success Metrics

### Technical Metrics
- ✅ **Quote Node Creation**: >90% of original quotes migrated to nodes
- ✅ **Line Number Accuracy**: Line numbers captured for >95% of quotes
- ✅ **Relationship Integrity**: Quote-entity and quote-code links preserve original connections
- ✅ **Query Performance**: Cross-analysis queries execute in <2 seconds
- ✅ **Data Consistency**: No quote duplication, proper deduplication maintained

### Functional Metrics  
- ✅ **Cross-Analysis Enhancement**: Quote evidence available for all consensus/divergence patterns
- ✅ **Traceability**: Every entity, code, relationship traceable to specific line numbers
- ✅ **Search Capability**: Full-text quote search with line number precision
- ✅ **Contradiction Detection**: Ability to identify conflicting quotes on same topics
- ✅ **Evidence Triangulation**: Multiple quote sources for same findings

### User Experience Metrics
- ✅ **CLI Functionality**: Quote search and contradiction detection commands working
- ✅ **API Endpoints**: REST endpoints for quote-based analysis
- ✅ **Documentation**: Clear usage examples for new quote-centric features
- ✅ **Migration Path**: Existing analyses remain functional post-migration

## Risk Mitigation

### Data Migration Risks
- **Quote Loss**: Backup existing data before migration, validate quote counts
- **Line Number Inaccuracy**: Use conservative estimation for legacy data
- **Performance Impact**: Batch operations, monitor query execution times

### Architecture Risks  
- **Storage Overhead**: Quote nodes increase storage ~2-3x, monitor disk usage
- **Query Complexity**: New relationship patterns may slow queries, optimize indexes
- **Backward Compatibility**: Maintain dual support during transition period

### Implementation Risks
- **Development Time**: Complex schema changes, allocate buffer time
- **Testing Coverage**: Comprehensive validation suite, automated testing
- **User Adoption**: Clear documentation, training materials

## Next Steps

1. **Immediate**: Review and approve this implementation plan
2. **Week 1**: Begin schema extension development
3. **Ongoing**: Create development branch for quote-centric work
4. **Pre-migration**: Full system backup and validation baseline
5. **Post-migration**: Performance monitoring and optimization

This plan transforms the qualitative coding system into a true quote-centric architecture with line-number precision, enabling advanced cross-analysis with complete provenance chains back to specific interview locations.
"""
Code-First Extraction Pipeline
Orchestrates the 4-phase extraction process
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import docx

from src.qc.extraction.code_first_schemas import (
    ExtractionConfig,
    ExtractionApproach,
    CodeTaxonomy,
    HierarchicalCode,
    SpeakerPropertySchema,
    DiscoveredSpeakerProperty,
    EntityRelationshipSchema,
    DiscoveredEntityType,
    DiscoveredRelationshipType,
    CodedInterview,
    EnhancedQuote,
    SpeakerInfo,
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionResults,
    GlobalEntity,
    GlobalRelationship,
    SimpleQuote,
    QuotesAndSpeakers,
    EntitiesAndRelationships,
    DialogueTurn,
    ConversationalContext,
    ThematicConnection
)
from src.qc.extraction.dialogue_processor import DialogueStructureDetector, DialogueAwareQuoteExtractor
from src.qc.extraction.schema_parser import SchemaParser, SchemaValidator
from src.qc.llm.llm_handler import LLMHandler
from src.qc.core.neo4j_manager import EnhancedNeo4jManager, EntityNode, RelationshipEdge
from src.qc.prompts.prompt_loader import PromptLoader
import logging

logger = logging.getLogger(__name__)


class CodeFirstExtractor:
    """Main extraction pipeline for code-first architecture"""
    
    def __init__(self, config: ExtractionConfig, llm_handler: Optional[LLMHandler] = None):
        """Initialize with configuration"""
        self.config = config
        self.llm = llm_handler or LLMHandler(model_name=config.llm_model)
        self.prompt_loader = PromptLoader()
        self.schema_parser = SchemaParser(self.llm)
        self.neo4j = EnhancedNeo4jManager(
            uri=config.neo4j_uri,
            username=config.neo4j_user,
            password=config.neo4j_password
        ) if config.auto_import_neo4j else None
        
        # Dialogue processing components (NEW)
        self.dialogue_detector = DialogueStructureDetector()
        self.dialogue_extractor = DialogueAwareQuoteExtractor(self.dialogue_detector)
        
        # Track extraction state
        self.code_taxonomy: Optional[CodeTaxonomy] = None
        self.speaker_schema: Optional[SpeakerPropertySchema] = None
        self.entity_schema: Optional[EntityRelationshipSchema] = None
        self.coded_interviews: List[CodedInterview] = []
        
        # Statistics
        self.total_tokens_used = 0
        self.start_time = None
    
    async def run_extraction(self) -> ExtractionResults:
        """
        Run the complete 4-phase extraction pipeline.
        Returns comprehensive extraction results.
        """
        logger.info("Starting code-first extraction pipeline")
        self.start_time = datetime.now()
        
        # Phase 0: Parse user-provided schemas (if closed/mixed)
        await self._run_phase_0()
        
        # Phase 1: Code taxonomy discovery
        await self._run_phase_1()
        
        # Phase 2: Speaker schema discovery
        await self._run_phase_2()
        
        # Phase 3: Entity/relationship schema discovery
        await self._run_phase_3()
        
        # Phase 4: Per-interview application
        await self._run_phase_4()
        
        # Aggregate global entities and relationships
        global_entities, global_relationships = self._aggregate_global_data()
        
        # Create final results
        results = ExtractionResults(
            config=self.config,
            code_taxonomy=self.code_taxonomy,
            speaker_schema=self.speaker_schema,
            entity_relationship_schema=self.entity_schema,
            coded_interviews=self.coded_interviews,
            global_entities=global_entities,
            global_relationships=global_relationships,
            total_interviews_processed=len(self.coded_interviews),
            total_quotes_extracted=sum(ci.total_quotes for ci in self.coded_interviews),
            total_unique_speakers=len(set(
                speaker.name for ci in self.coded_interviews 
                for speaker in ci.speakers
            )),
            total_unique_entities=len(global_entities),
            total_unique_relationships=len(global_relationships),
            extraction_timestamp=datetime.now().isoformat(),
            total_processing_time_seconds=(datetime.now() - self.start_time).total_seconds(),
            llm_tokens_used=int(self.total_tokens_used),
            overall_confidence=self._calculate_overall_confidence()
        )
        
        # Save outputs
        await self._save_outputs(results)
        
        # Import to Neo4j if configured
        if self.config.auto_import_neo4j:
            await self._import_to_neo4j(results)
        
        logger.info(f"Extraction complete. Processed {len(self.coded_interviews)} interviews")
        return results
    
    async def _run_phase_0(self):
        """Phase 0: Parse user-provided schema files for closed/mixed approaches"""
        logger.info("Phase 0: Parsing user-provided schemas")
        
        # Parse code schema if provided
        if self.config.coding_approach in [ExtractionApproach.CLOSED, ExtractionApproach.MIXED]:
            if self.config.predefined_codes_file:
                logger.info(f"Parsing code schema from: {self.config.predefined_codes_file}")
                parsed_codes = await self.schema_parser.parse_code_schema(
                    self.config.predefined_codes_file
                )
                
                # Validate
                is_valid, issues = SchemaValidator.validate_code_schema(parsed_codes)
                if not is_valid:
                    logger.warning(f"Code schema validation issues: {issues}")
                
                # Convert to taxonomy format if closed approach
                if self.config.coding_approach == ExtractionApproach.CLOSED:
                    self.code_taxonomy = self._convert_parsed_to_taxonomy(parsed_codes)
        
        # Parse speaker schema if provided
        if self.config.speaker_approach in [ExtractionApproach.CLOSED, ExtractionApproach.MIXED]:
            if self.config.predefined_speaker_schema_file:
                logger.info(f"Parsing speaker schema from: {self.config.predefined_speaker_schema_file}")
                parsed_speakers = await self.schema_parser.parse_speaker_schema(
                    self.config.predefined_speaker_schema_file
                )
                
                # Validate
                is_valid, issues = SchemaValidator.validate_speaker_schema(parsed_speakers)
                if not is_valid:
                    logger.warning(f"Speaker schema validation issues: {issues}")
                
                # Convert if closed approach
                if self.config.speaker_approach == ExtractionApproach.CLOSED:
                    self.speaker_schema = self._convert_parsed_to_speaker_schema(parsed_speakers)
        
        # Parse entity/relationship schema if provided
        if self.config.entity_approach in [ExtractionApproach.CLOSED, ExtractionApproach.MIXED]:
            if self.config.predefined_entity_schema_file:
                logger.info(f"Parsing entity schema from: {self.config.predefined_entity_schema_file}")
                parsed_entities = await self.schema_parser.parse_entity_schema(
                    self.config.predefined_entity_schema_file
                )
                
                # Validate
                is_valid, issues = SchemaValidator.validate_entity_schema(parsed_entities)
                if not is_valid:
                    logger.warning(f"Entity schema validation issues: {issues}")
                
                # Convert if closed approach
                if self.config.entity_approach == ExtractionApproach.CLOSED:
                    self.entity_schema = self._convert_parsed_to_entity_schema(parsed_entities)
    
    async def _run_phase_1(self):
        """Phase 1: Code taxonomy discovery from all interviews"""
        if self.config.coding_approach == ExtractionApproach.CLOSED:
            logger.info("Phase 1: Skipped (using predefined codes)")
            return
        
        logger.info("Phase 1: Discovering code taxonomy from all interviews")
        
        # Concatenate all interviews
        combined_text = await self._concatenate_interviews()
        
        # Build discovery prompt
        if self.config.coding_approach == ExtractionApproach.MIXED:
            prompt = self._build_mixed_code_discovery_prompt(
                combined_text, 
                self.code_taxonomy  # Pre-loaded from Phase 0
            )
        else:  # OPEN
            prompt = self._build_open_code_discovery_prompt(combined_text)
        
        # Extract taxonomy (single LLM call with all interviews)
        logger.info("Calling LLM for code discovery (this may take a while)...")
        self.code_taxonomy = await self.llm.extract_structured(
            prompt=prompt,
            schema=CodeTaxonomy,
            max_tokens=None  # Use maximum available
        )
        
        # Update token count
        self.total_tokens_used += len(prompt) / 4  # Rough estimate
        
        logger.info(f"Discovered {self.code_taxonomy.total_codes} codes in {self.code_taxonomy.hierarchy_depth} levels")
        
        # Save intermediate result
        await self._save_taxonomy()
    
    async def _run_phase_2(self):
        """Phase 2: Speaker property schema discovery"""
        if self.config.speaker_approach == ExtractionApproach.CLOSED:
            logger.info("Phase 2: Skipped (using predefined speaker schema)")
            return
        
        logger.info("Phase 2: Discovering speaker property schema from all interviews")
        
        # Use cached combined text or re-read
        combined_text = await self._concatenate_interviews()
        
        # Build discovery prompt
        if self.config.speaker_approach == ExtractionApproach.MIXED:
            prompt = self._build_mixed_speaker_discovery_prompt(
                combined_text,
                self.speaker_schema  # Pre-loaded from Phase 0
            )
        else:  # OPEN
            prompt = self._build_open_speaker_discovery_prompt(combined_text)
        
        # Extract speaker schema
        logger.info("Calling LLM for speaker schema discovery...")
        self.speaker_schema = await self.llm.extract_structured(
            prompt=prompt,
            schema=SpeakerPropertySchema,
            max_tokens=None
        )
        
        self.total_tokens_used += len(prompt) / 4
        
        logger.info(f"Discovered {len(self.speaker_schema.properties)} speaker properties")
        
        # Save intermediate result
        await self._save_speaker_schema()
    
    async def _run_phase_3(self):
        """Phase 3: Entity/relationship schema discovery"""
        if self.config.entity_approach == ExtractionApproach.CLOSED:
            logger.info("Phase 3: Skipped (using predefined entity schema)")
            return
        
        logger.info("Phase 3: Discovering entity/relationship schema from all interviews")
        
        # Use cached combined text or re-read
        combined_text = await self._concatenate_interviews()
        
        # Build discovery prompt
        if self.config.entity_approach == ExtractionApproach.MIXED:
            prompt = self._build_mixed_entity_discovery_prompt(
                combined_text,
                self.entity_schema  # Pre-loaded from Phase 0
            )
        else:  # OPEN
            prompt = self._build_open_entity_discovery_prompt(combined_text)
        
        # Extract entity/relationship schema
        logger.info("Calling LLM for entity/relationship schema discovery...")
        self.entity_schema = await self.llm.extract_structured(
            prompt=prompt,
            schema=EntityRelationshipSchema,
            max_tokens=None
        )
        
        self.total_tokens_used += len(prompt) / 4
        
        logger.info(f"Discovered {len(self.entity_schema.entity_types)} entity types and "
                   f"{len(self.entity_schema.relationship_types)} relationship types")
        
        # Save intermediate result
        await self._save_entity_schema()
    
    async def _run_phase_4(self):
        """Phase 4: Apply all schemas to each interview IN PARALLEL"""
        logger.info(f"Phase 4: Processing {len(self.config.interview_files)} interviews in parallel")
        
        # Add semaphore to limit concurrent API calls (prevent rate limiting)
        max_concurrent = getattr(self.config, 'max_concurrent_interviews', 5)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(interview_file):
            async with semaphore:
                return await self._process_single_interview(interview_file)
        
        # Process all interviews in parallel
        tasks = [
            process_with_semaphore(interview_file)
            for interview_file in self.config.interview_files
        ]
        
        # Wait for all interviews to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results and any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                interview_file = self.config.interview_files[i]
                logger.error(f"Failed to process {interview_file}: {result}")
                # Continue processing other interviews instead of failing completely
            else:
                self.coded_interviews.append(result)
                # Rough token estimate (based on measured data)
                self.total_tokens_used += 26000  # Based on measured ~26,843 tokens per interview
        
        logger.info(f"Phase 4 complete: {len(self.coded_interviews)} interviews processed successfully")
    
    async def _process_single_interview(self, interview_file: str) -> CodedInterview:
        """Process a single interview with dialogue-aware extraction"""
        logger.info(f"Processing interview: {interview_file}")
        
        # Auto-load taxonomy if not present (prevents regression from bypassing Phase 1)
        if self.code_taxonomy is None:
            await self._auto_load_existing_taxonomy()
        
        # Read interview content
        interview_text = self._read_interview_file(interview_file)
        interview_id = Path(interview_file).stem
        
        # NEW: Dialogue Structure Analysis
        logger.info(f"Analyzing dialogue structure for {interview_id}...")
        dialogue_turns = self.dialogue_detector.extract_dialogue_turns(interview_text, interview_id)
        conversational_contexts = self.dialogue_detector.build_conversational_contexts(dialogue_turns)
        
        interview_type = self.dialogue_detector.detect_interview_type(interview_text)
        logger.info(f"{interview_id}: Detected as {interview_type} with {len(dialogue_turns)} dialogue turns")
        
        # Phase 4A: Dialogue-aware quote extraction
        logger.info(f"Phase 4A for {interview_id}: Extracting quotes with dialogue structure...")
        
        if interview_type == "focus_group" and len(dialogue_turns) > 3:
            # FIXED: Route focus groups through LLM Call 4 (same as individual interviews)
            # Use original interview text instead of prepared text to avoid issues
            quotes_prompt = self._build_quotes_speakers_prompt(
                interview_text=interview_text,  # Use original text, not prepared text
                interview_id=interview_id,
                is_focus_group=True,
                dialogue_turns=dialogue_turns
            )
            
            quotes_and_speakers = await self.llm.extract_structured(
                prompt=quotes_prompt,
                schema=QuotesAndSpeakers,
                max_tokens=None
            )
            
            # Enhance quotes with dialogue structure information  
            quotes_and_speakers = self._enhance_quotes_with_dialogue_structure(
                quotes_and_speakers, dialogue_turns, conversational_contexts
            )
        else:
            # Use traditional extraction for individual interviews
            quotes_prompt = self._build_quotes_speakers_prompt(
                interview_text=interview_text,
                interview_id=interview_id
            )
            
            quotes_and_speakers = await self.llm.extract_structured(
                prompt=quotes_prompt,
                schema=QuotesAndSpeakers,
                max_tokens=None
            )
        
        logger.info(f"{interview_id}: Extracted {quotes_and_speakers.total_quotes} quotes with dialogue structure")
        
        # Phase 4A.5: Detect thematic connections (NEW)
        thematic_connections = []
        # Performance optimization: Disable expensive post-processing
        # Thematic connection detection integrated into Phase 4 quote extraction for focus groups
        logger.info(f"{interview_id}: Thematic connection post-processing disabled for performance optimization")
        
        # Phase 4B: Extract entities and relationships
        logger.info(f"Phase 4B for {interview_id}: Extracting entities and relationships...")
        entities_prompt = self._build_entities_relationships_prompt(
            interview_text=interview_text,
            interview_id=interview_id,
            quotes=quotes_and_speakers.quotes  # Pass quotes for context
        )
        
        entities_and_relationships = await self.llm.extract_structured(
            prompt=entities_prompt,
            schema=EntitiesAndRelationships,
            max_tokens=None
        )
        
        # Fix missing type fields in relationships
        from .relationship_fixer import fix_relationship_types
        entities_and_relationships = fix_relationship_types(entities_and_relationships)
        
        logger.info(f"{interview_id}: Extracted {entities_and_relationships.total_entities} entities and "
                   f"{entities_and_relationships.total_relationships} relationships")
        
        # Combine results into CodedInterview with dialogue context
        coded_interview = self._combine_extraction_results_with_dialogue(
            interview_id=interview_id,
            interview_file=interview_file,
            quotes_and_speakers=quotes_and_speakers,
            entities_and_relationships=entities_and_relationships,
            dialogue_turns=dialogue_turns,
            conversational_contexts=conversational_contexts,
            thematic_connections=thematic_connections  # NEW: Pass thematic connections
        )
        
        # Save individual interview result
        await self._save_coded_interview(coded_interview)
        
        logger.info(f"Completed interview: {interview_id}")
        return coded_interview
    
    def _convert_dialogue_quotes_to_schema(self, quotes_data: List[dict], 
                                         dialogue_turns: List[DialogueTurn]) -> QuotesAndSpeakers:
        """Convert dialogue-aware quotes to QuotesAndSpeakers schema"""
        simple_quotes = []
        speakers_dict = {}
        
        for quote_data in quotes_data:
            # Create SimpleQuote
            simple_quote = SimpleQuote(
                text=quote_data["text"],
                speaker_name=quote_data["speaker_name"],
                code_ids=quote_data.get("code_ids", []),  # Will be filled by LLM later
                location_start=quote_data["sequence_position"],
                location_end=quote_data["sequence_position"],
                location_type="dialogue_turn"
            )
            simple_quotes.append(simple_quote)
            
            # Track speakers
            speaker_name = quote_data["speaker_name"]
            if speaker_name not in speakers_dict:
                speakers_dict[speaker_name] = {
                    "quotes_count": 0,
                    "total_words": 0
                }
            speakers_dict[speaker_name]["quotes_count"] += 1
            speakers_dict[speaker_name]["total_words"] += len(quote_data["text"].split())
        
        # Create SpeakerInfo objects with dialogue patterns
        speakers = []
        total_turns = len(dialogue_turns)
        
        for speaker_name, stats in speakers_dict.items():
            # Find this speaker's turns for analysis
            speaker_turns = [turn for turn in dialogue_turns if turn.speaker_name == speaker_name]
            
            speaker_info = SpeakerInfo(
                name=speaker_name,
                confidence=0.9,  # High confidence from dialogue structure
                identification_method="dialogue_analysis",
                quotes_count=stats["quotes_count"],
                typical_turn_length=stats["total_words"] // max(len(speaker_turns), 1),
                interaction_frequency=len(speaker_turns) / total_turns if total_turns > 0 else 0.0,
                response_patterns=self._analyze_speaker_response_patterns(speaker_turns),
                topic_initiation_count=sum(1 for turn in speaker_turns if turn.turn_type == "question")
            )
            speakers.append(speaker_info)
        
        return QuotesAndSpeakers(
            quotes=simple_quotes,
            speakers=speakers,
            total_quotes=len(simple_quotes),
            total_codes_applied=sum(len(q.code_ids) for q in simple_quotes)
        )
    
    def _analyze_speaker_response_patterns(self, speaker_turns: List[DialogueTurn]) -> List[str]:
        """Analyze common response patterns for a speaker"""
        patterns = []
        
        # Count different types of responses
        agreement_count = sum(1 for turn in speaker_turns if turn.contains_response_markers)
        question_count = sum(1 for turn in speaker_turns if turn.contains_question)
        reference_count = sum(1 for turn in speaker_turns if turn.references_previous_speaker)
        
        total_turns = len(speaker_turns)
        if total_turns == 0:
            return patterns
        
        # Classify based on patterns
        if agreement_count / total_turns > 0.3:
            patterns.append("agreement")
        if question_count / total_turns > 0.2:
            patterns.append("questioning")
        if reference_count / total_turns > 0.2:
            patterns.append("building")
        if not patterns:
            patterns.append("statement")  # Default
        
        return patterns
    
    def _combine_extraction_results_with_dialogue(self, 
                                                 interview_id: str,
                                                 interview_file: str,
                                                 quotes_and_speakers: QuotesAndSpeakers,
                                                 entities_and_relationships: EntitiesAndRelationships,
                                                 dialogue_turns: List[DialogueTurn],
                                                 conversational_contexts: Dict[str, ConversationalContext],
                                                 thematic_connections: List[ThematicConnection] = None) -> CodedInterview:
        """Combine extraction results with dialogue structure preservation"""
        from datetime import datetime
        import uuid
        from .schema_validator import validate_extraction_results
        
        # Create enhanced quotes with dialogue context
        enhanced_quotes = []
        unique_codes = set()
        
        # Create lookup for dialogue turns
        turns_by_sequence = {turn.sequence_number: turn for turn in dialogue_turns}
        
        for i, simple_quote in enumerate(quotes_and_speakers.quotes):
            quote_id = f"{interview_id}_Q{i+1:03d}"
            
            # Find corresponding dialogue turn
            sequence_pos = simple_quote.location_start or (i + 1)
            dialogue_turn = turns_by_sequence.get(sequence_pos)
            
            # Find matching speaker
            speaker = next(
                (s for s in quotes_and_speakers.speakers 
                 if s.name == simple_quote.speaker_name),
                SpeakerInfo(
                    name=simple_quote.speaker_name,
                    confidence=0.5,
                    identification_method="from_quote",
                    quotes_count=1
                )
            )
            
            # Track unique codes
            unique_codes.update(simple_quote.code_ids)
            code_names = [self._get_code_name(code_id) for code_id in simple_quote.code_ids]
            
            # Find entities mentioned in this quote
            quote_entities = [
                e for e in entities_and_relationships.entities
                if e.name.lower() in simple_quote.text.lower()
            ]
            
            # Find relationships relevant to this quote
            quote_relationships = [
                r for r in entities_and_relationships.relationships
                if any(e.name == r.source_entity or e.name == r.target_entity 
                      for e in quote_entities)
            ]
            
            # Get or create conversational context
            turn_id = dialogue_turn.turn_id if dialogue_turn else f"{interview_id}_T{i+1:03d}"
            conv_context = conversational_contexts.get(turn_id, ConversationalContext())
            
            # Create dialogue turn if missing
            if not dialogue_turn:
                dialogue_turn = DialogueTurn(
                    turn_id=turn_id,
                    sequence_number=sequence_pos,
                    speaker_name=simple_quote.speaker_name,
                    raw_location=f"Quote {i+1}",
                    text=simple_quote.text,
                    word_count=len(simple_quote.text.split())
                )
            
            # Create enhanced quote with dialogue structure
            enhanced_quote = EnhancedQuote(
                id=quote_id,
                text=simple_quote.text,
                context_summary=f"Quote from {speaker.name} about {', '.join(code_names[:3])}",
                code_ids=simple_quote.code_ids,
                code_names=code_names,
                code_confidence_scores=[0.8] * len(simple_quote.code_ids),
                speaker=speaker,
                dialogue_turn=dialogue_turn,  # NEW: Dialogue structure
                conversational_context=conv_context,  # NEW: Conversational flow
                thematic_connection=simple_quote.thematic_connection,  # NEW: Thematic connection data
                connection_target=simple_quote.connection_target,
                connection_confidence=simple_quote.connection_confidence,
                connection_evidence=simple_quote.connection_evidence,
                interview_id=interview_id,
                interview_title=Path(interview_file).stem,
                line_start=simple_quote.location_start,
                line_end=simple_quote.location_end,
                sequence_position=sequence_pos,  # NEW: Position in conversation
                quote_entities=quote_entities[:5],
                quote_relationships=quote_relationships[:3],
                extraction_confidence=0.8
            )
            enhanced_quotes.append(enhanced_quote)
        
        # Validation (same as before)
        extraction_data = {
            'quotes': [{'id': f"{interview_id}_Q{i+1:03d}", 
                       'text': q.text, 
                       'code_ids': q.code_ids,
                       'speaker': {'name': q.speaker_name}} 
                      for i, q in enumerate(quotes_and_speakers.quotes)],
            'speakers': [s.dict() for s in quotes_and_speakers.speakers],
            'entities': [e.dict() for e in entities_and_relationships.entities],
            'relationships': [r.dict() for r in entities_and_relationships.relationships]
        }
        
        code_taxonomy_dict = self.code_taxonomy.dict() if self.code_taxonomy else {'codes': []}
        speaker_schema_dict = self.speaker_schema.dict() if self.speaker_schema else {'properties': []}
        entity_schema_dict = self.entity_schema.dict() if self.entity_schema else {'entity_types': [], 'relationship_types': []}
        
        validated_data = validate_extraction_results(
            extraction_data,
            code_taxonomy_dict,
            speaker_schema_dict,
            entity_schema_dict
        )
        
        # Log violations
        if validated_data.get('violations'):
            violations = validated_data['violations']
            if violations.get('invalid_codes'):
                logger.warning(f"Interview {interview_id}: Invalid codes detected and filtered: {violations['invalid_codes']}")
            if violations.get('invalid_entity_types'):
                logger.warning(f"Interview {interview_id}: Invalid entity types detected and filtered: {violations['invalid_entity_types']}")
            if violations.get('invalid_relationship_types'):
                logger.warning(f"Interview {interview_id}: Invalid relationship types detected and filtered: {violations['invalid_relationship_types']}")
        
        # Use validated entities and relationships
        validated_entities = [ExtractedEntity(**e) for e in validated_data['entities']]
        # Extract thematic connections from SimpleQuote objects (integrated approach)
        integrated_thematic_connections = []
        if thematic_connections is None:  # Only extract if not provided (avoid duplication)
            integrated_thematic_connections = self._extract_thematic_connections_from_quotes(
                quotes_and_speakers.quotes, interview_id
            )
        validated_relationships = [ExtractedRelationship(**r) for r in validated_data['relationships']]
        
        # Create coded interview with dialogue structure
        coded_interview = CodedInterview(
            interview_id=interview_id,
            interview_title=Path(interview_file).stem,
            interview_file=interview_file,
            quotes=enhanced_quotes,  # Now includes dialogue structure
            speakers=quotes_and_speakers.speakers,  # Enhanced with interaction patterns
            interview_entities=validated_entities,
            interview_relationships=validated_relationships,
            dialogue_turns=dialogue_turns,  # NEW: Dialogue structure
            thematic_connections=thematic_connections or [],  # NEW: Thematic connections
            total_quotes=len(enhanced_quotes),
            total_codes_applied=sum(len(q.code_ids) for q in enhanced_quotes),
            unique_codes_used=list(unique_codes),
            total_speakers=len(quotes_and_speakers.speakers),
            total_entities=len(validated_entities),
            total_relationships=len(validated_relationships),
            extraction_timestamp=datetime.now().isoformat(),
            extraction_confidence=0.8,
            processing_time_seconds=0.0
        )
        
        return coded_interview
    
    async def _concatenate_interviews(self) -> str:
        """Concatenate all interview files for phases 1-3"""
        combined_parts = []
        
        for interview_file in self.config.interview_files:
            content = self._read_interview_file(interview_file)
            interview_id = Path(interview_file).stem
            
            # Add header to identify interview boundaries
            combined_parts.append(f"\n\n{'='*80}")
            combined_parts.append(f"INTERVIEW: {interview_id}")
            combined_parts.append(f"FILE: {interview_file}")
            combined_parts.append(f"{'='*80}\n")
            combined_parts.append(content)
        
        return "\n".join(combined_parts)
    
    def _read_interview_file(self, file_path: str) -> str:
        """Read interview content from DOCX or TXT file"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Interview file not found: {file_path}")
        
        # Auto-detect format based on extension
        if path.suffix.lower() == '.docx':
            return self._read_docx(file_path)
        else:  # Assume text format
            return self._read_text_file(file_path)
    
    def _read_text_file(self, file_path: str) -> str:
        """Read text file with line markers"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Add line markers for LLM reference
        numbered_lines = []
        for i, line in enumerate(lines, 1):
            if line.strip():
                numbered_lines.append(f"[Line {i}] {line.strip()}")
        
        return "\n".join(numbered_lines)
    
    def _read_docx(self, file_path: str) -> str:
        """Read DOCX file content with paragraph markers"""
        doc = docx.Document(file_path)
        lines = []
        
        for i, paragraph in enumerate(doc.paragraphs, 1):
            if paragraph.text.strip():
                # Add paragraph marker for LLM reference
                lines.append(f"[Paragraph {i}] {paragraph.text.strip()}")
        
        return "\n".join(lines)
    
    def _build_open_code_discovery_prompt(self, combined_text: str) -> str:
        """Build prompt for open code discovery"""
        return self.prompt_loader.format_prompt(
            phase="phase1",
            template_name="open_code_discovery",
            num_interviews=len(self.config.interview_files),
            analytic_question=self.config.analytic_question,
            code_hierarchy_depth=self.config.code_hierarchy_depth,
            combined_text=combined_text,
            paradigm=self.config.paradigm
        )
    
    def _build_application_prompt(self, interview_text: str, interview_id: str, 
                                 interview_file: str) -> str:
        """Build prompt for applying all schemas to an interview"""
        return f"""
        You are applying discovered schemas to extract structured data from an interview.
        
        INTERVIEW: {interview_id}
        ANALYTIC QUESTION: {self.config.analytic_question}
        
        AVAILABLE CODES (from Phase 1):
        {self._format_codes_for_prompt()}
        
        SPEAKER PROPERTIES TO EXTRACT (from Phase 2):
        {self._format_speaker_schema_for_prompt()}
        
        ENTITY/RELATIONSHIP TYPES (from Phase 3):
        {self._format_entity_schema_for_prompt()}
        
        INSTRUCTIONS:
        1. QUOTE EXTRACTION WITH MANY-TO-MANY CODING:
           - CRITICAL: Extract AT LEAST 20-30 quotes from this interview (there are many substantive statements)
           - Look through the ENTIRE interview systematically - don't stop after finding a few quotes
           - Each speaker turn that contains substantive content should be a quote
           - Each quote should capture a complete thought or idea (use semantic boundaries)
           - IMPORTANT: Apply codes using the EXACT CODE IDs shown in brackets [CODE_ID] above
           - For example, if a quote discusses AI transcription, use the code ID: "AI_IMPACT_TRANSCRIPTION"
           - Most quotes will relate to MULTIPLE codes - analyze each quote against ALL codes
           - A quote discussing challenges with AI tools might have code_ids: ["AI_RISK_ACCURACY_NUANCE", "AI_TRUST_RELIABILITY", "AI_TRAINING_NEEDS"]
           - Be comprehensive in code assignment - it's better to over-code than under-code
           - Return the code_ids field with the exact IDs from the taxonomy, NOT the names
           
        2. SPEAKER IDENTIFICATION:
           - Identify speakers using all available contextual information
           - Look for explicit labels, document structure, conversational patterns
           - Extract ALL speaker properties defined in the schema for each identified speaker
           - Assign confidence scores based on clarity of identification
           
        3. ENTITY AND RELATIONSHIP EXTRACTION:
           - ACTIVELY SEARCH for all entity types defined in the schema
           - Entities are the important concepts, tools, methods, or actors mentioned
           - Extract entities at multiple levels:
             * Within each quote (what entities are discussed in this specific quote?)
             * Across the interview (what entities appear throughout?)
             * Mark entities that should be tracked globally across all interviews
           - RELATIONSHIPS: When entities co-occur or interact, capture their relationship
           - Look for relationships like: uses, challenges, benefits_from, compares_to, requires, impacts
           - Each relationship should connect two entities with a meaningful relationship type
           
        4. COMPREHENSIVENESS:
           - Every substantive statement should be captured as a quote
           - Every quote should be analyzed for ALL applicable codes (many-to-many is expected)
           - Every mentioned entity from the defined types should be extracted
           - Every meaningful connection between entities should be captured as a relationship
        
        INTERVIEW CONTENT:
        {interview_text}
        
        Extract all quotes, speakers, entities, and relationships according to the schemas.
        Be comprehensive - every relevant quote should be captured.
        """
    
    def _format_codes_for_prompt(self) -> str:
        """Format code taxonomy for prompt WITH IDs"""
        if not hasattr(self, "code_taxonomy") or self.code_taxonomy is None:
            return "No codes defined"
        lines = []
        for code in self.code_taxonomy.codes:
            indent = "  " * code.level
            # Include both ID and name so LLM can use the exact ID
            lines.append(f"{indent}- [{code.id}] {code.name}: {code.description}")
        return "\n".join(lines)
    
    def _get_code_name(self, code_id: str) -> str:
        """Get code name from ID"""
        if not hasattr(self, "code_taxonomy") or self.code_taxonomy is None:
            return code_id  # Return the ID itself if no taxonomy available
        for code in self.code_taxonomy.codes:
            if code.id == code_id:
                return code.name
        logger.warning(f"Code ID not found in taxonomy: {code_id}")
        return code_id  # Fallback to ID if not found
    
    def _format_speaker_schema_for_prompt(self) -> str:
        if not hasattr(self, "speaker_schema") or self.speaker_schema is None:
            return "No speaker properties defined"
        lines = []
        for prop in self.speaker_schema.properties:
            lines.append(f"- {prop.name} ({prop.property_type}): {prop.description or 'No description'}")
            if prop.possible_values:
                lines.append(f"  Possible values: {', '.join(prop.possible_values)}")
        return "\n".join(lines)
    
    def _prepare_focus_group_text_for_llm(self, dialogue_turns: List, conversational_contexts: Dict) -> str:
        """
        Prepare focus group dialogue turns for LLM processing
        
        Converts dialogue turns into structured text format that preserves 
        speaker information and conversational flow for LLM analysis.
        """
        text_sections = []
        
        for turn in dialogue_turns:
            # Create a clear speaker attribution
            speaker_info = f"[{turn.speaker_name}]"
            
            # Add conversation context markers for better thematic analysis
            context = conversational_contexts.get(turn.turn_id)
            if context and context.is_response_to:
                speaker_info += f" (responding to previous speaker)"
            
            # Format each semantic segment as a potential quote
            for segment in turn.semantic_segments:
                if len(segment.split()) >= 3:  # Lower threshold - include more content
                    text_sections.append(f"{speaker_info}: {segment}")
        
        return "\n\n".join(text_sections)
    
    def _enhance_quotes_with_dialogue_structure(self, quotes_and_speakers, dialogue_turns: List, 
                                              conversational_contexts: Dict):
        """
        Enhance LLM-extracted quotes with dialogue structure information
        
        Adds sequence positions and dialogue context to quotes extracted by LLM,
        preserving the conversational flow that was already reconstructed.
        """
        # Create mapping of text to dialogue turns for sequence position assignment
        turn_map = {}
        for turn in dialogue_turns:
            for segment in turn.semantic_segments:
                if len(segment.split()) >= 3:  # Lower threshold to match preparation
                    turn_map[segment[:100]] = turn  # Use first 100 chars as key
        
        # Enhance each quote with dialogue structure
        for quote in quotes_and_speakers.quotes:
            # Find matching turn by text similarity
            quote_text_key = quote.text[:100]
            matching_turn = None
            
            # Try to find exact match first
            if quote_text_key in turn_map:
                matching_turn = turn_map[quote_text_key]
            else:
                # Find best partial match
                for text_key, turn in turn_map.items():
                    if quote_text_key in text_key or text_key in quote_text_key:
                        matching_turn = turn
                        break
            
            # Add sequence position if found
            if matching_turn:
                quote.sequence_position = matching_turn.sequence_number
                quote.location_start = matching_turn.sequence_number
                quote.location_end = matching_turn.sequence_number
        
        return quotes_and_speakers
    
    def _validate_id_format(self, id_str: str, format_type: str) -> str:
        """Ensure ID follows expected format
        
        Args:
            id_str: The ID string to validate/normalize
            format_type: One of 'CAPS_SNAKE_CASE', 'CAPS', 'snake_case'
        
        Returns:
            Normalized ID string
        """
        if format_type == "CAPS_SNAKE_CASE":
            # Convert "AI Tool" → "AI_TOOL"
            return id_str.upper().replace(" ", "_").replace("-", "_")
        elif format_type == "CAPS":
            # Convert "Uses" → "USES"
            return id_str.upper().replace(" ", "_").replace("-", "_")
        elif format_type == "snake_case":
            # Convert "Years Experience" → "years_experience"
            return id_str.lower().replace(" ", "_").replace("-", "_")
        return id_str
    
    def _format_entity_schema_for_prompt(self) -> str:
        """Format entity/relationship schema for prompt"""
        if not hasattr(self, "entity_schema") or self.entity_schema is None:
            return "No entity types or relationship types defined"
        lines = ["ENTITY TYPES:"]
        for entity_type in self.entity_schema.entity_types:
            # Use ID if available, otherwise normalize name to ID format
            type_id = entity_type.id if hasattr(entity_type, 'id') else self._validate_id_format(entity_type.name, "CAPS_SNAKE_CASE")
            lines.append(f"- [{type_id}] {entity_type.name}: {entity_type.description}")
        
        lines.append("\nRELATIONSHIP TYPES:")
        for rel_type in self.entity_schema.relationship_types:
            # Use ID if available, otherwise normalize name to ID format
            rel_id = rel_type.id if hasattr(rel_type, 'id') else self._validate_id_format(rel_type.name, "CAPS")
            direction = "→" if rel_type.directional else "↔"
            lines.append(f"- [{rel_id}] {rel_type.name}: {rel_type.description}")
            lines.append(f"  ({', '.join(rel_type.common_source_types)} {direction} "
                        f"{', '.join(rel_type.common_target_types)})")
        
        return "\n".join(lines)
    
    def _aggregate_global_data(self) -> tuple[List[GlobalEntity], List[GlobalRelationship]]:
        """Aggregate entities and relationships across all interviews"""
        # Entity aggregation
        entity_map = {}
        for interview in self.coded_interviews:
            for entity in interview.interview_entities:
                key = (entity.name, entity.type)
                if key not in entity_map:
                    entity_map[key] = GlobalEntity(
                        name=entity.name,
                        type=entity.type,
                        total_mentions=0,
                        interview_ids=[],
                        quote_ids=[],
                        related_codes=[],
                        confidence=entity.confidence
                    )
                
                entity_map[key].total_mentions += entity.mention_count
                entity_map[key].interview_ids.append(interview.interview_id)
                
                # Find related codes through quotes
                for quote in interview.quotes:
                    if any(e.name == entity.name for e in quote.quote_entities):
                        entity_map[key].quote_ids.append(quote.id)
                        entity_map[key].related_codes.extend(quote.code_names)
        
        # Relationship aggregation
        relationship_map = {}
        for interview in self.coded_interviews:
            for rel in interview.interview_relationships:
                key = (rel.source_entity, rel.target_entity, rel.relationship_type)
                if key not in relationship_map:
                    relationship_map[key] = GlobalRelationship(
                        source_entity=rel.source_entity,
                        target_entity=rel.target_entity,
                        relationship_type=rel.relationship_type,
                        total_mentions=0,
                        interview_ids=[],
                        quote_ids=[],
                        related_codes=[],
                        confidence=rel.confidence
                    )
                
                relationship_map[key].total_mentions += 1
                relationship_map[key].interview_ids.append(interview.interview_id)
                relationship_map[key].quote_ids.extend(rel.supporting_quote_ids)
                
                # Find related codes
                for quote in interview.quotes:
                    if quote.id in rel.supporting_quote_ids:
                        relationship_map[key].related_codes.extend(quote.code_names)
        
        return list(entity_map.values()), list(relationship_map.values())
    
    def _calculate_overall_confidence(self) -> float:
        """Calculate overall extraction confidence"""
        confidences = []
        
        # Add schema confidences
        if self.code_taxonomy:
            confidences.append(self.code_taxonomy.extraction_confidence)
        if self.speaker_schema:
            confidences.append(self.speaker_schema.extraction_confidence)
        if self.entity_schema:
            confidences.append(self.entity_schema.extraction_confidence)
        
        # Add interview confidences
        for interview in self.coded_interviews:
            confidences.append(interview.extraction_confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    # Save methods
    async def _save_taxonomy(self):
        """Save code taxonomy to file"""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / "taxonomy.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.code_taxonomy.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved code taxonomy to {file_path}")
    
    async def _auto_load_existing_taxonomy(self):
        """Auto-load existing taxonomy from output directory if available"""
        import json
        from pathlib import Path
        
        # Check for taxonomy in output directory
        output_dir = Path(self.config.output_dir)
        taxonomy_path = output_dir / "taxonomy.json"
        
        if taxonomy_path.exists():
            try:
                logger.info(f"Auto-loading existing taxonomy from {taxonomy_path}")
                with open(taxonomy_path, 'r', encoding='utf-8') as f:
                    taxonomy_data = json.load(f)
                
                self.code_taxonomy = CodeTaxonomy(**taxonomy_data)
                logger.info(f"Loaded {len(self.code_taxonomy.codes)} codes from existing taxonomy")
                
            except Exception as e:
                logger.warning(f"Failed to auto-load taxonomy from {taxonomy_path}: {e}")
                logger.warning("Processing will continue without taxonomy (may result in 0 quotes extracted)")
        else:
            logger.warning(f"No existing taxonomy found at {taxonomy_path}")
            logger.warning("Run full pipeline with Phase 1 to generate taxonomy, or processing may result in 0 quotes")
    
    async def _save_speaker_schema(self):
        """Save speaker schema to file"""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / "speaker_schema.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.speaker_schema.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved speaker schema to {file_path}")
    
    async def _save_entity_schema(self):
        """Save entity/relationship schema to file"""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / "entity_schema.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.entity_schema.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved entity schema to {file_path}")
    
    async def _save_coded_interview(self, interview: CodedInterview):
        """Save individual coded interview to file"""
        output_dir = Path(self.config.output_dir) / "interviews"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f"{interview.interview_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(interview.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved coded interview to {file_path}")
    
    async def _save_outputs(self, results: ExtractionResults):
        """Save all extraction outputs"""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save complete results
        file_path = output_dir / "extraction_results.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved complete results to {file_path}")
    
    async def _import_to_neo4j(self, results: ExtractionResults):
        """Import results to Neo4j database"""
        logger.info("Importing results to Neo4j...")
        
        if not self.neo4j:
            logger.warning("Neo4j import skipped - not configured")
            return
        
        try:
            # Connect to Neo4j
            await self.neo4j.connect()
            
            # Clear existing data (optional - could be configurable)
            logger.info("Clearing existing data...")
            async with self.neo4j.driver.session() as session:
                await session.run("MATCH (n) DETACH DELETE n")
            
            # Import codes (hierarchical)
            logger.info(f"Importing {results.code_taxonomy.total_codes} codes...")
            code_id_map = {}
            for code in results.code_taxonomy.codes:
                entity = EntityNode(
                    id=code.id,
                    name=code.name,
                    entity_type="Code",
                    properties={
                        "description": code.description,
                        "semantic_definition": code.semantic_definition,
                        "level": code.level,
                        "discovery_confidence": code.discovery_confidence
                    },
                    labels=["Code", f"Level{code.level}"]
                )
                await self.neo4j.create_entity(entity)
                code_id_map[code.id] = code.name
                
                # Create hierarchy relationships
                if code.parent_id:
                    edge = RelationshipEdge(
                        source_id=code.parent_id,
                        target_id=code.id,
                        relationship_type="PARENT_OF",
                        properties={"hierarchy_level": code.level}
                    )
                    await self.neo4j.create_relationship(edge)
            
            # Import speakers
            logger.info("Importing speakers...")
            speaker_id_map = {}
            for interview in results.coded_interviews:
                for speaker in interview.speakers:
                    if speaker.name not in speaker_id_map:
                        speaker_entity = EntityNode(
                            id=f"speaker_{len(speaker_id_map)}",
                            name=speaker.name,
                            entity_type="Speaker",
                            properties={
                                "confidence": speaker.confidence,
                                "identification_method": speaker.identification_method,
                                "quotes_count": speaker.quotes_count
                            },
                            labels=["Speaker"]
                        )
                        speaker_id = await self.neo4j.create_entity(speaker_entity)
                        speaker_id_map[speaker.name] = speaker_id
            
            # Import quotes with relationships
            logger.info("Importing quotes...")
            for interview in results.coded_interviews:
                # Create interview node
                interview_entity = EntityNode(
                    id=interview.interview_id,
                    name=interview.interview_title,
                    entity_type="Interview",
                    properties={
                        "file": interview.interview_file,
                        "total_quotes": interview.total_quotes,
                        "extraction_timestamp": interview.extraction_timestamp,
                        "extraction_confidence": interview.extraction_confidence
                    },
                    labels=["Interview"]
                )
                await self.neo4j.create_entity(interview_entity)
                
                # Import quotes
                for quote in interview.quotes:
                    quote_entity = EntityNode(
                        id=quote.id,
                        name=quote.text[:100] + "..." if len(quote.text) > 100 else quote.text,
                        entity_type="Quote",
                        properties={
                            "text": quote.text,
                            "context_summary": quote.context_summary,
                            "line_start": quote.line_start,
                            "line_end": quote.line_end,
                            "sequence_position": quote.sequence_position,  # NEW: Proper sequence position
                            "extraction_confidence": quote.extraction_confidence
                        },
                        labels=["Quote"]
                    )
                    await self.neo4j.create_entity(quote_entity)
                    
                    # Link quote to codes (many-to-many)
                    for code_id in quote.code_ids:
                        edge = RelationshipEdge(
                            source_id=quote.id,
                            target_id=code_id,
                            relationship_type="SUPPORTS",
                            properties={"confidence": quote.extraction_confidence}
                        )
                        await self.neo4j.create_relationship(edge)
                    
                    # Link quote to speaker
                    if quote.speaker.name in speaker_id_map:
                        edge = RelationshipEdge(
                            source_id=quote.id,
                            target_id=speaker_id_map[quote.speaker.name],
                            relationship_type="SPOKEN_BY",
                            properties={"confidence": quote.speaker.confidence}
                        )
                        await self.neo4j.create_relationship(edge)
                    
                    # Link quote to interview
                    edge = RelationshipEdge(
                        source_id=quote.id,
                        target_id=interview.interview_id,
                        relationship_type="FROM_INTERVIEW",
                        properties={}
                    )
                    await self.neo4j.create_relationship(edge)
                    
                    # Import quote-level entities
                    for entity in quote.quote_entities:
                        entity_node = EntityNode(
                            id=f"entity_{entity.name}_{entity.type}",
                            name=entity.name,
                            entity_type=entity.type,
                            properties={"confidence": entity.confidence},
                            labels=["Entity", entity.type]
                        )
                        await self.neo4j.create_entity(entity_node)
                        
                        # Link quote to entity
                        edge = RelationshipEdge(
                            source_id=quote.id,
                            target_id=entity_node.id,
                            relationship_type="MENTIONS",
                            properties={"confidence": entity.confidence}
                        )
                        await self.neo4j.create_relationship(edge)
                
                # Import dialogue structure (NEW)
                if interview.dialogue_turns:
                    logger.info(f"Importing {len(interview.dialogue_turns)} dialogue turns...")
                    for turn in interview.dialogue_turns:
                        turn_entity = EntityNode(
                            id=turn.turn_id,
                            name=f"{turn.speaker_name}: {turn.text[:50]}...",
                            entity_type="DialogueTurn",
                            properties={
                                "sequence_number": turn.sequence_number,
                                "speaker_name": turn.speaker_name,
                                "timestamp": turn.timestamp,
                                "turn_type": turn.turn_type,
                                "text": turn.text,
                                "word_count": turn.word_count,
                                "contains_question": turn.contains_question,
                                "contains_response_markers": turn.contains_response_markers,
                                "references_previous_speaker": turn.references_previous_speaker,
                                "extraction_confidence": turn.extraction_confidence
                            },
                            labels=["DialogueTurn", f"Speaker_{turn.speaker_name.replace(' ', '_')}"]
                        )
                        await self.neo4j.create_entity(turn_entity)
                        
                        # Link turn to interview
                        edge = RelationshipEdge(
                            source_id=turn.turn_id,
                            target_id=interview.interview_id,
                            relationship_type="PART_OF_INTERVIEW",
                            properties={"sequence": turn.sequence_number}
                        )
                        await self.neo4j.create_relationship(edge)
                        
                        # Link turn to speaker
                        if turn.speaker_name in speaker_id_map:
                            edge = RelationshipEdge(
                                source_id=turn.turn_id,
                                target_id=speaker_id_map[turn.speaker_name],
                                relationship_type="SPOKEN_IN_TURN",
                                properties={"sequence": turn.sequence_number}
                            )
                            await self.neo4j.create_relationship(edge)
                
                # Import thematic connections (NEW) 
                if interview.thematic_connections:
                    logger.info(f"Importing {len(interview.thematic_connections)} thematic connections...")
                    for i, connection in enumerate(interview.thematic_connections):
                        connection_entity = EntityNode(
                            id=f"{interview.interview_id}_TC{i+1:03d}",
                            name=f"{connection.connection_type}: {connection.source_speaker} -> {connection.target_speaker}",
                            entity_type="ThematicConnection",
                            properties={
                                "connection_type": connection.connection_type,
                                "confidence_score": connection.confidence_score,
                                "evidence": connection.evidence,
                                "reasoning": connection.reasoning,
                                "thematic_overlap": connection.thematic_overlap,
                                "source_position": connection.source_position,
                                "target_position": connection.target_position,
                                "analysis_confidence": connection.analysis_confidence
                            },
                            labels=["ThematicConnection", f"Type_{connection.connection_type}"]
                        )
                        await self.neo4j.create_entity(connection_entity)
                        
                        # Link connection to source and target quotes
                        edge = RelationshipEdge(
                            source_id=connection_entity.id,
                            target_id=connection.source_quote_id,
                            relationship_type="CONNECTS_FROM",
                            properties={"position": connection.source_position}
                        )
                        await self.neo4j.create_relationship(edge)
                        
                        edge = RelationshipEdge(
                            source_id=connection_entity.id,
                            target_id=connection.target_quote_id, 
                            relationship_type="CONNECTS_TO",
                            properties={"position": connection.target_position}
                        )
                        await self.neo4j.create_relationship(edge)
                        
                        # Link connection to interview
                        edge = RelationshipEdge(
                            source_id=connection_entity.id,
                            target_id=interview.interview_id,
                            relationship_type="FOUND_IN_INTERVIEW",
                            properties={"confidence": connection.confidence_score}
                        )
                        await self.neo4j.create_relationship(edge)
            
            # Import global entities and relationships
            logger.info("Importing global entities and relationships...")
            for global_entity in results.global_entities:
                entity_node = EntityNode(
                    id=f"global_{global_entity.name}_{global_entity.type}",
                    name=global_entity.name,
                    entity_type=global_entity.type,
                    properties={
                        "total_mentions": global_entity.total_mentions,
                        "confidence": global_entity.confidence
                    },
                    labels=["Entity", global_entity.type, "Global"]
                )
                await self.neo4j.create_entity(entity_node)
            
            for global_rel in results.global_relationships:
                edge = RelationshipEdge(
                    source_id=f"global_{global_rel.source_entity}_Entity",
                    target_id=f"global_{global_rel.target_entity}_Entity",
                    relationship_type=global_rel.relationship_type,
                    properties={
                        "total_mentions": global_rel.total_mentions,
                        "confidence": global_rel.confidence
                    }
                )
                await self.neo4j.create_relationship(edge)
            
            await self.neo4j.close()
            logger.info("Neo4j import completed successfully")
            
        except Exception as e:
            logger.error(f"Neo4j import failed: {e}")
            if self.neo4j:
                await self.neo4j.close()
            raise
    
    # Helper conversion methods for Phase 0
    def _convert_parsed_to_taxonomy(self, parsed_codes) -> CodeTaxonomy:
        """Convert parsed codes to taxonomy format"""
        codes = []
        for parsed_code in parsed_codes.codes:
            codes.append(HierarchicalCode(
                id=f"code_{len(codes)}",
                name=parsed_code.name,
                description=parsed_code.description,
                semantic_definition=parsed_code.description,
                parent_id=self._find_parent_id(parsed_code.parent_name, codes) if parsed_code.parent_name else None,
                level=self._calculate_level(parsed_code, parsed_codes.codes),
                example_quotes=parsed_code.examples,
                discovery_confidence=parsed_codes.parsing_confidence
            ))
        
        return CodeTaxonomy(
            codes=codes,
            total_codes=len(codes),
            hierarchy_depth=parsed_codes.hierarchy_depth,
            discovery_method="closed",
            analytic_question=self.config.analytic_question,
            extraction_confidence=parsed_codes.parsing_confidence
        )
    
    def _find_parent_id(self, parent_name: str, codes: List[HierarchicalCode]) -> Optional[str]:
        """Find parent code ID by name"""
        for code in codes:
            if code.name == parent_name:
                return code.id
        return None
    
    def _calculate_level(self, code, all_codes) -> int:
        """Calculate hierarchy level for a code"""
        level = 0
        current = code
        while current.parent_name:
            level += 1
            # Find parent
            current = next((c for c in all_codes if c.name == current.parent_name), None)
            if not current:
                break
        return level
    
    # Similar conversion methods for speaker and entity schemas...
    def _convert_parsed_to_speaker_schema(self, parsed_speakers) -> SpeakerPropertySchema:
        """Convert parsed speaker schema"""
        properties = []
        for parsed_prop in parsed_speakers.properties:
            properties.append(DiscoveredSpeakerProperty(
                name=parsed_prop.name,
                property_type=parsed_prop.property_type,
                frequency=0,  # Will be updated during discovery
                example_values=[],
                is_categorical=parsed_prop.property_type == "categorical",
                possible_values=parsed_prop.allowed_values,
                confidence=parsed_speakers.parsing_confidence
            ))
        
        return SpeakerPropertySchema(
            properties=properties,
            discovery_method="closed",
            extraction_confidence=parsed_speakers.parsing_confidence
        )
    
    def _convert_parsed_to_entity_schema(self, parsed_entities) -> EntityRelationshipSchema:
        """Convert parsed entity/relationship schema"""
        entity_types = []
        for parsed_type in parsed_entities.entity_types:
            entity_types.append(DiscoveredEntityType(
                name=parsed_type.name,
                description=parsed_type.description,
                frequency=0,
                example_entities=[],
                common_contexts=parsed_type.identifying_patterns,
                confidence=parsed_entities.parsing_confidence
            ))
        
        relationship_types = []
        for parsed_rel in parsed_entities.relationship_types:
            relationship_types.append(DiscoveredRelationshipType(
                name=parsed_rel.name,
                description=parsed_rel.description,
                frequency=0,
                common_source_types=parsed_rel.valid_source_types,
                common_target_types=parsed_rel.valid_target_types,
                directional=parsed_rel.directional,
                example_relationships=[],
                confidence=parsed_entities.parsing_confidence
            ))
        
        return EntityRelationshipSchema(
            entity_types=entity_types,
            relationship_types=relationship_types,
            total_entities_found=0,
            total_relationships_found=0,
            discovery_method="closed",
            extraction_confidence=parsed_entities.parsing_confidence
        )
    
    # Additional prompt builders for mixed approaches
    def _build_mixed_code_discovery_prompt(self, combined_text: str, 
                                          existing_taxonomy: CodeTaxonomy) -> str:
        """Build prompt for mixed code discovery"""
        provided_codes = "\n".join([f"- {code.name}: {code.description}" 
                                   for code in existing_taxonomy.codes])
        
        return self.prompt_loader.format_prompt(
            phase="phase1",
            template_name="mixed_code_discovery",
            num_interviews=len(self.config.interview_files),
            analytic_question=self.config.analytic_question,
            provided_codes=provided_codes,
            code_hierarchy_depth=self.config.code_hierarchy_depth,
            combined_text=combined_text,
            paradigm=self.config.paradigm
        )
    
    def _build_open_speaker_discovery_prompt(self, combined_text: str) -> str:
        """Build prompt for open speaker schema discovery"""
        return self.prompt_loader.format_prompt(
            phase="phase2",
            template_name="open_speaker_discovery",
            num_interviews=len(self.config.interview_files),
            analytic_question=self.config.analytic_question,
            combined_text=combined_text,
            paradigm=self.config.paradigm
        )
    
    def _build_open_entity_discovery_prompt(self, combined_text: str) -> str:
        """Build prompt for open entity/relationship discovery"""
        return self.prompt_loader.format_prompt(
            phase="phase3",
            template_name="open_entity_discovery",
            num_interviews=len(self.config.interview_files),
            analytic_question=self.config.analytic_question,
            combined_text=combined_text,
            paradigm=self.config.paradigm
        )
    
    def _build_mixed_speaker_discovery_prompt(self, combined_text: str,
                                             existing_schema: SpeakerPropertySchema) -> str:
        """Build prompt for mixed speaker schema discovery"""
        existing_props = "\n".join([
            f"- {prop.name} ({prop.property_type.value}): {prop.description}"
            for prop in existing_schema.properties
        ])
        
        return self.prompt_loader.format_prompt(
            phase="phase2",
            template_name="mixed_speaker_discovery",
            num_interviews=len(self.config.interview_files),
            analytic_question=self.config.analytic_question,
            provided_properties=existing_props,
            combined_text=combined_text,
            paradigm=self.config.paradigm
        )
    
    def _build_mixed_entity_discovery_prompt(self, combined_text: str,
                                            existing_schema: EntityRelationshipSchema) -> str:
        """Build prompt for mixed entity/relationship discovery"""
        existing_entities = "\n".join([
            f"- {et.name}: {et.description}"
            for et in existing_schema.entity_types
        ])
        
        existing_relationships = "\n".join([
            f"- {rt.name}: {rt.description} (from {rt.source_types} to {rt.target_types})"
            for rt in existing_schema.relationship_types
        ])
        
        return self.prompt_loader.format_prompt(
            phase="phase3",
            template_name="mixed_entity_discovery",
            num_interviews=len(self.config.interview_files),
            analytic_question=self.config.analytic_question,
            provided_entity_types=existing_entities,
            provided_relationship_types=existing_relationships,
            combined_text=combined_text,
            paradigm=self.config.paradigm
        )
    
    def _build_quotes_speakers_prompt(self, interview_text: str, interview_id: str, 
                                     is_focus_group: bool = False, dialogue_turns: List = None) -> str:
        """Build prompt for Phase 4A: Extract quotes and speakers"""
        # Generate examples using actual code IDs from the taxonomy
        code_examples = self.prompt_loader.generate_code_examples(
            self.code_taxonomy.codes if (hasattr(self, 'code_taxonomy') and self.code_taxonomy is not None) else []
        )
        
        # FIXED: Use dialogue-aware template for focus groups
        if is_focus_group and dialogue_turns:
            template_name = "dialogue_aware_quotes"
            speaker_count = len(set(turn.speaker_name for turn in dialogue_turns)) if dialogue_turns else 0
            
            return self.prompt_loader.format_prompt(
                phase="phase4",
                template_name=template_name,
                interview_id=interview_id,
                analytic_question=self.config.analytic_question,
                speaker_count=speaker_count,
                formatted_codes=self._format_codes_for_prompt(),
                formatted_speaker_schema=self._format_speaker_schema_for_prompt(),
                code_examples=code_examples,
                interview_text=interview_text,
                paradigm=self.config.paradigm
            )
        else:
            # Use standard template for individual interviews
            template_name = "quotes_speakers"
            
            return self.prompt_loader.format_prompt(
                phase="phase4",
                template_name=template_name,
                interview_id=interview_id,
                analytic_question=self.config.analytic_question,
                formatted_codes=self._format_codes_for_prompt(),
                formatted_speaker_schema=self._format_speaker_schema_for_prompt(),
                code_examples=code_examples,
                interview_text=interview_text,
                paradigm=self.config.paradigm
            )
    
    def _build_entities_relationships_prompt(self, interview_text: str, 
                                            interview_id: str,
                                            quotes: List) -> str:
        """Build prompt for Phase 4B: Extract entities and relationships"""
        # Format quotes for context
        quote_context = "\n".join([
            f"Quote {i+1}: '{q.text[:100]}...'" 
            for i, q in enumerate(quotes[:10])  # Show first 10 as examples
        ])
        if len(quotes) > 10:
            quote_context += f"\n... and {len(quotes) - 10} more quotes"
        
        return self.prompt_loader.format_prompt(
            phase="phase4",
            template_name="entities_relationships",
            interview_id=interview_id,
            analytic_question=self.config.analytic_question,
            formatted_entity_schema=self._format_entity_schema_for_prompt(),
            quote_context=quote_context,
            interview_text=interview_text,
            paradigm=self.config.paradigm
        )
    
    def _combine_extraction_results(self, 
                                   interview_id: str,
                                   interview_file: str,
                                   quotes_and_speakers: 'QuotesAndSpeakers',
                                   entities_and_relationships: 'EntitiesAndRelationships') -> CodedInterview:
        """Combine Phase 4A and 4B results into CodedInterview format"""
        from datetime import datetime
        import uuid
        from .schema_validator import validate_extraction_results
        
        # Convert simple quotes to enhanced quotes
        enhanced_quotes = []
        unique_codes = set()
        
        for i, simple_quote in enumerate(quotes_and_speakers.quotes):
            # Generate quote ID
            quote_id = f"{interview_id}_Q{i+1:03d}"
            
            # Find matching speaker
            speaker = next(
                (s for s in quotes_and_speakers.speakers 
                 if s.name == simple_quote.speaker_name),
                SpeakerInfo(
                    name=simple_quote.speaker_name,
                    confidence=0.5,
                    identification_method="from_quote",
                    quotes_count=1
                )
            )
            
            # Track unique codes (now using code_ids)
            unique_codes.update(simple_quote.code_ids)
            
            # Get code names from IDs
            code_names = [self._get_code_name(code_id) for code_id in simple_quote.code_ids]
            
            # Find entities mentioned in this quote (simple heuristic)
            quote_entities = [
                e for e in entities_and_relationships.entities
                if e.name.lower() in simple_quote.text.lower()
            ]
            
            # Find relationships relevant to this quote
            quote_relationships = [
                r for r in entities_and_relationships.relationships
                if any(e.name == r.source_entity or e.name == r.target_entity 
                      for e in quote_entities)
            ]
            
            # Create enhanced quote
            enhanced_quote = EnhancedQuote(
                id=quote_id,
                text=simple_quote.text,
                context_summary=f"Quote from {speaker.name} about {', '.join(code_names[:3])}",
                code_ids=simple_quote.code_ids,  # Use IDs directly from LLM
                code_names=code_names,  # Names looked up from taxonomy
                code_confidence_scores=[0.8] * len(simple_quote.code_ids),
                speaker=speaker,
                thematic_connection=simple_quote.thematic_connection,  # NEW: Thematic connection data
                connection_target=simple_quote.connection_target,
                connection_confidence=simple_quote.connection_confidence,
                connection_evidence=simple_quote.connection_evidence,
                interview_id=interview_id,
                interview_title=Path(interview_file).stem,
                line_start=simple_quote.location_start,
                line_end=simple_quote.location_end,
                quote_entities=quote_entities[:5],  # Limit to avoid bloat
                quote_relationships=quote_relationships[:3],
                extraction_confidence=0.8
            )
            enhanced_quotes.append(enhanced_quote)
        
        # Validate extraction results against discovered schemas
        extraction_data = {
            'quotes': [{'id': f"{interview_id}_Q{i+1:03d}", 
                       'text': q.text, 
                       'code_ids': q.code_ids,
                       'speaker': {'name': q.speaker_name}} 
                      for i, q in enumerate(quotes_and_speakers.quotes)],
            'speakers': [s.dict() for s in quotes_and_speakers.speakers],
            'entities': [e.dict() for e in entities_and_relationships.entities],
            'relationships': [r.dict() for r in entities_and_relationships.relationships]
        }
        
        # Convert schemas to dict format for validator
        code_taxonomy_dict = self.code_taxonomy.dict() if self.code_taxonomy else {'codes': []}
        speaker_schema_dict = self.speaker_schema.dict() if self.speaker_schema else {'properties': []}
        entity_schema_dict = self.entity_schema.dict() if self.entity_schema else {'entity_types': [], 'relationship_types': []}
        
        validated_data = validate_extraction_results(
            extraction_data,
            code_taxonomy_dict,
            speaker_schema_dict,
            entity_schema_dict
        )
        
        # Log any violations
        if validated_data.get('violations'):
            violations = validated_data['violations']
            if violations.get('invalid_codes'):
                logger.warning(f"Interview {interview_id}: Invalid codes detected and filtered: {violations['invalid_codes']}")
            if violations.get('invalid_entity_types'):
                logger.warning(f"Interview {interview_id}: Invalid entity types detected and filtered: {violations['invalid_entity_types']}")
            if violations.get('invalid_relationship_types'):
                logger.warning(f"Interview {interview_id}: Invalid relationship types detected and filtered: {violations['invalid_relationship_types']}")
        
        # Use validated entities and relationships
        validated_entities = [ExtractedEntity(**e) for e in validated_data['entities']]
        validated_relationships = [ExtractedRelationship(**r) for r in validated_data['relationships']]
        
        # Create coded interview with validated data
        coded_interview = CodedInterview(
            interview_id=interview_id,
            interview_title=Path(interview_file).stem,
            interview_file=interview_file,
            quotes=enhanced_quotes,
            speakers=quotes_and_speakers.speakers,
            interview_entities=validated_entities,
            interview_relationships=validated_relationships,
            total_quotes=len(enhanced_quotes),
            total_codes_applied=quotes_and_speakers.total_codes_applied,
            unique_codes_used=list(unique_codes),
            total_speakers=len(quotes_and_speakers.speakers),
            total_entities=entities_and_relationships.total_entities,
            total_relationships=entities_and_relationships.total_relationships,
            extraction_timestamp=datetime.now().isoformat(),
            extraction_confidence=0.8,
            processing_time_seconds=0.0  # Will be set externally
        )
        
        return coded_interview
    def _extract_thematic_connections_from_quotes(self, quotes: List, interview_id: str) -> List:
        """Extract thematic connections from SimpleQuote objects with integrated connection fields"""
        from datetime import datetime
        
        thematic_connections = []
        
        for i, quote in enumerate(quotes):
            # Check if this quote has thematic connection data
            if (hasattr(quote, 'thematic_connection') and 
                quote.thematic_connection and 
                quote.thematic_connection != "none" and 
                quote.connection_target):
                
                # Find the target quote by speaker name (approximate matching)
                target_quote = None
                for j, potential_target in enumerate(quotes):
                    if (j < i and  # Target must be earlier in conversation
                        potential_target.speaker_name == quote.connection_target):
                        target_quote = potential_target
                        break
                
                if target_quote:
                    connection = ThematicConnection(
                        source_quote_id=f"{interview_id}_Q{quotes.index(target_quote)+1:03d}",
                        target_quote_id=f"{interview_id}_Q{i+1:03d}",
                        connection_type=quote.thematic_connection,
                        confidence_score=quote.connection_confidence or 0.7,
                        evidence=quote.connection_evidence or "Thematic connection detected",
                        reasoning=f"Connection detected during integrated extraction: {quote.connection_evidence}",
                        thematic_overlap=[],  # Future enhancement: Include shared code themes
                        source_speaker=target_quote.speaker_name,
                        source_position=getattr(target_quote, 'location_start', j),
                        source_content=target_quote.text[:100] + "...",
                        target_speaker=quote.speaker_name,
                        target_position=getattr(quote, 'location_start', i),
                        target_content=quote.text[:100] + "...",
                        detection_timestamp=datetime.now().isoformat()
                    )
                    thematic_connections.append(connection)
        
        return thematic_connections

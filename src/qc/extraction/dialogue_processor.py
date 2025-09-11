"""
Dialogue-Aware Processing Module for QCA Pipeline
Preserves conversational structure while maintaining thematic extraction
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from pathlib import Path

from .code_first_schemas import (
    DialogueTurn, ConversationalContext, SpeakerInfo, ThematicConnection
)

logger = logging.getLogger(__name__)


@dataclass
class TimestampMatch:
    """Structured timestamp information"""
    speaker: str
    timestamp: str
    raw_text: str
    start_position: int
    
    
class DialogueStructureDetector:
    """Detects and extracts dialogue structure from interview transcripts"""
    
    # Common patterns for dialogue structure detection
    SPEAKER_PATTERNS = [
        # "John Smith 0:03" or "John Smith   0:03"
        r'^([A-Za-z][A-Za-z\s]+?)\s{1,3}(\d{1,2}:\d{2}(?::\d{2})?)\s*$',
        # "Speaker: content" format
        r'^([A-Za-z][A-Za-z\s]+?):\s*(.+)$',
        # "[Speaker Name]" format
        r'^\[([A-Za-z][A-Za-z\s]+?)\]\s*(.*)$',
        # "SPEAKER NAME:" format
        r'^([A-Z][A-Z\s]+?):\s*(.+)$'
    ]
    
    RESPONSE_MARKERS = {
        'agreement': ['yes', 'right', 'exactly', 'absolutely', 'definitely', 'sure', 'yeah'],
        'disagreement': ['no', 'not really', 'I disagree', 'actually', 'but'],
        'building': ['also', 'and', 'building on that', 'to add to', 'following up'],
        'clarification': ['what I mean is', 'to clarify', 'let me explain', 'in other words']
    }
    
    QUESTION_MARKERS = ['?', 'what', 'how', 'why', 'when', 'where', 'who', 'would you', 'do you', 'can you']
    
    def __init__(self):
        self.compiled_patterns = [re.compile(pattern, re.MULTILINE) for pattern in self.SPEAKER_PATTERNS]
    
    def detect_interview_type(self, text: str) -> str:
        """
        Determine if interview is focus group or individual
        
        Returns:
            "focus_group" or "individual_interview"
        """
        # Look for timestamp patterns indicating multiple speakers
        timestamp_matches = self._find_timestamp_patterns(text)
        unique_speakers = set(match.speaker for match in timestamp_matches)
        
        if len(unique_speakers) > 2:  # More than interviewer + interviewee
            return "focus_group"
        elif len(unique_speakers) == 2:
            # Could be individual - check for rapid back-and-forth
            if len(timestamp_matches) > 10:  # Many turns suggest focus group
                return "focus_group"
            return "individual_interview"
        else:
            return "individual_interview"
    
    def _find_timestamp_patterns(self, text: str) -> List[TimestampMatch]:
        """Find all timestamp patterns in text"""
        matches = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            original_line = line.strip()
            if not original_line:
                continue
            
            # Remove [Paragraph X] prefix if present
            clean_line = original_line
            if clean_line.startswith('[Paragraph'):
                # Extract content after paragraph marker
                bracket_end = clean_line.find(']')
                if bracket_end != -1:
                    clean_line = clean_line[bracket_end + 1:].strip()
            
            # Check for "Speaker Name   0:03" pattern (standalone or at start of line)
            timestamp_patterns = [
                # Pattern 1: "Speaker Name   0:03" (standalone)
                r'^([A-Za-z][A-Za-z\s\.]+?)\s{2,}(\d{1,2}:\d{2}(?::\d{2})?)\s*$',
                # Pattern 2: "Speaker Name   0:03\nContent" (at start with content)
                r'^([A-Za-z][A-Za-z\s\.]+?)\s{2,}(\d{1,2}:\d{2}(?::\d{2})?)\s*\n',
                # Pattern 3: "Speaker Name   0:03 Content" (same line with content)
                r'^([A-Za-z][A-Za-z\s\.]+?)\s{2,}(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$'
            ]
            
            for pattern in timestamp_patterns:
                match = re.match(pattern, clean_line, re.MULTILINE)
                if match:
                    speaker_name = match.group(1).strip()
                    timestamp = match.group(2)
                    matches.append(TimestampMatch(
                        speaker=speaker_name,
                        timestamp=timestamp,
                        raw_text=original_line,
                        start_position=i
                    ))
                    break  # Found a match, don't try other patterns
        
        return matches
    
    def extract_dialogue_turns(self, text: str, interview_id: str) -> List[DialogueTurn]:
        """
        Extract structured dialogue turns from interview text
        
        Args:
            text: Raw interview text
            interview_id: Unique interview identifier
            
        Returns:
            List of DialogueTurn objects preserving conversational flow
        """
        interview_type = self.detect_interview_type(text)
        logger.info(f"Interview {interview_id} detected as: {interview_type}")
        
        if interview_type == "focus_group":
            return self._extract_focus_group_turns(text, interview_id)
        else:
            return self._extract_individual_turns(text, interview_id)
    
    def _extract_focus_group_turns(self, text: str, interview_id: str) -> List[DialogueTurn]:
        """Extract turns from focus group with multiple speakers and timestamps"""
        timestamp_matches = self._find_timestamp_patterns(text)
        lines = text.split('\n')
        turns = []
        
        for i, match in enumerate(timestamp_matches):
            # Extract content from the current line and subsequent lines
            current_line = lines[match.start_position].strip()
            
            # Remove [Paragraph X] prefix if present
            if current_line.startswith('[Paragraph'):
                bracket_end = current_line.find(']')
                if bracket_end != -1:
                    current_line = current_line[bracket_end + 1:].strip()
            
            # Extract content after timestamp
            turn_content = []
            timestamp_pattern = rf'^{re.escape(match.speaker)}\s+{re.escape(match.timestamp)}\s*(.*)$'
            timestamp_match = re.match(timestamp_pattern, current_line, re.DOTALL)
            
            if timestamp_match:
                initial_content = timestamp_match.group(1).strip()
                if initial_content:
                    # Split by newlines in case there's multi-line content in the paragraph
                    content_lines = initial_content.split('\n')
                    for content_line in content_lines:
                        if content_line.strip() and not self._is_metadata_line(content_line.strip()):
                            turn_content.append(content_line.strip())
            
            # Also collect content from following lines until next timestamp
            start_line = match.start_position + 1
            end_line = (timestamp_matches[i + 1].start_position 
                       if i + 1 < len(timestamp_matches) 
                       else len(lines))
            
            for line_idx in range(start_line, end_line):
                if line_idx < len(lines):
                    line = lines[line_idx].strip()
                    # Skip paragraph markers and empty lines
                    if line.startswith('[Paragraph'):
                        bracket_end = line.find(']')
                        if bracket_end != -1:
                            line = line[bracket_end + 1:].strip()
                    
                    if line and not self._is_metadata_line(line):
                        turn_content.append(line)
            
            if turn_content:  # Only create turn if there's actual content
                full_text = ' '.join(turn_content)
                
                # Analyze turn characteristics
                contains_question = any(marker in full_text.lower() for marker in self.QUESTION_MARKERS)
                contains_response_markers = self._detect_response_markers(full_text)
                references_previous = self._detect_speaker_references(full_text, timestamp_matches, i)
                
                turn = DialogueTurn(
                    turn_id=f"{interview_id}_T{i+1:03d}",
                    sequence_number=i + 1,
                    speaker_name=match.speaker,
                    timestamp=match.timestamp,
                    raw_location=match.raw_text,
                    turn_type=self._classify_turn_type(full_text, contains_question, contains_response_markers),
                    text=full_text,
                    semantic_segments=self._segment_turn_content(full_text),
                    contains_question=contains_question,
                    contains_response_markers=contains_response_markers,
                    references_previous_speaker=references_previous,
                    word_count=len(full_text.split()),
                    extraction_confidence=0.9 if match.timestamp else 0.7
                )
                
                # Link responses
                if i > 0 and contains_response_markers:
                    turn.responds_to_turn = f"{interview_id}_T{i:03d}"
                
                turns.append(turn)
        
        return turns
    
    def _extract_individual_turns(self, text: str, interview_id: str) -> List[DialogueTurn]:
        """Extract turns from individual interview (simpler structure)"""
        # For individual interviews, we'll segment by paragraph markers or speaker labels
        lines = text.split('\n')
        turns = []
        current_speaker = "Unknown"
        turn_content = []
        sequence = 1
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this line indicates a speaker change
            speaker_change = False
            for pattern in self.compiled_patterns:
                match = pattern.match(line)
                if match:
                    # Save previous turn
                    if turn_content:
                        full_text = ' '.join(turn_content)
                        turn = self._create_individual_turn(
                            interview_id, sequence, current_speaker, full_text, line_idx
                        )
                        turns.append(turn)
                        turn_content = []
                        sequence += 1
                    
                    # Start new turn
                    current_speaker = match.group(1).strip()
                    if len(match.groups()) > 1 and match.group(2):
                        turn_content.append(match.group(2).strip())
                    speaker_change = True
                    break
            
            if not speaker_change:
                turn_content.append(line)
        
        # Handle final turn
        if turn_content:
            full_text = ' '.join(turn_content)
            turn = self._create_individual_turn(
                interview_id, sequence, current_speaker, full_text, len(lines)
            )
            turns.append(turn)
        
        return turns
    
    def _create_individual_turn(self, interview_id: str, sequence: int, 
                              speaker: str, text: str, line_idx: int) -> DialogueTurn:
        """Create a dialogue turn for individual interview"""
        contains_question = any(marker in text.lower() for marker in self.QUESTION_MARKERS)
        contains_response_markers = self._detect_response_markers(text)
        
        return DialogueTurn(
            turn_id=f"{interview_id}_T{sequence:03d}",
            sequence_number=sequence,
            speaker_name=speaker,
            raw_location=f"Line {line_idx}",
            turn_type=self._classify_turn_type(text, contains_question, contains_response_markers),
            text=text,
            semantic_segments=self._segment_turn_content(text),
            contains_question=contains_question,
            contains_response_markers=contains_response_markers,
            references_previous_speaker=False,  # Simpler for individual interviews
            word_count=len(text.split()),
            extraction_confidence=0.8
        )
    
    def _is_metadata_line(self, line: str) -> bool:
        """Check if line is metadata rather than speech content"""
        metadata_patterns = [
            r'^Transcript\s*$',
            r'^\w+ \d+, \d{4}',  # Date patterns
            r'started transcription',
            r'^\d+:\d+\s*$',  # Lone timestamps
        ]
        
        return any(re.match(pattern, line.strip(), re.IGNORECASE) for pattern in metadata_patterns)
    
    def _detect_response_markers(self, text: str) -> bool:
        """Detect if text contains response markers"""
        text_lower = text.lower()
        for category, markers in self.RESPONSE_MARKERS.items():
            if any(marker in text_lower for marker in markers):
                return True
        return False
    
    def _detect_speaker_references(self, text: str, all_matches: List[TimestampMatch], 
                                  current_index: int) -> bool:
        """Detect if speaker references previous speakers"""
        if current_index == 0:
            return False
        
        # Get previous speakers
        previous_speakers = [match.speaker for match in all_matches[:current_index]]
        
        # Check for name references
        text_lower = text.lower()
        for speaker in previous_speakers:
            # Check for first name or full name references
            first_name = speaker.split()[0].lower()
            if (first_name in text_lower or 
                speaker.lower() in text_lower or
                any(phrase in text_lower for phrase in [
                    "as you said", "like you mentioned", "building on", "to your point"
                ])):
                return True
        
        return False
    
    def _classify_turn_type(self, text: str, contains_question: bool, 
                          contains_response_markers: bool) -> str:
        """Classify the type of dialogue turn"""
        if contains_question:
            return "question"
        elif contains_response_markers:
            return "response"
        elif len(text.split()) < 5:  # Very short turns
            return "interjection"
        else:
            return "statement"
    
    def _segment_turn_content(self, text: str) -> List[str]:
        """Break turn into semantic segments for better coding"""
        # Simple sentence-based segmentation for now
        sentences = re.split(r'[.!?]+', text)
        segments = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        # If no good sentences, return the whole text as one segment
        if not segments:
            segments = [text]
        
        return segments
    
    def build_conversational_contexts(self, turns: List[DialogueTurn]) -> Dict[str, ConversationalContext]:
        """
        Build conversational context for each turn
        
        Args:
            turns: List of DialogueTurn objects in sequence
            
        Returns:
            Dictionary mapping turn_id to ConversationalContext
        """
        contexts = {}
        
        for i, turn in enumerate(turns):
            # Get preceding and following turns
            preceding_turns = [turns[j].turn_id for j in range(max(0, i-3), i)]
            following_turns = [turns[j].turn_id for j in range(i+1, min(len(turns), i+3))]
            
            # Detect response relationships
            is_response_to = None
            if i > 0 and turn.contains_response_markers:
                is_response_to = turns[i-1].turn_id
            
            # Detect topic continuity
            topic_continuity = self._analyze_topic_continuity(turn, turns, i)
            
            context = ConversationalContext(
                preceding_turns=preceding_turns,
                following_turns=following_turns,
                turn_taking_pattern=self._analyze_turn_taking_pattern(turns, i),
                is_response_to=is_response_to,
                topic_continuity=topic_continuity,
                topic_markers=self._extract_topic_markers(turn.text)
            )
            
            contexts[turn.turn_id] = context
        
        return contexts
    
    def _analyze_topic_continuity(self, current_turn: DialogueTurn, 
                                 all_turns: List[DialogueTurn], index: int) -> str:
        """Analyze how this turn relates to topic flow"""
        if index == 0:
            return "initiates"
        
        current_text = current_turn.text.lower()
        
        # Check for topic shift markers
        shift_markers = ['but', 'however', 'actually', 'speaking of', 'on another note']
        if any(marker in current_text for marker in shift_markers):
            return "shifts"
        
        # Check for continuation markers
        continue_markers = ['also', 'and', 'furthermore', 'building on']
        if any(marker in current_text for marker in continue_markers):
            return "continues"
        
        # Check for return markers
        return_markers = ['back to', 'returning to', 'as we were saying']
        if any(marker in current_text for marker in return_markers):
            return "returns"
        
        return "continues"  # Default assumption
    
    def _analyze_turn_taking_pattern(self, turns: List[DialogueTurn], index: int) -> str:
        """Analyze turn-taking pattern around this turn"""
        if index == 0 or index >= len(turns) - 1:
            return "sequential"
        
        current_speaker = turns[index].speaker_name
        prev_speaker = turns[index - 1].speaker_name
        
        if current_speaker == prev_speaker:
            return "continued"
        else:
            return "sequential"
    
    def _extract_topic_markers(self, text: str) -> List[str]:
        """Extract words that might indicate topic flow"""
        topic_markers = []
        marker_patterns = [
            r'\b(but|however|actually|also|and|furthermore)\b',
            r'\b(speaking of|on another note|by the way)\b',
            r'\b(back to|returning to|as we were saying)\b'
        ]
        
        for pattern in marker_patterns:
            matches = re.findall(pattern, text.lower())
            topic_markers.extend(matches)
        
        return topic_markers


class DialogueAwareQuoteExtractor:
    """Extracts quotes while preserving dialogue structure and flow"""
    
    def __init__(self, dialogue_detector: DialogueStructureDetector):
        self.dialogue_detector = dialogue_detector
    
    def extract_quotes_with_dialogue_context(self, turns: List[DialogueTurn], 
                                           contexts: Dict[str, ConversationalContext],
                                           code_taxonomy: dict, interview_id: str) -> List[dict]:
        """
        Extract quotes from dialogue turns while preserving conversational context
        
        Args:
            turns: List of DialogueTurn objects
            contexts: Conversational context for each turn
            code_taxonomy: Available codes for thematic analysis
            interview_id: Interview identifier
            
        Returns:
            List of quote dictionaries with dialogue structure preserved
        """
        quotes = []
        
        for turn in turns:
            # Only extract quotes from substantial turns
            if turn.word_count < 5:  # Skip very short interjections
                continue
            
            # Process each semantic segment as potential quote
            for segment_idx, segment in enumerate(turn.semantic_segments):
                if len(segment.split()) < 8:  # Skip very short segments
                    continue
                
                quote_id = f"{interview_id}_Q{len(quotes)+1:03d}"
                
                # Get conversational context
                conv_context = contexts.get(turn.turn_id, ConversationalContext())
                
                # Create enhanced quote with dialogue structure
                quote = {
                    "id": quote_id,
                    "text": segment,
                    "speaker_name": turn.speaker_name,
                    "sequence_position": turn.sequence_number,
                    "timestamp": turn.timestamp,
                    "turn_id": turn.turn_id,
                    
                    # Dialogue context
                    "dialogue_context": {
                        "turn_type": turn.turn_type,
                        "is_response": conv_context.is_response_to is not None,
                        "responds_to": conv_context.is_response_to,
                        "topic_continuity": conv_context.topic_continuity,
                        "preceding_speakers": [
                            self._get_speaker_for_turn(prec_turn, turns) 
                            for prec_turn in conv_context.preceding_turns[-2:]  # Last 2
                        ],
                        "conversation_thread": self._identify_conversation_thread(turn, turns, contexts)
                    },
                    
                    # Location information (FIXED: no longer all the same line)
                    "location_start": turn.sequence_number,  # Use sequence instead of line
                    "location_end": turn.sequence_number,
                    "location_type": "dialogue_turn"
                }
                
                quotes.append(quote)
        
        logger.info(f"Extracted {len(quotes)} quotes with dialogue structure from {len(turns)} turns")
        return quotes
    
    def _get_speaker_for_turn(self, turn_id: str, turns: List[DialogueTurn]) -> str:
        """Get speaker name for a turn ID"""
        for turn in turns:
            if turn.turn_id == turn_id:
                return turn.speaker_name
        return "Unknown"
    
    def _identify_conversation_thread(self, current_turn: DialogueTurn, 
                                    all_turns: List[DialogueTurn],
                                    contexts: Dict[str, ConversationalContext]) -> str:
        """Identify which conversation thread this turn belongs to"""
        # Simple topic-based threading
        # In a full implementation, this could use more sophisticated NLP
        
        current_words = set(current_turn.text.lower().split())
        
        # Look for turns with similar vocabulary in recent context
        thread_id = f"thread_{current_turn.sequence_number // 5 + 1}"  # Group by rough topic chunks
        
        return thread_id


class ThematicConnectionDetector:
    """Detects thematic connections between dialogue segments using LLM analysis"""
    
    def __init__(self, llm_handler):
        """Initialize with LLM handler for analysis"""
        self.llm = llm_handler
        self.minimum_confidence = 0.7  # Minimum confidence to consider a connection valid
    
    async def detect_connections(self, quotes: List[dict], interview_id: str) -> List[ThematicConnection]:
        """
        Detect thematic connections between quotes in chronological order
        
        Args:
            quotes: List of quote dictionaries with dialogue context
            interview_id: Interview identifier for logging
            
        Returns:
            List of ThematicConnection objects with confidence >= minimum_confidence
        """
        logger.info(f"Starting thematic connection detection for {interview_id} with {len(quotes)} quotes")
        
        connections = []
        
        # Sort quotes by sequence position to ensure chronological analysis
        sorted_quotes = sorted(quotes, key=lambda q: q.get("sequence_position", 0))
        
        # Analyze connections within a sliding window of recent quotes
        window_size = 5  # Look back at most 5 quotes
        
        for i, target_quote in enumerate(sorted_quotes):
            # Look back at previous quotes within the window
            start_idx = max(0, i - window_size)
            
            for j in range(start_idx, i):
                source_quote = sorted_quotes[j]
                
                # Skip if same speaker and adjacent positions (likely same thought)
                if (source_quote["speaker_name"] == target_quote["speaker_name"] and 
                    abs(source_quote.get("sequence_position", 0) - target_quote.get("sequence_position", 0)) <= 1):
                    continue
                
                # Analyze potential connection
                connection = await self._analyze_connection_pair(source_quote, target_quote, interview_id)
                
                if connection and connection.confidence_score >= self.minimum_confidence:
                    connections.append(connection)
        
        logger.info(f"Detected {len(connections)} thematic connections above confidence threshold {self.minimum_confidence}")
        return connections
    
    async def _analyze_connection_pair(self, source_quote: dict, target_quote: dict, 
                                     interview_id: str) -> Optional[ThematicConnection]:
        """
        Analyze a single pair of quotes for thematic connections
        
        Args:
            source_quote: Earlier quote dictionary
            target_quote: Later quote dictionary
            interview_id: Interview identifier
            
        Returns:
            ThematicConnection object if connection found, None otherwise
        """
        try:
            # Load and format the prompt
            prompt_template = self._load_connection_prompt()
            
            prompt = prompt_template.format(
                speaker_a=source_quote["speaker_name"],
                position_a=source_quote.get("sequence_position", "unknown"),
                content_a=source_quote["text"],
                speaker_b=target_quote["speaker_name"], 
                position_b=target_quote.get("sequence_position", "unknown"),
                content_b=target_quote["text"]
            )
            
            # Define response schema for structured output
            from pydantic import BaseModel
            
            class ConnectionAnalysis(BaseModel):
                has_connection: bool
                connection_type: str  # "addresses", "builds_on", "relates_to", "contradicts", "exemplifies", "none"
                confidence_score: float  # 0.0-1.0
                evidence: str
                reasoning: str
                thematic_overlap: List[str]
            
            # Get LLM analysis
            logger.debug(f"Analyzing connection: {source_quote['speaker_name']} -> {target_quote['speaker_name']}")
            
            analysis = await self.llm.extract_structured(
                prompt=prompt,
                schema=ConnectionAnalysis,
                max_tokens=1000
            )
            
            # Create ThematicConnection if valid
            if analysis.has_connection and analysis.confidence_score >= 0.3:  # Lower threshold for initial detection
                from datetime import datetime
                
                connection = ThematicConnection(
                    source_quote_id=source_quote.get("id", f"unknown_{source_quote.get('sequence_position', 0)}"),
                    target_quote_id=target_quote.get("id", f"unknown_{target_quote.get('sequence_position', 0)}"),
                    connection_type=analysis.connection_type,
                    confidence_score=analysis.confidence_score,
                    evidence=analysis.evidence,
                    reasoning=analysis.reasoning,
                    thematic_overlap=analysis.thematic_overlap,
                    source_speaker=source_quote["speaker_name"],
                    source_position=source_quote.get("sequence_position", 0),
                    source_content=source_quote["text"],
                    target_speaker=target_quote["speaker_name"],
                    target_position=target_quote.get("sequence_position", 0),
                    target_content=target_quote["text"],
                    detection_timestamp=datetime.now().isoformat(),
                    analysis_confidence=min(0.9, analysis.confidence_score + 0.1)  # Slight boost for making it through analysis
                )
                
                return connection
                
        except Exception as e:
            logger.warning(f"Failed to analyze connection pair in {interview_id}: {e}")
            logger.debug(f"Prompt that failed: {prompt[:500]}...")
            logger.debug(f"Source quote: {source_quote}")
            logger.debug(f"Target quote: {target_quote}")
            return None
        
        return None
    
    def _load_connection_prompt(self) -> str:
        """Load the thematic connection analysis prompt"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "phase4" / "dialogue_aware_quotes.txt"
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Connection analysis prompt not found at {prompt_path}")
            # Fallback minimal prompt
            return """
            Analyze the thematic connection between these two dialogue segments:
            
            Segment A: Speaker {speaker_a} (Position {position_a}): "{content_a}"
            Segment B: Speaker {speaker_b} (Position {position_b}): "{content_b}"
            
            Respond with JSON: {{"has_connection": bool, "connection_type": "string", "confidence_score": float, "evidence": "string", "reasoning": "string", "thematic_overlap": []}}
            """
    
    def filter_high_confidence_connections(self, connections: List[ThematicConnection], 
                                         min_confidence: float = 0.8) -> List[ThematicConnection]:
        """
        Filter connections to only include high-confidence ones
        
        Args:
            connections: List of all detected connections
            min_confidence: Minimum confidence threshold (default 0.8)
            
        Returns:
            Filtered list of high-confidence connections
        """
        high_confidence = [c for c in connections if c.confidence_score >= min_confidence]
        logger.info(f"Filtered {len(connections)} connections to {len(high_confidence)} high-confidence ones (>= {min_confidence})")
        return high_confidence
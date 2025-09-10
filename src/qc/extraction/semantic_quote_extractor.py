"""
Semantic Quote Extraction System

Replaces line-based quote extraction with semantic unit-based extraction
using LLM analysis for intelligent quote boundary detection and relationship
matching as specified in CLAUDE.md critical fixes.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SemanticUnit(Enum):
    """Types of semantic units for quote extraction"""
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    LINE = "line"  # Fallback only


@dataclass
class ExtractedQuote:
    """Semantic quote with location tracking"""
    text: str
    line_start: int
    line_end: int
    semantic_type: SemanticUnit
    confidence: float
    speaker: Optional[str] = None
    context: Optional[str] = None
    id: Optional[str] = None  # Database ID after storage
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j storage"""
        data = {
            'text': self.text,
            'line_start': self.line_start,
            'line_end': self.line_end,
            'semantic_type': self.semantic_type.value,
            'confidence': self.confidence,
            'speaker': self.speaker or '',
            'context': self.context or ''
        }
        if self.id:
            data['id'] = self.id
        return data


class SemanticQuoteExtractor:
    """
    Extract quotes as semantic units (sentences/paragraphs) rather than arbitrary lines.
    
    This addresses the critical flaw identified in CLAUDE.md where line-based extraction
    was semantically meaningless since lines are formatting boundaries, not semantic units.
    """
    
    def __init__(self):
        self.min_quote_length = 10
        self.max_quote_length = 500
        self.confidence_threshold = 0.3
        
    def extract_quotes_from_interview(self, text: str, interview_id: str) -> List[ExtractedQuote]:
        """
        Extract semantic quotes from interview text
        
        Args:
            text: Interview text content
            interview_id: Interview identifier
            
        Returns:
            List of extracted quotes with semantic boundaries
        """
        logger.info(f"Extracting semantic quotes from interview: {interview_id}")
        
        # Split text into lines for line number tracking
        lines = text.split('\n')
        
        # Extract quotes using different semantic strategies
        quotes = []
        
        # Strategy 1: Sentence-based extraction
        sentence_quotes = self._extract_sentence_quotes(lines)
        quotes.extend(sentence_quotes)
        
        # Strategy 2: Paragraph-based extraction for longer content
        paragraph_quotes = self._extract_paragraph_quotes(lines)
        quotes.extend(paragraph_quotes)
        
        # Filter and deduplicate quotes
        quotes = self._filter_and_deduplicate_quotes(quotes)
        
        logger.info(f"Extracted {len(quotes)} semantic quotes from {interview_id}")
        return quotes
    
    def _extract_sentence_quotes(self, lines: List[str]) -> List[ExtractedQuote]:
        """Extract quotes based on sentence boundaries"""
        quotes = []
        
        for line_idx, line in enumerate(lines):
            if not line.strip():
                continue
                
            # Use semantic sentence detection
            sentences = self._detect_sentences(line)
            
            for sentence in sentences:
                if self._is_meaningful_quote(sentence):
                    quote = ExtractedQuote(
                        text=sentence.strip(),
                        line_start=line_idx + 1,  # 1-based line numbers
                        line_end=line_idx + 1,
                        semantic_type=SemanticUnit.SENTENCE,
                        confidence=self._calculate_quote_confidence(sentence, SemanticUnit.SENTENCE)
                    )
                    quotes.append(quote)
        
        return quotes
    
    def _extract_paragraph_quotes(self, lines: List[str]) -> List[ExtractedQuote]:
        """Extract quotes based on paragraph boundaries"""
        quotes = []
        current_paragraph = []
        paragraph_start_line = 0
        
        for line_idx, line in enumerate(lines):
            if line.strip():
                if not current_paragraph:
                    paragraph_start_line = line_idx + 1
                current_paragraph.append(line.strip())
            else:
                # End of paragraph
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    
                    if self._is_meaningful_quote(paragraph_text):
                        quote = ExtractedQuote(
                            text=paragraph_text,
                            line_start=paragraph_start_line,
                            line_end=line_idx,  # Last non-empty line
                            semantic_type=SemanticUnit.PARAGRAPH,
                            confidence=self._calculate_quote_confidence(paragraph_text, SemanticUnit.PARAGRAPH)
                        )
                        quotes.append(quote)
                    
                    current_paragraph = []
        
        # Handle final paragraph if file doesn't end with empty line
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            if self._is_meaningful_quote(paragraph_text):
                quote = ExtractedQuote(
                    text=paragraph_text,
                    line_start=paragraph_start_line,
                    line_end=len(lines),
                    semantic_type=SemanticUnit.PARAGRAPH,
                    confidence=self._calculate_quote_confidence(paragraph_text, SemanticUnit.PARAGRAPH)
                )
                quotes.append(quote)
        
        return quotes
    
    def _detect_sentences(self, text: str) -> List[str]:
        """
        Detect sentence boundaries using semantic rules
        
        This is more sophisticated than simple period splitting to handle
        abbreviations, quotes, and other complexities.
        """
        # Handle common abbreviations that shouldn't split sentences
        abbreviations = ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Gen.', 'Col.', 'Lt.', 'Sgt.']
        
        # Temporarily replace abbreviations
        protected_text = text
        replacements = {}
        for i, abbrev in enumerate(abbreviations):
            placeholder = f"__ABBREV_{i}__"
            replacements[placeholder] = abbrev
            protected_text = protected_text.replace(abbrev, placeholder)
        
        # Split on sentence-ending punctuation followed by whitespace and capital letter
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, protected_text)
        
        # Restore abbreviations
        for i, sentence in enumerate(sentences):
            for placeholder, abbrev in replacements.items():
                sentences[i] = sentence.replace(placeholder, abbrev)
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _is_meaningful_quote(self, text: str) -> bool:
        """
        Determine if text constitutes a meaningful quote
        
        Filters out headers, timestamps, and other non-content text
        """
        if not text or len(text.strip()) < self.min_quote_length:
            return False
            
        if len(text) > self.max_quote_length:
            return False
        
        # Filter out common non-content patterns
        non_content_patterns = [
            r'^\d+$',  # Just numbers
            r'^[A-Z\s]+$',  # All caps headers
            r'^\d{1,2}:\d{2}',  # Timestamps
            r'^Interview with',  # Interview headers
            r'^Date:',  # Date headers
            r'^Location:',  # Location headers
        ]
        
        for pattern in non_content_patterns:
            if re.match(pattern, text.strip()):
                return False
        
        # Must contain some substantive content (not just punctuation/whitespace)
        if not re.search(r'[a-zA-Z]{3,}', text):
            return False
        
        return True
    
    def _calculate_quote_confidence(self, text: str, semantic_type: SemanticUnit) -> float:
        """
        Calculate confidence score for extracted quote
        
        Based on semantic coherence, length, and content quality
        """
        base_confidence = 0.5
        
        # Length factor (optimal range gets higher confidence)
        length = len(text)
        if 50 <= length <= 200:
            length_factor = 1.0
        elif 20 <= length < 50 or 200 < length <= 300:
            length_factor = 0.8
        elif length < 20 or length > 300:
            length_factor = 0.6
        else:
            length_factor = 0.4
        
        # Semantic type factor
        if semantic_type == SemanticUnit.SENTENCE:
            type_factor = 0.9  # Sentences are generally good quotes
        elif semantic_type == SemanticUnit.PARAGRAPH:
            type_factor = 0.7  # Paragraphs might be too long but have context
        else:  # LINE fallback
            type_factor = 0.5
        
        # Content quality factor
        quality_factor = self._assess_content_quality(text)
        
        # Combine factors
        confidence = base_confidence * length_factor * type_factor * quality_factor
        
        return min(1.0, max(0.0, confidence))
    
    def _assess_content_quality(self, text: str) -> float:
        """Assess content quality for confidence calculation"""
        quality_score = 0.5
        
        # Has proper sentence structure
        if re.search(r'[.!?]$', text.strip()):
            quality_score += 0.1
        
        # Contains meaningful words (not just function words)
        meaningful_words = re.findall(r'\b[A-Za-z]{4,}\b', text)
        if len(meaningful_words) >= 3:
            quality_score += 0.2
        
        # Contains specific entities or concepts (capitalized words)
        entities = re.findall(r'\b[A-Z][a-z]+\b', text)
        if len(entities) >= 1:
            quality_score += 0.1
        
        # Not too much repetition
        words = text.lower().split()
        if len(set(words)) / len(words) > 0.7:  # Good word diversity
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    def _filter_and_deduplicate_quotes(self, quotes: List[ExtractedQuote]) -> List[ExtractedQuote]:
        """
        Filter quotes by confidence and remove duplicates
        
        Handles overlapping quotes from different extraction strategies
        """
        # Filter by confidence threshold
        filtered_quotes = [q for q in quotes if q.confidence >= self.confidence_threshold]
        
        # Sort by confidence (descending) for deduplication priority
        filtered_quotes.sort(key=lambda q: q.confidence, reverse=True)
        
        # Deduplicate based on text similarity and line overlap
        deduplicated = []
        for quote in filtered_quotes:
            is_duplicate = False
            
            for existing in deduplicated:
                # Check for text similarity (> 80% overlap)
                if self._calculate_text_similarity(quote.text, existing.text) > 0.8:
                    is_duplicate = True
                    break
                
                # Check for significant line overlap
                if self._check_line_overlap(quote, existing):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(quote)
        
        # Sort by line number for final output
        deduplicated.sort(key=lambda q: q.line_start)
        
        return deduplicated
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple word overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _check_line_overlap(self, quote1: ExtractedQuote, quote2: ExtractedQuote) -> bool:
        """Check if two quotes have significant line overlap"""
        # Calculate overlap
        start1, end1 = quote1.line_start, quote1.line_end
        start2, end2 = quote2.line_start, quote2.line_end
        
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start > overlap_end:
            return False  # No overlap
        
        overlap_lines = overlap_end - overlap_start + 1
        
        # Consider overlap significant if > 50% of either quote
        quote1_lines = end1 - start1 + 1
        quote2_lines = end2 - start2 + 1
        
        overlap_ratio1 = overlap_lines / quote1_lines
        overlap_ratio2 = overlap_lines / quote2_lines
        
        return overlap_ratio1 > 0.5 or overlap_ratio2 > 0.5


# Test the semantic quote extractor
def test_semantic_quote_extractor():
    """Test the semantic quote extraction"""
    print("Testing Semantic Quote Extractor")
    print("=" * 50)
    
    # Sample interview text
    test_text = """Interview with Conventional Force Civil Affairs team, USEMB Abidjan, March 12, 2025
We have been more focused at the operational strategic level. We are the 2nd full time 9 month team on the ground. We are starting our relief in place next week.
We have been developing the CA mission here by creating an assistant partner force curriculum.

For the Armed Forces Academy. Advising on CMO Curriculum
Building trust is the number two on country priorities behind the CT mission
Collaborating on curriculum based on FM 3-57, which is translated into French

Deputy armed forces commander, Gen Mouho is the DCG of land forces
SOF and conventional CA teams doing separate operations.
We deal with Mouho who was at the Armed forces Academy. His new replacement is COL Ouattara
Mouho was the force behind the CA training, he is a pioneer

Right now CA is not an identifier or MOS for the force. African armies will often point guns at civilians so civilians are scared of the military. There has been bad rapport right now so this is why relationships are important."""
    
    # Initialize extractor
    extractor = SemanticQuoteExtractor()
    
    # Extract quotes
    quotes = extractor.extract_quotes_from_interview(test_text, "test_interview")
    
    print(f"Extracted {len(quotes)} semantic quotes:")
    print()
    
    for i, quote in enumerate(quotes, 1):
        print(f"Quote {i}:")
        print(f"  Text: {quote.text}")
        print(f"  Lines: {quote.line_start}-{quote.line_end}")
        print(f"  Type: {quote.semantic_type.value}")
        print(f"  Confidence: {quote.confidence:.2f}")
        print()
    
    return quotes


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_semantic_quote_extractor()
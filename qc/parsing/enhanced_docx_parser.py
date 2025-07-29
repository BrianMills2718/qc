"""
Enhanced DOCX Parser with paragraph-level tracking for quote traceability
"""
from docx import Document
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EnhancedDOCXParser:
    """Enhanced parser that tracks paragraph positions for quote traceability"""
    
    def __init__(self):
        """Initialize enhanced DOCX parser"""
        self.paragraph_map = []  # List of (para_num, start_char, end_char, text)
        
    def parse_with_positions(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse DOCX file with paragraph-level position tracking.
        
        Returns:
            Dictionary containing:
            - content: Full text content
            - paragraphs: List of paragraph dictionaries with position info
            - metadata: File metadata
            - estimated_tokens: Token estimate
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Interview file not found: {file_path}")
            
        if not file_path.suffix.lower() == '.docx':
            raise ValueError(f"File must be DOCX format, got: {file_path.suffix}")
            
        try:
            doc = Document(file_path)
            
            # Parse with position tracking
            paragraphs = []
            full_text_parts = []
            current_char_offset = 0
            
            for para_num, paragraph in enumerate(doc.paragraphs, 1):
                if paragraph.text.strip():
                    text = paragraph.text.strip()
                    start_offset = current_char_offset
                    end_offset = start_offset + len(text)
                    
                    # Store paragraph info
                    para_info = {
                        'paragraph_number': para_num,
                        'text': text,
                        'start_offset': start_offset,
                        'end_offset': end_offset,
                        'speaker': self._extract_speaker(text),
                        'is_question': self._is_question(text)
                    }
                    paragraphs.append(para_info)
                    
                    full_text_parts.append(text)
                    # Add newline character offset
                    current_char_offset = end_offset + 1
            
            # Join full text
            content = '\n'.join(full_text_parts)
            
            # Extract metadata
            props = doc.core_properties
            word_count = len(content.split())
            
            metadata = {
                'title': props.title or file_path.stem,
                'author': props.author or 'Unknown',
                'created': props.created.isoformat() if props.created else None,
                'modified': props.modified.isoformat() if props.modified else None,
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size_bytes': file_path.stat().st_size,
                'word_count': word_count,
                'paragraph_count': len(paragraphs),
                'parsed_timestamp': datetime.now().isoformat()
            }
            
            # Estimate tokens
            estimated_tokens = int(word_count * 1.3)
            
            logger.info(f"Enhanced parse of {file_path.name}: {len(paragraphs)} paragraphs, {word_count} words")
            
            return {
                'content': content,
                'paragraphs': paragraphs,
                'metadata': metadata,
                'estimated_tokens': estimated_tokens,
                'parsing_info': {
                    'success': True,
                    'total_paragraphs': len(paragraphs),
                    'speakers_found': len(set(p['speaker'] for p in paragraphs if p['speaker']))
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to parse DOCX file {file_path}: {str(e)}")
            raise
            
    def find_quote_location(self, quote: str, paragraphs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find the paragraph location of a quote.
        
        Returns:
            Dictionary with paragraph_number, start_offset, end_offset
        """
        quote_lower = quote.lower().strip()
        
        for para in paragraphs:
            if quote_lower in para['text'].lower():
                # Find exact position within paragraph
                text_lower = para['text'].lower()
                quote_start_in_para = text_lower.find(quote_lower)
                
                if quote_start_in_para != -1:
                    return {
                        'paragraph_number': para['paragraph_number'],
                        'char_offset_in_para': quote_start_in_para,
                        'absolute_char_offset': para['start_offset'] + quote_start_in_para,
                        'speaker': para['speaker'],
                        'preceding_context': para['text'][:quote_start_in_para][-100:] if quote_start_in_para > 0 else '',
                        'following_context': para['text'][quote_start_in_para + len(quote):][:100]
                    }
        
        return None
        
    def _extract_speaker(self, text: str) -> Optional[str]:
        """Extract speaker name if this is a speaker line"""
        # Common patterns: "Name:", "INTERVIEWER:", "Participant 1:"
        if ':' in text and len(text.split(':')[0]) < 50:
            potential_speaker = text.split(':')[0].strip()
            # Basic validation
            if potential_speaker and not any(char.isdigit() for char in potential_speaker[-3:]):
                return potential_speaker
        return None
        
    def _is_question(self, text: str) -> bool:
        """Check if paragraph appears to be a question"""
        return text.strip().endswith('?')
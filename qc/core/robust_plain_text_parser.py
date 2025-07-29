"""
Robust plain text parser with flexible section detection and validation
"""
import re
import logging
from typing import Dict, Optional, List, Tuple

logger = logging.getLogger(__name__)


class RobustPlainTextParser:
    """Parse plain text responses with flexibility and error recovery."""
    
    def __init__(self):
        # Define section patterns with flexibility
        self.section_patterns = [
            r'===\s*(\w+(?:_\w+)*)\s*===',  # === SECTION_NAME ===
            r'==\s*(\w+(?:_\w+)*)\s*==',    # == SECTION_NAME ==
            r'###\s*(\w+(?:_\w+)*)\s*###',  # ### SECTION_NAME ###
            r'^(\w+(?:_\w+)*):$',           # SECTION_NAME:
            r'\[\s*(\w+(?:_\w+)*)\s*\]',    # [ SECTION_NAME ]
        ]
        
        # Expected sections for validation
        self.expected_sections = {
            'THEMES_CSV', 'CODES_CSV', 'QUOTES_CSV', 
            'QUOTE_CHAINS_CSV', 'CONTRADICTIONS_CSV',
            'STAKEHOLDER_POSITIONS_CSV', 'SATURATION_CURVE_CSV',
            'TRACEABILITY_MATRIX_CSV', 'MARKDOWN_REPORT',
            'EXECUTIVE_SUMMARY', 'COMPLETE_QUOTE_INVENTORY_JSON',
            'INTERVIEW_SUMMARIES_JSON', 'METRICS'
        }
        
        # Section aliases for flexibility
        self.section_aliases = {
            'THEMES CSV': 'THEMES_CSV',
            'CODES CSV': 'CODES_CSV',
            'QUOTES CSV': 'QUOTES_CSV',
            'QUOTE CHAINS CSV': 'QUOTE_CHAINS_CSV',
            'CONTRADICTIONS CSV': 'CONTRADICTIONS_CSV',
            'STAKEHOLDER POSITIONS CSV': 'STAKEHOLDER_POSITIONS_CSV',
            'SATURATION CURVE CSV': 'SATURATION_CURVE_CSV',
            'TRACEABILITY MATRIX CSV': 'TRACEABILITY_MATRIX_CSV',
            'MARKDOWN REPORT': 'MARKDOWN_REPORT',
            'EXECUTIVE SUMMARY': 'EXECUTIVE_SUMMARY',
            'COMPLETE QUOTE INVENTORY JSON': 'COMPLETE_QUOTE_INVENTORY_JSON',
            'INTERVIEW SUMMARIES JSON': 'INTERVIEW_SUMMARIES_JSON',
        }
    
    def parse(self, text: str) -> Dict[str, str]:
        """Parse plain text into sections with robust detection."""
        sections = {}
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for i, line in enumerate(lines):
            # Try to detect section header
            section_name = self._detect_section(line)
            
            if section_name:
                # Save previous section
                if current_section:
                    content = '\n'.join(current_content).strip()
                    sections[current_section] = content
                    logger.debug(f"Parsed section {current_section}: {len(content)} chars")
                
                # Start new section
                current_section = self._normalize_section_name(section_name)
                current_content = []
            else:
                # Add line to current section
                if current_section:
                    current_content.append(line)
        
        # Save last section
        if current_section:
            content = '\n'.join(current_content).strip()
            sections[current_section] = content
            logger.debug(f"Parsed section {current_section}: {len(content)} chars")
        
        # Validate and report missing sections
        missing = self.expected_sections - set(sections.keys())
        if missing:
            logger.warning(f"Missing expected sections: {missing}")
        
        # Fill in empty sections
        for section in self.expected_sections:
            if section not in sections:
                sections[section] = ""
                logger.debug(f"Added empty section: {section}")
        
        return sections
    
    def _detect_section(self, line: str) -> Optional[str]:
        """Detect if line is a section header."""
        line = line.strip()
        
        # Try each pattern
        for pattern in self.section_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _normalize_section_name(self, name: str) -> str:
        """Normalize section name to expected format."""
        # Convert to uppercase
        name = name.upper()
        
        # Check aliases
        if name in self.section_aliases:
            return self.section_aliases[name]
        
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        
        return name
    
    def validate_csv_content(self, csv_content: str, expected_headers: List[str]) -> Tuple[bool, str]:
        """Validate CSV content structure."""
        if not csv_content.strip():
            return True, "Empty CSV content"
        
        lines = csv_content.strip().split('\n')
        if not lines:
            return False, "No lines in CSV"
        
        # Check headers
        headers = lines[0].split(',')
        missing_headers = set(expected_headers) - set(h.strip() for h in headers)
        
        if missing_headers:
            return False, f"Missing headers: {missing_headers}"
        
        # Check at least one data row
        if len(lines) < 2:
            return False, "No data rows in CSV"
        
        return True, "Valid CSV structure"
    
    def extract_metrics(self, metrics_text: str) -> Dict[str, float]:
        """Extract metrics from various formats."""
        metrics = {}
        
        # Pattern 1: key: value
        pattern1 = r'(\w+(?:_\w+)*)\s*:\s*([\d.]+)'
        
        # Pattern 2: key = value
        pattern2 = r'(\w+(?:_\w+)*)\s*=\s*([\d.]+)'
        
        # Pattern 3: key - value
        pattern3 = r'(\w+(?:_\w+)*)\s*-\s*([\d.]+)'
        
        for pattern in [pattern1, pattern2, pattern3]:
            matches = re.findall(pattern, metrics_text, re.MULTILINE)
            for key, value in matches:
                try:
                    metrics[key.lower()] = float(value)
                except ValueError:
                    logger.warning(f"Could not parse metric value: {key}={value}")
        
        return metrics


def test_parser():
    """Test the robust parser with various formats."""
    
    test_cases = [
        # Case 1: Standard format
        """=== THEMES_CSV ===
theme_id,name,prevalence
T1,Theme 1,0.8

=== CODES_CSV ===
code_id,name
C1,Code 1""",
        
        # Case 2: Different markers
        """== THEMES CSV ==
theme_id,name
T1,Theme 1

### CODES CSV ###
code_id,name
C1,Code 1""",
        
        # Case 3: Simple headers
        """THEMES_CSV:
theme_id,name
T1,Theme 1

CODES_CSV:
code_id,name
C1,Code 1"""
    ]
    
    parser = RobustPlainTextParser()
    
    for i, test_text in enumerate(test_cases):
        print(f"\n--- Test Case {i+1} ---")
        sections = parser.parse(test_text)
        
        print(f"Found sections: {list(sections.keys())}")
        print(f"THEMES_CSV: {sections.get('THEMES_CSV', 'NOT FOUND')[:50]}...")
        print(f"CODES_CSV: {sections.get('CODES_CSV', 'NOT FOUND')[:50]}...")


if __name__ == "__main__":
    test_parser()
"""
Error recovery and data fixing utilities
"""
import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class DataFixer:
    """Fix common data issues from LLM responses."""
    
    def repair_json_string(self, json_str: str) -> str:
        """Attempt to repair common JSON formatting issues."""
        # Remove BOM if present
        if json_str.startswith('\ufeff'):
            json_str = json_str[1:]
        
        # Fix unescaped quotes inside strings
        # This is a simple heuristic that may not catch all cases
        lines = json_str.split('\n')
        fixed_lines = []
        in_string = False
        
        for line in lines:
            # Count quotes to track if we're in a string
            quote_count = 0
            fixed_line = []
            i = 0
            while i < len(line):
                char = line[i]
                if char == '"' and (i == 0 or line[i-1] != '\\'):
                    quote_count += 1
                    in_string = quote_count % 2 == 1
                elif char == '"' and in_string:
                    # Unescaped quote inside string, escape it
                    fixed_line.append('\\"')
                    i += 1
                    continue
                fixed_line.append(char)
                i += 1
            fixed_lines.append(''.join(fixed_line))
        
        json_str = '\n'.join(fixed_lines)
        
        # Fix trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # Ensure proper quote closure
        if json_str.count('"') % 2 != 0:
            # Find the last quote and check if it needs closing
            last_quote_idx = json_str.rfind('"')
            # Check if there's a closing brace or bracket after the last quote
            after_quote = json_str[last_quote_idx + 1:].strip()
            if after_quote and after_quote[0] in ['}', ']']:
                # Add closing quote before the brace/bracket
                json_str = json_str[:last_quote_idx + 1] + '"' + json_str[last_quote_idx + 1:]
        
        return json_str
    
    def fix_missing_theme_ids(self, themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add missing theme_id fields to themes."""
        fixed_themes = []
        
        for i, theme in enumerate(themes):
            if 'theme_id' not in theme:
                theme['theme_id'] = f"T{i+1:03d}"
                logger.warning(f"Added missing theme_id: {theme['theme_id']}")
            fixed_themes.append(theme)
        
        return fixed_themes
    
    def fix_missing_code_ids(self, codes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add missing code_id fields to codes."""
        fixed_codes = []
        
        for i, code in enumerate(codes):
            if 'code_id' not in code:
                code['code_id'] = f"C{i+1:03d}"
                logger.warning(f"Added missing code_id: {code['code_id']}")
            fixed_codes.append(code)
        
        return fixed_codes
    
    def fix_missing_fields(self, data: Dict[str, Any], 
                          required_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Add missing required fields with defaults."""
        fixed_data = data.copy()
        
        for field, default_value in required_fields.items():
            if field not in fixed_data:
                fixed_data[field] = default_value
                logger.warning(f"Added missing field '{field}' with default: {default_value}")
        
        return fixed_data
    
    def fix_response_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Fix common issues in LLM response data."""
        fixed_response = response.copy()
        
        # Fix themes
        if 'themes' in fixed_response:
            fixed_response['themes'] = self.fix_missing_theme_ids(fixed_response['themes'])
            
            # Ensure each theme has required fields
            for theme in fixed_response['themes']:
                theme_defaults = {
                    'description': 'No description provided',
                    'prevalence': 0.5,
                    'interviews_count': 1,
                    'key_quotes': [],
                    'confidence_score': 0.5
                }
                for field, default in theme_defaults.items():
                    if field not in theme:
                        theme[field] = default
                
                # Fix prevalence if it's a string
                if isinstance(theme.get('prevalence'), str):
                    prevalence_str = theme['prevalence'].lower()
                    if 'universal' in prevalence_str or 'all' in prevalence_str or 'every' in prevalence_str:
                        theme['prevalence'] = 1.0
                    elif 'high' in prevalence_str or 'most' in prevalence_str or 'majority' in prevalence_str:
                        theme['prevalence'] = 0.8
                    elif 'medium' in prevalence_str or 'moderate' in prevalence_str or 'some' in prevalence_str:
                        theme['prevalence'] = 0.5
                    elif 'low' in prevalence_str or 'few' in prevalence_str or 'minor' in prevalence_str:
                        theme['prevalence'] = 0.3
                    elif 'rare' in prevalence_str or 'minimal' in prevalence_str:
                        theme['prevalence'] = 0.1
                    else:
                        # Try to extract any number from the string
                        import re
                        numbers = re.findall(r'\d+\.?\d*', prevalence_str)
                        if numbers:
                            # Check for "X of Y" pattern
                            if len(numbers) >= 2 and ' of ' in prevalence_str:
                                # Calculate ratio
                                theme['prevalence'] = float(numbers[0]) / float(numbers[1])
                            else:
                                # Single number
                                num = float(numbers[0])
                                if num > 1:  # Assume it's a percentage
                                    theme['prevalence'] = num / 100.0
                                else:
                                    theme['prevalence'] = num
                        else:
                            theme['prevalence'] = 0.5  # Default
                    logger.warning(f"Converted prevalence '{prevalence_str[:50]}...' to {theme['prevalence']}")
        
        # Fix codes
        if 'codes' in fixed_response:
            fixed_response['codes'] = self.fix_missing_code_ids(fixed_response['codes'])
            
            # Ensure each code has required fields
            for code in fixed_response['codes']:
                code_defaults = {
                    'definition': 'No definition provided',
                    'frequency': 1,
                    'interviews_present': [],
                    'first_appearance': 'INT_001',
                    'theme_id': 'T001',  # Default theme
                    'parent_code_id': None,
                    'hierarchy_level': 0
                }
                for field, default in code_defaults.items():
                    if field not in code:
                        code[field] = default
        
        # Fix theoretical_insights if they're objects instead of strings
        if 'theoretical_insights' in fixed_response:
            insights = fixed_response['theoretical_insights']
            if insights and isinstance(insights[0], dict):
                # Convert dict insights to strings
                fixed_insights = []
                for insight in insights:
                    if isinstance(insight, dict):
                        # Extract the insight text from the dict
                        insight_text = insight.get('insight', insight.get('description', str(insight)))
                        fixed_insights.append(insight_text)
                    else:
                        fixed_insights.append(str(insight))
                fixed_response['theoretical_insights'] = fixed_insights
                logger.warning(f"Converted {len(insights)} theoretical insights from dict to string")
        
        # Fix stakeholder positions if present
        if 'stakeholder_positions' in fixed_response:
            for position in fixed_response['stakeholder_positions']:
                position_defaults = {
                    'recommendations': []  # This is the missing field causing errors
                }
                for field, default in position_defaults.items():
                    if field not in position:
                        position[field] = default
                        logger.warning(f"Added missing field '{field}' to stakeholder position")
        
        # Fix other required top-level fields
        top_level_defaults = {
            'quote_chains': [],
            'theoretical_insights': [],
            'emergent_theory': 'Theory not yet developed',
            'methodological_notes': 'Standard grounded theory approach',
            'saturation_point': 'INT_010',
            'saturation_evidence': 'Saturation assessment pending',
            'overall_confidence': 0.7,
            'contradictions': [],
            'stakeholder_positions': []
        }
        
        for field, default in top_level_defaults.items():
            if field not in fixed_response:
                fixed_response[field] = default
                logger.warning(f"Added missing top-level field '{field}'")
        
        return fixed_response
    
    def extract_interview_id_from_quote(self, quote_text: str) -> Optional[str]:
        """Extract interview ID from quote text."""
        # Pattern 1: "Interview 001:" or "(Interview 001)"
        pattern1 = r'Interview\s+(\d+)[:\)]'
        match1 = re.search(pattern1, quote_text)
        if match1:
            num = match1.group(1).zfill(3)
            return f"INT_{num}"
        
        # Pattern 2: "INT_001" directly in text
        pattern2 = r'INT_(\d{3})'
        match2 = re.search(pattern2, quote_text)
        if match2:
            return f"INT_{match2.group(1)}"
        
        return None


class RetryHandler:
    """Handle retries with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def retry_with_backoff(self, func, *args, **kwargs):
        """Retry a function with exponential backoff."""
        import asyncio
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Succeeded on attempt {attempt + 1}")
                return result
            
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
        
        raise last_error
"""
Generate CSV files programmatically from structured data
"""
import csv
import io
from typing import List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CSVGenerator:
    """Generate CSV files from structured analysis data."""
    
    def generate_themes_csv(self, themes: List[Dict[str, Any]]) -> str:
        """Generate themes CSV from theme objects."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'theme_id', 'name', 'prevalence', 'confidence', 'interview_count'
        ])
        writer.writeheader()
        
        for theme in themes:
            writer.writerow({
                'theme_id': theme.get('theme_id'),
                'name': theme.get('name'),
                'prevalence': theme.get('prevalence', 0.0),
                'confidence': theme.get('confidence_score', 0.0),
                'interview_count': theme.get('interviews_count', 0)
            })
        
        return output.getvalue()
    
    def generate_codes_csv(self, codes: List[Dict[str, Any]]) -> str:
        """Generate codes CSV from code objects."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'code_id', 'name', 'definition', 'frequency', 'first_appearance', 'theme_id',
            'parent_code_id', 'hierarchy_level'
        ])
        writer.writeheader()
        
        # Sort codes by hierarchy level and parent to show structure
        sorted_codes = sorted(codes, key=lambda c: (
            c.get('hierarchy_level', 0),
            c.get('parent_code_id', ''),
            c.get('code_id', '')
        ))
        
        for code in sorted_codes:
            # Add indentation to name based on hierarchy level
            hierarchy_level = code.get('hierarchy_level', 0)
            name = code.get('name', '')
            if hierarchy_level > 0:
                name = '  ' * hierarchy_level + name
            
            writer.writerow({
                'code_id': code.get('code_id'),
                'name': name,
                'definition': code.get('definition', ''),
                'frequency': code.get('frequency', 0),
                'first_appearance': code.get('first_appearance', ''),
                'theme_id': code.get('theme_id', ''),
                'parent_code_id': code.get('parent_code_id', ''),
                'hierarchy_level': hierarchy_level
            })
        
        return output.getvalue()
    
    def generate_quotes_csv(self, quotes: List[Dict[str, Any]]) -> str:
        """Generate quotes CSV from quote objects."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'quote_id', 'text', 'speaker', 'interview_id', 'interview_name', 
            'line_number', 'code_ids', 'theme_ids'
        ])
        writer.writeheader()
        
        for quote in quotes:
            writer.writerow({
                'quote_id': quote.get('quote_id'),
                'text': quote.get('text', ''),
                'speaker': quote.get('speaker_role', ''),
                'interview_id': quote.get('interview_id', ''),
                'interview_name': quote.get('interview_name', ''),
                'line_number': quote.get('line_number', 0),
                'code_ids': ';'.join(quote.get('code_ids', [])),
                'theme_ids': ';'.join(quote.get('theme_ids', []))
            })
        
        return output.getvalue()
    
    def generate_theme_analysis_csv(self, themes: List[Dict[str, Any]], codes: List[Dict[str, Any]]) -> str:
        """Generate detailed theme analysis CSV with statistics and exemplar quotes."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'theme_id', 'theme_name', 'prevalence', 'interview_count', 'code_count',
            'exemplar_quote_1', 'exemplar_quote_2', 'exemplar_quote_3',
            'key_insights', 'saturation_point'
        ])
        writer.writeheader()
        
        # Create theme to codes mapping
        theme_codes = {}
        for theme in themes:
            theme_codes[theme['theme_id']] = theme.get('codes', [])
        
        for theme in themes:
            # Get first 3 key quotes
            key_quotes = theme.get('key_quotes', [])
            exemplar_1 = key_quotes[0]['text'] if len(key_quotes) > 0 else ''
            exemplar_2 = key_quotes[1]['text'] if len(key_quotes) > 1 else ''
            exemplar_3 = key_quotes[2]['text'] if len(key_quotes) > 2 else ''
            
            writer.writerow({
                'theme_id': theme.get('theme_id'),
                'theme_name': theme.get('name'),
                'prevalence': theme.get('prevalence', 0.0),
                'interview_count': theme.get('interviews_count', 0),
                'code_count': len(theme_codes.get(theme['theme_id'], [])),
                'exemplar_quote_1': exemplar_1[:200] + '...' if len(exemplar_1) > 200 else exemplar_1,
                'exemplar_quote_2': exemplar_2[:200] + '...' if len(exemplar_2) > 200 else exemplar_2,
                'exemplar_quote_3': exemplar_3[:200] + '...' if len(exemplar_3) > 200 else exemplar_3,
                'key_insights': theme.get('theoretical_memo', '')[:300],
                'saturation_point': theme.get('saturation_point', '')
            })
        
        return output.getvalue()
    
    def generate_code_progression_csv(self, codes: List[Dict[str, Any]]) -> str:
        """Generate code progression CSV showing how codes evolve."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'code_id', 'code_name', 'first_appearance', 'evolution_notes',
            'frequency', 'interview_progression', 'saturation_point'
        ])
        writer.writeheader()
        
        for code in codes:
            writer.writerow({
                'code_id': code.get('code_id'),
                'code_name': code.get('name'),
                'first_appearance': code.get('first_appearance', ''),
                'evolution_notes': code.get('evolution_notes', ''),
                'frequency': code.get('frequency', 0),
                'interview_progression': ', '.join(code.get('interviews_present', [])),
                'saturation_point': code.get('saturation_point', '')
            })
        
        return output.getvalue()
    
    def generate_quote_evidence_csv(self, quotes: List[Dict[str, Any]], 
                                   codes: List[Dict[str, Any]], 
                                   themes: List[Dict[str, Any]]) -> str:
        """Generate quote evidence CSV with full traceability."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'quote_id', 'text', 'speaker_name', 'speaker_role', 'interview_id',
            'paragraph_number', 'char_offset', 'preceding_context', 'following_context',
            'code_ids', 'theme_ids', 'confidence_score'
        ])
        writer.writeheader()
        
        for quote in quotes:
            # Extract text and speaker from combined format
            text = quote.get('text', '')
            speaker_name = 'Unknown'
            speaker_role = ''
            
            # Parse "Speaker Name (Role): Quote text" format
            if ':' in text:
                speaker_part, quote_text = text.split(':', 1)
                quote_text = quote_text.strip()
                
                # Extract role from parentheses if present
                if '(' in speaker_part and ')' in speaker_part:
                    name_part = speaker_part[:speaker_part.find('(')].strip()
                    role_part = speaker_part[speaker_part.find('(')+1:speaker_part.find(')')].strip()
                    speaker_name = name_part
                    speaker_role = role_part
                else:
                    speaker_name = speaker_part.strip()
            else:
                quote_text = text
            
            writer.writerow({
                'quote_id': quote.get('quote_id', ''),
                'text': quote_text[:500] + '...' if len(quote_text) > 500 else quote_text,
                'speaker_name': speaker_name,
                'speaker_role': speaker_role or quote.get('speaker_role', ''),
                'interview_id': quote.get('interview_id', ''),
                'paragraph_number': quote.get('paragraph_number', ''),
                'char_offset': quote.get('char_offset', ''),
                'preceding_context': quote.get('context', '')[:100],
                'following_context': '',  # Would need enhanced parser
                'code_ids': '; '.join(quote.get('code_ids', [])),
                'theme_ids': '; '.join(quote.get('theme_ids', [])),
                'confidence_score': quote.get('confidence', 0.0)
            })
        
        return output.getvalue()
    
    def generate_contradiction_matrix_csv(self, contradictions: List[Dict[str, Any]]) -> str:
        """Generate contradiction matrix CSV showing opposing viewpoints."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'contradiction_id', 'topic', 'position_1', 'position_1_holders',
            'position_1_quote_1', 'position_1_quote_2', 'position_2', 'position_2_holders',
            'position_2_quote_1', 'position_2_quote_2', 'resolution_suggested',
            'related_themes', 'related_codes'
        ])
        writer.writeheader()
        
        for cont in contradictions:
            # Get first 2 quotes for each position
            p1_quotes = cont.get('position_1_quotes', [])
            p2_quotes = cont.get('position_2_quotes', [])
            
            writer.writerow({
                'contradiction_id': cont.get('contradiction_id', ''),
                'topic': cont.get('topic', ''),
                'position_1': cont.get('position_1', ''),
                'position_1_holders': '; '.join(cont.get('position_1_holders', [])),
                'position_1_quote_1': p1_quotes[0]['text'][:300] if len(p1_quotes) > 0 else '',
                'position_1_quote_2': p1_quotes[1]['text'][:300] if len(p1_quotes) > 1 else '',
                'position_2': cont.get('position_2', ''),
                'position_2_holders': '; '.join(cont.get('position_2_holders', [])),
                'position_2_quote_1': p2_quotes[0]['text'][:300] if len(p2_quotes) > 0 else '',
                'position_2_quote_2': p2_quotes[1]['text'][:300] if len(p2_quotes) > 1 else '',
                'resolution_suggested': cont.get('resolution_suggested', ''),
                'related_themes': '; '.join(cont.get('theme_ids', [])),
                'related_codes': '; '.join(cont.get('code_ids', []))
            })
        
        return output.getvalue()
    
    def generate_stakeholder_positions_csv(self, stakeholders: List[Dict[str, Any]]) -> str:
        """Generate stakeholder positions CSV for policy analysis."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'stakeholder_id', 'stakeholder_name', 'stakeholder_type',
            'position_summary', 'main_quote', 'key_concerns', 'recommendations',
            'influence_level'
        ])
        writer.writeheader()
        
        for stake in stakeholders:
            # Get first main quote
            quotes = stake.get('supporting_quotes', [])
            main_quote = quotes[0]['text'] if quotes else ''
            
            writer.writerow({
                'stakeholder_id': stake.get('stakeholder_id', ''),
                'stakeholder_name': stake.get('stakeholder_name', ''),
                'stakeholder_type': stake.get('stakeholder_type', ''),
                'position_summary': stake.get('position_summary', '')[:500],
                'main_quote': main_quote[:500],
                'key_concerns': '; '.join(stake.get('concerns', [])),
                'recommendations': '; '.join(stake.get('recommendations', [])),
                'influence_level': stake.get('influence_level', 'medium')
            })
        
        return output.getvalue()
    
    def generate_all_csvs(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """Generate all CSV files from analysis result."""
        csvs = {}
        
        # Generate basic CSVs
        if 'themes' in analysis_result:
            csvs['themes.csv'] = self.generate_themes_csv(analysis_result['themes'])
            
        if 'codes' in analysis_result:
            csvs['codes.csv'] = self.generate_codes_csv(analysis_result['codes'])
        
        # Generate quotes CSV if we have quote inventory
        if 'complete_quote_inventory' in analysis_result:
            csvs['quotes.csv'] = self.generate_quotes_csv(
                analysis_result['complete_quote_inventory']
            )
        
        # Generate advanced CSVs
        if 'themes' in analysis_result and 'codes' in analysis_result:
            csvs['theme_analysis.csv'] = self.generate_theme_analysis_csv(
                analysis_result['themes'], 
                analysis_result['codes']
            )
        
        if 'codes' in analysis_result:
            csvs['code_progression.csv'] = self.generate_code_progression_csv(
                analysis_result['codes']
            )
        
        # Generate quote evidence CSV if we have enhanced quote data
        if 'complete_quote_inventory' in analysis_result:
            csvs['quote_evidence.csv'] = self.generate_quote_evidence_csv(
                analysis_result['complete_quote_inventory'],
                analysis_result.get('codes', []),
                analysis_result.get('themes', [])
            )
        
        # Generate contradiction matrix CSV
        if 'contradictions' in analysis_result:
            csvs['contradiction_matrix.csv'] = self.generate_contradiction_matrix_csv(
                analysis_result['contradictions']
            )
        
        # Generate stakeholder positions CSV
        if 'stakeholder_positions' in analysis_result:
            csvs['stakeholder_positions.csv'] = self.generate_stakeholder_positions_csv(
                analysis_result['stakeholder_positions']
            )
        
        # Add more CSV generators as needed
        
        logger.info(f"Generated {len(csvs)} CSV files programmatically")
        return csvs
    
    def save_csvs_to_disk(self, csvs: Dict[str, str], output_dir: Path):
        """Save generated CSVs to disk."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in csvs.items():
            filepath = output_dir / filename
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            logger.info(f"Saved {filename} ({len(content)} bytes)")
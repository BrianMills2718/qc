"""
CSV Export Utilities for Qualitative Coding Results

Ensures proper formatting and full traceability in CSV exports.
"""
import csv
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export qualitative coding results to CSV with full traceability."""
    
    @staticmethod
    def export_themes_table(themes: List[Dict], output_path: Path):
        """Export themes table with prevalence and confidence."""
        if not themes:
            logger.warning("No themes to export")
            return
            
        fieldnames = [
            'theme_id', 'theme_name', 'description', 'prevalence',
            'confidence', 'interview_count', 'code_count', 'has_contradictions'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for theme in themes:
                writer.writerow({
                    'theme_id': theme.get('theme_id', ''),
                    'theme_name': theme.get('name', ''),
                    'description': theme.get('description', ''),
                    'prevalence': theme.get('prevalence', 0),
                    'confidence': theme.get('confidence_score', 0),
                    'interview_count': theme.get('interviews_count', 0),
                    'code_count': len(theme.get('codes', [])),
                    'has_contradictions': 'Yes' if theme.get('contradictions') else 'No'
                })
        
        logger.info(f"Exported {len(themes)} themes to {output_path}")
    
    @staticmethod
    def export_codes_table(codes: List[Dict], output_path: Path):
        """Export codes table with frequencies and definitions."""
        if not codes:
            logger.warning("No codes to export")
            return
            
        fieldnames = [
            'code_id', 'code_name', 'definition', 'frequency',
            'interview_count', 'first_appearance', 'evolution_notes'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for code in codes:
                writer.writerow({
                    'code_id': code.get('code_id', ''),
                    'code_name': code.get('name', ''),
                    'definition': code.get('definition', ''),
                    'frequency': code.get('frequency', 0),
                    'interview_count': len(code.get('interviews_present', [])),
                    'first_appearance': code.get('first_appearance', ''),
                    'evolution_notes': code.get('evolution_notes', '')
                })
        
        logger.info(f"Exported {len(codes)} codes to {output_path}")
    
    @staticmethod
    def export_quotes_table(quotes: List[Dict], output_path: Path):
        """Export all quotes with full traceability."""
        if not quotes:
            logger.warning("No quotes to export")
            return
            
        fieldnames = [
            'quote_id', 'interview_id', 'interview_name', 'line_number',
            'quote_text', 'context', 'speaker_role', 'theme_ids', 'code_ids'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            for quote in quotes:
                # Clean quote text for CSV
                quote_text = quote.get('text', '').replace('\n', ' ').replace('\r', '')
                context = quote.get('context', '').replace('\n', ' ').replace('\r', '')
                
                writer.writerow({
                    'quote_id': quote.get('quote_id', ''),
                    'interview_id': quote.get('interview_id', ''),
                    'interview_name': quote.get('interview_name', ''),
                    'line_number': quote.get('line_number', ''),
                    'quote_text': quote_text,
                    'context': context,
                    'speaker_role': quote.get('speaker_role', ''),
                    'theme_ids': ';'.join(quote.get('theme_ids', [])),
                    'code_ids': ';'.join(quote.get('code_ids', []))
                })
        
        logger.info(f"Exported {len(quotes)} quotes to {output_path}")
    
    @staticmethod
    def export_quote_chains_table(chains: List[Dict], output_path: Path):
        """Export quote chains showing progressions."""
        if not chains:
            logger.warning("No quote chains to export")
            return
            
        fieldnames = [
            'chain_id', 'theme_id', 'chain_type', 'description',
            'quote_count', 'interviews_spanned', 'interpretation'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for chain in chains:
                quotes = chain.get('quotes_sequence', [])
                interview_ids = set(q.get('interview_id') for q in quotes if q.get('interview_id'))
                
                writer.writerow({
                    'chain_id': chain.get('chain_id', ''),
                    'theme_id': chain.get('theme_id', ''),
                    'chain_type': chain.get('chain_type', ''),
                    'description': chain.get('description', ''),
                    'quote_count': len(quotes),
                    'interviews_spanned': len(interview_ids),
                    'interpretation': chain.get('interpretation', '')
                })
        
        logger.info(f"Exported {len(chains)} quote chains to {output_path}")
    
    @staticmethod
    def export_contradictions_table(contradictions: List[Dict], output_path: Path):
        """Export contradictions with evidence from both sides."""
        if not contradictions:
            logger.warning("No contradictions to export")
            return
            
        fieldnames = [
            'contradiction_id', 'theme_id', 'issue', 'position_a', 'position_b',
            'evidence_count_a', 'evidence_count_b', 'stakeholders_a', 'stakeholders_b'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for contra in contradictions:
                writer.writerow({
                    'contradiction_id': contra.get('contradiction_id', ''),
                    'theme_id': contra.get('theme_id', ''),
                    'issue': contra.get('issue', ''),
                    'position_a': contra.get('position_a', ''),
                    'position_b': contra.get('position_b', ''),
                    'evidence_count_a': len(contra.get('evidence_a', [])),
                    'evidence_count_b': len(contra.get('evidence_b', [])),
                    'stakeholders_a': ';'.join(contra.get('stakeholders_a', [])),
                    'stakeholders_b': ';'.join(contra.get('stakeholders_b', []))
                })
        
        logger.info(f"Exported {len(contradictions)} contradictions to {output_path}")
    
    @staticmethod
    def export_traceability_matrix(matrix: List[Dict], output_path: Path):
        """Export complete traceability from themes to interviews."""
        if not matrix:
            logger.warning("No traceability data to export")
            return
            
        fieldnames = [
            'theme_id', 'theme_name', 'code_id', 'code_name',
            'quote_id', 'interview_id', 'interview_name', 'line_number'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in matrix:
                writer.writerow({
                    'theme_id': entry.get('theme_id', ''),
                    'theme_name': entry.get('theme_name', ''),
                    'code_id': entry.get('code_id', ''),
                    'code_name': entry.get('code_name', ''),
                    'quote_id': entry.get('quote_id', ''),
                    'interview_id': entry.get('interview_id', ''),
                    'interview_name': entry.get('interview_name', ''),
                    'line_number': entry.get('line_number', '')
                })
        
        logger.info(f"Exported {len(matrix)} traceability entries to {output_path}")
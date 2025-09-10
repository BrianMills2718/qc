#!/usr/bin/env python3
"""
Data Exporter - Export analysis results to various formats
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class DataExporter:
    """Export qualitative coding analysis results to various formats"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_results(self, results: Dict[str, Any], format: str = "json", filename: str = "results") -> str:
        """Export analysis results in specified format"""
        try:
            if format.lower() == "json":
                return self._export_json(results, filename)
            elif format.lower() == "csv":
                return self._export_csv(results, filename)
            elif format.lower() == "markdown":
                return self._export_markdown(results, filename)
            else:
                raise ValueError(f"Unsupported export format: {format}")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise
    
    def _export_json(self, results: Dict[str, Any], filename: str) -> str:
        """Export results as JSON"""
        output_path = self.output_dir / f"{filename}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results exported to {output_path}")
        return str(output_path)
    
    def _export_csv(self, results: Dict[str, Any], filename: str) -> str:
        """Export results as CSV"""
        output_path = self.output_dir / f"{filename}.csv"
        
        # Extract main data for CSV export
        rows = []
        if 'codes' in results:
            for code in results['codes']:
                rows.append({
                    'type': 'code',
                    'name': code.get('code_name', 'Unknown'),
                    'description': code.get('description', ''),
                    'frequency': code.get('frequency', 0)
                })
        
        if 'quotes' in results:
            for quote in results['quotes']:
                rows.append({
                    'type': 'quote',
                    'content': quote.get('text', ''),
                    'speaker': quote.get('speaker', 'Unknown'),
                    'codes': ', '.join(quote.get('codes', []))
                })
        
        if rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['type', 'name', 'description', 'frequency', 'content', 'speaker', 'codes']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        
        logger.info(f"Results exported to {output_path}")
        return str(output_path)
    
    def _export_markdown(self, results: Dict[str, Any], filename: str) -> str:
        """Export results as Markdown"""
        output_path = self.output_dir / f"{filename}.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Qualitative Coding Analysis Results\n\n")
            f.write(f"Generated: {results.get('timestamp', 'Unknown')}\n\n")
            
            # Export codes
            if 'codes' in results and results['codes']:
                f.write("## Codes Discovered\n\n")
                for code in results['codes']:
                    name = code.get('code_name', 'Unknown')
                    desc = code.get('description', 'No description')
                    freq = code.get('frequency', 0)
                    f.write(f"### {name}\n")
                    f.write(f"**Description**: {desc}\n")
                    f.write(f"**Frequency**: {freq}\n\n")
            
            # Export quotes
            if 'quotes' in results and results['quotes']:
                f.write("## Key Quotes\n\n")
                for i, quote in enumerate(results['quotes'][:10], 1):  # Limit to first 10
                    content = quote.get('text', 'No content')
                    speaker = quote.get('speaker', 'Unknown')
                    codes = quote.get('codes', [])
                    f.write(f"### Quote {i}\n")
                    f.write(f"**Speaker**: {speaker}\n")
                    f.write(f"**Content**: {content}\n")
                    if codes:
                        f.write(f"**Codes**: {', '.join(codes)}\n")
                    f.write("\n")
        
        logger.info(f"Results exported to {output_path}")
        return str(output_path)
    
    def export_codes_only(self, codes: List[Dict[str, Any]], format: str = "csv") -> str:
        """Export only the codes in specified format"""
        codes_data = {'codes': codes}
        return self.export_results(codes_data, format, "codes_only")
    
    def export_quotes_only(self, quotes: List[Dict[str, Any]], format: str = "csv") -> str:
        """Export only the quotes in specified format"""
        quotes_data = {'quotes': quotes}
        return self.export_results(quotes_data, format, "quotes_only")
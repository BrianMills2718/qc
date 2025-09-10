"""
Data loader for extraction results viewer
Handles all data loading and provides clean interfaces for components
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd


@dataclass
class ExtractionData:
    """Container for all extraction data"""
    taxonomy: Dict[str, Any]
    speaker_schema: Dict[str, Any]
    entity_schema: Dict[str, Any]
    interviews: Dict[str, Any]  # interview_id -> interview data
    extraction_results: Optional[Dict[str, Any]] = None
    
    def get_code_by_id(self, code_id: str) -> Optional[Dict]:
        """Get code details by ID"""
        for code in self.taxonomy.get('codes', []):
            if code['id'] == code_id:
                return code
        return None
    
    def get_codes_hierarchy(self) -> Dict[str, List[Dict]]:
        """Get codes organized by level"""
        hierarchy = {}
        for code in self.taxonomy.get('codes', []):
            level = code.get('level', 0)
            if level not in hierarchy:
                hierarchy[level] = []
            hierarchy[level].append(code)
        return hierarchy
    
    def get_all_quotes(self) -> List[Dict]:
        """Get all quotes from all interviews"""
        all_quotes = []
        for interview_id, interview in self.interviews.items():
            for quote in interview.get('quotes', []):
                quote['interview_id'] = interview_id
                all_quotes.append(quote)
        return all_quotes
    
    def get_quotes_by_code(self, code_id: str) -> List[Dict]:
        """Get all quotes for a specific code"""
        quotes = []
        for quote in self.get_all_quotes():
            if code_id in quote.get('code_ids', []):
                quotes.append(quote)
        return quotes
    
    def get_code_frequency(self) -> pd.DataFrame:
        """Get frequency of each code usage"""
        code_counts = {}
        for quote in self.get_all_quotes():
            for code_id in quote.get('code_ids', []):
                code_counts[code_id] = code_counts.get(code_id, 0) + 1
        
        # Add code names
        data = []
        for code_id, count in code_counts.items():
            code = self.get_code_by_id(code_id)
            data.append({
                'Code ID': code_id,
                'Code Name': code['name'] if code else 'Unknown',
                'Level': code.get('level', 0) if code else 0,
                'Frequency': count
            })
        
        return pd.DataFrame(data).sort_values('Frequency', ascending=False)
    
    def get_speaker_summary(self) -> pd.DataFrame:
        """Get summary of speakers across interviews"""
        speakers = []
        for interview_id, interview in self.interviews.items():
            for speaker in interview.get('speakers', []):
                speaker_data = speaker.copy()
                speaker_data['interview'] = interview_id
                speakers.append(speaker_data)
        return pd.DataFrame(speakers)
    
    def get_entity_summary(self) -> pd.DataFrame:
        """Get summary of entities across interviews"""
        entities = []
        for interview_id, interview in self.interviews.items():
            for entity in interview.get('interview_entities', []):
                entity_data = entity.copy()
                entity_data['interview'] = interview_id
                entities.append(entity_data)
        return pd.DataFrame(entities)


class DataLoader:
    """Load extraction results from output directory"""
    
    def __init__(self, output_dir: str = "output_production"):
        self.output_dir = Path(output_dir)
        
    def load_all_data(self) -> ExtractionData:
        """Load all extraction data"""
        # Load schemas
        taxonomy = self._load_json('taxonomy.json')
        speaker_schema = self._load_json('speaker_schema.json')
        entity_schema = self._load_json('entity_schema.json')
        
        # Load interviews
        interviews = {}
        interviews_dir = self.output_dir / 'interviews'
        if interviews_dir.exists():
            for interview_file in interviews_dir.glob('*.json'):
                interview_data = self._load_json(f'interviews/{interview_file.name}')
                interview_id = interview_file.stem
                interviews[interview_id] = interview_data
        
        # Load complete results if available
        extraction_results = None
        if (self.output_dir / 'extraction_results.json').exists():
            extraction_results = self._load_json('extraction_results.json')
        
        return ExtractionData(
            taxonomy=taxonomy,
            speaker_schema=speaker_schema,
            entity_schema=entity_schema,
            interviews=interviews,
            extraction_results=extraction_results
        )
    
    def _load_json(self, filename: str) -> Dict:
        """Load JSON file from output directory"""
        filepath = self.output_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
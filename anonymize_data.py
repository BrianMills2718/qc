#!/usr/bin/env python3
"""
Script to anonymize names in qualitative coding output files.
Creates anonymized copies of all CSV files that contain personal names.
"""

import os
import csv
import json
import shutil
from pathlib import Path
import re
from typing import Dict, Set, List, Tuple

class DataAnonymizer:
    def __init__(self, output_dir: str, anonymized_dir: str):
        self.output_dir = Path(output_dir)
        self.anonymized_dir = Path(anonymized_dir)
        self.name_mapping = {}
        self.role_mapping = {}
        self.speaker_counter = 1
        self.role_counter = 1
        
    def create_anonymized_directory(self):
        """Create directory structure for anonymized data."""
        if self.anonymized_dir.exists():
            shutil.rmtree(self.anonymized_dir)
        self.anonymized_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_names_from_quotes(self, filepath: Path) -> Set[Tuple[str, str]]:
        """Extract speaker names and roles from quote files."""
        names_roles = set()
        
        if filepath.suffix == '.csv':
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'speaker_name' in row and row['speaker_name']:
                        name = row['speaker_name'].strip()
                        role = row.get('speaker_role', '').strip()
                        if name and name != 'Unknown':
                            names_roles.add((name, role))
                    
                    # Also check text field for inline names
                    if 'text' in row:
                        # Pattern to match "Name: quote" format
                        matches = re.findall(r'([A-Z][a-z]+ [A-Z][a-z]+):', row['text'])
                        for match in matches:
                            names_roles.add((match, ''))
                            
        return names_roles
    
    def build_name_mappings(self):
        """Build mappings for all names and roles found in the data."""
        print("Scanning for names and roles...")
        
        # Scan all CSV files
        for filepath in self.output_dir.rglob('*.csv'):
            if 'quote' in filepath.name.lower():
                names_roles = self.extract_names_from_quotes(filepath)
                for name, role in names_roles:
                    if name not in self.name_mapping:
                        self.name_mapping[name] = f"SPEAKER_{self.speaker_counter:03d}"
                        self.speaker_counter += 1
                    
                    if role and role not in self.role_mapping:
                        self.role_mapping[role] = f"ROLE_{self.role_counter:03d}"
                        self.role_counter += 1
        
        print(f"Found {len(self.name_mapping)} unique names and {len(self.role_mapping)} unique roles")
        
    def anonymize_csv_file(self, input_path: Path, output_path: Path):
        """Anonymize a single CSV file."""
        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            
            rows = []
            for row in reader:
                # Anonymize speaker_name field
                if 'speaker_name' in row and row['speaker_name'] in self.name_mapping:
                    row['speaker_name'] = self.name_mapping[row['speaker_name']]
                
                # Anonymize speaker_role field
                if 'speaker_role' in row and row['speaker_role'] in self.role_mapping:
                    row['speaker_role'] = self.role_mapping[row['speaker_role']]
                
                # Anonymize names in text fields
                if 'text' in row:
                    text = row['text']
                    for name, anon_id in self.name_mapping.items():
                        text = text.replace(f"{name}:", f"{anon_id}:")
                        text = text.replace(f'"{name}', f'"{anon_id}')
                        text = text.replace(f"'{name}", f"'{anon_id}")
                    row['text'] = text
                
                # Anonymize exemplar quotes
                for i in range(1, 10):
                    quote_field = f'exemplar_quote_{i}'
                    if quote_field in row:
                        text = row[quote_field]
                        for name, anon_id in self.name_mapping.items():
                            text = text.replace(name, anon_id)
                        row[quote_field] = text
                
                rows.append(row)
        
        # Write anonymized file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    def anonymize_json_file(self, input_path: Path, output_path: Path):
        """Anonymize a single JSON file."""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Recursively anonymize JSON data
        def anonymize_dict(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ['speaker_name', 'speaker'] and value in self.name_mapping:
                        obj[key] = self.name_mapping[value]
                    elif key in ['speaker_role', 'role'] and value in self.role_mapping:
                        obj[key] = self.role_mapping[value]
                    elif key == 'text' and isinstance(value, str):
                        for name, anon_id in self.name_mapping.items():
                            value = value.replace(name, anon_id)
                        obj[key] = value
                    else:
                        anonymize_dict(value)
            elif isinstance(obj, list):
                for item in obj:
                    anonymize_dict(item)
        
        anonymize_dict(data)
        
        # Write anonymized file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def save_mapping_file(self):
        """Save the name/role mappings for reference."""
        mapping_data = {
            'name_mapping': self.name_mapping,
            'role_mapping': self.role_mapping,
            'statistics': {
                'total_names': len(self.name_mapping),
                'total_roles': len(self.role_mapping)
            }
        }
        
        mapping_file = self.anonymized_dir / 'anonymization_mapping.json'
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, indent=2)
        
        print(f"Saved mapping file to {mapping_file}")
    
    def anonymize_all_files(self):
        """Anonymize all relevant files in the output directory."""
        self.create_anonymized_directory()
        self.build_name_mappings()
        
        # Process all files
        for input_path in self.output_dir.rglob('*'):
            if input_path.is_file():
                relative_path = input_path.relative_to(self.output_dir)
                output_path = self.anonymized_dir / relative_path
                
                if input_path.suffix == '.csv':
                    print(f"Anonymizing CSV: {relative_path}")
                    self.anonymize_csv_file(input_path, output_path)
                elif input_path.suffix == '.json':
                    print(f"Anonymizing JSON: {relative_path}")
                    self.anonymize_json_file(input_path, output_path)
                elif input_path.suffix == '.txt':
                    # Copy text files as-is (they don't contain names)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(input_path, output_path)
        
        self.save_mapping_file()
        print(f"\nAnonymization complete! Files saved to: {self.anonymized_dir}")


def main():
    """Main function to run the anonymization process."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Anonymize qualitative coding output files')
    parser.add_argument('--input', default='output', help='Input directory containing original files')
    parser.add_argument('--output', default='output_anonymized', help='Output directory for anonymized files')
    
    args = parser.parse_args()
    
    anonymizer = DataAnonymizer(args.input, args.output)
    anonymizer.anonymize_all_files()


if __name__ == '__main__':
    main()
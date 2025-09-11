"""
Real Frequency-Based Analysis - Fixed Implementation
Loads actual participant data from JSON files and counts real frequencies.
"""

import json
import glob
import time
from typing import Dict, List, Tuple, Any
from collections import defaultdict, Counter
from dataclasses import dataclass
import pandas as pd
from pathlib import Path


@dataclass
class RealFrequencyChain:
    """A code chain with actual frequency counts from real data."""
    sequence: List[str]
    frequency: int
    participants: List[str]
    evidence_relationships: List[Dict]
    sequence_str: str
    
    def __post_init__(self):
        if not self.sequence_str:
            self.sequence_str = " → ".join(self.sequence)


@dataclass
class RealFrequencyPattern:
    """A co-occurrence pattern with real frequency metrics."""
    pattern_type: str
    elements: Tuple[str, ...]
    frequency: int
    participants: List[str]
    context: str


class RealFrequencyAnalyzer:
    """Analyzes qualitative coding patterns using actual frequency counting from JSON data."""
    
    def __init__(self, json_data_path: str = "end_to_end_results", scale_config: Dict[str, int] = None):
        """
        Initialize with path to JSON data and scale configuration.
        
        Args:
            json_data_path: Path to directory containing interview JSON files
            scale_config: Dict mapping data size ranges to top-N values
        """
        self.json_data_path = json_data_path
        self.scale_config = scale_config or {
            "small": 5,      # 2-10 interviews  
            "medium": 10,    # 10-25 interviews
            "large": 15,     # 25-50 interviews
            "xlarge": 20     # 50+ interviews
        }
        self.all_relationships = []
        self.all_entities = []
        self.participants = set()
        self.processing_times = {}
        
    def load_all_interview_data(self) -> Dict[str, Any]:
        """Load all interview data from JSON files."""
        start_time = time.time()
        
        # Find all JSON data files
        json_pattern = f"{self.json_data_path}/**/*_data.json"
        json_files = glob.glob(json_pattern, recursive=True)
        
        print(f"Found {len(json_files)} JSON data files")
        
        all_data = {
            'interviews': [],
            'total_entities': 0,
            'total_relationships': 0,
            'total_codes': 0
        }
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    interview_data = json.load(f)
                
                all_data['interviews'].append(interview_data)
                all_data['total_entities'] += interview_data.get('total_entities', 0)
                all_data['total_relationships'] += interview_data.get('total_relationships', 0)
                all_data['total_codes'] += interview_data.get('total_codes', 0)
                
                # Collect all relationships and entities
                self.all_relationships.extend(interview_data.get('relationships', []))
                self.all_entities.extend(interview_data.get('entities', []))
                
                # Track participants
                for entity in interview_data.get('entities', []):
                    if entity.get('type') == 'Person':
                        self.participants.add(entity.get('name', ''))
                
                print(f"Loaded: {interview_data.get('interview_name', json_file)}")
                print(f"  - Entities: {interview_data.get('total_entities', 0)}")
                print(f"  - Relationships: {interview_data.get('total_relationships', 0)}")
                
            except Exception as e:
                # FAIL-FAST: Don't continue with incomplete data
                print(f"Error loading {json_file}: {e}")
                raise Exception(f"Failed to load required data file {json_file}: {e}") from e
        
        load_time = time.time() - start_time
        self.processing_times['data_loading'] = load_time
        
        print(f"\n>> TOTAL DATA LOADED:")
        print(f"  - Interviews: {len(all_data['interviews'])}")
        print(f"  - Entities: {all_data['total_entities']}")
        print(f"  - Relationships: {all_data['total_relationships']}")
        print(f"  - Participants: {len(self.participants)}")
        print(f"  - Load Time: {load_time:.2f} seconds")
        
        return all_data
    
    def identify_person_entities(self) -> List[str]:
        """Identify all person entities from the data."""
        persons = []
        for entity in self.all_entities:
            if entity.get('type') == 'Person':
                persons.append(entity.get('name', ''))
        return list(set(persons))  # Remove duplicates
    
    def identify_code_entities(self) -> List[str]:
        """Identify all code-like entities (methods, activities, concepts)."""
        codes = []
        code_types = ['Method_Tool', 'Activity', 'Code', 'Concept', 'Topic']
        
        for entity in self.all_entities:
            if entity.get('type') in code_types:
                codes.append(entity.get('name', ''))
        
        # Also look for codes in relationships
        for rel in self.all_relationships:
            target = rel.get('target', '')
            # If target is not a person, it might be a code
            if target and not any(target == person for person in self.participants):
                codes.append(target)
        
        return list(set(codes))  # Remove duplicates
    
    def count_real_person_code_frequencies(self) -> Dict[Tuple[str, str], int]:
        """Count actual frequencies of person-code associations."""
        start_time = time.time()
        
        person_code_counts = defaultdict(int)
        persons = self.identify_person_entities()
        codes = self.identify_code_entities()
        
        print(f"\n>> COUNTING REAL FREQUENCIES:")
        print(f"  - Persons identified: {len(persons)}")
        print(f"  - Codes identified: {len(codes)}")
        print(f"  - Relationships to analyze: {len(self.all_relationships)}")
        
        for rel in self.all_relationships:
            source = rel.get('source', '')
            target = rel.get('target', '')
            relationship_type = rel.get('relationship', '')
            
            # Count person → code relationships
            if source in persons and (target in codes or target not in persons):
                person_code_counts[(source, target)] += 1
            
            # Also count reverse: code → person relationships  
            elif target in persons and (source in codes or source not in persons):
                person_code_counts[(target, source)] += 1
        
        count_time = time.time() - start_time
        self.processing_times['frequency_counting'] = count_time
        
        print(f"  - Unique person-code pairs found: {len(person_code_counts)}")
        print(f"  - Counting time: {count_time:.2f} seconds")
        
        return dict(person_code_counts)
    
    def extract_real_code_chains(self) -> List[RealFrequencyChain]:
        """Extract code chains by analyzing person-code relationship patterns."""
        start_time = time.time()
        
        # Group relationships by person to find sequences
        person_relationships = defaultdict(list)
        persons = self.identify_person_entities()
        
        for rel in self.all_relationships:
            source = rel.get('source', '')
            target = rel.get('target', '')
            
            if source in persons:
                person_relationships[source].append({
                    'target': target,
                    'relationship': rel.get('relationship', ''),
                    'properties': rel.get('properties', {}),
                    'raw_rel': rel
                })
        
        # Find chains within each person's relationships
        chains = []
        chain_counter = Counter()
        chain_evidence = defaultdict(list)
        chain_relationships = defaultdict(list)
        
        for person, relationships in person_relationships.items():
            # Extract targets (codes/methods/activities)
            targets = [rel['target'] for rel in relationships]
            
            # Find 2-4 step sequences
            for length in range(2, min(5, len(targets) + 1)):
                for i in range(len(targets) - length + 1):
                    sequence = targets[i:i+length]
                    
                    # Skip sequences with duplicates (not meaningful chains)
                    if len(set(sequence)) == len(sequence):
                        sequence_str = " → ".join(sequence)
                        chain_counter[sequence_str] += 1
                        chain_evidence[sequence_str].append(person)
                        chain_relationships[sequence_str].extend([
                            rel['raw_rel'] for rel in relationships[i:i+length]
                        ])
        
        # Convert to RealFrequencyChain objects
        for sequence_str, frequency in chain_counter.items():
            sequence = sequence_str.split(" → ")
            chains.append(RealFrequencyChain(
                sequence=sequence,
                frequency=frequency,
                participants=list(set(chain_evidence[sequence_str])),
                evidence_relationships=chain_relationships[sequence_str],
                sequence_str=sequence_str
            ))
        
        chains_time = time.time() - start_time
        self.processing_times['chain_extraction'] = chains_time
        
        print(f"\n>> CHAIN EXTRACTION COMPLETE:")
        print(f"  - Total chains found: {len(chains)}")
        print(f"  - Extraction time: {chains_time:.2f} seconds")
        
        return sorted(chains, key=lambda x: x.frequency, reverse=True)
    
    def extract_real_cooccurrence_patterns(self) -> List[RealFrequencyPattern]:
        """Extract real co-occurrence patterns from participant data."""
        start_time = time.time()
        
        # Group codes by person to find co-occurrences
        person_codes = defaultdict(set)
        persons = self.identify_person_entities()
        
        for rel in self.all_relationships:
            source = rel.get('source', '')
            target = rel.get('target', '')
            
            if source in persons:
                person_codes[source].add(target)
            elif target in persons:
                person_codes[target].add(source)
        
        # Find co-occurrences
        cooccur_counter = Counter()
        cooccur_evidence = defaultdict(list)
        
        for person, codes in person_codes.items():
            codes_list = list(codes)
            # All pairs of codes that co-occur in same person
            for i in range(len(codes_list)):
                for j in range(i + 1, len(codes_list)):
                    pair = tuple(sorted([codes_list[i], codes_list[j]]))
                    cooccur_counter[pair] += 1
                    cooccur_evidence[pair].append(person)
        
        patterns = []
        for pair, frequency in cooccur_counter.items():
            patterns.append(RealFrequencyPattern(
                pattern_type="co-occurrence",
                elements=pair,
                frequency=frequency,
                participants=cooccur_evidence[pair],
                context=f"Codes appear together in {frequency} participants"
            ))
        
        cooccur_time = time.time() - start_time
        self.processing_times['cooccurrence_extraction'] = cooccur_time
        
        print(f"\n>> CO-OCCURRENCE EXTRACTION COMPLETE:")
        print(f"  - Co-occurrence patterns found: {len(patterns)}")
        print(f"  - Extraction time: {cooccur_time:.2f} seconds")
        
        return sorted(patterns, key=lambda x: x.frequency, reverse=True)
    
    def determine_scale(self, participant_count: int) -> str:
        """Determine scale category based on participant count."""
        if participant_count <= 10:
            return "small"
        elif participant_count <= 25:
            return "medium" 
        elif participant_count <= 50:
            return "large"
        else:
            return "xlarge"
    
    def get_top_n_for_scale(self, participant_count: int) -> int:
        """Get appropriate top-N value for participant count."""
        scale = self.determine_scale(participant_count)
        return self.scale_config[scale]
    
    def generate_real_frequency_report(self, max_chains: int = None) -> Dict[str, Any]:
        """Generate a complete frequency-based analysis report using real data."""
        total_start_time = time.time()
        
        print(">> STARTING REAL FREQUENCY ANALYSIS")
        print("=" * 50)
        
        # Load all data
        interview_data = self.load_all_interview_data()
        participant_count = len(self.participants)
        
        if max_chains is None:
            max_chains = self.get_top_n_for_scale(participant_count)
        
        # Extract patterns
        person_code_frequencies = self.count_real_person_code_frequencies()
        chains = self.extract_real_code_chains()
        cooccurrences = self.extract_real_cooccurrence_patterns()
        
        # Filter to top N
        top_chains = chains[:max_chains]
        top_cooccurrences = cooccurrences[:max_chains]
        
        total_time = time.time() - total_start_time
        self.processing_times['total_analysis'] = total_time
        
        report = {
            'metadata': {
                'participant_count': participant_count,
                'participant_names': list(self.participants),
                'scale_category': self.determine_scale(participant_count),
                'max_chains_shown': max_chains,
                'total_chains_found': len(chains),
                'total_cooccurrences_found': len(cooccurrences),
                'total_person_code_pairs': len(person_code_frequencies),
                'processing_times': self.processing_times,
                'data_summary': {
                    'interviews_processed': len(interview_data['interviews']),
                    'total_entities': interview_data['total_entities'],
                    'total_relationships': interview_data['total_relationships']
                }
            },
            'top_chains': [
                {
                    'sequence': chain.sequence_str,
                    'frequency': chain.frequency,
                    'participant_count': len(chain.participants),
                    'participants': chain.participants,
                    'evidence_relationships': len(chain.evidence_relationships)
                }
                for chain in top_chains
            ],
            'top_cooccurrences': [
                {
                    'pattern': f"{pattern.elements[0]} + {pattern.elements[1]}",
                    'frequency': pattern.frequency,
                    'participants': pattern.participants,
                    'context': pattern.context
                }
                for pattern in top_cooccurrences
            ],
            'person_code_frequencies': [
                {
                    'person': person,
                    'code': code,
                    'frequency': freq
                }
                for (person, code), freq in sorted(person_code_frequencies.items(), 
                                                  key=lambda x: x[1], reverse=True)  # All entries
            ]
        }
        
        print(f"\n>> ANALYSIS COMPLETE!")
        print(f"  - Total time: {total_time:.2f} seconds")
        print(f"  - Participants analyzed: {participant_count}")
        print(f"  - Top chains found: {len(top_chains)}")
        print(f"  - Co-occurrences found: {len(top_cooccurrences)}")
        
        return report
    
    def export_real_analysis_to_csv(self, report: Dict[str, Any], output_prefix: str = "real_frequency_analysis"):
        """Export real frequency analysis to CSV files."""
        
        # Export top chains
        chains_df = pd.DataFrame(report['top_chains'])
        chains_file = f"{output_prefix}_chains.csv"
        chains_df.to_csv(chains_file, index=False)
        
        # Export co-occurrences  
        cooccur_df = pd.DataFrame(report['top_cooccurrences'])
        cooccur_file = f"{output_prefix}_cooccurrences.csv"
        cooccur_df.to_csv(cooccur_file, index=False)
        
        # Export person-code frequencies
        person_code_df = pd.DataFrame(report['person_code_frequencies'])
        person_code_file = f"{output_prefix}_person_codes.csv"
        person_code_df.to_csv(person_code_file, index=False)
        
        # Export metadata
        metadata_df = pd.DataFrame([report['metadata']])
        metadata_file = f"{output_prefix}_metadata.csv"
        metadata_df.to_csv(metadata_file, index=False)
        
        return {
            'chains_file': chains_file,
            'cooccurrences_file': cooccur_file,
            'person_codes_file': person_code_file,
            'metadata_file': metadata_file
        }


def main():
    """Run real frequency analysis with actual data."""
    
    print(">> REAL FREQUENCY-BASED ANALYSIS")
    print("Loading actual participant data from JSON files...")
    print()
    
    # Initialize analyzer
    analyzer = RealFrequencyAnalyzer()
    
    # Generate report
    report = analyzer.generate_real_frequency_report()
    
    # Export results
    files = analyzer.export_real_analysis_to_csv(report, "real_frequency_analysis")
    
    # Show results
    print(f"\n>> FINAL RESULTS:")
    print(f"  - Participants: {report['metadata']['participant_count']}")
    print(f"  - Scale: {report['metadata']['scale_category']}")
    print(f"  - Processing time: {report['metadata']['processing_times']['total_analysis']:.2f}s")
    
    print(f"\n>> Top 3 Most Frequent Code Chains (REAL DATA):")
    for i, chain in enumerate(report['top_chains'][:3], 1):
        # Replace arrow character for console compatibility
        sequence_str = chain['sequence'].replace('→', '->')
        print(f"  {i}. {sequence_str}")
        print(f"     Frequency: {chain['frequency']} | Participants: {chain['participant_count']}")
        print(f"     Evidence: {chain['participants']}")
    
    print(f"\n>> Top 3 Co-occurrences (REAL DATA):")
    for i, cooccur in enumerate(report['top_cooccurrences'][:3], 1):
        print(f"  {i}. {cooccur['pattern']}")
        print(f"     Frequency: {cooccur['frequency']} | Participants: {len(cooccur['participants'])}")
    
    print(f"\n>> Files created: {list(files.values())}")


if __name__ == "__main__":
    main()
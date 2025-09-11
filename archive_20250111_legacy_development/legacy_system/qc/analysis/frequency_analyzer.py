"""
Frequency-based analysis for qualitative coding patterns.
Focuses on simple, scalable frequency counting rather than complex statistical measures.
"""

from typing import Dict, List, Tuple, Any
from collections import defaultdict, Counter
import pandas as pd
from dataclasses import dataclass
import json
import logging

from ..utils.error_handler import ProcessingError

logger = logging.getLogger(__name__)


@dataclass
class FrequencyChain:
    """A code chain with frequency-based metrics."""
    sequence: List[str]
    frequency: int
    evidence_sources: List[str]
    sample_quotes: List[str]
    sequence_str: str
    
    def __post_init__(self):
        if not self.sequence_str:
            self.sequence_str = " → ".join(self.sequence)


@dataclass 
class FrequencyPattern:
    """A co-occurrence or other pattern with frequency metrics."""
    pattern_type: str  # "co-occurrence", "division-code", "seniority-code"
    elements: Tuple[str, ...]
    frequency: int
    evidence_sources: List[str]
    context: str


class FrequencyAnalyzer:
    """Analyzes qualitative coding patterns using simple frequency-based methods."""
    
    def __init__(self, scale_config: Dict[str, int] = None):
        """
        Initialize with scale-aware configuration.
        
        Args:
            scale_config: Dict mapping data size ranges to top-N values
        """
        self.scale_config = scale_config or {
            "small": 5,      # 2-10 interviews  
            "medium": 10,    # 10-25 interviews
            "large": 15,     # 25-50 interviews
            "xlarge": 20     # 50+ interviews
        }
        
    def determine_scale(self, data_size: int) -> str:
        """Determine scale category based on data size."""
        if data_size <= 10:
            return "small"
        elif data_size <= 25:
            return "medium" 
        elif data_size <= 50:
            return "large"
        else:
            return "xlarge"
            
    def get_top_n_for_scale(self, data_size: int) -> int:
        """Get appropriate top-N value for data size."""
        scale = self.determine_scale(data_size)
        return self.scale_config[scale]
    
    def extract_code_chains_from_existing_analysis(self, chains_csv_path: str) -> List[FrequencyChain]:
        """
        Extract code chains from existing analysis CSV rather than raw data.
        This works better with our current data structure.
        
        Args:
            chains_csv_path: Path to existing code_chains_analysis.csv
            
        Returns:
            List of FrequencyChain objects
        """
        try:
            df = pd.read_csv(chains_csv_path)
            chains = []
            
            for _, row in df.iterrows():
                sequence_parts = row['Sequence'].split(' → ')
                # Remove self-loops and invalid chains
                if len(sequence_parts) > 1 and len(set(sequence_parts)) == len(sequence_parts):
                    
                    # Map strength to frequency for now
                    strength_to_freq = {'Strong': 3, 'Medium': 2, 'Weak': 1}
                    frequency = strength_to_freq.get(row.get('Strength', 'Medium'), 2)
                    
                    chains.append(FrequencyChain(
                        sequence=sequence_parts,
                        frequency=frequency,
                        evidence_sources=[row.get('Evidence', 'Manual Analysis')],
                        sample_quotes=[row.get('Evidence', '')[:200]],  # Truncate long evidence
                        sequence_str=row['Sequence']
                    ))
            
            return sorted(chains, key=lambda x: x.frequency, reverse=True)
            
        except Exception as e:
            logger.error(f"Could not load existing chains: {e}")
            raise ProcessingError(f"Could not load existing chains: {e}") from e
    
    def extract_cooccurrence_patterns(self, quote_data: List[Dict]) -> List[FrequencyPattern]:
        """Extract code co-occurrence patterns."""
        # Group by speaker/interview to find co-occurrences
        speaker_codes = defaultdict(set)
        
        for quote in quote_data:
            speaker = quote.get('Speaker', quote.get('speaker', ''))
            code = quote.get('Code_Association', quote.get('code', ''))
            if speaker and code:
                speaker_codes[speaker].add(code)
        
        # Find co-occurrences
        cooccur_counter = Counter()
        cooccur_evidence = defaultdict(list)
        
        for speaker, codes in speaker_codes.items():
            codes_list = list(codes)
            # All pairs of codes that co-occur in same speaker
            for i in range(len(codes_list)):
                for j in range(i + 1, len(codes_list)):
                    pair = tuple(sorted([codes_list[i], codes_list[j]]))
                    cooccur_counter[pair] += 1
                    cooccur_evidence[pair].append(speaker)
        
        patterns = []
        for pair, frequency in cooccur_counter.items():
            patterns.append(FrequencyPattern(
                pattern_type="co-occurrence",
                elements=pair,
                frequency=frequency,
                evidence_sources=cooccur_evidence[pair],
                context=f"Codes appear together in {frequency} speakers"
            ))
        
        return sorted(patterns, key=lambda x: x.frequency, reverse=True)
    
    def generate_frequency_report(self, 
                                quote_data: List[Dict],
                                participant_data: List[Dict] = None,
                                max_chains: int = None,
                                chains_csv_path: str = "code_chains_analysis.csv") -> Dict[str, Any]:
        """
        Generate a complete frequency-based analysis report.
        
        Args:
            quote_data: Quote/code data
            participant_data: Participant demographic data
            max_chains: Override for max chains to show (if None, uses scale-based)
            chains_csv_path: Path to existing chains analysis CSV
            
        Returns:
            Dict with analysis results
        """
        data_size = len(set(q.get('Speaker', q.get('speaker', '')) for q in quote_data))
        
        if max_chains is None:
            max_chains = self.get_top_n_for_scale(data_size)
        
        # Extract patterns - try existing analysis first
        chains = self.extract_code_chains_from_existing_analysis(chains_csv_path)
        cooccurrence = self.extract_cooccurrence_patterns(quote_data)
        
        # Filter to top N
        top_chains = chains[:max_chains]
        top_cooccurrence = cooccurrence[:max_chains]
        
        report = {
            'metadata': {
                'data_size': data_size,
                'scale_category': self.determine_scale(data_size),
                'max_chains_shown': max_chains,
                'total_chains_found': len(chains),
                'total_cooccurrences_found': len(cooccurrence)
            },
            'top_chains': [
                {
                    'sequence': chain.sequence_str,
                    'frequency': chain.frequency,
                    'evidence_count': len(chain.evidence_sources),
                    'evidence_sources': chain.evidence_sources,
                    'sample_quotes': chain.sample_quotes
                }
                for chain in top_chains
            ],
            'top_cooccurrences': [
                {
                    'pattern': f"{pattern.elements[0]} + {pattern.elements[1]}",
                    'frequency': pattern.frequency,
                    'evidence_sources': pattern.evidence_sources,
                    'context': pattern.context
                }
                for pattern in top_cooccurrence
            ]
        }
        
        return report
    
    def export_to_csv(self, report: Dict[str, Any], output_prefix: str = "frequency_analysis"):
        """Export frequency analysis to CSV files."""
        
        # Export top chains
        chains_df = pd.DataFrame(report['top_chains'])
        chains_df.to_csv(f"{output_prefix}_top_chains.csv", index=False)
        
        # Export co-occurrences  
        cooccur_df = pd.DataFrame(report['top_cooccurrences'])
        cooccur_df.to_csv(f"{output_prefix}_cooccurrences.csv", index=False)
        
        # Export metadata
        metadata_df = pd.DataFrame([report['metadata']])
        metadata_df.to_csv(f"{output_prefix}_metadata.csv", index=False)
        
        return {
            'chains_file': f"{output_prefix}_top_chains.csv",
            'cooccurrences_file': f"{output_prefix}_cooccurrences.csv", 
            'metadata_file': f"{output_prefix}_metadata.csv"
        }


def load_quote_data_from_csv(csv_path: str) -> List[Dict]:
    """Load quote data from CSV file."""
    df = pd.read_csv(csv_path)
    return df.to_dict('records')


def main():
    """Example usage of frequency analyzer."""
    
    # Load existing data
    quote_data = load_quote_data_from_csv("quote_evidence_database.csv")
    
    # Initialize analyzer
    analyzer = FrequencyAnalyzer()
    
    # Generate report using existing chains analysis
    report = analyzer.generate_frequency_report(
        quote_data, 
        chains_csv_path="code_chains_analysis.csv"
    )
    
    # Export results
    files = analyzer.export_to_csv(report, "frequency_analysis_updated")
    
    print(f"Analysis complete. Data size: {report['metadata']['data_size']}")
    print(f"Scale category: {report['metadata']['scale_category']}")
    print(f"Top chains shown: {report['metadata']['max_chains_shown']}")
    print(f"Files created: {list(files.values())}")
    
    # Print top 3 chains (fix Unicode issue)
    print("\nTop 3 Most Frequent Code Chains:")
    for i, chain in enumerate(report['top_chains'][:3], 1):
        # Replace arrow character for console compatibility
        sequence_str = chain['sequence'].replace('→', '->')
        print(f"{i}. {sequence_str} (frequency: {chain['frequency']})")


if __name__ == "__main__":
    main()
"""
Division-Level Insights Analyzer
Extracts division-specific patterns from real frequency data.
"""

import pandas as pd
from collections import defaultdict
from typing import Dict, List, Any


class DivisionInsightsAnalyzer:
    """Analyzes division-level patterns from real frequency data."""
    
    def __init__(self, person_codes_file: str = "real_frequency_analysis_person_codes.csv"):
        """Initialize with person-codes data file."""
        self.person_codes_file = person_codes_file
        self.person_codes_df = None
        self.division_mapping = {
            # From original participant_demographics.csv
            "Caroline Johnston": "Quantitative Methods",
            "Shannon Walsh": "AI Research", 
            "Lynn Karoly": "Domestic Policy",
            "Todd Helmus": "National Security",
            "Kandice Kapinos": "Methods Center for Causal Inference",
            "Alice Huguet": "Methods Division",
            # Inferred from data patterns
            "Brian Mills": "Technical Services",
            "Brian Jackson": "AI/Social Media Research",
            "Caitlin McCulloch": "AI/Social Media Research", 
            "Sean Robson": "Operations Research",
            "Ryan Brown": "Operations Research"
        }
        
    def load_data(self):
        """Load person-codes frequency data."""
        try:
            self.person_codes_df = pd.read_csv(self.person_codes_file)
            print(f"Loaded {len(self.person_codes_df)} person-code associations")
            return True
        except FileNotFoundError:
            print(f"Error: Could not find {self.person_codes_file}")
            return False
    
    def analyze_division_patterns(self) -> Dict[str, Any]:
        """Analyze patterns by division."""
        if self.person_codes_df is None:
            if not self.load_data():
                return {}
        
        # Add division column
        self.person_codes_df['division'] = self.person_codes_df['person'].map(self.division_mapping)
        
        # Group by division
        division_stats = {}
        
        for division in self.person_codes_df['division'].unique():
            if pd.isna(division):
                continue
                
            div_data = self.person_codes_df[self.person_codes_df['division'] == division]
            
            # Calculate division metrics
            total_codes = len(div_data)
            unique_codes = div_data['code'].nunique()
            people_count = div_data['person'].nunique()
            avg_codes_per_person = total_codes / people_count if people_count > 0 else 0
            
            # Top codes for this division
            top_codes = div_data.groupby('code')['frequency'].sum().sort_values(ascending=False).head(5)
            
            # People in this division
            people = div_data['person'].unique().tolist()
            
            division_stats[division] = {
                'people_count': people_count,
                'people': people,
                'total_code_associations': total_codes,
                'unique_codes': unique_codes,
                'avg_codes_per_person': round(avg_codes_per_person, 1),
                'top_codes': top_codes.to_dict(),
                'specialization_index': round(unique_codes / total_codes, 2) if total_codes > 0 else 0
            }
        
        return division_stats
    
    def identify_division_characteristics(self, division_stats: Dict[str, Any]) -> Dict[str, str]:
        """Identify key characteristics of each division."""
        characteristics = {}
        
        for division, stats in division_stats.items():
            top_codes = list(stats['top_codes'].keys())
            people = stats['people']
            
            # Analyze division based on top codes and patterns
            if division == "Quantitative Methods":
                characteristics[division] = f"Mathematical modeling specialists. {stats['people_count']} person with {stats['unique_codes']} different methods including mathematical optimization and simulation."
                
            elif division == "AI Research":
                characteristics[division] = f"Mixed-methods AI research. {stats['people_count']} person combining qualitative data collection with quantitative analysis for AI applications."
                
            elif division == "Domestic Policy":
                characteristics[division] = f"Policy research focus. {stats['people_count']} person specializing in domestic policy, early childhood, and family programs with strong RAND institutional connection."
                
            elif division == "AI/Social Media Research":
                characteristics[division] = f"AI-powered social media analysis. {stats['people_count']} people working on AI applications for social media posts and content analysis."
                
            elif division == "Technical Services":
                characteristics[division] = f"Research support services. {stats['people_count']} person focused on transcription and technical research support activities."
                
            else:
                # Generic characterization
                top_code = top_codes[0] if top_codes else "various methods"
                characteristics[division] = f"Specialized research unit. {stats['people_count']} people with focus on {top_code} and related methods."
        
        return characteristics
    
    def generate_division_insights_report(self) -> Dict[str, Any]:
        """Generate comprehensive division-level insights report."""
        print(">> ANALYZING DIVISION-LEVEL PATTERNS")
        print("=" * 50)
        
        # Analyze patterns
        division_stats = self.analyze_division_patterns()
        characteristics = self.identify_division_characteristics(division_stats)
        
        # Calculate cross-division metrics
        total_people = sum(stats['people_count'] for stats in division_stats.values())
        total_divisions = len(division_stats)
        avg_people_per_division = total_people / total_divisions if total_divisions > 0 else 0
        
        # Find most/least specialized divisions
        specialization_scores = {div: stats['specialization_index'] for div, stats in division_stats.items()}
        most_specialized = max(specialization_scores.items(), key=lambda x: x[1]) if specialization_scores else ("N/A", 0)
        most_diverse = min(specialization_scores.items(), key=lambda x: x[1]) if specialization_scores else ("N/A", 0)
        
        report = {
            'metadata': {
                'total_divisions': total_divisions,
                'total_people_analyzed': total_people,
                'avg_people_per_division': round(avg_people_per_division, 1),
                'most_specialized_division': most_specialized[0],
                'most_diverse_division': most_diverse[0]
            },
            'division_statistics': division_stats,
            'division_characteristics': characteristics,
            'cross_division_insights': {
                'largest_division': max(division_stats.items(), key=lambda x: x[1]['people_count'])[0],
                'most_method_diverse': max(division_stats.items(), key=lambda x: x[1]['unique_codes'])[0],
                'highest_activity': max(division_stats.items(), key=lambda x: x[1]['total_code_associations'])[0]
            }
        }
        
        return report
    
    def export_division_insights(self, report: Dict[str, Any], output_file: str = "division_insights_analysis.csv"):
        """Export division insights to CSV."""
        
        # Prepare data for CSV export
        division_rows = []
        for division, stats in report['division_statistics'].items():
            division_rows.append({
                'Division': division,
                'People_Count': stats['people_count'],
                'People': '; '.join(stats['people']),
                'Total_Code_Associations': stats['total_code_associations'],
                'Unique_Methods': stats['unique_codes'],
                'Avg_Methods_Per_Person': stats['avg_codes_per_person'],
                'Specialization_Index': stats['specialization_index'],
                'Top_Method': list(stats['top_codes'].keys())[0] if stats['top_codes'] else '',
                'Characteristic': report['division_characteristics'].get(division, '')
            })
        
        # Export to CSV
        df = pd.DataFrame(division_rows)
        df.to_csv(output_file, index=False)
        
        return output_file


def main():
    """Run division insights analysis."""
    
    print(">> DIVISION-LEVEL INSIGHTS ANALYSIS")
    print("Analyzing real frequency data by organizational division...")
    print()
    
    # Initialize analyzer
    analyzer = DivisionInsightsAnalyzer()
    
    # Generate report
    report = analyzer.generate_division_insights_report()
    
    # Export results
    output_file = analyzer.export_division_insights(report)
    
    # Display results
    print(f"\n>> ANALYSIS RESULTS:")
    print(f"  - Divisions analyzed: {report['metadata']['total_divisions']}")
    print(f"  - People analyzed: {report['metadata']['total_people_analyzed']}")
    print(f"  - Most specialized: {report['metadata']['most_specialized_division']}")
    print(f"  - Most diverse: {report['metadata']['most_diverse_division']}")
    
    print(f"\n>> DIVISION CHARACTERISTICS:")
    for division, characteristic in report['division_characteristics'].items():
        print(f"  • {division}: {characteristic}")
    
    print(f"\n>> CROSS-DIVISION INSIGHTS:")
    insights = report['cross_division_insights']
    print(f"  - Largest division: {insights['largest_division']}")
    print(f"  - Most method-diverse: {insights['most_method_diverse']}")
    print(f"  - Highest activity: {insights['highest_activity']}")
    
    print(f"\n>> File created: {output_file}")


if __name__ == "__main__":
    main()
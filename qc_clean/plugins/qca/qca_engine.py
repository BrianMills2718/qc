#!/usr/bin/env python3
"""
QCA Engine - Simplified QCA Analysis Engine

Provides core QCA functionality including calibration, truth table construction,
and basic minimization for the QCA plugin.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class QCAConfiguration:
    """QCA analysis configuration"""
    enable_qca_conversion: bool = True
    default_analysis_method: str = "crisp_set"
    calibration_method: str = "binary"
    truth_table_consistency_threshold: float = 0.8
    truth_table_frequency_threshold: int = 1
    generate_minimization: bool = True
    output_format: str = "standard"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'enable_qca_conversion': self.enable_qca_conversion,
            'default_analysis_method': self.default_analysis_method,
            'calibration_method': self.calibration_method,
            'truth_table_consistency_threshold': self.truth_table_consistency_threshold,
            'truth_table_frequency_threshold': self.truth_table_frequency_threshold,
            'generate_minimization': self.generate_minimization,
            'output_format': self.output_format
        }


@dataclass
class QCAResults:
    """QCA analysis results"""
    truth_table: pd.DataFrame
    necessary_conditions: List[Dict[str, Any]]
    sufficient_conditions: List[Dict[str, Any]]
    minimization_results: Dict[str, Any]
    consistency_scores: Dict[str, float]
    coverage_scores: Dict[str, float]
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)


class QCAEngine:
    """Simplified QCA Analysis Engine"""
    
    def __init__(self, config: QCAConfiguration):
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.QCAEngine")
        self._logger.info(f"QCA Engine initialized with method: {config.default_analysis_method}")
    
    def run_analysis(self, qca_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete QCA analysis pipeline"""
        try:
            self._logger.info("Starting QCA analysis pipeline...")
            
            # Extract data
            case_matrix = qca_data['case_matrix']
            conditions = qca_data['conditions']
            outcomes = qca_data['outcomes']
            
            # Convert to DataFrame
            df = pd.DataFrame(case_matrix)
            df = df.set_index('case_id')
            
            self._logger.info(f"Processing {len(df)} cases with {len(conditions)} conditions and {len(outcomes)} outcomes")
            
            # Build truth table
            truth_table = self._build_truth_table(df, conditions, outcomes)
            
            # Calculate necessity analysis
            necessity_results = self._analyze_necessity(df, conditions, outcomes)
            
            # Calculate sufficiency analysis  
            sufficiency_results = self._analyze_sufficiency(df, conditions, outcomes, truth_table)
            
            # Generate minimization if requested
            minimization_results = {}
            if self.config.generate_minimization:
                minimization_results = self._perform_minimization(truth_table, conditions, outcomes)
            
            # Compile results
            results = {
                'truth_table': truth_table.to_dict('records'),
                'truth_table_df': truth_table,  # Keep DataFrame for internal use
                'necessary_conditions': necessity_results,
                'sufficient_conditions': sufficiency_results,
                'minimization_results': minimization_results,
                'consistency_scores': self._calculate_consistency_scores(df, conditions, outcomes),
                'coverage_scores': self._calculate_coverage_scores(df, conditions, outcomes),
                'analysis_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_cases': len(df),
                    'total_conditions': len(conditions),
                    'total_outcomes': len(outcomes),
                    'analysis_method': self.config.default_analysis_method,
                    'consistency_threshold': self.config.truth_table_consistency_threshold,
                    'frequency_threshold': self.config.truth_table_frequency_threshold
                }
            }
            
            self._logger.info("QCA analysis pipeline completed successfully")
            return results
            
        except Exception as e:
            self._logger.error(f"Error in QCA analysis pipeline: {e}")
            raise
    
    def _build_truth_table(self, df: pd.DataFrame, conditions: List[str], outcomes: List[str]) -> pd.DataFrame:
        """Build QCA truth table"""
        self._logger.info("Building truth table...")
        
        # Group by conditions to create truth table rows
        truth_table_data = []
        
        # Generate all possible combinations of conditions
        from itertools import product
        
        condition_combinations = list(product([0, 1], repeat=len(conditions)))
        
        for combo in condition_combinations:
            # Create filter for this combination
            filters = []
            combo_dict = {}
            
            for i, condition in enumerate(conditions):
                value = combo[i]
                filters.append(df[condition] == value)
                combo_dict[condition] = value
            
            # Find cases matching this combination
            if filters:
                combined_filter = filters[0]
                for f in filters[1:]:
                    combined_filter = combined_filter & f
                
                matching_cases = df[combined_filter]
            else:
                matching_cases = df
            
            # Calculate outcome statistics for this combination
            row_data = combo_dict.copy()
            row_data['frequency'] = len(matching_cases)
            row_data['case_ids'] = list(matching_cases.index)
            
            # For each outcome, calculate consistency
            for outcome in outcomes:
                if len(matching_cases) > 0:
                    consistency = matching_cases[outcome].mean()
                    row_data[f'{outcome}_consistency'] = consistency
                    row_data[f'{outcome}_outcome'] = 1 if consistency >= self.config.truth_table_consistency_threshold else 0
                else:
                    row_data[f'{outcome}_consistency'] = 0.0
                    row_data[f'{outcome}_outcome'] = 0
            
            # Only include rows that meet frequency threshold
            if row_data['frequency'] >= self.config.truth_table_frequency_threshold:
                truth_table_data.append(row_data)
        
        truth_table = pd.DataFrame(truth_table_data)
        self._logger.info(f"Truth table built with {len(truth_table)} rows")
        
        return truth_table
    
    def _analyze_necessity(self, df: pd.DataFrame, conditions: List[str], outcomes: List[str]) -> List[Dict[str, Any]]:
        """Analyze necessary conditions"""
        self._logger.info("Analyzing necessary conditions...")
        
        necessity_results = []
        
        for outcome in outcomes:
            outcome_cases = df[df[outcome] == 1]
            
            if len(outcome_cases) == 0:
                continue
            
            for condition in conditions:
                # Calculate necessity consistency: cases where outcome=1 and condition=1 / cases where outcome=1
                necessity_consistency = outcome_cases[condition].mean()
                
                # Calculate necessity coverage: cases where outcome=1 and condition=1 / cases where condition=1
                condition_cases = df[df[condition] == 1]
                if len(condition_cases) > 0:
                    necessity_coverage = len(outcome_cases[outcome_cases[condition] == 1]) / len(condition_cases)
                else:
                    necessity_coverage = 0.0
                
                necessity_results.append({
                    'condition': condition,
                    'outcome': outcome,
                    'consistency': necessity_consistency,
                    'coverage': necessity_coverage,
                    'is_necessary': necessity_consistency >= 0.9  # Standard threshold
                })
        
        return necessity_results
    
    def _analyze_sufficiency(self, df: pd.DataFrame, conditions: List[str], outcomes: List[str], truth_table: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze sufficient conditions"""
        self._logger.info("Analyzing sufficient conditions...")
        
        sufficiency_results = []
        
        for outcome in outcomes:
            for condition in conditions:
                # Calculate sufficiency consistency: cases where condition=1 and outcome=1 / cases where condition=1
                condition_cases = df[df[condition] == 1]
                
                if len(condition_cases) > 0:
                    sufficiency_consistency = condition_cases[outcome].mean()
                    
                    # Calculate sufficiency coverage: cases where condition=1 and outcome=1 / cases where outcome=1
                    outcome_cases = df[df[outcome] == 1]
                    if len(outcome_cases) > 0:
                        sufficiency_coverage = len(condition_cases[condition_cases[outcome] == 1]) / len(outcome_cases)
                    else:
                        sufficiency_coverage = 0.0
                    
                    sufficiency_results.append({
                        'condition': condition,
                        'outcome': outcome,
                        'consistency': sufficiency_consistency,
                        'coverage': sufficiency_coverage,
                        'is_sufficient': sufficiency_consistency >= self.config.truth_table_consistency_threshold
                    })
        
        return sufficiency_results
    
    def _perform_minimization(self, truth_table: pd.DataFrame, conditions: List[str], outcomes: List[str]) -> Dict[str, Any]:
        """Perform basic logical minimization"""
        self._logger.info("Performing logical minimization...")
        
        minimization_results = {}
        
        for outcome in outcomes:
            outcome_col = f'{outcome}_outcome'
            
            if outcome_col not in truth_table.columns:
                continue
            
            # Find rows where outcome = 1 (sufficient combinations)
            sufficient_rows = truth_table[truth_table[outcome_col] == 1]
            
            if len(sufficient_rows) == 0:
                minimization_results[outcome] = {
                    'minimal_formula': "No sufficient conditions found",
                    'prime_implicants': [],
                    'solution': None
                }
                continue
            
            # Basic minimization: identify prime implicants
            prime_implicants = []
            
            for _, row in sufficient_rows.iterrows():
                implicant = []
                for condition in conditions:
                    if row[condition] == 1:
                        implicant.append(condition)
                    else:
                        implicant.append(f"~{condition}")
                
                implicant_str = " * ".join(implicant)
                prime_implicants.append({
                    'formula': implicant_str,
                    'consistency': row.get(f'{outcome}_consistency', 0.0),
                    'frequency': row.get('frequency', 0)
                })
            
            # Create minimal formula (basic OR of prime implicants)
            if prime_implicants:
                minimal_formula = " + ".join([pi['formula'] for pi in prime_implicants])
            else:
                minimal_formula = "No solution"
            
            minimization_results[outcome] = {
                'minimal_formula': minimal_formula,
                'prime_implicants': prime_implicants,
                'solution': {
                    'formula': minimal_formula,
                    'complexity': len(prime_implicants),
                    'avg_consistency': np.mean([pi['consistency'] for pi in prime_implicants]) if prime_implicants else 0.0
                }
            }
        
        return minimization_results
    
    def _calculate_consistency_scores(self, df: pd.DataFrame, conditions: List[str], outcomes: List[str]) -> Dict[str, float]:
        """Calculate overall consistency scores"""
        consistency_scores = {}
        
        for outcome in outcomes:
            outcome_cases = df[df[outcome] == 1]
            if len(outcome_cases) > 0:
                # Simple consistency measure: average consistency across conditions
                consistencies = []
                for condition in conditions:
                    condition_cases = df[df[condition] == 1]
                    if len(condition_cases) > 0:
                        consistency = condition_cases[outcome].mean()
                        consistencies.append(consistency)
                
                if consistencies:
                    consistency_scores[outcome] = np.mean(consistencies)
                else:
                    consistency_scores[outcome] = 0.0
            else:
                consistency_scores[outcome] = 0.0
        
        return consistency_scores
    
    def _calculate_coverage_scores(self, df: pd.DataFrame, conditions: List[str], outcomes: List[str]) -> Dict[str, float]:
        """Calculate overall coverage scores"""
        coverage_scores = {}
        
        for outcome in outcomes:
            outcome_cases = df[df[outcome] == 1]
            if len(outcome_cases) > 0:
                # Coverage: how well conditions explain the outcome
                coverages = []
                for condition in conditions:
                    condition_cases = df[df[condition] == 1]
                    if len(condition_cases) > 0:
                        # Cases where both condition and outcome are present
                        both_present = len(df[(df[condition] == 1) & (df[outcome] == 1)])
                        coverage = both_present / len(outcome_cases)
                        coverages.append(coverage)
                
                if coverages:
                    coverage_scores[outcome] = np.mean(coverages)
                else:
                    coverage_scores[outcome] = 0.0
            else:
                coverage_scores[outcome] = 0.0
        
        return coverage_scores
"""
QCA Truth Table Builder - Phase QCA-2
Constructs truth tables from calibrated conditions and outcomes
"""
import json
import logging
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any
from collections import defaultdict
from itertools import product

from .qca_schemas import (
    QCAConfiguration, CalibratedCase, TruthTable, TruthTableRow,
    OutcomeDefinition, CalibratedCondition, CalibrationMethod
)

logger = logging.getLogger(__name__)

class TruthTableBuilder:
    """Constructs QCA truth tables from calibrated cases"""
    
    def __init__(self, config: QCAConfiguration):
        self.config = config
        self.calibrated_cases: List[CalibratedCase] = []
    
    def load_calibrated_cases(self, cases: List[CalibratedCase] = None) -> None:
        """Load calibrated cases from file or parameter"""
        if cases:
            self.calibrated_cases = cases
            logger.info(f"Loaded {len(cases)} calibrated cases from parameter")
            return
        
        # Load from file
        calibration_file = Path(self.config.output_dir) / "calibrated_cases.json"
        if not calibration_file.exists():
            raise FileNotFoundError(f"Calibrated cases file not found: {calibration_file}")
        
        with open(calibration_file, 'r', encoding='utf-8') as f:
            cases_data = json.load(f)
        
        self.calibrated_cases = [CalibratedCase(**case_data) for case_data in cases_data]
        logger.info(f"Loaded {len(self.calibrated_cases)} calibrated cases from file")
    
    def calibrate_outcomes(self) -> None:
        """CRITICAL FIX: Calibrate outcome variables with explicit audit trail"""
        logger.info("Calibrating outcome variables with explicit derivation tracking")
        
        # Create outcome calculation diagnostics directory
        from pathlib import Path
        diagnostics_dir = Path(self.config.output_dir) / "outcome_diagnostics"
        diagnostics_dir.mkdir(parents=True, exist_ok=True)
        
        for outcome in self.config.outcomes:
            logger.info(f"Calibrating outcome: {outcome.outcome_id}")
            logger.info(f"Source conditions: {outcome.source_conditions}")
            logger.info(f"Combination rule: {outcome.combination_rule}")
            
            outcome_calculation_log = []
            
            for case in self.calibrated_cases:
                outcome_calculation = self._calculate_outcome_value_with_audit(case, outcome)
                
                # CRITICAL FIX: Store complete derivation trail
                outcome_calculation_log.append(outcome_calculation)
                
                # Create calibrated outcome condition
                calibrated_outcome = CalibratedCondition(
                    condition_id=outcome.outcome_id,
                    membership_score=outcome_calculation["final_value"],
                    raw_value=outcome_calculation["raw_combination"],
                    calibration_method=outcome.calibration.method
                )
                
                case.outcomes.append(calibrated_outcome)
            
            # CRITICAL FIX: Save outcome calculation audit trail
            audit_file = diagnostics_dir / f"outcome_calculation_{outcome.outcome_id}.json"
            with open(audit_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "outcome_definition": {
                        "outcome_id": outcome.outcome_id,
                        "name": outcome.name,
                        "description": outcome.description,
                        "source_conditions": outcome.source_conditions,
                        "combination_rule": outcome.combination_rule,
                        "calibration_method": outcome.calibration.method
                    },
                    "case_calculations": outcome_calculation_log
                }, f, indent=2)
            
            logger.info(f"Outcome calculation audit trail saved: {audit_file}")
    
    def _calculate_outcome_value_with_audit(self, case: CalibratedCase, outcome: OutcomeDefinition) -> Dict[str, Any]:
        """CRITICAL FIX: Calculate outcome value with complete audit trail"""
        # Get membership scores for all source conditions
        condition_memberships = {}
        missing_conditions = []
        
        for condition_id in outcome.source_conditions:
            found = False
            for condition in case.conditions:
                if condition.condition_id == condition_id:
                    condition_memberships[condition_id] = condition.membership_score
                    found = True
                    break
            
            if not found:
                missing_conditions.append(condition_id)
                condition_memberships[condition_id] = 0.0  # Default to 0 for missing conditions
        
        # Log any missing conditions
        if missing_conditions:
            logger.warning(f"Missing conditions for outcome {outcome.outcome_id} in case {case.case_id}: {missing_conditions}")
        
        # Apply combination rule with detailed tracking
        calculation_steps = []
        
        if outcome.combination_rule == "any":
            # Maximum of all source conditions
            raw_result = max(condition_memberships.values()) if condition_memberships else 0.0
            calculation_steps.append(f"max({condition_memberships}) = {raw_result}")
            
        elif outcome.combination_rule == "all":
            # Minimum of all source conditions  
            raw_result = min(condition_memberships.values()) if condition_memberships else 0.0
            calculation_steps.append(f"min({condition_memberships}) = {raw_result}")
            
        else:
            # Custom Python expression with detailed error handling
            try:
                # Make condition IDs available as variables
                namespace = {"__builtins__": {}, "min": min, "max": max}
                namespace.update(condition_memberships)
                
                calculation_steps.append(f"Evaluating: {outcome.combination_rule}")
                calculation_steps.append(f"With variables: {condition_memberships}")
                
                raw_result = eval(outcome.combination_rule, namespace)
                calculation_steps.append(f"Raw result: {raw_result}")
                
                raw_result = max(0.0, min(1.0, float(raw_result)))  # Clamp to [0,1]
                calculation_steps.append(f"Clamped result: {raw_result}")
                
            except Exception as e:
                logger.error(f"Outcome calculation failed for {outcome.outcome_id}: {e}")
                raw_result = 0.0
                calculation_steps.append(f"ERROR: {str(e)}")
        
        # Apply outcome-specific calibration if needed
        if hasattr(outcome.calibration, 'method') and outcome.calibration.method != CalibrationMethod.FUZZY:
            # Apply the same calibration logic as conditions
            final_value = self._apply_outcome_calibration(raw_result, outcome.calibration)
            calculation_steps.append(f"Applied {outcome.calibration.method} calibration: {final_value}")
        else:
            final_value = raw_result
        
        # Return complete audit trail
        return {
            "case_id": case.case_id,
            "source_condition_values": condition_memberships,
            "missing_conditions": missing_conditions,
            "combination_rule": outcome.combination_rule,
            "calculation_steps": calculation_steps,
            "raw_combination": raw_result,
            "final_value": final_value,
            "calibration_applied": outcome.calibration.method if hasattr(outcome.calibration, 'method') else "none"
        }
    
    def _calculate_outcome_value(self, case: CalibratedCase, outcome: OutcomeDefinition) -> float:
        """Calculate outcome value for a specific case (legacy method for compatibility)"""
        audit_result = self._calculate_outcome_value_with_audit(case, outcome)
        return audit_result["final_value"]
    
    def _apply_outcome_calibration(self, raw_value: float, calibration: Any) -> float:
        """Apply calibration to outcome values"""
        if not hasattr(calibration, 'method'):
            return raw_value
        
        if calibration.method == CalibrationMethod.BINARY:
            threshold = getattr(calibration, 'binary_threshold', 0.5)
            return 1.0 if raw_value >= threshold else 0.0
        
        elif calibration.method == CalibrationMethod.FREQUENCY:
            # Apply same frequency calibration as conditions
            breakpoints = getattr(calibration, 'frequency_breakpoints', [0.2, 0.5, 0.8])
            if raw_value <= breakpoints[0]:
                return 0.2
            elif raw_value <= breakpoints[1]:
                return 0.5
            else:
                return 0.8
        
        else:
            # For other methods, return raw value
            return raw_value
    
    def construct_truth_table(self, outcome_id: str, table_mode: str = None) -> TruthTable:
        """Construct truth table for a specific outcome in specified mode"""
        if table_mode is None:
            table_mode = "fuzzy" if self.config.truth_table_mode in ["fuzzy", "dual"] else "crisp"
        
        logger.info(f"Constructing {table_mode} truth table for outcome: {outcome_id}")
        
        # Get condition IDs (exclude the outcome itself)
        condition_ids = [cond.condition_id for cond in self.config.conditions]
        
        # Group cases by their condition configurations
        configurations = defaultdict(list)
        
        for case in self.calibrated_cases:
            # Create configuration tuple
            config_key = []
            config_dict = {}
            
            for cond_id in condition_ids:
                # Find membership score for this condition
                membership = 0.0
                for condition in case.conditions:
                    if condition.condition_id == cond_id:
                        membership = condition.membership_score
                        break
                
                # CRITICAL FIX: Preserve fuzzy information or discretize based on mode
                if table_mode == "fuzzy":
                    # Preserve exact membership scores - NO INFORMATION LOSS
                    processed_membership = membership
                else:  # crisp mode
                    # Apply discretization only in crisp mode
                    processed_membership = self._discretize_membership(membership)
                
                config_key.append(processed_membership)
                config_dict[cond_id] = processed_membership
            
            # Get outcome value
            outcome_membership = 0.0
            for outcome in case.outcomes:
                if outcome.condition_id == outcome_id:
                    outcome_membership = outcome.membership_score
                    break
            
            # CRITICAL FIX: Use precise tuple for fuzzy, rounded tuple for crisp
            if table_mode == "fuzzy":
                # Group by precise membership values (could be 0.2, 0.5, 0.8, etc.)
                config_tuple = tuple(round(val, 3) for val in config_key)  # Round to avoid floating point issues
            else:
                # Group by crisp values (0.0 or 1.0 only)
                config_tuple = tuple(config_key)
            
            configurations[config_tuple].append({
                'case_id': case.case_id,
                'config_dict': config_dict,
                'outcome': outcome_membership
            })
        
        # Build truth table rows
        truth_table_rows = []
        for config_tuple, cases_with_config in configurations.items():
            case_ids = [case_info['case_id'] for case_info in cases_with_config]
            config_dict = cases_with_config[0]['config_dict']  # All cases have same config
            
            # Calculate outcome for this configuration
            outcome_values = [case_info['outcome'] for case_info in cases_with_config]
            
            # CRITICAL FIX: Handle outcome calculation properly for fuzzy vs crisp
            if table_mode == "fuzzy":
                # For fuzzy tables, preserve the actual outcome scores
                avg_outcome = sum(outcome_values) / len(outcome_values) if outcome_values else 0.0
            else:
                # For crisp tables, apply discretization to outcome as well
                discrete_outcomes = [self._discretize_membership(val) for val in outcome_values]
                avg_outcome = sum(discrete_outcomes) / len(discrete_outcomes) if discrete_outcomes else 0.0
            
            # Calculate consistency (how consistently this config leads to outcome)
            consistency = self._calculate_consistency(outcome_values)
            
            # Coverage will be calculated later across all rows
            truth_table_row = TruthTableRow(
                configuration=config_dict,
                outcome=avg_outcome,
                cases=case_ids,
                consistency=consistency,
                coverage=0.0  # Will be calculated after all rows
            )
            truth_table_rows.append(truth_table_row)
        
        # Calculate coverage for each row
        total_outcome_membership = sum(
            max(case_info['outcome'] for case_info in cases_with_config)
            for cases_with_config in configurations.values()
        )
        
        for row in truth_table_rows:
            if total_outcome_membership > 0:
                row.coverage = row.outcome * len(row.cases) / total_outcome_membership
        
        # Calculate logical remainders - adjust for fuzzy vs crisp
        if table_mode == "crisp":
            total_possible_configs = 2 ** len(condition_ids)  # Binary combinations
        else:
            # For fuzzy tables, logical remainders are less meaningful but still calculate
            total_possible_configs = len(configurations)  # Just observed configs
        
        observed_configs = len(configurations)
        logical_remainders = max(0, total_possible_configs - observed_configs)
        
        truth_table = TruthTable(
            conditions=condition_ids,
            outcome=outcome_id,
            rows=truth_table_rows,
            table_mode=table_mode,  # CRITICAL: Track the mode
            total_cases=len(self.calibrated_cases),
            configurations_found=observed_configs,
            logical_remainders=logical_remainders
        )
        
        logger.info(f"{table_mode.capitalize()} truth table constructed: {observed_configs} configurations, {logical_remainders} logical remainders")
        return truth_table
    
    def _discretize_membership(self, membership: float, threshold: float = None) -> float:
        """Discretize membership score for truth table construction"""
        if threshold is None:
            threshold = self.config.minimum_membership_threshold
        
        # Simple binary discretization
        return 1.0 if membership >= threshold else 0.0
        
        # Alternative: Could keep fuzzy or use multiple thresholds
        # if membership >= 0.8:
        #     return 1.0
        # elif membership >= 0.5:
        #     return 0.5
        # else:
        #     return 0.0
    
    def _calculate_consistency(self, outcome_values: List[float]) -> float:
        """Calculate consistency score for a configuration"""
        if not outcome_values:
            return 0.0
        
        # Simple consistency: how close are all outcomes to the mean?
        mean_outcome = sum(outcome_values) / len(outcome_values)
        deviations = [abs(value - mean_outcome) for value in outcome_values]
        avg_deviation = sum(deviations) / len(deviations)
        
        # Convert to consistency score (lower deviation = higher consistency)
        consistency = 1.0 - min(avg_deviation, 1.0)
        return consistency
    
    def construct_all_truth_tables(self) -> List[TruthTable]:
        """Construct truth tables for all outcomes in configured mode(s)"""
        logger.info(f"Constructing truth tables for all outcomes in {self.config.truth_table_mode} mode")
        
        # First calibrate outcomes
        self.calibrate_outcomes()
        
        # Construct truth table for each outcome
        truth_tables = []
        for outcome in self.config.outcomes:
            
            if self.config.truth_table_mode == "dual":
                # CRITICAL FIX: Generate both crisp and fuzzy tables
                crisp_table = self.construct_truth_table(outcome.outcome_id, "crisp")
                fuzzy_table = self.construct_truth_table(outcome.outcome_id, "fuzzy")
                truth_tables.extend([crisp_table, fuzzy_table])
                logger.info(f"Generated both crisp and fuzzy truth tables for outcome: {outcome.outcome_id}")
                
            else:
                # Generate single table in specified mode
                truth_table = self.construct_truth_table(outcome.outcome_id, self.config.truth_table_mode)
                truth_tables.append(truth_table)
        
        return truth_tables
    
    def save_truth_tables(self, truth_tables: List[TruthTable]) -> List[str]:
        """Save truth tables to output files"""
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        for truth_table in truth_tables:
            outcome_id = truth_table.outcome
            mode_suffix = f"_{truth_table.table_mode}"
            
            # CRITICAL FIX: Include mode in filename to distinguish crisp vs fuzzy
            # Save as JSON
            json_file = output_path / f"truth_table_{outcome_id}{mode_suffix}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(truth_table.model_dump(), f, indent=2)
            saved_files.append(str(json_file))
            
            # Save as CSV
            csv_file = output_path / f"truth_table_{outcome_id}{mode_suffix}.csv"
            self._save_truth_table_csv(truth_table, csv_file)
            saved_files.append(str(csv_file))
        
        # Save summary of all truth tables
        summary_file = output_path / "truth_tables_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            summary = {
                'total_outcomes': len(truth_tables),
                'total_cases': truth_tables[0].total_cases if truth_tables else 0,
                'outcomes': [
                    {
                        'outcome_id': tt.outcome,
                        'table_mode': tt.table_mode,  # CRITICAL: Include mode in summary
                        'configurations_found': tt.configurations_found,
                        'logical_remainders': tt.logical_remainders,
                        'conditions': tt.conditions
                    }
                    for tt in truth_tables
                ]
            }
            json.dump(summary, f, indent=2)
        saved_files.append(str(summary_file))
        
        logger.info(f"Saved {len(truth_tables)} truth tables to {len(saved_files)} files")
        return saved_files
    
    def _save_truth_table_csv(self, truth_table: TruthTable, csv_file: Path) -> None:
        """Save truth table as CSV file"""
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            header = truth_table.conditions + [truth_table.outcome, 'cases', 'consistency', 'coverage']
            writer.writerow(header)
            
            # Data rows
            for row in truth_table.rows:
                csv_row = []
                
                # Condition values
                for cond_id in truth_table.conditions:
                    csv_row.append(row.configuration.get(cond_id, 0.0))
                
                # Outcome, cases, consistency, coverage
                csv_row.extend([
                    row.outcome,
                    ';'.join(row.cases),
                    row.consistency or 0.0,
                    row.coverage or 0.0
                ])
                
                writer.writerow(csv_row)
    
    def run_truth_table_phase(self, calibrated_cases: List[CalibratedCase] = None) -> List[TruthTable]:
        """Run complete Phase QCA-2: Truth Table Construction"""
        logger.info("=== Running Phase QCA-2: Truth Table Construction ===")
        
        # Load calibrated cases
        self.load_calibrated_cases(calibrated_cases)
        
        # Construct all truth tables
        truth_tables = self.construct_all_truth_tables()
        
        # Save results
        saved_files = self.save_truth_tables(truth_tables)
        
        logger.info(f"Phase QCA-2 complete: {len(truth_tables)} truth tables constructed, {len(saved_files)} files saved")
        return truth_tables
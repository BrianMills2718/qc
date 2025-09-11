"""
QCA Calibration Engine - Phase QCA-1
Converts codes, speaker properties, entities to set membership scores
"""
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Union, Optional
from collections import Counter

from .qca_schemas import (
    QCAConfiguration, CalibrationRule, CalibrationMethod, 
    CalibratedCondition, CalibratedCase, ConditionDefinition
)

logger = logging.getLogger(__name__)

class CalibrationEngine:
    """Engine for calibrating qualitative data to QCA set memberships"""
    
    def __init__(self, config: QCAConfiguration):
        self.config = config
        self.coded_interviews: List[Dict[str, Any]] = []
        self.raw_data_cache: Dict[str, Dict[str, Any]] = {}  # condition_id -> case_id -> raw_value
        
    def load_coded_interviews(self) -> None:
        """Load all coded interview JSON files from input directory"""
        input_path = Path(self.config.input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {self.config.input_dir}")
        
        json_files = list(input_path.glob("**/*.json"))
        interview_files = [f for f in json_files if 'interviews' in str(f) or f.name.startswith('interview_')]
        
        logger.info(f"Loading {len(interview_files)} coded interview files")
        
        for file_path in interview_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    interview_data = json.load(f)
                    interview_data['source_file'] = str(file_path)
                    self.coded_interviews.append(interview_data)
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
        
        logger.info(f"Successfully loaded {len(self.coded_interviews)} interviews")
    
    def extract_raw_values(self) -> None:
        """Extract raw values for each condition from coded interviews"""
        logger.info("Extracting raw values for calibration")
        
        for condition in self.config.conditions:
            self.raw_data_cache[condition.condition_id] = {}
            
            for interview in self.coded_interviews:
                case_id = interview.get(self.config.case_id_field, interview.get('interview_id', 'unknown'))
                raw_value = self._extract_condition_value(interview, condition)
                self.raw_data_cache[condition.condition_id][case_id] = raw_value
    
    def _extract_condition_value(self, interview: Dict[str, Any], condition: ConditionDefinition) -> Union[int, float, str]:
        """Extract raw value for a specific condition from an interview"""
        
        if condition.source_type == "code":
            # Count occurrences of this code - handle both formats
            total_count = 0
            for quote in interview.get('quotes', []):
                # New format: code_ids list
                if 'code_ids' in quote:
                    code_ids = quote.get('code_ids', [])
                    total_count += code_ids.count(condition.source_id)
                # Legacy format: applied_codes list
                elif 'applied_codes' in quote:
                    for applied_code in quote.get('applied_codes', []):
                        if applied_code.get('code_id') == condition.source_id:
                            total_count += 1
            return total_count
        
        elif condition.source_type == "speaker_property":
            # Count speakers with this property
            speakers_with_property = 0
            for speaker in interview.get('speakers', []):
                for prop in speaker.get('properties', []):
                    if prop.get('property_id') == condition.source_id:
                        speakers_with_property += 1
            return speakers_with_property
        
        elif condition.source_type == "entity":
            # Count entities of this type - handle both formats
            entity_count = 0
            # Check at interview level
            for entity in interview.get('entities', []):
                if entity.get('entity_type') == condition.source_id or entity.get('type') == condition.source_id:
                    entity_count += 1
            # Also check in quotes
            for quote in interview.get('quotes', []):
                for entity in quote.get('quote_entities', []):
                    if entity.get('type') == condition.source_id:
                        entity_count += 1
            return entity_count
        
        elif condition.source_type == "relationship":
            # Count relationships of this type - handle both formats  
            relationship_count = 0
            # Check at interview level
            for relationship in interview.get('relationships', []):
                if relationship.get('relationship_type') == condition.source_id:
                    relationship_count += 1
            # Also check in quotes
            for quote in interview.get('quotes', []):
                for relationship in quote.get('quote_relationships', []):
                    if relationship.get('relationship_type') == condition.source_id:
                        relationship_count += 1
            return relationship_count
        
        else:
            logger.warning(f"Unknown source_type: {condition.source_type}")
            return 0
    
    def calibrate_condition(self, condition: ConditionDefinition) -> Dict[str, CalibratedCondition]:
        """Calibrate a single condition across all cases"""
        raw_values = self.raw_data_cache[condition.condition_id]
        
        # CRITICAL FIX: Apply normalization before calibration if specified
        if condition.calibration.normalization_method != "none":
            raw_values = self._normalize_values(raw_values, condition.calibration.normalization_method)
        
        calibrated_results = {}
        
        logger.info(f"Calibrating condition: {condition.condition_id} using {condition.calibration.method}")
        logger.info(f"Theoretical justification: {condition.calibration.theoretical_justification}")
        
        if condition.calibration.method == CalibrationMethod.BINARY:
            threshold = condition.calibration.binary_threshold or 1
            for case_id, raw_value in raw_values.items():
                membership = 1.0 if raw_value >= threshold else 0.0
                calibrated_results[case_id] = CalibratedCondition(
                    condition_id=condition.condition_id,
                    membership_score=membership,
                    raw_value=raw_value,
                    calibration_method="binary"
                )
        
        elif condition.calibration.method == CalibrationMethod.FREQUENCY:
            breakpoints = condition.calibration.frequency_breakpoints or [1, 3, 5]
            thresholds = condition.calibration.frequency_thresholds or {
                "rare": 0.2, "moderate": 0.5, "frequent": 0.8
            }
            
            for case_id, raw_value in raw_values.items():
                membership = self._frequency_calibration(raw_value, breakpoints, thresholds)
                calibrated_results[case_id] = CalibratedCondition(
                    condition_id=condition.condition_id,
                    membership_score=membership,
                    raw_value=raw_value,
                    calibration_method="frequency"
                )
        
        elif condition.calibration.method == CalibrationMethod.FUZZY:
            fuzzy_function = condition.calibration.fuzzy_function or "min(count / 10, 1.0)"
            for case_id, raw_value in raw_values.items():
                try:
                    # Safe evaluation of fuzzy function
                    count = raw_value  # Make 'count' available in expression
                    membership = eval(fuzzy_function, {"__builtins__": {}, "min": min, "max": max}, {"count": count})
                    membership = max(0.0, min(1.0, float(membership)))  # Clamp to [0,1]
                except Exception as e:
                    logger.error(f"Fuzzy function evaluation failed for {condition.condition_id}: {e}")
                    membership = 0.0
                
                calibrated_results[case_id] = CalibratedCondition(
                    condition_id=condition.condition_id,
                    membership_score=membership,
                    raw_value=raw_value,
                    calibration_method="fuzzy"
                )
        
        elif condition.calibration.method == CalibrationMethod.PERCENTILE:
            values = list(raw_values.values())
            percentiles = condition.calibration.percentile_thresholds or [0.33, 0.67]
            breakpoints = [np.percentile(values, p * 100) for p in percentiles]
            
            for case_id, raw_value in raw_values.items():
                membership = self._percentile_calibration(raw_value, breakpoints)
                calibrated_results[case_id] = CalibratedCondition(
                    condition_id=condition.condition_id,
                    membership_score=membership,
                    raw_value=raw_value,
                    calibration_method="percentile"
                )
        
        # CRITICAL FIX: New theoretically grounded calibration methods
        elif condition.calibration.method == CalibrationMethod.DIRECT:
            direct_thresholds = condition.calibration.direct_thresholds or {
                "non_membership": 0.0, "crossover": 0.5, "full_membership": 1.0
            }
            
            for case_id, raw_value in raw_values.items():
                membership = self._direct_calibration(raw_value, direct_thresholds)
                calibrated_results[case_id] = CalibratedCondition(
                    condition_id=condition.condition_id,
                    membership_score=membership,
                    raw_value=raw_value,
                    calibration_method="direct"
                )
        
        elif condition.calibration.method == CalibrationMethod.ANCHOR_POINTS:
            anchor_points = condition.calibration.anchor_points or {
                "non_member": 0, "crossover": 3, "full_member": 6
            }
            
            for case_id, raw_value in raw_values.items():
                membership = self._anchor_points_calibration(raw_value, anchor_points)
                calibrated_results[case_id] = CalibratedCondition(
                    condition_id=condition.condition_id,
                    membership_score=membership,
                    raw_value=raw_value,
                    calibration_method="anchor_points"
                )
        
        elif condition.calibration.method == CalibrationMethod.INTERACTIVE:
            # For now, fall back to percentile but log requirement for validation
            logger.warning(f"Interactive calibration for {condition.condition_id} requires researcher validation")
            values = list(raw_values.values())
            percentiles = condition.calibration.percentile_thresholds or [0.33, 0.67]
            breakpoints = [np.percentile(values, p * 100) for p in percentiles]
            
            for case_id, raw_value in raw_values.items():
                membership = self._percentile_calibration(raw_value, breakpoints)
                calibrated_results[case_id] = CalibratedCondition(
                    condition_id=condition.condition_id,
                    membership_score=membership,
                    raw_value=raw_value,
                    calibration_method="interactive_pending"
                )
        
        # Generate calibration diagnostics (CRITICAL FIX: Audit trail)
        self._generate_calibration_diagnostics(condition, raw_values, calibrated_results)
        
        return calibrated_results
    
    def _frequency_calibration(self, raw_value: Union[int, float], breakpoints: List[int], 
                             thresholds: Dict[str, float]) -> float:
        """Apply frequency-based calibration"""
        if raw_value == 0:
            return 0.0
        elif raw_value < breakpoints[0]:
            return thresholds.get("rare", 0.2)
        elif raw_value < breakpoints[1]:
            return thresholds.get("moderate", 0.5)
        else:
            return thresholds.get("frequent", 0.8)
    
    def _percentile_calibration(self, raw_value: Union[int, float], breakpoints: List[float]) -> float:
        """Apply percentile-based calibration"""
        if raw_value <= breakpoints[0]:
            return 0.2
        elif raw_value <= breakpoints[1]:
            return 0.5
        else:
            return 0.8
    
    def _direct_calibration(self, raw_value: Union[int, float], thresholds: Dict[str, float]) -> float:
        """CRITICAL FIX: Direct calibration with explicit thresholds"""
        non_membership = thresholds.get("non_membership", 0.0)
        crossover = thresholds.get("crossover", 0.5)
        full_membership = thresholds.get("full_membership", 1.0)
        
        # Map raw value to membership based on direct assignment
        if raw_value == 0:
            return non_membership
        elif raw_value == 1:
            return crossover
        else:
            return full_membership
    
    def _anchor_points_calibration(self, raw_value: Union[int, float], anchor_points: Dict[str, Union[int, float]]) -> float:
        """CRITICAL FIX: Three-value anchor points calibration (standard QCA practice)"""
        non_member = anchor_points.get("non_member", 0)
        crossover = anchor_points.get("crossover", 3)
        full_member = anchor_points.get("full_member", 6)
        
        if raw_value <= non_member:
            return 0.0  # Non-membership
        elif raw_value <= crossover:
            # Linear interpolation between non-member and crossover
            return 0.5 * (raw_value - non_member) / (crossover - non_member)
        elif raw_value <= full_member:
            # Linear interpolation between crossover and full member
            return 0.5 + 0.5 * (raw_value - crossover) / (full_member - crossover)
        else:
            return 1.0  # Full membership
    
    def _normalize_values(self, raw_values: Dict[str, Union[int, float]], 
                         normalization_method: str) -> Dict[str, float]:
        """CRITICAL FIX: Normalize values for meaningful comparison"""
        normalized_values = {}
        
        for case_id, raw_value in raw_values.items():
            # Get interview metadata for normalization
            interview_metadata = self._get_interview_metadata(case_id)
            
            if normalization_method == "per_thousand_words":
                word_count = interview_metadata.get("word_count", 1000)  # Default fallback
                normalized_values[case_id] = (raw_value / word_count) * 1000
            
            elif normalization_method == "per_speaker":
                speaker_count = interview_metadata.get("speaker_count", 1)
                normalized_values[case_id] = raw_value / speaker_count
            
            elif normalization_method == "per_quote":
                quote_count = interview_metadata.get("quote_count", 1)
                normalized_values[case_id] = raw_value / quote_count
            
            else:  # "none" or unknown
                normalized_values[case_id] = float(raw_value)
        
        return normalized_values
    
    def _get_interview_metadata(self, case_id: str) -> Dict[str, int]:
        """Extract metadata from interview for normalization"""
        # Find the interview data for this case
        for interview in self.coded_interviews:
            if interview.get(self.config.case_id_field, interview.get('interview_id', 'unknown')) == case_id:
                quotes = interview.get('quotes', [])
                speakers = interview.get('speakers', [])
                
                # Estimate word count from quotes (rough approximation)
                total_text = " ".join(quote.get('text', '') for quote in quotes)
                word_count = len(total_text.split()) if total_text else 1000
                
                return {
                    "word_count": word_count,
                    "speaker_count": len(speakers) or 1,
                    "quote_count": len(quotes) or 1
                }
        
        # Fallback metadata
        return {"word_count": 1000, "speaker_count": 1, "quote_count": 1}
    
    def _generate_calibration_diagnostics(self, condition: ConditionDefinition, 
                                        raw_values: Dict[str, Union[int, float]], 
                                        calibrated_results: Dict[str, CalibratedCondition]) -> None:
        """CRITICAL FIX: Generate calibration audit trail and diagnostics"""
        import os
        from pathlib import Path
        
        # Create diagnostics directory
        diagnostics_dir = Path(self.config.output_dir) / "calibration_diagnostics"
        diagnostics_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate calibration report
        diagnostic_data = {
            "condition_id": condition.condition_id,
            "condition_name": condition.name,
            "calibration_method": condition.calibration.method,
            "theoretical_justification": condition.calibration.theoretical_justification,
            "raw_value_statistics": {
                "min": min(raw_values.values()) if raw_values else 0,
                "max": max(raw_values.values()) if raw_values else 0,
                "mean": sum(raw_values.values()) / len(raw_values) if raw_values else 0,
                "count": len(raw_values)
            },
            "membership_score_statistics": {
                "min": min(cr.membership_score for cr in calibrated_results.values()) if calibrated_results else 0,
                "max": max(cr.membership_score for cr in calibrated_results.values()) if calibrated_results else 0,
                "mean": sum(cr.membership_score for cr in calibrated_results.values()) / len(calibrated_results) if calibrated_results else 0
            },
            "threshold_placement": self._analyze_threshold_placement(raw_values, calibrated_results),
            "cases_by_membership": self._group_cases_by_membership(calibrated_results)
        }
        
        # Save diagnostic report
        diagnostic_file = diagnostics_dir / f"calibration_{condition.condition_id}.json"
        with open(diagnostic_file, 'w', encoding='utf-8') as f:
            json.dump(diagnostic_data, f, indent=2)
        
        logger.info(f"Calibration diagnostics saved: {diagnostic_file}")
    
    def _analyze_threshold_placement(self, raw_values: Dict[str, Union[int, float]], 
                                   calibrated_results: Dict[str, CalibratedCondition]) -> Dict[str, Any]:
        """Analyze how thresholds divide the cases"""
        # Group cases by their membership scores
        membership_groups = {}
        for case_id, calibrated in calibrated_results.items():
            score = calibrated.membership_score
            if score not in membership_groups:
                membership_groups[score] = []
            membership_groups[score].append({
                "case_id": case_id,
                "raw_value": raw_values[case_id],
                "membership_score": score
            })
        
        return {
            "unique_membership_scores": sorted(membership_groups.keys()),
            "membership_distribution": {
                str(score): len(cases) for score, cases in membership_groups.items()
            },
            "threshold_effectiveness": len(membership_groups) > 1  # Are thresholds creating meaningful distinctions?
        }
    
    def _group_cases_by_membership(self, calibrated_results: Dict[str, CalibratedCondition]) -> Dict[str, List[str]]:
        """Group cases by their final membership scores for analysis"""
        groups = {}
        for case_id, calibrated in calibrated_results.items():
            score_key = f"{calibrated.membership_score:.2f}"
            if score_key not in groups:
                groups[score_key] = []
            groups[score_key].append(case_id)
        
        return groups
    
    def calibrate_all_conditions(self) -> List[CalibratedCase]:
        """Calibrate all conditions and create calibrated cases"""
        logger.info("Starting calibration of all conditions")
        
        # First extract raw values
        self.extract_raw_values()
        
        # Calibrate each condition
        all_calibrated_conditions = {}
        for condition in self.config.conditions:
            calibrated_condition = self.calibrate_condition(condition)
            all_calibrated_conditions[condition.condition_id] = calibrated_condition
        
        # Create calibrated cases
        calibrated_cases = []
        for interview in self.coded_interviews:
            case_id = interview.get(self.config.case_id_field, interview.get('interview_id', 'unknown'))
            
            # Collect all conditions for this case
            case_conditions = []
            for condition in self.config.conditions:
                if case_id in all_calibrated_conditions[condition.condition_id]:
                    case_conditions.append(all_calibrated_conditions[condition.condition_id][case_id])
            
            # Create calibrated case
            calibrated_case = CalibratedCase(
                case_id=case_id,
                conditions=case_conditions,
                outcomes=[],  # Outcomes will be calculated separately
                source_file=interview.get('source_file', ''),
                total_quotes=len(interview.get('quotes', [])),
                total_codes=sum(len(quote.get('code_ids', quote.get('applied_codes', []))) for quote in interview.get('quotes', []))
            )
            calibrated_cases.append(calibrated_case)
        
        logger.info(f"Calibrated {len(calibrated_cases)} cases with {len(self.config.conditions)} conditions each")
        return calibrated_cases
    
    def save_calibration_results(self, calibrated_cases: List[CalibratedCase]) -> List[str]:
        """Save calibration results to output files"""
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        # Save as JSON
        json_file = output_path / "calibrated_cases.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump([case.model_dump() for case in calibrated_cases], f, indent=2)
        saved_files.append(str(json_file))
        
        # Save as CSV for external analysis
        csv_file = output_path / "calibration_matrix.csv"
        self._save_as_csv(calibrated_cases, csv_file)
        saved_files.append(str(csv_file))
        
        logger.info(f"Saved calibration results to {len(saved_files)} files")
        return saved_files
    
    def _save_as_csv(self, calibrated_cases: List[CalibratedCase], csv_file: Path) -> None:
        """Save calibrated cases as CSV matrix"""
        import csv
        
        # Get all condition IDs
        condition_ids = []
        if calibrated_cases and calibrated_cases[0].conditions:
            condition_ids = [cond.condition_id for cond in calibrated_cases[0].conditions]
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            header = ['case_id'] + condition_ids + ['total_quotes', 'total_codes']
            writer.writerow(header)
            
            # Data rows
            for case in calibrated_cases:
                row = [case.case_id]
                
                # Add condition membership scores
                condition_scores = {cond.condition_id: cond.membership_score for cond in case.conditions}
                for cond_id in condition_ids:
                    row.append(condition_scores.get(cond_id, 0.0))
                
                # Add metadata
                row.extend([case.total_quotes, case.total_codes])
                writer.writerow(row)
    
    def run_calibration_phase(self) -> List[CalibratedCase]:
        """Run complete Phase QCA-1: Code to Set Membership calibration"""
        logger.info("=== Running Phase QCA-1: Code to Set Membership Calibration ===")
        
        # Load data
        self.load_coded_interviews()
        
        # Calibrate all conditions
        calibrated_cases = self.calibrate_all_conditions()
        
        # Save results
        saved_files = self.save_calibration_results(calibrated_cases)
        
        logger.info(f"Phase QCA-1 complete: {len(calibrated_cases)} cases calibrated, {len(saved_files)} files saved")
        return calibrated_cases
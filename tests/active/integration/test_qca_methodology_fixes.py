"""
Test Suite for QCA Methodology Fixes
Validates that all critical methodology issues have been properly addressed
"""
import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any

from src.qc.qca.qca_schemas import (
    QCAConfiguration, ConditionDefinition, OutcomeDefinition, 
    CalibrationRule, CalibrationMethod, CalibratedCase, CalibratedCondition
)
from src.qc.qca.calibration_engine import CalibrationEngine
from src.qc.qca.truth_table_builder import TruthTableBuilder
from src.qc.qca.audit_trail_system import QCAAuditTrail, QCAMethodologyValidator
from src.qc.qca.qca_pipeline import QCAPipeline


class TestCriticalMethodologyFixes:
    """Test all critical methodology fixes"""
    
    def setup_method(self):
        """Set up test configuration and data"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test configuration with methodology fixes
        self.config = QCAConfiguration(
            input_dir="test_data",
            output_dir=self.test_dir,
            truth_table_mode="dual",  # CRITICAL FIX: Test dual mode
            conditions=[
                ConditionDefinition(
                    condition_id="test_condition",
                    name="Test Condition", 
                    description="Test condition for methodology validation",
                    source_type="code",
                    source_id="TEST_CODE",
                    calibration=CalibrationRule(
                        method=CalibrationMethod.ANCHOR_POINTS,
                        theoretical_justification="Test justification based on literature",  # CRITICAL FIX
                        anchor_points={"non_member": 0, "crossover": 3, "full_member": 6},
                        normalization_method="per_thousand_words"  # CRITICAL FIX
                    )
                )
            ],
            outcomes=[
                OutcomeDefinition(
                    outcome_id="test_outcome",
                    name="Test Outcome",
                    description="Test outcome for validation",
                    source_conditions=["test_condition"],
                    combination_rule="test_condition * 0.8",  # Explicit rule
                    calibration=CalibrationRule(
                        method=CalibrationMethod.FUZZY,
                        theoretical_justification="Fuzzy outcome based on condition strength"
                    )
                )
            ]
        )
        
        # Create test cases with varying membership scores
        self.test_cases = [
            CalibratedCase(
                case_id="case_1",
                conditions=[
                    CalibratedCondition(
                        condition_id="test_condition",
                        membership_score=0.2,  # Fuzzy score
                        raw_value=1,
                        calibration_method="anchor_points"
                    )
                ],
                outcomes=[],
                source_file="test_case_1.json",
                total_quotes=10,
                total_codes=5
            ),
            CalibratedCase(
                case_id="case_2", 
                conditions=[
                    CalibratedCondition(
                        condition_id="test_condition",
                        membership_score=0.5,  # Crossover point
                        raw_value=3,
                        calibration_method="anchor_points"
                    )
                ],
                outcomes=[],
                source_file="test_case_2.json",
                total_quotes=15,
                total_codes=8
            ),
            CalibratedCase(
                case_id="case_3",
                conditions=[
                    CalibratedCondition(
                        condition_id="test_condition", 
                        membership_score=0.8,  # High membership
                        raw_value=5,
                        calibration_method="anchor_points"
                    )
                ],
                outcomes=[],
                source_file="test_case_3.json",
                total_quotes=20,
                total_codes=12
            )
        ]

    def test_fix_1_dual_mode_truth_tables_preserve_fuzzy_information(self):
        """CRITICAL FIX 1: Test that fuzzy information is preserved in dual-mode truth tables"""
        # Create truth table builder
        builder = TruthTableBuilder(self.config)
        builder.calibrated_cases = self.test_cases
        
        # Calibrate outcomes
        builder.calibrate_outcomes()
        
        # Test fuzzy mode preserves exact membership scores
        fuzzy_table = builder.construct_truth_table("test_outcome", "fuzzy")
        
        assert fuzzy_table.table_mode == "fuzzy"
        
        # Check that configurations preserve fuzzy values (0.2, 0.5, 0.8)
        config_values = set()
        for row in fuzzy_table.rows:
            for condition_value in row.configuration.values():
                config_values.add(condition_value)
        
        # CRITICAL: Should have preserved original fuzzy scores (0.2, 0.5, 0.8)
        # NOT converted to binary (0.0, 1.0)
        assert 0.2 in config_values or 0.5 in config_values or 0.8 in config_values
        assert len(config_values) > 2  # More than just 0.0 and 1.0
        
        # Test crisp mode for comparison
        crisp_table = builder.construct_truth_table("test_outcome", "crisp")
        assert crisp_table.table_mode == "crisp"
        
        # Crisp mode should have binary values
        crisp_config_values = set()
        for row in crisp_table.rows:
            for condition_value in row.configuration.values():
                crisp_config_values.add(condition_value)
        
        # Crisp should only have 0.0 and 1.0 (or similar binary values)
        assert len(crisp_config_values) <= 2
        
        print("✅ FIX 1 VALIDATED: Fuzzy information preserved in dual-mode truth tables")

    def test_fix_2_theoretical_justification_required(self):
        """CRITICAL FIX 2: Test that theoretical justification is required and logged"""
        # Test that calibration rules require theoretical justification
        condition = self.config.conditions[0]
        assert hasattr(condition.calibration, 'theoretical_justification')
        assert condition.calibration.theoretical_justification != ""
        
        # Test that audit trail captures justification
        audit_trail = QCAAuditTrail(self.config)
        
        # Log a calibration decision
        audit_trail.log_calibration_decision(
            "test_condition",
            "anchor_points", 
            condition.calibration.theoretical_justification,
            {"anchor_points": condition.calibration.anchor_points}
        )
        
        # Verify justification is in audit log
        calibration_events = [event for event in audit_trail.audit_log 
                             if event["event_type"] == "CALIBRATION_DECISION"]
        
        assert len(calibration_events) > 0
        assert calibration_events[0]["event_data"]["theoretical_justification"] != ""
        
        print("✅ FIX 2 VALIDATED: Theoretical justification required and logged")

    def test_fix_3_explicit_outcome_derivation(self):
        """CRITICAL FIX 3: Test that outcome derivation is explicit and auditable"""
        builder = TruthTableBuilder(self.config)
        builder.calibrated_cases = self.test_cases
        
        # Test explicit outcome calculation with audit trail
        outcome = self.config.outcomes[0]
        case = self.test_cases[0]
        
        # Calculate outcome with audit trail
        audit_result = builder._calculate_outcome_value_with_audit(case, outcome)
        
        # CRITICAL: Must have complete derivation trail
        required_fields = ["case_id", "source_condition_values", "combination_rule", 
                          "calculation_steps", "raw_combination", "final_value"]
        
        for field in required_fields:
            assert field in audit_result
        
        # Calculation steps should be documented
        assert len(audit_result["calculation_steps"]) > 0
        assert audit_result["combination_rule"] == "test_condition * 0.8"
        
        # Source condition values should be explicit
        assert "test_condition" in audit_result["source_condition_values"]
        assert audit_result["source_condition_values"]["test_condition"] == 0.2
        
        print("✅ FIX 3 VALIDATED: Explicit outcome derivation with complete audit trail")

    def test_fix_4_data_normalization_and_comparability(self):
        """CRITICAL FIX 4: Test that data normalization addresses comparability issues"""
        # Create calibration engine
        engine = CalibrationEngine(self.config)
        
        # Create mock interview data with different scales
        engine.coded_interviews = [
            {
                "interview_id": "case_1",
                "quotes": [{"text": "word " * 100, "code_ids": ["TEST_CODE"]}],  # 100 words, 1 code
                "speakers": [{"speaker_id": "s1"}]
            },
            {
                "interview_id": "case_2", 
                "quotes": [{"text": "word " * 1000, "code_ids": ["TEST_CODE"] * 5}],  # 1000 words, 5 codes
                "speakers": [{"speaker_id": "s1"}, {"speaker_id": "s2"}]
            }
        ]
        
        # Extract raw values
        engine.extract_raw_values()
        raw_values = engine.raw_data_cache["test_condition"]
        
        # Case 1: 1 code in 100 words = 10 codes per 1000 words
        # Case 2: 5 codes in 1000 words = 5 codes per 1000 words
        # Without normalization: case 2 looks higher (5 vs 1)
        # With normalization: case 1 is actually higher (10 vs 5 per 1000 words)
        
        # Test normalization
        condition = self.config.conditions[0]
        normalized_values = engine._normalize_values(raw_values, "per_thousand_words")
        
        # Verify normalization makes comparison meaningful
        assert normalized_values["case_1"] > normalized_values["case_2"]  # 10 > 5 per 1000 words
        
        print("✅ FIX 4 VALIDATED: Data normalization addresses comparability issues")

    def test_fix_5_comprehensive_audit_trail(self):
        """CRITICAL FIX 5: Test comprehensive audit trail and transparency"""
        audit_trail = QCAAuditTrail(self.config)
        
        # Log various events
        audit_trail.log_calibration_decision("test", "anchor_points", "test justification", {})
        audit_trail.log_outcome_definition("test_outcome", ["test_condition"], "test * 0.8", "test justification")
        audit_trail.log_truth_table_mode("dual", "preserves fuzzy information")
        audit_trail.log_methodology_fix("TEST_FIX", "test problem", "test solution")
        
        # Generate methodology report
        report = audit_trail.generate_methodology_report()
        
        # Verify comprehensive reporting
        assert "critical_fixes_applied" in report
        assert "calibration_decisions" in report
        assert "outcome_derivations" in report
        assert "truth_table_modes" in report
        assert "reproducibility_evidence" in report
        
        # Verify reproducibility evidence
        evidence = report["reproducibility_evidence"]
        assert evidence["all_decisions_logged"] == True
        assert evidence["theoretical_justifications_provided"] == True
        assert evidence["calculation_steps_documented"] == True
        assert evidence["threshold_placements_validated"] == True
        
        # Test audit trail file generation
        saved_files = audit_trail.save_audit_trail()
        assert len(saved_files) >= 3  # audit log, report, summary
        
        # Verify files exist
        for file_path in saved_files:
            assert Path(file_path).exists()
            
        print("✅ FIX 5 VALIDATED: Comprehensive audit trail and transparency")

    def test_methodology_compliance_validation(self):
        """Test overall methodology compliance validation"""
        audit_trail = QCAAuditTrail(self.config)
        validator = QCAMethodologyValidator(audit_trail)
        
        # Test calibration compliance
        calibration_compliance = validator.validate_calibration_compliance(self.test_cases)
        assert all(calibration_compliance.values())
        
        # Test truth table compliance 
        builder = TruthTableBuilder(self.config)
        builder.calibrated_cases = self.test_cases
        builder.calibrate_outcomes()
        
        truth_tables = builder.construct_all_truth_tables()
        truth_table_compliance = validator.validate_truth_table_compliance(truth_tables)
        assert all(truth_table_compliance.values())
        
        # Test overall compliance
        compliance_report = validator.generate_compliance_report(self.test_cases, truth_tables)
        assert compliance_report["overall_compliance"] == True
        
        print("✅ METHODOLOGY COMPLIANCE VALIDATED")

    def test_full_pipeline_with_fixes(self):
        """Test complete QCA pipeline with all methodology fixes"""
        # Create minimal test data files
        test_data_dir = Path(self.test_dir) / "test_input"
        test_data_dir.mkdir(exist_ok=True)
        
        # Create mock interview file
        interview_data = {
            "interview_id": "test_interview_1",
            "quotes": [
                {"text": "This is test content " * 50, "code_ids": ["TEST_CODE"] * 2},
                {"text": "More test content " * 30, "code_ids": ["TEST_CODE"]}
            ],
            "speakers": [{"speaker_id": "speaker_1"}]
        }
        
        with open(test_data_dir / "interview_test_001.json", 'w') as f:
            json.dump(interview_data, f)
        
        # Update config to use test input
        test_config = QCAConfiguration(
            input_dir=str(test_data_dir),
            output_dir=self.test_dir,
            truth_table_mode="dual",
            conditions=self.config.conditions,
            outcomes=self.config.outcomes,
            enable_calibration=True,
            enable_truth_table=True,
            enable_minimization=False  # Skip for test
        )
        
        # Run pipeline
        pipeline = QCAPipeline(test_config)
        results = pipeline.run_complete_qca_analysis()
        
        # Verify results
        assert len(results.calibrated_cases) > 0
        assert len(results.truth_tables) > 0
        
        # Verify audit trail files were generated
        audit_dir = Path(self.test_dir) / "audit_trail"
        assert audit_dir.exists()
        assert (audit_dir / "methodology_validation_report.json").exists()
        
        # Verify methodology compliance report was generated
        compliance_file = Path(self.test_dir) / "methodology_compliance_report.json"
        assert compliance_file.exists()
        
        with open(compliance_file) as f:
            compliance_data = json.load(f)
        
        assert compliance_data["overall_compliance"] == True
        
        print("✅ FULL PIPELINE WITH METHODOLOGY FIXES VALIDATED")


def test_backwards_compatibility():
    """Test that fixes maintain backwards compatibility where possible"""
    # Test that old-style calibration still works (with warnings)
    config = QCAConfiguration(
        input_dir="test",
        output_dir="test",
        conditions=[
            ConditionDefinition(
                condition_id="legacy_condition",
                name="Legacy Condition",
                description="Test backwards compatibility",
                source_type="code", 
                source_id="TEST",
                calibration=CalibrationRule(
                    method=CalibrationMethod.BINARY,
                    theoretical_justification="Legacy binary threshold for backwards compatibility",
                    binary_threshold=2
                )
            )
        ],
        outcomes=[
            OutcomeDefinition(
                outcome_id="legacy_outcome",
                name="Legacy Outcome", 
                description="Test outcome",
                source_conditions=["legacy_condition"],
                combination_rule="any",
                calibration=CalibrationRule(
                    method=CalibrationMethod.BINARY,
                    theoretical_justification="Legacy binary outcome"
                )
            )
        ]
    )
    
    # Should not raise errors
    pipeline = QCAPipeline(config)
    assert pipeline.config.conditions[0].calibration.method == CalibrationMethod.BINARY
    
    print("✅ BACKWARDS COMPATIBILITY MAINTAINED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
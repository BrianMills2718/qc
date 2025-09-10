"""
QCA Analysis Pipeline - Main Orchestrator
Coordinates all QCA phases: Calibration → Truth Tables → Minimization
"""
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from .qca_schemas import QCAConfiguration, QCAResults, CalibratedCase, TruthTable
from .calibration_engine import CalibrationEngine
from .truth_table_builder import TruthTableBuilder
from .minimization_engine import MinimizationEngine
from .audit_trail_system import QCAAuditTrail, QCAMethodologyValidator

logger = logging.getLogger(__name__)

class QCAPipeline:
    """Main QCA analysis pipeline orchestrator"""
    
    def __init__(self, config: QCAConfiguration):
        self.config = config
        self.calibration_engine = CalibrationEngine(config)
        self.truth_table_builder = TruthTableBuilder(config)
        self.minimization_engine = MinimizationEngine(config)
        
        # CRITICAL FIX: Initialize audit trail system
        self.audit_trail = QCAAuditTrail(config)
        self.methodology_validator = QCAMethodologyValidator(self.audit_trail)
        
        # Log methodology fixes applied
        self._log_methodology_fixes()
        
        # Results storage
        self.calibrated_cases: List[CalibratedCase] = []
        self.truth_tables: List[TruthTable] = []
        self.generated_files: List[str] = []
    
    def validate_configuration(self) -> bool:
        """Validate QCA configuration before running analysis"""
        logger.info("Validating QCA configuration")
        
        # Check input directory exists
        if not Path(self.config.input_dir).exists():
            logger.error(f"Input directory does not exist: {self.config.input_dir}")
            return False
        
        # Check that conditions are defined
        if not self.config.conditions:
            logger.error("No conditions defined for QCA analysis")
            return False
        
        # Check that outcomes are defined
        if not self.config.outcomes:
            logger.error("No outcomes defined for QCA analysis")
            return False
        
        # Validate condition definitions
        for condition in self.config.conditions:
            if not condition.source_id:
                logger.error(f"Condition {condition.condition_id} missing source_id")
                return False
        
        # Validate outcome definitions
        for outcome in self.config.outcomes:
            if not outcome.source_conditions:
                logger.error(f"Outcome {outcome.outcome_id} has no source conditions")
                return False
        
        logger.info("QCA configuration validation passed")
        return True
    
    def _log_methodology_fixes(self) -> None:
        """CRITICAL FIX: Log all methodology fixes applied to address QCA violations"""
        
        # Fix 1: Dual-mode truth tables preserve fuzzy information
        self.audit_trail.log_methodology_fix(
            "DUAL_MODE_TRUTH_TABLES",
            "Information Loss: Fuzzy membership scores (0.5) converted to binary (1.0) in truth tables",
            "Implemented dual-mode system preserving both fuzzy and crisp representations"
        )
        
        # Fix 2: Theoretically grounded calibration
        self.audit_trail.log_methodology_fix(
            "THEORETICALLY_GROUNDED_CALIBRATION",
            "Arbitrary Calibration: Thresholds like 'binary_threshold: 2' have no theoretical grounding",
            "Required theoretical justification for all calibration decisions with multiple strategies"
        )
        
        # Fix 3: Explicit outcome definition
        self.audit_trail.log_methodology_fix(
            "EXPLICIT_OUTCOME_DERIVATION",
            "Broken Outcome Logic: Outcomes appear mysteriously without clear derivation",
            "Complete audit trail for outcome calculation with step-by-step documentation"
        )
        
        # Fix 4: Data normalization
        self.audit_trail.log_methodology_fix(
            "DATA_NORMALIZATION",
            "Incomparable Data: Raw counts not normalized (28 mentions vs 1 mention across interviews)",
            "Implemented normalization methods: per-1000-words, per-speaker, per-quote"
        )
        
        # Fix 5: Comprehensive audit trail
        self.audit_trail.log_methodology_fix(
            "COMPREHENSIVE_AUDIT_TRAIL", 
            "Opaque Calculations: No audit trail for how membership scores are derived",
            "Full transparency and reproducibility with complete calculation documentation"
        )
        
        # Log truth table mode choice
        mode_rationale = {
            "dual": "Preserves fuzzy information while enabling crisp analysis",
            "fuzzy": "Maintains full membership score information throughout analysis", 
            "crisp": "Enables Boolean minimization for traditional QCA approaches"
        }
        
        self.audit_trail.log_truth_table_mode(
            self.config.truth_table_mode,
            mode_rationale.get(self.config.truth_table_mode, "Custom mode configuration")
        )
    
    def run_phase_qca1_calibration(self) -> List[CalibratedCase]:
        """Run Phase QCA-1: Code to Set Membership Calibration"""
        if not self.config.enable_calibration:
            logger.info("Phase QCA-1 disabled in configuration")
            return []
        
        logger.info("=" * 60)
        logger.info("PHASE QCA-1: CODE TO SET MEMBERSHIP CALIBRATION")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        try:
            self.calibrated_cases = self.calibration_engine.run_calibration_phase()
            
            elapsed_time = time.time() - start_time
            logger.info(f"Phase QCA-1 completed in {elapsed_time:.1f} seconds")
            logger.info(f"Calibrated {len(self.calibrated_cases)} cases with {len(self.config.conditions)} conditions")
            
            return self.calibrated_cases
            
        except Exception as e:
            logger.error(f"Phase QCA-1 failed: {e}")
            raise
    
    def run_phase_qca2_truth_tables(self) -> List[TruthTable]:
        """Run Phase QCA-2: Truth Table Construction"""
        if not self.config.enable_truth_table:
            logger.info("Phase QCA-2 disabled in configuration")
            return []
        
        logger.info("=" * 60)
        logger.info("PHASE QCA-2: TRUTH TABLE CONSTRUCTION")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        try:
            self.truth_tables = self.truth_table_builder.run_truth_table_phase(self.calibrated_cases)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Phase QCA-2 completed in {elapsed_time:.1f} seconds")
            logger.info(f"Constructed {len(self.truth_tables)} truth tables for {len(self.config.outcomes)} outcomes")
            
            return self.truth_tables
            
        except Exception as e:
            logger.error(f"Phase QCA-2 failed: {e}")
            raise
    
    def run_phase_qca3_minimization(self) -> List[str]:
        """Run Phase QCA-3: Boolean Minimization Integration"""
        if not self.config.enable_minimization:
            logger.info("Phase QCA-3 disabled in configuration")
            return []
        
        logger.info("=" * 60)
        logger.info("PHASE QCA-3: BOOLEAN MINIMIZATION INTEGRATION")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        try:
            generated_files = self.minimization_engine.run_minimization_phase(self.truth_tables)
            self.generated_files.extend(generated_files)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Phase QCA-3 completed in {elapsed_time:.1f} seconds")
            logger.info(f"Generated {len(generated_files)} files for external QCA analysis")
            
            return generated_files
            
        except Exception as e:
            logger.error(f"Phase QCA-3 failed: {e}")
            raise
    
    def generate_final_results(self) -> QCAResults:
        """Generate comprehensive QCA analysis results with methodology validation"""
        logger.info("Generating final QCA analysis results")
        
        # CRITICAL FIX: Generate methodology compliance validation
        compliance_report = self.methodology_validator.generate_compliance_report(
            self.calibrated_cases, self.truth_tables
        )
        
        # Save audit trail
        audit_files = self.audit_trail.save_audit_trail()
        self.generated_files.extend(audit_files)
        
        # Count generated files by type
        csv_files = [f for f in self.generated_files if f.endswith('.csv')]
        json_files = [f for f in self.generated_files if f.endswith('.json')]
        r_scripts = [f for f in self.generated_files if f.endswith('.R')]
        
        results = QCAResults(
            configuration=self.config,
            calibrated_cases=self.calibrated_cases,
            truth_tables=self.truth_tables,
            total_cases_analyzed=len(self.calibrated_cases),
            conditions_analyzed=len(self.config.conditions),
            outcomes_analyzed=len(self.config.outcomes),
            csv_files=csv_files,
            json_files=json_files,
            r_scripts=r_scripts
        )
        
        # Save final results
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results_file = output_path / "qca_analysis_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(results.model_dump(), f, indent=2)
        
        # Save methodology compliance report
        compliance_file = output_path / "methodology_compliance_report.json"
        with open(compliance_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(compliance_report, f, indent=2)
        
        logger.info(f"Final QCA results saved to: {results_file}")
        logger.info(f"Methodology compliance report saved to: {compliance_file}")
        
        # Log compliance status
        if compliance_report["overall_compliance"]:
            logger.info("✅ QCA METHODOLOGY COMPLIANCE: PASSED")
        else:
            logger.warning("⚠️ QCA METHODOLOGY COMPLIANCE: ISSUES DETECTED")
        
        return results
    
    def run_complete_qca_analysis(self) -> QCAResults:
        """Run complete QCA analysis pipeline"""
        logger.info("=" * 80)
        logger.info("STARTING COMPLETE QCA ANALYSIS PIPELINE")
        logger.info("=" * 80)
        
        overall_start_time = time.time()
        
        # Validate configuration
        if not self.validate_configuration():
            raise ValueError("QCA configuration validation failed")
        
        try:
            # Phase QCA-1: Calibration
            self.run_phase_qca1_calibration()
            
            # Phase QCA-2: Truth Tables
            self.run_phase_qca2_truth_tables()
            
            # Phase QCA-3: Minimization
            self.run_phase_qca3_minimization()
            
            # Generate final results
            results = self.generate_final_results()
            
            # Summary
            total_elapsed = time.time() - overall_start_time
            logger.info("=" * 80)
            logger.info("QCA ANALYSIS PIPELINE COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Total execution time: {total_elapsed:.1f} seconds")
            logger.info(f"Cases analyzed: {len(self.calibrated_cases)}")
            logger.info(f"Conditions: {len(self.config.conditions)}")
            logger.info(f"Outcomes: {len(self.config.outcomes)}")
            logger.info(f"Truth tables: {len(self.truth_tables)}")
            logger.info(f"Files generated: {len(self.generated_files)}")
            logger.info("=" * 80)
            
            return results
            
        except Exception as e:
            logger.error(f"QCA analysis pipeline failed: {e}")
            raise

def load_qca_config_from_yaml(config_file: str) -> QCAConfiguration:
    """Load QCA configuration from YAML file"""
    import yaml
    from pathlib import Path
    
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"QCA config file not found: {config_file}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    # Convert to QCA configuration
    qca_config = QCAConfiguration(**config_data)
    
    logger.info(f"Loaded QCA configuration from: {config_file}")
    logger.info(f"Conditions: {len(qca_config.conditions)}")
    logger.info(f"Outcomes: {len(qca_config.outcomes)}")
    
    return qca_config

def run_qca_from_config_file(config_file: str) -> QCAResults:
    """Run QCA analysis from configuration file"""
    # Load configuration
    qca_config = load_qca_config_from_yaml(config_file)
    
    # Create and run pipeline
    pipeline = QCAPipeline(qca_config)
    results = pipeline.run_complete_qca_analysis()
    
    return results
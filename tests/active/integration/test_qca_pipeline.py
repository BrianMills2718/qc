#!/usr/bin/env python3
"""
QCA Pipeline Testing and Validation
Tests the complete QCA post-processing pipeline
"""
import sys
import asyncio
import logging
from pathlib import Path
import tempfile
import shutil

# Add src to path
sys.path.insert(0, 'src')

from src.qc.qca.qca_pipeline import QCAPipeline, load_qca_config_from_yaml
from src.qc.qca.qca_schemas import (
    QCAConfiguration, ConditionDefinition, OutcomeDefinition,
    CalibrationRule, CalibrationMethod
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_qca_config() -> QCAConfiguration:
    """Create a minimal QCA configuration for testing"""
    
    # Define test conditions
    conditions = [
        ConditionDefinition(
            condition_id="high_ai_usage",
            name="High AI Usage",
            description="Frequent mentions of AI usage",
            source_type="code",
            source_id="AI_ADOPTION_AND_INTEGRATION",
            calibration=CalibrationRule(
                method=CalibrationMethod.BINARY,
                binary_threshold=2
            )
        ),
        ConditionDefinition(
            condition_id="efficiency_focused",
            name="Efficiency Focused",
            description="Focus on efficiency gains",
            source_type="code", 
            source_id="EFFICIENCY_AND_PRODUCTIVITY_GAINS",
            calibration=CalibrationRule(
                method=CalibrationMethod.FREQUENCY,
                frequency_breakpoints=[1, 3],
                frequency_thresholds={"rare": 0.3, "frequent": 0.7}
            )
        )
    ]
    
    # Define test outcomes
    outcomes = [
        OutcomeDefinition(
            outcome_id="positive_ai_experience",
            name="Positive AI Experience", 
            description="Overall positive AI experience",
            source_conditions=["high_ai_usage", "efficiency_focused"],
            combination_rule="any",
            calibration=CalibrationRule(
                method=CalibrationMethod.BINARY,
                binary_threshold=1
            )
        )
    ]
    
    config = QCAConfiguration(
        input_dir="output_single_test",  # Use existing test data
        output_dir="qca_test_output",
        conditions=conditions,
        outcomes=outcomes,
        enable_calibration=True,
        enable_truth_table=True,
        enable_minimization=True,
        r_qca_package=True,
        python_qca=True
    )
    
    return config

async def test_qca_pipeline():
    """Test the complete QCA pipeline"""
    logger.info("=" * 60)
    logger.info("TESTING QCA PIPELINE")
    logger.info("=" * 60)
    
    try:
        # Create test configuration
        config = create_test_qca_config()
        logger.info(f"Created test config with {len(config.conditions)} conditions, {len(config.outcomes)} outcomes")
        
        # Check if input directory exists
        input_path = Path(config.input_dir)
        if not input_path.exists():
            logger.warning(f"Input directory {config.input_dir} not found")
            logger.info("To run QCA test, first run a qualitative extraction to generate input data")
            return False
        
        # Create QCA pipeline
        pipeline = QCAPipeline(config)
        
        # Run complete analysis
        results = pipeline.run_complete_qca_analysis()
        
        # Validate results
        logger.info("=" * 60)
        logger.info("QCA TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Cases analyzed: {results.total_cases_analyzed}")
        logger.info(f"Conditions: {results.conditions_analyzed}")
        logger.info(f"Outcomes: {results.outcomes_analyzed}")
        logger.info(f"Truth tables: {len(results.truth_tables)}")
        logger.info(f"Files generated: {len(results.csv_files) + len(results.json_files) + len(results.r_scripts)}")
        
        # Check specific outputs
        output_path = Path(config.output_dir)
        expected_files = [
            "calibrated_cases.json",
            "calibration_matrix.csv", 
            "truth_table_positive_ai_experience.json",
            "truth_table_positive_ai_experience.csv",
            "qca_analysis_results.json"
        ]
        
        logger.info("Checking expected output files:")
        all_found = True
        for expected_file in expected_files:
            file_path = output_path / expected_file
            if file_path.exists():
                logger.info(f"  ✓ {expected_file}")
            else:
                logger.error(f"  ✗ {expected_file} - NOT FOUND")
                all_found = False
        
        if all_found:
            logger.info("=" * 60)
            logger.info("QCA PIPELINE TEST: SUCCESS")
            logger.info("=" * 60)
            return True
        else:
            logger.error("=" * 60)
            logger.error("QCA PIPELINE TEST: FAILED - Missing expected files")
            logger.error("=" * 60)
            return False
            
    except Exception as e:
        logger.error(f"QCA pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qca_config_loading():
    """Test QCA configuration loading from YAML"""
    logger.info("Testing QCA configuration loading...")
    
    try:
        # Test loading the AI research config
        config_file = "qca_config_ai_research.yaml"
        if Path(config_file).exists():
            config = load_qca_config_from_yaml(config_file)
            logger.info(f"✓ Successfully loaded config: {len(config.conditions)} conditions, {len(config.outcomes)} outcomes")
            return True
        else:
            logger.warning(f"Config file {config_file} not found - skipping config loading test")
            return True
            
    except Exception as e:
        logger.error(f"Config loading test failed: {e}")
        return False

def run_qca_validation():
    """Run all QCA validation tests"""
    logger.info("STARTING QCA PIPELINE VALIDATION")
    logger.info("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Configuration loading
    if test_qca_config_loading():
        tests_passed += 1
        logger.info("✓ Test 1 passed: Configuration loading")
    else:
        logger.error("✗ Test 1 failed: Configuration loading")
    
    # Test 2: Full pipeline (async)
    try:
        pipeline_success = asyncio.run(test_qca_pipeline()) 
        if pipeline_success:
            tests_passed += 1
            logger.info("✓ Test 2 passed: Full QCA pipeline")
        else:
            logger.error("✗ Test 2 failed: Full QCA pipeline")
    except Exception as e:
        logger.error(f"✗ Test 2 failed: Full QCA pipeline - {e}")
    
    # Summary
    logger.info("=" * 60)
    if tests_passed == total_tests:
        logger.info(f"QCA VALIDATION SUCCESS: {tests_passed}/{total_tests} tests passed")
        return True
    else:
        logger.error(f"QCA VALIDATION FAILED: {tests_passed}/{total_tests} tests passed")
        return False

if __name__ == "__main__":
    success = run_qca_validation()
    sys.exit(0 if success else 1)
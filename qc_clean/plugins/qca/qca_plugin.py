#!/usr/bin/env python3
"""
QCA Analysis Plugin Implementation

This plugin provides Qualitative Comparative Analysis (QCA) functionality 
as an optional extension to the core GT workflow.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from plugins.base import QCAPlugin, PluginStatus
from .qca_engine import QCAEngine, QCAConfiguration, QCAResults

logger = logging.getLogger(__name__)


class QCAAnalysisPlugin(QCAPlugin):
    """QCA Analysis Plugin Implementation"""
    
    def __init__(self):
        super().__init__()
        self.qca_engine: Optional[QCAEngine] = None
        self.current_config: Optional[QCAConfiguration] = None
        self._logger = logging.getLogger(f"{__name__}.QCAAnalysisPlugin")
    
    def get_name(self) -> str:
        """Return plugin name"""
        return "qca_analysis"
    
    def get_version(self) -> str:
        """Return plugin version"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return plugin description"""
        return "Qualitative Comparative Analysis (QCA) post-processing for GT results"
    
    def get_dependencies(self) -> List[str]:
        """Return plugin dependencies"""
        return ["core.workflow.grounded_theory"]
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize QCA plugin with configuration"""
        try:
            self._logger.info("Initializing QCA Analysis plugin...")
            
            # Store configuration
            self._config = config
            
            # Extract QCA-specific settings
            qca_config = QCAConfiguration(
                enable_qca_conversion=config.get('enable_qca_conversion', True),
                default_analysis_method=config.get('default_analysis_method', 'crisp_set'),
                calibration_method=config.get('calibration_method', 'binary'),
                truth_table_consistency_threshold=config.get('consistency_threshold', 0.8),
                truth_table_frequency_threshold=config.get('frequency_threshold', 1),
                generate_minimization=config.get('generate_minimization', True),
                output_format=config.get('output_format', 'standard')
            )
            
            # Initialize QCA engine
            self.qca_engine = QCAEngine(qca_config)
            self.current_config = qca_config
            
            self.status = PluginStatus.INITIALIZED
            self._logger.info("QCA Analysis plugin initialized successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to initialize QCA plugin: {e}")
            self.status = PluginStatus.ERROR
            return False
    
    def is_available(self) -> bool:
        """Check if QCA plugin dependencies are available"""
        try:
            # Check for required dependencies
            import pandas as pd
            import numpy as np
            
            # Check for optional QCA libraries
            try:
                # Try to import QCA-specific libraries if available
                pass  # For now, we'll implement basic QCA functionality
            except ImportError:
                self._logger.warning("Advanced QCA libraries not available, using basic implementation")
            
            return True
            
        except ImportError as e:
            self._logger.error(f"Required dependencies not available: {e}")
            return False
    
    def can_process(self, gt_results: Dict[str, Any]) -> bool:
        """Check if GT results can be converted to QCA"""
        try:
            # Check if we have the required GT results structure
            required_keys = ['codes', 'interviews', 'hierarchy']
            
            for key in required_keys:
                if key not in gt_results:
                    self._logger.warning(f"Missing required GT result key: {key}")
                    return False
            
            # Check if we have sufficient codes for QCA
            codes = gt_results.get('codes', [])
            if len(codes) < 2:
                self._logger.warning("Insufficient codes for QCA analysis (minimum 2 required)")
                return False
            
            # Check if we have cases (interviews) 
            interviews = gt_results.get('interviews', [])
            if len(interviews) < 3:
                self._logger.warning("Insufficient cases for QCA analysis (minimum 3 recommended)")
                return False
            
            self._logger.info(f"GT results can be processed: {len(codes)} codes, {len(interviews)} cases")
            return True
            
        except Exception as e:
            self._logger.error(f"Error checking GT results compatibility: {e}")
            return False
    
    def convert_to_qca(self, gt_results: Dict[str, Any]) -> Dict[str, Any]:
        """Convert GT codes to QCA conditions/outcomes"""
        if not self.qca_engine:
            raise RuntimeError("QCA plugin not initialized")
        
        try:
            self._logger.info("Converting GT results to QCA format...")
            
            # Extract GT data
            codes = gt_results.get('codes', [])
            interviews = gt_results.get('interviews', [])
            hierarchy = gt_results.get('hierarchy', {})
            
            # Identify potential conditions and outcomes
            conditions = []
            potential_outcomes = []
            
            # Process codes - use hierarchical structure if available
            for code in codes:
                code_info = {
                    'name': code.get('name', ''),
                    'description': code.get('description', ''),
                    'frequency': code.get('frequency', 0),
                    'level': code.get('level', 0),
                    'parent_id': code.get('parent_id', None),
                    'applications': code.get('applications', [])
                }
                
                # Determine if code should be condition or outcome
                # Higher level codes or core categories might be outcomes
                if code_info['level'] == 0 or 'core' in code_info['name'].lower():
                    potential_outcomes.append(code_info)
                else:
                    conditions.append(code_info)
            
            # If no clear outcomes identified, use most frequent codes as outcomes
            if not potential_outcomes and conditions:
                # Sort by frequency and take top codes as potential outcomes
                sorted_codes = sorted(conditions, key=lambda x: x['frequency'], reverse=True)
                potential_outcomes = sorted_codes[:min(2, len(sorted_codes)//2)]
                conditions = [c for c in conditions if c not in potential_outcomes]
            
            # Create case matrix
            case_matrix = []
            for interview in interviews:
                case_id = interview.get('id', interview.get('name', 'unknown'))
                case_row = {'case_id': case_id}
                
                # For each condition, check if it appears in this interview
                for condition in conditions:
                    condition_name = condition['name']
                    # Check if this condition/code was applied to this interview
                    applied = self._check_code_applied_to_interview(condition, interview, gt_results)
                    case_row[condition_name] = 1 if applied else 0
                
                # For each potential outcome
                for outcome in potential_outcomes:
                    outcome_name = f"outcome_{outcome['name']}"
                    applied = self._check_code_applied_to_interview(outcome, interview, gt_results)
                    case_row[outcome_name] = 1 if applied else 0
                
                case_matrix.append(case_row)
            
            qca_data = {
                'case_matrix': case_matrix,
                'conditions': [c['name'] for c in conditions],
                'outcomes': [f"outcome_{o['name']}" for o in potential_outcomes],
                'condition_descriptions': {c['name']: c['description'] for c in conditions},
                'outcome_descriptions': {f"outcome_{o['name']}": o['description'] for o in potential_outcomes},
                'conversion_metadata': {
                    'total_gt_codes': len(codes),
                    'conditions_identified': len(conditions),
                    'outcomes_identified': len(potential_outcomes),
                    'cases_processed': len(interviews),
                    'conversion_method': 'hierarchical_frequency_based'
                }
            }
            
            self._logger.info(f"Converted GT to QCA: {len(conditions)} conditions, {len(potential_outcomes)} outcomes, {len(case_matrix)} cases")
            return qca_data
            
        except Exception as e:
            self._logger.error(f"Error converting GT results to QCA: {e}")
            raise
    
    def run_qca_analysis(self, qca_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute QCA analysis pipeline"""
        if not self.qca_engine:
            raise RuntimeError("QCA plugin not initialized")
        
        try:
            self._logger.info("Running QCA analysis...")
            
            # Run the QCA analysis using our engine
            results = self.qca_engine.run_analysis(qca_data)
            
            # Add plugin metadata
            results['plugin_metadata'] = {
                'plugin_name': self.get_name(),
                'plugin_version': self.get_version(),
                'analysis_timestamp': results.get('analysis_metadata', {}).get('timestamp'),
                'configuration_used': self.current_config.to_dict() if self.current_config else {}
            }
            
            self._logger.info("QCA analysis completed successfully")
            return results
            
        except Exception as e:
            self._logger.error(f"Error running QCA analysis: {e}")
            raise
    
    def _check_code_applied_to_interview(self, code: Dict[str, Any], interview: Dict[str, Any], gt_results: Dict[str, Any]) -> bool:
        """Check if a code was applied to a specific interview"""
        try:
            code_name = code['name']
            interview_id = interview.get('id', interview.get('name'))
            
            # Check in code applications if available
            applications = code.get('applications', [])
            for app in applications:
                if app.get('interview_id') == interview_id or app.get('source') == interview_id:
                    return True
            
            # Fallback: check if code appears in interview content or metadata
            interview_content = str(interview.get('content', '')).lower()
            if code_name.lower() in interview_content:
                return True
            
            return False
            
        except Exception as e:
            self._logger.warning(f"Error checking code application: {e}")
            return False
    
    def cleanup(self) -> bool:
        """Cleanup QCA plugin resources"""
        try:
            self._logger.info("Cleaning up QCA plugin resources...")
            
            if self.qca_engine:
                # Clean up QCA engine resources if needed
                self.qca_engine = None
            
            self.current_config = None
            self.status = PluginStatus.DISABLED
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error during QCA plugin cleanup: {e}")
            return False
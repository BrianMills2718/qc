#!/usr/bin/env python3
"""
Audit Trail for GT Analysis - Minimal Implementation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class AnalysisStep:
    """Represents a step in the analysis process"""
    
    def __init__(self, step_name: str, description: str, data: Dict[str, Any] = None):
        self.step_name = step_name
        self.description = description
        self.timestamp = datetime.now().isoformat()
        self.data = data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_name': self.step_name,
            'description': self.description,
            'timestamp': self.timestamp,
            'data': self.data
        }

class GTAuditTrail:
    """Audit trail for Grounded Theory analysis"""
    
    def __init__(self, methodology: str = "grounded_theory", analysis_config: Dict[str, Any] = None, 
                 start_time: str = None, input_summary: Dict[str, Any] = None):
        self.methodology = methodology
        self.analysis_config = analysis_config or {}
        self.input_summary = input_summary or {}
        self.steps: List[AnalysisStep] = []
        self.started_at = start_time or datetime.now().isoformat()
    
    def add_step(self, step_name: str = None, description: str = None, data: Dict[str, Any] = None, 
                 step: str = None, input_summary: Dict[str, Any] = None, 
                 output_summary: Dict[str, Any] = None, metadata: Dict[str, Any] = None):
        """Add a step to the audit trail"""
        # Support both calling conventions
        name = step_name or step or "unknown_step"
        desc = description or "No description provided"
        
        # Combine all data into single dictionary
        combined_data = data or {}
        if input_summary:
            combined_data['input_summary'] = input_summary
        if output_summary:
            combined_data['output_summary'] = output_summary
        if metadata:
            combined_data['metadata'] = metadata
            
        analysis_step = AnalysisStep(name, desc, combined_data)
        self.steps.append(analysis_step)
        logger.info(f"Audit: {name} - {desc}")
    
    def finalize_workflow(self, final_summary: Dict[str, Any] = None):
        """Finalize the workflow with summary information"""
        self.final_summary = final_summary or {}
        self.finished_at = datetime.now().isoformat()
        logger.info("Audit trail finalized")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get audit trail summary"""
        return {
            'methodology': self.methodology,
            'started_at': self.started_at,
            'total_steps': len(self.steps),
            'steps': [step.to_dict() for step in self.steps]
        }
    
    def export_to_file(self, filepath: str):
        """Export audit trail to file"""
        with open(filepath, 'w') as f:
            json.dump(self.get_summary(), f, indent=2)
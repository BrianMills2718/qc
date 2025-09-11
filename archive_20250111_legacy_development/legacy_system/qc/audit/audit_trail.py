#!/usr/bin/env python3
"""
Audit Trail System for Autonomous Research

Provides complete transparency of AI decision-making for research validation.
Captures every analysis step, reasoning process, and configuration used
to ensure reproducibility and methodological rigor.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class AnalysisStep:
    """Represents a single step in the analysis process"""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    step_name: str = ""                    # "open_coding", "axial_coding", etc.
    timestamp: datetime = field(default_factory=datetime.now)
    input_data_summary: Dict[str, Any] = field(default_factory=dict)  # Summary of input (not full data)
    configuration_used: Dict[str, Any] = field(default_factory=dict)  # Config parameters for this step
    llm_prompt: str = ""                   # Exact prompt sent to LLM
    llm_response: Dict[str, Any] = field(default_factory=dict)  # Structured LLM response
    decision_rationale: str = ""           # Why this analysis approach was chosen
    alternatives_considered: List[str] = field(default_factory=list)  # Other approaches considered
    confidence_metrics: Dict[str, float] = field(default_factory=dict)  # Confidence scores
    output_summary: Dict[str, Any] = field(default_factory=dict)  # Summary of step output
    execution_time_seconds: float = 0.0   # Time taken for this step
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper datetime serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class GTAuditTrail:
    """Complete audit trail for Grounded Theory analysis"""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    methodology: str = "grounded_theory"
    analysis_config: Optional[Dict[str, Any]] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    input_summary: Dict[str, Any] = field(default_factory=dict)
    steps: List[AnalysisStep] = field(default_factory=list)
    final_results_summary: Dict[str, Any] = field(default_factory=dict)
    total_execution_time: float = 0.0
    
    def add_step(self, step: AnalysisStep) -> str:
        """Add an analysis step to the audit trail"""
        self.steps.append(step)
        logger.info(f"Audit trail: Added step '{step.step_name}' ({step.step_id})")
        return step.step_id
    
    def finalize_workflow(self, final_results: Dict[str, Any]) -> None:
        """Finalize the workflow with end time and results"""
        self.end_time = datetime.now()
        self.total_execution_time = (self.end_time - self.start_time).total_seconds()
        self.final_results_summary = final_results
        logger.info(f"Audit trail finalized: {len(self.steps)} steps, {self.total_execution_time:.2f}s total")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper datetime serialization"""
        return {
            'workflow_id': self.workflow_id,
            'methodology': self.methodology,
            'analysis_config': self.analysis_config,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'input_summary': self.input_summary,
            'steps': [step.to_dict() for step in self.steps],
            'final_results_summary': self.final_results_summary,
            'total_execution_time': self.total_execution_time
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def export_audit_report(self) -> str:
        """Generate human-readable audit report"""
        report_lines = [
            "GROUNDED THEORY ANALYSIS - AUDIT TRAIL REPORT",
            "=" * 50,
            f"Workflow ID: {self.workflow_id}",
            f"Analysis Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Analysis End: {self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else 'In Progress'}",
            f"Total Duration: {self.total_execution_time:.2f} seconds",
            f"Input Data: {self.input_summary.get('interview_count', 0)} interviews, "
            f"{self.input_summary.get('total_quotes', 0)} quotes",
            "",
            "CONFIGURATION USED:",
            "-" * 20
        ]
        
        if self.analysis_config:
            for section, params in self.analysis_config.items():
                if isinstance(params, dict):
                    report_lines.append(f"{section.upper()}:")
                    for key, value in params.items():
                        report_lines.append(f"  {key}: {value}")
                else:
                    report_lines.append(f"{section}: {params}")
        
        report_lines.extend([
            "",
            "ANALYSIS STEPS:",
            "-" * 15
        ])
        
        for i, step in enumerate(self.steps, 1):
            report_lines.extend([
                f"{i}. {step.step_name.upper()} ({step.step_id})",
                f"   Time: {step.timestamp.strftime('%H:%M:%S')} "
                f"(Duration: {step.execution_time_seconds:.1f}s)",
                f"   Rationale: {step.decision_rationale}",
                f"   Output: {len(step.output_summary)} items generated"
            ])
            
            if step.alternatives_considered:
                report_lines.append(f"   Alternatives Considered: {', '.join(step.alternatives_considered)}")
            
            if step.confidence_metrics:
                confidence_str = ", ".join([f"{k}={v:.2f}" for k, v in step.confidence_metrics.items()])
                report_lines.append(f"   Confidence Metrics: {confidence_str}")
            
            report_lines.append("")
        
        if self.final_results_summary:
            report_lines.extend([
                "FINAL RESULTS SUMMARY:",
                "-" * 22
            ])
            for key, value in self.final_results_summary.items():
                if isinstance(value, (int, float)):
                    report_lines.append(f"{key}: {value}")
                elif isinstance(value, str) and len(value) < 100:
                    report_lines.append(f"{key}: {value}")
                elif isinstance(value, list):
                    report_lines.append(f"{key}: {len(value)} items")
                else:
                    report_lines.append(f"{key}: [Complex data structure]")
        
        return "\n".join(report_lines)
    
    def export_methodology_compliance_report(self) -> str:
        """Generate methodology compliance validation report"""
        report_lines = [
            "GROUNDED THEORY METHODOLOGY COMPLIANCE REPORT",
            "=" * 50,
            f"Workflow ID: {self.workflow_id}",
            f"Analysis Date: {self.start_time.strftime('%Y-%m-%d')}",
            "",
            "METHODOLOGY ADHERENCE CHECKLIST:",
            "-" * 35
        ]
        
        # Check for required GT phases
        required_phases = ["open_coding", "axial_coding", "selective_coding", "theory_integration"]
        completed_phases = [step.step_name for step in self.steps if step.step_name in required_phases]
        
        report_lines.append("Required Grounded Theory Phases:")
        for phase in required_phases:
            status = "✓ COMPLETED" if phase in completed_phases else "✗ MISSING"
            report_lines.append(f"  {phase.replace('_', ' ').title()}: {status}")
        
        # Check configuration compliance
        report_lines.extend([
            "",
            "Configuration Compliance:",
            f"  Theoretical Sensitivity: {self.analysis_config.get('analysis_parameters', {}).get('theoretical_sensitivity', 'NOT SET')}",
            f"  Coding Depth: {self.analysis_config.get('analysis_parameters', {}).get('coding_depth', 'NOT SET')}",
            f"  Memo Generation: {self.analysis_config.get('analysis_parameters', {}).get('memo_generation_frequency', 'NOT SET')}"
        ])
        
        # Check for memo generation
        memo_steps = [step for step in self.steps if 'memo' in step.step_name.lower()]
        report_lines.extend([
            "",
            "Theoretical Memo Generation:",
            f"  Memos Generated: {len(memo_steps)}",
            f"  Memo Frequency: {self.analysis_config.get('analysis_parameters', {}).get('memo_generation_frequency', 'not configured')}"
        ])
        
        # Check for proper data grounding
        data_grounded_steps = [step for step in self.steps if step.input_data_summary.get('quote_count', 0) > 0]
        report_lines.extend([
            "",
            "Data Grounding Verification:",
            f"  Steps with Data Input: {len(data_grounded_steps)}/{len(self.steps)}",
            f"  Total Quotes Analyzed: {sum(step.input_data_summary.get('quote_count', 0) for step in self.steps)}"
        ])
        
        # Overall compliance assessment
        compliance_score = (len(completed_phases) / len(required_phases)) * 100
        report_lines.extend([
            "",
            "OVERALL COMPLIANCE ASSESSMENT:",
            "-" * 32,
            f"Methodology Compliance Score: {compliance_score:.1f}%",
            f"Status: {'COMPLIANT' if compliance_score >= 75 else 'NON-COMPLIANT'}",
            "",
            "Recommendations:",
            "- Ensure all four GT phases are completed",
            "- Generate theoretical memos at configured frequency",
            "- Maintain clear audit trail for reproducibility"
        ])
        
        return "\n".join(report_lines)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'GTAuditTrail':
        """Create audit trail from JSON string"""
        data = json.loads(json_str)
        
        # Reconstruct datetime objects
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time']) if data.get('end_time') else None
        
        # Reconstruct analysis steps
        steps = []
        for step_data in data.get('steps', []):
            step = AnalysisStep(
                step_id=step_data['step_id'],
                step_name=step_data['step_name'],
                timestamp=datetime.fromisoformat(step_data['timestamp']),
                input_data_summary=step_data.get('input_data_summary', {}),
                configuration_used=step_data.get('configuration_used', {}),
                llm_prompt=step_data.get('llm_prompt', ''),
                llm_response=step_data.get('llm_response', {}),
                decision_rationale=step_data.get('decision_rationale', ''),
                alternatives_considered=step_data.get('alternatives_considered', []),
                confidence_metrics=step_data.get('confidence_metrics', {}),
                output_summary=step_data.get('output_summary', {}),
                execution_time_seconds=step_data.get('execution_time_seconds', 0.0)
            )
            steps.append(step)
        
        return cls(
            workflow_id=data['workflow_id'],
            methodology=data['methodology'],
            analysis_config=data.get('analysis_config'),
            start_time=start_time,
            end_time=end_time,
            input_summary=data.get('input_summary', {}),
            steps=steps,
            final_results_summary=data.get('final_results_summary', {}),
            total_execution_time=data.get('total_execution_time', 0.0)
        )
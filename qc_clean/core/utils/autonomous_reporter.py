#!/usr/bin/env python3
"""
Autonomous Report Generation for Qualitative Research

Generates publication-ready reports from GT analysis results with multiple output formats.
Provides academic reports, executive summaries, and raw data exports based on configuration.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import asdict

logger = logging.getLogger(__name__)


class AutonomousReporter:
    """Generates publication-ready reports from GT analysis results"""
    
    def __init__(self, config=None):
        """Initialize with optional configuration"""
        self.config = config
        
    def generate_all_configured_reports(self, results, audit_trail) -> Dict[str, str]:
        """Generate all reports specified in configuration"""
        reports = {}
        
        if self.config and self.config.report_formats:
            for format_name in self.config.report_formats:
                if format_name == "academic_report":
                    reports["academic_report"] = self.generate_academic_report(results, audit_trail)
                elif format_name == "executive_summary":
                    reports["executive_summary"] = self.generate_executive_summary(results)
                elif format_name == "raw_data":
                    reports["raw_data"] = self.generate_raw_data_export(results)
        else:
            # Default to academic report
            reports["academic_report"] = self.generate_academic_report(results, audit_trail)
        
        return reports
    
    def generate_academic_report(self, results, audit_trail=None) -> str:
        """Generate academic paper format report"""
        
        # Extract key information
        core_category_name = results.core_category.category_name if results.core_category else "Not identified"
        theoretical_model_name = results.theoretical_model.model_name if results.theoretical_model else "Not developed"
        num_codes = len(results.open_codes) if results.open_codes else 0
        num_relationships = len(results.axial_relationships) if results.axial_relationships else 0
        
        report_sections = []
        
        # Title and Header
        report_sections.append("# Grounded Theory Analysis Report")
        report_sections.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if audit_trail:
            report_sections.append(f"**Workflow ID:** {audit_trail.workflow_id}")
        report_sections.append("")
        
        # Abstract
        report_sections.append("## Abstract")
        report_sections.append("")
        abstract_text = f"""This report presents the findings of a grounded theory analysis conducted on qualitative interview data. 
Through systematic application of open coding, axial coding, and selective coding procedures, we identified {num_codes} 
initial concepts and {num_relationships} key relationships. The analysis culminated in the identification of 
'{core_category_name}' as the core category, leading to the development of the '{theoretical_model_name}' theoretical model. 
This study contributes to understanding of the phenomenon through empirically-grounded theoretical development."""
        report_sections.append(abstract_text)
        report_sections.append("")
        
        # Methodology
        report_sections.append("## Methodology")
        report_sections.append("")
        report_sections.append("### Research Approach")
        methodology_text = """This study employed grounded theory methodology following the systematic approach outlined by 
Strauss and Corbin (1998). The analysis proceeded through four distinct phases: open coding to identify initial concepts, 
axial coding to establish relationships between categories, selective coding to identify the core category, and theoretical 
integration to develop the final theoretical model."""
        report_sections.append(methodology_text)
        report_sections.append("")
        
        if self.config:
            report_sections.append("### Configuration Parameters")
            report_sections.append(f"- **Theoretical Sensitivity:** {self.config.theoretical_sensitivity}")
            report_sections.append(f"- **Coding Depth:** {self.config.coding_depth}")
            report_sections.append(f"- **Validation Level:** {self.config.validation_level}")
            if hasattr(self.config, 'minimum_code_frequency'):
                report_sections.append(f"- **Minimum Code Frequency:** {self.config.minimum_code_frequency}")
            report_sections.append("")
        
        # Analysis metadata
        if results.analysis_metadata:
            metadata = results.analysis_metadata
            report_sections.append("### Data Analysis Summary")
            report_sections.append(f"- **Interviews Analyzed:** {metadata.get('interview_count', 'Unknown')}")
            report_sections.append(f"- **Analysis Duration:** {metadata.get('duration_seconds', 0):.1f} seconds")
            report_sections.append(f"- **Theoretical Memos Generated:** {metadata.get('memos_generated', 0)}")
            report_sections.append("")
        
        # Results - Open Coding
        report_sections.append("## Results")
        report_sections.append("")
        report_sections.append("### Phase 1: Open Coding")
        if results.open_codes:
            report_sections.append(f"The open coding phase identified {len(results.open_codes)} distinct concepts from the data. "
                                 f"The most significant codes by frequency were:")
            report_sections.append("")
            
            # Sort codes by frequency and show top 10
            sorted_codes = sorted(results.open_codes, key=lambda x: x.frequency, reverse=True)[:10]
            for i, code in enumerate(sorted_codes, 1):
                report_sections.append(f"{i}. **{code.code_name}** (n={code.frequency}, conf={code.confidence:.2f})")
                report_sections.append(f"   {code.description}")
                if self.config and self.config.include_supporting_quotes and code.supporting_quotes:
                    quote_preview = code.supporting_quotes[0][:200] + "..." if len(code.supporting_quotes[0]) > 200 else code.supporting_quotes[0]
                    report_sections.append(f"   *Supporting quote: \"{quote_preview}\"*")
                report_sections.append("")
        else:
            report_sections.append("No open codes were identified in this analysis.")
            report_sections.append("")
        
        # Results - Axial Coding
        report_sections.append("### Phase 2: Axial Coding")
        if results.axial_relationships:
            report_sections.append(f"Axial coding revealed {len(results.axial_relationships)} significant relationships between categories. "
                                 f"The strongest relationships identified were:")
            report_sections.append("")
            
            # Sort relationships by strength
            sorted_rels = sorted(results.axial_relationships, key=lambda x: x.strength, reverse=True)[:5]
            for i, rel in enumerate(sorted_rels, 1):
                report_sections.append(f"{i}. **{rel.central_category} → {rel.related_category}**")
                report_sections.append(f"   *Type:* {rel.relationship_type} (strength: {rel.strength:.2f})")
                report_sections.append(f"   *Conditions:* {', '.join(rel.conditions)}")
                report_sections.append(f"   *Consequences:* {', '.join(rel.consequences)}")
                report_sections.append("")
        else:
            report_sections.append("No axial relationships were identified in this analysis.")
            report_sections.append("")
        
        # Results - Core Category
        report_sections.append("### Phase 3: Selective Coding - Core Category")
        if results.core_category:
            core = results.core_category
            report_sections.append(f"The selective coding process identified **'{core.category_name}'** as the core category.")
            report_sections.append("")
            report_sections.append(f"**Definition:** {core.definition}")
            report_sections.append("")
            report_sections.append(f"**Central Phenomenon:** {core.central_phenomenon}")
            report_sections.append("")
            report_sections.append(f"**Explanatory Power:** {core.explanatory_power}")
            report_sections.append("")
            report_sections.append(f"**Integration Rationale:** {core.integration_rationale}")
            report_sections.append("")
            
            if core.related_categories:
                report_sections.append("**Related Categories:**")
                for category in core.related_categories:
                    report_sections.append(f"- {category}")
                report_sections.append("")
        else:
            report_sections.append("No core category was identified in this analysis.")
            report_sections.append("")
        
        # Results - Theoretical Model
        report_sections.append("### Phase 4: Theoretical Integration")
        if results.theoretical_model:
            model = results.theoretical_model
            report_sections.append(f"The final phase produced the **'{model.model_name}'** theoretical model.")
            report_sections.append("")
            report_sections.append("#### Theoretical Framework")
            report_sections.append(model.theoretical_framework)
            report_sections.append("")
            
            if model.propositions:
                report_sections.append("#### Key Propositions")
                for i, prop in enumerate(model.propositions, 1):
                    report_sections.append(f"{i}. {prop}")
                report_sections.append("")
            
            if model.conceptual_relationships:
                report_sections.append("#### Conceptual Relationships")
                for i, rel in enumerate(model.conceptual_relationships, 1):
                    report_sections.append(f"{i}. {rel}")
                report_sections.append("")
        else:
            report_sections.append("No theoretical model was developed in this analysis.")
            report_sections.append("")
        
        # Discussion
        report_sections.append("## Discussion")
        if results.theoretical_model:
            model = results.theoretical_model
            
            if model.implications:
                report_sections.append("### Theoretical Implications")
                for implication in model.implications:
                    report_sections.append(f"- {implication}")
                report_sections.append("")
            
            if model.scope_conditions:
                report_sections.append("### Scope and Limitations")
                report_sections.append("This theory applies under the following conditions:")
                for condition in model.scope_conditions:
                    report_sections.append(f"- {condition}")
                report_sections.append("")
        
        # Methodology Compliance
        if self.config and self.config.include_audit_trail and audit_trail:
            report_sections.append("### Methodological Compliance")
            report_sections.append("This analysis was conducted following established grounded theory procedures with complete audit trail documentation. "
                                 f"The analysis included {len(audit_trail.steps)} documented steps with full transparency of decision-making processes.")
            report_sections.append("")
        
        # Future Research
        if results.theoretical_model and results.theoretical_model.future_research:
            report_sections.append("### Future Research Directions")
            for i, direction in enumerate(results.theoretical_model.future_research, 1):
                report_sections.append(f"{i}. {direction}")
            report_sections.append("")
        
        # References
        report_sections.append("## References")
        report_sections.append("")
        report_sections.append("Strauss, A., & Corbin, J. (1998). *Basics of qualitative research: Techniques and procedures for developing grounded theory* (2nd ed.). Sage Publications.")
        report_sections.append("")
        report_sections.append("Charmaz, K. (2006). *Constructing grounded theory: A practical guide through qualitative analysis*. Sage Publications.")
        report_sections.append("")
        
        return "\n".join(report_sections)
    
    def generate_executive_summary(self, results) -> str:
        """Generate executive summary for non-academic audiences"""
        
        summary_sections = []
        
        # Header
        summary_sections.append("# Executive Summary - Grounded Theory Analysis")
        summary_sections.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d')}")
        summary_sections.append("")
        
        # Key Findings Overview
        summary_sections.append("## Key Findings")
        
        if results.core_category:
            summary_sections.append(f"**Central Finding:** The analysis identified '{results.core_category.category_name}' as the core theme "
                                   f"explaining the phenomenon under study.")
            summary_sections.append("")
        
        # Quantitative Summary
        num_codes = len(results.open_codes) if results.open_codes else 0
        num_relationships = len(results.axial_relationships) if results.axial_relationships else 0
        
        summary_sections.append("## Analysis Overview")
        summary_sections.append(f"- **Concepts Identified:** {num_codes}")
        summary_sections.append(f"- **Key Relationships:** {num_relationships}")
        if results.analysis_metadata:
            summary_sections.append(f"- **Interviews Analyzed:** {results.analysis_metadata.get('interview_count', 'Unknown')}")
        summary_sections.append("")
        
        # Top Findings with Hierarchy
        if results.open_codes:
            summary_sections.append("## Most Significant Themes")
            
            # Check if codes have hierarchical structure
            hierarchical_codes = [c for c in results.open_codes if c.parent_id or c.child_codes]
            
            if hierarchical_codes:
                # Generate hierarchical view
                summary_sections.append("")
                summary_sections.append("### Code Hierarchy")
                
                # Get top-level codes
                top_level_codes = [c for c in results.open_codes if c.level == 0]
                
                # Build parent-child map
                child_map = {}
                for parent in top_level_codes:
                    # Match by normalized code name
                    parent_id = parent.code_name.replace(' ', '_')
                    children = [c for c in results.open_codes 
                              if c.parent_id == parent_id]
                    if children:
                        child_map[parent.code_name] = children
                
                # Display hierarchical structure with multiple levels
                def display_code_tree(code, indent_level=0):
                    """Recursively display code hierarchy"""
                    indent = "   " * indent_level
                    prefix = "└── " if indent_level > 0 else ""
                    
                    # Display current code
                    if indent_level == 0:
                        summary_sections.append(f"**{code.code_name}** (frequency: {code.frequency})")
                        summary_sections.append(f"   {code.description}")
                    else:
                        summary_sections.append(f"{indent}{prefix}{code.code_name} (frequency: {code.frequency})")
                    
                    # Find and display children
                    code_id = code.code_name.replace(' ', '_')
                    children = [c for c in results.open_codes if c.parent_id == code_id]
                    
                    for child in children:
                        display_code_tree(child, indent_level + 1)
                
                # Display top-level codes and their full hierarchy
                for parent in sorted(top_level_codes, key=lambda x: x.frequency, reverse=True)[:5]:
                    display_code_tree(parent)
                    summary_sections.append("")
            else:
                # Fallback to flat list
                sorted_codes = sorted(results.open_codes, key=lambda x: x.frequency, reverse=True)[:5]
                for i, code in enumerate(sorted_codes, 1):
                    summary_sections.append(f"{i}. **{code.code_name}:** {code.description}")
                summary_sections.append("")
            
            summary_sections.append("")
        
        # Theoretical Insights
        if results.theoretical_model:
            model = results.theoretical_model
            summary_sections.append("## Key Insights")
            summary_sections.append(model.theoretical_framework)
            summary_sections.append("")
            
            if model.implications:
                summary_sections.append("## Implications")
                for implication in model.implications:
                    summary_sections.append(f"- {implication}")
                summary_sections.append("")
        
        # Recommendations
        if results.theoretical_model and results.theoretical_model.future_research:
            summary_sections.append("## Recommendations for Action")
            # Convert research directions to action recommendations
            for direction in results.theoretical_model.future_research[:3]:
                if "test" in direction.lower():
                    summary_sections.append(f"- Pilot implementation to validate findings")
                elif "examine" in direction.lower():
                    summary_sections.append(f"- Further investigation recommended")
                else:
                    summary_sections.append(f"- {direction}")
        
        return "\n".join(summary_sections)
    
    def generate_raw_data_export(self, results) -> str:
        """Generate structured data export for further analysis"""
        import json
        
        raw_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "analysis_type": "grounded_theory",
                "analysis_metadata": results.analysis_metadata
            },
            "open_codes": [],
            "axial_relationships": [],
            "core_category": None,
            "theoretical_model": None
        }
        
        # Convert open codes (including hierarchy fields)
        if results.open_codes:
            for code in results.open_codes:
                raw_data["open_codes"].append({
                    "code_name": code.code_name,
                    "description": code.description,
                    "properties": code.properties,
                    "dimensions": code.dimensions,
                    "supporting_quotes": code.supporting_quotes,
                    "frequency": code.frequency,
                    "confidence": code.confidence,
                    "parent_id": code.parent_id,
                    "level": code.level,
                    "child_codes": code.child_codes
                })
        
        # Convert axial relationships
        if results.axial_relationships:
            for rel in results.axial_relationships:
                raw_data["axial_relationships"].append({
                    "central_category": rel.central_category,
                    "related_category": rel.related_category,
                    "relationship_type": rel.relationship_type,
                    "conditions": rel.conditions,
                    "consequences": rel.consequences,
                    "supporting_evidence": rel.supporting_evidence,
                    "strength": rel.strength
                })
        
        # Convert core category
        if results.core_category:
            core = results.core_category
            raw_data["core_category"] = {
                "category_name": core.category_name,
                "definition": core.definition,
                "central_phenomenon": core.central_phenomenon,
                "related_categories": core.related_categories,
                "theoretical_properties": core.theoretical_properties,
                "explanatory_power": core.explanatory_power,
                "integration_rationale": core.integration_rationale
            }
        
        # Convert theoretical model
        if results.theoretical_model:
            model = results.theoretical_model
            raw_data["theoretical_model"] = {
                "model_name": model.model_name,
                "core_category": model.core_category,
                "theoretical_framework": model.theoretical_framework,
                "propositions": model.propositions,
                "conceptual_relationships": model.conceptual_relationships,
                "scope_conditions": model.scope_conditions,
                "implications": model.implications,
                "future_research": model.future_research
            }
        
        return json.dumps(raw_data, indent=2, ensure_ascii=False)
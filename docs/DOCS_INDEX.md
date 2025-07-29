# Documentation Index

This index provides a comprehensive guide to all documentation in the qualitative coding system project.

## Planning & Architecture Documents

### Core System Design
- **[SYSTEM_ARCHITECTURE.md](../SYSTEM_ARCHITECTURE.md)** - Consolidated system architecture including three-phase workflow, dual-layer design, batch processing, and three-mode system. Primary technical reference.

- **[ACADEMIC_QC_SPECIFICATION.md](../ACADEMIC_QC_SPECIFICATION.md)** - Overall system specification and philosophy for autonomous policy-focused qualitative coding. Defines core goals and features.

### Implementation Planning
- **[IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md)** - Master implementation plan with timeline, deliverables, and technical specifications for all components using Gemini 2.5 Flash.

- **[POLICY_ANALYSIS_FEATURES.md](../POLICY_ANALYSIS_FEATURES.md)** - Comprehensive guide to policy-specific features including stakeholder mapping, contradiction detection, and executive summaries.

## Research & Analysis Documents

### Critiques & Problem Statements
- **[ACADEMIC_QC_CRITIQUE.md](../ACADEMIC_QC_CRITIQUE.md)** - Critical analysis of academic qualitative coding approaches and their limitations.

- **[CRITICAL_QC_PROBLEM.md](../CRITICAL_QC_PROBLEM.md)** - Core problem statement defining the challenges in current qualitative coding methods.

## Technical Documentation

### System Constraints
- **[neo4j-constraints-limitation.md](neo4j-constraints-limitation.md)** - Technical limitations and constraints when using Neo4j for entity storage.

### Configuration
- All system settings via `.env` file including:
  - `MAX_BATCH_TOKENS` - Token limit per batch (default 200K)
  - `GEMINI_INPUT_PRICE` - Cost per 1M input tokens ($0.30)
  - `GEMINI_OUTPUT_PRICE` - Cost per 1M output tokens ($2.50)
  - See **[SYSTEM_ARCHITECTURE.md](../SYSTEM_ARCHITECTURE.md)** for full configuration reference

## Report Documentation

### System Reports
- **[reports/README.md](../reports/README.md)** - Index of all generated reports and their purposes.

### Technical Implementation Reports
- **[reports/TOKEN_LIMITS_EXPLANATION.md](../reports/TOKEN_LIMITS_EXPLANATION.md)** - Explanation of token limits and batching strategies.

### Security & Operations
- **[reports/SECURITY_STEPS.md](../reports/SECURITY_STEPS.md)** - Security measures and best practices for the system.

## Data Documentation

### Validation & Testing
- **[data/research_validation/README.md](../data/research_validation/README.md)** - Documentation for research validation procedures.

- **[data/end_to_end_results/END_TO_END_SUMMARY.md](../data/end_to_end_results/END_TO_END_SUMMARY.md)** - Summary of end-to-end testing results.

## Usage Examples

### Analysis Reports
- **[reports/Division_Level_Insights_Report.md](../reports/Division_Level_Insights_Report.md)** - Example of division-level analysis output.

- **[reports/Frequency_Based_RAND_Analysis.md](../reports/Frequency_Based_RAND_Analysis.md)** - Example frequency-based analysis report.

- **[reports/INTERVIEW_EXTRACTION_REPORT.md](../reports/INTERVIEW_EXTRACTION_REPORT.md)** - Sample interview extraction report.

## Quick Start Guides

### For Policy Analysts
1. Start with **[POLICY_ANALYSIS_FEATURES.md](../POLICY_ANALYSIS_FEATURES.md)** to understand capabilities
2. Review **[SYSTEM_ARCHITECTURE.md](../SYSTEM_ARCHITECTURE.md)** for modes and configuration
3. Check **[IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md)** for operational features

### For Developers
1. Begin with **[SYSTEM_ARCHITECTURE.md](../SYSTEM_ARCHITECTURE.md)** for technical overview
2. Study **[IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md)** for development plan
3. Configure system via `.env` file as documented

### For Researchers
1. Read **[ACADEMIC_QC_SPECIFICATION.md](../ACADEMIC_QC_SPECIFICATION.md)** for methodology
2. Understand **[SYSTEM_ARCHITECTURE.md](../SYSTEM_ARCHITECTURE.md)** for dual-layer analysis
3. Review critique in **[ACADEMIC_QC_CRITIQUE.md](../ACADEMIC_QC_CRITIQUE.md)**

## Key Features Documentation

### Core Capabilities
- **Flexible Batch Processing**: Automatic batching based on token count
- **Cost Management**: Pre-execution estimation with Gemini 2.5 Flash pricing
- **Error Recovery**: Automatic quarantine of corrupted interviews
- **Progress Tracking**: Real-time phase updates
- **Contradiction Detection**: Identify opposing stakeholder views
- **Executive Summaries**: One-page policy briefs

### Analysis Modes
- **OPEN**: Emergent themes from data
- **CLOSED**: Predefined framework only
- **HYBRID**: Combination approach

### Dual Layers
- **Qualitative Layer**: Codes, themes, meanings
- **Knowledge Layer**: Entities, stakeholders, relationships

## Configuration Reference

See **[SYSTEM_ARCHITECTURE.md](../SYSTEM_ARCHITECTURE.md)** for configuration reference.
All settings managed via `.env` file - no hardcoded values.

## Future Development

See **[reports/phase1.5_deferred_features_plan.md](../reports/phase1.5_deferred_features_plan.md)** for planned enhancements.
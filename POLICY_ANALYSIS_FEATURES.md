# Policy Analysis Features

## Overview

This document outlines the policy-specific features of our qualitative coding system, designed for autonomous processing of large-scale policy consultations and stakeholder interviews.

---

## Core Policy Features

### 1. Automatic Stakeholder Mapping

**Already Built-In**: The dual-layer architecture automatically provides stakeholder mapping through entity extraction.

```python
# Entities capture stakeholders
ENT_john_smith (person)
  properties:
    - role: "policy_director"
    - department: "health"
    - stakeholder_type: "implementer"  # Auto-detected

# Query: Who are the implementers concerned about funding?
LINK_john_exhibits_CODE_funding_concerns
```

### 2. Voice Counting

**Already Built-In**: Track how many unique entities express each view.

```python
def count_voices_per_code(code_id):
    """
    Returns unique entities linked to a code
    """
    # CODE_budget_concerns linked to:
    # - 45 unique people
    # - 12 organizations
    # - Breakdown by stakeholder_type
```

### 3. Contradiction Detection

**Phase 2 Feature**: Identify opposing views during aggregation.

```python
class ContradictionDetector:
    async def detect_in_aggregation(self, all_codes, all_entities):
        """
        Find contradictions between stakeholder groups
        """
        # Example output:
        # Issue: "remote work productivity"
        # Managers: "productivity decreased" (CODE_productivity_concerns)
        # Employees: "productivity increased" (CODE_productivity_gains)
        # Tension Level: HIGH
```

---

## Policy Entity Types

### Standard Schema

```python
POLICY_ENTITY_TYPES = {
    # Base types
    "person": {
        "properties": ["role", "department", "stakeholder_type"]
    },
    "organization": {
        "properties": ["type", "sector", "size", "jurisdiction"]
    },
    
    # Policy-specific types
    "policy_recommendation": {
        "properties": ["urgency", "complexity", "cost_implication"],
        "examples": ["streamline_process", "increase_funding"]
    },
    "implementation_barrier": {
        "properties": ["type", "severity", "affected_groups"],
        "examples": ["regulatory_complexity", "resource_shortage"]
    },
    "metaphor": {
        "properties": ["source_domain", "target_domain", "implication"],
        "examples": ["policy as journey", "regulation as red tape"]
    }
}
```

### Stakeholder Types (Entity Properties)

Use HYBRID approach - start with common types but allow emergence:

```python
BASE_STAKEHOLDER_TYPES = [
    "implementer",      # Those who deliver
    "beneficiary",      # Those who receive
    "regulator",        # Those who oversee
    "funder",           # Those who pay
    "advocate",         # Those who champion
    "opponent"          # Those who resist
]

# But allow discovery of new types like:
# "intermediary", "technical_expert", "gatekeeper"
```

---

## Post-Processing Analytics

### 1. Contradiction Matrix

```python
def generate_contradiction_matrix(analysis_results):
    """
    Visual matrix of opposing views
    """
    # Output format:
    #              | Implementers | Beneficiaries | Regulators
    # -------------|--------------|---------------|------------
    # Digital ID   | Support      | Oppose        | Support
    # Data Sharing | Concerns     | Support       | Neutral
    # Costs        | High burden  | Acceptable    | Justified
```

### 2. Executive Summary Generator

```python
def generate_executive_summary(final_analysis):
    """
    One-page policy brief
    """
    return {
        "key_findings": [
            "85% of implementers cite resource constraints",
            "Beneficiaries prioritize accessibility over efficiency"
        ],
        "stakeholder_alignment": {
            "consensus": ["Need for digital transformation"],
            "conflicts": ["Timeline expectations", "Cost allocation"]
        },
        "implementation_barriers": [
            ("Technical capacity", "HIGH", ["rural_providers"]),
            ("Regulatory clarity", "MEDIUM", ["all_groups"])
        ],
        "recommendations": [
            ("Phased rollout", "6 months", "addresses capacity"),
            ("Stakeholder workshops", "immediate", "builds consensus")
        ]
    }
```

### 3. Consensus Analysis

```python
def analyze_consensus(codes, entities):
    """
    Find areas of broad agreement
    """
    consensus_threshold = 0.75  # 75% of stakeholder types agree
    
    return {
        "strong_consensus": [
            "CODE_need_for_change",  # All groups agree
            "CODE_user_focus"        # 90% agreement
        ],
        "emerging_consensus": [
            "CODE_phased_approach"   # 75% agreement
        ],
        "no_consensus": [
            "CODE_funding_model"     # Split views
        ]
    }
```

---

## Quantitative Integration

### 1. Survey Data Weighting

```python
class QuantIntegration:
    def weight_by_demographics(self, qual_themes, survey_data):
        """
        Adjust theme importance by population representation
        """
        # If rural = 40% of population but 20% of interviews
        # Upweight rural-linked codes by 2x
        
    def validate_themes(self, qual_codes, survey_results):
        """
        Check convergence between qual and quant
        """
        # Theme: "digital_divide" (80% of interviews)
        # Survey: 73% report internet access issues
        # Convergence: HIGH
```

### 2. Mixed Methods Matrix

```
| Theme               | Qual Evidence      | Quant Evidence    | Convergence |
|--------------------|-------------------|-------------------|-------------|
| Access Barriers    | 85% mention       | 78% survey agree  | HIGH        |
| Cost Concerns      | 60% discuss       | 82% cite as #1    | MEDIUM      |
| Technical Support  | 30% mention       | 45% need help     | MEDIUM      |
```

---

## Configuration for Policy Analysis

### Public Consultation Mode
```bash
# .env configuration
ANALYSIS_MODE=policy_consultation
CODING_MODE=HYBRID
ENTITY_MODE=HYBRID
DETECT_CONTRADICTIONS=true
GENERATE_EXECUTIVE_SUMMARY=true
MIN_STAKEHOLDER_VOICES=5  # Only report if 5+ people say it
```

### Regulatory Analysis Mode
```bash
ANALYSIS_MODE=regulatory_impact
CODING_MODE=CLOSED  # Use regulatory framework
ENTITY_MODE=HYBRID  # Discover affected groups
TRACK_IMPLEMENTATION_BARRIERS=true
SEVERITY_THRESHOLDS=true
```

---

## Quick Implementation Wins

1. **Stakeholder Properties** (1 day)
   - Add to entity extraction prompts
   - No additional API calls needed

2. **Contradiction Detection** (2 days)
   - Add to Phase 2 aggregation
   - Simple opposing view finder

3. **Executive Summary** (2 days)
   - Post-processing template
   - Key sections for policy makers

4. **Consensus Metrics** (1 day)
   - Calculate agreement percentages
   - Identify split issues

5. **Basic Quant Integration** (1 day)
   - Simple weighting functions
   - Convergence calculations

---

## Not Included (Future Research)

- **Temporal Analysis**: Track opinion changes over time
- **Predictive Modeling**: Forecast implementation success
- **Multi-jurisdiction Comparison**: Compare across regions
- **Real-time Dashboards**: Live consultation monitoring
- **Researcher Reflexivity**: For sensitive political topics
- **Inter-Rater Reliability**: For contested policy areas
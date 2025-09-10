# Problems Index - 2025-08-05

## Architectural Problems

### 1. Duplicate Consolidation Logic
- **Location**: `qc/validation/relationship_consolidator.py` vs `qc/consolidation/llm_consolidator.py`
- **Issue**: Two separate systems doing semantic consolidation with different approaches
- **Impact**: Conflicting decisions, maintenance burden, inconsistent results
- **Root Cause**: Validation layer has hardcoded semantic groups while LLM layer uses AI reasoning

### 2. Hardcoded Semantic Assumptions
- **Location**: `qc/validation/relationship_consolidator.py` lines 19-64
- **Issue**: Manual categorization of relationship types into semantic groups
- **Impact**: Requires code changes for new relationship types, subjective classifications
- **Example**: "EMPLOYS" was hardcoded in "usage" group instead of "employment" group

### 3. Non-Generalist Problem Solving
- **Issue**: Band-aid fixes for specific cases rather than systematic solutions
- **Impact**: Technical debt accumulation, brittle system architecture
- **Example**: Moving "EMPLOYS" between hardcoded groups instead of fixing the categorization system

## Data Pipeline Problems

### 4. Direction Flipping Logic Complexity
- **Location**: `qc/cli.py` lines 683-720
- **Issue**: Complex conditional logic for handling relationship direction flipping
- **Impact**: Hard to maintain, extend, or debug
- **Root Cause**: Should be handled by semantic understanding, not hardcoded rules

### 5. Missing Thematic Code Definitions
- **Location**: Thematic codes show "No definition provided" in outputs
- **Issue**: LLM extraction not generating semantic definitions for codes
- **Impact**: Reduced analytical value of thematic codes
- **Status**: Identified but not addressed

## Design Problems

### 6. Inconsistent Relationship Direction Semantics
- **Issue**: Some relationships show semantically incorrect directions
- **Example**: "Docker → Jennifer Martinez" instead of "Jennifer Martinez → Docker"
- **Root Cause**: Lack of semantic validation during extraction

### 7. Validation Layer Overreach
- **Location**: `qc/validation/relationship_consolidator.py`
- **Issue**: Validation layer making semantic decisions that should be in consolidation layer
- **Impact**: Confusion about where consolidation logic belongs

## Technical Debt

### 8. Hardcoded Entity-Relationship Patterns
- **Location**: `qc/validation/relationship_consolidator.py` lines 187-195
- **Issue**: Hardcoded typical relationship patterns between entity types
- **Impact**: Not adaptable to new domains or relationship types

### 9. Manual Semantic Group Maintenance
- **Issue**: All semantic relationships must be manually coded and maintained
- **Impact**: Scalability issues, human error prone, domain knowledge bottleneck

### 10. Mixed Responsibility Layers
- **Issue**: Unclear separation between validation, consolidation, and export responsibilities
- **Impact**: Hard to understand data flow, difficult to modify behavior

## Scalability Problems

### 11. Static Relationship Type System
- **Issue**: System assumes predefined set of relationship types
- **Impact**: Cannot adapt to new domains or evolving relationship vocabularies
- **Example**: Adding new relationship types requires code changes

### 12. Domain-Specific Hardcoding
- **Issue**: Semantic rules are hardcoded for current domain
- **Impact**: Cannot generalize to other qualitative research domains
- **Example**: "Person-Organization-Tool" assumptions baked into validation

## Solution Architecture Needed

### 13. Unified Consolidation System
- **Need**: Single system for semantic consolidation using LLM reasoning
- **Benefit**: Eliminates duplicate logic, improves consistency
- **Approach**: Remove hardcoded groups, use LLM for semantic decisions

### 14. Context-Aware Semantic Understanding
- **Need**: Consider entity types when determining relationship semantics
- **Benefit**: More accurate consolidation decisions
- **Example**: "employs" means different things for Person-Organization vs Organization-Tool

### 15. Configurable Semantic Rules
- **Need**: Allow domain experts to define semantic rules without code changes
- **Benefit**: Adaptable to different research domains
- **Approach**: Configuration-driven semantic understanding

## Priority Assessment

**High Priority** (Architectural Issues):
- Problems 1, 2, 3 - Core architecture problems affecting maintainability

**Medium Priority** (Functionality Issues):
- Problems 4, 5, 6, 7 - Specific functionality that needs improvement

**Low Priority** (Technical Debt):
- Problems 8, 9, 10, 11, 12 - Long-term maintainability and scalability

**Future Work** (System Redesign):
- Problems 13, 14, 15 - Architectural solutions for generalist approach
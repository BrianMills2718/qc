# CRITICAL PROBLEM: This is NOT Qualitative Coding!

## The Fundamental Misunderstanding

The current system treats qualitative coding as **entity/relationship extraction** (like building a knowledge graph), when it should be focused on **thematic analysis** and **hierarchical code development**.

---

## What Qualitative Coding ACTUALLY Is

### Core Principles of Qualitative Coding
1. **Thematic Analysis**: Identifying patterns of meaning across data
2. **Hierarchical Code Structure**: Codes organized from specific to abstract
3. **Grounded Theory**: Codes emerge from data, not predefined entities
4. **Iterative Refinement**: Codes evolve through multiple readings
5. **Theoretical Sensitivity**: Understanding context and meaning

### Proper Code Hierarchy Example
```
Trust in Remote Work (Theme)
├── Trust Breakdown
│   ├── Surveillance Behaviors
│   │   ├── "constantly checking Slack status"
│   │   ├── "monitoring green dots"
│   │   └── "tracking login times"
│   ├── Micromanagement
│   │   ├── "requiring camera always on"
│   │   └── "hourly check-ins"
│   └── Assumption of Laziness
│       ├── "they think we're slacking"
│       └── "need to prove I'm working"
├── Trust Building Mechanisms  
│   ├── Deliverable-Based Trust
│   │   ├── "judge me by output"
│   │   └── "results speak for themselves"
│   └── Communication Rituals
│       ├── "daily standups help"
│       └── "regular 1-on-1s build rapport"
└── Trust Paradoxes
    ├── "trust them but verify anyway"
    └── "say they trust but actions show otherwise"
```

---

## Current System Problems

### 1. Entity Extraction ≠ Qualitative Coding
```python
# WRONG - Current approach
entities = [
    {"name": "John", "type": "Person"},
    {"name": "TechCorp", "type": "Organization"},
    {"name": "Slack", "type": "Tool"}
]

# RIGHT - Qualitative coding approach
codes = {
    "remote_work_challenges": {
        "definition": "Difficulties experienced in remote work settings",
        "child_codes": {
            "communication_breakdown": {
                "definition": "Loss of informal communication channels",
                "quotes": [
                    {
                        "text": "I miss the casual conversations with my colleague Sarah",
                        "memo": "Loss of serendipitous interaction",
                        "line_number": 45
                    }
                ]
            },
            "tool_fatigue": {
                "definition": "Exhaustion from constant digital tool usage",
                "quotes": [
                    {
                        "text": "We use Slack and Zoom, but it's not the same",
                        "memo": "Tools can't replace human connection",
                        "line_number": 52
                    }
                ]
            }
        }
    }
}
```

### 2. Missing Core QC Features

#### ❌ No Code Hierarchy
- Current: Flat list of "codes"
- Needed: Parent-child relationships, themes, sub-themes

#### ❌ No Memo Writing
- Current: No analytical memos
- Needed: Researcher notes on why codes were applied

#### ❌ No Code Evolution
- Current: One-shot extraction
- Needed: Iterative refinement, code merging/splitting

#### ❌ No Theoretical Framework
- Current: Just extracting mentioned concepts
- Needed: Building theory from patterns

#### ❌ No Saturation Tracking
- Current: No concept of theoretical saturation
- Needed: Track when no new codes emerge

---

## What the System SHOULD Do

### 1. Initial Coding (Open Coding)
```python
class OpenCode:
    text_segment: str
    initial_code: str
    memo: str
    line_numbers: Tuple[int, int]
    
# Example:
OpenCode(
    text_segment="I don't trust my colleagues when working remotely",
    initial_code="remote_trust_issues",
    memo="Participant expresses lack of trust specifically tied to remote context",
    line_numbers=(42, 42)
)
```

### 2. Axial Coding (Finding Relationships)
```python
class AxialCode:
    category: str
    properties: Dict[str, Any]
    dimensions: Dict[str, str]
    related_codes: List[str]
    
# Example:
AxialCode(
    category="trust_in_remote_work",
    properties={
        "conditions": ["lack of visibility", "no casual interaction"],
        "consequences": ["increased monitoring", "decreased autonomy"],
        "strategies": ["over-communication", "performance proof"]
    },
    dimensions={
        "intensity": "low <-> high",
        "frequency": "rare <-> constant"
    },
    related_codes=["surveillance", "autonomy", "communication"]
)
```

### 3. Selective Coding (Core Categories)
```python
class CoreCategory:
    name: str
    definition: str
    theoretical_model: str
    supporting_categories: List[str]
    
# Example:
CoreCategory(
    name="Digital Trust Paradox",
    definition="The contradiction between stated trust and surveillance behaviors in remote work",
    theoretical_model="Trust requires visibility in physical space but surveillance in digital space",
    supporting_categories=["trust_breakdown", "digital_surveillance", "performance_anxiety"]
)
```

---

## Proper Qualitative Coding Prompt

```python
QC_PROMPT = """
Perform qualitative coding analysis on this interview transcript.

QUALITATIVE CODING PROCESS:
1. Read the entire transcript to understand context
2. Identify meaningful segments that relate to the research question
3. Assign initial codes to these segments (open coding)
4. Group related codes into categories (axial coding)
5. Identify relationships between categories
6. Develop theoretical insights

For EACH coded segment provide:
- The exact quote
- Line numbers
- Initial code name
- Code definition
- Analytical memo (why this code?)
- Suggested parent category
- Related codes

Focus on MEANING and PATTERNS, not just entities mentioned.

Output a hierarchical code structure showing:
- Core themes
  - Categories
    - Subcategories
      - Individual codes
        - Supporting quotes

Remember: We're building THEORY from data, not just extracting information.
"""
```

---

## Implementation Plan

### 1. New Data Models
```python
from pydantic import BaseModel
from typing import List, Dict, Optional

class CodedSegment(BaseModel):
    """A single coded segment from the transcript"""
    quote: str
    line_start: int
    line_end: int
    code: str
    memo: str
    confidence: float

class HierarchicalCode(BaseModel):
    """A code with hierarchical structure"""
    name: str
    definition: str
    level: int  # 0=theme, 1=category, 2=subcategory, 3=code
    parent: Optional[str]
    children: List[str]
    segments: List[CodedSegment]
    properties: Dict[str, Any]
    
class QualitativeCodingResult(BaseModel):
    """Complete QC analysis result"""
    themes: List[HierarchicalCode]
    code_hierarchy: Dict[str, List[str]]  # parent -> children
    theoretical_insights: List[str]
    saturation_indicators: Dict[str, float]
    researcher_memos: List[Dict[str, str]]
```

### 2. Revised Extraction Process
```python
class QualitativeCodingExtractor(SimpleGeminiExtractor):
    """Proper qualitative coding using Gemini"""
    
    async def perform_qualitative_coding(
        self,
        transcript: str,
        research_question: str,
        existing_codebook: Optional[Dict] = None
    ) -> QualitativeCodingResult:
        
        # Phase 1: Open coding
        open_codes = await self.open_coding(transcript, research_question)
        
        # Phase 2: Axial coding (find relationships)
        categories = await self.axial_coding(open_codes)
        
        # Phase 3: Build hierarchy
        hierarchy = await self.build_code_hierarchy(categories)
        
        # Phase 4: Theoretical development
        insights = await self.develop_theoretical_insights(hierarchy)
        
        return QualitativeCodingResult(
            themes=hierarchy,
            theoretical_insights=insights,
            # ... etc
        )
```

### 3. Features for Proper QC

1. **Codebook Management**
   - Import/export codebooks
   - Version control for code evolution
   - Code merging and splitting

2. **Memo System**
   - Analytical memos for each code
   - Theoretical memos for insights
   - Method memos for decisions

3. **Saturation Tracking**
   - Monitor when new codes stop emerging
   - Track code frequency across interviews
   - Identify theoretical saturation

4. **Inter-Rater Reliability**
   - Support multiple coders
   - Calculate agreement metrics
   - Resolve coding conflicts

5. **Theory Building Tools**
   - Concept mapping
   - Relationship visualization
   - Pattern identification

---

## Migration Path - UPDATED

### Phase 1: Three-Mode Foundation (Week 1)
- Implement OPEN mode (thematic analysis)
- Implement CLOSED mode (framework analysis)
- Implement HYBRID mode (mixed approach)
- Add directed vs exploratory goal setting

### Phase 2: Academic Features (Week 2)
- Add hermeneutic cycles (re-reading with evolved understanding)
- Implement negative case analysis
- Build audit trail system
- Add theoretical sampling guidance

### Phase 3: Analysis & Reporting (Week 3)
- Cross-interview pattern analysis
- Academic report generation
- Framework evolution tracking (HYBRID mode)
- Export to SPSS/R/JSON formats

### Phase 4: Advanced Features (Week 4)
- Optional constant comparison (for GT users)
- Quality metrics and saturation curves
- Framework version control
- Performance optimization

---

## Conclusion

The current system is building a **knowledge graph**, not doing **qualitative coding**. This is a fundamental architectural problem that needs to be addressed before the system can be useful for actual qualitative research.

**Priority**: This should be the #1 priority - without fixing this, the system doesn't serve its stated purpose.
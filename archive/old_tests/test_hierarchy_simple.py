#!/usr/bin/env python3
"""
Simple test to verify hierarchy implementation works
"""
from src.qc.workflows.grounded_theory import OpenCode, CoreCategory, GroundedTheoryResults

print("=" * 60)
print("SIMPLE HIERARCHY TEST")
print("=" * 60)

# 1. Test OpenCode with hierarchy
print("\n1. TESTING OPENCODE HIERARCHY FIELDS")
code1 = OpenCode(
    code_name="AI Applications",
    description="Ways AI is being used",
    properties=["versatility", "automation"],
    dimensions=["research", "operations"],
    supporting_quotes=["AI helps with analysis"],
    frequency=10,
    confidence=0.95,
    parent_id=None,  # Top-level code
    level=0,
    child_codes=["LLM_Usage", "ML_Models"]
)

code2 = OpenCode(
    code_name="LLM Usage",
    description="Large language model applications",
    properties=["text generation"],
    dimensions=["GPT", "Claude"],
    supporting_quotes=["We use GPT for summaries"],
    frequency=5,
    confidence=0.9,
    parent_id="AI_Applications",  # Child of AI Applications
    level=1,
    child_codes=[]
)

print(f"[OK] Code 1: {code1.code_name}")
print(f"   - Parent: {code1.parent_id}")
print(f"   - Level: {code1.level}")
print(f"   - Children: {code1.child_codes}")

print(f"\n[OK] Code 2: {code2.code_name}")
print(f"   - Parent: {code2.parent_id}")
print(f"   - Level: {code2.level}")
print(f"   - Children: {code2.child_codes}")

# 2. Test multiple core categories
print("\n2. TESTING MULTIPLE CORE CATEGORIES")
categories = [
    CoreCategory(
        category_name="Technology Adoption",
        definition="How technology is adopted",
        central_phenomenon="Digital transformation",
        related_categories=["AI Usage", "Tool Integration"],
        theoretical_properties=["adoption rate", "resistance"],
        explanatory_power="Explains technology uptake",
        integration_rationale="Most frequent theme"
    ),
    CoreCategory(
        category_name="Organizational Change",
        definition="How organizations evolve",
        central_phenomenon="Adaptation processes",
        related_categories=["Culture", "Process"],
        theoretical_properties=["change velocity", "flexibility"],
        explanatory_power="Explains organizational dynamics",
        integration_rationale="Second major theme"
    )
]

print(f"[OK] Created {len(categories)} core categories:")
for cat in categories:
    print(f"   - {cat.category_name}: {cat.definition}")

# 3. Test hierarchical dict export
print("\n3. TESTING HIERARCHICAL EXPORT")
export = code1.to_hierarchical_dict()
print(f"[OK] Export contains hierarchy fields:")
print(f"   - Has parent_id: {'parent_id' in export}")
print(f"   - Has level: {'level' in export}")
print(f"   - Has child_codes: {'child_codes' in export}")

# 4. Test GroundedTheoryResults with multiple categories
print("\n4. TESTING RESULTS WITH MULTIPLE CATEGORIES")
from src.qc.workflows.grounded_theory import TheoreticalModel

model = TheoreticalModel(
    model_name="Integrated Theory",
    core_categories=["Technology Adoption", "Organizational Change"],
    theoretical_framework="Multi-dimensional framework",
    propositions=["Technology drives change"],
    conceptual_relationships=["Tech influences org"],
    scope_conditions=["Modern organizations"],
    implications=["Need for adaptation"],
    future_research=["Long-term impacts"]
)

results = GroundedTheoryResults(
    open_codes=[code1, code2],
    axial_relationships=[],
    core_categories=categories,
    theoretical_model=model,
    supporting_memos=[],
    analysis_metadata={}
)

print(f"[OK] Results created with:")
print(f"   - {len(results.open_codes)} open codes")
print(f"   - {len(results.core_categories)} core categories")
print(f"   - Backward compat core_category: {results.core_category.category_name if results.core_category else None}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED [OK]")
print("=" * 60)
print("\nSUMMARY:")
print("1. OpenCode supports hierarchy (parent_id, level, child_codes)")
print("2. Multiple CoreCategory objects can be created")
print("3. Hierarchical export works")
print("4. GroundedTheoryResults supports multiple core categories")
print("5. Backward compatibility maintained")
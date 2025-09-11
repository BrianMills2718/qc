#!/usr/bin/env python3
"""
Test the multi-level hierarchy display without running full workflow
"""
import json
from pathlib import Path
from src.qc.reporting.autonomous_reporter import AutonomousReporter
from src.qc.workflows.grounded_theory import GroundedTheoryResults, OpenCode

# Load the data we already generated
with open('hierarchy_analysis.json', 'r') as f:
    data = json.load(f)

# Convert to OpenCode objects
open_codes = []
for code_data in data['codes']:
    code = OpenCode(
        code_name=code_data['name'],
        description=f"Description of {code_data['name']}",
        properties=[],
        dimensions=[],
        supporting_quotes=[],
        frequency=1,
        confidence=0.8,
        parent_id=code_data['parent_id'],
        level=code_data['level'],
        child_codes=code_data['child_codes'] or []
    )
    open_codes.append(code)

# Create results object
results = GroundedTheoryResults(
    open_codes=open_codes,
    axial_relationships=[],
    core_categories=[],
    theoretical_model=None,
    supporting_memos=[],
    analysis_metadata={'interview_count': 3}
)

# Generate report
reporter = AutonomousReporter()
summary = reporter.generate_executive_summary(results)

# Save report
output_file = Path("test_multi_level_report.md")
output_file.write_text(summary, encoding='utf-8')

print(f"Report saved to {output_file}")
print("\nChecking hierarchy depth in report...")

# Check if multi-level hierarchy is shown
lines = summary.split('\n')
for i, line in enumerate(lines):
    if '└──' in line:
        indent_count = (len(line) - len(line.lstrip())) // 3
        if indent_count > 1:
            print(f"Found level {indent_count} hierarchy: {line.strip()}")

# Count hierarchy levels
max_indent = 0
for line in lines:
    if '└──' in line:
        indent = (len(line) - len(line.lstrip())) // 3
        max_indent = max(max_indent, indent)

print(f"\nMaximum hierarchy depth in report: {max_indent + 1} levels")
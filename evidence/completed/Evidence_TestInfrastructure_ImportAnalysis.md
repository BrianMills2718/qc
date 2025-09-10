# Test Infrastructure Import Analysis

## Date: 2025-01-29

## Problem Summary
Tests are using `from qc.` imports while the actual code structure uses `src.qc.`

## Evidence Collection

### Setup Files Check
- **Result**: No setup.py or pyproject.toml found
- **Implication**: Package is not installed, must use explicit src.qc imports

### Import Path Analysis
- **Total affected files**: 71 test files use incorrect import pattern
- **Pattern**: All tests use `from qc.` instead of `from src.qc.`

### Sample Affected Files
```
tests/active/e2e/test_network_api_direct.py
tests/active/e2e/test_network_relationships.py
tests/active/e2e/test_network_simple.py
tests/active/integration/test_5_interviews_litellm.py
tests/active/integration/test_api_basic.py
tests/active/integration/test_automation_display.py
```

### Git History Analysis
Recent commits show system restructuring:
- 502acb2: GT workflow functional, test suite broken
- 8a44ead: LLM Reliability Investigation
- 1aeb370: Mock System Removal

## Root Cause
The codebase was restructured to use `src/qc/` directory structure but tests were not updated to match the new import paths.

## Resolution Strategy
Create and run an import fix script to update all 71 test files from `qc.` to `src.qc.` imports.
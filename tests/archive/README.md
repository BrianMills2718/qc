# Archived Tests

**Historical test files** from previous system versions and obsolete test approaches.

## Archive Categories

### `validation_system/`
**Tests from the old "validation system" architecture** - System focused on entity validation rather than code-first extraction.

**Contents**:
- `test_end_to_end_validation.py` - Complete validation workflow tests
- `test_integration_validation.py` - Validation component integration tests

**Historical Context**: These tests were written for a system that prioritized entity extraction with post-hoc validation. The current system uses code-first discovery, making these tests obsolete but preserved for architectural reference.

### `phase2_2/`  
**Tests from the "Phase 2.2" system version** - Historical versioning approach.

**Contents**:
- `test_end_to_end.py` - Complete system tests using old "MultiPassExtractor"

**Historical Context**: Tests reference "Phase 2.2 system" versioning and use deprecated components like `MultiPassExtractor`. Current system uses 4-phase code-first architecture.

### `duplicates/`
**Duplicate test files** removed from the active test suite to eliminate confusion.

**Contents**:
- `test_neo4j_connection.py` - Duplicate of connection tests (multiple versions existed)
- `test_neo4j_schema_compatibility.py` - Schema compatibility tests superseded by integration tests

**Reason for Archival**: Multiple copies of similar tests existed across unit/, integration/, and root directories. Active versions consolidated in `active/` directories.

## Purpose of Archive

**Why preserve these tests?**
- **Architectural reference** - Understanding previous system designs and approaches
- **Code archaeology** - Recovering useful patterns or test strategies from older versions
- **Migration validation** - Comparing old vs new system expectations and behaviors
- **Historical documentation** - Preserving evolution of testing approaches

## Usage Notes

**These tests should NOT be run** as part of the active test suite:
- ❌ May reference deprecated modules or APIs
- ❌ May expect different data structures or workflows  
- ❌ May conflict with current system architecture
- ❌ Not maintained or updated for current dependencies

**For reference only** - Examine code patterns, test strategies, or architectural decisions but do not execute.

## Migration Notes

**What was migrated to active tests**:
- **Neo4j connection logic** - Consolidated into `active/unit/test_neo4j_connection.py`
- **Integration patterns** - Adapted for 4-phase code-first architecture in `active/integration/`
- **End-to-end concepts** - Restructured for current pipeline in `active/e2e/`

**What was retired**:
- **Validation-specific workflows** - No longer applicable to code-first system
- **"Phase 2.2" versioning** - Replaced with semantic feature-based organization
- **Duplicate test logic** - Consolidated to eliminate redundancy
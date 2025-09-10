# Active Test Suite

**Production-ready tests** for the 4-Phase Code-First Extraction System.

## Directory Structure

### `unit/` - Component Isolation Tests
**Purpose**: Test individual components in isolation with mocked dependencies.

**Current Tests** (4 files):
- `test_entity_types_direct.py` - Entity type validation and processing
- `test_error_handling.py` - Exception handling and error recovery
- `test_neo4j_connection.py` - Database connection management
- `test_neo4j_direct.py` - Direct database operations

**Coverage**: Core components, error scenarios, database layer

### `integration/` - Cross-Component Tests  
**Purpose**: Test interaction between multiple system components.

**Current Tests** (16 files):
- **API Testing**: `test_api_*.py` - REST API endpoints and responses
- **Pipeline Testing**: `test_extraction_simple.py`, `test_phase4_baseline_only.py` - Multi-phase workflow
- **LLM Integration**: `test_gemini_integration.py`, `test_litellm_structured.py` - AI service integration
- **Configuration**: `test_config_*.py` - YAML configuration loading and validation
- **Quality Assurance**: `test_qca_*.py` - QCA methodology integration
- **Schema Validation**: `test_schema_*.py` - Data model validation
- **UI Integration**: `test_web_interface.py`, `test_automation_display.py` - Frontend components

**Coverage**: System integration, API layer, configuration management, LLM services

### `e2e/` - End-to-End Workflow Tests
**Purpose**: Test complete workflows from input files to final outputs.

**Current Tests** (3 files):
- `test_network_api_direct.py` - Network operations and API interactions
- `test_network_relationships.py` - Relationship extraction and storage
- `test_network_simple.py` - Basic network functionality

**Coverage**: Complete pipeline execution, real data processing, output validation

### `data/` - Test Input Files
**Sample interview content** for testing pipeline functionality:
- `sample_interview_test.txt` - Basic structured test interview
- `test_interview_real.txt` - Realistic interview content with complexity
- `test_simple.txt` - Minimal test case for unit testing

### `fixtures/` - Real Interview Files  
**Production interview files** for integration and end-to-end testing:
- **Focus Groups**: AI and methods focus group discussions (2 files)
- **Individual Interviews**: Researcher interviews about AI tools (4 files)
- **Format Testing**: DOCX files for document processing validation

## Test Execution

### Quick Commands
```bash
# All active tests
pytest tests/active/ -v

# By category
pytest tests/active/unit/ -v
pytest tests/active/integration/ -v  
pytest tests/active/e2e/ -v

# Specific test file
pytest tests/active/integration/test_extraction_simple.py -v

# With coverage
pytest tests/active/ --cov=src/qc --cov-report=html
```

### Test Markers
Current tests use these pytest markers:
- `@pytest.mark.integration` - Integration tests requiring multiple components
- `@pytest.mark.slow` - Long-running tests (>30 seconds)
- `@pytest.mark.api` - Tests requiring API connectivity
- `@pytest.mark.database` - Tests requiring Neo4j database

### Environment Requirements
**System Dependencies**:
- Neo4j database running on localhost:7687
- GEMINI_API_KEY environment variable set
- Python 3.11+ with all project requirements installed

**Test Dependencies**:
```bash
pip install pytest pytest-asyncio pytest-cov
```

## Test Quality Standards

### Unit Test Standards
- ✅ **Isolated components** - No external dependencies
- ✅ **Mocked services** - LLM and database calls mocked
- ✅ **Fast execution** - <5 seconds per test file
- ✅ **Clear assertions** - Specific expected outcomes

### Integration Test Standards  
- ✅ **Multi-component** - Tests interaction between 2+ components
- ✅ **Real services** - Uses actual LLM and database connections
- ✅ **Data validation** - Verifies complete data flow
- ✅ **Error scenarios** - Tests failure and recovery paths

### End-to-End Test Standards
- ✅ **Complete workflows** - Input files → final outputs
- ✅ **Real data** - Uses actual interview files
- ✅ **Output validation** - Verifies JSON structure and content
- ✅ **Performance bounds** - Completes within reasonable timeframes

## Contributing New Tests

### Test Placement Guidelines
- **Unit tests** → `unit/` - Single component, mocked dependencies
- **Integration tests** → `integration/` - Multiple components, real services  
- **End-to-end tests** → `e2e/` - Complete workflows, real data

### Test Naming Conventions
- `test_[component]_[functionality].py` - Descriptive component and feature
- `test_integration_[workflow].py` - Integration test workflows
- `test_e2e_[scenario].py` - End-to-end scenarios

### Required Elements
1. **Docstring** - Explain test purpose and expected outcomes
2. **Appropriate markers** - Use `@pytest.mark.*` for categorization
3. **Clean setup/teardown** - Use fixtures for resource management
4. **Clear assertions** - Specific, testable expectations
5. **Error testing** - Include negative test cases

### Fixture Usage
Leverage shared fixtures from `../conftest.py`:
- Database connections
- Sample data
- Configuration objects  
- Mock services

## Maintenance

### Regular Updates
- **API changes** - Update tests when endpoints change
- **Schema evolution** - Update validation tests for new data models
- **Performance regression** - Add tests for critical performance paths
- **New features** - Add comprehensive test coverage for new functionality

### Test Health
Monitor test suite health:
- **Execution time** - Keep individual tests under reasonable limits
- **Flaky tests** - Identify and fix intermittently failing tests
- **Coverage gaps** - Ensure new code has corresponding tests
- **Obsolete tests** - Remove tests for deprecated functionality

## Current Status

**Test Suite Health**: ✅ **Good**
- **Total active tests**: 23 test files
- **Coverage distribution**: Unit (17%), Integration (70%), E2E (13%)  
- **Execution time**: <5 minutes for complete suite
- **Success rate**: >95% on clean environment

**Recent Changes**:
- Reorganized from scattered 31 files to structured 23 active tests
- Archived 5 obsolete tests from previous system versions
- Updated all tests to use current 4-phase code-first architecture
- Consolidated duplicate Neo4j connection tests
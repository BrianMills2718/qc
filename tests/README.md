# Test Suite - Qualitative Coding Analysis Tool

Comprehensive test suite for the **4-Phase Code-First Extraction System**.

## Test Structure

### 🧪 `active/` - Current Working Tests
**Production test suite** for the code-first extraction system:

#### `active/unit/` - Unit Tests  
- **Component isolation tests** - Individual module functionality
- **Schema validation** - Data model correctness
- **Error handling** - Edge case and failure scenarios
- **Database operations** - Neo4j connection and query tests

#### `active/integration/` - Integration Tests
- **Pipeline integration** - Multi-component workflow tests  
- **API testing** - REST API endpoints and responses
- **LLM integration** - Gemini API interaction and schema validation
- **Configuration management** - YAML config loading and validation
- **System integration** - Cross-module interaction tests

#### `active/e2e/` - End-to-End Tests
- **Complete workflow** - Full extraction pipeline from input to output
- **Network operations** - API and database connectivity
- **Real data processing** - Interview files through complete system

#### `active/data/` & `active/fixtures/`
- **Test data files** - Sample interviews and expected outputs
- **Interview fixtures** - Real interview files for integration testing
- **Mock data** - Controlled test inputs for unit tests

### 📁 `archive/` - Historical Tests
**Preserved tests** from previous system versions:

#### `archive/validation_system/`  
- Tests from the old "validation system" architecture
- Preserved for reference and potential code archaeology

#### `archive/phase2_2/`
- Tests from the "Phase 2.2" system version
- Historical milestone testing approach

#### `archive/duplicates/`
- Duplicate test files removed from active suite
- Multiple neo4j connection tests and schema compatibility tests

### 🔧 `scripts/` - Test Utilities
- **Test runners** - Automated test execution scripts
- **API test scripts** - Comprehensive API validation
- **Integration helpers** - Test orchestration utilities

## Running Tests

### Quick Start
```bash
# Run all active tests
pytest tests/active/ -v

# Run specific test categories
pytest tests/active/unit/ -v              # Unit tests only
pytest tests/active/integration/ -v       # Integration tests only  
pytest tests/active/e2e/ -v              # End-to-end tests only

# Run with coverage
pytest tests/active/ --cov=src/qc --cov-report=html
```

### Test Environment Setup
```bash
# 1. Ensure system dependencies
./scripts/startup.sh                      # Start Neo4j and validate environment

# 2. Install test dependencies  
pip install pytest pytest-asyncio pytest-cov

# 3. Configure environment
# Ensure .env file contains GEMINI_API_KEY
# Verify Neo4j is running on localhost:7687
```

### Advanced Testing
```bash
# Run integration test suite script
python tests/scripts/run_integration_tests.py

# API comprehensive testing
bash tests/scripts/comprehensive_api_test.sh

# Run tests with specific markers
pytest tests/active/ -m "integration" -v
pytest tests/active/ -m "slow" -v
pytest tests/active/ -m "not slow" -v    # Skip slow tests
```

## Test Categories

### Unit Tests Coverage
- ✅ **Entity extraction** - Code, speaker, entity validation
- ✅ **Schema processing** - YAML configuration and data models  
- ✅ **Database operations** - Neo4j connectivity and queries
- ✅ **Error handling** - Exception scenarios and recovery

### Integration Tests Coverage  
- ✅ **4-Phase pipeline** - Complete code-first extraction workflow
- ✅ **LLM integration** - Gemini API calls and structured output
- ✅ **Configuration management** - Multiple config file types
- ✅ **API endpoints** - REST API functionality and responses
- ✅ **Multi-interview processing** - Batch processing capabilities

### End-to-End Tests Coverage
- ✅ **Real interview analysis** - Complete workflow with actual interview files
- ✅ **Output validation** - Verify expected JSON structure and content
- ✅ **Database storage** - Neo4j import and retrieval
- ✅ **Cross-interview analysis** - Multi-interview pattern detection

## Test Data

### Sample Interviews (`active/data/`)
- `sample_interview_test.txt` - Basic test interview
- `test_interview_real.txt` - Realistic interview content  
- `test_simple.txt` - Minimal test case

### Real Interview Fixtures (`active/fixtures/`)
- **Focus group files** - AI and methods focus group discussions
- **Individual interviews** - Researcher interviews about AI tools
- **Multiple formats** - DOCX interview files for format testing

## Expected Results

### Unit Test Expectations
- **Schema validation** - All data models validate correctly
- **Component isolation** - Each module functions independently
- **Error scenarios** - Graceful handling of edge cases
- **Database connectivity** - Reliable Neo4j connection management

### Integration Test Expectations  
- **Pipeline completion** - All 4 phases execute successfully
- **API responsiveness** - All endpoints return expected data
- **Configuration loading** - All YAML configs parse correctly
- **LLM integration** - Structured output meets schema requirements

### End-to-End Test Expectations
- **Complete analysis** - Interview files produce valid analysis results
- **Output structure** - JSON files match expected schema
- **Database storage** - All extracted data stored in Neo4j
- **Performance** - Analysis completes within acceptable timeframes

## Troubleshooting

### Common Issues

**Neo4j Connection Failures**
```bash
# Verify Neo4j is running
docker ps | grep neo4j

# Check connectivity
python -c "from qc.core.neo4j_manager import EnhancedNeo4jManager; import asyncio; asyncio.run(EnhancedNeo4jManager().connect())"
```

**API Key Issues**
```bash
# Verify API key is set
echo $GEMINI_API_KEY

# Test API connectivity  
python -c "from qc.core.native_gemini_client import NativeGeminiClient; client = NativeGeminiClient()"
```

**Test Environment Issues**
```bash
# Clean test environment
rm -rf test_output_*
rm -rf outputs/testing/*

# Reinstall dependencies
pip install -r requirements.txt
```

### Debug Mode
```bash
# Run with detailed output
pytest tests/active/ -v -s --tb=long

# Monitor performance
pytest tests/active/ --durations=10

# Generate coverage report
pytest tests/active/ --cov=src/qc --cov-report=html --cov-report=term
```

## Contributing Tests

### Adding New Tests
1. **Place in appropriate directory** - unit/, integration/, or e2e/
2. **Use descriptive names** - `test_[component]_[functionality].py`
3. **Include docstrings** - Explain test purpose and expected outcomes
4. **Use shared fixtures** - Leverage `conftest.py` fixtures
5. **Add appropriate markers** - `@pytest.mark.integration`, etc.

### Test Naming Conventions
- `test_unit_*.py` - Unit tests for specific components
- `test_integration_*.py` - Integration tests across components  
- `test_e2e_*.py` - End-to-end workflow tests
- `test_api_*.py` - API endpoint tests
- `test_*_simple.py` - Basic functionality tests

### Fixture Guidelines  
- **Use shared fixtures** from `conftest.py`
- **Clean up resources** in fixture teardown
- **Document fixture scope** - session, module, function
- **Mock external dependencies** when appropriate

## Test Metrics

Current test suite statistics:
- **Total active tests**: 20+ test files
- **Coverage areas**: Unit (4 files), Integration (16 files), E2E (3 files)  
- **Archived tests**: 5 obsolete test files preserved for reference
- **Test data**: 9 fixture files + 3 sample data files

## Integration with Development Workflow

Tests integrate with:
- **CI/CD pipelines** - Automated testing on code changes
- **Development scripts** - `scripts/startup.sh` includes test validation
- **Quality gates** - Tests must pass before deployment
- **Documentation** - Test results inform system documentation
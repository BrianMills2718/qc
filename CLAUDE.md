# Qualitative Coding Analysis System - WSL Migration and Web UI Completion

## 🚫 Development Philosophy (MANDATORY)

### Core Principles
- **NO LAZY IMPLEMENTATIONS**: No mocking, stubs, fallbacks, pseudo-code, or simplified implementations without explicit user permission
- **FAIL-FAST AND LOUD PRINCIPLES**: Surface errors immediately, don't hide them in logs or fallbacks
- **EVIDENCE-BASED DEVELOPMENT**: All claims require raw execution evidence with structured validation
- **TEST-DRIVEN DEVELOPMENT**: Write failing tests first, then implement to pass
- **THIS IS NOT A PRODUCTION SYSTEM**: Focus on research functionality, not enterprise features

## 📁 Codebase Structure

### Current Implementation Status: CLI + API Complete, Web UI Issues on Windows ✅
- **Server Foundation**: ✅ Complete - FastAPI with uvicorn HTTP binding on port 8002
- **API Endpoints**: ✅ Complete - Real LLM analysis (no demo mode), document processing
- **CLI System**: ✅ Complete - Full CLI with analyze, query, status, server commands
- **Document Processing**: ✅ Complete - .txt, .docx, .pdf, .rtf support with proper text extraction
- **Web UI Foundation**: ✅ Complete - Direct API integration (no subprocess complexity)
- **Windows Issues**: 🚨 **IDENTIFIED** - Unicode encoding, file paths, process permissions

### Key Entry Points
- **API Server**: `qc_clean/plugins/api/api_server.py` - Real qualitative coding analysis (fail-fast LLM calls)
- **CLI Interface**: `qc_cli.py` - Comprehensive command-line interface
- **Web UI**: `direct_ui.py` - Direct API integration (Flask app on port 5002)
- **API Client**: `qc_clean/core/cli/api_client.py` - HTTP client with document format support
- **LLM Handler**: `qc_clean/core/llm/llm_handler.py` - Real analysis using complete_raw() method

### Working Components
- **API Server** (port 8002): Real LLM analysis, job tracking, document processing
- **CLI Commands**: analyze, query, status, server with proper error handling
- **Document Support**: Text extraction from .txt, .docx, .pdf, .rtf files
- **Web Interface** (port 5002): Upload files → API analysis → display results

### Windows Compatibility Issues Identified
1. **Unicode/Encoding**: Subprocess calls fail with emoji/Unicode CLI output
2. **File Path Spaces**: Windows paths with spaces break command parsing
3. **Process Permissions**: Windows process spawning restrictions cause failures

## 🎯 NEXT PHASE: WSL Migration and Web UI Completion

### **OBJECTIVE**
Migrate to WSL to resolve Windows compatibility issues and complete the web UI implementation using the CLI-to-Web subprocess pattern that should work seamlessly on Linux.

### **Success Criteria**
- **CLI-Web Integration**: Web UI successfully calls CLI commands via subprocess
- **File Upload Pipeline**: Upload → Save → CLI Analysis → Results Display
- **Cross-Format Support**: Handle .txt, .docx, .pdf, .rtf uploads seamlessly
- **Error Handling**: Clear, actionable error messages for users
- **Performance**: Analysis completes with real results, not demo data

## 📋 IMPLEMENTATION TASKS: WSL Migration

### **Task 1: Environment Migration** ⚡ PRIORITY 1

**Goal**: Set up complete development environment in WSL

**Implementation Requirements**:
1. **WSL Setup and Project Migration**:
   - Install Ubuntu WSL2
   - Clone repository to WSL filesystem
   - Install Python 3.11+ and required packages
   - Set up .env file with API keys

2. **Dependency Installation**:
   ```bash
   pip install fastapi uvicorn python-docx PyPDF2 striprtf requests flask
   pip install litellm neo4j pydantic python-dotenv
   ```

3. **Verification Steps**:
   ```bash
   python start_server.py  # API server on port 8002
   python qc_cli.py --help  # CLI interface working
   python direct_ui.py     # Web UI on port 5002
   ```

**Evidence Requirements**:
- All three components start without errors in WSL
- API health check returns successful response
- CLI commands execute and return proper help output
- Document test files (.docx samples) upload successfully

### **Task 2: CLI-Web Integration** ⚡ PRIORITY 2

**Goal**: Implement subprocess-based web UI that calls CLI commands

**Implementation Requirements**:
1. **Create `simple_cli_web.py`**:
   - Flask app that saves uploaded files to WSL filesystem
   - Execute CLI commands via subprocess with proper encoding
   - Parse CLI output and display formatted results
   - Handle file paths without Windows space issues

2. **Subprocess Integration**:
   ```python
   # This should work seamlessly in WSL/Linux:
   result = subprocess.run([
       "python", "qc_cli.py", "analyze", "--files", file_path, "--format", "json"
   ], capture_output=True, text=True, encoding='utf-8')
   ```

3. **File Upload Workflow**:
   ```
   User uploads files → Save to /tmp/uploads/ → 
   Execute: python qc_cli.py analyze --files /tmp/uploads/file.docx →
   Parse JSON output → Display results in web interface
   ```

**Evidence Requirements**:
- File uploads save correctly to WSL filesystem
- CLI commands execute without encoding errors
- JSON output parses and displays properly in web interface
- Error messages from CLI surface clearly in web UI

### **Task 3: Real Analysis Integration** ⚡ PRIORITY 3

**Goal**: Ensure real LLM analysis works through the CLI-web pipeline

**Implementation Requirements**:
1. **Environment Configuration**:
   - Set up API keys in WSL .env file
   - Verify LLM handler can connect to OpenAI/Anthropic APIs
   - Test real analysis with sample documents

2. **Analysis Pipeline Testing**:
   ```bash
   # Test CLI analysis works:
   python qc_cli.py analyze --files test_interview.txt --format json
   
   # Should return real analysis with:
   # - "demo_mode": false
   # - Actual themes from document content
   # - Processing time >5 seconds for real LLM calls
   ```

3. **Web Integration Validation**:
   - Upload same test file via web UI
   - Verify results match CLI output
   - Confirm no "fallback_mode" or demo results

**Evidence Requirements**:
- Real LLM analysis produces content-specific themes and codes
- Processing time reflects actual LLM API calls (5-30 seconds)
- Results show "demo_mode": false and include "model_used" field
- CLI and web interfaces return identical analysis results

### **Task 4: Document Format Support** ⚡ PRIORITY 4

**Goal**: Verify all document formats work through WSL CLI-web pipeline

**Implementation Requirements**:
1. **Format Testing**:
   - Test .docx upload and text extraction
   - Test .pdf upload and text extraction  
   - Test .rtf upload and text extraction
   - Test .txt direct processing

2. **Error Handling**:
   - Unsupported formats show clear error messages
   - Corrupted files handled gracefully
   - Large files processed or rejected appropriately

3. **Integration Validation**:
   ```bash
   # Test each format via CLI:
   python qc_cli.py analyze --files sample.docx --format json
   python qc_cli.py analyze --files sample.pdf --format json
   python qc_cli.py analyze --files sample.txt --format json
   ```

**Evidence Requirements**:
- Each format extracts text content successfully
- Analysis results reflect actual document content
- Error messages provide actionable guidance for users
- Web interface handles all formats seamlessly

### **Task 5: Performance and Error Handling** ⚡ PRIORITY 5

**Goal**: Optimize performance and implement comprehensive error handling

**Implementation Requirements**:
1. **Performance Optimization**:
   - Add progress indicators for long-running analysis
   - Implement timeout handling for LLM API calls
   - Cache results for identical file uploads

2. **Error Scenarios**:
   - Server not running → Clear guidance to start API server
   - API key missing → Specific configuration instructions
   - Network issues → Retry logic with user feedback
   - File processing errors → Format-specific guidance

3. **User Experience**:
   ```python
   # Web interface should show:
   # - "Analysis starting..." 
   # - Progress updates during processing
   # - Clear success/error states
   # - Actionable error messages
   ```

**Evidence Requirements**:
- Long-running analysis shows progress to users
- All error scenarios provide clear next steps
- Performance meets expectations (real analysis in 10-60 seconds)
- User experience flows smoothly from upload to results

## 🛡️ Quality Standards & Validation Framework

### **Evidence Structure Requirements**
```
evidence/
├── current/
│   └── Evidence_WSL_Migration.md         # Current WSL migration evidence
├── completed/  
│   └── Evidence_CLI_Implementation.md    # Completed CLI phase (archived)
```

### **Evidence Requirements (MANDATORY)**
- **Environment Migration**: All components working in WSL environment
- **CLI-Web Integration**: Subprocess calls working without Windows issues
- **Real Analysis**: LLM analysis producing content-specific results
- **Document Processing**: All formats extracting text correctly

### **Success Criteria Validation**
```python
# WSL migration must demonstrate:
def validate_wsl_migration():
    assert api_server_starts_in_wsl()           # Port 8002 accessible
    assert cli_commands_work_in_wsl()           # All qc_cli.py commands functional
    assert web_ui_calls_cli_successfully()     # Subprocess integration working
    assert real_llm_analysis_produces_results() # No demo mode, real content analysis
    assert document_formats_process_correctly() # .txt, .docx, .pdf, .rtf working
    return "WSL migration and CLI-web integration validated"
```

### **Anti-Patterns to Avoid**
❌ Continuing to develop on Windows with compatibility workarounds
❌ Reverting to demo mode or fallback implementations
❌ Complex subprocess alternatives instead of simple Linux/WSL solutions
❌ Ignoring document format edge cases

## Integration Points

### **WSL Environment Setup**
- **File System**: Use Linux paths (/home/user/project/), no Windows drive mapping
- **Process Model**: Standard Linux subprocess.run() without encoding issues
- **Text Encoding**: UTF-8 throughout the pipeline
- **File Permissions**: Standard Unix permissions, no Windows restrictions

### **CLI-Web Integration**
- **Upload Directory**: `/tmp/uploads/` for temporary file storage
- **Command Execution**: Direct Python subprocess calls to qc_cli.py
- **Output Parsing**: JSON parsing of CLI command output
- **Error Handling**: CLI stderr captured and displayed in web interface

## Development Notes for New LLM Context
- **Current Status**: CLI and API components are complete and functional
- **Windows Issues**: Unicode subprocess encoding, file path spaces, process permissions
- **WSL Solution**: Should resolve all Windows compatibility issues
- **Architecture**: CLI-web subprocess pattern is architecturally sound, just needs Linux environment
- **Real Analysis**: LLM integration is working, removed demo mode, using complete_raw() method
- **Document Support**: Text extraction implemented for all major formats

The WSL migration should resolve the Windows-specific issues and allow the CLI-web integration pattern to work as originally intended.
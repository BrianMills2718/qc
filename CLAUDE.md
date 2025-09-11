# Qualitative Coding Analysis System - CLI Wrapper Implementation Phase

## 🚫 Development Philosophy (MANDATORY)

### Core Principles
- **NO LAZY IMPLEMENTATIONS**: No mocking, stubs, fallbacks, pseudo-code, or simplified implementations without explicit user permission
- **FAIL-FAST AND LOUD PRINCIPLES**: Surface errors immediately, don't hide them in logs or fallbacks
- **EVIDENCE-BASED DEVELOPMENT**: All claims require raw execution evidence with structured validation
- **TEST-DRIVEN DEVELOPMENT**: Write failing tests first, then implement to pass
- **THIS IS NOT A PRODUCTION SYSTEM**: Focus on research functionality, not enterprise features

## 📁 Codebase Structure

### Current Implementation Status: WEB UI INTEGRATION COMPLETE ✅
- **Server Foundation**: ✅ Complete - FastAPI with uvicorn HTTP binding on port 8002
- **API Endpoints**: ✅ Complete - Natural language query processing and analysis endpoints
- **UI Integration**: ✅ Complete - React frontend with static file serving and CORS
- **Database Integration**: ✅ Complete - Real Neo4j data flowing through all endpoints
- **Analysis Pipeline**: ✅ Complete - Demo mode analysis with realistic mock results
- **Frontend-Backend**: ✅ Complete - Full request-response cycle functional

### Key Entry Points
- **API Server**: `qc_clean/plugins/api/api_server.py` - FastAPI application with working endpoints
- **Server Startup**: `start_server.py` - Development server with dependency checking
- **Query Processing**: `qc_clean/plugins/api/query_endpoints.py` - Neo4j integration complete
- **Environment Config**: `qc_clean/core/config/env_config.py` - Configuration system with .env support
- **Existing CLI Infrastructure**: `qc_clean/core/cli/cli_robust.py` - Robust CLI foundation available

### Working API Endpoints (Port 8002)
- `GET /health` - Health check
- `POST /analyze` - Start analysis (returns job_id, completes in 2 seconds with demo results)
- `GET /jobs/{job_id}` - Get job status and results
- `POST /api/query/natural-language` - Natural language to Cypher conversion
- `GET /api/query/health` - Query system health check

## 🎯 NEXT PHASE: CLI Wrapper Implementation

### **OBJECTIVE**
Create a command-line interface that wraps the existing API functionality, providing file analysis and natural language querying from the terminal.

### **Success Criteria**
- **File Analysis**: Users can analyze interview files via command line
- **Natural Language Queries**: Users can perform queries from terminal
- **Progress Monitoring**: Real-time feedback on analysis jobs
- **Error Handling**: Clear, actionable error messages
- **Multiple Formats**: Support for various output formats (JSON, table, human-readable)

## 📋 IMPLEMENTATION TASKS: CLI Wrapper

### **Task 1: Create Main CLI Entry Point** ⚡ PRIORITY 1

**Goal**: Build the main CLI application with argument parsing and command routing

**Implementation Requirements**:
1. **Create `qc_cli.py` in project root**:
   - Use `argparse` for command parsing
   - Support subcommands: `analyze`, `query`, `status`, `server`, `config`
   - Global error handling with meaningful messages
   - Logging configuration for CLI operations

2. **Command Structure**:
   ```bash
   qc_cli.py analyze --files file1.txt file2.docx
   qc_cli.py query "Find codes related to communication"
   qc_cli.py status --job JOB_ID
   qc_cli.py server --start
   qc_cli.py config --show
   ```

3. **Error Handling Requirements**:
   - Network errors → Clear message + server start suggestion
   - File errors → Path validation and format guidance
   - API errors → Parse and display meaningful responses

**Evidence Requirements**:
- Working `qc_cli.py --help` output showing all commands
- Basic command routing functional (even with stub implementations)
- Error handling demonstrates helpful user guidance

### **Task 2: Implement API Client Module** ⚡ PRIORITY 2

**Goal**: Create HTTP client for communicating with existing API server

**Implementation Requirements**:
1. **Create `qc_clean/core/cli/api_client.py`**:
   - HTTP client using `requests` or `httpx`
   - Base URL configuration (default: http://127.0.0.1:8002)
   - Request/response handling with proper error parsing
   - Retry logic for network issues

2. **API Methods Required**:
   ```python
   class APIClient:
       def health_check(self) -> bool
       def start_analysis(self, files: List[str], config: dict) -> str  # returns job_id
       def get_job_status(self, job_id: str) -> dict
       def natural_language_query(self, query: str) -> dict
   ```

3. **Error Handling**:
   - Connection refused → "Server not running, use 'qc_cli.py server --start'"
   - API errors → Parse JSON error responses and display clearly
   - Timeouts → Graceful handling with user notification

**Evidence Requirements**:
- API client can communicate with running server (port 8002)
- All four core API methods functional with proper error handling
- Connection error produces helpful guidance message

### **Task 3: Implement Analysis Command** ⚡ PRIORITY 3

**Goal**: Enable file analysis through command line interface

**Implementation Requirements**:
1. **Create `qc_clean/core/cli/commands/analyze.py`**:
   - File validation and reading (support .txt, .docx formats initially)
   - Submit files to `/analyze` endpoint
   - Monitor job progress with polling
   - Display results in human-readable format

2. **Command Options**:
   ```bash
   qc_cli.py analyze --files interview1.txt interview2.docx
   qc_cli.py analyze --directory /path/to/interviews/
   qc_cli.py analyze --watch-job JOB_ID
   qc_cli.py analyze --format json|table|human
   ```

3. **Progress Display**:
   - Show "Analysis submitted, Job ID: job_xyz"
   - Poll job status every 2 seconds until completion
   - Display progress indicator or status updates
   - Show final results with codes, themes, recommendations

**Evidence Requirements**:
- Can analyze actual files and get demo results
- Progress monitoring works from submission to completion
- Results display includes codes, themes, and recommendations
- File validation prevents invalid submissions

### **Task 4: Implement Query Command** ⚡ PRIORITY 4

**Goal**: Enable natural language queries from command line

**Implementation Requirements**:
1. **Create `qc_clean/core/cli/commands/query.py`**:
   - Single query mode: `qc_cli.py query "Find communication codes"`
   - Interactive mode: `qc_cli.py query --interactive`
   - Query history tracking
   - Result formatting and display

2. **Interactive Mode Features**:
   - Prompt loop with readline support
   - Command history navigation
   - Exit commands (`exit`, `quit`, Ctrl+C)
   - Help text and examples

3. **Output Formatting**:
   - Human-readable results by default
   - JSON format option for programmatic use
   - Table format for structured display

**Evidence Requirements**:
- Single queries return properly formatted results
- Interactive mode provides usable query interface
- Different output formats work correctly
- Query history functionality operational

### **Task 5: Implement Status and Server Commands** ⚡ PRIORITY 5

**Goal**: Provide system status monitoring and server management

**Implementation Requirements**:
1. **Create `qc_clean/core/cli/commands/status.py`**:
   - Overall system health check
   - Specific job status monitoring
   - Server connectivity verification

2. **Create `qc_clean/core/cli/commands/server.py`**:
   - Server start/stop functionality (subprocess management)
   - Health monitoring and port checking
   - Configuration display

3. **Status Command Options**:
   ```bash
   qc_cli.py status                    # Overall system health
   qc_cli.py status --job JOB_ID       # Specific job status
   qc_cli.py status --server           # Server connectivity
   ```

**Evidence Requirements**:
- Status commands provide accurate system information
- Server management works for development server
- Health checks validate API connectivity properly

## 🛡️ Quality Standards & Validation Framework

### **Evidence Structure Requirements**
```
evidence/
├── current/
│   └── Evidence_CLI_Implementation.md     # Current CLI development evidence
├── completed/  
│   └── Evidence_WebUI_Integration.md      # Completed web UI phase (archived)
```

### **Evidence Requirements (MANDATORY)**
- **Functional Validation**: All CLI commands work with real API server
- **Error Handling**: Demonstrate graceful failure scenarios with helpful messages
- **Integration Testing**: Full workflow from file input to results display
- **Performance Validation**: Commands respond within 2 seconds for simple operations

### **Success Criteria Validation**
```python
# CLI wrapper must demonstrate:
def validate_cli_implementation():
    assert cli_analyze_command_works()              # File analysis functional
    assert natural_language_queries_work()         # Query interface operational
    assert progress_monitoring_functional()        # Job status tracking works
    assert error_messages_helpful()                # User guidance provided
    assert multiple_output_formats_supported()     # JSON, table, human formats
    return "CLI wrapper implementation validated"
```

### **Anti-Patterns to Avoid**
❌ Mocking the API server instead of using real integration
❌ Complex enterprise features not needed for research tool
❌ Silent failures or cryptic error messages
❌ Blocking operations without progress indicators

## File Structure for Implementation

### **Required Files to Create**
```
qc_cli.py                              # Main entry point (create in project root)
qc_clean/core/cli/
├── api_client.py                      # HTTP client for API communication
├── commands/
│   ├── __init__.py                    # Command module initialization
│   ├── analyze.py                     # File analysis commands
│   ├── query.py                       # Natural language query commands
│   ├── status.py                      # Status monitoring commands
│   └── server.py                      # Server management commands
├── formatters/
│   ├── __init__.py                    # Formatter module initialization
│   ├── human_formatter.py            # Human-readable output
│   ├── json_formatter.py             # JSON output formatting
│   └── table_formatter.py            # Table format output
└── utils/
    ├── __init__.py                    # Utilities module initialization
    ├── file_handler.py               # File operations and validation
    └── progress.py                   # Progress monitoring utilities
```

## Integration Points

### **API Server Integration**
- **Base URL**: http://127.0.0.1:8002 (configurable via environment)
- **Authentication**: None required for current demo system
- **Endpoints**: Use existing working endpoints documented above
- **Job Polling**: 2-second intervals for analysis job monitoring

### **File System Integration**
- **Supported Formats**: .txt, .docx (extensible architecture for others)
- **Directory Scanning**: Recursive file discovery with format filtering
- **File Validation**: Size limits, format verification, permission checks

### **Configuration Integration**
- **Environment Variables**: Use existing .env configuration system
- **CLI Settings**: API URL, output format preferences, polling intervals
- **User Preferences**: Persistent settings for commonly used options

## Development Notes
- **Current Server**: Running on port 8002 via `python start_server.py`
- **Demo Analysis**: Returns realistic qualitative coding results in 2 seconds
- **API Testing**: Use `curl` commands for validation during development
- **Error Scenarios**: Test with server down, invalid files, malformed queries
- **Output Formats**: Design for both human users and programmatic consumption

This CLI wrapper should provide a professional command-line interface to the existing qualitative coding analysis system, making it accessible for researchers who prefer terminal-based workflows.
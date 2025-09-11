# Scripts Directory

Operational utilities and automation scripts for the Qualitative Coding Analysis Tool.

## Quick Start Scripts

### System Startup
**Cross-platform system initialization with full validation**

#### `startup.sh` (Unix/Mac/WSL)
```bash
./scripts/startup.sh
```

#### `startup.bat` (Windows)  
```batch
scripts\startup.bat
```

**What startup scripts do**:
1. ✅ Verify Docker installation and status
2. 🐳 Start Neo4j database container (`docker-compose up -d`)
3. 🔗 Test Neo4j connectivity on port 7474
4. ⚙️ Validate environment configuration (.env file and API keys)
5. 🧪 Run quick system validation tests
6. 📋 Display usage instructions and next steps

**Requirements**: Docker Desktop, .env file with GEMINI_API_KEY

## Operational Scripts

### Data Processing (`data_processing/`)

#### `reprocess_all_interviews_with_entity_fix.py`
**Full interview re-processing with updated extraction logic**
```bash
python scripts/data_processing/reprocess_all_interviews_with_entity_fix.py
```

**Purpose**:
- Re-processes all interviews using current LLM prompts and validation
- Fixes entity extraction issues from previous system versions
- Updates Neo4j knowledge graph with improved data quality
- Handles 16+ interviews with complete three-layer knowledge graph

**Use cases**:
- After major prompt improvements
- Fixing data quality issues in existing analyses
- Migrating to new system versions

### Deployment (`deployment/`)

Development server management utilities for rapid iteration:

#### `restart_server.py` 
**Standard server restart with process cleanup**
```bash
python scripts/deployment/restart_server.py
```

#### `simple_restart.py`
**Quick restart for minor changes**
```bash  
python scripts/deployment/simple_restart.py
```

#### `force_server_restart.py`
**Aggressive restart when servers are stuck**
```bash
python scripts/deployment/force_server_restart.py
```

#### `complete_server_restart.py`
**Full system restart including database connections**
```bash
python scripts/deployment/complete_server_restart.py
```

**All deployment scripts**:
- Kill existing Python server processes on port 8000
- Clean up orphaned connections
- Restart dashboard/API servers with fresh state
- Handle process management across Windows/Unix

## Usage Patterns

### First-Time Setup
```bash
# 1. System startup
./scripts/startup.sh

# 2. Run analysis (as shown by startup script)
python run_code_first_extraction.py extraction_config.yaml

# 3. View results
python start_dashboard.py
```

### Development Workflow
```bash
# Make code changes...

# Quick restart for minor changes
python scripts/deployment/simple_restart.py

# Or full restart for major changes  
python scripts/deployment/complete_server_restart.py
```

### Data Management
```bash
# Re-process after system improvements
python scripts/data_processing/reprocess_all_interviews_with_entity_fix.py
```

## Script Dependencies

**System Requirements**:
- Python 3.11+ with project requirements installed
- Docker Desktop running
- .env file with API keys configured

**Python Packages Used**:
- `psutil` - Process management in deployment scripts
- `asyncio` - Async processing in data scripts  
- `pathlib` - File system operations
- Project modules (`qc.*`) - Core system integration

## Troubleshooting

### Startup Issues
- **Docker not found**: Install Docker Desktop
- **Neo4j connection failed**: Check `docker logs qualitative_coding_neo4j_1`
- **API key missing**: Verify .env file contains `GEMINI_API_KEY=your_key`

### Server Issues  
- **Port 8000 in use**: Run `force_server_restart.py`
- **Processes won't die**: Check Task Manager/Activity Monitor manually
- **Database connections stuck**: Use `complete_server_restart.py`

### Data Processing Issues
- **Interviews not found**: Check `interviews_dir` path in script
- **LLM failures**: Verify API key and network connectivity
- **Neo4j errors**: Ensure database is running and accessible

## Integration with Main System

These scripts integrate with:
- **Main extraction pipeline**: `run_code_first_extraction.py`
- **Dashboard system**: `start_dashboard.py`  
- **Configuration system**: Uses project YAML configs
- **Documentation**: See `docs/user-guides/getting-started.md` for workflow integration
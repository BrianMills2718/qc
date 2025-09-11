# Configuration Guide - Qualitative Coding Analysis Tool

**Purpose**: Comprehensive guide to all configuration files and environment setup for the qualitative coding system.

**Last Updated**: 2025-08-26  
**Status**: Current and complete configuration documentation

---

## Configuration Architecture Overview

### **Configuration Philosophy**
- **Single Source of Truth**: Each config type has one authoritative location
- **Environment-Aware**: Development, staging, and production configurations
- **Template-Based**: Easy setup with provided templates
- **Security-First**: Sensitive data handled via environment variables

### **Configuration Categories**
1. **Extraction Pipeline Configuration** - Main analysis workflow settings
2. **Environment Configuration** - Runtime environment and API keys
3. **Database Configuration** - Neo4j connection and security
4. **Docker Configuration** - Containerization and deployment
5. **Schema Configuration** - Entity and relationship definitions

---

## Core Configuration Files

### **1. Extraction Pipeline Configuration**

#### **Primary Config: `extraction_config.yaml`** (Root Level)
**Purpose**: Main configuration for the code-first extraction pipeline  
**Status**: ✅ **Authoritative** - Used by production system

```yaml
# Research question driving the analysis
analytic_question: "How are researchers experiencing and adapting to the integration of AI tools in qualitative research methods?"

# Directory containing interview files (DOCX or TXT)
interview_files_dir: "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews_3_for_test"

# Extraction approaches (open, closed, or mixed)
coding_approach: open
speaker_approach: open
entity_approach: open

# Output configuration
output_dir: "outputs/current"
auto_import_neo4j: true

# Neo4j connection settings (using existing Docker container)
neo4j_uri: "bolt://localhost:7687"
neo4j_user: "neo4j"
neo4j_password: "devpassword"  # Matches existing Docker container

# LLM configuration
llm_model: "gemini/gemini-2.5-flash"
temperature: 0.1

# Analysis paradigm (optional)
paradigm: "expert_qualitative_coder"

# Performance configuration
max_concurrent_interviews: 1

# Code hierarchy depth
code_hierarchy_depth: 3
```

#### **Usage**:
```bash
python run_code_first_extraction.py extraction_config.yaml
```

#### **Configuration Options**:

**Extraction Approaches**:
- `open`: Discover codes/speakers/entities from data
- `closed`: Use predefined schemas only
- `mixed`: Start with predefined, discover additional

**Coding Paradigms**:
- `expert_qualitative_coder`: Standard thematic analysis
- `phenomenological`: Phenomenological research approach
- `critical_theory`: Critical theory lens
- `constructivist`: Constructivist grounded theory
- `feminist`: Feminist research methodology
- `postmodern`: Postmodern analytical approach

**LLM Models** (via LiteLLM):
- `gemini/gemini-2.5-flash`: Fast, cost-effective (recommended)
- `gemini/gemini-2.5-pro`: Higher quality, slower
- `gpt-4`: OpenAI GPT-4 (requires OPENAI_API_KEY)
- `claude-3-sonnet`: Anthropic Claude (requires ANTHROPIC_API_KEY)

### **2. Environment Configuration**

#### **Development: `.env`** (Root Level)
**Purpose**: Development environment variables and API keys  
**Status**: ✅ **Active** - Used by development system  
**Security**: ⚠️ **Not in Git** - Contains actual API keys

**Required Variables**:
```bash
# LLM API Keys
GEMINI_API_KEY=your_actual_gemini_key_here
OPENAI_API_KEY=your_openai_key_here  # Optional
ANTHROPIC_API_KEY=your_anthropic_key_here  # Optional

# Database
NEO4J_PASSWORD=your_neo4j_password
NEO4J_ENABLED=true

# Security
SECRET_KEY=your_32_character_secret_key_here
ENVIRONMENT=development
```

#### **Production: `.env.production.template`** (Root Level)
**Purpose**: Production environment template  
**Usage**: Copy to `.env.production` and fill in values

```bash
# Environment Setting
ENVIRONMENT=production

# Database Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_neo4j_password_here

# LLM API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Security Configuration
SECRET_KEY=your_32_character_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Performance Configuration
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT_SECONDS=300
DATABASE_POOL_SIZE=10
```

#### **Environment Management (Code)**
Environment configuration is handled by `src/qc/config/environment.py`:

```python
from qc.config.environment import get_config, is_production, is_development

# Get current configuration
config = get_config()

# Environment-specific behavior
if is_production():
    # Production settings
    pass
elif is_development():
    # Development settings  
    pass
```

### **3. Database Configuration**

#### **Neo4j Development: `docker-compose.yml`** (config/docker/)
**Purpose**: Local development Neo4j instance

```yaml
services:
  neo4j:
    image: neo4j:5-community
    container_name: qualitative_coding_neo4j
    ports:
      - "7474:7474"  # Web interface
      - "7687:7687"  # Bolt protocol
    environment:
      - NEO4J_AUTH=none  # Development only!
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data
    mem_limit: 2g
    cpus: 1.5
```

#### **Neo4j Production: `docker-compose.production.yml`** (config/docker/)
**Purpose**: Production Neo4j with security and resource management

```yaml
neo4j:
  image: neo4j:5.15
  environment:
    - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:-production_password}
    - NEO4J_PLUGINS=["apoc"]
    - NEO4J_dbms_memory_heap_max_size=2G
    - NEO4J_dbms_memory_pagecache_size=1G
  volumes:
    - neo4j_data:/data
    - neo4j_logs:/logs
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD}", "RETURN 1"]
    interval: 30s
    timeout: 10s
    retries: 5
```

**Usage**:
```bash
# Development
cd config/docker && docker-compose up -d

# Production
cd config/docker && docker-compose -f docker-compose.production.yml up -d
```

### **4. Schema Configuration**

#### **Research Schema: `src/qc/core/research_schema.yaml`**
**Purpose**: Defines entity types, properties, and relationships for qualitative research  
**Status**: ✅ **Active** - Used by system via `create_research_schema()`

**Entity Types Defined**:
- **Person**: Researchers, participants, mentioned individuals
- **Organization**: Institutions, companies, departments
- **Method**: Research methods, analytical approaches
- **Tool**: Software tools, AI systems, platforms
- **Quote**: Individual quotes with line-based tracking

**Usage in Code**:
```python
from qc.core.schema_config import create_research_schema

schema = create_research_schema()
```

**Customization**: Modify `src/qc/core/research_schema.yaml` for different research domains

### **5. Testing Configuration**

#### **Pytest: `config/pytest.ini`**
**Purpose**: Python testing configuration

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_paths = src
markers =
    asyncio: marks tests as async
```

---

## Configuration Management Patterns

### **Environment-Specific Loading**

The system supports multiple environment configurations:

1. **Development** (`.env`)
   - Local development with debugging
   - Relaxed security for testing
   - Local file paths and development databases

2. **Production** (`.env.production`)
   - Secure API key handling
   - Production database connections
   - Performance optimizations
   - Security hardening

3. **Docker** (docker-compose files)
   - Containerized environments
   - Service orchestration
   - Resource management

### **Configuration Precedence**

Configuration values are loaded in this order (later values override earlier):

1. **Default values** (in code)
2. **YAML config files** (extraction_config.yaml)
3. **Environment files** (.env, .env.production)
4. **Environment variables** (direct OS environment)
5. **Command line arguments** (when applicable)

### **Security Best Practices**

✅ **Implemented Security Measures**:
- API keys stored in environment variables only
- Production passwords with minimum 8 character requirement
- Secret keys with minimum 32 character requirement
- Allowed hosts restriction in production
- Non-root Docker containers
- Resource limits and health checks

❌ **Never Do This**:
- Commit actual API keys to git
- Use default passwords in production
- Store secrets in YAML config files
- Run production containers as root

---

## Configuration Setup Guide

### **1. Initial Setup (New Installation)**

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your API keys
# GEMINI_API_KEY=your_actual_key_here

# 3. Start Neo4j database
cd config/docker
docker-compose up -d

# 4. Copy and customize extraction config  
cp extraction_config.yaml my_project_config.yaml
# Edit paths and settings as needed

# 5. Run extraction
python run_code_first_extraction.py my_project_config.yaml
```

### **2. Production Deployment**

```bash
# 1. Create production environment file
cp .env.production.template .env.production
# Fill in production values

# 2. Deploy with Docker
cd config/docker
docker-compose -f docker-compose.production.yml up -d

# 3. Configure extraction for production paths
cp extraction_config.yaml production_config.yaml
# Update interview_files_dir for production data location

# 4. Run production extraction
python run_code_first_extraction.py production_config.yaml
```

### **3. Custom Research Domain Setup**

```bash
# 1. Copy schema template
cp src/qc/core/research_schema.yaml custom_research_schema.yaml
# Customize entities and relationships for your domain

# 2. Update schema loading (if needed)
# Modify create_research_schema() to load custom schema

# 3. Create domain-specific extraction config
cp extraction_config.yaml domain_config.yaml
# Set analytic_question and paradigm for your research domain
```

---

## Troubleshooting Configuration Issues

### **Common Problems**

#### **"GEMINI_API_KEY not found"**
**Cause**: Missing or incorrectly named environment variable  
**Solution**: 
```bash
# Check if .env file exists
ls -la .env

# Add API key to .env
echo "GEMINI_API_KEY=your_key_here" >> .env
```

#### **"Neo4j connection failed"**
**Cause**: Neo4j container not running or wrong connection settings  
**Solution**:
```bash
# Check Neo4j container status
docker ps | grep neo4j

# Restart Neo4j
cd config/docker && docker-compose restart neo4j

# Check connection settings in extraction_config.yaml
```

#### **"Interview files not found"**
**Cause**: Incorrect interview_files_dir path in extraction_config.yaml  
**Solution**: Update path to match your actual data location

#### **"Permission denied writing to output directory"**
**Cause**: Insufficient permissions or directory doesn't exist  
**Solution**:
```bash
# Create output directory
mkdir -p output_production

# Fix permissions (if needed)
chmod 755 output_production
```

### **Configuration Validation**

```bash
# Test configuration loading
python -c "
from qc.extraction.code_first_schemas import ExtractionConfig
import yaml
with open('extraction_config.yaml') as f:
    config_data = yaml.safe_load(f)
config = ExtractionConfig(**config_data)
print('✅ Configuration valid')
"

# Test environment setup
python tests/current/test_config_setup.py

# Test database connection
python test_neo4j_connection.py
```

---

## Advanced Configuration

### **Multiple Project Configurations**

Organize configurations for different research projects:

```
project_configs/
├── ai_research_config.yaml
├── healthcare_study_config.yaml
├── education_analysis_config.yaml
└── .env_ai_research
```

**Usage**:
```bash
# Set environment for specific project
cp project_configs/.env_ai_research .env

# Run with project-specific config
python run_code_first_extraction.py project_configs/ai_research_config.yaml
```

### **Custom LLM Model Configuration**

Add new models via environment variables in `.env`:

```bash
# Custom model configurations
CUSTOM_MODEL_1=azure/gpt-4,true,4096
CUSTOM_MODEL_2=ollama/llama2,false,2048
```

### **Performance Tuning**

Optimize for large datasets:

```yaml
# In extraction_config.yaml
max_concurrent_interviews: 3  # Increase for more parallelism
code_hierarchy_depth: 2      # Reduce for faster processing

# Neo4j memory tuning (in docker-compose.yml)
NEO4J_dbms_memory_heap_max_size: 4G
NEO4J_dbms_memory_pagecache_size: 2G
```

**System Resources**: Monitor memory usage and adjust concurrent processing based on available RAM.

---

## Configuration File Reference

### **File Locations Summary**

| Configuration Type | File Location | Purpose | Status |
|-------------------|---------------|---------|--------|
| **Extraction Pipeline** | `extraction_config.yaml` | Main analysis config | ✅ Active |
| **Development Environment** | `.env` | Dev API keys & settings | ✅ Active |
| **Production Environment** | `.env.production.template` | Prod config template | ✅ Template |
| **Development Database** | `config/docker/docker-compose.yml` | Local Neo4j | ✅ Active |
| **Production Database** | `config/docker/docker-compose.production.yml` | Production Neo4j | ✅ Active |
| **Research Schema** | `src/qc/core/research_schema.yaml` | Entity definitions | ✅ Active |
| **Test Configuration** | `config/pytest.ini` | Python testing | ✅ Active |

### **Environment Variables Reference**

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GEMINI_API_KEY` | ✅ Yes | None | Google Gemini LLM access |
| `OPENAI_API_KEY` | Optional | None | OpenAI GPT models |
| `ANTHROPIC_API_KEY` | Optional | None | Claude models |
| `NEO4J_PASSWORD` | Production | "devpassword" | Neo4j authentication |
| `SECRET_KEY` | Production | Generated | Application security |
| `ENVIRONMENT` | Optional | "development" | Runtime environment |
| `MAX_CONCURRENT_REQUESTS` | Optional | 10 | Performance tuning |

---

## Migration and Maintenance

### **Configuration Updates**
When system requirements change:

1. **Update templates** (.env.example, .env.production.template)
2. **Update documentation** (this file)  
3. **Test with existing configurations** to ensure backward compatibility
4. **Provide migration instructions** for breaking changes

### **Version Control**
✅ **Include in Git**:
- All template files
- Example configurations
- Schema definitions
- Docker configurations

❌ **Never Commit**:
- Actual `.env` files with real API keys
- `.env.production` with production secrets
- Any files containing actual passwords or keys

### **Backup Recommendations**
- **Configuration Templates**: Stored in version control
- **Environment Files**: Backup securely, separate from code
- **Custom Schemas**: Include in project documentation
- **Docker Volumes**: Regular backup of Neo4j data volumes

**Configuration Status**: ✅ **CURRENT AND COMPLETE** - All configuration files documented with usage examples, troubleshooting guides, and security best practices.
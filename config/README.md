# Configuration Directory

This directory contains configuration files and templates for the Qualitative Coding Analysis Tool.

## Directory Structure

```
config/
├── docker/                          # Docker configurations
│   ├── docker-compose.yml          # Development Neo4j setup
│   ├── docker-compose.production.yml # Production deployment
│   └── Dockerfile.production       # Production container build
├── templates/                       # Configuration templates
│   ├── extraction_config_template.yaml # Pipeline config template
│   └── environment_template.env    # Environment variables template
├── examples/                        # Example schema files
│   ├── example_codes.txt           # Example code definitions
│   ├── example_speaker_properties.txt # Example speaker properties
│   └── example_entity_relationships.txt # Example entity relationships
├── pytest.ini                      # Python testing configuration
└── README.md                       # This file
```

## Quick Setup

### 1. Environment Setup
```bash
# Copy environment template
cp config/templates/environment_template.env .env

# Edit .env with your API keys
nano .env
```

### 2. Database Setup
```bash
# Start Neo4j database
cd config/docker
docker-compose up -d
```

### 3. Extraction Configuration
```bash
# Copy extraction config template
cp config/templates/extraction_config_template.yaml my_project_config.yaml

# Edit with your research question and data paths
nano my_project_config.yaml
```

### 4. Run Analysis
```bash
# Run extraction pipeline
python run_code_first_extraction.py my_project_config.yaml
```

## Configuration Files Reference

### **Active System Configuration** (Outside this directory)
- `extraction_config.yaml` (root) - Main extraction pipeline configuration
- `.env` (root) - Development environment variables  
- `.env.production.template` (root) - Production environment template
- `src/qc/core/research_schema.yaml` - Entity/relationship definitions

### **Templates** (Use these to create new configurations)
- `templates/extraction_config_template.yaml` - Pipeline configuration template
- `templates/environment_template.env` - Environment variables template

### **Examples** (For reference and testing)
- `examples/example_codes.txt` - Example thematic code definitions
- `examples/example_speaker_properties.txt` - Example speaker properties
- `examples/example_entity_relationships.txt` - Example entity relationships

### **Docker** (Container deployment)
- `docker/docker-compose.yml` - Development database setup
- `docker/docker-compose.production.yml` - Production deployment
- `docker/Dockerfile.production` - Production container image

## Need Help?

- **Full Documentation**: See `docs/CONFIGURATION_GUIDE.md`
- **Troubleshooting**: Check the configuration guide for common issues
- **Schema Customization**: Modify `src/qc/core/research_schema.yaml` for different research domains

## Configuration Philosophy

- **Templates First**: Use templates to create project-specific configurations
- **Environment Variables**: Sensitive data (API keys, passwords) in .env files
- **Single Source**: Each configuration type has one authoritative location
- **Security**: Never commit actual API keys or passwords to version control
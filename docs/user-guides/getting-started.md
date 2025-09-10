# Getting Started

Quick start guide for the Qualitative Coding Analysis Tool - get up and running in under 10 minutes.

## What This System Does

This is a **4-phase code-first extraction system** that automatically discovers and applies thematic codes, speaker properties, and entity relationships from qualitative interviews using AI.

**Key Benefits**:
- 🎯 **Automatic Code Discovery**: Finds thematic codes from your actual interview content  
- 🔄 **Consistent Schema**: All interviews analyzed with the same discovered patterns
- ⚡ **Fast Processing**: Parallel processing of interviews after schema discovery
- 📊 **Rich Output**: Codes, entities, relationships, and Neo4j graph database

## Prerequisites

- **Python 3.11+** installed
- **Docker** installed (for Neo4j database)
- **Gemini API Key** (free tier available from Google AI Studio)
- **Interview Files** in DOCX or TXT format

## 5-Minute Setup

### 1. Clone and Install

```bash
git clone <repository-url>
cd qualitative_coding
pip install -r requirements.txt
```

### 2. Get Your API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key (starts with `AIza...`)

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your API key
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Start System (Automated)

**Option A: Automated Startup (Recommended)**
```bash
# Cross-platform startup with full validation
./scripts/startup.sh          # Unix/Mac/WSL
# OR
scripts\startup.bat           # Windows
```

**Option B: Manual Startup**
```bash
cd config/docker
docker-compose up -d
```

The automated startup script will:
- ✅ Verify Docker and dependencies
- 🐳 Start Neo4j database  
- 🔗 Test connectivity
- ⚙️ Validate your .env configuration
- 🧪 Run system validation tests

### 5. Run Your First Analysis

```bash
# Copy and customize the configuration template
cp config/templates/extraction_config_template.yaml my_analysis_config.yaml

# Edit my_analysis_config.yaml:
# - Set your research question
# - Point interview_files_dir to your interview files
# - Adjust output_dir if needed

# Run the analysis
python run_code_first_extraction.py my_analysis_config.yaml
```

## What Happens During Analysis

The system runs through 4 phases:

```
Phase 1: Code Discovery     → Finds all thematic codes from ALL interviews
Phase 2: Speaker Schema     → Discovers speaker properties across interviews  
Phase 3: Entity Schema      → Identifies entity types and relationships
Phase 4: Application        → Applies discovered schemas to each interview
```

**Total Time**: Usually 10-30 minutes depending on interview count and length.

## Check Your Results

After completion, you'll find:

```
output_production/
├── taxonomy.json              # All discovered thematic codes
├── speaker_schema.json        # Speaker properties found
├── entity_schema.json         # Entity types and relationships
├── extraction_results.json    # Summary statistics
└── interviews/               # Individual interview analyses
    ├── interview1.json
    └── interview2.json
```

**View in Neo4j**:
1. Open http://localhost:7474 in browser
2. Connect with no authentication (development setup)
3. Run: `MATCH (n) RETURN n LIMIT 100`

## Next Steps

### Learn More
- **Configuration Options**: See [Configuration Guide](CONFIGURATION_GUIDE.md)
- **API Access**: See [API Guide](API_GUIDE.md) to access data programmatically
- **System Architecture**: See [technical-reference/CODE_FIRST_IMPLEMENTATION.md](../technical-reference/CODE_FIRST_IMPLEMENTATION.md)

### Customize for Your Research
- **Research Question**: Update `analytic_question` in your config file
- **Analysis Paradigm**: Set `paradigm` to match your methodology (phenomenological, critical_theory, etc.)
- **Code Hierarchy**: Adjust `code_hierarchy_depth` for more or fewer code levels

### Production Deployment  
- **Security Setup**: See [technical-reference/SECURITY_STEPS.md](../technical-reference/SECURITY_STEPS.md)
- **Production Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)

## Common Issues

### "GEMINI_API_KEY not found"
- Check your `.env` file exists and contains the API key
- Verify the API key is valid and hasn't expired

### "Neo4j connection failed"
- Ensure Docker is running: `docker ps | grep neo4j`
- Restart database: `cd config/docker && docker-compose restart`

### "Interview files not found"
- Check the `interview_files_dir` path in your config file
- Ensure files are in supported format (.docx or .txt)

### "No codes found"
- Check interview files contain substantial qualitative content
- Verify files are readable and not corrupted
- Consider adjusting the research question to be more specific

## Example Configuration

Here's a complete example configuration for analyzing AI adoption interviews:

```yaml
# Research question driving the analysis
analytic_question: "How are organizations experiencing challenges and benefits in AI adoption?"

# Directory containing interview files
interview_files_dir: "/path/to/your/interviews"

# Discovery approach (open = discover from data)
coding_approach: open
speaker_approach: open
entity_approach: open

# Output configuration
output_dir: "output_my_research"
auto_import_neo4j: true

# Database connection (using Docker setup)
neo4j_uri: "bolt://localhost:7687"
neo4j_user: "neo4j"
neo4j_password: "your_password"

# LLM settings
llm_model: "gemini/gemini-2.5-flash"
temperature: 0.1

# Analysis settings
paradigm: "expert_qualitative_coder"
max_concurrent_interviews: 1
code_hierarchy_depth: 3
```

## Getting Help

- **Configuration Issues**: See [Configuration Guide](CONFIGURATION_GUIDE.md)
- **API Questions**: See [API Guide](API_GUIDE.md)  
- **Technical Details**: See [technical-reference/](../technical-reference/)
- **Deployment Help**: See [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Ready to analyze your qualitative data? Follow the 5-minute setup above and start discovering insights from your interviews!**
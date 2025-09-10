# Outputs Directory

Organized output structure for qualitative coding analysis results.

## Directory Structure

### 📊 `current/`
**Latest production results** - Always contains the most recent analysis output.
- Use this directory to find your latest research results
- Contains complete analysis: taxonomy, schemas, and individual interviews
- Updated each time you run a new analysis

### 📁 `runs/`
**Historical analyses** - Timestamped archive of previous analysis runs.
- Organized by date: `YYYY-MM-DD_project_name/`
- Each run includes configuration snapshot and complete results
- Browse previous analyses by date and project

### 🧪 `testing/`
**Development outputs** - Test runs and quality validation results.
- Separated from research outputs to avoid confusion
- Includes performance tests, quality validation, and unit test outputs
- Used for system development and validation

## Quick Start

**Find latest results**: Look in `current/`
**Browse history**: Check `runs/` for previous analyses
**Development work**: Testing outputs in `testing/`

## Output Contents

Each analysis directory contains:
- `taxonomy.json` - Discovered thematic codes
- `speaker_schema.json` - Speaker properties  
- `entity_schema.json` - Entity types and relationships
- `extraction_results.json` - Analysis metadata and configuration
- `interviews/` - Individual interview analyses
- `README.md` - Analysis details and context
# Historical Analysis Runs

Archive of previous analysis runs organized chronologically.

## Directory Structure

Each historical run is stored in a timestamped directory:
```
YYYY-MM-DD_project_name/
├── README.md              # Run details and context
├── config.yaml           # Configuration snapshot
├── taxonomy.json         # Discovered codes
├── speaker_schema.json   # Speaker properties
├── entity_schema.json    # Entity relationships
├── extraction_results.json # Analysis metadata
└── interviews/           # Individual analyses
```

## Usage

- **Browse by date**: Find analyses from specific time periods
- **Compare runs**: Compare different configurations or datasets
- **Configuration reference**: See exactly how previous analyses were configured
- **Result history**: Track evolution of findings across multiple runs

## Archiving

Runs are automatically archived from `current/` when new analyses are performed, or can be manually archived for important milestone analyses.

**Naming Convention**: `YYYY-MM-DD_brief_description`
- Example: `2025-08-26_ai_research_methods`
- Example: `2025-08-20_africa_interviews_pilot`
# Output Organization Design

## Current State Analysis

**Current Structure**:
- `output_production/` - Main production results (✅ Good location)
- `test_quality_improvement/` - Test output in root (❌ Poor location)
- Various scattered test outputs throughout project

**User Pain Points**:
- No clear documentation of what each output contains
- Test outputs mixed with production outputs
- No consistent naming convention for different run types
- Historical results not organized by date/purpose

## Proposed Optimal Structure

```
outputs/
├── current/                    # Latest production results
│   ├── README.md              # What this contains, when generated
│   ├── taxonomy.json          # Discovered codes
│   ├── speaker_schema.json    # Speaker properties
│   ├── entity_schema.json     # Entity types
│   ├── extraction_results.json # Analysis metadata
│   └── interviews/            # Individual analyses
│       ├── interview1.json
│       └── interview2.json
│
├── runs/                      # Historical runs organized by date
│   ├── 2025-08-26_ai_research/
│   │   ├── README.md         # Run details, config used
│   │   ├── config.yaml       # Configuration snapshot
│   │   └── [same structure as current/]
│   │
│   └── 2025-08-25_africa_pilot/
│       ├── README.md
│       ├── config.yaml  
│       └── [analysis files...]
│
└── testing/                   # Development and test outputs
    ├── README.md             # Testing purpose documentation
    ├── quality_validation/   # Quality improvement tests
    ├── performance_tests/    # Performance benchmarking
    └── unit_tests/          # Unit test outputs
```

## Migration Strategy

### Phase 1: Create New Structure
1. Create `outputs/` directory with subdirectories
2. Add README files explaining purpose of each section

### Phase 2: Move Current Production
1. Move `output_production/` → `outputs/current/`
2. Create `outputs/current/README.md` with current analysis details

### Phase 3: Organize Test Outputs  
1. Move `test_quality_improvement/` → `outputs/testing/quality_validation/`
2. Clean up scattered test outputs

### Phase 4: Update System Integration
1. Update run scripts to output to `outputs/current/`
2. Add automatic timestamped archiving to `outputs/runs/`

## Benefits for Users

**Clear Navigation**:
- `outputs/current/` - always know where latest results are
- `outputs/runs/` - easy browsing of historical analyses
- `outputs/testing/` - development work separated from research

**Self-Documenting**:
- README in each directory explains contents and context
- Config snapshots show exactly how analysis was run
- Timestamp-based organization for historical tracking

**Predictable Locations**:
- Users always know where to find latest results
- Historical results organized chronologically
- Testing separate from production outputs

## Implementation Commands

```bash
# Create new structure
mkdir -p outputs/{current,runs,testing}

# Move current production
mv output_production/* outputs/current/
rmdir output_production

# Move test outputs
mkdir -p outputs/testing/quality_validation
mv test_quality_improvement/* outputs/testing/quality_validation/
rmdir test_quality_improvement

# Create documentation
# [README files for each section]
```
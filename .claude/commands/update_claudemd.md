Commit and then update CLAUDE.md to clear out resolve/out of date tasks and populate it with instructions for resolving the next tasks using evidence-based development practices. The instructions should be detailed enough for a new LLM to implement with no context beyond CLAUDE.md and referenced files.

## Core CLAUDE.md Requirements

#THIS IS NOT A PRODUCTION SYSTEM. DON'T BUILD PRODUCTION/ENTERPRISE FEATURES. HO

### 1. Coding Philosophy Section (Mandatory)
Every CLAUDE.md must include:
- **NO LAZY IMPLEMENTATIONS**: No mocking/stubs/fallbacks/pseudo-code/simplified implementations. do not mock llms without permission from the user.
- **FAIL-FAST AND LOUD PRINCIPLES**: Surface errors immediately, don't hide them
- **EVIDENCE-BASED DEVELOPMENT**: All claims require raw evidence in structured evidence files
- **Use Test Driven Design where possible.
### 2. Codebase Structure Section (Mandatory)  
Concisely document:
- Key entry points and main orchestration files
- Module organization and responsibilities
- Important integration points (ResourceOrchestrator, healing_integration.py, etc.)

### 3. Evidence Structure Requirements (Updated)
**CURRENT PRACTICE**: Use structured evidence organization instead of single Evidence.md:

```
evidence/
├── current/
│   └── Evidence_[PHASE]_[TASK].md     # Current development phase only
├── completed/  
│   └── Evidence_[PHASE]_[TASK].md     # Completed phases (archived)
```

**CRITICAL**: 
- Evidence files must contain ONLY current phase work (no historical contradictions)
- Raw execution logs required for all claims
- No success declarations without demonstrable proof
- Archive completed phases to avoid chronological confusion
# Archived Source Components

**Historical source code components** removed during src directory optimization.

## Archive Categories

### `universal_llm_kit/`
**Unused LLM abstraction framework** - Complete directory with setup, documentation, and examples.

**Original Purpose**: Universal LLM interface supporting multiple providers with smart routing
**Current Status**: UNUSED - System uses LiteLLM directly via `LLMHandler` 
**Reason for Archival**: 
- No active imports found in codebase
- Duplicates functionality in `qc/external/universal_llm.py`
- Enhanced LLM client was unused wrapper around this

**Contents**:
- Full Python package with setup.py
- README and documentation
- Demo files and examples  
- Requirements.txt with dependencies

### `enhanced_llm_client.py`
**Unused LLM client wrapper** - Drop-in replacement attempt for UniversalModelClient.

**Original Purpose**: Enhanced reliability and cost optimization wrapper around universal_llm
**Current Status**: UNUSED - No imports found in active codebase
**Reason for Archival**: 
- System uses `LLMHandler` with LiteLLM directly
- No references to EnhancedLLMClient class
- Import present but never instantiated

**Functionality**: Mock response objects, error handling, universal LLM integration

### `extraction_backups/`
**Backup and original files** from extraction pipeline development.

**Contents**:
- `code_first_extractor.py.backup` - Backup of main extractor 
- `code_first_schemas.py.backup` - Backup of schema definitions
- `multi_pass_extractor.py.backup` - Backup of old architecture extractor
- `multi_pass_extractor_original.py` - Original version of multi-pass system
- `quotes_speakers.txt.backup` - Backup of prompt template
- `quotes_speakers_original.txt` - Original prompt version

**Historical Context**: These represent development history of the extraction pipeline evolution from multi-pass architecture to 4-phase code-first approach.

## Usage Notes

**These components should NOT be restored** to active codebase:
- ❌ May have unresolved dependencies or conflicts
- ❌ Represent superseded architectural approaches
- ❌ Not maintained or tested with current system
- ❌ May introduce security or performance issues

**For reference only** - Examine architectural decisions, code patterns, or historical development approach.

## What Replaced These Components

### LLM Handling
**Replaced by**: `qc/llm/llm_handler.py` with direct LiteLLM integration
- Simpler, more direct approach
- Better performance and reliability
- Maintained and tested with current system

### Extraction Pipeline  
**Replaced by**: `qc/extraction/code_first_extractor.py` 
- 4-phase code-first discovery architecture
- Improved schema consistency and evidence grounding
- Better performance with parallel processing

### Backup Files
**Replaced by**: Current versions in active codebase
- All functionality preserved in current implementations
- Improved error handling and validation
- Better integration with overall system architecture

## Recovery Notes

If any of these components need to be referenced:
1. **Check git history** - Full development history available in version control
2. **Review current implementation** - Most functionality migrated to current system
3. **Test thoroughly** - Any restored code must be fully tested with current dependencies
4. **Update dependencies** - Ensure compatibility with current system requirements

## Migration History

**Archived**: 2025-08-26 during src directory optimization
**Reason**: Cleanup of unused components and backup files  
**Impact**: No functional changes - all active functionality preserved in current codebase
**Verification**: Extensive grep analysis confirmed no active usage of archived components
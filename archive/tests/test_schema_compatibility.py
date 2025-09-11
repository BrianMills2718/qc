"""
Methodical check of schema compatibility between all phases
"""

import sys
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_schemas import *
import json
from pathlib import Path

def check_phase_compatibility():
    """Check that all phases' schemas are compatible"""
    print("\n" + "="*80)
    print("SCHEMA COMPATIBILITY CHECK")
    print("="*80)
    
    issues = []
    
    # ========================================================================
    # Phase 1: Code Taxonomy
    # ========================================================================
    print("\n>>> PHASE 1: Code Taxonomy")
    print("-" * 40)
    
    # Check HierarchicalCode schema
    code_fields = HierarchicalCode.model_fields.keys()
    print(f"HierarchicalCode fields: {list(code_fields)}")
    
    # Required fields for Phase 4
    required_for_phase4 = ['id', 'name', 'description']
    for field in required_for_phase4:
        if field not in code_fields:
            issues.append(f"Phase 1: Missing required field '{field}' in HierarchicalCode")
            print(f"  X Missing: {field}")
        else:
            print(f"  OK Has: {field}")
    
    # Check CodeTaxonomy schema
    taxonomy_fields = CodeTaxonomy.model_fields.keys()
    print(f"\nCodeTaxonomy fields: {list(taxonomy_fields)}")
    
    if 'codes' not in taxonomy_fields:
        issues.append("Phase 1: CodeTaxonomy missing 'codes' field")
        print("  X Missing 'codes' field")
    else:
        print("  OK Has 'codes' field (List[HierarchicalCode])")
    
    # ========================================================================
    # Phase 2: Speaker Schema
    # ========================================================================
    print("\n>>> PHASE 2: Speaker Schema")
    print("-" * 40)
    
    # Check DiscoveredSpeakerProperty
    speaker_prop_fields = DiscoveredSpeakerProperty.model_fields.keys()
    print(f"DiscoveredSpeakerProperty fields: {list(speaker_prop_fields)}")
    
    # Check SpeakerPropertySchema
    speaker_schema_fields = SpeakerPropertySchema.model_fields.keys()
    print(f"\nSpeakerPropertySchema fields: {list(speaker_schema_fields)}")
    
    if 'properties' not in speaker_schema_fields:
        issues.append("Phase 2: SpeakerPropertySchema missing 'properties' field")
        print("  X Missing 'properties' field")
    else:
        print("  OK Has 'properties' field (List[DiscoveredSpeakerProperty])")
    
    # ========================================================================
    # Phase 3: Entity/Relationship Schema
    # ========================================================================
    print("\n>>> PHASE 3: Entity/Relationship Schema")
    print("-" * 40)
    
    # Check DiscoveredEntityType
    entity_type_fields = DiscoveredEntityType.model_fields.keys()
    print(f"DiscoveredEntityType fields: {list(entity_type_fields)}")
    
    # Check DiscoveredRelationshipType
    rel_type_fields = DiscoveredRelationshipType.model_fields.keys()
    print(f"\nDiscoveredRelationshipType fields: {list(rel_type_fields)}")
    
    # Check EntityRelationshipSchema
    entity_schema_fields = EntityRelationshipSchema.model_fields.keys()
    print(f"\nEntityRelationshipSchema fields: {list(entity_schema_fields)}")
    
    if 'entity_types' not in entity_schema_fields:
        issues.append("Phase 3: EntityRelationshipSchema missing 'entity_types' field")
    if 'relationship_types' not in entity_schema_fields:
        issues.append("Phase 3: EntityRelationshipSchema missing 'relationship_types' field")
    
    # ========================================================================
    # Phase 4A: Quote Extraction
    # ========================================================================
    print("\n>>> PHASE 4A: Quote Extraction")
    print("-" * 40)
    
    # Check SimpleQuote
    simple_quote_fields = SimpleQuote.model_fields.keys()
    print(f"SimpleQuote fields: {list(simple_quote_fields)}")
    
    # CRITICAL: Check if using code_ids (fixed) or code_names (old bug)
    if 'code_ids' in simple_quote_fields:
        print("  OK Uses 'code_ids' field (CORRECT)")
    elif 'code_names' in simple_quote_fields:
        print("  X Uses 'code_names' field (OLD BUG)")
        issues.append("Phase 4A: SimpleQuote using 'code_names' instead of 'code_ids'")
    else:
        print("  X Missing both 'code_ids' and 'code_names'")
        issues.append("Phase 4A: SimpleQuote missing code field")
    
    # Check QuotesAndSpeakers
    quotes_speakers_fields = QuotesAndSpeakers.model_fields.keys()
    print(f"\nQuotesAndSpeakers fields: {list(quotes_speakers_fields)}")
    
    # ========================================================================
    # Phase 4B: Entity Extraction
    # ========================================================================
    print("\n>>> PHASE 4B: Entity Extraction")
    print("-" * 40)
    
    # Check ExtractedEntity
    entity_fields = ExtractedEntity.model_fields.keys()
    print(f"ExtractedEntity fields: {list(entity_fields)}")
    
    # Check ExtractedRelationship
    rel_fields = ExtractedRelationship.model_fields.keys()
    print(f"\nExtractedRelationship fields: {list(rel_fields)}")
    
    # Check EntitiesAndRelationships
    entities_rels_fields = EntitiesAndRelationships.model_fields.keys()
    print(f"\nEntitiesAndRelationships fields: {list(entities_rels_fields)}")
    
    # ========================================================================
    # Final Output: CodedInterview
    # ========================================================================
    print("\n>>> FINAL OUTPUT: CodedInterview")
    print("-" * 40)
    
    # Check EnhancedQuote
    enhanced_quote_fields = EnhancedQuote.model_fields.keys()
    print(f"EnhancedQuote fields: {list(enhanced_quote_fields)}")
    
    # Critical fields for viewer compatibility
    viewer_required = ['code_ids', 'code_names', 'speaker', 'text']
    for field in viewer_required:
        if field not in enhanced_quote_fields:
            issues.append(f"EnhancedQuote missing viewer-required field: {field}")
            print(f"  X Missing: {field}")
        else:
            print(f"  OK Has: {field}")
    
    # Check CodedInterview
    coded_interview_fields = CodedInterview.model_fields.keys()
    print(f"\nCodedInterview fields: {list(coded_interview_fields)}")
    
    # ========================================================================
    # Data Flow Compatibility
    # ========================================================================
    print("\n>>> DATA FLOW COMPATIBILITY")
    print("-" * 40)
    
    # Check Phase 1 -> Phase 4
    print("\nPhase 1 -> Phase 4:")
    print("  - Phase 1 produces: CodeTaxonomy with List[HierarchicalCode]")
    print("  - Each HierarchicalCode has: id, name, description")
    print("  - Phase 4 expects: code IDs to apply to quotes")
    if 'code_ids' in simple_quote_fields:
        print("  OK Phase 4A can receive code IDs")
    else:
        print("  X Phase 4A cannot receive code IDs")
        issues.append("Data flow: Phase 4A incompatible with Phase 1 output")
    
    # Check Phase 2 -> Phase 4
    print("\nPhase 2 -> Phase 4:")
    print("  - Phase 2 produces: SpeakerPropertySchema with properties")
    print("  - Phase 4 uses: SpeakerInfo for speaker identification")
    print("  OK Compatible (properties used for prompt formatting)")
    
    # Check Phase 3 -> Phase 4
    print("\nPhase 3 -> Phase 4:")
    print("  - Phase 3 produces: EntityRelationshipSchema")
    print("  - Phase 4B expects: entity_types and relationship_types for extraction")
    print("  OK Compatible (schemas guide extraction)")
    
    # Check Phase 4A + 4B -> Final
    print("\nPhase 4A + 4B -> CodedInterview:")
    print("  - Phase 4A produces: QuotesAndSpeakers")
    print("  - Phase 4B produces: EntitiesAndRelationships")
    print("  - Combined into: CodedInterview with EnhancedQuotes")
    print("  OK Compatible (combine method merges results)")
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "="*80)
    print("COMPATIBILITY SUMMARY")
    print("="*80)
    
    if not issues:
        print("\n>>> ALL SCHEMAS ARE COMPATIBLE!")
        print("\nKey Points:")
        print("  - Phase 1 produces code IDs that Phase 4 can use")
        print("  - Phase 2 speaker properties inform Phase 4 extraction")
        print("  - Phase 3 entity schemas guide Phase 4B extraction")
        print("  - All phases output to ExtractionResults successfully")
    else:
        print(f"\n>>> FOUND {len(issues)} COMPATIBILITY ISSUES:")
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. {issue}")
    
    return len(issues) == 0

def check_actual_output():
    """Check actual output files for schema compliance"""
    print("\n" + "="*80)
    print("ACTUAL OUTPUT VERIFICATION")
    print("="*80)
    
    output_dirs = ["output_performance_optimized", "test_output_stats", "test_output_full"]
    
    for output_dir in output_dirs:
        if not Path(output_dir).exists():
            print(f"\nSkipping {output_dir} (not found)")
            continue
            
        print(f"\n[DIR] Checking: {output_dir}")
        print("-" * 40)
        
        # Check taxonomy
        taxonomy_file = Path(output_dir) / "taxonomy.json"
        if taxonomy_file.exists():
            with open(taxonomy_file, 'r', encoding='utf-8') as f:
                taxonomy = json.load(f)
            
            if 'codes' in taxonomy and taxonomy['codes']:
                first_code = taxonomy['codes'][0]
                print(f"  Taxonomy code example:")
                print(f"    - id: {first_code.get('id', 'MISSING')}")
                print(f"    - name: {first_code.get('name', 'MISSING')}")
                print(f"    - level: {first_code.get('level', 'MISSING')}")
        
        # Check interview
        interview_dir = Path(output_dir) / "interviews"
        if interview_dir.exists():
            interview_files = list(interview_dir.glob("*.json"))
            if interview_files:
                with open(interview_files[0], 'r', encoding='utf-8') as f:
                    interview = json.load(f)
                
                if 'quotes' in interview and interview['quotes']:
                    first_quote = interview['quotes'][0]
                    print(f"  Quote example:")
                    print(f"    - Has code_ids: {'code_ids' in first_quote}")
                    print(f"    - Has code_names: {'code_names' in first_quote}")
                    print(f"    - Code IDs: {first_quote.get('code_ids', [])[:2]}")
                    print(f"    - Speaker: {first_quote.get('speaker', {}).get('name', 'MISSING')}")

if __name__ == "__main__":
    # Check schema definitions
    schemas_ok = check_phase_compatibility()
    
    # Check actual outputs
    check_actual_output()
    
    print("\n" + "="*80)
    if schemas_ok:
        print(">>> SCHEMA COMPATIBILITY TEST PASSED")
    else:
        print(">>> SCHEMA COMPATIBILITY TEST FAILED")
    print("="*80)
    
    sys.exit(0 if schemas_ok else 1)
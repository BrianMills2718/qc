"""Test that Phase 4 respects discovered schemas"""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig

async def test_schema_constraints():
    """Test that extraction respects discovered schemas"""
    
    # Use existing extraction results
    output_dir = Path("output_production")
    
    print("Loading discovered schemas...")
    taxonomy = json.load(open(output_dir / "taxonomy.json"))
    speaker_schema = json.load(open(output_dir / "speaker_schema.json"))
    entity_schema = json.load(open(output_dir / "entity_schema.json"))
    
    # Get valid IDs from schemas
    valid_code_ids = {c['id'] for c in taxonomy['codes']}
    valid_entity_types = {e['id'] for e in entity_schema['entity_types']}
    valid_relationship_types = {r['id'] for r in entity_schema['relationship_types']}
    
    print(f"\nDiscovered schemas:")
    print(f"  Codes: {', '.join(sorted(valid_code_ids))}")
    print(f"  Entity types: {', '.join(sorted(valid_entity_types))}")
    print(f"  Relationship types: {', '.join(sorted(valid_relationship_types))}")
    
    # Check existing extractions for violations
    print(f"\nChecking existing extractions for violations...")
    
    violations_found = False
    for interview_file in (output_dir / "interviews").glob("*.json"):
        interview = json.load(open(interview_file))
        interview_id = interview_file.stem
        
        # Check codes
        for quote in interview.get('quotes', []):
            for code_id in quote.get('code_ids', []):
                if code_id not in valid_code_ids:
                    print(f"  ERROR {interview_id}: Invalid code '{code_id}'")
                    violations_found = True
        
        # Check entity types
        for entity in interview.get('interview_entities', []):
            if entity['type'] not in valid_entity_types:
                print(f"  ERROR {interview_id}: Invalid entity type '{entity['type']}'")
                violations_found = True
        
        # Check relationship types
        for rel in interview.get('interview_relationships', []):
            if rel['relationship_type'] not in valid_relationship_types:
                print(f"  ERROR {interview_id}: Invalid relationship type '{rel['relationship_type']}'")
                violations_found = True
    
    if not violations_found:
        print("  OK No violations found in existing extractions")
    
    # Now test with a small extraction using the fixed pipeline
    print(f"\nTesting new extraction with constraints...")
    
    config = ExtractionConfig(
        analytic_question="How are researchers experiencing and adapting to the integration of AI tools in qualitative research methods?",
        interview_files=[
            "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI assessment Arroyo SDR.docx"
        ],
        output_dir="output_test_constraints",
        auto_import_neo4j=False,
        llm_model="gemini/gemini-2.5-flash",
        max_concurrent_interviews=1
    )
    
    extractor = CodeFirstExtractor(config)
    
    # Set the discovered schemas (simulating they were already discovered)
    from src.qc.extraction.code_first_schemas import (
        CodeTaxonomy, SpeakerPropertySchema, EntityRelationshipSchema,
        HierarchicalCode, SpeakerProperty, DiscoveredEntityType, DiscoveredRelationshipType
    )
    
    extractor.code_taxonomy = CodeTaxonomy(
        codes=[HierarchicalCode(**c) for c in taxonomy['codes']],
        hierarchy_depth=taxonomy['hierarchy_depth']
    )
    
    extractor.speaker_schema = SpeakerPropertySchema(
        properties=[SpeakerProperty(**p) for p in speaker_schema['properties']]
    )
    
    extractor.entity_schema = EntityRelationshipSchema(
        entity_types=[DiscoveredEntityType(**e) for e in entity_schema['entity_types']],
        relationship_types=[DiscoveredRelationshipType(**r) for r in entity_schema['relationship_types']]
    )
    
    # Run only Phase 4 with one interview
    print("Running Phase 4 with constraint validation...")
    await extractor._run_phase_4()
    
    # Check results
    print("\nChecking new extraction for violations...")
    new_violations = False
    
    for interview_file in Path("output_test_constraints/interviews").glob("*.json"):
        interview = json.load(open(interview_file))
        
        # Check codes
        used_codes = set()
        for quote in interview.get('quotes', []):
            used_codes.update(quote.get('code_ids', []))
        
        invalid_codes = used_codes - valid_code_ids
        if invalid_codes:
            print(f"  ERROR Invalid codes used: {invalid_codes}")
            new_violations = True
        
        # Check entity types
        used_entity_types = {e['type'] for e in interview.get('interview_entities', [])}
        invalid_entity_types = used_entity_types - valid_entity_types
        if invalid_entity_types:
            print(f"  ERROR Invalid entity types used: {invalid_entity_types}")
            new_violations = True
        
        # Check relationship types
        used_rel_types = {r['relationship_type'] for r in interview.get('interview_relationships', [])}
        invalid_rel_types = used_rel_types - valid_relationship_types
        if invalid_rel_types:
            print(f"  ERROR Invalid relationship types used: {invalid_rel_types}")
            new_violations = True
    
    if not new_violations:
        print("  SUCCESS SUCCESS: New extraction respects all schema constraints!")
    else:
        print("  ERROR FAILURE: Constraints not properly enforced")
    
    return not new_violations

if __name__ == "__main__":
    success = asyncio.run(test_schema_constraints())
    sys.exit(0 if success else 1)
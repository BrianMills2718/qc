"""Import existing extraction results to Neo4j"""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, 'src')

from src.qc.core.neo4j_manager import EnhancedNeo4jManager, EntityNode, RelationshipEdge
from src.qc.extraction.code_first_schemas import Neo4jImportData

async def import_extraction_results():
    # Load extraction results
    results_file = Path("output_production/extraction_results.json")
    if not results_file.exists():
        print(f"ERROR: {results_file} not found. Run extraction first.")
        return False
    
    print(f"Loading extraction results from {results_file}...")
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Convert to Neo4jImportData format
    neo4j_data = Neo4jImportData(
        codes=results['code_taxonomy']['codes'],
        quotes=[],  # Will be collected from interviews
        speakers=[],  # Will be collected from interviews  
        entities=results['global_entities'],
        interviews=[],
        code_hierarchies=[],  # Will be generated from parent relationships
        quote_to_codes=[],
        quote_to_speakers=[],
        quote_to_entities=[],
        entity_relationships=results['global_relationships'],
        quote_to_interviews=[]
    )
    
    # Collect data from coded interviews
    for interview in results['coded_interviews']:
        # Add interview
        neo4j_data.interviews.append({
            'id': interview['interview_id'],
            'file_path': interview['interview_file'],
            'total_quotes': interview['total_quotes'],
            'total_speakers': interview['total_speakers'],
            'total_entities': interview['total_entities']
        })
        
        # Add speakers
        for speaker in interview['speakers']:
            # Use name as ID for speakers
            speaker_with_id = speaker.copy()
            speaker_with_id['id'] = speaker['name']
            if not any(s['id'] == speaker_with_id['id'] for s in neo4j_data.speakers):
                neo4j_data.speakers.append(speaker_with_id)
        
        # Add quotes and relationships
        for quote in interview['quotes']:
            quote_data = {
                'id': quote['id'],
                'text': quote['text'],
                'interview_id': interview['interview_id'],
                'line_start': quote.get('line_start'),
                'line_end': quote.get('line_end'),
                'confidence': quote.get('confidence', 1.0)
            }
            neo4j_data.quotes.append(quote_data)
            
            # Add quote-code relationships
            for code_id in quote['code_ids']:
                neo4j_data.quote_to_codes.append({
                    'quote_id': quote['id'],
                    'code_id': code_id
                })
            
            # Add speaker-quote relationship
            if 'speaker' in quote:
                neo4j_data.quote_to_speakers.append({
                    'speaker_id': quote['speaker']['name'],  # Use name as ID
                    'quote_id': quote['id']
                })
            
            # Add quote-interview relationship
            neo4j_data.quote_to_interviews.append({
                'quote_id': quote['id'],
                'interview_id': interview['interview_id']
            })
    
    # Generate code parent relationships
    for code in results['code_taxonomy']['codes']:
        if code.get('parent_id'):
            neo4j_data.code_hierarchies.append({
                'parent_id': code['parent_id'],
                'child_id': code['id'],
                'relationship_type': 'PARENT_OF'
            })
    
    print(f"Loaded data:")
    print(f"  - {len(neo4j_data.codes)} codes")
    print(f"  - {len(neo4j_data.quotes)} quotes")
    print(f"  - {len(neo4j_data.speakers)} speakers")
    print(f"  - {len(neo4j_data.entities)} entities")
    print(f"  - {len(neo4j_data.interviews)} interviews")
    
    # Connect to Neo4j
    neo4j = EnhancedNeo4jManager(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="devpassword"
    )
    
    try:
        await neo4j.connect()
        print("\nConnected to Neo4j. Starting import...")
        
        # Clear existing data (optional)
        print("Clearing existing data...")
        await neo4j.clear_database()
        
        # Import the data manually using existing methods
        print("Importing new data...")
        
        # Import Codes
        print(f"  Importing {len(neo4j_data.codes)} codes...")
        for code in neo4j_data.codes:
            await neo4j.create_code(code)
        
        # Import Code Hierarchies  
        print(f"  Creating {len(neo4j_data.code_hierarchies)} code hierarchies...")
        for hierarchy in neo4j_data.code_hierarchies:
            await neo4j.execute_cypher("""
                MATCH (parent:Code {id: $parent_id}), (child:Code {id: $child_id})
                CREATE (parent)-[:PARENT_OF]->(child)
            """, hierarchy)
        
        # Import Quotes
        print(f"  Importing {len(neo4j_data.quotes)} quotes...")
        for quote in neo4j_data.quotes:
            await neo4j.create_quote_node(quote)
        
        # Import Quote-Code relationships
        print(f"  Creating {len(neo4j_data.quote_to_codes)} quote-code links...")
        for link in neo4j_data.quote_to_codes:
            await neo4j.link_quote_to_code(link['quote_id'], link['code_id'])
        
        # Import Speakers as entities
        print(f"  Importing {len(neo4j_data.speakers)} speakers...")
        for speaker in neo4j_data.speakers:
            entity_node = EntityNode(
                id=speaker['id'],
                name=speaker['name'],
                entity_type='Speaker',
                properties=speaker
            )
            await neo4j.create_entity(entity_node)
        
        # Import Quote-Speaker relationships
        print(f"  Creating {len(neo4j_data.quote_to_speakers)} quote-speaker links...")
        for link in neo4j_data.quote_to_speakers:
            await neo4j.execute_cypher("""
                MATCH (q:Quote {id: $quote_id}), (s:Entity {id: $speaker_id, entity_type: 'Speaker'})
                CREATE (q)-[:SPOKEN_BY]->(s)
            """, link)
        
        # Import other Entities
        print(f"  Importing {len(neo4j_data.entities)} entities...")
        for entity in neo4j_data.entities:
            # Create entity with proper type
            entity_node = EntityNode(
                id=f"{entity['type']}_{entity['name'].replace(' ', '_')}",
                name=entity['name'],
                entity_type=entity['type'],
                properties=entity.get('properties', {})
            )
            await neo4j.create_entity(entity_node)
        
        # Import Entity Relationships
        print(f"  Creating {len(neo4j_data.entity_relationships)} entity relationships...")
        for rel in neo4j_data.entity_relationships:
            # For now, use entity names as IDs since we don't have types in global relationships
            edge = RelationshipEdge(
                source_id=f"Entity_{rel['source_entity'].replace(' ', '_')}",
                target_id=f"Entity_{rel['target_entity'].replace(' ', '_')}",
                relationship_type=rel['relationship_type'],
                properties={
                    'total_mentions': rel.get('total_mentions', 1),
                    'confidence': rel.get('confidence', 1.0)
                }
            )
            try:
                await neo4j.create_relationship(edge)
            except Exception as e:
                print(f"    Warning: Could not create relationship {rel['source_entity']} -> {rel['target_entity']}: {e}")
        
        # Import Interviews
        print(f"  Importing {len(neo4j_data.interviews)} interviews...")
        for interview in neo4j_data.interviews:
            await neo4j.execute_cypher("""
                CREATE (i:Interview {
                    id: $id,
                    file_path: $file_path,
                    total_quotes: $total_quotes,
                    total_speakers: $total_speakers,
                    total_entities: $total_entities
                })
            """, interview)
        
        # Import Quote-Interview relationships
        print(f"  Creating {len(neo4j_data.quote_to_interviews)} quote-interview links...")
        for link in neo4j_data.quote_to_interviews:
            await neo4j.execute_cypher("""
                MATCH (q:Quote {id: $quote_id}), (i:Interview {id: $interview_id})
                CREATE (q)-[:FROM_INTERVIEW]->(i)
            """, link)
        
        # Get statistics
        async with neo4j.driver.session() as session:
            # Count nodes
            result = await session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            records = [record async for record in result]
            
            print("\nImport complete! Node counts:")
            for record in records:
                print(f"  - {record['label']}: {record['count']}")
            
            # Count relationships
            result = await session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            records = [record async for record in result]
            
            print("\nRelationship counts:")
            for record in records:
                print(f"  - {record['type']}: {record['count']}")
        
        await neo4j.close()
        print("\nSuccess! Data imported to Neo4j.")
        print("\nYou can now:")
        print("1. Open Neo4j Browser at http://localhost:7474")
        print("2. Login with neo4j/devpassword")
        print("3. Run queries to explore your data")
        return True
        
    except Exception as e:
        print(f"ERROR: Import failed: {e}")
        await neo4j.close()
        return False

if __name__ == "__main__":
    success = asyncio.run(import_extraction_results())
    sys.exit(0 if success else 1)
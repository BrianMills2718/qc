#!/usr/bin/env python3
"""Import individual interview JSON files to Neo4j"""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, 'src')

from src.qc.core.neo4j_manager import EnhancedNeo4jManager

async def import_interview_data():
    """Import data from individual interview JSON files."""
    
    print("=== IMPORTING INTERVIEW DATA TO NEO4J ===")
    
    # Connect to Neo4j
    neo4j = EnhancedNeo4jManager(
        uri="bolt://localhost:7687",
        username="neo4j", 
        password="devpassword"
    )
    
    try:
        await neo4j.connect()
        print("Connected to Neo4j")
        
        # Load interview files
        interviews_dir = Path('output_production/interviews')
        json_files = list(interviews_dir.glob('*.json'))
        
        print(f"Found {len(json_files)} interview files")
        
        for json_file in json_files:
            print(f"\nProcessing {json_file.name}...")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    interview_data = json.load(f)
                
                interview_id = interview_data.get('interview_id', json_file.stem)
                quotes = interview_data.get('quotes', [])
                speakers = interview_data.get('speakers', [])
                
                print(f"  - Interview: {interview_id}")
                print(f"  - Quotes: {len(quotes)}")
                print(f"  - Speakers: {len(speakers)}")
                
                # Create Interview node
                await neo4j.execute_cypher("""
                    MERGE (i:Interview {id: $interview_id})
                    SET i.title = $interview_id,
                        i.file_path = $file_path,
                        i.total_quotes = $total_quotes,
                        i.total_speakers = $total_speakers
                """, {
                    'interview_id': interview_id,
                    'file_path': str(json_file),
                    'total_quotes': len(quotes),
                    'total_speakers': len(speakers)
                })
                
                # Import speakers as entities
                for speaker in speakers:
                    speaker_id = speaker.get('name', f"speaker_{speakers.index(speaker)}")
                    await neo4j.execute_cypher("""
                        MERGE (s:Speaker {id: $speaker_id})
                        SET s.name = $name,
                            s.confidence = $confidence,
                            s.identification_method = $method,
                            s.quotes_count = $quotes_count,
                            s.conversational_role = $role
                    """, {
                        'speaker_id': speaker_id,
                        'name': speaker.get('name', speaker_id),
                        'confidence': speaker.get('confidence', 1.0),
                        'method': speaker.get('identification_method', 'dialogue_analysis'),
                        'quotes_count': speaker.get('quotes_count', 0),
                        'role': speaker.get('conversational_role')
                    })
                
                # Import quotes with thematic connections
                for quote in quotes:
                    quote_id = quote.get('id', f"{interview_id}_Q{quotes.index(quote):03d}")
                    
                    # Create quote node
                    await neo4j.execute_cypher("""
                        MERGE (q:Quote {id: $quote_id})
                        SET q.text = $text,
                            q.interview_id = $interview_id,
                            q.speaker_name = $speaker_name,
                            q.sequence_position = $sequence_position,
                            q.line_start = $line_start,
                            q.line_end = $line_end,
                            q.thematic_connection = $thematic_connection,
                            q.connection_target = $connection_target,
                            q.connection_confidence = $connection_confidence,
                            q.connection_evidence = $connection_evidence
                    """, {
                        'quote_id': quote_id,
                        'text': quote.get('text', ''),
                        'interview_id': interview_id,
                        'speaker_name': quote.get('speaker', {}).get('name') if quote.get('speaker') else None,
                        'sequence_position': quote.get('sequence_position'),
                        'line_start': quote.get('line_start'),
                        'line_end': quote.get('line_end'),
                        'thematic_connection': quote.get('thematic_connection', 'none'),
                        'connection_target': quote.get('connection_target'),
                        'connection_confidence': quote.get('connection_confidence'),
                        'connection_evidence': quote.get('connection_evidence')
                    })
                    
                    # Link quote to interview
                    await neo4j.execute_cypher("""
                        MATCH (q:Quote {id: $quote_id}), (i:Interview {id: $interview_id})
                        MERGE (q)-[:FROM_INTERVIEW]->(i)
                    """, {
                        'quote_id': quote_id,
                        'interview_id': interview_id
                    })
                    
                    # Link quote to speaker
                    speaker_name = quote.get('speaker', {}).get('name') if quote.get('speaker') else None
                    if speaker_name:
                        await neo4j.execute_cypher("""
                            MATCH (q:Quote {id: $quote_id}), (s:Speaker {id: $speaker_name})
                            MERGE (q)-[:SPOKEN_BY]->(s)
                        """, {
                            'quote_id': quote_id,
                            'speaker_name': speaker_name
                        })
                    
                    # Link quote to codes
                    for code_id in quote.get('code_ids', []):
                        await neo4j.execute_cypher("""
                            MATCH (q:Quote {id: $quote_id}), (c:Code {id: $code_id})
                            MERGE (q)-[:HAS_CODE]->(c)
                        """, {
                            'quote_id': quote_id,
                            'code_id': code_id
                        })
                    
                    # Create thematic connections between quotes
                    if quote.get('thematic_connection') != 'none' and quote.get('connection_target'):
                        # Find target quotes by speaker name and create connections
                        connection_type = quote.get('thematic_connection', '').upper().replace(' ', '_')
                        target_speaker = quote.get('connection_target')
                        source_sequence = quote.get('sequence_position', 0)
                        
                        print(f"    Creating thematic connection: {connection_type} to {target_speaker}")
                        
                        if connection_type and target_speaker:
                            # Find the most recent quote from target speaker that comes before this quote
                            await neo4j.execute_cypher("""
                                MATCH (source_quote:Quote {id: $source_quote_id})
                                MATCH (target_quote:Quote)
                                WHERE target_quote.speaker_name = $target_speaker
                                  AND target_quote.interview_id = $interview_id
                                  AND target_quote.sequence_position < $source_sequence
                                WITH source_quote, target_quote
                                ORDER BY target_quote.sequence_position DESC
                                LIMIT 1
                                MERGE (source_quote)-[r:THEMATIC_CONNECTION]->(target_quote)
                                SET r.connection_type = $connection_type,
                                    r.confidence = $confidence,
                                    r.evidence = $evidence
                            """, {
                                'source_quote_id': quote_id,
                                'target_speaker': target_speaker,
                                'interview_id': interview_id,
                                'source_sequence': source_sequence,
                                'connection_type': connection_type,
                                'confidence': quote.get('connection_confidence', 0.5),
                                'evidence': quote.get('connection_evidence')
                            })
                
                print(f"  SUCCESS: Imported {len(quotes)} quotes and {len(speakers)} speakers")
                
            except Exception as e:
                print(f"  ERROR processing {json_file.name}: {e}")
        
        # Get final statistics
        print(f"\n=== FINAL NEO4J DATABASE STATISTICS ===")
        
        stats_queries = [
            ("Interviews", "MATCH (n:Interview) RETURN count(n) as count"),
            ("Speakers", "MATCH (n:Speaker) RETURN count(n) as count"),  
            ("Quotes", "MATCH (n:Quote) RETURN count(n) as count"),
            ("Codes", "MATCH (n:Code) RETURN count(n) as count"),
            ("Quote-Code Links", "MATCH ()-[r:HAS_CODE]->() RETURN count(r) as count"),
            ("Quote-Speaker Links", "MATCH ()-[r:SPOKEN_BY]->() RETURN count(r) as count"),
            ("Thematic Connections", "MATCH ()-[r:THEMATIC_CONNECTION]->() RETURN count(r) as count"),
            ("Code Hierarchies", "MATCH ()-[r:PARENT_OF]->() RETURN count(r) as count")
        ]
        
        for name, query in stats_queries:
            result = await neo4j.execute_cypher(query)
            count = result[0]['count'] if result else 0
            print(f"{name}: {count}")
        
        await neo4j.close()
        
        print(f"\nSUCCESS! Data imported to Neo4j")
        print(f"You can now explore the data at: http://localhost:7474")
        print(f"Login: neo4j / devpassword")
        
        print(f"\nTry these queries in Neo4j Browser:")
        print(f"1. MATCH (i:Interview) RETURN i.title, i.total_quotes")
        print(f"2. MATCH (q:Quote)-[:HAS_CODE]->(c:Code) RETURN q.text, c.name LIMIT 10")
        print(f"3. MATCH (q1:Quote)-[r:THEMATIC_CONNECTION]->(q2:Quote) RETURN q1.text, r.connection_type, q2.text LIMIT 10")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        await neo4j.close()
        return False

if __name__ == "__main__":
    success = asyncio.run(import_interview_data())
    sys.exit(0 if success else 1)
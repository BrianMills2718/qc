#!/usr/bin/env python3
"""Discover actual Neo4j patterns instead of assuming relationship types"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment  
load_dotenv()

async def discover_neo4j_patterns():
    """Discover what actually exists in Neo4j and suggest queries based on real data"""
    print("DISCOVER: Analyzing actual Neo4j database contents")
    
    try:
        from qc_clean.core.data.neo4j_manager import EnhancedNeo4jManager
        
        neo4j = EnhancedNeo4jManager(password='password123')  # Working password
        await neo4j.connect()
        print("SUCCESS: Connected to Neo4j")
        
        # 1. Discover all node types with properties
        print("\n=== NODE ANALYSIS ===")
        nodes = await neo4j.execute_cypher("""
            MATCH (n) 
            RETURN labels(n) as labels, 
                   count(n) as count,
                   collect(keys(n))[0..3] as sample_properties
            ORDER BY count DESC
        """)
        
        print("NODE TYPES:")
        for result in nodes:
            labels = result['labels']
            count = result['count'] 
            props = result['sample_properties']
            label_name = labels[0] if labels else 'Unknown'
            print(f"   {label_name}: {count} nodes")
            if props:
                print(f"      Sample properties: {props}")
        
        # 2. Check for any relationships that might exist
        print("\n=== RELATIONSHIP ANALYSIS ===")
        relationships = await neo4j.execute_cypher("""
            MATCH (a)-[r]->(b)
            RETURN type(r) as rel_type, 
                   count(r) as count,
                   labels(a)[0] as from_type,
                   labels(b)[0] as to_type
        """)
        
        if relationships:
            print("EXISTING RELATIONSHIPS:")
            for rel in relationships:
                print(f"   {rel['from_type']} --{rel['rel_type']}--> {rel['to_type']} ({rel['count']})")
        else:
            print("NO RELATIONSHIPS: Database has 0 relationships")
        
        # 3. Analyze actual entity data to suggest potential relationships  
        print("\n=== ENTITY CONTENT ANALYSIS ===")
        entities = await neo4j.execute_cypher("""
            MATCH (n:Entity)
            RETURN n.name as name, 
                   n.type as type,
                   n.description as description
            LIMIT 10
        """)
        
        print("SAMPLE ENTITIES:")
        entity_types = {}
        for entity in entities:
            name = entity.get('name', 'unnamed')
            etype = entity.get('type', 'unknown')  
            desc = entity.get('description', 'no description')[:100]
            
            entity_types[etype] = entity_types.get(etype, 0) + 1
            print(f"   {name} ({etype}): {desc}...")
        
        print(f"\nENTITY TYPE DISTRIBUTION:")
        for etype, count in entity_types.items():
            print(f"   {etype}: {count}")
        
        # 4. Suggest potential relationship patterns based on entity types
        print("\n=== SUGGESTED QUERY PATTERNS ===")
        
        if 'Person' in entity_types and 'Organization' in entity_types:
            print("PATTERN 1: Person-Organization Connections")
            print("   Query: Find which people are connected to which organizations")
            print("   Cypher: MATCH (p:Entity {type: 'Person'}), (o:Entity {type: 'Organization'}) RETURN p.name, o.name")
        
        if 'Concept' in entity_types:
            print("PATTERN 2: Concept Relationships") 
            print("   Query: Find concepts that co-occur in descriptions")
            print("   Cypher: MATCH (c1:Entity {type: 'Concept'}), (c2:Entity {type: 'Concept'}) RETURN c1.name, c2.name")
        
        if len(entity_types) > 1:
            print("PATTERN 3: Cross-Type Analysis")
            print("   Query: Find entities mentioned together in descriptions")
            print("   Use: Text analysis of description fields to find co-mentions")
        
        print("\nPATTERN 4: Hierarchical Code Relationships")
        print("   Query: Find hierarchical relationships between codes")  
        print("   Note: Check if any codes have parent-child relationships in properties")
        
        await neo4j.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(discover_neo4j_patterns())
    if result:
        print("\nSUCCESS: Neo4j pattern discovery complete")
        print("\nNEXT STEPS:")
        print("1. Choose which relationship pattern to implement")  
        print("2. Create relationships based on actual entity content")
        print("3. Build queries that work with real data, not assumed schemas")
    else:
        print("\nFAILED: Neo4j pattern discovery failed")
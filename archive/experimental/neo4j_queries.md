# Neo4j Cypher Queries for Qualitative Coding Analysis

## Data Successfully Imported to Neo4j!

Your qualitative coding data is now in Neo4j with:
- **129 nodes**: 10 Codes, 25 Quotes, 91 Entities (including 7 Speakers), 3 Interviews
- **118 relationships**: Code applications, speaker attributions, entity mentions, hierarchies

## Access Neo4j Browser
1. Open http://localhost:7474
2. Login with neo4j/devpassword
3. Run these queries to explore your data

## Essential Queries

### 1. View Code Hierarchy
```cypher
// See the hierarchical structure of codes
MATCH (parent:Code)-[:PARENT_OF]->(child:Code)
RETURN parent, child
```

### 2. Find Most Applied Codes
```cypher
// Which codes are used most frequently?
MATCH (c:Code)<-[:SUPPORTS]-(q:Quote)
RETURN c.name as Code, c.description as Description, count(q) as QuoteCount
ORDER BY QuoteCount DESC
```

### 3. Code Co-occurrence Analysis
```cypher
// Find codes that frequently appear together
MATCH (q:Quote)-[:SUPPORTS]->(c1:Code)
MATCH (q)-[:SUPPORTS]->(c2:Code)
WHERE id(c1) < id(c2)
RETURN c1.name as Code1, c2.name as Code2, count(q) as CoOccurrences
ORDER BY CoOccurrences DESC
LIMIT 10
```

### 4. Speaker Analysis
```cypher
// Who speaks most about each topic?
MATCH (s:Entity {entity_type: 'Speaker'})<-[:SPOKEN_BY]-(q:Quote)-[:SUPPORTS]->(c:Code)
RETURN s.name as Speaker, c.name as Code, count(q) as Mentions
ORDER BY Mentions DESC
```

### 5. Find Quotes by Code
```cypher
// Get all quotes for a specific code
MATCH (q:Quote)-[:SUPPORTS]->(c:Code {name: 'AI Training and Validation Methods'})
MATCH (q)-[:SPOKEN_BY]->(s:Entity)
RETURN q.text as Quote, s.name as Speaker, q.interview_id as Interview
```

### 6. Entity Relationship Network
```cypher
// Explore relationships between entities
MATCH (e1:Entity)-[r]->(e2:Entity)
WHERE e1.entity_type <> 'Speaker' AND e2.entity_type <> 'Speaker'
RETURN e1.name as Source, type(r) as Relationship, e2.name as Target
LIMIT 50
```

### 7. Cross-Interview Pattern Analysis
```cypher
// Find patterns across interviews
MATCH (i:Interview)<-[:FROM_INTERVIEW]-(q:Quote)-[:SUPPORTS]->(c:Code)
RETURN i.id as Interview, c.name as Code, count(q) as QuoteCount
ORDER BY Interview, QuoteCount DESC
```

### 8. Find Bridge Concepts
```cypher
// Identify codes that connect different themes
MATCH (c1:Code)<-[:SUPPORTS]-(q1:Quote)-[:SPOKEN_BY]->(s:Entity)
MATCH (s)<-[:SPOKEN_BY]-(q2:Quote)-[:SUPPORTS]->(c2:Code)
WHERE c1 <> c2
RETURN c1.name as Code1, c2.name as Code2, s.name as Speaker, count(*) as Connections
ORDER BY Connections DESC
LIMIT 20
```

### 9. Quote Chains
```cypher
// Find related quotes through shared codes
MATCH (q1:Quote)-[:SUPPORTS]->(c:Code)<-[:SUPPORTS]-(q2:Quote)
WHERE q1 <> q2 AND c.name = 'Challenges of AI in Research'
MATCH (q1)-[:SPOKEN_BY]->(s1:Entity)
MATCH (q2)-[:SPOKEN_BY]->(s2:Entity)
RETURN q1.text as Quote1, s1.name as Speaker1, q2.text as Quote2, s2.name as Speaker2
LIMIT 5
```

### 10. Multi-hop Analysis
```cypher
// Complex query: Find speakers discussing both benefits AND challenges
MATCH (s:Entity {entity_type: 'Speaker'})<-[:SPOKEN_BY]-(q1:Quote)-[:SUPPORTS]->(c1:Code)
WHERE c1.name CONTAINS 'Benefits'
WITH s, collect(DISTINCT c1.name) as BenefitCodes
MATCH (s)<-[:SPOKEN_BY]-(q2:Quote)-[:SUPPORTS]->(c2:Code)
WHERE c2.name CONTAINS 'Challenges'
RETURN s.name as Speaker, BenefitCodes, collect(DISTINCT c2.name) as ChallengeCodes
```

## Advanced Network Analysis

### Community Detection
```cypher
// Find clusters of related codes through quote connections
CALL gds.graph.project(
  'code-network',
  'Code',
  {
    CONNECTS_TO: {
      type: 'CONNECTS_TO',
      orientation: 'UNDIRECTED'
    }
  }
)
YIELD graphName, nodeCount, relationshipCount
```

### Centrality Analysis
```cypher
// Find most central/important codes
MATCH (c:Code)
OPTIONAL MATCH (c)<-[:SUPPORTS]-(q:Quote)
OPTIONAL MATCH (c)-[:PARENT_OF|:PARENT_OF*]-(related:Code)
RETURN c.name as Code, 
       count(DISTINCT q) as DirectQuotes,
       count(DISTINCT related) as RelatedCodes,
       count(DISTINCT q) + count(DISTINCT related) as Centrality
ORDER BY Centrality DESC
```

## Visualization Tips

1. **In Neo4j Browser**, use these commands for better visualization:
   - `:style` - Customize node and relationship appearance
   - Double-click nodes to expand relationships
   - Use the sidebar to filter by labels

2. **Color coding suggestions**:
   - Codes: Blue (hierarchy levels in different shades)
   - Quotes: Green
   - Speakers: Orange
   - Other Entities: Purple
   - Interviews: Gray

3. **Layout tips**:
   - Use hierarchical layout for code taxonomy
   - Use force-directed layout for entity networks
   - Pin important nodes to organize the view

## Export Queries

### Export for Network Analysis Tools
```cypher
// Export node list
MATCH (n)
RETURN id(n) as id, labels(n)[0] as type, n.name as name, n
```

```cypher
// Export edge list
MATCH (n1)-[r]->(n2)
RETURN id(n1) as source, id(n2) as target, type(r) as relationship
```

## Query Templates

### Find quotes about [TOPIC]
```cypher
MATCH (q:Quote)
WHERE toLower(q.text) CONTAINS toLower('[TOPIC]')
MATCH (q)-[:SPOKEN_BY]->(s:Entity)
MATCH (q)-[:SUPPORTS]->(c:Code)
RETURN q.text, s.name, collect(c.name) as Codes
```

### Find relationships between [ENTITY1] and [ENTITY2]
```cypher
MATCH path = shortestPath((e1:Entity {name: '[ENTITY1]'})-[*]-(e2:Entity {name: '[ENTITY2]'}))
RETURN path
```

## Benefits of Neo4j for Qualitative Coding

1. **Pattern Discovery**: Find hidden connections between codes, speakers, and concepts
2. **Multi-hop Queries**: Answer complex questions like "Who discusses both X and Y?"
3. **Network Metrics**: Calculate centrality, clustering, and other graph metrics
4. **Visual Exploration**: Interactive graph visualization reveals patterns
5. **Scalability**: Handles thousands of interviews efficiently
6. **Flexibility**: Add new relationship types and properties as needed
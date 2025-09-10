# Phase 1.5 Deferred Features Plan

## Overview
**Goal**: Add multi-model consensus, graph relationships, and advanced analytics
**Timeline**: Week 4-5 (2 weeks after Phase 1.0)
**Prerequisite**: Phase 1.0 must be working and tested

---

## Features to Add

### 1. Multi-Model Consensus
Add Claude to work alongside Gemini for validation and richer analysis.

```python
# Upgrade from single model to consensus
class ConsensusAnalyzer:
    def __init__(self):
        self.models = {
            "gemini": GeminiFlashClient(),
            "claude": ClaudeSonnetClient()
        }
        self.consensus_validator = LLMConsensusValidator()
    
    async def analyze_with_consensus(
        self,
        interview_text: str,
        session_id: str
    ) -> ConsensusResult:
        # Run both models in parallel
        async with anyio.create_task_group() as tg:
            results = {}
            
            async def run_model(name, client):
                results[name] = await client.extract_codes(interview_text)
            
            for name, client in self.models.items():
                tg.start_soon(run_model, name, client)
        
        # LLM-based consensus
        consensus = await self.consensus_validator.consolidate_codes(results)
        return consensus
```

### 2. Neo4j Graph Database
Migrate from SQLite to Neo4j for relationship discovery.

```cypher
// Neo4j schema for relationships
CREATE (c1:Code {name: "trust_issues"})
CREATE (c2:Code {name: "communication_breakdown"})
CREATE (c1)-[:LEADS_TO {strength: 0.8}]->(c2)
CREATE (c1)-[:CONFLICTS_WITH {reason: "opposite_outcomes"}]->(c3)
```

```python
# Graph migration
class Neo4jMigration:
    async def migrate_from_sqlite(self, session_id: str):
        # 1. Export SQLite data
        codes = await sqlite_db.get_codes(session_id)
        quotes = await sqlite_db.get_quotes(session_id)
        
        # 2. Create nodes in Neo4j
        for code in codes:
            await neo4j.create_node("Code", {
                "id": code.id,
                "name": code.name,
                "definition": code.definition,
                "session_id": session_id
            })
        
        # 3. Discover relationships with LLM
        relationships = await self.discover_relationships(codes)
        
        # 4. Create relationship edges
        for rel in relationships:
            await neo4j.create_relationship(
                from_id=rel.from_code,
                to_id=rel.to_code,
                type=rel.relationship_type,
                properties={"strength": rel.strength}
            )
```

### 3. LLM Relationship Discovery
Use LLMs to find semantic relationships between codes.

```python
class RelationshipDiscovery:
    async def discover_relationships(
        self,
        codes: List[Code]
    ) -> List[CodeRelationship]:
        
        prompt = f"""
        Analyze these codes and identify relationships:
        
        Codes:
        {json.dumps([{"name": c.name, "definition": c.definition} for c in codes])}
        
        Find relationships like:
        - LEADS_TO (causal)
        - CONFLICTS_WITH (contradictory)
        - REINFORCES (supportive)
        - SIMILAR_TO (semantic similarity)
        
        Return JSON with relationships and strength (0-1).
        """
        
        result = await llm.analyze(prompt)
        return [CodeRelationship(**rel) for rel in result["relationships"]]
```

### 4. Predefined Analytics Dashboards
Convert graph insights into table views for non-technical users.

```python
# Analytics API endpoints
@app.get("/api/sessions/{session_id}/analytics/most-connected")
async def most_connected_codes(session_id: str):
    """Find network hubs - codes with most relationships"""
    query = """
    MATCH (c:Code {session_id: $sid})-[r]-(other:Code)
    RETURN c.name, c.definition, count(r) as connections
    ORDER BY connections DESC LIMIT 20
    """
    return await neo4j.query(query, sid=session_id)

@app.get("/api/sessions/{session_id}/analytics/causal-chains")
async def causal_chains(session_id: str):
    """Multi-step cause-effect paths"""
    query = """
    MATCH path = (start:Code)-[:LEADS_TO*1..4]->(end:Code)
    WHERE start.session_id = $sid
    RETURN [n in nodes(path) | n.name] as chain
    ORDER BY length(path) DESC
    """
    return await neo4j.query(query, sid=session_id)

@app.get("/api/sessions/{session_id}/analytics/conflicts")
async def conflict_patterns(session_id: str):
    """Codes that contradict each other"""
    query = """
    MATCH (a:Code)-[r:CONFLICTS_WITH]-(b:Code)
    WHERE a.session_id = $sid AND id(a) < id(b)
    RETURN a.name, b.name, r.reason
    """
    return await neo4j.query(query, sid=session_id)
```

### 5. Enhanced UI Components

```jsx
// ConsensusView.jsx - Show model agreement/disagreement
function ConsensusView({ consensusResult }) {
  return (
    <div className="consensus-view">
      <h3>Model Agreement: {consensusResult.agreement_score}%</h3>
      
      <div className="consensus-codes">
        <h4>Agreed Codes ({consensusResult.agreed_codes.length})</h4>
        {consensusResult.agreed_codes.map(code => (
          <CodeCard 
            key={code.id}
            code={code}
            badge="Both Models"
            badgeColor="green"
          />
        ))}
      </div>
      
      <div className="conflicting-codes">
        <h4>Conflicting Interpretations</h4>
        {consensusResult.conflicts.map(conflict => (
          <ConflictCard
            key={conflict.id}
            geminiCode={conflict.gemini_code}
            claudeCode={conflict.claude_code}
            reason={conflict.reason}
          />
        ))}
      </div>
    </div>
  );
}

// AnalyticsDashboard.jsx - Network insights as tables
function AnalyticsDashboard({ sessionId }) {
  const [view, setView] = useState('most-connected');
  const [data, setData] = useState([]);
  
  const views = {
    'most-connected': 'Network Hubs',
    'causal-chains': 'Cause-Effect Chains',
    'conflicts': 'Contradictions',
    'clusters': 'Code Groups'
  };
  
  useEffect(() => {
    axios.get(`/api/sessions/${sessionId}/analytics/${view}`)
      .then(res => setData(res.data));
  }, [sessionId, view]);
  
  return (
    <div className="analytics-dashboard">
      <div className="view-tabs">
        {Object.entries(views).map(([key, label]) => (
          <button
            key={key}
            className={view === key ? 'active' : ''}
            onClick={() => setView(key)}
          >
            {label}
          </button>
        ))}
      </div>
      
      <AnalyticsTable data={data} type={view} />
      
      <button onClick={() => exportAnalytics(sessionId)}>
        Export Full Report
      </button>
    </div>
  );
}
```

### 6. Advanced Memo System
Link memos to codes and track theoretical development.

```python
# Enhanced memo with relationships
@app.post("/api/memos/{memo_id}/link-codes")
async def link_memo_to_codes(memo_id: str, code_ids: List[str]):
    """Create memo-analyzes-code relationships in graph"""
    for code_id in code_ids:
        await neo4j.create_relationship(
            from_id=memo_id,
            to_id=code_id,
            type="ANALYZES"
        )

@app.get("/api/codes/{code_id}/theoretical-development")
async def get_theoretical_development(code_id: str):
    """Track how understanding of a code evolved through memos"""
    query = """
    MATCH (m:Memo)-[:ANALYZES]->(c:Code {id: $cid})
    RETURN m.title, m.content, m.created_at
    ORDER BY m.created_at
    """
    return await neo4j.query(query, cid=code_id)
```

---

## Migration Strategy

### Step 1: Add Consensus (Keep SQLite)
First add multi-model consensus while keeping simple storage:
```python
# Phase 1.5a - Consensus with SQLite
codes = await analyze_with_consensus(interview)
await sqlite_db.save_consensus_codes(codes)
```

### Step 2: Migrate to Neo4j
Then migrate data and add relationships:
```python
# Phase 1.5b - Move to graph
await migrate_to_neo4j(session_id)
relationships = await discover_relationships(codes)
await store_relationships(relationships)
```

### Step 3: Add Analytics
Finally add analytics on top of graph:
```python
# Phase 1.5c - Analytics layer
analytics = PredefinedAnalytics(neo4j)
results = await analytics.get_most_connected(session_id)
```

---

## Technical Considerations

### 1. Database Migration
```python
# Provide both options during transition
class DualDatabaseAdapter:
    def __init__(self):
        self.sqlite = SQLiteDB()
        self.neo4j = Neo4jDB()
        self.use_graph = False  # Feature flag
    
    async def get_codes(self, session_id):
        if self.use_graph:
            return await self.neo4j.get_codes(session_id)
        return await self.sqlite.get_codes(session_id)
```

### 2. Backward Compatibility
- Keep all Phase 1.0 endpoints working
- Add new endpoints for consensus/analytics
- Use feature flags for gradual rollout

### 3. Performance Optimization
```python
# Cache expensive graph queries
@cache(ttl=300)  # 5 minute cache
async def get_most_connected_codes(session_id: str):
    # Expensive graph traversal
    return await neo4j.query(complex_query)
```

---

## Implementation Timeline

### Week 4: Consensus + Relationships
- **Day 1-2**: Add Claude client and consensus algorithm
- **Day 3**: Set up Neo4j with Docker
- **Day 4**: Implement data migration
- **Day 5**: Add relationship discovery

### Week 5: Analytics + UI
- **Day 1-2**: Create analytics queries
- **Day 3**: Build analytics UI components
- **Day 4**: Enhance memo system with linking
- **Day 5**: Testing and integration

---

## Success Criteria

### Must Have
- [ ] Multi-model consensus working
- [ ] Codes migrated to Neo4j
- [ ] At least 3 analytics views
- [ ] Relationships discovered by LLM
- [ ] Memos can link to codes

### Nice to Have
- [ ] Export network visualization
- [ ] Batch relationship editing
- [ ] Custom analytics queries

---

## Risks and Mitigations

### Risk: Neo4j Setup Complexity
**Mitigation**: Provide Docker Compose file with pre-configured Neo4j

### Risk: Consensus Failures
**Mitigation**: Fallback to side-by-side view when models disagree strongly

### Risk: Graph Query Performance
**Mitigation**: Index key properties, cache common queries

---

## Future Extensions (Phase 2.0)

1. **Natural Language Querying** - After understanding user needs
2. **Cross-Session Analysis** - Compare across projects
3. **Temporal Analysis** - How codes evolve over time
4. **Custom Relationship Types** - User-defined connections
5. **Machine Learning** - Suggest codes based on past analyses
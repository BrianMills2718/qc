# Simplified Neo4j Approach for Qualitative Coding

## 🎯 Core Philosophy: Research Tool, Not Production System

**Key Decision**: Use Neo4j Desktop for graph queries without enterprise complexity.

---

## 📊 Why Neo4j Desktop?

### What We Actually Need:
1. **Graph Queries** for quote chains and code progressions
2. **Visual Browser** to explore relationships
3. **Simple Persistence** for 103 interviews
4. **Research Flexibility** to try different queries

### What We DON'T Need:
- ACID compliance (this isn't banking)
- High availability (single researcher use)
- Production monitoring (just need it to work)
- Complex connection pooling (local database)
- Docker orchestration (just an app)

---

## 🏗️ Simple Implementation

### Step 1: Install Neo4j Desktop
```bash
# Download from: https://neo4j.com/download/
# Just install like any desktop app
# Create a local database called "qualitative_coding"
# Start it with default settings (bolt://localhost:7687)
```

### Step 2: Simple Neo4j Client
```python
# qc/storage/simple_neo4j_client.py
from neo4j import GraphDatabase
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SimpleNeo4jClient:
    """Simple Neo4j client for research use - no production complexity"""
    
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("Connected to Neo4j Desktop")
    
    def close(self):
        self.driver.close()
    
    def store_interview_result(self, result: Dict[str, Any]) -> str:
        """Store three-phase coding result in graph format"""
        with self.driver.session() as session:
            # Simple transaction - store the interview
            interview_id = session.write_transaction(
                self._create_interview_subgraph, result
            )
            logger.info(f"Stored interview {interview_id} in Neo4j")
            return interview_id
    
    def _create_interview_subgraph(self, tx, result):
        """Create nodes and relationships for one interview"""
        # Create interview node
        tx.run("""
            CREATE (i:Interview {
                id: $interview_id,
                file_path: $file_path,
                processed_date: datetime()
            })
        """, interview_id=result['interview_id'], 
             file_path=result['metadata']['file_path'])
        
        # Create codes with quotes
        for code in result['open_coding_result']['codes']:
            tx.run("""
                MATCH (i:Interview {id: $interview_id})
                CREATE (c:Code {
                    id: $code_id,
                    name: $name,
                    definition: $definition
                })
                CREATE (i)-[:HAS_CODE]->(c)
            """, interview_id=result['interview_id'],
                 code_id=code['id'],
                 name=code['name'],
                 definition=code['definition'])
            
            # Add quotes for each code
            for segment in code['segments']:
                tx.run("""
                    MATCH (c:Code {id: $code_id})
                    CREATE (q:Quote {
                        id: $quote_id,
                        text: $text,
                        line_start: $line_start,
                        line_end: $line_end
                    })
                    CREATE (c)-[:HAS_QUOTE]->(q)
                """, code_id=code['id'],
                     quote_id=segment['id'],
                     text=segment['text'],
                     line_start=segment['start_line'],
                     line_end=segment['end_line'])
        
        return result['interview_id']
    
    # Graph queries for analysis
    def find_quote_chains(self, theme: str, min_length: int = 2) -> List[Dict]:
        """Find chains of quotes showing progression of ideas"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Theme {name: $theme})-[:CONTAINS]->(c:Code)
                MATCH (c)-[:HAS_QUOTE]->(q1:Quote)
                MATCH path = (q1)-[:LEADS_TO*1..10]->(q2:Quote)
                WHERE length(path) >= $min_length
                RETURN path, 
                       [n in nodes(path) | n.text] as quote_sequence,
                       length(path) as chain_length
                ORDER BY chain_length DESC
                LIMIT 20
            """, theme=theme, min_length=min_length)
            
            return [record.data() for record in result]
    
    def find_code_progression(self, code_name: str) -> List[Dict]:
        """Track how a code develops across interviews"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Code {name: $code_name})-[:HAS_QUOTE]->(q:Quote)
                MATCH (i:Interview)-[:HAS_CODE]->(c)
                RETURN i.id as interview_id,
                       q.text as quote,
                       q.line_start as line,
                       i.processed_date as date
                ORDER BY date, line
            """, code_name=code_name)
            
            return [record.data() for record in result]
    
    def find_contradictions(self) -> List[Dict]:
        """Find opposing viewpoints in the data"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c1:Code)-[:CONTRADICTS]->(c2:Code)
                MATCH (c1)-[:HAS_QUOTE]->(q1:Quote)
                MATCH (c2)-[:HAS_QUOTE]->(q2:Quote)
                RETURN c1.name as position_1,
                       c2.name as position_2,
                       collect(DISTINCT q1.text)[0..3] as evidence_1,
                       collect(DISTINCT q2.text)[0..3] as evidence_2
                LIMIT 10
            """)
            
            return [record.data() for record in result]
    
    def export_for_networkx(self) -> Dict:
        """Export graph data for NetworkX analysis if needed"""
        with self.driver.session() as session:
            nodes = session.run("MATCH (n) RETURN n").data()
            edges = session.run("MATCH ()-[r]->() RETURN r").data()
            return {"nodes": nodes, "edges": edges}
```

### Step 3: Integration with Three-Phase Pipeline
```python
# In qc/core/three_phase_extractor.py
async def process_interview_with_neo4j(self, file_path: Path) -> Dict:
    """Process interview and store in Neo4j"""
    
    # Run three-phase coding
    result = await self.perform_three_phase_coding(
        transcript=interview.content,
        interview_id=interview.id
    )
    
    # Store in Neo4j (simple, no transactions needed)
    self.neo4j_client.store_interview_result(result)
    
    # Also save JSON for backup/portability
    with open(f"output/{interview.id}.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    return result
```

---

## 🔍 Example Queries We Can Now Do

### 1. Quote Chain Analysis
```cypher
// Find how "trust" concept evolved
MATCH path = (q1:Quote)-[:LEADS_TO*]->(q2:Quote)
WHERE q1.text CONTAINS 'distrust' AND q2.text CONTAINS 'trust'
RETURN path
```

### 2. Code Development Tracking
```cypher
// See how a code appears across interviews
MATCH (i:Interview)-[:HAS_CODE]->(c:Code {name: 'remote_work_challenges'})
MATCH (c)-[:HAS_QUOTE]->(q:Quote)
RETURN i.id, i.processed_date, collect(q.text) as quotes
ORDER BY i.processed_date
```

### 3. Contradiction Networks
```cypher
// Find participants with opposing views
MATCH (p1:Participant)-[:SAID]->(q1:Quote)-[:SUPPORTS]->(position:Position)
MATCH (p2:Participant)-[:SAID]->(q2:Quote)-[:OPPOSES]->(position)
WHERE p1 <> p2
RETURN p1.id, p2.id, position.topic, q1.text, q2.text
```

---

## 📁 Simplified File Structure

```
qc/
├── storage/
│   ├── simple_neo4j_client.py  # Just the basics
│   └── json_backup.py          # For portability
├── core/
│   └── three_phase_extractor.py
└── output/
    ├── graphs/                 # Neo4j query results
    └── json/                   # JSON backups
```

---

## 🚀 Getting Started

1. **Install Neo4j Desktop** (5 minutes)
2. **Create local database** (2 minutes)
3. **Run our simple client** (works immediately)

No Docker, no Kubernetes, no production config. Just a graph database for research.

---

## 💡 When to Add Complexity

Only add features when you actually need them:
- **Connection pooling**: When processing gets slow
- **Transactions**: If you need atomic operations
- **Indexes**: When queries get slow with 100+ interviews
- **Constraints**: If data integrity becomes an issue

For 103 interviews, the simple approach will work perfectly.
"""
Neo4j-Style Connected Graph Viewer for Qualitative Coding Results
Interactive exploration of codes, quotes, entities, and their relationships
"""

import streamlit as st
import json
from pathlib import Path
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config
from collections import defaultdict
import random

# Page config
st.set_page_config(
    page_title="Graph Explorer - Qualitative Coding",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Neo4j-like styling
st.markdown("""
<style>
    .stApp {
        background-color: #f5f5f5;
    }
    .details-panel {
        background-color: white;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-top: 10px;
    }
    .node-type-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 5px;
    }
    .quote-type { background-color: #4A90E2; color: white; }
    .code-type { background-color: #7FBA00; color: white; }
    .speaker-type { background-color: #FF8C00; color: white; }
    .entity-type { background-color: #AA4A98; color: white; }
    .interview-type { background-color: #808080; color: white; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(output_dir):
    """Load all data from output directory"""
    output_path = Path(output_dir)
    data = {}
    
    # Load taxonomy
    taxonomy_file = output_path / "taxonomy.json"
    if taxonomy_file.exists():
        with open(taxonomy_file, 'r', encoding='utf-8') as f:
            data['taxonomy'] = json.load(f)
    
    # Load schemas
    speaker_file = output_path / "speaker_schema.json"
    if speaker_file.exists():
        with open(speaker_file, 'r', encoding='utf-8') as f:
            data['speaker_schema'] = json.load(f)
    
    entity_file = output_path / "entity_schema.json"
    if entity_file.exists():
        with open(entity_file, 'r', encoding='utf-8') as f:
            data['entity_schema'] = json.load(f)
    
    # Load all interviews
    data['interviews'] = {}
    interview_dir = output_path / "interviews"
    if interview_dir.exists():
        for file in interview_dir.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                interview_data = json.load(f)
                data['interviews'][file.stem] = interview_data
    
    return data

def build_graph_data(data, focus_node=None, depth=1):
    """Build nodes and edges for the graph visualization"""
    nodes = []
    edges = []
    node_ids = set()
    
    # Node colors by type
    colors = {
        'quote': '#4A90E2',      # Blue
        'code': '#7FBA00',       # Green
        'speaker': '#FF8C00',    # Orange
        'entity': '#AA4A98',     # Purple
        'interview': '#808080',  # Gray
        'relationship': '#FF1493' # Deep Pink
    }
    
    # Build code nodes from taxonomy
    if 'taxonomy' in data and data['taxonomy']:
        for code in data['taxonomy'].get('codes', []):
            code_id = f"code_{code['id']}"
            if code_id not in node_ids:
                nodes.append(Node(
                    id=code_id,
                    label=code['name'],
                    size=25,
                    color=colors['code'],
                    title=code.get('description', ''),
                    node_type='code',
                    data=code
                ))
                node_ids.add(code_id)
            
            # Add parent-child relationships between codes
            if code.get('parent_id') and code['parent_id'] != 'None':
                parent_id = f"code_{code['parent_id']}"
                edges.append(Edge(
                    source=parent_id,
                    target=code_id,
                    label="parent_of",
                    color="#cccccc"
                ))
    
    # Build nodes from interviews
    for interview_name, interview in data.get('interviews', {}).items():
        # Add interview node
        interview_id = f"interview_{interview_name}"
        if interview_id not in node_ids:
            nodes.append(Node(
                id=interview_id,
                label=interview_name[:30],
                size=30,
                color=colors['interview'],
                title=f"Interview: {interview_name}",
                node_type='interview',
                data={'name': interview_name}
            ))
            node_ids.add(interview_id)
        
        # Add speakers
        for speaker in interview.get('speakers', []):
            speaker_id = f"speaker_{speaker['name']}"
            if speaker_id not in node_ids:
                nodes.append(Node(
                    id=speaker_id,
                    label=speaker['name'],
                    size=20,
                    color=colors['speaker'],
                    title=f"Speaker: {speaker['name']}",
                    node_type='speaker',
                    data=speaker
                ))
                node_ids.add(speaker_id)
            
            # Link speaker to interview
            edges.append(Edge(
                source=speaker_id,
                target=interview_id,
                label="participates_in",
                color="#cccccc"
            ))
        
        # Add quotes (limit for performance)
        for i, quote in enumerate(interview.get('quotes', [])[:50]):  # Limit to 50 quotes per interview
            quote_id = f"quote_{interview_name}_{i}"
            quote_text = quote['text'][:100] + "..." if len(quote['text']) > 100 else quote['text']
            
            if quote_id not in node_ids:
                nodes.append(Node(
                    id=quote_id,
                    label=f"Quote {i+1}",
                    size=15,
                    color=colors['quote'],
                    title=quote_text,
                    node_type='quote',
                    data=quote
                ))
                node_ids.add(quote_id)
            
            # Link quote to speaker
            if quote.get('speaker'):
                speaker_id = f"speaker_{quote['speaker']['name']}"
                edges.append(Edge(
                    source=quote_id,
                    target=speaker_id,
                    label="spoken_by",
                    color="#cccccc"
                ))
            
            # Link quote to codes
            for code in quote.get('codes', []):
                code_id = f"code_{code.get('code_id', code.get('id', ''))}"
                if code_id != "code_":
                    edges.append(Edge(
                        source=quote_id,
                        target=code_id,
                        label="coded_with",
                        color="#90EE90"
                    ))
            
            # Link quote to interview
            edges.append(Edge(
                source=quote_id,
                target=interview_id,
                label="from",
                color="#cccccc"
            ))
        
        # Add entities
        for entity in interview.get('interview_entities', [])[:30]:  # Limit entities
            entity_id = f"entity_{entity['name']}"
            if entity_id not in node_ids:
                nodes.append(Node(
                    id=entity_id,
                    label=entity['name'][:20],
                    size=18,
                    color=colors['entity'],
                    title=f"{entity['type']}: {entity['name']}",
                    node_type='entity',
                    data=entity
                ))
                node_ids.add(entity_id)
        
        # Add relationships between entities
        for rel in interview.get('interview_relationships', [])[:30]:  # Limit relationships
            source_id = f"entity_{rel.get('source_entity', '')}"
            target_id = f"entity_{rel.get('target_entity', '')}"
            rel_type = rel.get('relationship_type', rel.get('type', 'related'))
            
            if source_id in node_ids and target_id in node_ids:
                edges.append(Edge(
                    source=source_id,
                    target=target_id,
                    label=rel_type,
                    color="#FF69B4"
                ))
    
    return nodes, edges

def display_node_details(selected_nodes, data):
    """Display details for selected nodes"""
    if not selected_nodes:
        st.info("👆 Click on a node to see its details")
        return
    
    for node_id in selected_nodes:
        st.markdown("---")
        
        # Parse node type and display appropriate details
        if node_id.startswith("quote_"):
            st.markdown('<span class="node-type-badge quote-type">QUOTE</span>', unsafe_allow_html=True)
            # Find the quote data
            parts = node_id.replace("quote_", "").rsplit("_", 1)
            if len(parts) == 2:
                interview_name, quote_idx = parts
                quote_idx = int(quote_idx)
                if interview_name in data.get('interviews', {}):
                    quotes = data['interviews'][interview_name].get('quotes', [])
                    if quote_idx < len(quotes):
                        quote = quotes[quote_idx]
                        st.write(f"**Text:** {quote['text']}")
                        if quote.get('speaker'):
                            st.write(f"**Speaker:** {quote['speaker']['name']}")
                        if quote.get('codes'):
                            codes = [c.get('code_id', c.get('id', 'Unknown')) for c in quote['codes']]
                            st.write(f"**Codes:** {', '.join(codes)}")
        
        elif node_id.startswith("code_"):
            st.markdown('<span class="node-type-badge code-type">CODE</span>', unsafe_allow_html=True)
            code_id = node_id.replace("code_", "")
            # Find code in taxonomy
            if 'taxonomy' in data and data['taxonomy']:
                for code in data['taxonomy'].get('codes', []):
                    if code['id'] == code_id:
                        st.write(f"**Name:** {code['name']}")
                        st.write(f"**Description:** {code.get('description', 'N/A')}")
                        if code.get('semantic_definition'):
                            st.write(f"**Definition:** {code['semantic_definition']}")
                        if code.get('example_quotes'):
                            st.write("**Example Quotes:**")
                            for ex in code['example_quotes'][:2]:
                                st.info(f'"{ex[:200]}..."')
                        break
        
        elif node_id.startswith("speaker_"):
            st.markdown('<span class="node-type-badge speaker-type">SPEAKER</span>', unsafe_allow_html=True)
            speaker_name = node_id.replace("speaker_", "")
            st.write(f"**Name:** {speaker_name}")
            
            # Count quotes from this speaker
            quote_count = 0
            for interview in data.get('interviews', {}).values():
                for quote in interview.get('quotes', []):
                    if quote.get('speaker', {}).get('name') == speaker_name:
                        quote_count += 1
            st.write(f"**Total Quotes:** {quote_count}")
        
        elif node_id.startswith("entity_"):
            st.markdown('<span class="node-type-badge entity-type">ENTITY</span>', unsafe_allow_html=True)
            entity_name = node_id.replace("entity_", "")
            st.write(f"**Name:** {entity_name}")
            
            # Find entity details
            for interview in data.get('interviews', {}).values():
                for entity in interview.get('interview_entities', []):
                    if entity['name'] == entity_name:
                        st.write(f"**Type:** {entity.get('type', 'Unknown')}")
                        st.write(f"**Mentions:** {entity.get('mention_count', 0)}")
                        if entity.get('contexts'):
                            st.write(f"**Contexts:** {', '.join(entity['contexts'][:3])}")
                        break
        
        elif node_id.startswith("interview_"):
            st.markdown('<span class="node-type-badge interview-type">INTERVIEW</span>', unsafe_allow_html=True)
            interview_name = node_id.replace("interview_", "")
            if interview_name in data.get('interviews', {}):
                interview = data['interviews'][interview_name]
                st.write(f"**Name:** {interview_name}")
                st.write(f"**Quotes:** {len(interview.get('quotes', []))}")
                st.write(f"**Speakers:** {len(interview.get('speakers', []))}")
                st.write(f"**Entities:** {len(interview.get('interview_entities', []))}")
                st.write(f"**Relationships:** {len(interview.get('interview_relationships', []))}")

def main():
    st.title("🔗 Graph Explorer - Qualitative Coding")
    st.markdown("**Neo4j-style interactive exploration** - Click any node to explore connections")
    
    # Sidebar controls
    st.sidebar.title("⚙️ Controls")
    
    # Data selection
    output_dirs = []
    for d in Path('.').glob('output*'):
        if d.is_dir() and (d / "taxonomy.json").exists():
            output_dirs.append(d)
    
    if not output_dirs:
        st.error("No output directories found. Please run the extraction pipeline first.")
        return
    
    selected_dir = st.sidebar.selectbox(
        "📁 Select Data Source",
        options=[str(d) for d in output_dirs],
        index=len(output_dirs)-1 if output_dirs else 0
    )
    
    # Load data
    data = load_data(selected_dir)
    
    if not data:
        st.error("No data found in selected directory")
        return
    
    # Display statistics
    st.sidebar.markdown("### 📊 Dataset Statistics")
    st.sidebar.metric("Interviews", len(data.get('interviews', {})))
    if 'taxonomy' in data and data['taxonomy']:
        st.sidebar.metric("Codes", len(data['taxonomy'].get('codes', [])))
    
    total_quotes = sum(len(i.get('quotes', [])) for i in data.get('interviews', {}).values())
    st.sidebar.metric("Quotes", total_quotes)
    
    total_entities = sum(len(i.get('interview_entities', [])) for i in data.get('interviews', {}).values())
    st.sidebar.metric("Entities", total_entities)
    
    # Filter controls
    st.sidebar.markdown("### 🎯 Focus & Filter")
    
    node_types = st.sidebar.multiselect(
        "Show Node Types",
        options=['Quotes', 'Codes', 'Speakers', 'Entities', 'Interviews'],
        default=['Codes', 'Speakers', 'Entities']
    )
    
    # Search
    search_term = st.sidebar.text_input("🔍 Search nodes", "")
    
    # Graph configuration
    config = Config(
        width=1200,
        height=700,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False
    )
    
    # Build graph
    with st.spinner("Building graph..."):
        nodes, edges = build_graph_data(data)
        
        # Filter based on selected node types
        filtered_nodes = []
        filtered_node_ids = set()
        
        for node in nodes:
            include = False
            if 'Quotes' in node_types and node.node_type == 'quote':
                include = True
            elif 'Codes' in node_types and node.node_type == 'code':
                include = True
            elif 'Speakers' in node_types and node.node_type == 'speaker':
                include = True
            elif 'Entities' in node_types and node.node_type == 'entity':
                include = True
            elif 'Interviews' in node_types and node.node_type == 'interview':
                include = True
            
            # Apply search filter
            if search_term and search_term.lower() not in node.label.lower():
                include = False
            
            if include:
                filtered_nodes.append(node)
                filtered_node_ids.add(node.id)
        
        # Filter edges to only include those between visible nodes
        filtered_edges = [e for e in edges if e.source in filtered_node_ids and e.to in filtered_node_ids]
    
    # Display instructions
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🖱️ **Click** to select • **Drag** to move • **Scroll** to zoom")
    with col2:
        st.info("🔗 **Double-click** to expand connections (coming soon)")
    with col3:
        st.info("📊 Currently showing **{} nodes** and **{} edges**".format(len(filtered_nodes), len(filtered_edges)))
    
    # Display the graph
    if filtered_nodes:
        return_value = agraph(
            nodes=filtered_nodes,
            edges=filtered_edges,
            config=config
        )
        
        # Display details for selected nodes
        if return_value:
            st.markdown("### 📋 Node Details")
            display_node_details([return_value], data)
    else:
        st.warning("No nodes to display. Try adjusting your filters.")
    
    # Export options
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Export")
    
    if st.sidebar.button("Export to Neo4j Format"):
        # Create Cypher commands for Neo4j import
        cypher_commands = []
        
        # Create constraints
        cypher_commands.append("// Create constraints")
        cypher_commands.append("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Code) REQUIRE c.id IS UNIQUE;")
        cypher_commands.append("CREATE CONSTRAINT IF NOT EXISTS FOR (q:Quote) REQUIRE q.id IS UNIQUE;")
        cypher_commands.append("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Speaker) REQUIRE s.name IS UNIQUE;")
        cypher_commands.append("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE;")
        cypher_commands.append("")
        
        # Create nodes
        cypher_commands.append("// Create nodes")
        for node in filtered_nodes:
            if node.node_type == 'code':
                cypher_commands.append(f"CREATE (c:Code {{id: '{node.id}', name: '{node.label}'}});")
            elif node.node_type == 'quote':
                cypher_commands.append(f"CREATE (q:Quote {{id: '{node.id}', text: '{node.title[:100]}'}});")
            elif node.node_type == 'speaker':
                cypher_commands.append(f"CREATE (s:Speaker {{name: '{node.label}'}});")
            elif node.node_type == 'entity':
                cypher_commands.append(f"CREATE (e:Entity {{name: '{node.label}'}});")
        
        cypher_commands.append("")
        cypher_commands.append("// Create relationships")
        for edge in filtered_edges:
            cypher_commands.append(f"MATCH (a {{id: '{edge.source}'}}), (b {{id: '{edge.to}'}}) CREATE (a)-[:{edge.label.upper()}]->(b);")
        
        # Offer download
        cypher_script = "\n".join(cypher_commands)
        st.sidebar.download_button(
            label="Download Neo4j Script",
            data=cypher_script,
            file_name="qualitative_coding_neo4j.cypher",
            mime="text/plain"
        )
        st.sidebar.success("✅ Neo4j script ready for download!")

if __name__ == "__main__":
    main()
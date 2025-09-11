"""
Connected Viewer for Qualitative Coding Results
Everything is interlinked - click any code, speaker, entity to see all its connections
"""

import streamlit as st
import json
from pathlib import Path
import pandas as pd
from collections import defaultdict, Counter

# Page config
st.set_page_config(
    page_title="Connected Viewer - Qualitative Coding",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state for navigation
if 'current_view' not in st.session_state:
    st.session_state.current_view = {'type': None, 'id': None}

# Custom CSS
st.markdown("""
<style>
    .clickable-link {
        color: #0066cc;
        text-decoration: underline;
        cursor: pointer;
    }
    .code-badge {
        background-color: #7FBA00;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        margin: 2px;
        display: inline-block;
    }
    .speaker-badge {
        background-color: #FF8C00;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        margin: 2px;
        display: inline-block;
    }
    .entity-badge {
        background-color: #AA4A98;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        margin: 2px;
        display: inline-block;
    }
    .quote-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-left: 4px solid #4A90E2;
        margin: 10px 0;
        border-radius: 4px;
    }
    .stats-box {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
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

def build_indexes(data):
    """Build indexes for quick lookups"""
    indexes = {
        'codes_to_quotes': defaultdict(list),
        'speakers_to_quotes': defaultdict(list),
        'entities_to_quotes': defaultdict(list),
        'quotes_to_codes': defaultdict(list),
        'quotes_to_entities': defaultdict(list),
        'code_hierarchy': defaultdict(list),
        'entity_relationships': defaultdict(list),
        'speaker_stats': defaultdict(lambda: {'quotes': 0, 'codes': set(), 'entities': set()}),
        'code_stats': defaultdict(lambda: {'quotes': 0, 'speakers': set(), 'entities': set()}),
        'entity_stats': defaultdict(lambda: {'mentions': 0, 'speakers': set(), 'codes': set(), 'relationships': []})
    }
    
    # Build code hierarchy
    if 'taxonomy' in data and data['taxonomy']:
        for code in data['taxonomy'].get('codes', []):
            if code.get('parent_id') and code['parent_id'] != 'None':
                indexes['code_hierarchy'][code['parent_id']].append(code['id'])
    
    # Process interviews
    for interview_name, interview in data.get('interviews', {}).items():
        # Process quotes
        for i, quote in enumerate(interview.get('quotes', [])):
            quote_id = f"{interview_name}_{i}"
            speaker_name = quote.get('speaker', {}).get('name', 'Unknown')
            
            # Index by speaker
            indexes['speakers_to_quotes'][speaker_name].append({
                'id': quote_id,
                'text': quote['text'],
                'interview': interview_name,
                'codes': quote.get('codes', [])
            })
            
            # Index by codes
            for code in quote.get('codes', []):
                code_id = code.get('code_id', code.get('id', ''))
                if code_id:
                    indexes['codes_to_quotes'][code_id].append({
                        'id': quote_id,
                        'text': quote['text'],
                        'speaker': speaker_name,
                        'interview': interview_name
                    })
                    indexes['quotes_to_codes'][quote_id].append(code_id)
                    
                    # Update stats
                    indexes['code_stats'][code_id]['quotes'] += 1
                    indexes['code_stats'][code_id]['speakers'].add(speaker_name)
            
            # Update speaker stats
            indexes['speaker_stats'][speaker_name]['quotes'] += 1
            for code in quote.get('codes', []):
                code_id = code.get('code_id', code.get('id', ''))
                if code_id:
                    indexes['speaker_stats'][speaker_name]['codes'].add(code_id)
        
        # Process entities
        for entity in interview.get('interview_entities', []):
            entity_name = entity['name']
            entity_type = entity['type']
            
            # Update entity stats
            indexes['entity_stats'][entity_name]['mentions'] += entity.get('mention_count', 1)
            indexes['entity_stats'][entity_name]['type'] = entity_type
            
            # Link entities to quotes (approximate - based on context)
            for context in entity.get('contexts', []):
                for i, quote in enumerate(interview.get('quotes', [])):
                    if context.lower() in quote['text'].lower():
                        quote_id = f"{interview_name}_{i}"
                        indexes['entities_to_quotes'][entity_name].append({
                            'id': quote_id,
                            'text': quote['text'],
                            'interview': interview_name
                        })
                        indexes['quotes_to_entities'][quote_id].append(entity_name)
                        
                        # Link entity to speaker
                        speaker_name = quote.get('speaker', {}).get('name', 'Unknown')
                        indexes['entity_stats'][entity_name]['speakers'].add(speaker_name)
                        indexes['speaker_stats'][speaker_name]['entities'].add(entity_name)
                        
                        # Link entity to codes
                        for code in quote.get('codes', []):
                            code_id = code.get('code_id', code.get('id', ''))
                            if code_id:
                                indexes['entity_stats'][entity_name]['codes'].add(code_id)
                                indexes['code_stats'][code_id]['entities'].add(entity_name)
        
        # Process relationships
        for rel in interview.get('interview_relationships', []):
            source = rel.get('source_entity', '')
            target = rel.get('target_entity', '')
            rel_type = rel.get('relationship_type', rel.get('type', 'related'))
            
            if source and target:
                indexes['entity_relationships'][source].append({
                    'target': target,
                    'type': rel_type
                })
                indexes['entity_stats'][source]['relationships'].append({
                    'entity': target,
                    'type': rel_type,
                    'direction': 'outgoing'
                })
                indexes['entity_stats'][target]['relationships'].append({
                    'entity': source,
                    'type': rel_type,
                    'direction': 'incoming'
                })
    
    return indexes

def navigate_to(view_type, item_id):
    """Navigate to a specific view"""
    st.session_state.current_view = {'type': view_type, 'id': item_id}
    st.rerun()

def display_codes_tab(data, indexes):
    """Display the Codes tab with all connections"""
    st.header("📚 Codes")
    
    if not data.get('taxonomy'):
        st.warning("No taxonomy found")
        return
    
    codes = data['taxonomy'].get('codes', [])
    
    # Create code lookup
    code_dict = {code['id']: code for code in codes}
    
    # Sidebar for code list
    with st.sidebar:
        st.subheader("Code List")
        
        # Search
        search = st.text_input("Search codes", "")
        
        # Filter codes
        filtered_codes = codes
        if search:
            filtered_codes = [c for c in codes if search.lower() in c['name'].lower()]
        
        # Display code tree
        def display_code_tree(parent_id=None, level=0):
            for code in filtered_codes:
                if (parent_id is None and not code.get('parent_id')) or \
                   (code.get('parent_id') == parent_id):
                    indent = "　" * level
                    if st.button(f"{indent}→ {code['name']}", key=f"code_nav_{code['id']}"):
                        navigate_to('code', code['id'])
                    
                    # Display children
                    if code['id'] in indexes['code_hierarchy']:
                        display_code_tree(code['id'], level + 1)
        
        display_code_tree()
    
    # Main content area
    selected_code_id = st.session_state.current_view.get('id')
    
    if selected_code_id and selected_code_id in code_dict:
        code = code_dict[selected_code_id]
        
        # Code header
        st.subheader(f"Code: {code['name']}")
        
        # Code details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Description")
            st.write(code.get('description', 'No description available'))
            
            if code.get('semantic_definition'):
                st.markdown("### Semantic Definition")
                st.write(code['semantic_definition'])
        
        with col2:
            st.markdown("### Statistics")
            stats = indexes['code_stats'][selected_code_id]
            st.metric("Total Quotes", stats['quotes'])
            st.metric("Unique Speakers", len(stats['speakers']))
            st.metric("Related Entities", len(stats['entities']))
        
        # Parent/Child codes
        if code.get('parent_id') and code['parent_id'] in code_dict:
            st.markdown("### Parent Code")
            parent = code_dict[code['parent_id']]
            if st.button(f"⬆️ {parent['name']}", key=f"parent_{parent['id']}"):
                navigate_to('code', parent['id'])
        
        if selected_code_id in indexes['code_hierarchy']:
            st.markdown("### Child Codes")
            for child_id in indexes['code_hierarchy'][selected_code_id]:
                if child_id in code_dict:
                    child = code_dict[child_id]
                    if st.button(f"⬇️ {child['name']}", key=f"child_{child['id']}"):
                        navigate_to('code', child['id'])
        
        # Quotes with this code
        st.markdown("### Quotes with this Code")
        quotes = indexes['codes_to_quotes'][selected_code_id]
        
        if quotes:
            for i, quote in enumerate(quotes[:20]):  # Limit to 20
                with st.expander(f"Quote {i+1} - Speaker: {quote['speaker']} ({quote['interview']})"):
                    st.markdown(f'<div class="quote-box">{quote["text"]}</div>', unsafe_allow_html=True)
                    if st.button(f"View Speaker: {quote['speaker']}", key=f"speaker_from_code_{i}"):
                        navigate_to('speaker', quote['speaker'])
        else:
            st.info("No quotes found with this code")
        
        # Related entities
        if stats['entities']:
            st.markdown("### Related Entities")
            cols = st.columns(4)
            for i, entity in enumerate(list(stats['entities'])[:20]):
                with cols[i % 4]:
                    if st.button(entity, key=f"entity_from_code_{entity}"):
                        navigate_to('entity', entity)
        
        # Related speakers
        if stats['speakers']:
            st.markdown("### Speakers using this Code")
            cols = st.columns(4)
            for i, speaker in enumerate(stats['speakers']):
                with cols[i % 4]:
                    if st.button(speaker, key=f"speaker_link_from_code_{speaker}"):
                        navigate_to('speaker', speaker)
    else:
        st.info("Select a code from the sidebar to view details")

def display_speakers_tab(data, indexes):
    """Display the Speakers tab with all connections"""
    st.header("👥 Speakers")
    
    # Get all speakers
    all_speakers = set()
    for interview in data.get('interviews', {}).values():
        for speaker in interview.get('speakers', []):
            all_speakers.add(speaker['name'])
    
    # Sidebar for speaker list
    with st.sidebar:
        st.subheader("Speaker List")
        for speaker in sorted(all_speakers):
            stats = indexes['speaker_stats'][speaker]
            if st.button(f"{speaker} ({stats['quotes']} quotes)", key=f"speaker_nav_{speaker}"):
                navigate_to('speaker', speaker)
    
    # Main content
    selected_speaker = st.session_state.current_view.get('id')
    
    if selected_speaker and selected_speaker in indexes['speaker_stats']:
        st.subheader(f"Speaker: {selected_speaker}")
        
        # Statistics
        stats = indexes['speaker_stats'][selected_speaker]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Quotes", stats['quotes'])
        with col2:
            st.metric("Codes Used", len(stats['codes']))
        with col3:
            st.metric("Entities Mentioned", len(stats['entities']))
        
        # Quotes from this speaker
        st.markdown("### Quotes")
        quotes = indexes['speakers_to_quotes'][selected_speaker]
        
        for i, quote in enumerate(quotes[:20]):  # Limit to 20
            with st.expander(f"Quote {i+1} - {quote['interview']}"):
                st.markdown(f'<div class="quote-box">{quote["text"]}</div>', unsafe_allow_html=True)
                
                # Show codes for this quote
                if quote.get('codes'):
                    st.markdown("**Codes:**")
                    cols = st.columns(6)
                    for j, code in enumerate(quote['codes']):
                        code_id = code.get('code_id', code.get('id', ''))
                        with cols[j % 6]:
                            if st.button(code_id, key=f"code_from_speaker_{i}_{j}"):
                                navigate_to('code', code_id)
        
        # Codes used by this speaker
        if stats['codes']:
            st.markdown("### All Codes Used")
            cols = st.columns(4)
            for i, code_id in enumerate(stats['codes']):
                with cols[i % 4]:
                    if st.button(code_id, key=f"all_codes_speaker_{code_id}"):
                        navigate_to('code', code_id)
        
        # Entities mentioned
        if stats['entities']:
            st.markdown("### Entities Mentioned")
            cols = st.columns(4)
            for i, entity in enumerate(stats['entities']):
                with cols[i % 4]:
                    if st.button(entity, key=f"entity_from_speaker_{entity}"):
                        navigate_to('entity', entity)
    else:
        st.info("Select a speaker from the sidebar to view details")

def display_entities_tab(data, indexes):
    """Display the Entities tab with all connections"""
    st.header("🔗 Entities")
    
    # Get all entities
    all_entities = set(indexes['entity_stats'].keys())
    
    # Sidebar for entity list
    with st.sidebar:
        st.subheader("Entity List")
        
        # Group by type
        entities_by_type = defaultdict(list)
        for entity, stats in indexes['entity_stats'].items():
            entity_type = stats.get('type', 'Unknown')
            entities_by_type[entity_type].append(entity)
        
        for entity_type, entities in sorted(entities_by_type.items()):
            with st.expander(f"{entity_type} ({len(entities)})"):
                for entity in sorted(entities):
                    if st.button(entity, key=f"entity_nav_{entity}"):
                        navigate_to('entity', entity)
    
    # Main content
    selected_entity = st.session_state.current_view.get('id')
    
    if selected_entity and selected_entity in indexes['entity_stats']:
        stats = indexes['entity_stats'][selected_entity]
        
        st.subheader(f"Entity: {selected_entity}")
        st.write(f"**Type:** {stats.get('type', 'Unknown')}")
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mentions", stats['mentions'])
        with col2:
            st.metric("Speakers", len(stats['speakers']))
        with col3:
            st.metric("Related Codes", len(stats['codes']))
        with col4:
            st.metric("Relationships", len(stats['relationships']))
        
        # Relationships
        if stats['relationships']:
            st.markdown("### Relationships")
            for rel in stats['relationships'][:20]:
                direction = "→" if rel['direction'] == 'outgoing' else "←"
                col1, col2, col3 = st.columns([2, 1, 2])
                with col1:
                    if rel['direction'] == 'outgoing':
                        st.write(f"{selected_entity}")
                    else:
                        if st.button(rel['entity'], key=f"rel_entity_{rel['entity']}_{rel['type']}"):
                            navigate_to('entity', rel['entity'])
                with col2:
                    st.write(f"{direction} {rel['type']} {direction}")
                with col3:
                    if rel['direction'] == 'outgoing':
                        if st.button(rel['entity'], key=f"rel_entity_out_{rel['entity']}_{rel['type']}"):
                            navigate_to('entity', rel['entity'])
                    else:
                        st.write(f"{selected_entity}")
        
        # Quotes mentioning this entity
        entity_quotes = indexes['entities_to_quotes'].get(selected_entity, [])
        if entity_quotes:
            st.markdown("### Quotes Mentioning This Entity")
            for i, quote in enumerate(entity_quotes[:10]):
                with st.expander(f"Quote from {quote['interview']}"):
                    st.markdown(f'<div class="quote-box">{quote["text"]}</div>', unsafe_allow_html=True)
        
        # Related codes
        if stats['codes']:
            st.markdown("### Related Codes")
            cols = st.columns(4)
            for i, code_id in enumerate(stats['codes']):
                with cols[i % 4]:
                    if st.button(code_id, key=f"code_from_entity_{code_id}"):
                        navigate_to('code', code_id)
        
        # Speakers mentioning this entity
        if stats['speakers']:
            st.markdown("### Speakers Mentioning This Entity")
            cols = st.columns(4)
            for i, speaker in enumerate(stats['speakers']):
                with cols[i % 4]:
                    if st.button(speaker, key=f"speaker_from_entity_{speaker}"):
                        navigate_to('speaker', speaker)
    else:
        st.info("Select an entity from the sidebar to view details")

def display_quotes_tab(data, indexes):
    """Display the Quotes tab with search and filtering"""
    st.header("💬 Quotes")
    
    # Search and filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search_text = st.text_input("Search quotes", "")
    with col2:
        speaker_filter = st.selectbox(
            "Filter by Speaker",
            ["All"] + sorted(list(indexes['speakers_to_quotes'].keys()))
        )
    with col3:
        code_filter = st.selectbox(
            "Filter by Code",
            ["All"] + sorted(list(indexes['codes_to_quotes'].keys()))
        )
    
    # Collect all quotes
    all_quotes = []
    for interview_name, interview in data.get('interviews', {}).items():
        for i, quote in enumerate(interview.get('quotes', [])):
            quote_data = {
                'id': f"{interview_name}_{i}",
                'text': quote['text'],
                'speaker': quote.get('speaker', {}).get('name', 'Unknown'),
                'interview': interview_name,
                'codes': [c.get('code_id', c.get('id', '')) for c in quote.get('codes', [])]
            }
            
            # Apply filters
            if search_text and search_text.lower() not in quote['text'].lower():
                continue
            if speaker_filter != "All" and quote_data['speaker'] != speaker_filter:
                continue
            if code_filter != "All" and code_filter not in quote_data['codes']:
                continue
            
            all_quotes.append(quote_data)
    
    # Display quotes
    st.write(f"Showing {len(all_quotes)} quotes")
    
    for quote in all_quotes[:50]:  # Limit to 50
        with st.expander(f"{quote['speaker']} - {quote['interview']}"):
            st.markdown(f'<div class="quote-box">{quote["text"]}</div>', unsafe_allow_html=True)
            
            # Clickable speaker
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button(f"Speaker: {quote['speaker']}", key=f"quote_speaker_{quote['id']}"):
                    navigate_to('speaker', quote['speaker'])
            
            # Clickable codes
            with col2:
                if quote['codes']:
                    st.write("Codes:")
                    cols = st.columns(6)
                    for i, code_id in enumerate(quote['codes']):
                        with cols[i % 6]:
                            if st.button(code_id, key=f"quote_code_{quote['id']}_{code_id}"):
                                navigate_to('code', code_id)

def main():
    st.title("🔗 Connected Viewer - Qualitative Coding")
    st.markdown("Everything is connected - click any code, speaker, or entity to explore")
    
    # Data selection
    output_dirs = []
    for d in Path('.').glob('output*'):
        if d.is_dir() and (d / "taxonomy.json").exists():
            output_dirs.append(d)
    
    if not output_dirs:
        st.error("No output directories found. Please run the extraction pipeline first.")
        return
    
    selected_dir = st.selectbox(
        "Select Data Source",
        options=[str(d) for d in output_dirs],
        index=len(output_dirs)-1 if output_dirs else 0
    )
    
    # Load data and build indexes
    with st.spinner("Loading data..."):
        data = load_data(selected_dir)
        indexes = build_indexes(data)
    
    # Navigation breadcrumb
    if st.session_state.current_view['type']:
        breadcrumb = f"📍 Current: {st.session_state.current_view['type'].title()} > {st.session_state.current_view['id']}"
        st.markdown(breadcrumb)
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Codes", "👥 Speakers", "🔗 Entities", "💬 Quotes"])
    
    with tab1:
        display_codes_tab(data, indexes)
    
    with tab2:
        display_speakers_tab(data, indexes)
    
    with tab3:
        display_entities_tab(data, indexes)
    
    with tab4:
        display_quotes_tab(data, indexes)

if __name__ == "__main__":
    main()
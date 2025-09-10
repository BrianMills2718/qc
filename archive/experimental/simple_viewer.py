"""
Simple Connected Viewer for Qualitative Coding Results
Clean interface with dropdowns and clickable links between all related data
"""

import streamlit as st
import json
from pathlib import Path
from collections import defaultdict

# Page config
st.set_page_config(
    page_title="Qualitative Coding Viewer",
    page_icon="📊",
    layout="wide"
)

# Session state for navigation
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0
if 'selected_code' not in st.session_state:
    st.session_state.selected_code = None
if 'selected_speaker' not in st.session_state:
    st.session_state.selected_speaker = None
if 'selected_entity' not in st.session_state:
    st.session_state.selected_entity = None

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
    
    # Load interviews
    data['interviews'] = {}
    interview_dir = output_path / "interviews"
    if interview_dir.exists():
        for file in interview_dir.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                interview_data = json.load(f)
                data['interviews'][file.stem] = interview_data
    
    return data

@st.cache_data
def build_connections(data):
    """Build all the connections between codes, speakers, entities, and quotes"""
    connections = {
        'code_to_quotes': defaultdict(list),
        'code_to_speakers': defaultdict(set),
        'code_to_entities': defaultdict(set),
        'speaker_to_quotes': defaultdict(list),
        'speaker_to_codes': defaultdict(set),
        'speaker_to_entities': defaultdict(set),
        'entity_to_quotes': defaultdict(list),
        'entity_to_speakers': defaultdict(set),
        'entity_to_codes': defaultdict(set),
        'all_speakers': set(),
        'all_entities': defaultdict(str),  # entity_name -> entity_type
        'all_quotes': []
    }
    
    # Process all interviews
    for interview_name, interview in data.get('interviews', {}).items():
        # Track speakers
        for speaker in interview.get('speakers', []):
            connections['all_speakers'].add(speaker['name'])
        
        # Track entities
        for entity in interview.get('interview_entities', []):
            connections['all_entities'][entity['name']] = entity['type']
        
        # Process quotes
        for i, quote in enumerate(interview.get('quotes', [])):
            quote_id = f"{interview_name}||{i}"  # Unique ID for each quote
            speaker_name = quote.get('speaker', {}).get('name', 'Unknown')
            
            # Store full quote data
            quote_data = {
                'id': quote_id,
                'text': quote['text'],
                'speaker': speaker_name,
                'interview': interview_name,
                'codes': [c.get('code_id', c.get('id', '')) for c in quote.get('codes', [])]
            }
            connections['all_quotes'].append(quote_data)
            
            # Connect speaker to quote
            connections['speaker_to_quotes'][speaker_name].append(quote_data)
            
            # Connect codes to everything
            for code in quote.get('codes', []):
                code_id = code.get('code_id', code.get('id', ''))
                if code_id:
                    # Code to quote
                    connections['code_to_quotes'][code_id].append(quote_data)
                    # Code to speaker
                    connections['code_to_speakers'][code_id].add(speaker_name)
                    # Speaker to code
                    connections['speaker_to_codes'][speaker_name].add(code_id)
        
        # Connect entities to quotes (based on context matching)
        for entity in interview.get('interview_entities', []):
            entity_name = entity['name']
            # Simple matching: check if entity is mentioned in quote
            for i, quote in enumerate(interview.get('quotes', [])):
                if entity_name.lower() in quote['text'].lower():
                    quote_id = f"{interview_name}||{i}"
                    speaker_name = quote.get('speaker', {}).get('name', 'Unknown')
                    
                    # Find the full quote data
                    quote_data = next((q for q in connections['all_quotes'] if q['id'] == quote_id), None)
                    if quote_data:
                        # Entity to quote
                        connections['entity_to_quotes'][entity_name].append(quote_data)
                        # Entity to speaker
                        connections['entity_to_speakers'][entity_name].add(speaker_name)
                        # Speaker to entity
                        connections['speaker_to_entities'][speaker_name].add(entity_name)
                        
                        # Entity to codes
                        for code_id in quote_data['codes']:
                            connections['entity_to_codes'][entity_name].add(code_id)
                            connections['code_to_entities'][code_id].add(entity_name)
    
    return connections

def navigate_to_code(code_id):
    """Navigate to Codes tab with specific code selected"""
    st.session_state.active_tab = 0
    st.session_state.selected_code = code_id

def navigate_to_speaker(speaker_name):
    """Navigate to Speakers tab with specific speaker selected"""
    st.session_state.active_tab = 1
    st.session_state.selected_speaker = speaker_name

def navigate_to_entity(entity_name):
    """Navigate to Entities tab with specific entity selected"""
    st.session_state.active_tab = 2
    st.session_state.selected_entity = entity_name

def display_codes_tab(data, connections):
    """Display the Codes tab"""
    st.header("📚 Codes")
    
    # Get all codes
    codes = data.get('taxonomy', {}).get('codes', [])
    if not codes:
        st.warning("No codes found in the data")
        return
    
    # Create code lookup dictionary
    code_dict = {code['id']: code for code in codes}
    code_options = ["Select a code..."] + [f"{code['id']}: {code['name']}" for code in codes]
    
    # Dropdown to select code
    selected_option = st.selectbox(
        "Select a Code",
        options=code_options,
        index=0 if not st.session_state.selected_code else next(
            (i for i, opt in enumerate(code_options) if opt.startswith(st.session_state.selected_code + ":")),
            0
        )
    )
    
    if selected_option != "Select a code...":
        code_id = selected_option.split(":")[0]
        st.session_state.selected_code = code_id
        code = code_dict[code_id]
        
        # Display code details
        st.markdown(f"### {code['name']}")
        if code.get('description'):
            st.write(f"**Description:** {code['description']}")
        if code.get('semantic_definition'):
            st.write(f"**Definition:** {code['semantic_definition']}")
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Quotes", len(connections['code_to_quotes'][code_id]))
        with col2:
            st.metric("Speakers", len(connections['code_to_speakers'][code_id]))
        with col3:
            st.metric("Entities", len(connections['code_to_entities'][code_id]))
        
        # Quotes with this code
        quotes = connections['code_to_quotes'][code_id]
        if quotes:
            st.markdown("### Quotes with this code")
            for quote in quotes[:20]:  # Limit to 20
                with st.expander(f"Quote from {quote['speaker']} ({quote['interview']})"):
                    st.write(quote['text'])
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button(f"→ {quote['speaker']}", key=f"speaker_{quote['id']}"):
                            navigate_to_speaker(quote['speaker'])
        
        # Speakers using this code
        speakers = connections['code_to_speakers'][code_id]
        if speakers:
            st.markdown("### Speakers using this code")
            cols = st.columns(5)
            for i, speaker in enumerate(speakers):
                with cols[i % 5]:
                    if st.button(speaker, key=f"speaker_link_{speaker}"):
                        navigate_to_speaker(speaker)
        
        # Entities related to this code
        entities = connections['code_to_entities'][code_id]
        if entities:
            st.markdown("### Related entities")
            cols = st.columns(5)
            for i, entity in enumerate(list(entities)[:20]):
                with cols[i % 5]:
                    if st.button(entity, key=f"entity_link_{entity}"):
                        navigate_to_entity(entity)

def display_speakers_tab(data, connections):
    """Display the Speakers tab"""
    st.header("👥 Speakers")
    
    speakers = sorted(list(connections['all_speakers']))
    if not speakers:
        st.warning("No speakers found in the data")
        return
    
    # Dropdown to select speaker
    speaker_options = ["Select a speaker..."] + speakers
    selected_speaker = st.selectbox(
        "Select a Speaker",
        options=speaker_options,
        index=speaker_options.index(st.session_state.selected_speaker) if st.session_state.selected_speaker in speaker_options else 0
    )
    
    if selected_speaker != "Select a speaker...":
        st.session_state.selected_speaker = selected_speaker
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Quotes", len(connections['speaker_to_quotes'][selected_speaker]))
        with col2:
            st.metric("Codes Used", len(connections['speaker_to_codes'][selected_speaker]))
        with col3:
            st.metric("Entities Mentioned", len(connections['speaker_to_entities'][selected_speaker]))
        
        # Quotes from this speaker
        quotes = connections['speaker_to_quotes'][selected_speaker]
        if quotes:
            st.markdown("### Quotes from this speaker")
            for quote in quotes[:20]:  # Limit to 20
                with st.expander(f"Quote from {quote['interview']}"):
                    st.write(quote['text'])
                    if quote['codes']:
                        st.write("**Codes:**")
                        cols = st.columns(min(len(quote['codes']), 5))
                        for i, code_id in enumerate(quote['codes']):
                            with cols[i % len(cols)]:
                                if st.button(code_id, key=f"code_{quote['id']}_{code_id}"):
                                    navigate_to_code(code_id)
        
        # All codes used by this speaker
        codes = connections['speaker_to_codes'][selected_speaker]
        if codes:
            st.markdown("### All codes used by this speaker")
            cols = st.columns(5)
            for i, code_id in enumerate(codes):
                with cols[i % 5]:
                    if st.button(code_id, key=f"all_codes_{code_id}"):
                        navigate_to_code(code_id)
        
        # Entities mentioned by this speaker
        entities = connections['speaker_to_entities'][selected_speaker]
        if entities:
            st.markdown("### Entities mentioned")
            cols = st.columns(5)
            for i, entity in enumerate(list(entities)[:20]):
                with cols[i % 5]:
                    if st.button(entity, key=f"entity_{entity}"):
                        navigate_to_entity(entity)

def display_entities_tab(data, connections):
    """Display the Entities tab"""
    st.header("🔗 Entities")
    
    # Group entities by type
    entities_by_type = defaultdict(list)
    for entity_name, entity_type in connections['all_entities'].items():
        entities_by_type[entity_type].append(entity_name)
    
    if not entities_by_type:
        st.warning("No entities found in the data")
        return
    
    # Create flat list for dropdown
    entity_options = ["Select an entity..."]
    for entity_type in sorted(entities_by_type.keys()):
        for entity_name in sorted(entities_by_type[entity_type]):
            entity_options.append(f"[{entity_type}] {entity_name}")
    
    # Dropdown to select entity
    selected_option = st.selectbox(
        "Select an Entity",
        options=entity_options,
        index=0 if not st.session_state.selected_entity else next(
            (i for i, opt in enumerate(entity_options) if st.session_state.selected_entity in opt),
            0
        )
    )
    
    if selected_option != "Select an entity...":
        # Extract entity name from selection
        entity_name = selected_option.split("] ", 1)[1] if "] " in selected_option else selected_option
        entity_type = selected_option.split("[")[1].split("]")[0] if "[" in selected_option else "Unknown"
        st.session_state.selected_entity = entity_name
        
        st.markdown(f"### {entity_name}")
        st.write(f"**Type:** {entity_type}")
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Quotes", len(connections['entity_to_quotes'][entity_name]))
        with col2:
            st.metric("Speakers", len(connections['entity_to_speakers'][entity_name]))
        with col3:
            st.metric("Related Codes", len(connections['entity_to_codes'][entity_name]))
        
        # Quotes mentioning this entity
        quotes = connections['entity_to_quotes'][entity_name]
        if quotes:
            st.markdown("### Quotes mentioning this entity")
            for quote in quotes[:10]:  # Limit to 10
                with st.expander(f"Quote from {quote['speaker']} ({quote['interview']})"):
                    st.write(quote['text'])
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button(f"→ {quote['speaker']}", key=f"entity_speaker_{quote['id']}"):
                            navigate_to_speaker(quote['speaker'])
                    with col2:
                        if quote['codes']:
                            st.write("**Codes:**")
                            cols = st.columns(min(len(quote['codes']), 4))
                            for i, code_id in enumerate(quote['codes']):
                                with cols[i % len(cols)]:
                                    if st.button(code_id, key=f"entity_code_{quote['id']}_{code_id}"):
                                        navigate_to_code(code_id)
        
        # Speakers who mentioned this entity
        speakers = connections['entity_to_speakers'][entity_name]
        if speakers:
            st.markdown("### Speakers who mentioned this entity")
            cols = st.columns(5)
            for i, speaker in enumerate(speakers):
                with cols[i % 5]:
                    if st.button(speaker, key=f"entity_speaker_link_{speaker}"):
                        navigate_to_speaker(speaker)
        
        # Codes related to this entity
        codes = connections['entity_to_codes'][entity_name]
        if codes:
            st.markdown("### Related codes")
            cols = st.columns(5)
            for i, code_id in enumerate(codes):
                with cols[i % 5]:
                    if st.button(code_id, key=f"entity_code_link_{code_id}"):
                        navigate_to_code(code_id)

def display_quotes_tab(data, connections):
    """Display the Quotes tab"""
    st.header("💬 Quotes")
    
    # Search box
    search_term = st.text_input("Search quotes", "")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        speaker_filter = st.selectbox(
            "Filter by speaker",
            ["All speakers"] + sorted(list(connections['all_speakers']))
        )
    with col2:
        # Get all unique codes
        all_codes = set()
        for quote in connections['all_quotes']:
            all_codes.update(quote['codes'])
        code_filter = st.selectbox(
            "Filter by code",
            ["All codes"] + sorted(list(all_codes))
        )
    
    # Filter quotes
    filtered_quotes = []
    for quote in connections['all_quotes']:
        # Apply search filter
        if search_term and search_term.lower() not in quote['text'].lower():
            continue
        # Apply speaker filter
        if speaker_filter != "All speakers" and quote['speaker'] != speaker_filter:
            continue
        # Apply code filter
        if code_filter != "All codes" and code_filter not in quote['codes']:
            continue
        filtered_quotes.append(quote)
    
    st.write(f"Showing {len(filtered_quotes)} quotes")
    
    # Display quotes
    for quote in filtered_quotes[:50]:  # Limit to 50
        with st.expander(f"{quote['speaker']} - {quote['interview']}"):
            st.write(quote['text'])
            
            # Clickable speaker
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(f"→ {quote['speaker']}", key=f"quote_speaker_{quote['id']}"):
                    navigate_to_speaker(quote['speaker'])
            
            # Clickable codes
            with col2:
                if quote['codes']:
                    st.write("**Codes:**")
                    cols = st.columns(min(len(quote['codes']), 5))
                    for i, code_id in enumerate(quote['codes']):
                        with cols[i % len(cols)]:
                            if st.button(code_id, key=f"quote_code_{quote['id']}_{code_id}"):
                                navigate_to_code(code_id)

def main():
    st.title("📊 Qualitative Coding Viewer")
    
    # Data selection
    output_dirs = []
    for d in Path('.').glob('output*'):
        if d.is_dir() and (d / "taxonomy.json").exists():
            output_dirs.append(d)
    
    if not output_dirs:
        st.error("No output directories found. Please run the extraction pipeline first.")
        return
    
    selected_dir = st.selectbox(
        "Select data source",
        options=[str(d) for d in output_dirs],
        index=len(output_dirs)-1 if output_dirs else 0
    )
    
    # Load data and build connections
    with st.spinner("Loading data..."):
        data = load_data(selected_dir)
        connections = build_connections(data)
    
    # Create tabs
    tabs = st.tabs(["📚 Codes", "👥 Speakers", "🔗 Entities", "💬 Quotes"])
    
    # Set active tab based on session state
    active_tab = st.session_state.active_tab
    
    with tabs[0]:
        display_codes_tab(data, connections)
    
    with tabs[1]:
        display_speakers_tab(data, connections)
    
    with tabs[2]:
        display_entities_tab(data, connections)
    
    with tabs[3]:
        display_quotes_tab(data, connections)

if __name__ == "__main__":
    main()
"""
Clean, simple viewer with expandable details and clickable links
"""

import streamlit as st
import json
from pathlib import Path
from collections import defaultdict

st.set_page_config(page_title="Qualitative Coding Browser", layout="wide")

# Custom CSS for clean styling
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-left: 20px;
        padding-right: 20px;
    }
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #e0e2e6;
        border-radius: 8px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_process_data(output_dir):
    """Load data and build all connections"""
    output_path = Path(output_dir)
    
    # Load taxonomy
    taxonomy = {}
    taxonomy_file = output_path / "taxonomy.json"
    if taxonomy_file.exists():
        with open(taxonomy_file, 'r', encoding='utf-8') as f:
            taxonomy = json.load(f)
    
    # Load all interviews
    interviews = {}
    interview_dir = output_path / "interviews"
    if interview_dir.exists():
        for file in interview_dir.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                interviews[file.stem] = json.load(f)
    
    # Build organized data structure
    organized_data = {
        'codes': {},
        'speakers': {},
        'entities': {},
        'quotes': []
    }
    
    # Process codes from taxonomy
    for code in taxonomy.get('codes', []):
        code_id = code.get('id', '')
        organized_data['codes'][code_id] = {
            'name': code.get('name', ''),
            'description': code.get('description', ''),
            'definition': code.get('semantic_definition', ''),
            'parent': code.get('parent_id'),
            'quotes': [],
            'speakers': set(),
            'entities': set()
        }
    
    # Process interviews
    quote_counter = 0
    for interview_name, interview in interviews.items():
        # Process speakers
        for speaker in interview.get('speakers', []):
            speaker_name = speaker['name']
            if speaker_name not in organized_data['speakers']:
                organized_data['speakers'][speaker_name] = {
                    'quotes': [],
                    'codes': set(),
                    'entities': set(),
                    'interviews': set()
                }
            organized_data['speakers'][speaker_name]['interviews'].add(interview_name)
        
        # Process entities
        for entity in interview.get('interview_entities', []):
            entity_name = entity['name']
            if entity_name not in organized_data['entities']:
                organized_data['entities'][entity_name] = {
                    'type': entity.get('type', 'Unknown'),
                    'quotes': [],
                    'codes': set(),
                    'speakers': set(),
                    'mentions': 0
                }
            organized_data['entities'][entity_name]['mentions'] += entity.get('mention_count', 1)
        
        # Process quotes
        for quote in interview.get('quotes', []):
            quote_id = f"Q{quote_counter:04d}"
            quote_counter += 1
            
            speaker_name = quote.get('speaker', {}).get('name', 'Unknown')
            
            # Create clean quote object
            clean_quote = {
                'id': quote_id,
                'text': quote['text'],
                'speaker': speaker_name,
                'interview': interview_name,
                'codes': []
            }
            
            # Process codes for this quote
            for code in quote.get('codes', []):
                # Try different field names for code ID
                code_id = code.get('code_id') or code.get('id') or code.get('code', '')
                if code_id and code_id in organized_data['codes']:
                    clean_quote['codes'].append(code_id)
                    organized_data['codes'][code_id]['quotes'].append(clean_quote)
                    organized_data['codes'][code_id]['speakers'].add(speaker_name)
                    organized_data['speakers'][speaker_name]['codes'].add(code_id)
            
            # Add quote to speaker
            organized_data['speakers'][speaker_name]['quotes'].append(clean_quote)
            
            # Simple entity matching (check if entity name appears in quote text)
            for entity_name in organized_data['entities'].keys():
                if entity_name.lower() in quote['text'].lower():
                    organized_data['entities'][entity_name]['quotes'].append(clean_quote)
                    organized_data['entities'][entity_name]['speakers'].add(speaker_name)
                    organized_data['speakers'][speaker_name]['entities'].add(entity_name)
                    # Link entity to codes
                    for code_id in clean_quote['codes']:
                        organized_data['entities'][entity_name]['codes'].add(code_id)
                        organized_data['codes'][code_id]['entities'].add(entity_name)
            
            organized_data['quotes'].append(clean_quote)
    
    return organized_data

def display_codes_page(data):
    """Display codes in a clean, browsable format"""
    st.header("📚 Codes")
    
    codes = data['codes']
    if not codes:
        st.warning("No codes found")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Codes", len(codes))
    with col2:
        total_coded_quotes = sum(len(c['quotes']) for c in codes.values())
        st.metric("Coded Quotes", total_coded_quotes)
    with col3:
        codes_with_quotes = sum(1 for c in codes.values() if c['quotes'])
        st.metric("Active Codes", codes_with_quotes)
    
    st.markdown("---")
    
    # Display each code as an expandable section
    for code_id, code_data in sorted(codes.items()):
        num_quotes = len(code_data['quotes'])
        num_speakers = len(code_data['speakers'])
        
        # Create expander with summary info
        with st.expander(f"**{code_id}: {code_data['name']}** — {num_quotes} quotes, {num_speakers} speakers"):
            # Code details
            if code_data['description']:
                st.markdown(f"**Description:** {code_data['description']}")
            if code_data['definition']:
                st.markdown(f"**Definition:** {code_data['definition']}")
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Quotes", num_quotes)
            with col2:
                st.metric("Speakers", num_speakers)
            with col3:
                st.metric("Entities", len(code_data['entities']))
            
            # Quotes section
            if code_data['quotes']:
                st.markdown("### Quotes with this code")
                for i, quote in enumerate(code_data['quotes'][:10], 1):  # Show first 10
                    st.markdown(f"**{i}. {quote['speaker']}** ({quote['interview']})")
                    st.markdown(f"> {quote['text'][:300]}{'...' if len(quote['text']) > 300 else ''}")
                    if len(quote['text']) > 300:
                        if st.button(f"Read full quote", key=f"full_{code_id}_{quote['id']}"):
                            st.write(quote['text'])
                    st.markdown("")
                
                if len(code_data['quotes']) > 10:
                    st.info(f"Showing 10 of {len(code_data['quotes'])} quotes")
            
            # Speakers section
            if code_data['speakers']:
                st.markdown("### Speakers using this code")
                st.write(", ".join(sorted(code_data['speakers'])))
            
            # Entities section
            if code_data['entities']:
                st.markdown("### Related entities")
                st.write(", ".join(sorted(code_data['entities'])))

def display_speakers_page(data):
    """Display speakers in a clean, browsable format"""
    st.header("👥 Speakers")
    
    speakers = data['speakers']
    if not speakers:
        st.warning("No speakers found")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Speakers", len(speakers))
    with col2:
        total_quotes = sum(len(s['quotes']) for s in speakers.values())
        st.metric("Total Quotes", total_quotes)
    with col3:
        total_interviews = len(set(i for s in speakers.values() for i in s['interviews']))
        st.metric("Interviews", total_interviews)
    
    st.markdown("---")
    
    # Display each speaker as an expandable section
    for speaker_name, speaker_data in sorted(speakers.items()):
        num_quotes = len(speaker_data['quotes'])
        num_codes = len(speaker_data['codes'])
        
        with st.expander(f"**{speaker_name}** — {num_quotes} quotes, {num_codes} codes"):
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Quotes", num_quotes)
            with col2:
                st.metric("Codes Used", num_codes)
            with col3:
                st.metric("Entities", len(speaker_data['entities']))
            with col4:
                st.metric("Interviews", len(speaker_data['interviews']))
            
            # Quotes section
            if speaker_data['quotes']:
                st.markdown("### Quotes from this speaker")
                for i, quote in enumerate(speaker_data['quotes'][:10], 1):
                    st.markdown(f"**Quote {i}** ({quote['interview']})")
                    st.markdown(f"> {quote['text'][:300]}{'...' if len(quote['text']) > 300 else ''}")
                    if quote['codes']:
                        st.markdown(f"**Codes:** {', '.join(quote['codes'])}")
                    st.markdown("")
                
                if len(speaker_data['quotes']) > 10:
                    st.info(f"Showing 10 of {len(speaker_data['quotes'])} quotes")
            
            # Codes section
            if speaker_data['codes']:
                st.markdown("### Codes used by this speaker")
                # Display codes with their names if available
                code_list = []
                for code_id in sorted(speaker_data['codes']):
                    if code_id in data['codes']:
                        code_list.append(f"{code_id}: {data['codes'][code_id]['name']}")
                    else:
                        code_list.append(code_id)
                for code in code_list:
                    st.write(f"• {code}")
            
            # Entities section
            if speaker_data['entities']:
                st.markdown("### Entities mentioned")
                st.write(", ".join(sorted(speaker_data['entities'])))

def display_entities_page(data):
    """Display entities in a clean, browsable format"""
    st.header("🔗 Entities")
    
    entities = data['entities']
    if not entities:
        st.warning("No entities found")
        return
    
    # Group entities by type
    entities_by_type = defaultdict(list)
    for entity_name, entity_data in entities.items():
        entities_by_type[entity_data['type']].append((entity_name, entity_data))
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Entities", len(entities))
    with col2:
        st.metric("Entity Types", len(entities_by_type))
    with col3:
        total_mentions = sum(e['mentions'] for e in entities.values())
        st.metric("Total Mentions", total_mentions)
    
    st.markdown("---")
    
    # Display entities grouped by type
    for entity_type in sorted(entities_by_type.keys()):
        st.subheader(f"{entity_type} ({len(entities_by_type[entity_type])} entities)")
        
        for entity_name, entity_data in sorted(entities_by_type[entity_type]):
            num_quotes = len(entity_data['quotes'])
            num_mentions = entity_data['mentions']
            
            with st.expander(f"**{entity_name}** — {num_mentions} mentions, {num_quotes} quotes"):
                # Statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Mentions", num_mentions)
                with col2:
                    st.metric("Quotes", num_quotes)
                with col3:
                    st.metric("Speakers", len(entity_data['speakers']))
                with col4:
                    st.metric("Codes", len(entity_data['codes']))
                
                # Quotes section
                if entity_data['quotes']:
                    st.markdown("### Quotes mentioning this entity")
                    for i, quote in enumerate(entity_data['quotes'][:5], 1):
                        st.markdown(f"**{quote['speaker']}** ({quote['interview']})")
                        st.markdown(f"> {quote['text'][:300]}{'...' if len(quote['text']) > 300 else ''}")
                        st.markdown("")
                    
                    if len(entity_data['quotes']) > 5:
                        st.info(f"Showing 5 of {len(entity_data['quotes'])} quotes")
                
                # Related codes
                if entity_data['codes']:
                    st.markdown("### Related codes")
                    code_list = []
                    for code_id in sorted(entity_data['codes']):
                        if code_id in data['codes']:
                            code_list.append(f"{code_id}: {data['codes'][code_id]['name']}")
                        else:
                            code_list.append(code_id)
                    for code in code_list:
                        st.write(f"• {code}")
                
                # Speakers
                if entity_data['speakers']:
                    st.markdown("### Mentioned by")
                    st.write(", ".join(sorted(entity_data['speakers'])))

def display_quotes_page(data):
    """Display searchable quotes"""
    st.header("💬 All Quotes")
    
    quotes = data['quotes']
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("Search quotes", "")
    with col2:
        st.metric("Total Quotes", len(quotes))
    
    # Filter quotes
    if search:
        filtered_quotes = [q for q in quotes if search.lower() in q['text'].lower()]
        st.write(f"Found {len(filtered_quotes)} matching quotes")
    else:
        filtered_quotes = quotes
    
    # Display quotes
    for quote in filtered_quotes[:50]:  # Show max 50
        with st.expander(f"{quote['speaker']} - {quote['interview'][:50]}"):
            st.write(quote['text'])
            if quote['codes']:
                st.markdown("**Codes:**")
                for code_id in quote['codes']:
                    if code_id in data['codes']:
                        st.write(f"• {code_id}: {data['codes'][code_id]['name']}")
                    else:
                        st.write(f"• {code_id}")
    
    if len(filtered_quotes) > 50:
        st.info(f"Showing 50 of {len(filtered_quotes)} quotes")

def main():
    st.title("📊 Qualitative Coding Browser")
    
    # Data selection
    output_dirs = []
    for d in Path('.').glob('output*'):
        if d.is_dir() and (d / "taxonomy.json").exists():
            output_dirs.append(d)
    
    if not output_dirs:
        st.error("No output directories found")
        return
    
    selected_dir = st.selectbox(
        "Select data source",
        options=[str(d) for d in output_dirs]
    )
    
    # Load and process data
    data = load_and_process_data(selected_dir)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Codes", "👥 Speakers", "🔗 Entities", "💬 Quotes"])
    
    with tab1:
        display_codes_page(data)
    
    with tab2:
        display_speakers_page(data)
    
    with tab3:
        display_entities_page(data)
    
    with tab4:
        display_quotes_page(data)

if __name__ == "__main__":
    main()
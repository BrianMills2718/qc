"""
Modular view components for extraction viewer
Each function is a self-contained component that can be added to the main app
"""
import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go


def show_overview_metrics(data):
    """Display overview metrics in columns"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Codes", len(data.taxonomy.get('codes', [])))
        st.metric("Hierarchy Depth", data.taxonomy.get('hierarchy_depth', 0))
    
    with col2:
        total_quotes = len(data.get_all_quotes())
        st.metric("Total Quotes", total_quotes)
        st.metric("Interviews", len(data.interviews))
    
    with col3:
        st.metric("Entity Types", len(data.entity_schema.get('entity_types', [])))
        st.metric("Relationship Types", len(data.entity_schema.get('relationship_types', [])))
    
    with col4:
        st.metric("Speaker Properties", len(data.speaker_schema.get('properties', [])))
        avg_quotes = total_quotes / len(data.interviews) if data.interviews else 0
        st.metric("Avg Quotes/Interview", f"{avg_quotes:.1f}")


def show_code_hierarchy(data):
    """Display hierarchical code structure"""
    st.subheader("📊 Code Taxonomy Hierarchy")
    
    hierarchy = data.get_codes_hierarchy()
    
    # Display by level
    for level in sorted(hierarchy.keys()):
        with st.expander(f"Level {level} Codes ({len(hierarchy[level])} codes)", expanded=(level==0)):
            for code in hierarchy[level]:
                # Indentation based on level
                indent = "　" * level * 2
                
                # Show code with details
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"{indent}**[{code['id']}]** {code['name']}")
                    st.caption(f"{indent}{code['description']}")
                with col2:
                    quotes = data.get_quotes_by_code(code['id'])
                    st.metric("Quotes", len(quotes), label_visibility="collapsed")


def show_code_frequency(data):
    """Display code frequency analysis"""
    st.subheader("📈 Code Usage Frequency")
    
    df = data.get_code_frequency()
    
    if not df.empty:
        # Bar chart
        fig = px.bar(df, x='Frequency', y='Code Name', orientation='h',
                     color='Level', title='Code Application Frequency',
                     hover_data=['Code ID'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        with st.expander("View Frequency Table"):
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No coded quotes found")


def show_quotes_explorer(data):
    """Interactive quote explorer with filters"""
    st.subheader("🔍 Quote Explorer")
    
    all_quotes = data.get_all_quotes()
    
    if not all_quotes:
        st.info("No quotes found")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Code filter
        all_codes = [code['id'] for code in data.taxonomy.get('codes', [])]
        selected_code = st.selectbox(
            "Filter by Code",
            ["All"] + all_codes,
            format_func=lambda x: x if x == "All" else f"{x} - {data.get_code_by_id(x)['name']}" if data.get_code_by_id(x) else x
        )
    
    with col2:
        # Interview filter
        interview_ids = list(data.interviews.keys())
        selected_interview = st.selectbox(
            "Filter by Interview",
            ["All"] + interview_ids
        )
    
    with col3:
        # Speaker filter
        all_speakers = list(set(q.get('speaker', {}).get('name', 'Unknown') 
                              for q in all_quotes if 'speaker' in q))
        selected_speaker = st.selectbox(
            "Filter by Speaker",
            ["All"] + sorted(all_speakers)
        )
    
    # Apply filters
    filtered_quotes = all_quotes
    
    if selected_code != "All":
        filtered_quotes = [q for q in filtered_quotes if selected_code in q.get('code_ids', [])]
    
    if selected_interview != "All":
        filtered_quotes = [q for q in filtered_quotes if q.get('interview_id') == selected_interview]
    
    if selected_speaker != "All":
        filtered_quotes = [q for q in filtered_quotes if q.get('speaker', {}).get('name') == selected_speaker]
    
    # Display quotes
    st.write(f"Showing {len(filtered_quotes)} quotes")
    
    for i, quote in enumerate(filtered_quotes[:50]):  # Limit to 50 for performance
        with st.container():
            # Quote header
            col1, col2 = st.columns([3, 1])
            with col1:
                speaker_name = quote.get('speaker', {}).get('name', 'Unknown')
                st.markdown(f"**{speaker_name}** ({quote.get('interview_id', 'Unknown')})")
            with col2:
                location = f"¶{quote.get('line_start', '?')}" if quote.get('line_start') else ""
                st.caption(location)
            
            # Quote text
            st.write(quote.get('text', ''))
            
            # Codes
            code_labels = []
            for code_id in quote.get('code_ids', []):
                code = data.get_code_by_id(code_id)
                if code:
                    code_labels.append(f"`{code['name']}`")
            if code_labels:
                st.markdown("Codes: " + " ".join(code_labels))
            
            st.divider()
    
    if len(filtered_quotes) > 50:
        st.info(f"Showing first 50 of {len(filtered_quotes)} quotes")


def show_entity_network(data):
    """Display entity and relationship network"""
    st.subheader("🔗 Entity Network")
    
    # Collect all entities and relationships
    entities = []
    relationships = []
    
    for interview_id, interview in data.interviews.items():
        for entity in interview.get('interview_entities', []):
            entities.append({
                'name': entity['name'],
                'type': entity['type'],
                'interview': interview_id
            })
        
        for rel in interview.get('interview_relationships', []):
            relationships.append({
                'source': rel['source_entity'],
                'target': rel['target_entity'],
                'type': rel['relationship_type']
            })
    
    if not entities:
        st.info("No entities found")
        return
    
    # Summary metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Entities", len(entities))
    with col2:
        st.metric("Total Relationships", len(relationships))
    
    # Entity type distribution
    entity_df = pd.DataFrame(entities)
    type_counts = entity_df['type'].value_counts()
    
    fig = px.pie(values=type_counts.values, names=type_counts.index, 
                 title="Entity Type Distribution")
    st.plotly_chart(fig, use_container_width=True)
    
    # Top entities table
    with st.expander("Top Entities by Mention Count"):
        entity_counts = entity_df['name'].value_counts().head(20)
        st.dataframe(pd.DataFrame({
            'Entity': entity_counts.index,
            'Mentions': entity_counts.values
        }), use_container_width=True)


def show_speaker_analysis(data):
    """Display speaker analysis"""
    st.subheader("👥 Speaker Analysis")
    
    speaker_df = data.get_speaker_summary()
    
    if speaker_df.empty:
        st.info("No speaker data found")
        return
    
    # Speaker properties from schema
    st.write("**Discovered Speaker Properties:**")
    for prop in data.speaker_schema.get('properties', []):
        st.write(f"- **{prop['name']}**: {prop.get('description', 'No description')}")
        if prop.get('example_values'):
            st.caption(f"  Examples: {', '.join(str(v) for v in prop['example_values'][:3])}")
    
    # Speaker distribution
    if 'name' in speaker_df.columns:
        speaker_counts = speaker_df['name'].value_counts()
        
        fig = px.bar(x=speaker_counts.values, y=speaker_counts.index,
                     orientation='h', title="Quotes by Speaker")
        st.plotly_chart(fig, use_container_width=True)


def show_raw_data(data):
    """Display raw JSON data for debugging"""
    st.subheader("🔧 Raw Data Inspector")
    
    data_type = st.selectbox(
        "Select data to inspect",
        ["Taxonomy", "Speaker Schema", "Entity Schema", "Interview (select)", "Quote Sample"]
    )
    
    if data_type == "Taxonomy":
        st.json(data.taxonomy)
    elif data_type == "Speaker Schema":
        st.json(data.speaker_schema)
    elif data_type == "Entity Schema":
        st.json(data.entity_schema)
    elif data_type == "Interview (select)":
        if data.interviews:
            selected = st.selectbox("Select interview", list(data.interviews.keys()))
            st.json(data.interviews[selected])
    elif data_type == "Quote Sample":
        quotes = data.get_all_quotes()[:5]
        st.json(quotes)
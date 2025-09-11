"""
Example of how to add new viewer components

To add a new view:
1. Create a function that takes 'data' parameter
2. Add it to AVAILABLE_VIEWS in streamlit_viewer.py
3. Add it to ACTIVE_VIEWS to enable it
"""

import streamlit as st
import pandas as pd


def show_code_connections(data):
    """
    Example: Show which codes frequently appear together
    This demonstrates how to add a new analysis view
    """
    st.subheader("🔗 Code Co-occurrence Analysis")
    
    # Find codes that appear together
    co_occurrences = {}
    
    for quote in data.get_all_quotes():
        codes = quote.get('code_ids', [])
        # Check pairs of codes
        for i, code1 in enumerate(codes):
            for code2 in codes[i+1:]:
                pair = tuple(sorted([code1, code2]))
                co_occurrences[pair] = co_occurrences.get(pair, 0) + 1
    
    if not co_occurrences:
        st.info("No code co-occurrences found")
        return
    
    # Display top co-occurring codes
    top_pairs = sorted(co_occurrences.items(), key=lambda x: x[1], reverse=True)[:10]
    
    data_for_df = []
    for (code1, code2), count in top_pairs:
        code1_name = data.get_code_by_id(code1)['name'] if data.get_code_by_id(code1) else code1
        code2_name = data.get_code_by_id(code2)['name'] if data.get_code_by_id(code2) else code2
        data_for_df.append({
            'Code 1': code1_name,
            'Code 2': code2_name,
            'Co-occurrences': count
        })
    
    df = pd.DataFrame(data_for_df)
    st.dataframe(df, use_container_width=True)


def show_interview_comparison(data):
    """
    Example: Compare code usage across interviews
    """
    st.subheader("📊 Interview Code Comparison")
    
    # Build matrix of interviews vs codes
    interview_codes = {}
    
    for interview_id, interview in data.interviews.items():
        code_counts = {}
        for quote in interview.get('quotes', []):
            for code_id in quote.get('code_ids', []):
                code_counts[code_id] = code_counts.get(code_id, 0) + 1
        interview_codes[interview_id] = code_counts
    
    if not interview_codes:
        st.info("No interview data found")
        return
    
    # Create comparison table
    all_codes = set()
    for counts in interview_codes.values():
        all_codes.update(counts.keys())
    
    comparison_data = []
    for interview_id, counts in interview_codes.items():
        row = {'Interview': interview_id[:30]}  # Truncate long names
        for code_id in sorted(all_codes):
            code = data.get_code_by_id(code_id)
            code_name = code['name'][:20] if code else code_id
            row[code_name] = counts.get(code_id, 0)
        comparison_data.append(row)
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True)


def show_quote_search(data):
    """
    Example: Full-text search in quotes
    """
    st.subheader("🔍 Quote Search")
    
    search_term = st.text_input("Search quotes", placeholder="Enter search term...")
    
    if search_term:
        matching_quotes = []
        for quote in data.get_all_quotes():
            if search_term.lower() in quote.get('text', '').lower():
                matching_quotes.append(quote)
        
        st.write(f"Found {len(matching_quotes)} matching quotes")
        
        for quote in matching_quotes[:20]:  # Show first 20
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    # Highlight search term
                    text = quote.get('text', '')
                    highlighted = text.replace(
                        search_term, 
                        f"**{search_term}**"
                    )
                    st.markdown(highlighted)
                with col2:
                    st.caption(quote.get('interview_id', 'Unknown'))
                    speaker = quote.get('speaker', {}).get('name', 'Unknown')
                    st.caption(f"Speaker: {speaker}")
                
                # Show codes
                codes = []
                for code_id in quote.get('code_ids', []):
                    code = data.get_code_by_id(code_id)
                    if code:
                        codes.append(code['name'])
                if codes:
                    st.caption(f"Codes: {', '.join(codes)}")
                
                st.divider()


# To use these components:
# 1. Import them in streamlit_viewer.py:
#    from viewer_components_example import show_code_connections, show_interview_comparison, show_quote_search
#
# 2. Add to AVAILABLE_VIEWS:
#    "Code Connections": show_code_connections,
#    "Interview Comparison": show_interview_comparison,
#    "Quote Search": show_quote_search,
#
# 3. Add to ACTIVE_VIEWS to enable them
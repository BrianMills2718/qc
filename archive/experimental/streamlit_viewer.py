"""
Modular Streamlit viewer for qualitative coding extraction results

Run with: streamlit run streamlit_viewer.py

This app is designed for easy iteration:
- Each view is a separate function in viewer_components.py
- Add new views by creating new functions and adding them to AVAILABLE_VIEWS
- Comment out views you don't want in ACTIVE_VIEWS
- Reorder views by changing their position in ACTIVE_VIEWS
"""

import streamlit as st
from viewer_data_loader import DataLoader
from viewer_components import (
    show_overview_metrics,
    show_code_hierarchy,
    show_code_frequency,
    show_quotes_explorer,
    show_entity_network,
    show_speaker_analysis,
    show_raw_data
)

# Page configuration
st.set_page_config(
    page_title="Qualitative Coding Viewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define available views - add new components here
AVAILABLE_VIEWS = {
    "Overview": show_overview_metrics,
    "Code Hierarchy": show_code_hierarchy,
    "Code Frequency": show_code_frequency,
    "Quote Explorer": show_quotes_explorer,
    "Entity Network": show_entity_network,
    "Speaker Analysis": show_speaker_analysis,
    "Raw Data": show_raw_data,
}

# Define which views are active (comment out to disable)
ACTIVE_VIEWS = [
    "Overview",
    "Code Hierarchy", 
    "Code Frequency",
    "Quote Explorer",
    "Entity Network",
    "Speaker Analysis",
    "Raw Data"
]


def main():
    st.title("📊 Qualitative Coding Extraction Viewer")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Output directory selection
        output_dir = st.text_input(
            "Output Directory",
            value="output_production",
            help="Path to the extraction output directory"
        )
        
        # Refresh button
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        # Info
        st.divider()
        st.caption("💡 Tip: Modify viewer_components.py to add new views")
        st.caption("💡 Tip: This app auto-reloads when you save changes")
        
        # Show data status
        st.divider()
        st.subheader("Data Status")
    
    # Load data (cached for performance)
    @st.cache_data
    def load_extraction_data(directory):
        loader = DataLoader(directory)
        return loader.load_all_data()
    
    try:
        data = load_extraction_data(output_dir)
        
        # Check if data was loaded
        if not data.taxonomy:
            st.error(f"No taxonomy.json found in {output_dir}")
            st.info("Make sure you've run the extraction pipeline first")
            return
        
        # Show data status in sidebar
        with st.sidebar:
            st.success(f"✅ Loaded {len(data.interviews)} interviews")
            st.info(f"📚 {len(data.taxonomy.get('codes', []))} codes")
            st.info(f"💬 {len(data.get_all_quotes())} quotes")
        
        # Create tabs for different views
        tabs = st.tabs([f"📊 {name}" for name in ACTIVE_VIEWS if name in AVAILABLE_VIEWS])
        
        # Display each view in its tab
        for tab, view_name in zip(tabs, [name for name in ACTIVE_VIEWS if name in AVAILABLE_VIEWS]):
            with tab:
                try:
                    AVAILABLE_VIEWS[view_name](data)
                except Exception as e:
                    st.error(f"Error in {view_name}: {str(e)}")
                    with st.expander("Show error details"):
                        st.exception(e)
        
    except Exception as e:
        st.error(f"Failed to load data from {output_dir}")
        st.exception(e)
        st.info("Check that the extraction pipeline has been run and output files exist")


# Add custom CSS for better styling
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .stExpander {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
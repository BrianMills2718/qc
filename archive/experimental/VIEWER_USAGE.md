# Modular Viewer System for Qualitative Coding Results

## Quick Start

```bash
streamlit run streamlit_viewer.py
```

The viewer will automatically load data from `output_production/` directory.

## Architecture

The viewer uses a **modular component architecture** for easy iteration:

```
streamlit_viewer.py         # Main app - just orchestrates components
viewer_data_loader.py       # Data loading and helper methods
viewer_components.py        # Individual view components (functions)
viewer_components_example.py # Example new components
```

## How to Add New Views

### 1. Create a Component Function

Add a new function to `viewer_components.py` (or create your own file):

```python
def show_my_new_view(data):
    """My new analysis view"""
    st.subheader("📊 My New Analysis")
    
    # Your analysis code here
    # data is an ExtractionData object with helpers:
    # - data.get_all_quotes()
    # - data.get_code_by_id(code_id)
    # - data.get_quotes_by_code(code_id)
    # - data.get_code_frequency()
    # etc.
    
    st.write("Your visualization here")
```

### 2. Register the Component

In `streamlit_viewer.py`, add your function to `AVAILABLE_VIEWS`:

```python
AVAILABLE_VIEWS = {
    "Overview": show_overview_metrics,
    "My New View": show_my_new_view,  # Add here
    # ... other views
}
```

### 3. Enable the View

Add it to `ACTIVE_VIEWS` to make it appear:

```python
ACTIVE_VIEWS = [
    "Overview",
    "My New View",  # Add here
    # ... other views
]
```

That's it! The app will auto-reload when you save.

## Data Access Helpers

The `ExtractionData` class provides these helper methods:

```python
# Get specific code details
code = data.get_code_by_id("AI_CHALLENGES")

# Get codes organized by hierarchy level
hierarchy = data.get_codes_hierarchy()  # {0: [...], 1: [...], 2: [...]}

# Get all quotes
quotes = data.get_all_quotes()

# Get quotes for a specific code
quotes = data.get_quotes_by_code("AI_CHALLENGES")

# Get code frequency as DataFrame
df = data.get_code_frequency()

# Get speaker summary as DataFrame
df = data.get_speaker_summary()

# Get entity summary as DataFrame
df = data.get_entity_summary()

# Access raw data
data.taxonomy          # Code taxonomy
data.speaker_schema    # Speaker properties
data.entity_schema     # Entity types
data.interviews        # Dict of interview_id -> interview data
```

## Example Components

See `viewer_components_example.py` for three example components:
- **Code Connections**: Shows which codes frequently appear together
- **Interview Comparison**: Compares code usage across interviews
- **Quote Search**: Full-text search in quotes

## Tips for Development

1. **Hot Reload**: Streamlit automatically reloads when you save changes
2. **Caching**: Data is cached with `@st.cache_data` for performance
3. **Error Handling**: Each component has its own error handling
4. **Modular**: Components are independent - disable/enable as needed

## Component Ideas

Here are some views you might want to add:

- **Timeline View**: Show quotes chronologically
- **Speaker Network**: Visualize speaker relationships
- **Code Evolution**: Track how codes are applied across interviews
- **Sentiment Analysis**: Analyze tone of quotes per code
- **Export View**: Generate reports in different formats
- **Validation View**: Check for coding consistency
- **Statistics Dashboard**: Detailed statistical analysis
- **Word Cloud**: Visualize most common terms per code

## Troubleshooting

**No data showing?**
- Check that extraction pipeline has been run
- Verify files exist in `output_production/`
- Use the "Raw Data" view to inspect what was loaded

**Component not appearing?**
- Make sure it's added to both `AVAILABLE_VIEWS` and `ACTIVE_VIEWS`
- Check for Python syntax errors in your component function

**Performance issues?**
- Limit displayed items (e.g., show first 50 quotes)
- Use Streamlit's caching decorators
- Consider pagination for large datasets

## Next Steps

1. Run the viewer: `streamlit run streamlit_viewer.py`
2. Explore your extraction results
3. Add custom analysis views as needed
4. Iterate quickly without rewriting the whole app!
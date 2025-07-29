# LLM-Native Qualitative Coding Documentation

This GitHub Pages site provides comprehensive documentation for the LLM-Native Qualitative Coding system.

## Pages

- **index.html** - Main documentation with methodology, terminology, and results
- **visualizations.html** - Interactive charts and data visualizations
- **style.css** - Styling for all pages
- **script.js** - JavaScript for interactivity

## Setting up GitHub Pages

1. Push this repository to GitHub
2. Go to Settings → Pages
3. Select "Deploy from a branch"
4. Choose "main" branch and "/docs" folder
5. Save and wait for deployment

Your documentation will be available at:
`https://[username].github.io/qualitative_coding_clean/`

## Data Anonymization

Before publishing, run the anonymization script:

```bash
python anonymize_data.py --input output --output output_anonymized
```

This will create anonymized versions of all CSV files, replacing names with IDs like SPEAKER_001, ROLE_001, etc.

## Updating Results

To add new analysis results:

1. Run the analysis: `python run_full_ai_analysis.py`
2. Anonymize the output: `python anonymize_data.py`
3. Copy anonymized CSVs to `docs/data/`
4. Update the statistics in `index.html`
5. Push changes to GitHub

## Features

- **Responsive Design** - Works on desktop, tablet, and mobile
- **Interactive Navigation** - Smooth scrolling and active section highlighting
- **Copy Code Blocks** - Click any code block to copy its contents
- **Print-Friendly** - Optimized CSS for printing documentation
- **Data Tables** - Sortable columns for all data tables
- **Interactive Charts** - Visualizations using Chart.js

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## License

This documentation is part of the LLM-Native Qualitative Coding project.
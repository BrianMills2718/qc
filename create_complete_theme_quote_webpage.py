#!/usr/bin/env python3
"""
Enhanced Comprehensive Theme-Quote Analysis Webpage Generator
Creates HTML visualization showing ALL themes linked to ALL available quotes
"""

import csv
import json
import argparse
from pathlib import Path
import re

class CompleteThemeQuoteAnalyzer:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.all_quotes = []
        self.themes = []
        self.codes = []
        
    def extract_exemplar_quotes_from_theme_analysis(self):
        """Extract exemplar quotes from theme_analysis.csv for themes T1, T2, T3"""
        theme_analysis_path = self.data_dir / "theme_analysis.csv"
        
        if not theme_analysis_path.exists():
            print(f"Warning: {theme_analysis_path} not found")
            return []
        
        extracted_quotes = []
        
        with open(theme_analysis_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                theme_id = row['theme_id']
                theme_name = row['theme_name']
                
                # Extract exemplar quotes for this theme
                for i in range(1, 4):  # exemplar_quote_1, exemplar_quote_2, exemplar_quote_3
                    quote_key = f'exemplar_quote_{i}'
                    if quote_key in row and row[quote_key].strip():
                        quote_text = row[quote_key].strip()
                        
                        # Parse speaker and quote from format: "Speaker: 'Quote text' (Interview XXX)"
                        speaker_match = re.match(r'^([^:]+):\s*[\'"](.+?)[\'"](?:\s*\(Interview\s+(\d+)\))?', quote_text)
                        
                        if speaker_match:
                            speaker = speaker_match.group(1).strip()
                            quote = speaker_match.group(2).strip()
                            interview_num = speaker_match.group(3) if speaker_match.group(3) else "Unknown"
                            
                            extracted_quotes.append({
                                'quote_id': f'{theme_id}_EX{i}',
                                'text': quote,
                                'speaker': speaker,
                                'interview_id': f'INT_{interview_num.zfill(3)}' if interview_num != "Unknown" else "INT_Unknown",
                                'theme_ids': [theme_id],
                                'theme_name': theme_name,
                                'source': 'theme_analysis_exemplar',
                                'exemplar_index': i
                            })
        
        return extracted_quotes
    
    def load_formal_quotes(self):
        """Load formal quotes from quote_inventory.json or quotes.csv"""
        formal_quotes = []
        
        # Try quote_inventory.json first
        quote_inventory_path = self.data_dir / "quote_inventory.json"
        if quote_inventory_path.exists():
            with open(quote_inventory_path, 'r', encoding='utf-8') as f:
                formal_quotes_data = json.load(f)
                for quote in formal_quotes_data:
                    formal_quotes.append({
                        'quote_id': quote['quote_id'],
                        'text': quote['text'],
                        'speaker': quote['speaker'],
                        'interview_id': quote['interview_id'],
                        'theme_ids': quote['theme_ids'],
                        'code_ids': quote.get('code_ids', []),
                        'source': 'formal_extraction'
                    })
        else:
            # Fallback to quotes.csv
            quotes_path = self.data_dir / "quotes.csv"
            if quotes_path.exists():
                with open(quotes_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        formal_quotes.append({
                            'quote_id': row['quote_id'],
                            'text': row['text'],
                            'speaker': row['speaker'],
                            'interview_id': row['interview_id'],
                            'theme_ids': row['theme_ids'].split(';') if row['theme_ids'] else [],
                            'code_ids': row['code_ids'].split(';') if row.get('code_ids') else [],
                            'source': 'formal_extraction'
                        })
        
        return formal_quotes
    
    def load_themes(self):
        """Load themes data"""
        themes_path = self.data_dir / "themes.csv"
        themes = []
        
        if themes_path.exists():
            with open(themes_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    themes.append({
                        'id': row['theme_id'],
                        'name': row['name'],
                        'prevalence': float(row['prevalence']),
                        'confidence': float(row['confidence']),
                        'interview_count': int(row['interview_count'])
                    })
        
        return themes
    
    def load_codes(self):
        """Load codes data"""
        codes_path = self.data_dir / "codes.csv"
        codes = []
        
        if codes_path.exists():
            with open(codes_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    codes.append({
                        'id': row['code_id'],
                        'name': row['name'],
                        'definition': row['definition'],
                        'frequency': int(row['frequency']),
                        'theme_id': row['theme_id'],
                        'parent_code_id': row.get('parent_code_id', ''),
                        'hierarchy_level': int(row['hierarchy_level'])
                    })
        
        return codes
    
    def generate_complete_html(self, output_file: str):
        """Generate comprehensive HTML with ALL theme-quote linkages"""
        
        # Load all data
        exemplar_quotes = self.extract_exemplar_quotes_from_theme_analysis()
        formal_quotes = self.load_formal_quotes()
        self.themes = self.load_themes()
        self.codes = self.load_codes()
        
        # Combine all quotes
        self.all_quotes = exemplar_quotes + formal_quotes
        
        print(f"Loaded {len(exemplar_quotes)} exemplar quotes from theme analysis")
        print(f"Loaded {len(formal_quotes)} formal quotes")
        print(f"Total quotes: {len(self.all_quotes)}")
        
        # Group quotes by theme
        quotes_by_theme = {}
        for quote in self.all_quotes:
            for theme_id in quote['theme_ids']:
                if theme_id not in quotes_by_theme:
                    quotes_by_theme[theme_id] = []
                quotes_by_theme[theme_id].append(quote)
        
        # Generate HTML
        html_content = self._generate_html_template(quotes_by_theme)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Generated complete theme-quote analysis: {output_file}")
        
        # Print summary
        print("\nQuote Distribution by Theme:")
        for theme in self.themes:
            theme_quotes = quotes_by_theme.get(theme['id'], [])
            print(f"  {theme['id']}: {theme['name']} - {len(theme_quotes)} quotes")
    
    def _generate_html_template(self, quotes_by_theme):
        """Generate the complete HTML template"""
        
        # Create JavaScript data structure
        themes_js = json.dumps([{
            'id': theme['id'],
            'name': theme['name'],
            'prevalence': theme['prevalence'],
            'confidence': theme['confidence'],
            'interview_count': theme['interview_count'],
            'quote_count': len(quotes_by_theme.get(theme['id'], []))
        } for theme in self.themes], indent=2)
        
        quotes_js = json.dumps(self.all_quotes, indent=2)
        codes_js = json.dumps(self.codes, indent=2)
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complete Theme-Quote Analysis - AI Integration Research</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        :root {{
            --primary: #2563eb;
            --secondary: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --info: #06b6d4;
            --dark: #1f2937;
            --light: #f9fafb;
            --border: #e5e7eb;
            --quote-bg: #fef3c7;
            --quote-border: #f59e0b;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--dark);
            background: var(--light);
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 40px 0;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border-radius: 8px;
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 4px solid;
        }}

        .stat-card.themes {{ border-left-color: var(--primary); }}
        .stat-card.quotes {{ border-left-color: var(--warning); }}
        .stat-card.exemplar {{ border-left-color: var(--secondary); }}
        .stat-card.formal {{ border-left-color: var(--info); }}

        .stat-card .number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--dark);
            margin-bottom: 5px;
        }}

        .stat-card .label {{
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .theme-section {{
            background: white;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .theme-header {{
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            color: white;
            padding: 20px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .theme-header h2 {{
            font-size: 1.5rem;
            margin: 0;
        }}

        .theme-stats {{
            display: flex;
            gap: 20px;
            font-size: 0.9rem;
        }}

        .theme-stats span {{
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 20px;
        }}

        .theme-content {{
            padding: 25px;
        }}

        .theme-description {{
            background: var(--light);
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-style: italic;
        }}

        .quotes-grid {{
            display: grid;
            gap: 20px;
        }}

        .quote-card {{
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .quote-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}

        .quote-header {{
            background: var(--quote-bg);
            border-bottom: 1px solid var(--quote-border);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .quote-meta {{
            display: flex;
            gap: 15px;
            font-size: 0.9rem;
        }}

        .quote-source {{
            background: var(--primary);
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
        }}

        .quote-body {{
            padding: 20px;
        }}

        .quote-text {{
            font-size: 1.1rem;
            line-height: 1.8;
            margin-bottom: 15px;
            position: relative;
        }}

        .quote-text::before {{
            content: '"';
            font-size: 3rem;
            color: var(--quote-border);
            position: absolute;
            left: -15px;
            top: -10px;
            font-family: serif;
        }}

        .quote-text::after {{
            content: '"';
            font-size: 3rem;
            color: var(--quote-border);
            position: absolute;
            right: -10px;
            bottom: -20px;
            font-family: serif;
        }}

        .quote-footer {{
            background: var(--light);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .code-tags {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .code-tag {{
            background: var(--info);
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            text-decoration: none;
        }}

        .code-tag:hover {{
            background: #0891b2;
        }}

        .no-quotes {{
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 40px;
            background: var(--light);
            border-radius: 6px;
        }}

        .search-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .search-controls {{
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}

        .search-controls input,
        .search-controls select {{
            padding: 10px 15px;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 14px;
        }}

        .search-controls input {{
            flex: 1;
            min-width: 200px;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .theme-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
            
            .theme-stats {{
                flex-direction: column;
                gap: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1><i class="fas fa-link"></i> Complete Theme-Quote Analysis</h1>
            <div class="subtitle">AI Integration in Qualitative Research - ALL Themes Linked to ALL Quotes</div>
        </div>

        <!-- Statistics Overview -->
        <div class="stats-grid">
            <div class="stat-card themes">
                <div class="number" id="totalThemes">5</div>
                <div class="label">Total Themes</div>
            </div>
            <div class="stat-card quotes">
                <div class="number" id="totalQuotes">0</div>
                <div class="label">Total Quotes</div>
            </div>
            <div class="stat-card exemplar">
                <div class="number" id="exemplarQuotes">0</div>
                <div class="label">Exemplar Quotes</div>
            </div>
            <div class="stat-card formal">
                <div class="number" id="formalQuotes">0</div>
                <div class="label">Formal Quotes</div>
            </div>
        </div>

        <!-- Search and Filter Section -->
        <div class="search-section">
            <div class="search-controls">
                <input type="text" id="searchInput" placeholder="Search quotes by text, speaker, or theme...">
                <select id="themeFilter">
                    <option value="">All Themes</option>
                </select>
                <select id="sourceFilter">
                    <option value="">All Sources</option>
                    <option value="theme_analysis_exemplar">Exemplar Quotes</option>
                    <option value="formal_extraction">Formal Extractions</option>
                </select>
                <button id="clearFilters" style="background: var(--danger); color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer;">
                    <i class="fas fa-times"></i> Clear
                </button>
            </div>
        </div>

        <!-- Theme Sections -->
        <div id="themeSections">
            <!-- Theme sections will be populated here -->
        </div>
    </div>

    <script>
        // Data from analysis
        const themes = {themes_js};
        const quotes = {quotes_js};
        const codes = {codes_js};

        // Initialize the page
        document.addEventListener('DOMContentLoaded', function() {{
            updateStatistics();
            populateFilters();
            renderThemeSections();
            setupEventListeners();
        }});

        function updateStatistics() {{
            const exemplarCount = quotes.filter(q => q.source === 'theme_analysis_exemplar').length;
            const formalCount = quotes.filter(q => q.source === 'formal_extraction').length;
            
            document.getElementById('totalQuotes').textContent = quotes.length;
            document.getElementById('exemplarQuotes').textContent = exemplarCount;
            document.getElementById('formalQuotes').textContent = formalCount;
        }}

        function populateFilters() {{
            const themeFilter = document.getElementById('themeFilter');
            themes.forEach(theme => {{
                const option = document.createElement('option');
                option.value = theme.id;
                option.textContent = `${{theme.id}}: ${{theme.name}}`;
                themeFilter.appendChild(option);
            }});
        }}

        function renderThemeSections() {{
            const container = document.getElementById('themeSections');
            container.innerHTML = '';

            themes.forEach(theme => {{
                const themeQuotes = quotes.filter(quote => 
                    quote.theme_ids && quote.theme_ids.includes(theme.id)
                );

                const themeSection = createThemeSection(theme, themeQuotes);
                container.appendChild(themeSection);
            }});
        }}

        function createThemeSection(theme, themeQuotes) {{
            const section = document.createElement('div');
            section.className = 'theme-section';
            section.setAttribute('data-theme-id', theme.id);

            const prevalencePercent = Math.round(theme.prevalence * 100);
            
            section.innerHTML = `
                <div class="theme-header">
                    <h2><i class="fas fa-tag"></i> ${{theme.id}}: ${{theme.name}}</h2>
                    <div class="theme-stats">
                        <span><i class="fas fa-percentage"></i> ${{prevalencePercent}}% Prevalence</span>
                        <span><i class="fas fa-users"></i> ${{theme.interview_count}} Interviews</span>
                        <span><i class="fas fa-quote-left"></i> ${{themeQuotes.length}} Quotes</span>
                    </div>
                </div>
                <div class="theme-content">
                    <div class="quotes-grid" id="quotes-${{theme.id}}">
                        ${{themeQuotes.length === 0 ? 
                            '<div class="no-quotes"><i class="fas fa-info-circle"></i> No quotes available for this theme</div>' : 
                            themeQuotes.map(quote => createQuoteCard(quote)).join('')
                        }}
                    </div>
                </div>
            `;

            return section;
        }}

        function createQuoteCard(quote) {{
            const codes_for_quote = quote.code_ids ? quote.code_ids : [];
            const sourceLabel = quote.source === 'theme_analysis_exemplar' ? 'Exemplar' : 'Formal';
            const sourceIcon = quote.source === 'theme_analysis_exemplar' ? 'star' : 'search';

            return `
                <div class="quote-card" data-quote-id="${{quote.quote_id}}">
                    <div class="quote-header">
                        <div class="quote-meta">
                            <span><i class="fas fa-user"></i> ${{quote.speaker}}</span>
                            <span><i class="fas fa-file-alt"></i> ${{quote.interview_id}}</span>
                        </div>
                        <div class="quote-source">
                            <i class="fas fa-${{sourceIcon}}"></i> ${{sourceLabel}}
                        </div>
                    </div>
                    <div class="quote-body">
                        <div class="quote-text">${{quote.text}}</div>
                    </div>
                    <div class="quote-footer">
                        <div class="code-tags">
                            ${{codes_for_quote.map(code_id => 
                                `<a href="#" class="code-tag" data-code-id="${{code_id}}">${{code_id}}</a>`
                            ).join('')}}
                        </div>
                        <small style="color: #666;">Quote ID: ${{quote.quote_id}}</small>
                    </div>
                </div>
            `;
        }}

        function setupEventListeners() {{
            // Search functionality
            document.getElementById('searchInput').addEventListener('input', filterQuotes);
            document.getElementById('themeFilter').addEventListener('change', filterQuotes);
            document.getElementById('sourceFilter').addEventListener('change', filterQuotes);
            document.getElementById('clearFilters').addEventListener('click', clearFilters);
        }}

        function filterQuotes() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const selectedTheme = document.getElementById('themeFilter').value;
            const selectedSource = document.getElementById('sourceFilter').value;

            themes.forEach(theme => {{
                const themeSection = document.querySelector(`[data-theme-id="${{theme.id}}"]`);
                const quotesContainer = document.getElementById(`quotes-${{theme.id}}`);
                
                let filteredQuotes = quotes.filter(quote => 
                    quote.theme_ids && quote.theme_ids.includes(theme.id)
                );

                // Apply filters
                if (selectedTheme && selectedTheme !== theme.id) {{
                    themeSection.style.display = 'none';
                    return;
                }}

                if (selectedSource) {{
                    filteredQuotes = filteredQuotes.filter(quote => quote.source === selectedSource);
                }}

                if (searchTerm) {{
                    filteredQuotes = filteredQuotes.filter(quote => 
                        quote.text.toLowerCase().includes(searchTerm) ||
                        quote.speaker.toLowerCase().includes(searchTerm) ||
                        theme.name.toLowerCase().includes(searchTerm)
                    );
                }}

                // Show/hide theme section
                themeSection.style.display = filteredQuotes.length > 0 || !searchTerm ? 'block' : 'none';

                // Update quotes display
                quotesContainer.innerHTML = filteredQuotes.length === 0 ? 
                    '<div class="no-quotes"><i class="fas fa-search"></i> No quotes match the current filters</div>' :
                    filteredQuotes.map(quote => createQuoteCard(quote)).join('');
            }});
        }}

        function clearFilters() {{
            document.getElementById('searchInput').value = '';
            document.getElementById('themeFilter').value = '';
            document.getElementById('sourceFilter').value = '';
            filterQuotes();
        }}
    </script>
</body>
</html>'''

def main():
    parser = argparse.ArgumentParser(description='Generate complete theme-quote analysis webpage')
    parser.add_argument('--input', required=True, help='Input directory with analysis CSV files')
    parser.add_argument('--output', default='complete_theme_quote_analysis.html', help='Output HTML file')
    
    args = parser.parse_args()
    
    analyzer = CompleteThemeQuoteAnalyzer(args.input)
    analyzer.generate_complete_html(args.output)

if __name__ == "__main__":
    main()
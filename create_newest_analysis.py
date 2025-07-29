#!/usr/bin/env python3
"""
Create analysis using the NEWEST dataset (083101) with enhanced quote extraction
"""

import csv
import json
import re
from pathlib import Path

def create_newest_analysis():
    """Create comprehensive analysis using the newest dataset"""
    
    data_dir = Path("C:/Users/Brian/projects/qualitative_coding_clean/output/full_ai_analysis_20250729_083101")
    
    # Load themes
    themes = []
    with open(data_dir / "themes.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            themes.append({
                'id': row['theme_id'],
                'name': row['name'],
                'prevalence': float(row['prevalence']),
                'confidence': float(row['confidence']),
                'interview_count': int(row['interview_count'])
            })
    
    # Extract ALL exemplar quotes from theme_analysis.csv
    all_quotes = []
    with open(data_dir / "theme_analysis.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            theme_id = row['theme_id']
            theme_name = row['theme_name']
            
            # Extract all 3 exemplar quotes for this theme
            for i in range(1, 4):
                quote_key = f'exemplar_quote_{i}'
                if quote_key in row and row[quote_key].strip():
                    quote_text = row[quote_key].strip()
                    
                    # Parse speaker and quote from format: "Speaker: Quote text (Interview XXX)"
                    speaker_match = re.match(r'^([^:]+):\s*(.+?)(?:\s*\(Interview\s+(\d+)\))?$', quote_text)
                    
                    if speaker_match:
                        speaker = speaker_match.group(1).strip()
                        quote = speaker_match.group(2).strip()
                        interview_num = speaker_match.group(3) if speaker_match.group(3) else "Unknown"
                        
                        all_quotes.append({
                            'quote_id': f'{theme_id}_EX{i}',
                            'text': quote,
                            'speaker': speaker,
                            'interview_id': f'INT_{interview_num.zfill(3)}' if interview_num != "Unknown" else "INT_Unknown",
                            'theme_ids': [theme_id],
                            'theme_name': theme_name,
                            'source': 'exemplar',
                            'exemplar_index': i
                        })
    
    # Also load any working quotes from quote_inventory.json (excluding failed extractions)
    try:
        with open(data_dir / "quote_inventory.json", 'r', encoding='utf-8') as f:
            formal_quotes_data = json.load(f)
            for quote in formal_quotes_data:
                # Skip failed extractions
                if not quote['text'].startswith('[Quote extraction failed'):
                    all_quotes.append({
                        'quote_id': quote['quote_id'],
                        'text': quote['text'],
                        'speaker': quote.get('speaker_role', 'Unknown'),
                        'interview_id': quote['interview_id'],
                        'theme_ids': quote['theme_ids'],
                        'source': 'formal',
                        'confidence': quote.get('confidence', 0.0)
                    })
    except FileNotFoundError:
        pass
    
    # Load codes
    codes = []
    with open(data_dir / "codes.csv", 'r', encoding='utf-8') as f:
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
    
    print(f"Loaded {len(themes)} themes")
    print(f"Loaded {len(all_quotes)} quotes")
    print(f"Loaded {len(codes)} codes")
    
    # Group quotes by theme
    quotes_by_theme = {}
    for quote in all_quotes:
        for theme_id in quote['theme_ids']:
            if theme_id not in quotes_by_theme:
                quotes_by_theme[theme_id] = []
            quotes_by_theme[theme_id].append(quote)
    
    # Print quote distribution
    print("\nQuote Distribution by Theme:")
    for theme in themes:
        theme_quotes = quotes_by_theme.get(theme['id'], [])
        exemplar_count = len([q for q in theme_quotes if q['source'] == 'exemplar'])
        formal_count = len([q for q in theme_quotes if q['source'] == 'formal'])
        print(f"  {theme['id']}: {theme['name']} - {len(theme_quotes)} quotes ({exemplar_count} exemplar, {formal_count} formal)")
    
    # Generate HTML
    html_content = generate_html_template(themes, all_quotes, codes, quotes_by_theme)
    
    with open('newest_complete_analysis_083101.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nGenerated newest analysis: newest_complete_analysis_083101.html")
    return len(all_quotes)

def generate_html_template(themes, quotes, codes, quotes_by_theme):
    """Generate the complete HTML template with login page"""
    
    # Create JavaScript data
    themes_js = json.dumps([{
        'id': theme['id'],
        'name': theme['name'],
        'prevalence': theme['prevalence'],
        'confidence': theme['confidence'],
        'interview_count': theme['interview_count'],
        'quote_count': len(quotes_by_theme.get(theme['id'], []))
    } for theme in themes], indent=2)
    
    quotes_js = json.dumps(quotes, indent=2)
    codes_js = json.dumps(codes, indent=2)
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAND Corporation - Secure Research Portal</title>
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

        /* Login Page Styles */
        .login-container {{
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}

        .login-box {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }}

        .login-logo {{
            width: 120px;
            height: 60px;
            background: var(--primary);
            border-radius: 8px;
            margin: 0 auto 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: bold;
        }}

        .login-title {{
            color: var(--dark);
            margin-bottom: 10px;
            font-size: 24px;
        }}

        .login-subtitle {{
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }}

        .form-group {{
            margin-bottom: 20px;
            text-align: left;
        }}

        .form-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: var(--dark);
        }}

        .form-group input {{
            width: 100%;
            padding: 12px;
            border: 2px solid var(--border);
            border-radius: 6px;
            font-size: 16px;
            transition: border-color 0.3s;
        }}

        .form-group input:focus {{
            outline: none;
            border-color: var(--primary);
        }}

        .login-btn {{
            width: 100%;
            padding: 12px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.3s;
        }}

        .login-btn:hover {{
            background: #1d4ed8;
        }}

        .demo-note {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 6px;
            padding: 10px;
            margin-top: 15px;
            font-size: 12px;
            color: #1e40af;
        }}

        .login-footer {{
            margin-top: 20px;
            font-size: 12px;
            color: #666;
        }}

        /* Main Application Styles (hidden initially) */
        .main-app {{
            display: none;
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

        .header .meta {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 15px;
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
        .stat-card.codes {{ border-left-color: var(--secondary); }}
        .stat-card.quotes {{ border-left-color: var(--warning); }}
        .stat-card.interviews {{ border-left-color: var(--info); }}

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

        .no-quotes {{
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 40px;
            background: var(--light);
            border-radius: 6px;
        }}

        .logout-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--danger);
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            z-index: 1000;
        }}

        .logout-btn:hover {{
            background: #dc2626;
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
    <!-- Login Page -->
    <div id="loginPage" class="login-container">
        <div class="login-box">
            <div class="login-logo">
                <i class="fas fa-shield-alt"></i>
            </div>
            <h2 class="login-title">RAND Corporation</h2>
            <p class="login-subtitle">Secure Research Portal - Methods & AI Integration Analysis</p>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <button type="submit" class="login-btn">
                    <i class="fas fa-sign-in-alt"></i> Sign In
                </button>
            </form>
            
            <div class="demo-note">
                <i class="fas fa-info-circle"></i>
                <strong>Demo Access:</strong> Any username/password combination will work for this demonstration.
            </div>
            
            <div class="login-footer">
                © 2025 RAND Corporation. All rights reserved.<br>
                Secure research data portal - Authorized users only
            </div>
        </div>
    </div>

    <!-- Main Application (Hidden Initially) -->
    <div id="mainApp" class="main-app">
        <button id="logoutBtn" class="logout-btn">
            <i class="fas fa-sign-out-alt"></i> Logout
        </button>

        <div class="container">
            <!-- Header -->
            <div class="header">
                <h1><i class="fas fa-microscope"></i> Methods & AI Integration Analysis</h1>
                <div class="subtitle">Research Question: What are methods being used, what is important about methods, and how does AI fit into this?</div>
                <div class="meta">
                    Generated: July 29, 2025 08:31:01 | Processing Time: 321.0 seconds<br>
                    Dataset: 18 interviews, 103 codes, {len(quotes)} quotes with complete theme linkage
                </div>
            </div>

            <!-- Statistics Overview -->
            <div class="stats-grid">
                <div class="stat-card themes">
                    <div class="number">5</div>
                    <div class="label">Research Themes</div>
                </div>
                <div class="stat-card codes">
                    <div class="number">103</div>
                    <div class="label">Total Codes</div>
                </div>
                <div class="stat-card quotes">
                    <div class="number">{len(quotes)}</div>
                    <div class="label">Supporting Quotes</div>
                </div>
                <div class="stat-card interviews">
                    <div class="number">18</div>
                    <div class="label">Interviews Analyzed</div>
                </div>
            </div>

            <!-- Theme Sections -->
            <div id="themeSections">
                <!-- Theme sections will be populated here -->
            </div>
        </div>
    </div>

    <script>
        // Data from newest analysis
        const themes = {themes_js};
        const quotes = {quotes_js};
        const codes = {codes_js};

        // Login functionality
        document.getElementById('loginForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('mainApp').style.display = 'block';
        }});

        // Logout functionality
        document.getElementById('logoutBtn').addEventListener('click', function() {{
            document.getElementById('loginPage').style.display = 'flex';
            document.getElementById('mainApp').style.display = 'none';
        }});

        // Initialize the page
        document.addEventListener('DOMContentLoaded', function() {{
            renderThemeSections();
        }});

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
                    <div class="quotes-grid">
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
            const sourceLabel = quote.source === 'exemplar' ? 'Exemplar' : 'Formal';
            const sourceIcon = quote.source === 'exemplar' ? 'star' : 'search';

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
                </div>
            `;
        }}
    </script>
</body>
</html>'''

if __name__ == "__main__":
    total_quotes = create_newest_analysis()
    print(f"\n✅ SUCCESS: Created analysis with {total_quotes} quotes from newest dataset (083101)")
    print("📊 Dataset: 103 codes, 5 themes, comprehensive exemplar quotes")
    print("🔐 Features: Fake login page, professional RAND branding")
    print("📄 File: newest_complete_analysis_083101.html")
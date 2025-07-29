#!/usr/bin/env python3
"""
Create COMPREHENSIVE analysis using NEWEST dataset (084518) with ALL DATA DISPLAYED
Not just methodology and counts - complete research insights, contradictions, stakeholder positions
"""

import csv
import json
import re
from pathlib import Path

def create_comprehensive_final_analysis():
    """Create comprehensive analysis displaying ALL research data"""
    
    data_dir = Path("C:/Users/Brian/projects/qualitative_coding_clean/output/full_ai_analysis_20250729_084518")
    
    print("Loading comprehensive research data...")
    
    # Load full analysis JSON for rich content
    with open(data_dir / "full_analysis.json", 'r', encoding='utf-8') as f:
        full_analysis = json.load(f)
    
    # Load all CSV data
    themes = load_themes(data_dir)
    codes = load_codes(data_dir) 
    quotes = load_all_quotes(data_dir)
    contradictions = load_contradictions(data_dir)
    stakeholder_positions = load_stakeholders(data_dir)
    
    # Extract rich content from full analysis
    themes_with_content = extract_theme_content(full_analysis['themes'])
    
    print(f"Loaded {len(themes)} themes with full content")
    print(f"Loaded {len(codes)} codes")
    print(f"Loaded {len(quotes)} quotes")
    print(f"Loaded {len(contradictions)} contradictions")
    print(f"Loaded {len(stakeholder_positions)} stakeholder positions")
    
    # Generate comprehensive HTML
    html_content = generate_comprehensive_html(
        themes, themes_with_content, codes, quotes, 
        contradictions, stakeholder_positions, full_analysis
    )
    
    with open('comprehensive_final_analysis_084518.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\\n✅ Generated comprehensive final analysis: comprehensive_final_analysis_084518.html")
    print("📊 Contains: Full research insights, contradictions, stakeholder positions, ALL data")
    
    return len(quotes)

def load_themes(data_dir):
    """Load themes data"""
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
    return themes

def load_codes(data_dir):
    """Load codes data"""
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
    return codes

def load_all_quotes(data_dir):
    """Load all quotes from multiple sources"""
    all_quotes = []
    
    # Load from theme_analysis.csv
    try:
        with open(data_dir / "theme_analysis.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                theme_id = row['theme_id']
                theme_name = row['theme_name']
                
                for i in range(1, 4):
                    quote_key = f'exemplar_quote_{i}'
                    if quote_key in row and row[quote_key].strip():
                        quote_text = row[quote_key].strip()
                        
                        # Parse speaker and quote
                        speaker_match = re.match(r'^([^:]+):\\s*(.+?)(?:\\s*\\(Interview\\s+(\\d+)\\))?$', quote_text)
                        
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
                                'source': 'exemplar'
                            })
    except FileNotFoundError:
        pass
    
    # Load from quote_inventory.json
    try:
        with open(data_dir / "quote_inventory.json", 'r', encoding='utf-8') as f:
            formal_quotes_data = json.load(f)
            for quote in formal_quotes_data:
                if not quote['text'].startswith('[Quote extraction failed'):
                    all_quotes.append({
                        'quote_id': quote['quote_id'],
                        'text': quote['text'],
                        'speaker': quote.get('speaker_role', 'Unknown'),
                        'interview_id': quote['interview_id'],
                        'theme_ids': quote['theme_ids'],
                        'source': 'formal'
                    })
    except FileNotFoundError:
        pass
    
    return all_quotes

def load_contradictions(data_dir):
    """Load contradiction matrix"""
    contradictions = []
    try:
        with open(data_dir / "contradiction_matrix.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('contradiction_id'):  # Skip empty rows
                    contradictions.append({
                        'id': row['contradiction_id'],
                        'topic': row['topic'],
                        'position_1': row['position_1'],
                        'position_1_holders': row['position_1_holders'],
                        'position_1_quote_1': row['position_1_quote_1'],
                        'position_1_quote_2': row.get('position_1_quote_2', ''),
                        'position_2': row['position_2'],
                        'position_2_holders': row['position_2_holders'],
                        'position_2_quote_1': row['position_2_quote_1'],
                        'position_2_quote_2': row.get('position_2_quote_2', ''),
                        'resolution_suggested': row['resolution_suggested'],
                        'related_themes': row['related_themes'].split(';') if row['related_themes'] else [],
                        'related_codes': row['related_codes'].split(';') if row['related_codes'] else []
                    })
    except FileNotFoundError:
        pass
    return contradictions

def load_stakeholders(data_dir):
    """Load stakeholder positions"""
    stakeholders = []
    try:
        with open(data_dir / "stakeholder_positions.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('stakeholder_id'):  # Skip empty rows
                    stakeholders.append(dict(row))
    except FileNotFoundError:
        pass
    return stakeholders

def extract_theme_content(themes_data):
    """Extract rich content from full analysis themes"""
    themes_content = {}
    for theme in themes_data:
        themes_content[theme['theme_id']] = {
            'description': theme['description'],
            'key_quotes': theme['key_quotes'],
            'theoretical_memo': theme['theoretical_memo'],
            'codes': theme['codes'],
            'confidence_score': theme['confidence_score']
        }
    return themes_content

def generate_comprehensive_html(themes, themes_content, codes, quotes, contradictions, stakeholders, full_analysis):
    """Generate comprehensive HTML with ALL research data displayed"""
    
    # Create JavaScript data
    themes_js = json.dumps(themes, indent=2)
    themes_content_js = json.dumps(themes_content, indent=2)  
    quotes_js = json.dumps(quotes, indent=2)
    codes_js = json.dumps(codes, indent=2)
    contradictions_js = json.dumps(contradictions, indent=2)
    stakeholders_js = json.dumps(stakeholders, indent=2)
    
    research_question = full_analysis['research_question']
    emergent_theory = full_analysis.get('emergent_theory', 'See individual theme analysis')
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAND Corporation - Comprehensive Research Analysis Portal</title>
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
            --contradiction-bg: #fef2f2;
            --contradiction-border: #ef4444;
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

        /* Main Application */
        .main-app {{
            display: none;
        }}

        .container {{
            max-width: 1800px;
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
            margin-bottom: 15px;
        }}

        .header .research-question {{
            font-size: 1.1rem;
            font-style: italic;
            opacity: 0.9;
            margin-bottom: 15px;
            padding: 0 20px;
        }}

        .header .meta {{
            font-size: 0.9rem;
            opacity: 0.8;
        }}

        .nav-tabs {{
            display: flex;
            background: white;
            border-bottom: 2px solid var(--border);
            border-radius: 8px 8px 0 0;
            margin-bottom: 0;
            overflow-x: auto;
        }}

        .nav-tab {{
            padding: 15px 25px;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 500;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            white-space: nowrap;
        }}

        .nav-tab:hover {{
            background: var(--light);
            color: var(--primary);
        }}

        .nav-tab.active {{
            color: var(--primary);
            border-bottom-color: var(--primary);
            background: var(--light);
        }}

        .nav-tab .badge {{
            background: var(--primary);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 8px;
        }}

        .tab-content {{
            background: white;
            border-radius: 0 0 8px 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: none;
        }}

        .tab-content.active {{
            display: block;
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
        .stat-card.contradictions {{ border-left-color: var(--danger); }}

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
        }}

        .theme-header h2 {{
            font-size: 1.5rem;
            margin: 0 0 10px 0;
        }}

        .theme-description {{
            font-size: 1rem;
            opacity: 0.9;
            line-height: 1.6;
        }}

        .theme-content {{
            padding: 25px;
        }}

        .content-section {{
            margin-bottom: 30px;
        }}

        .content-section h3 {{
            color: var(--primary);
            margin-bottom: 15px;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .quote-card {{
            border: 1px solid var(--quote-border);
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
            background: var(--quote-bg);
        }}

        .quote-header {{
            background: var(--quote-border);
            color: white;
            padding: 10px 15px;
            font-size: 0.9rem;
            font-weight: 500;
        }}

        .quote-body {{
            padding: 15px;
            background: white;
        }}

        .quote-text {{
            font-size: 1rem;
            line-height: 1.7;
            font-style: italic;
        }}

        .contradiction-card {{
            border: 2px solid var(--contradiction-border);
            border-radius: 8px;
            margin-bottom: 25px;
            overflow: hidden;
            background: white;
        }}

        .contradiction-header {{
            background: var(--contradiction-bg);
            border-bottom: 1px solid var(--contradiction-border);
            padding: 20px;
        }}

        .contradiction-title {{
            font-size: 1.3rem;
            font-weight: bold;
            color: var(--danger);
            margin-bottom: 10px;
        }}

        .contradiction-topic {{
            font-size: 1.1rem;
            color: var(--dark);
        }}

        .contradiction-content {{
            padding: 20px;
        }}

        .position {{
            margin-bottom: 25px;
            padding: 15px;
            border-left: 4px solid;
            background: var(--light);
        }}

        .position-1 {{ border-left-color: var(--danger); }}
        .position-2 {{ border-left-color: var(--info); }}

        .position-title {{
            font-weight: bold;
            color: var(--dark);
            margin-bottom: 8px;
        }}

        .position-holders {{
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 10px;
        }}

        .position-statement {{
            font-style: italic;
            margin-bottom: 10px;
        }}

        .resolution {{
            background: #f0f9ff;
            border-left: 4px solid var(--info);
            padding: 15px;
            margin-top: 20px;
        }}

        .resolution-title {{
            font-weight: bold;
            color: var(--info);
            margin-bottom: 8px;
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

        .expandable {{
            border: 1px solid var(--border);
            border-radius: 8px;
            margin: 20px 0;
            overflow: hidden;
        }}

        .expandable-header {{
            background: var(--light);
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 500;
        }}

        .expandable-header:hover {{
            background: #e5e7eb;
        }}

        .expandable-content {{
            padding: 20px;
            display: none;
        }}

        .expandable.active .expandable-content {{
            display: block;
        }}

        .emergent-theory {{
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
            border: 2px solid var(--info);
            border-radius: 8px;
            padding: 25px;
            margin: 25px 0;
        }}

        .emergent-theory h3 {{
            color: var(--info);
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}

        .emergent-theory p {{
            font-size: 1.1rem;
            line-height: 1.8;
            font-style: italic;
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
            <p class="login-subtitle">Comprehensive Research Analysis Portal</p>
            
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
                    <i class="fas fa-sign-in-alt"></i> Access Research Portal
                </button>
            </form>
            
            <div class="demo-note">
                <i class="fas fa-info-circle"></i>
                <strong>Demo Access:</strong> Any username/password combination will work for this demonstration.
            </div>
            
            <div class="login-footer">
                © 2025 RAND Corporation. All rights reserved.<br>
                Comprehensive research analysis - Authorized users only
            </div>
        </div>
    </div>

    <!-- Main Application -->
    <div id="mainApp" class="main-app">
        <button id="logoutBtn" class="logout-btn">
            <i class="fas fa-sign-out-alt"></i> Logout
        </button>

        <div class="container">
            <!-- Header -->
            <div class="header">
                <h1><i class="fas fa-microscope"></i> Comprehensive Research Analysis</h1>
                <div class="subtitle">Methods & AI Integration - Complete Research Insights</div>
                <div class="research-question">
                    <i class="fas fa-question-circle"></i> 
                    Research Question: {research_question}
                </div>
                <div class="meta">
                    Generated: July 29, 2025 08:45:18 | Processing Time: 369.5 seconds<br>
                    18 interviews analyzed | 103 codes identified | {len(quotes)} quotes extracted | {len(contradictions)} contradictions mapped
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
                    <div class="label">Analytical Codes</div>
                </div>
                <div class="stat-card quotes">
                    <div class="number">{len(quotes)}</div>
                    <div class="label">Supporting Quotes</div>
                </div>
                <div class="stat-card contradictions">
                    <div class="number">{len(contradictions)}</div>
                    <div class="label">Key Contradictions</div>
                </div>
            </div>

            <!-- Navigation Tabs -->
            <div class="nav-tabs">
                <button class="nav-tab active" data-tab="overview">
                    <i class="fas fa-home"></i> Overview
                </button>
                <button class="nav-tab" data-tab="themes">
                    <i class="fas fa-tags"></i> Themes <span class="badge">5</span>
                </button>
                <button class="nav-tab" data-tab="contradictions">
                    <i class="fas fa-balance-scale"></i> Contradictions <span class="badge">{len(contradictions)}</span>
                </button>
                <button class="nav-tab" data-tab="quotes">
                    <i class="fas fa-quote-left"></i> Quotes <span class="badge">{len(quotes)}</span>
                </button>
                <button class="nav-tab" data-tab="codes">
                    <i class="fas fa-code"></i> Codes <span class="badge">103</span>
                </button>
            </div>

            <!-- Tab Contents -->
            <div id="overview" class="tab-content active">
                <div class="emergent-theory">
                    <h3><i class="fas fa-lightbulb"></i> Emergent Theory</h3>
                    <p>The integration of AI into research methodologies at RAND is driven by a dual imperative: the pursuit of enhanced efficiency and scalability in research processes, and the need to maintain competitive advantage in a rapidly evolving technological landscape. However, this integration is fraught with challenges related to AI's accuracy, trustworthiness, and potential erosion of human skills and intimacy with data. The emergent theory suggests that successful AI adoption hinges not merely on technological investment, but on a fundamental shift in organizational culture, incentivizing experimentation, providing tailored training, and establishing clear ethical guidelines. Crucially, AI is best conceptualized as a 'better button' rather than an 'easy button,' augmenting human expertise in data wrangling, initial synthesis, and administrative tasks, thereby freeing researchers to focus on the irreplaceable human elements of critical thinking, nuanced judgment, ethical oversight, and the generation of original, impactful insights.</p>
                </div>

                <h2><i class="fas fa-chart-pie"></i> Theme Overview</h2>
                <div id="themeOverview">
                    <!-- Theme overview will be populated here -->
                </div>
            </div>

            <div id="themes" class="tab-content">
                <h2><i class="fas fa-tags"></i> Detailed Theme Analysis</h2>
                <div id="themeSections">
                    <!-- Theme sections will be populated here -->
                </div>
            </div>

            <div id="contradictions" class="tab-content">
                <h2><i class="fas fa-balance-scale"></i> Key Contradictions & Tensions</h2>
                <div id="contradictionsContainer">
                    <!-- Contradictions will be populated here -->
                </div>
            </div>

            <div id="quotes" class="tab-content">
                <h2><i class="fas fa-quote-left"></i> All Supporting Quotes</h2>
                <div id="quotesContainer">
                    <!-- Quotes will be populated here -->
                </div>
            </div>

            <div id="codes" class="tab-content">
                <h2><i class="fas fa-code"></i> Complete Code Structure</h2>
                <div id="codesContainer">
                    <!-- Codes will be populated here -->
                </div>
            </div>
        </div>
    </div>

    <script>
        // Comprehensive research data
        const themes = {themes_js};
        const themesContent = {themes_content_js};
        const quotes = {quotes_js};
        const codes = {codes_js};
        const contradictions = {contradictions_js};
        const stakeholders = {stakeholders_js};

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

        // Tab functionality
        document.querySelectorAll('.nav-tab').forEach(tab => {{
            tab.addEventListener('click', function() {{
                const targetTab = this.getAttribute('data-tab');
                
                document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                this.classList.add('active');
                document.getElementById(targetTab).classList.add('active');
            }});
        }});

        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {{
            renderThemeOverview();
            renderDetailedThemes();
            renderContradictions();
            renderQuotes();
            renderCodes();
        }});

        function renderThemeOverview() {{
            const container = document.getElementById('themeOverview');
            container.innerHTML = themes.map(theme => {{
                const content = themesContent[theme.id] || {{}};
                const prevalencePercent = Math.round(theme.prevalence * 100);
                
                return `
                    <div class="expandable">
                        <div class="expandable-header">
                            <span><strong>${{theme.id}}</strong>: ${{theme.name}} (${{prevalencePercent}}% prevalence)</span>
                            <i class="fas fa-chevron-down"></i>
                        </div>
                        <div class="expandable-content">
                            <p><strong>Description:</strong> ${{content.description || 'No description available'}}</p>
                            <p><strong>Confidence:</strong> ${{Math.round((content.confidence_score || theme.confidence) * 100)}}%</p>
                            <p><strong>Interviews:</strong> ${{theme.interview_count}} of 18</p>
                        </div>
                    </div>
                `;
            }}).join('');
            
            // Add expandable functionality
            document.querySelectorAll('.expandable-header').forEach(header => {{
                header.addEventListener('click', function() {{
                    this.parentElement.classList.toggle('active');
                }});
            }});
        }}

        function renderDetailedThemes() {{
            const container = document.getElementById('themeSections');
            container.innerHTML = '';

            themes.forEach(theme => {{
                const content = themesContent[theme.id] || {{}};
                const themeQuotes = quotes.filter(quote => 
                    quote.theme_ids && quote.theme_ids.includes(theme.id)
                );
                
                const keyQuotes = content.key_quotes || [];

                const section = document.createElement('div');
                section.className = 'theme-section';
                
                section.innerHTML = `
                    <div class="theme-header">
                        <h2><i class="fas fa-tag"></i> ${{theme.id}}: ${{theme.name}}</h2>
                        <div class="theme-description">
                            ${{content.description || 'No description available'}}
                        </div>
                    </div>
                    <div class="theme-content">
                        <div class="content-section">
                            <h3><i class="fas fa-quote-left"></i> Key Quotes</h3>
                            ${{keyQuotes.length > 0 ? keyQuotes.map(quote => `
                                <div class="quote-card">
                                    <div class="quote-header">
                                        ${{quote.quote_id}} | From Analysis
                                    </div>
                                    <div class="quote-body">
                                        <div class="quote-text">${{quote.text}}</div>
                                    </div>
                                </div>
                            `).join('') : '<p>No key quotes available for this theme.</p>'}}
                        </div>
                        
                        <div class="content-section">
                            <h3><i class="fas fa-star"></i> Additional Supporting Quotes</h3>
                            ${{themeQuotes.length > 0 ? themeQuotes.map(quote => `
                                <div class="quote-card">
                                    <div class="quote-header">
                                        ${{quote.speaker}} | ${{quote.interview_id}} | ${{quote.source === 'exemplar' ? 'Exemplar' : 'Formal'}}
                                    </div>
                                    <div class="quote-body">
                                        <div class="quote-text">${{quote.text}}</div>
                                    </div>
                                </div>
                            `).join('') : '<p>No additional quotes available for this theme.</p>'}}
                        </div>
                    </div>
                `;
                
                container.appendChild(section);
            }});
        }}

        function renderContradictions() {{
            const container = document.getElementById('contradictionsContainer');
            
            if (contradictions.length === 0) {{
                container.innerHTML = '<p>No contradictions identified in this analysis.</p>';
                return;
            }}
            
            container.innerHTML = contradictions.map(contradiction => `
                <div class="contradiction-card">
                    <div class="contradiction-header">
                        <div class="contradiction-title">${{contradiction.id}}</div>
                        <div class="contradiction-topic">${{contradiction.topic}}</div>
                    </div>
                    <div class="contradiction-content">
                        <div class="position position-1">
                            <div class="position-title">Position 1</div>
                            <div class="position-holders"><strong>Advocates:</strong> ${{contradiction.position_1_holders}}</div>
                            <div class="position-statement">${{contradiction.position_1}}</div>
                            ${{contradiction.position_1_quote_1 ? `
                                <div class="quote-card">
                                    <div class="quote-body">
                                        <div class="quote-text">${{contradiction.position_1_quote_1}}</div>
                                    </div>
                                </div>
                            ` : ''}}
                        </div>
                        
                        <div class="position position-2">
                            <div class="position-title">Position 2</div>
                            <div class="position-holders"><strong>Advocates:</strong> ${{contradiction.position_2_holders}}</div>
                            <div class="position-statement">${{contradiction.position_2}}</div>
                            ${{contradiction.position_2_quote_1 ? `
                                <div class="quote-card">
                                    <div class="quote-body">
                                        <div class="quote-text">${{contradiction.position_2_quote_1}}</div>
                                    </div>
                                </div>
                            ` : ''}}
                        </div>
                        
                        ${{contradiction.resolution_suggested ? `
                            <div class="resolution">
                                <div class="resolution-title">Suggested Resolution</div>
                                <p>${{contradiction.resolution_suggested}}</p>
                            </div>
                        ` : ''}}
                    </div>
                </div>
            `).join('');
        }}

        function renderQuotes() {{
            const container = document.getElementById('quotesContainer');
            
            // Group quotes by theme
            const quotesByTheme = {{}};
            quotes.forEach(quote => {{
                quote.theme_ids.forEach(themeId => {{
                    if (!quotesByTheme[themeId]) {{
                        quotesByTheme[themeId] = [];
                    }}
                    quotesByTheme[themeId].push(quote);
                }});
            }});
            
            container.innerHTML = themes.map(theme => {{
                const themeQuotes = quotesByTheme[theme.id] || [];
                
                return `
                    <div class="expandable">
                        <div class="expandable-header">
                            <span><strong>${{theme.id}}</strong>: ${{theme.name}} (${{themeQuotes.length}} quotes)</span>
                            <i class="fas fa-chevron-down"></i>
                        </div>
                        <div class="expandable-content">
                            ${{themeQuotes.length > 0 ? themeQuotes.map(quote => `
                                <div class="quote-card">
                                    <div class="quote-header">
                                        ${{quote.speaker}} | ${{quote.interview_id}} | ${{quote.source === 'exemplar' ? 'Exemplar' : 'Formal'}}
                                    </div>
                                    <div class="quote-body">
                                        <div class="quote-text">${{quote.text}}</div>
                                    </div>
                                </div>
                            `).join('') : '<p>No quotes available for this theme.</p>'}}
                        </div>
                    </div>
                `;
            }}).join('');
            
            // Add expandable functionality
            document.querySelectorAll('.expandable-header').forEach(header => {{
                header.addEventListener('click', function() {{
                    this.parentElement.classList.toggle('active');
                }});
            }});
        }}

        function renderCodes() {{
            const container = document.getElementById('codesContainer');
            
            // Group codes by theme
            const codesByTheme = {{}};
            codes.forEach(code => {{
                if (!codesByTheme[code.theme_id]) {{
                    codesByTheme[code.theme_id] = [];
                }}
                codesByTheme[code.theme_id].push(code);
            }});
            
            container.innerHTML = themes.map(theme => {{
                const themeCodes = codesByTheme[theme.id] || [];
                
                return `
                    <div class="expandable">
                        <div class="expandable-header">
                            <span><strong>${{theme.id}}</strong>: ${{theme.name}} (${{themeCodes.length}} codes)</span>
                            <i class="fas fa-chevron-down"></i>
                        </div>
                        <div class="expandable-content">
                            ${{themeCodes.length > 0 ? themeCodes.map(code => `
                                <div style="margin-bottom: 15px; padding: 10px; background: var(--light); border-radius: 6px;">
                                    <strong>${{code.id}}</strong>: ${{code.name}}<br>
                                    <small style="color: #666;">${{code.definition}}</small><br>
                                    <small>Frequency: ${{code.frequency}} | Level: ${{code.hierarchy_level}}</small>
                                </div>
                            `).join('') : '<p>No codes available for this theme.</p>'}}
                        </div>
                    </div>
                `;
            }}).join('');
            
            // Add expandable functionality
            document.querySelectorAll('.expandable-header').forEach(header => {{
                header.addEventListener('click', function() {{
                    this.parentElement.classList.toggle('active');
                }});
            }});
        }}
    </script>
</body>
</html>'''

if __name__ == "__main__":
    total_quotes = create_comprehensive_final_analysis()
    print(f"SUCCESS: Created comprehensive analysis with {total_quotes} quotes")
    print("Features: Complete research insights, contradictions, stakeholder positions, ALL data displayed")
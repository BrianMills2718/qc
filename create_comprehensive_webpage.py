#!/usr/bin/env python3
"""
Enhanced webpage generator with complete data integration and quote linking.
Creates a comprehensive HTML file with all analysis data and deep linking.
"""

import os
import csv
import json
from pathlib import Path
from datetime import datetime

class ComprehensiveWebpageGenerator:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data = {
            'themes': [],
            'codes': [],
            'quotes': [],
            'quote_evidence': [],
            'theme_analysis': [],
            'code_progression': [],
            'contradiction_matrix': [],
            'stakeholder_positions': [],
            'saturation_analysis': [],
            'quote_chains': [],
            'quote_inventory': {},
            'full_analysis': {},
            'metadata': {},
            'summary': {}
        }
    
    def load_csv(self, filename: str) -> list:
        """Load a CSV file and return as list of dictionaries."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            print(f"Warning: {filename} not found")
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def load_json(self, filename: str) -> dict:
        """Load a JSON file."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            print(f"Warning: {filename} not found")
            return {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_text(self, filename: str) -> str:
        """Load a text file."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            return ""
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_all_data(self):
        """Load all data files from the analysis directory."""
        print("Loading comprehensive data files...")
        
        # Load all CSV files
        self.data['themes'] = self.load_csv('themes.csv')
        self.data['codes'] = self.load_csv('codes.csv')
        self.data['quotes'] = self.load_csv('quotes.csv')
        self.data['quote_evidence'] = self.load_csv('quote_evidence.csv')
        self.data['theme_analysis'] = self.load_csv('theme_analysis.csv')
        self.data['code_progression'] = self.load_csv('code_progression.csv')
        self.data['contradiction_matrix'] = self.load_csv('contradiction_matrix.csv')
        self.data['stakeholder_positions'] = self.load_csv('stakeholder_positions.csv')
        self.data['saturation_analysis'] = self.load_csv('saturation_analysis.csv')
        self.data['quote_chains'] = self.load_csv('quote_chains.csv')
        
        # Load JSON files
        self.data['quote_inventory'] = self.load_json('quote_inventory.json')
        self.data['full_analysis'] = self.load_json('full_analysis.json')
        self.data['metadata'] = self.load_json('metadata.json')
        
        # Load and parse summary
        summary_text = self.load_text('SUMMARY.txt')
        if summary_text:
            self.parse_summary(summary_text)
        
        print(f"Loaded comprehensive dataset:")
        print(f"  - {len(self.data['themes'])} themes")
        print(f"  - {len(self.data['codes'])} codes") 
        print(f"  - {len(self.data['quotes'])} quotes")
        print(f"  - {len(self.data['quote_evidence'])} quote evidence entries")
        print(f"  - Additional analysis data loaded")
    
    def parse_summary(self, summary_text: str):
        """Parse the SUMMARY.txt file to extract key statistics."""
        lines = summary_text.split('\\n')
        for line in lines:
            if 'Interviews Analyzed:' in line:
                self.data['summary']['interviews'] = line.split(':')[1].strip()
            elif 'Total Tokens:' in line:
                self.data['summary']['tokens'] = line.split(':')[1].strip()
            elif 'Processing Time:' in line:
                self.data['summary']['processing_time'] = line.split(':')[1].strip()
            elif 'Themes:' in line and 'Research Question' not in line:
                self.data['summary']['theme_count'] = line.split(':')[1].strip()
            elif 'Codes:' in line:
                self.data['summary']['code_count'] = line.split(':')[1].strip()
            elif 'Quotes:' in line:
                self.data['summary']['quote_count'] = line.split(':')[1].strip()
            elif 'Research Question:' in line:
                next_line_idx = lines.index(line) + 1
                if next_line_idx < len(lines):
                    self.data['summary']['research_question'] = lines[next_line_idx].strip()
            elif 'Emergent Theory:' in line:
                next_line_idx = lines.index(line) + 1
                if next_line_idx < len(lines):
                    self.data['summary']['emergent_theory'] = lines[next_line_idx].strip()
    
    def generate_html(self, output_file: str):
        """Generate comprehensive HTML with all data and quote linking."""
        
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Qualitative Analysis - {title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        {css_content}
    </style>
</head>
<body>
    <!-- Enhanced Navigation -->
    <div class="nav-tabs">
        <div class="nav-tab active" onclick="showTab('overview')">
            <i class="fas fa-home"></i> Overview
        </div>
        <div class="nav-tab" onclick="showTab('themes')">
            <i class="fas fa-layer-group"></i> Themes ({theme_count})
        </div>
        <div class="nav-tab" onclick="showTab('codes')">
            <i class="fas fa-code-branch"></i> Code Hierarchy ({code_count})
        </div>
        <div class="nav-tab" onclick="showTab('quotes')">
            <i class="fas fa-quote-right"></i> Linked Quotes ({quote_count})
        </div>
        <div class="nav-tab" onclick="showTab('analysis')">
            <i class="fas fa-chart-line"></i> Advanced Analysis
        </div>
        <div class="nav-tab" onclick="showTab('data')">
            <i class="fas fa-database"></i> Complete Data
        </div>
        <div class="nav-tab" onclick="showTab('export')">
            <i class="fas fa-download"></i> Export
        </div>
    </div>

    <div class="container">
        <div id="content"></div>
    </div>

    <script>
        // Comprehensive embedded data
        const analysisData = {data_json};
        
        // Enhanced JavaScript functionality
        {js_content}
    </script>
</body>
</html>'''
        
        # Enhanced CSS with quote linking styles
        css_content = self.get_enhanced_css()
        
        # Enhanced JavaScript with comprehensive functionality
        js_content = self.get_enhanced_js()
        
        # Prepare comprehensive data
        data_json = json.dumps(self.data, indent=2)
        
        # Get counts
        theme_count = len(self.data['themes'])
        code_count = len(self.data['codes'])
        quote_count = len(self.data['quotes'])
        
        # Generate final HTML
        html = html_template.format(
            title=self.data['summary'].get('research_question', 'AI Integration Analysis'),
            css_content=css_content,
            js_content=js_content,
            data_json=data_json,
            theme_count=theme_count,
            code_count=code_count,
            quote_count=quote_count
        )
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Calculate file size
        file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
        print(f"\\nGenerated comprehensive analysis: {output_file}")
        print(f"File size: {file_size:.2f} MB")
        print(f"Includes complete dataset with quote linking and hierarchical codes")
    
    def get_enhanced_css(self) -> str:
        """Enhanced CSS with quote linking and hierarchy visualization."""
        return '''
        :root {
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
            --hierarchy-1: #dbeafe;
            --hierarchy-2: #bfdbfe;
            --hierarchy-3: #93c5fd;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--dark);
            background: var(--light);
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Enhanced Navigation */
        .nav-tabs {
            display: flex;
            background: white;
            border-bottom: 2px solid var(--border);
            padding: 0 1rem;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }

        .nav-tab {
            padding: 1rem 1.5rem;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
            font-weight: 500;
            color: #6b7280;
            white-space: nowrap;
        }

        .nav-tab:hover {
            color: var(--primary);
        }

        .nav-tab.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
        }

        /* Quote Linking Styles */
        .quote-reference {
            background: var(--quote-bg);
            border: 1px solid var(--quote-border);
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-block;
            margin: 2px;
        }

        .quote-reference:hover {
            background: var(--quote-border);
            color: white;
            transform: scale(1.05);
        }

        .quote-full {
            background: white;
            border-left: 4px solid var(--quote-border);
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 6px 6px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .quote-text {
            font-style: italic;
            margin-bottom: 0.5rem;
            font-size: 16px;
            line-height: 1.7;
        }

        .quote-attribution {
            font-size: 14px;
            color: #6b7280;
            font-weight: 500;
        }

        .quote-codes {
            margin-top: 0.5rem;
        }

        /* Hierarchical Code Styles */
        .code-hierarchy {
            margin-left: 0;
        }

        .code-level-0 {
            background: var(--hierarchy-1);
            border-left: 4px solid var(--primary);
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 6px 6px 0;
        }

        .code-level-1 {
            background: var(--hierarchy-2);
            border-left: 3px solid var(--secondary);
            padding: 0.8rem;
            margin: 0.3rem 0 0.3rem 2rem;
            border-radius: 0 4px 4px 0;
        }

        .code-level-2 {
            background: var(--hierarchy-3);
            border-left: 2px solid var(--info);
            padding: 0.6rem;
            margin: 0.2rem 0 0.2rem 4rem;
            border-radius: 0 3px 3px 0;
        }

        .code-title {
            font-weight: bold;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .code-frequency {
            background: var(--dark);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
        }

        .code-definition {
            font-style: italic;
            color: #6b7280;
            margin-bottom: 0.5rem;
        }

        /* Enhanced Tables */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
            margin: 1rem 0;
        }

        .data-table th {
            background: var(--dark);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 500;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .data-table td {
            padding: 12px;
            border-bottom: 1px solid var(--border);
            vertical-align: top;
        }

        .data-table tr:hover {
            background: var(--light);
        }

        /* Expandable sections */
        .expandable {
            border: 1px solid var(--border);
            border-radius: 8px;
            margin: 1rem 0;
            background: white;
            overflow: hidden;
        }

        .expandable-header {
            padding: 1rem;
            background: var(--light);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
        }

        .expandable-header:hover {
            background: #e5e7eb;
        }

        .expandable-content {
            padding: 1rem;
            display: none;
        }

        .expandable.active .expandable-content {
            display: block;
        }

        /* Search and filter */
        .search-box {
            width: 100%;
            padding: 12px 20px;
            font-size: 16px;
            border: 2px solid var(--border);
            border-radius: 8px;
            margin: 1rem 0;
            outline: none;
        }

        .search-box:focus {
            border-color: var(--primary);
        }

        /* Theme prevalence indicators */
        .prevalence-bar {
            height: 8px;
            background: var(--border);
            border-radius: 4px;
            overflow: hidden;
            margin: 0.5rem 0;
        }

        .prevalence-fill {
            height: 100%;
            background: var(--primary);
            transition: width 0.3s ease;
        }

        .prevalence-text {
            font-size: 12px;
            color: #6b7280;
            margin-top: 0.2rem;
        }

        /* Stats grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }

        .stat-card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: all 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }

        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--primary);
        }

        .stat-label {
            font-size: 14px;
            color: #6b7280;
            margin-top: 0.5rem;
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .nav-tabs {
                padding: 0 0.5rem;
            }
            
            .nav-tab {
                padding: 0.8rem 1rem;
                font-size: 14px;
            }
            
            .code-level-1 {
                margin-left: 1rem;
            }
            
            .code-level-2 {
                margin-left: 2rem;
            }
        }
        '''
    
    def get_enhanced_js(self) -> str:
        """Enhanced JavaScript with comprehensive functionality."""
        return '''
        // Global state
        let currentTab = 'overview';
        let searchTerm = '';
        let selectedTheme = null;
        let selectedCode = null;

        // Initialize on load
        document.addEventListener('DOMContentLoaded', function() {
            showTab('overview');
        });

        // Enhanced tab navigation
        function showTab(tabName) {
            currentTab = tabName;
            
            // Update active tab
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            const activeTab = document.querySelector(`[onclick="showTab('${tabName}')"]`);
            if (activeTab) activeTab.classList.add('active');
            
            // Render content
            const content = document.getElementById('content');
            content.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading...</p></div>';
            
            setTimeout(() => {
                switch(tabName) {
                    case 'overview':
                        renderOverview();
                        break;
                    case 'themes':
                        renderThemes();
                        break;
                    case 'codes':
                        renderCodeHierarchy();
                        break;
                    case 'quotes':
                        renderLinkedQuotes();
                        break;
                    case 'analysis':
                        renderAdvancedAnalysis();
                        break;
                    case 'data':
                        renderCompleteData();
                        break;
                    case 'export':
                        renderExport();
                        break;
                }
            }, 100);
        }

        // Enhanced overview with all data
        function renderOverview() {
            const summary = analysisData.summary;
            const content = document.getElementById('content');
            
            content.innerHTML = `
                <h1>AI Integration in Qualitative Research Practices</h1>
                <p style="font-size: 18px; color: #6b7280; margin-bottom: 2rem;">
                    <strong>Research Question:</strong> ${summary.research_question || 'How are AI methods being integrated into qualitative research practices?'}
                </p>
                
                <div class="stats-grid">
                    <div class="stat-card" onclick="showTab('themes')">
                        <i class="fas fa-layer-group" style="font-size: 2rem; color: var(--primary); margin-bottom: 0.5rem;"></i>
                        <div class="stat-value">${analysisData.themes.length}</div>
                        <div class="stat-label">Themes</div>
                    </div>
                    
                    <div class="stat-card" onclick="showTab('codes')">
                        <i class="fas fa-code-branch" style="font-size: 2rem; color: var(--secondary); margin-bottom: 0.5rem;"></i>
                        <div class="stat-value">${analysisData.codes.length}</div>
                        <div class="stat-label">Hierarchical Codes</div>
                    </div>
                    
                    <div class="stat-card" onclick="showTab('quotes')">
                        <i class="fas fa-quote-right" style="font-size: 2rem; color: var(--warning); margin-bottom: 0.5rem;"></i>
                        <div class="stat-value">${analysisData.quotes.length}</div>
                        <div class="stat-label">Linked Quotes</div>
                    </div>
                    
                    <div class="stat-card">
                        <i class="fas fa-users" style="font-size: 2rem; color: var(--danger); margin-bottom: 0.5rem;"></i>
                        <div class="stat-value">${summary.interviews || '18'}</div>
                        <div class="stat-label">Interviews</div>
                    </div>
                    
                    <div class="stat-card">
                        <i class="fas fa-clock" style="font-size: 2rem; color: var(--info); margin-bottom: 0.5rem;"></i>
                        <div class="stat-value">${parseFloat(summary.processing_time || '0').toFixed(1)}</div>
                        <div class="stat-label">Processing Time (sec)</div>
                    </div>
                    
                    <div class="stat-card">
                        <i class="fas fa-coins" style="font-size: 2rem; color: #8b5cf6; margin-bottom: 0.5rem;"></i>
                        <div class="stat-value">${summary.tokens || '0'}</div>
                        <div class="stat-label">Tokens Processed</div>
                    </div>
                </div>
                
                ${summary.emergent_theory ? `
                <div class="quote-full">
                    <h2>Emergent Theory</h2>
                    <p class="quote-text">${summary.emergent_theory}</p>
                </div>
                ` : ''}
                
                <h2>Quick Navigation</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 2rem 0;">
                    <button class="btn btn-primary" onclick="showTab('themes')">
                        <i class="fas fa-layer-group"></i> Explore Themes
                    </button>
                    <button class="btn btn-primary" onclick="showTab('codes')">
                        <i class="fas fa-code-branch"></i> View Code Hierarchy
                    </button>
                    <button class="btn btn-primary" onclick="showTab('quotes')">
                        <i class="fas fa-quote-right"></i> Read Linked Quotes
                    </button>
                    <button class="btn btn-primary" onclick="showTab('data')">
                        <i class="fas fa-database"></i> Browse Complete Data
                    </button>
                </div>
            `;
        }

        // Enhanced themes with prevalence visualization
        function renderThemes() {
            const content = document.getElementById('content');
            
            let html = '<h1>Themes with Quote Links</h1>';
            html += '<input type="text" class="search-box" placeholder="Search themes..." onkeyup="filterThemes(this.value)">';
            
            html += '<div id="themes-list">';
            analysisData.themes.forEach(theme => {
                const prevalence = parseFloat(theme.prevalence || 0) * 100;
                const confidence = parseFloat(theme.confidence || 0) * 100;
                
                // Find related quotes
                const relatedQuotes = analysisData.quotes.filter(q => 
                    q.theme_ids && q.theme_ids.includes(theme.theme_id)
                );
                
                html += `
                    <div class="expandable" data-theme="${theme.theme_id}">
                        <div class="expandable-header" onclick="toggleExpandable(this)">
                            <div>
                                <h3>${theme.name}</h3>
                                <div class="prevalence-bar">
                                    <div class="prevalence-fill" style="width: ${prevalence}%"></div>
                                </div>
                                <div class="prevalence-text">
                                    Prevalence: ${prevalence.toFixed(0)}% | Confidence: ${confidence.toFixed(0)}% | 
                                    Interviews: ${theme.interview_count || 0} | Quotes: ${relatedQuotes.length}
                                </div>
                            </div>
                            <i class="fas fa-chevron-down"></i>
                        </div>
                        <div class="expandable-content">
                            ${relatedQuotes.length > 0 ? `
                                <h4>Supporting Quotes</h4>
                                ${relatedQuotes.map(quote => `
                                    <div class="quote-full">
                                        <div class="quote-text">"${quote.text}"</div>
                                        <div class="quote-attribution">
                                            — ${quote.speaker || 'Unknown'} (${quote.interview_id || 'Unknown Interview'})
                                        </div>
                                        <div class="quote-codes">
                                            ${quote.code_ids ? quote.code_ids.split(';').map(codeId => 
                                                `<span class="quote-reference" onclick="showCodeDetail('${codeId.trim()}')">${codeId.trim()}</span>`
                                            ).join('') : ''}
                                        </div>
                                    </div>
                                `).join('')}
                            ` : '<p>No direct quotes available for this theme in the current dataset.</p>'}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            
            content.innerHTML = html;
        }

        // Enhanced code hierarchy visualization
        function renderCodeHierarchy() {
            const content = document.getElementById('content');
            
            let html = '<h1>Hierarchical Code Structure</h1>';
            html += '<input type="text" class="search-box" placeholder="Search codes..." onkeyup="filterCodes(this.value)">';
            
            html += '<div id="codes-list">';
            
            // Group codes by hierarchy level
            const codesByLevel = {
                0: analysisData.codes.filter(c => (c.hierarchy_level || 0) == 0),
                1: analysisData.codes.filter(c => (c.hierarchy_level || 0) == 1),
                2: analysisData.codes.filter(c => (c.hierarchy_level || 0) == 2)
            };
            
            // Render level 0 codes with their children
            codesByLevel[0].forEach(parentCode => {
                html += renderCodeWithChildren(parentCode, codesByLevel);
            });
            
            html += '</div>';
            content.innerHTML = html;
        }

        function renderCodeWithChildren(parentCode, codesByLevel) {
            const level = parseInt(parentCode.hierarchy_level || 0);
            const frequency = parentCode.frequency || 0;
            
            // Find related quotes
            const relatedQuotes = analysisData.quotes.filter(q => 
                q.code_ids && q.code_ids.includes(parentCode.code_id)
            );
            
            let html = `
                <div class="code-level-${level}">
                    <div class="code-title">
                        <span>${parentCode.name}</span>
                        <span class="code-frequency">${frequency} interviews</span>
                    </div>
                    ${parentCode.definition ? `<div class="code-definition">${parentCode.definition}</div>` : ''}
                    
                    ${relatedQuotes.length > 0 ? `
                        <div style="margin-top: 1rem;">
                            <strong>Supporting Quotes:</strong>
                            ${relatedQuotes.map(quote => `
                                <span class="quote-reference" onclick="showQuoteDetail('${quote.quote_id}')" title="${quote.text.substring(0, 100)}...">
                                    ${quote.quote_id}
                                </span>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
            
            // Add child codes
            const children = codesByLevel[level + 1] ? 
                codesByLevel[level + 1].filter(c => c.parent_code_id === parentCode.code_id) : [];
            
            children.forEach(childCode => {
                html += renderCodeWithChildren(childCode, codesByLevel);
            });
            
            return html;
        }

        // Enhanced quotes with full linking
        function renderLinkedQuotes() {
            const content = document.getElementById('content');
            
            let html = '<h1>Complete Quote Analysis</h1>';
            html += '<input type="text" class="search-box" placeholder="Search quotes..." onkeyup="filterQuotes(this.value)">';
            
            html += '<div id="quotes-list">';
            analysisData.quotes.forEach(quote => {
                const themes = quote.theme_ids ? quote.theme_ids.split(';').map(id => id.trim()) : [];
                const codes = quote.code_ids ? quote.code_ids.split(';').map(id => id.trim()) : [];
                
                html += `
                    <div class="quote-full" id="quote-${quote.quote_id}">
                        <div class="quote-text">"${quote.text}"</div>
                        <div class="quote-attribution">
                            — <strong>${quote.speaker || 'Unknown'}</strong> (${quote.interview_id || 'Unknown Interview'})
                        </div>
                        
                        ${themes.length > 0 ? `
                            <div style="margin-top: 1rem;">
                                <strong>Themes:</strong>
                                ${themes.map(themeId => {
                                    const theme = analysisData.themes.find(t => t.theme_id === themeId);
                                    return theme ? `<span class="quote-reference" onclick="showThemeDetail('${themeId}')">${theme.name}</span>` : '';
                                }).join('')}
                            </div>
                        ` : ''}
                        
                        ${codes.length > 0 ? `
                            <div style="margin-top: 0.5rem;">
                                <strong>Codes:</strong>
                                ${codes.map(codeId => `
                                    <span class="quote-reference" onclick="showCodeDetail('${codeId}')">${codeId}</span>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            html += '</div>';
            
            content.innerHTML = html;
        }

        // Advanced analysis with all data
        function renderAdvancedAnalysis() {
            const content = document.getElementById('content');
            
            let html = '<h1>Advanced Analysis Dashboard</h1>';
            
            // Theme analysis
            if (analysisData.theme_analysis && analysisData.theme_analysis.length > 0) {
                html += '<h2>Theme Analysis</h2>';
                html += '<table class="data-table">';
                html += '<thead><tr>';
                const headers = Object.keys(analysisData.theme_analysis[0]);
                headers.forEach(header => {
                    html += `<th>${header.replace(/_/g, ' ').toUpperCase()}</th>`;
                });
                html += '</tr></thead><tbody>';
                
                analysisData.theme_analysis.forEach(row => {
                    html += '<tr>';
                    headers.forEach(header => {
                        html += `<td>${row[header] || ''}</td>`;
                    });
                    html += '</tr>';
                });
                html += '</tbody></table>';
            }
            
            // Code progression
            if (analysisData.code_progression && analysisData.code_progression.length > 0) {
                html += '<h2>Code Progression Analysis</h2>';
                html += '<div class="expandable">';
                html += '<div class="expandable-header" onclick="toggleExpandable(this)">';
                html += '<span>Code Evolution Patterns</span><i class="fas fa-chevron-down"></i>';
                html += '</div>';
                html += '<div class="expandable-content">';
                html += '<table class="data-table">';
                html += '<thead><tr>';
                const progHeaders = Object.keys(analysisData.code_progression[0]);
                progHeaders.forEach(header => {
                    html += `<th>${header.replace(/_/g, ' ').toUpperCase()}</th>`;
                });
                html += '</tr></thead><tbody>';
                
                analysisData.code_progression.forEach(row => {
                    html += '<tr>';
                    progHeaders.forEach(header => {
                        html += `<td>${row[header] || ''}</td>`;
                    });
                    html += '</tr>';
                });
                html += '</tbody></table>';
                html += '</div></div>';
            }
            
            content.innerHTML = html;
        }

        // Complete data browser
        function renderCompleteData() {
            const content = document.getElementById('content');
            
            let html = '<h1>Complete Dataset Browser</h1>';
            
            const datasets = [
                {name: 'Themes', data: analysisData.themes, key: 'themes'},
                {name: 'Codes', data: analysisData.codes, key: 'codes'},
                {name: 'Quotes', data: analysisData.quotes, key: 'quotes'},
                {name: 'Quote Evidence', data: analysisData.quote_evidence, key: 'quote_evidence'},
                {name: 'Theme Analysis', data: analysisData.theme_analysis, key: 'theme_analysis'},
                {name: 'Code Progression', data: analysisData.code_progression, key: 'code_progression'},
                {name: 'Contradiction Matrix', data: analysisData.contradiction_matrix, key: 'contradiction_matrix'},
                {name: 'Saturation Analysis', data: analysisData.saturation_analysis, key: 'saturation_analysis'},
                {name: 'Quote Chains', data: analysisData.quote_chains, key: 'quote_chains'}
            ];
            
            datasets.forEach(dataset => {
                if (dataset.data && dataset.data.length > 0) {
                    html += `
                        <div class="expandable">
                            <div class="expandable-header" onclick="toggleExpandable(this)">
                                <span>${dataset.name} (${dataset.data.length} entries)</span>
                                <i class="fas fa-chevron-down"></i>
                            </div>
                            <div class="expandable-content">
                                <table class="data-table">
                                    <thead><tr>
                                        ${Object.keys(dataset.data[0]).map(key => 
                                            `<th>${key.replace(/_/g, ' ').toUpperCase()}</th>`
                                        ).join('')}
                                    </tr></thead>
                                    <tbody>
                                        ${dataset.data.slice(0, 50).map(row => `
                                            <tr>
                                                ${Object.keys(row).map(key => 
                                                    `<td>${String(row[key] || '').substring(0, 200)}${String(row[key] || '').length > 200 ? '...' : ''}</td>`
                                                ).join('')}
                                            </tr>
                                        `).join('')}
                                        ${dataset.data.length > 50 ? `<tr><td colspan="${Object.keys(dataset.data[0]).length}"><em>... ${dataset.data.length - 50} more entries</em></td></tr>` : ''}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    `;
                }
            });
            
            content.innerHTML = html;
        }

        // Export functionality
        function renderExport() {
            const content = document.getElementById('content');
            
            let html = '<h1>Export Complete Dataset</h1>';
            html += '<div class="card">';
            html += '<h3>Export Options</h3>';
            html += '<p>Download the complete analysis dataset in various formats:</p>';
            
            html += '<div style="margin-top: 2rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">';
            html += '<button class="btn btn-primary" onclick="exportJSON()"><i class="fas fa-file-code"></i> Complete JSON</button>';
            html += '<button class="btn btn-primary" onclick="exportCSV(\\'themes\\')"><i class="fas fa-file-csv"></i> Themes CSV</button>';
            html += '<button class="btn btn-primary" onclick="exportCSV(\\'codes\\')"><i class="fas fa-file-csv"></i> Codes CSV</button>';
            html += '<button class="btn btn-primary" onclick="exportCSV(\\'quotes\\')"><i class="fas fa-file-csv"></i> Quotes CSV</button>';
            html += '<button class="btn btn-primary" onclick="exportAllCSV()"><i class="fas fa-archive"></i> All CSV Files</button>';
            html += '<button class="btn btn-primary" onclick="printReport()"><i class="fas fa-print"></i> Print Report</button>';
            html += '</div>';
            html += '</div>';
            
            content.innerHTML = html;
        }

        // Helper functions
        function toggleExpandable(header) {
            const expandable = header.closest('.expandable');
            expandable.classList.toggle('active');
            const icon = header.querySelector('i');
            icon.classList.toggle('fa-chevron-down');
            icon.classList.toggle('fa-chevron-up');
        }

        function showQuoteDetail(quoteId) {
            const quote = analysisData.quotes.find(q => q.quote_id === quoteId);
            if (quote) {
                showTab('quotes');
                setTimeout(() => {
                    const element = document.getElementById(`quote-${quoteId}`);
                    if (element) {
                        element.scrollIntoView({behavior: 'smooth'});
                        element.style.backgroundColor = '#fef3c7';
                        setTimeout(() => {
                            element.style.backgroundColor = '';
                        }, 2000);
                    }
                }, 200);
            }
        }

        function showThemeDetail(themeId) {
            selectedTheme = themeId;
            showTab('themes');
        }

        function showCodeDetail(codeId) {
            selectedCode = codeId;
            showTab('codes');
        }

        // Export functions
        function exportJSON() {
            const dataStr = JSON.stringify(analysisData, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', 'comprehensive_qualitative_analysis.json');
            linkElement.click();
        }

        function exportCSV(type) {
            let csv = '';
            let filename = '';
            
            const data = analysisData[type];
            if (data && data.length > 0) {
                const headers = Object.keys(data[0]);
                csv = headers.join(',') + '\\n';
                
                data.forEach(row => {
                    csv += headers.map(header => `"${String(row[header] || '').replace(/"/g, '""')}"`).join(',') + '\\n';
                });
                
                filename = `${type}_comprehensive.csv`;
            }
            
            if (csv) {
                const dataUri = 'data:text/csv;charset=utf-8,'+ encodeURIComponent(csv);
                const linkElement = document.createElement('a');
                linkElement.setAttribute('href', dataUri);
                linkElement.setAttribute('download', filename);
                linkElement.click();
            }
        }

        function exportAllCSV() {
            ['themes', 'codes', 'quotes', 'quote_evidence', 'theme_analysis', 'code_progression'].forEach(type => {
                setTimeout(() => exportCSV(type), 100);
            });
        }

        function printReport() {
            window.print();
        }

        // Filter functions
        function filterThemes(searchValue) {
            const themes = document.querySelectorAll('#themes-list .expandable');
            themes.forEach(theme => {
                const text = theme.textContent.toLowerCase();
                theme.style.display = text.includes(searchValue.toLowerCase()) ? 'block' : 'none';
            });
        }

        function filterCodes(searchValue) {
            const codes = document.querySelectorAll('#codes-list > div');
            codes.forEach(code => {
                const text = code.textContent.toLowerCase();
                code.style.display = text.includes(searchValue.toLowerCase()) ? 'block' : 'none';
            });
        }

        function filterQuotes(searchValue) {
            const quotes = document.querySelectorAll('#quotes-list .quote-full');
            quotes.forEach(quote => {
                const text = quote.textContent.toLowerCase();
                quote.style.display = text.includes(searchValue.toLowerCase()) ? 'block' : 'none';
            });
        }
        '''

def main():
    """Main function to generate comprehensive webpage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate comprehensive qualitative analysis webpage with full data integration')
    parser.add_argument('--input', required=True, help='Input directory containing complete analysis results')
    parser.add_argument('--output', default='comprehensive_qualitative_analysis.html', help='Output HTML file')
    
    args = parser.parse_args()
    
    # Create generator
    generator = ComprehensiveWebpageGenerator(args.input)
    
    # Load all data
    generator.load_all_data()
    
    # Generate comprehensive HTML
    generator.generate_html(args.output)

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Script to create a self-contained HTML webpage with all qualitative coding data embedded.
This creates a single file that can be emailed or shared without needing a server.
"""

import os
import csv
import json
from pathlib import Path
import base64
from datetime import datetime

class WebpageGenerator:
    def __init__(self, data_dir: str, template_file: str = None):
        self.data_dir = Path(data_dir)
        self.template_file = template_file
        self.data = {
            'themes': [],
            'codes': [],
            'quotes': [],
            'metadata': {},
            'summary': {},
            'analysis': {}
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
        print("Loading data files...")
        
        # Load CSVs
        self.data['themes'] = self.load_csv('themes.csv')
        self.data['codes'] = self.load_csv('codes.csv')
        self.data['quotes'] = self.load_csv('quote_evidence.csv')
        self.data['theme_analysis'] = self.load_csv('theme_analysis.csv')
        self.data['code_progression'] = self.load_csv('code_progression.csv')
        self.data['contradiction_matrix'] = self.load_csv('contradiction_matrix.csv')
        self.data['stakeholder_positions'] = self.load_csv('stakeholder_positions.csv')
        self.data['saturation_analysis'] = self.load_csv('saturation_analysis.csv')
        self.data['quote_chains'] = self.load_csv('quote_chains.csv')
        
        # Load JSON files
        self.data['full_analysis'] = self.load_json('full_analysis.json')
        self.data['metadata'] = self.load_json('metadata.json')
        self.data['quote_inventory'] = self.load_json('quote_inventory.json')
        
        # Load summary
        summary_text = self.load_text('SUMMARY.txt')
        if summary_text:
            self.parse_summary(summary_text)
        
        print(f"Loaded {len(self.data['themes'])} themes, {len(self.data['codes'])} codes, {len(self.data['quotes'])} quotes")
    
    def parse_summary(self, summary_text: str):
        """Parse the SUMMARY.txt file to extract key statistics."""
        lines = summary_text.split('\n')
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
        """Generate the self-contained HTML file with embedded data."""
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qualitative Coding Analysis - {title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* Embedded CSS */
        {css_content}
    </style>
</head>
<body>
    <!-- Navigation -->
    <div class="nav-tabs">
        <div class="nav-tab active" onclick="showTab('overview')">
            <i class="fas fa-home"></i> Overview
        </div>
        <div class="nav-tab" onclick="showTab('themes')">
            <i class="fas fa-layer-group"></i> Themes ({theme_count})
        </div>
        <div class="nav-tab" onclick="showTab('codes')">
            <i class="fas fa-tags"></i> Codes ({code_count})
        </div>
        <div class="nav-tab" onclick="showTab('quotes')">
            <i class="fas fa-quote-right"></i> Quotes ({quote_count})
        </div>
        <div class="nav-tab" onclick="showTab('analysis')">
            <i class="fas fa-chart-bar"></i> Analysis
        </div>
        <div class="nav-tab" onclick="showTab('export')">
            <i class="fas fa-download"></i> Export
        </div>
    </div>

    <div class="container">
        <!-- Content will be dynamically generated -->
        <div id="content"></div>
    </div>

    <script>
        // Embedded data
        const analysisData = {data_json};
        
        // Embedded JavaScript
        {js_content}
    </script>
</body>
</html>'''
        
        # Load CSS content
        css_content = self.get_css_content()
        
        # Load JavaScript content
        js_content = self.get_js_content()
        
        # Prepare data
        data_json = json.dumps(self.data, indent=2)
        
        # Get counts for navigation
        theme_count = len(self.data['themes'])
        code_count = len(self.data['codes'])
        quote_count = len(self.data['quotes'])
        
        # Generate final HTML
        html = html_template.format(
            title=self.data['summary'].get('research_question', 'Qualitative Analysis'),
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
        print(f"\nGenerated {output_file}")
        print(f"File size: {file_size:.2f} MB")
        print(f"This file can be opened directly in a web browser or emailed as an attachment.")
    
    def get_css_content(self) -> str:
        """Return the CSS content for the webpage."""
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
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Navigation */
        .nav-tabs {
            display: flex;
            background: white;
            border-bottom: 2px solid var(--border);
            padding: 0 1rem;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .nav-tab {
            padding: 1rem 1.5rem;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
            font-weight: 500;
            color: #6b7280;
        }

        .nav-tab:hover {
            color: var(--primary);
        }

        .nav-tab.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
        }

        /* Stats */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

        /* Data tables */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
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
        }

        .data-table tr:hover {
            background: var(--light);
        }

        /* Cards */
        .card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Quotes */
        .quote-card {
            background: white;
            border-left: 4px solid var(--primary);
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 6px 6px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: all 0.2s;
        }

        .quote-card:hover {
            transform: translateX(4px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }

        .quote-text {
            font-style: italic;
            margin-bottom: 0.5rem;
        }

        .quote-meta {
            font-size: 14px;
            color: #6b7280;
        }

        /* Tags */
        .tag {
            display: inline-block;
            padding: 4px 12px;
            margin: 2px;
            background: var(--light);
            border: 1px solid var(--border);
            border-radius: 20px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .tag:hover {
            background: var(--primary);
            color: white;
            transform: scale(1.05);
        }

        .tag-theme {
            background: #dbeafe;
            border-color: var(--primary);
        }

        .tag-code {
            background: #d1fae5;
            border-color: var(--secondary);
        }

        /* Search */
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

        /* Buttons */
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background: var(--primary);
            color: white;
        }

        .btn-primary:hover {
            background: #1d4ed8;
            transform: translateY(-1px);
        }

        /* Tooltips */
        [data-tooltip] {
            position: relative;
            cursor: help;
            border-bottom: 2px dotted var(--primary);
        }

        [data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background: var(--dark);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
            white-space: nowrap;
            z-index: 1000;
            max-width: 300px;
        }

        /* Expandable */
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

        /* Loading */
        .loading {
            text-align: center;
            padding: 3rem;
            color: #6b7280;
        }

        .spinner {
            border: 3px solid var(--light);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        '''
    
    def get_js_content(self) -> str:
        """Return the JavaScript content for the webpage."""
        return '''
        // Global state
        let currentTab = 'overview';
        let searchTerm = '';

        // Initialize on load
        document.addEventListener('DOMContentLoaded', function() {
            showTab('overview');
        });

        // Tab navigation
        function showTab(tabName) {
            currentTab = tabName;
            
            // Update active tab
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target?.classList.add('active') || 
                document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
            
            // Render content
            const content = document.getElementById('content');
            content.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading...</p></div>';
            
            // Small delay for loading animation
            setTimeout(() => {
                switch(tabName) {
                    case 'overview':
                        renderOverview();
                        break;
                    case 'themes':
                        renderThemes();
                        break;
                    case 'codes':
                        renderCodes();
                        break;
                    case 'quotes':
                        renderQuotes();
                        break;
                    case 'analysis':
                        renderAnalysis();
                        break;
                    case 'export':
                        renderExport();
                        break;
                }
            }, 100);
        }

        // Render overview
        function renderOverview() {
            const summary = analysisData.summary;
            const content = document.getElementById('content');
            
            content.innerHTML = `
                <h1>Qualitative Coding Analysis</h1>
                <p style="font-size: 18px; color: #6b7280; margin-bottom: 2rem;">
                    ${summary.research_question || 'Research Question Not Found'}
                </p>
                
                <div class="stats-grid">
                    <div class="stat-card" onclick="showTab('themes')">
                        <i class="fas fa-layer-group" style="font-size: 2rem; color: var(--primary); margin-bottom: 0.5rem;"></i>
                        <div class="stat-value">${analysisData.themes.length}</div>
                        <div class="stat-label">Themes</div>
                    </div>
                    
                    <div class="stat-card" onclick="showTab('codes')">
                        <i class="fas fa-tags" style="font-size: 2rem; color: var(--secondary); margin-bottom: 0.5rem;"></i>
                        <div class="stat-value">${analysisData.codes.length}</div>
                        <div class="stat-label">Codes</div>
                    </div>
                    
                    <div class="stat-card" onclick="showTab('quotes')">
                        <i class="fas fa-quote-right" style="font-size: 2rem; color: var(--danger); margin-bottom: 0.5rem;"></i>
                        <div class="stat-value">${analysisData.quotes.length}</div>
                        <div class="stat-label">Quotes</div>
                    </div>
                    
                    <div class="stat-card">
                        <i class="fas fa-users" style="font-size: 2rem; color: var(--warning); margin-bottom: 0.5rem;"></i>
                        <div class="stat-value">${summary.interviews || '18'}</div>
                        <div class="stat-label">Interviews</div>
                    </div>
                    
                    <div class="stat-card">
                        <i class="fas fa-coins" style="font-size: 2rem; color: var(--info); margin-bottom: 0.5rem;"></i>
                        <div class="stat-value" data-tooltip="1 token ≈ 0.75 words">${summary.tokens || '0'}</div>
                        <div class="stat-label">Tokens</div>
                    </div>
                    
                    <div class="stat-card">
                        <i class="fas fa-clock" style="font-size: 2rem; color: #8b5cf6; margin-bottom: 0.5rem;"></i>
                        <div class="stat-value">${parseFloat(summary.processing_time || '0').toFixed(1)}</div>
                        <div class="stat-label">Processing (sec)</div>
                    </div>
                </div>
                
                ${summary.emergent_theory ? `
                <div class="card">
                    <h2>Emergent Theory</h2>
                    <p style="font-style: italic; line-height: 1.8;">${summary.emergent_theory}</p>
                </div>
                ` : ''}
            `;
        }

        // Render themes
        function renderThemes() {
            const content = document.getElementById('content');
            
            let html = '<h1>Themes</h1>';
            html += '<input type="text" class="search-box" placeholder="Search themes..." onkeyup="filterThemes(this.value)">';
            
            html += '<div id="themes-list">';
            analysisData.themes.forEach(theme => {
                const relatedCodes = analysisData.codes.filter(c => c.theme_id === theme.theme_id);
                const prevalence = parseFloat(theme.prevalence || 0) * 100;
                
                html += `
                    <div class="expandable" data-theme="${theme.theme_id}">
                        <div class="expandable-header" onclick="toggleExpandable(this)">
                            <div>
                                <h3>${theme.name}</h3>
                                <p style="margin-top: 0.5rem;">
                                    <span class="tag">Prevalence: ${prevalence.toFixed(0)}%</span>
                                    <span class="tag">${theme.interview_count || 0} interviews</span>
                                    <span class="tag">${relatedCodes.length} codes</span>
                                </p>
                            </div>
                            <i class="fas fa-chevron-down"></i>
                        </div>
                        <div class="expandable-content">
                            <h4>Related Codes</h4>
                            <div style="margin: 1rem 0;">
                                ${relatedCodes.map(code => `
                                    <span class="tag tag-code" onclick="showCode('${code.code_id}')">
                                        ${code.name} (${code.frequency || 0})
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            
            content.innerHTML = html;
        }

        // Render codes
        function renderCodes() {
            const content = document.getElementById('content');
            
            let html = '<h1>Codes</h1>';
            html += '<input type="text" class="search-box" placeholder="Search codes..." onkeyup="filterCodes(this.value)">';
            
            html += '<table class="data-table" id="codes-table">';
            html += '<thead><tr>';
            html += '<th>Code ID</th><th>Name</th><th>Definition</th><th>Theme</th><th>Frequency</th>';
            html += '</tr></thead>';
            html += '<tbody>';
            
            analysisData.codes.forEach(code => {
                const theme = analysisData.themes.find(t => t.theme_id === code.theme_id);
                html += '<tr>';
                html += `<td>${code.code_id}</td>`;
                html += `<td>${code.name}</td>`;
                html += `<td>${code.definition || ''}</td>`;
                html += `<td>${theme ? theme.name : code.theme_id}</td>`;
                html += `<td>${code.frequency || 0}</td>`;
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            content.innerHTML = html;
        }

        // Render quotes
        function renderQuotes() {
            const content = document.getElementById('content');
            
            let html = '<h1>Quotes</h1>';
            html += '<input type="text" class="search-box" placeholder="Search quotes..." onkeyup="filterQuotes(this.value)">';
            
            html += '<div id="quotes-list">';
            analysisData.quotes.forEach(quote => {
                html += `
                    <div class="quote-card">
                        <p class="quote-text">"${quote.text}"</p>
                        <p class="quote-meta">
                            <strong>${quote.speaker_name || 'Unknown'}</strong> - 
                            ${quote.speaker_role || 'Unknown Role'} 
                            (${quote.interview_id || 'Unknown Interview'})
                        </p>
                        <div style="margin-top: 0.5rem;">
                            ${quote.theme_ids ? quote.theme_ids.split(';').map(id => {
                                const theme = analysisData.themes.find(t => t.theme_id === id.trim());
                                return theme ? `<span class="tag tag-theme">${theme.name}</span>` : '';
                            }).join('') : ''}
                        </div>
                        <div style="margin-top: 0.5rem;">
                            ${quote.code_ids ? quote.code_ids.split(';').map(id => {
                                const code = analysisData.codes.find(c => c.code_id === id.trim());
                                return code ? `<span class="tag tag-code">${code.name}</span>` : '';
                            }).join('') : ''}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            
            content.innerHTML = html;
        }

        // Render analysis
        function renderAnalysis() {
            const content = document.getElementById('content');
            
            let html = '<h1>Analysis & Visualizations</h1>';
            
            // Theme distribution
            html += '<div class="card">';
            html += '<h3>Theme Distribution</h3>';
            html += '<canvas id="themeChart" width="400" height="200"></canvas>';
            html += '</div>';
            
            // Code frequency
            html += '<div class="card">';
            html += '<h3>Top Codes by Frequency</h3>';
            html += '<canvas id="codeChart" width="400" height="300"></canvas>';
            html += '</div>';
            
            content.innerHTML = html;
            
            // Render charts
            setTimeout(() => {
                renderCharts();
            }, 100);
        }

        // Render export
        function renderExport() {
            const content = document.getElementById('content');
            
            let html = '<h1>Export Data</h1>';
            html += '<div class="card">';
            html += '<h3>Export Options</h3>';
            html += '<p>Click the buttons below to export data in different formats:</p>';
            
            html += '<div style="margin-top: 2rem; display: flex; flex-direction: column; gap: 1rem;">';
            html += '<button class="btn btn-primary" onclick="exportJSON()"><i class="fas fa-file-code"></i> Export as JSON</button>';
            html += '<button class="btn btn-primary" onclick="exportCSV(\'themes\')"><i class="fas fa-file-csv"></i> Export Themes CSV</button>';
            html += '<button class="btn btn-primary" onclick="exportCSV(\'codes\')"><i class="fas fa-file-csv"></i> Export Codes CSV</button>';
            html += '<button class="btn btn-primary" onclick="exportCSV(\'quotes\')"><i class="fas fa-file-csv"></i> Export Quotes CSV</button>';
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

        function filterThemes(searchValue) {
            const themes = document.querySelectorAll('#themes-list .expandable');
            themes.forEach(theme => {
                const text = theme.textContent.toLowerCase();
                theme.style.display = text.includes(searchValue.toLowerCase()) ? 'block' : 'none';
            });
        }

        function filterCodes(searchValue) {
            const rows = document.querySelectorAll('#codes-table tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchValue.toLowerCase()) ? '' : 'none';
            });
        }

        function filterQuotes(searchValue) {
            const quotes = document.querySelectorAll('#quotes-list .quote-card');
            quotes.forEach(quote => {
                const text = quote.textContent.toLowerCase();
                quote.style.display = text.includes(searchValue.toLowerCase()) ? 'block' : 'none';
            });
        }

        function renderCharts() {
            // Theme distribution pie chart
            const themeCtx = document.getElementById('themeChart').getContext('2d');
            const themeData = analysisData.themes.map(t => {
                const codeCount = analysisData.codes.filter(c => c.theme_id === t.theme_id).length;
                return {
                    label: t.name,
                    value: codeCount
                };
            });
            
            new Chart(themeCtx, {
                type: 'pie',
                data: {
                    labels: themeData.map(d => d.label),
                    datasets: [{
                        data: themeData.map(d => d.value),
                        backgroundColor: [
                            '#2563eb', '#ef4444', '#10b981', '#f59e0b', 
                            '#8b5cf6', '#06b6d4', '#ec4899', '#f97316'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            
            // Code frequency bar chart
            const codeCtx = document.getElementById('codeChart').getContext('2d');
            const topCodes = analysisData.codes
                .sort((a, b) => (b.frequency || 0) - (a.frequency || 0))
                .slice(0, 20);
            
            new Chart(codeCtx, {
                type: 'bar',
                data: {
                    labels: topCodes.map(c => c.name),
                    datasets: [{
                        label: 'Frequency',
                        data: topCodes.map(c => c.frequency || 0),
                        backgroundColor: '#2563eb'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        },
                        x: {
                            ticks: {
                                autoSkip: false,
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }
                    }
                }
            });
        }

        // Export functions
        function exportJSON() {
            const dataStr = JSON.stringify(analysisData, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            
            const exportFileDefaultName = 'qualitative_analysis.json';
            
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
        }

        function exportCSV(type) {
            let csv = '';
            let filename = '';
            
            if (type === 'themes') {
                csv = 'theme_id,name,prevalence,interview_count\\n';
                analysisData.themes.forEach(t => {
                    csv += `"${t.theme_id}","${t.name}","${t.prevalence}","${t.interview_count}"\\n`;
                });
                filename = 'themes.csv';
            } else if (type === 'codes') {
                csv = 'code_id,name,definition,theme_id,frequency\\n';
                analysisData.codes.forEach(c => {
                    csv += `"${c.code_id}","${c.name}","${c.definition || ''}","${c.theme_id}","${c.frequency || 0}"\\n`;
                });
                filename = 'codes.csv';
            } else if (type === 'quotes') {
                csv = 'quote_id,text,speaker,interview_id,themes,codes\\n';
                analysisData.quotes.forEach(q => {
                    csv += `"${q.quote_id}","${q.text}","${q.speaker_name || ''}","${q.interview_id || ''}","${q.theme_ids || ''}","${q.code_ids || ''}"\\n`;
                });
                filename = 'quotes.csv';
            }
            
            const dataUri = 'data:text/csv;charset=utf-8,'+ encodeURIComponent(csv);
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', filename);
            linkElement.click();
        }

        function printReport() {
            window.print();
        }
        '''


def main():
    """Main function to generate the webpage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate self-contained qualitative analysis webpage')
    parser.add_argument('--input', required=True, help='Input directory containing analysis results')
    parser.add_argument('--output', default='qualitative_analysis.html', help='Output HTML file')
    
    args = parser.parse_args()
    
    # Create generator
    generator = WebpageGenerator(args.input)
    
    # Load data
    generator.load_all_data()
    
    # Generate HTML
    generator.generate_html(args.output)


if __name__ == '__main__':
    main()
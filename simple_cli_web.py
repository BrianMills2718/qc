#!/usr/bin/env python3
"""
CLI-Web Integration for WSL Environment
Implements subprocess-based web UI that calls CLI commands
This resolves Windows compatibility issues by using WSL/Linux subprocess model
"""

import os
import json
import subprocess
import tempfile
from flask import Flask, request, render_template, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)
app.secret_key = 'qualitative-coding-cli-web'

# Configure upload settings
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'txt', 'docx', 'doc', 'pdf', 'rtf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def run_cli_command(command_args):
    """Execute CLI command via subprocess with proper WSL/Linux encoding"""
    try:
        # Activate virtual environment and run command
        cmd = [
            '/bin/bash', '-c', 
            'source qc_env/bin/activate && python3 qc_cli.py ' + ' '.join(command_args)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd='/home/brian/projects/qualitative_coding'
        )
        
        return {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except Exception as e:
        return {
            'returncode': 1,
            'stdout': '',
            'stderr': f'Subprocess error: {str(e)}'
        }

def parse_cli_output(cli_result):
    """Parse CLI output to extract JSON results or error messages"""
    if cli_result['returncode'] != 0:
        # Extract meaningful error from stderr
        stderr = cli_result['stderr']
        if 'You exceeded your current quota' in stderr:
            return {'error': 'OpenAI API quota exceeded. Please check your billing.', 'type': 'quota'}
        elif 'Cannot connect to API server' in stderr:
            return {'error': 'API server not running. Start with: python start_server.py', 'type': 'server'}
        else:
            return {'error': f'CLI error: {stderr}', 'type': 'cli'}
    
    # Try to parse JSON from stdout
    stdout = cli_result['stdout'].strip()
    lines = stdout.split('\n')
    
    # Look for JSON output (usually at the end)
    json_found = False
    for line in reversed(lines):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                return {'success': True, 'data': json.loads(line)}
            except json.JSONDecodeError:
                continue
    
    # No JSON found, return the full output
    return {'success': True, 'data': {'output': stdout, 'raw': True}}

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Qualitative Coding Analysis - CLI Web Interface</title>
        <style>
            body { font-family: Arial; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select { padding: 8px; margin: 5px 0; width: 100%; max-width: 400px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a8a; }
            .error { color: red; background: #ffebee; padding: 10px; border-radius: 4px; margin: 10px 0; }
            .info { color: #1976d2; background: #e3f2fd; padding: 10px; border-radius: 4px; margin: 10px 0; }
            .server-status { text-align: center; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Qualitative Coding Analysis</h1>
            <p><strong>CLI-Web Integration for WSL Environment</strong></p>
            
            <div class="server-status">
                <p><em>This interface calls CLI commands via subprocess - perfect for WSL/Linux!</em></p>
                <p><strong>Make sure the API server is running:</strong> <code>python start_server.py</code></p>
            </div>
            
            <form action="/upload" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="files">Select interview files (.txt, .docx, .pdf, .rtf):</label>
                    <input type="file" name="files" multiple accept=".txt,.docx,.doc,.pdf,.rtf" required>
                </div>
                
                <div class="form-group">
                    <label for="format">Output format:</label>
                    <select name="format">
                        <option value="human">Human readable</option>
                        <option value="json">JSON</option>
                    </select>
                </div>
                
                <button type="submit">Analyze Files</button>
            </form>
            
            <hr>
            <h3>Test Files Available:</h3>
            <p>Use the africa interview corpus at: <code>/home/brian/projects/qualitative_coding/data/interviews/africa_3_interviews_for_test/</code></p>
            <ul>
                <li>Chris Runyon.docx</li>
                <li>Aristide Kanga notes.docx</li>
                <li>ALFS France notes.docx</li>
            </ul>
        </div>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        # Get uploaded files
        files = request.files.getlist('files')
        format_choice = request.form.get('format', 'human')
        
        if not files or all(f.filename == '' for f in files):
            return f'''
            <div class="error">No files selected</div>
            <a href="/">← Back to upload</a>
            '''
        
        # Save uploaded files to WSL filesystem
        file_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                file_paths.append(file_path)
        
        if not file_paths:
            return f'''
            <div class="error">No valid files uploaded</div>
            <a href="/">← Back to upload</a>
            '''
        
        # Generate unique session ID for tracking
        import uuid
        session_id = str(uuid.uuid4())[:8]
        
        # Return progress page that will start analysis
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Qualitative Analysis in Progress</title>
            <style>
                body {{ font-family: Arial; margin: 40px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 8px; max-width: 800px; margin: 0 auto; }}
                .progress-bar {{ width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; margin: 20px 0; }}
                .progress-fill {{ height: 100%; background: linear-gradient(90deg, #4CAF50, #2196F3); border-radius: 10px; transition: width 0.5s ease; }}
                .phase {{ margin: 15px 0; padding: 15px; border-radius: 8px; background: #f9f9f9; }}
                .phase.active {{ background: #e3f2fd; border-left: 4px solid #2196F3; }}
                .phase.completed {{ background: #e8f5e9; border-left: 4px solid #4CAF50; }}
                .phase.pending {{ background: #f5f5f5; border-left: 4px solid #ccc; }}
                .spinner {{ display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                .status {{ font-size: 18px; margin: 20px 0; text-align: center; }}
                .file-list {{ background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .eta {{ color: #666; font-style: italic; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🧠 Qualitative Coding Analysis in Progress</h1>
                
                <div class="status" id="status">
                    <span class="spinner"></span> Starting comprehensive analysis...
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill" id="progress" style="width: 0%"></div>
                </div>
                
                <div class="eta" id="eta">Estimated time: 5-10 minutes for comprehensive analysis</div>
                
                <div class="file-list">
                    <strong>Files being analyzed:</strong>
                    <ul>
                        {''.join([f"<li>{os.path.basename(f)}</li>" for f in file_paths])}
                    </ul>
                </div>
                
                <div id="phases">
                    <div class="phase pending" id="phase1">
                        <strong>Phase 1:</strong> Hierarchical Code Discovery
                        <div>Identifying major themes and creating code taxonomy</div>
                    </div>
                    <div class="phase pending" id="phase2">
                        <strong>Phase 2:</strong> Participant Perspective Analysis
                        <div>Analyzing different viewpoints and speaker characteristics</div>
                    </div>
                    <div class="phase pending" id="phase3">
                        <strong>Phase 3:</strong> Entity and Relationship Mapping
                        <div>Mapping concepts, organizations, and their relationships</div>
                    </div>
                    <div class="phase pending" id="phase4">
                        <strong>Phase 4:</strong> Synthesis and Recommendations
                        <div>Final integration and actionable insights</div>
                    </div>
                </div>
                
                <div id="results" style="display: none;"></div>
            </div>
            
            <script>
                let startTime = Date.now();
                let currentPhase = 0;
                let jobId = '';
                
                // Start analysis
                startAnalysis();
                
                async function startAnalysis() {{
                    try {{
                        const response = await fetch('/start_analysis', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                files: {json.dumps([os.path.basename(f) for f in file_paths])},
                                format: '{format_choice}',
                                session_id: '{session_id}'
                            }})
                        }});
                        
                        const data = await response.json();
                        if (data.job_id) {{
                            jobId = data.job_id;
                            monitorProgress();
                        }} else {{
                            showError('Failed to start analysis: ' + (data.error || 'Unknown error'));
                        }}
                    }} catch (error) {{
                        showError('Error starting analysis: ' + error.message);
                    }}
                }}
                
                async function monitorProgress() {{
                    const interval = setInterval(async () => {{
                        try {{
                            const response = await fetch(`/job_status/${{jobId}}`);
                            const data = await response.json();
                            
                            updateProgress(data);
                            
                            if (data.status === 'completed') {{
                                clearInterval(interval);
                                showResults(data);
                            }} else if (data.status === 'failed') {{
                                clearInterval(interval);
                                showError(data.error || 'Analysis failed');
                            }}
                        }} catch (error) {{
                            console.error('Progress monitoring error:', error);
                        }}
                    }}, 2000); // Check every 2 seconds
                }}
                
                function updateProgress(data) {{
                    const elapsed = Math.round((Date.now() - startTime) / 1000);
                    const elapsedMin = Math.floor(elapsed / 60);
                    const elapsedSec = elapsed % 60;
                    
                    // Update status based on server logs or phase detection
                    let statusText = 'Processing...';
                    let progress = 10; // Base progress
                    
                    if (data.status === 'processing') {{
                        // Estimate progress based on time elapsed
                        const estimatedTotal = 300; // 5 minutes
                        progress = Math.min(90, (elapsed / estimatedTotal) * 100);
                        
                        // Update phases based on time
                        if (elapsed > 30) {{ setPhaseActive(1); progress = Math.max(25, progress); }}
                        if (elapsed > 90) {{ setPhaseCompleted(1); setPhaseActive(2); progress = Math.max(50, progress); }}
                        if (elapsed > 150) {{ setPhaseCompleted(2); setPhaseActive(3); progress = Math.max(75, progress); }}
                        if (elapsed > 210) {{ setPhaseCompleted(3); setPhaseActive(4); progress = Math.max(85, progress); }}
                        
                        statusText = `Running comprehensive analysis... (${{elapsedMin}}m ${{elapsedSec}}s elapsed)`;
                    }}
                    
                    document.getElementById('status').innerHTML = 
                        '<span class="spinner"></span> ' + statusText;
                    document.getElementById('progress').style.width = progress + '%';
                }}
                
                function setPhaseActive(phaseNum) {{
                    const phase = document.getElementById('phase' + phaseNum);
                    if (phase && !phase.classList.contains('completed')) {{
                        phase.className = 'phase active';
                    }}
                }}
                
                function setPhaseCompleted(phaseNum) {{
                    const phase = document.getElementById('phase' + phaseNum);
                    if (phase) {{
                        phase.className = 'phase completed';
                    }}
                }}
                
                function showResults(data) {{
                    // Mark all phases complete
                    for (let i = 1; i <= 4; i++) {{
                        setPhaseCompleted(i);
                    }}
                    
                    document.getElementById('progress').style.width = '100%';
                    document.getElementById('status').innerHTML = '✅ Analysis Complete!';
                    
                    // Redirect to results page
                    window.location.href = `/results/${{jobId}}`;
                }}
                
                function showError(message) {{
                    document.getElementById('status').innerHTML = '❌ ' + message;
                    document.getElementById('eta').innerHTML = '<a href="/">← Try again</a>';
                }}
            </script>
        </body>
        </html>
        '''
        
    except Exception as e:
        return f'''
        <div class="error">Unexpected error: {str(e)}</div>
        <a href="/">← Back to upload</a>
        '''

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    """Start analysis via API and return job ID"""
    try:
        data = request.get_json()
        files = data.get('files', [])
        format_choice = data.get('format', 'human')
        session_id = data.get('session_id', '')
        
        # Build file paths
        file_paths = [os.path.join(UPLOAD_FOLDER, f) for f in files]
        
        # Start analysis by calling API server directly (not CLI)
        import requests
        
        # Prepare interview data for API
        interviews = []
        for file_path in file_paths:
            try:
                # Read file content
                if file_path.endswith('.docx'):
                    from docx import Document
                    doc = Document(file_path)
                    content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                elif file_path.endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                interviews.append({
                    'name': os.path.basename(file_path),
                    'content': content
                })
            except Exception as e:
                return jsonify({'error': f'Error reading file {file_path}: {str(e)}'})
        
        # Call API server directly
        api_payload = {
            'interviews': interviews,
            'config': {'format': format_choice}
        }
        
        response = requests.post('http://127.0.0.1:8002/analyze', json=api_payload)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({'job_id': result.get('job_id'), 'status': 'started'})
        else:
            return jsonify({'error': f'API server error: {response.status_code} - {response.text}'})
            
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/job_status/<job_id>')
def job_status(job_id):
    """Get job status from API server"""
    try:
        import requests
        response = requests.get(f'http://127.0.0.1:8002/jobs/{job_id}')
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'status': 'unknown', 'error': f'API returned {response.status_code}'})
    except Exception as e:
        return jsonify({'status': 'unknown', 'error': str(e)})

@app.route('/results/<job_id>')
def show_results(job_id):
    """Display formatted results page"""
    try:
        import requests
        response = requests.get(f'http://127.0.0.1:8002/jobs/{job_id}')
        if response.status_code != 200:
            return f'''
            <div class="error">Could not retrieve results for job {job_id}</div>
            <a href="/">← Back to upload</a>
            '''
        
        job_data = response.json()
        if job_data.get('status') != 'completed':
            return f'''
            <div class="error">Analysis not completed yet. Status: {job_data.get('status', 'unknown')}</div>
            <a href="/">← Back to upload</a>
            '''
        
        detailed_results = job_data.get('results', {})
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis Results</title>
            <style>
                body {{ font-family: Arial; margin: 40px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 8px; max-width: 1200px; margin: 0 auto; }}
                .success {{ color: green; background: #e8f5e9; padding: 15px; border-radius: 4px; margin: 10px 0; }}
                .results {{ background: #f5f5f5; padding: 20px; border-radius: 4px; margin: 15px 0; }}
                .themes {{ background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 15px 0; }}
                .recommendations {{ background: #f3e5f5; padding: 15px; border-radius: 4px; margin: 15px 0; }}
                .section {{ margin: 20px 0; }}
                .full-analysis {{ background: #fafafa; padding: 20px; border-radius: 4px; margin: 15px 0; white-space: pre-wrap; font-family: Georgia, serif; line-height: 1.6; max-height: 400px; overflow-y: auto; }}
                .code-list {{ list-style-type: none; padding: 0; }}
                .code-item {{ background: #e8f5e9; margin: 5px 0; padding: 8px; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Comprehensive Qualitative Coding Results</h1>
                
                <div class="success">✅ 4-Phase qualitative coding analysis completed successfully!</div>
                
                <div class="section">
                    <h3>📈 Analysis Summary:</h3>
                    <div class="results">
                        <p><strong>Total Interviews:</strong> {detailed_results.get('total_interviews', 'N/A')}</p>
                        <p><strong>Processing Time:</strong> {detailed_results.get('processing_time_seconds', 'N/A')} seconds</p>
                        <p><strong>Model Used:</strong> {detailed_results.get('model_used', 'N/A')}</p>
                        <p><strong>Demo Mode:</strong> {'❌ No (Real Analysis)' if not detailed_results.get('demo_mode', True) else '✅ Yes (Demo)'}</p>
                        <p><strong>Job ID:</strong> <code>{job_id}</code></p>
                    </div>
                </div>
                
                <div class="section">
                    <h3>🎯 Key Themes Identified:</h3>
                    <div class="themes">
                        <ul>
                            {''.join([f"<li><strong>{theme}</strong></li>" for theme in detailed_results.get('key_themes', [])])}
                        </ul>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📋 Codes Identified:</h3>
                    <div class="results">
                        <ul class="code-list">
                            {''.join([f'<li class="code-item"><strong>{code.get("code", "Unknown")}</strong> - Frequency: {code.get("frequency", 0)}, Confidence: {code.get("confidence", 0)}</li>' for code in detailed_results.get('codes_identified', [])])}
                        </ul>
                    </div>
                </div>
                
                <div class="section">
                    <h3>💡 Recommendations:</h3>
                    <div class="recommendations">
                        <ul>
                            {''.join([f"<li>{rec}</li>" for rec in detailed_results.get('recommendations', [])])}
                        </ul>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📝 Full Comprehensive Analysis:</h3>
                    <div class="full-analysis">
{detailed_results.get('full_analysis', 'No detailed analysis available')}
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="/" style="background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">← Analyze More Files</a>
                </div>
            </div>
        </body>
        </html>
        '''
        
    except Exception as e:
        return f'''
        <div class="error">Error loading results: {str(e)}</div>
        <a href="/">← Back to upload</a>
        '''

@app.route('/test')
def test_cli():
    """Test endpoint to verify CLI integration"""
    command_args = ['--help']
    cli_result = run_cli_command(command_args)
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>CLI Test</title>
        <style>
            body {{ font-family: Arial; margin: 40px; }}
            .debug {{ background: #f5f5f5; padding: 15px; font-family: monospace; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <h1>CLI Integration Test</h1>
        <h3>Command: qc_cli --help</h3>
        <div class="debug">
Return Code: {cli_result['returncode']}

STDOUT:
{cli_result['stdout']}

STDERR:
{cli_result['stderr']}
        </div>
        <a href="/">← Back to main page</a>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("=== CLI-Web Integration Server ===")
    print("Starting on http://127.0.0.1:5003")
    print("This version uses subprocess to call CLI commands")
    print("Perfect for WSL/Linux environment!")
    print("===================================")
    app.run(debug=True, host='127.0.0.1', port=5003)
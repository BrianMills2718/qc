#!/usr/bin/env python3
"""
Web UI Wrapper for QC CLI
Simple Flask web interface that wraps the working CLI commands
"""

import os
import subprocess
import json
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'qc-web-ui-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configuration
UPLOAD_FOLDER = Path('temp_uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'txt', 'docx', 'doc', 'pdf', 'rtf'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def run_cli_command(command_args):
    """Run CLI command and return result"""
    try:
        # Build full command
        cli_path = Path(__file__).parent / 'qc_cli.py'
        full_command = ['python', str(cli_path)] + command_args
        
        logger.info(f"Running CLI command: {' '.join(full_command)}")
        
        # Run command with UTF-8 encoding
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Replace invalid characters instead of failing
            cwd=Path(__file__).parent,
            timeout=300  # 5 minute timeout
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Command timed out after 5 minutes',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

@app.route('/')
def index():
    """Main dashboard"""
    # Get system status
    status_result = run_cli_command(['status'])
    
    return render_template('index.html', 
                         system_status=status_result,
                         page_title='QC Analysis Dashboard')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """File analysis page"""
    if request.method == 'GET':
        return render_template('analyze.html', page_title='File Analysis')
    
    # Handle file upload and analysis
    if 'files' not in request.files:
        flash('No files selected', 'error')
        return redirect(request.url)
    
    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        flash('No files selected', 'error')
        return redirect(request.url)
    
    uploaded_files = []
    
    # Save uploaded files
    for file in files:
        if file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            import time
            timestamp = str(int(time.time()))
            filename = f"{timestamp}_{filename}"
            filepath = UPLOAD_FOLDER / filename
            file.save(filepath)
            uploaded_files.append(str(filepath))
        else:
            flash(f'File {file.filename} has unsupported format', 'error')
    
    if not uploaded_files:
        flash('No valid files to analyze', 'error')
        return redirect(request.url)
    
    # Get output format
    output_format = request.form.get('format', 'human')
    
    # Run analysis
    cli_args = ['analyze', '--files'] + uploaded_files + ['--format', output_format]
    result = run_cli_command(cli_args)
    
    # Cleanup uploaded files
    for filepath in uploaded_files:
        try:
            os.unlink(filepath)
        except:
            pass
    
    return render_template('analyze_results.html', 
                         result=result,
                         format=output_format,
                         page_title='Analysis Results')

@app.route('/query', methods=['GET', 'POST'])
def query():
    """Query interface page"""
    if request.method == 'GET':
        return render_template('query.html', page_title='Natural Language Query')
    
    # Handle query submission
    query_text = request.form.get('query', '').strip()
    output_format = request.form.get('format', 'human')
    
    if not query_text:
        flash('Please enter a query', 'error')
        return redirect(request.url)
    
    # Run query
    cli_args = ['query', query_text, '--format', output_format]
    result = run_cli_command(cli_args)
    
    return render_template('query_results.html', 
                         result=result,
                         query=query_text,
                         format=output_format,
                         page_title='Query Results')

@app.route('/status')
def status():
    """System status page"""
    overall_status = run_cli_command(['status'])
    server_status = run_cli_command(['status', '--server'])
    
    return render_template('status.html', 
                         overall_status=overall_status,
                         server_status=server_status,
                         page_title='System Status')

@app.route('/api/status')
def api_status():
    """JSON API endpoint for status checks"""
    result = run_cli_command(['status'])
    return jsonify(result)

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """JSON API endpoint for analysis"""
    if 'files' not in request.files:
        return jsonify({'success': False, 'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    uploaded_files = []
    
    # Save files temporarily
    for file in files:
        if file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            import time
            timestamp = str(int(time.time()))
            filename = f"{timestamp}_{filename}"
            filepath = UPLOAD_FOLDER / filename
            file.save(filepath)
            uploaded_files.append(str(filepath))
    
    if not uploaded_files:
        return jsonify({'success': False, 'error': 'No valid files'}), 400
    
    # Run analysis
    output_format = request.form.get('format', 'json')
    cli_args = ['analyze', '--files'] + uploaded_files + ['--format', output_format]
    result = run_cli_command(cli_args)
    
    # Cleanup
    for filepath in uploaded_files:
        try:
            os.unlink(filepath)
        except:
            pass
    
    return jsonify(result)

@app.route('/api/query', methods=['POST'])
def api_query():
    """JSON API endpoint for queries"""
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'success': False, 'error': 'No query provided'}), 400
    
    query_text = data['query'].strip()
    output_format = data.get('format', 'json')
    
    if not query_text:
        return jsonify({'success': False, 'error': 'Empty query'}), 400
    
    # Run query
    cli_args = ['query', query_text, '--format', output_format]
    result = run_cli_command(cli_args)
    
    return jsonify(result)

if __name__ == '__main__':
    print("Starting QC Web UI...")
    print("Upload folder:", UPLOAD_FOLDER.absolute())
    print("Max file size: 50MB")
    print("Allowed extensions:", ALLOWED_EXTENSIONS)
    print()
    print("Web UI will be available at: http://127.0.0.1:5000")
    print("Dashboard: http://127.0.0.1:5000")
    print("File Analysis: http://127.0.0.1:5000/analyze")
    print("Query Interface: http://127.0.0.1:5000/query")
    print("System Status: http://127.0.0.1:5000/status")
    print()
    
    app.run(host='127.0.0.1', port=5000, debug=True)
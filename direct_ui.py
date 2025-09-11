#!/usr/bin/env python3
"""
Simple web UI that directly calls the API server.
No CLI wrapper, no subprocess - just direct API calls.
"""

import os
import sys
import time
from flask import Flask, request, render_template, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename

# Add project root to path so we can import our modules
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from qc_clean.core.cli.api_client import APIClient

app = Flask(__name__)
app.secret_key = 'qualitative-coding-ui'

# Configure upload settings
UPLOAD_FOLDER = os.path.join(project_root, 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'docx', 'doc', 'pdf', 'rtf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        # Get uploaded files
        files = request.files.getlist('files')
        format_choice = request.form.get('format', 'human')
        
        if not files or all(f.filename == '' for f in files):
            flash('No files selected')
            return redirect(url_for('index'))
        
        # Save uploaded files
        file_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                file_paths.append(file_path)
        
        if not file_paths:
            flash('No valid files uploaded')
            return redirect(url_for('index'))
        
        # Call API directly (no subprocess)
        client = APIClient()
        
        # Check if server is running
        if not client.health_check():
            flash('Analysis server is not running. Please start it with: python start_server.py')
            return redirect(url_for('index'))
        
        # Start analysis
        job_id = client.start_analysis(file_paths, {'format': format_choice})
        
        # Poll for results
        max_attempts = 30  # 60 seconds max
        for attempt in range(max_attempts):
            result = client.get_job_status(job_id)
            
            if result['status'] == 'completed':
                return render_template('results.html', 
                                     job_id=job_id,
                                     results=result['results'],
                                     files=[os.path.basename(f) for f in file_paths])
            elif result['status'] == 'failed':
                flash(f"Analysis failed: {result.get('error', 'Unknown error')}")
                return redirect(url_for('index'))
            
            time.sleep(2)  # Wait 2 seconds before next check
        
        flash('Analysis is taking too long. Please try again.')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/query')
def query_page():
    return render_template('query.html')

@app.route('/query', methods=['POST'])
def process_query():
    try:
        query = request.form.get('query', '').strip()
        format_choice = request.form.get('format', 'human')
        
        if not query:
            flash('Please enter a query')
            return redirect(url_for('query_page'))
        
        # Call API directly
        client = APIClient()
        
        # Check if server is running
        if not client.health_check():
            flash('Query server is not running. Please start it with: python start_server.py')
            return redirect(url_for('query_page'))
        
        # Execute query
        result = client.natural_language_query(query)
        
        return render_template('query_results.html', 
                             query=query,
                             results=result)
        
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('query_page'))

if __name__ == '__main__':
    print("Starting Direct UI on http://127.0.0.1:5002")
    print("Make sure the API server is running on port 8002!")
    app.run(debug=True, host='127.0.0.1', port=5002)
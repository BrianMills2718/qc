#!/usr/bin/env python3
"""
Simple Web UI - Just shows CLI commands instead of executing them
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from pathlib import Path
import os

app = Flask(__name__)
app.secret_key = 'simple-web-ui'

UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'txt', 'docx', 'doc', 'pdf', 'rtf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('simple_index.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'GET':
        return render_template('simple_analyze.html')
    
    # Handle file upload
    if 'files' not in request.files:
        flash('No files selected', 'error')
        return redirect(request.url)
    
    files = request.files.getlist('files')
    uploaded_files = []
    
    for file in files:
        if file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = UPLOAD_FOLDER / filename
            file.save(filepath)
            uploaded_files.append(filename)
    
    if not uploaded_files:
        flash('No valid files uploaded', 'error')
        return redirect(request.url)
    
    # Generate CLI commands instead of executing them
    format_choice = request.form.get('format', 'human')
    file_args = ' '.join([f'uploads/{f}' for f in uploaded_files])
    
    cli_command = f'python qc_cli.py analyze --files {file_args} --format {format_choice}'
    
    return render_template('simple_results.html', 
                         command=cli_command,
                         files=uploaded_files,
                         format=format_choice)

@app.route('/query', methods=['GET', 'POST'])
def query():
    if request.method == 'GET':
        return render_template('simple_query.html')
    
    query_text = request.form.get('query', '').strip()
    format_choice = request.form.get('format', 'human')
    
    if not query_text:
        flash('Please enter a query', 'error')
        return redirect(request.url)
    
    cli_command = f'python qc_cli.py query "{query_text}" --format {format_choice}'
    
    return render_template('simple_query_results.html',
                         command=cli_command,
                         query=query_text,
                         format=format_choice)

if __name__ == '__main__':
    print("Simple Web UI starting...")
    print("URL: http://127.0.0.1:5001")
    print()
    print("This UI shows you the CLI commands to run manually.")
    print("No subprocess complexity - just copy/paste the commands!")
    app.run(host='127.0.0.1', port=5001, debug=True)
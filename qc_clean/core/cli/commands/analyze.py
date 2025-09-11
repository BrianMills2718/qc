"""
Analyze Command Handler - File analysis through CLI
"""

import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from ..api_client import APIClient, APIClientError
from ..formatters.human_formatter import format_analysis_results
from ..formatters.json_formatter import format_json_output
from ..formatters.table_formatter import format_table_output
from ..utils.file_handler import discover_files, validate_file_formats
from ..utils.progress import ProgressIndicator

logger = logging.getLogger(__name__)


def handle_analyze_command(args) -> int:
    """Handle the analyze command"""
    
    try:
        # Initialize API client
        api_client = APIClient(base_url=args.api_url)
        
        if args.watch_job:
            return handle_watch_job(api_client, args.watch_job, args.format)
        
        # Discover files to analyze
        if args.files:
            files_to_analyze = args.files
        elif args.directory:
            files_to_analyze = discover_files(args.directory)
            if not files_to_analyze:
                print(f"No supported files found in directory: {args.directory}")
                return 1
        else:
            logger.error("No files or directory specified")
            return 1
        
        # Validate files
        try:
            validated_files = validate_file_formats(files_to_analyze)
            print(f"Found {len(validated_files)} files to analyze:")
            for file_path in validated_files:
                print(f"  - {file_path}")
            print()
        except Exception as e:
            print(f"File validation error: {e}")
            return 1
        
        # Check server connectivity
        if not api_client.health_check():
            print("❌ Cannot connect to API server.")
            print("Please start the server with: python start_server.py")
            return 1
        
        print("✅ Connected to API server")
        
        # Submit analysis
        print("📤 Submitting files for analysis...")
        try:
            job_id = api_client.start_analysis(validated_files)
            print(f"✅ Analysis submitted successfully")
            print(f"🆔 Job ID: {job_id}")
            print()
            
        except APIClientError as e:
            print(f"❌ Analysis submission failed: {e}")
            return 1
        
        # Monitor progress
        print("⏳ Monitoring analysis progress...")
        progress = ProgressIndicator("Analyzing")
        progress.start()
        
        try:
            result = api_client.wait_for_job_completion(job_id, max_wait_time=300)
            progress.stop()
            
            print("✅ Analysis completed!")
            print()
            
            # Format and display results
            if args.format == 'json':
                output = format_json_output(result)
            elif args.format == 'table':
                output = format_table_output(result)
            else:  # human format
                output = format_analysis_results(result)
            
            print(output)
            return 0
            
        except APIClientError as e:
            progress.stop()
            print(f"\n❌ Analysis failed: {e}")
            return 1
        except KeyboardInterrupt:
            progress.stop()
            print(f"\n⚠️  Analysis interrupted. Job ID: {job_id}")
            print("You can resume monitoring with: qc_cli analyze --watch-job", job_id)
            return 130
            
    except Exception as e:
        logger.error(f"Unexpected error in analyze command: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
        return 1


def handle_watch_job(api_client: APIClient, job_id: str, output_format: str) -> int:
    """Handle watching an existing job"""
    
    print(f"🔍 Checking job status: {job_id}")
    
    # Check server connectivity
    if not api_client.health_check():
        print("❌ Cannot connect to API server.")
        print("Please start the server with: python start_server.py")
        return 1
    
    print("✅ Connected to API server")
    
    try:
        # Get current status
        status_data = api_client.get_job_status(job_id)
        current_status = status_data.get('status', 'unknown')
        
        print(f"📊 Current status: {current_status}")
        
        if current_status in ['completed', 'success']:
            print("✅ Job already completed!")
            
            # Format and display results
            if output_format == 'json':
                output = format_json_output(status_data)
            elif output_format == 'table':
                output = format_table_output(status_data)
            else:  # human format
                output = format_analysis_results(status_data)
            
            print()
            print(output)
            return 0
            
        elif current_status in ['failed', 'error']:
            error_msg = status_data.get('error', 'Job failed without error message')
            print(f"❌ Job failed: {error_msg}")
            return 1
            
        else:
            # Job still running, monitor progress
            print("⏳ Job still running, monitoring progress...")
            progress = ProgressIndicator("Processing")
            progress.start()
            
            try:
                result = api_client.wait_for_job_completion(job_id, max_wait_time=300)
                progress.stop()
                
                print("✅ Job completed!")
                print()
                
                # Format and display results
                if output_format == 'json':
                    output = format_json_output(result)
                elif output_format == 'table':
                    output = format_table_output(result)
                else:  # human format
                    output = format_analysis_results(result)
                
                print(output)
                return 0
                
            except APIClientError as e:
                progress.stop()
                print(f"\n❌ Job monitoring failed: {e}")
                return 1
            except KeyboardInterrupt:
                progress.stop()
                print(f"\n⚠️  Monitoring interrupted. Job ID: {job_id}")
                print("You can resume monitoring later with the same command")
                return 130
                
    except APIClientError as e:
        print(f"❌ Error accessing job: {e}")
        return 1
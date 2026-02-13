"""
Analyze Command Handler - File analysis through CLI
"""

import logging
import sys
from ..api_client import APIClient, APIClientError
from ..formatters.human_formatter import format_analysis_results
from ..formatters.json_formatter import format_json_output
from ..formatters.table_formatter import format_table_output
from ..utils.file_handler import discover_files, validate_file_formats
from ..utils.progress import ProgressIndicator

logger = logging.getLogger(__name__)


def handle_analyze_command(args) -> int:
    """Handle the analyze command"""
    
    # Determine if we should suppress progress output for clean JSON
    quiet_mode = args.format == 'json' or hasattr(args, 'quiet') and args.quiet
    
    def output(msg, force_stderr=False):
        """Output message to stdout unless in quiet mode, or force to stderr"""
        if quiet_mode or force_stderr:
            print(msg, file=sys.stderr)
        else:
            print(msg)
    
    try:
        # Initialize API client
        api_client = APIClient(base_url=args.api_url)
        
        if args.watch_job:
            return handle_watch_job(api_client, args.watch_job, args.format, args)
        
        # Discover files to analyze
        if args.files:
            files_to_analyze = args.files
        elif args.directory:
            files_to_analyze = discover_files(args.directory)
            if not files_to_analyze:
                output(f"No supported files found in directory: {args.directory}", True)
                return 1
        else:
            logger.error("No files or directory specified")
            return 1
        
        # Validate files
        try:
            validated_files = validate_file_formats(files_to_analyze)
            output(f"Found {len(validated_files)} files to analyze:")
            for file_path in validated_files:
                output(f"  - {file_path}")
            output("")
        except Exception as e:
            output(f"File validation error: {e}", True)
            return 1
        
        # Check server connectivity
        if not api_client.health_check():
            output("❌ Cannot connect to API server.", True)
            output("Please start the server with: python start_server.py", True)
            return 1
        
        output("✅ Connected to API server")
        
        # Submit analysis
        output("📤 Submitting files for analysis...")
        try:
            job_id = api_client.start_analysis(validated_files)
            output(f"✅ Analysis submitted successfully")
            output(f"🆔 Job ID: {job_id}")
            output("")
            
        except APIClientError as e:
            output(f"❌ Analysis submission failed: {e}", True)
            return 1
        
        # Monitor progress
        output("⏳ Monitoring analysis progress...")
        progress = ProgressIndicator("Analyzing")
        if not quiet_mode:
            progress.start()
        
        try:
            result = api_client.wait_for_job_completion(job_id, max_wait_time=600)
            if not quiet_mode:
                progress.stop()
            
            output("✅ Analysis completed!")
            output("")
            
            # Format and display results
            if args.format == 'json':
                # For JSON format, output ONLY the JSON to stdout
                formatted_output = format_json_output(result)
            elif args.format == 'table':
                formatted_output = format_table_output(result)
            else:  # human format
                formatted_output = format_analysis_results(result)
            
            # Handle output file or stdout
            if hasattr(args, 'output_file') and args.output_file:
                try:
                    with open(args.output_file, 'w', encoding='utf-8') as f:
                        f.write(formatted_output)
                    output(f"✅ Results saved to: {args.output_file}")
                except Exception as e:
                    output(f"❌ Failed to save to file: {e}", True)
                    return 1
            else:
                print(formatted_output)  # Always to stdout
            
            return 0
            
        except APIClientError as e:
            if not quiet_mode:
                progress.stop()
            output(f"\n❌ Analysis failed: {e}", True)
            return 1
        except KeyboardInterrupt:
            if not quiet_mode:
                progress.stop()
            output(f"\n⚠️  Analysis interrupted. Job ID: {job_id}", True)
            output("You can resume monitoring with: qc_cli analyze --watch-job " + job_id, True)
            return 130
            
    except Exception as e:
        logger.error(f"Unexpected error in analyze command: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
        return 1


def handle_watch_job(api_client: APIClient, job_id: str, output_format: str, args=None) -> int:
    """Handle watching an existing job"""
    
    # Determine if we should suppress progress output for clean JSON
    quiet_mode = output_format == 'json' or (args and hasattr(args, 'quiet') and args.quiet)
    
    def output(msg, force_stderr=False):
        """Output message to stdout unless in quiet mode, or force to stderr"""
        if quiet_mode or force_stderr:
            print(msg, file=sys.stderr)
        else:
            print(msg)
    
    output(f"🔍 Checking job status: {job_id}")
    
    # Check server connectivity
    if not api_client.health_check():
        output("❌ Cannot connect to API server.", True)
        output("Please start the server with: python start_server.py", True)
        return 1
    
    output("✅ Connected to API server")
    
    try:
        # Get current status
        status_data = api_client.get_job_status(job_id)
        current_status = status_data.get('status', 'unknown')
        
        output(f"📊 Current status: {current_status}")
        
        if current_status in ['completed', 'success']:
            output("✅ Job already completed!")
            
            # Format and display results
            if output_format == 'json':
                # For JSON format, output ONLY the JSON to stdout
                formatted_output = format_json_output(status_data)
            elif output_format == 'table':
                formatted_output = format_table_output(status_data)
            else:  # human format
                formatted_output = format_analysis_results(status_data)
            
            # Handle output file or stdout
            if args and hasattr(args, 'output_file') and args.output_file:
                try:
                    with open(args.output_file, 'w', encoding='utf-8') as f:
                        f.write(formatted_output)
                    output(f"✅ Results saved to: {args.output_file}")
                except Exception as e:
                    output(f"❌ Failed to save to file: {e}", True)
                    return 1
            else:
                if output_format != 'json':
                    output("")  # Add spacing for non-JSON formats
                print(formatted_output)
            
            return 0
            
        elif current_status in ['failed', 'error']:
            error_msg = status_data.get('error', 'Job failed without error message')
            output(f"❌ Job failed: {error_msg}", True)
            return 1
            
        else:
            # Job still running, monitor progress
            output("⏳ Job still running, monitoring progress...")
            progress = ProgressIndicator("Processing")
            if not quiet_mode:
                progress.start()
            
            try:
                result = api_client.wait_for_job_completion(job_id, max_wait_time=600)
                if not quiet_mode:
                    progress.stop()
                
                output("✅ Job completed!")
                output("")
                
                # Format and display results
                if output_format == 'json':
                    # For JSON format, output ONLY the JSON to stdout
                    formatted_output = format_json_output(result)
                elif output_format == 'table':
                    formatted_output = format_table_output(result)
                else:  # human format
                    formatted_output = format_analysis_results(result)
                
                # Handle output file or stdout
                if args and hasattr(args, 'output_file') and args.output_file:
                    try:
                        with open(args.output_file, 'w', encoding='utf-8') as f:
                            f.write(formatted_output)
                        output(f"✅ Results saved to: {args.output_file}")
                    except Exception as e:
                        output(f"❌ Failed to save to file: {e}", True)
                        return 1
                else:
                    print(formatted_output)
                
                return 0
                
            except APIClientError as e:
                if not quiet_mode:
                    progress.stop()
                output(f"\n❌ Job monitoring failed: {e}", True)
                return 1
            except KeyboardInterrupt:
                if not quiet_mode:
                    progress.stop()
                output(f"\n⚠️  Monitoring interrupted. Job ID: {job_id}", True)
                output("You can resume monitoring later with the same command", True)
                return 130
                
    except APIClientError as e:
        output(f"❌ Error accessing job: {e}", True)
        return 1
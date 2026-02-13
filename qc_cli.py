#!/usr/bin/env python3
"""
Qualitative Coding CLI - Command Line Interface
Main entry point for command-line access to qualitative coding analysis system
"""

import argparse
import sys
import logging
import os
from pathlib import Path

# Configure console encoding for Windows compatibility
if os.name == 'nt' and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI operations"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands"""
    parser = argparse.ArgumentParser(
        prog='qc_cli',
        description='Command-line interface for qualitative coding analysis system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  qc_cli analyze --files interview1.txt interview2.docx
  qc_cli project create --name "My Study" --methodology grounded_theory
  qc_cli project run <project_id>
  qc_cli project export <project_id> --format markdown --output-file report.md
  qc_cli status --server
        """
    )
    
    # Global options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--api-url',
        default='http://127.0.0.1:8002',
        help='API server URL (default: http://127.0.0.1:8002)'
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        metavar='COMMAND'
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze interview files',
        description='Submit interview files for qualitative coding analysis'
    )
    file_group = analyze_parser.add_mutually_exclusive_group(required=True)
    file_group.add_argument(
        '--files', 
        nargs='+',
        help='List of files to analyze'
    )
    file_group.add_argument(
        '--directory',
        help='Directory containing interview files to analyze'
    )
    file_group.add_argument(
        '--watch-job',
        help='Monitor progress of existing analysis job by ID'
    )
    analyze_parser.add_argument(
        '--format',
        choices=['json', 'table', 'human'],
        default='human',
        help='Output format (default: human)'
    )
    analyze_parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress indicators (useful for JSON output)'
    )
    analyze_parser.add_argument(
        '--output-file',
        help='Save results to specific file'
    )
    
    # Status command
    status_parser = subparsers.add_parser(
        'status',
        help='Show system status',
        description='Check system health and job status'
    )
    status_parser.add_argument(
        '--job',
        help='Check status of specific job by ID'
    )
    status_parser.add_argument(
        '--server',
        action='store_true',
        help='Check server connectivity only'
    )
    
    # Server command
    server_parser = subparsers.add_parser(
        'server',
        help='Manage server instance',
        description='Start, stop, or check server status'
    )
    server_group = server_parser.add_mutually_exclusive_group(required=True)
    server_group.add_argument(
        '--start',
        action='store_true',
        help='Start the API server'
    )
    server_group.add_argument(
        '--stop',
        action='store_true',
        help='Stop the API server'
    )
    server_group.add_argument(
        '--status',
        action='store_true',
        help='Check server status'
    )
    
    # Project command
    project_parser = subparsers.add_parser(
        'project',
        help='Project management',
        description='Create, list, and manage analysis projects'
    )
    project_subparsers = project_parser.add_subparsers(
        dest='project_action',
        help='Project actions',
        metavar='ACTION'
    )

    proj_create = project_subparsers.add_parser('create', help='Create a new project')
    proj_create.add_argument('--name', required=True, help='Project name')
    proj_create.add_argument(
        '--methodology',
        choices=['default', 'thematic_analysis', 'grounded_theory'],
        default='default',
        help='Analysis methodology (default: default)'
    )

    proj_list = project_subparsers.add_parser('list', help='List all projects')

    proj_show = project_subparsers.add_parser('show', help='Show project details')
    proj_show.add_argument('project_id', help='Project ID')

    proj_add = project_subparsers.add_parser('add-docs', help='Add documents to project')
    proj_add.add_argument('project_id', help='Project ID')
    proj_add.add_argument('--files', nargs='+', help='Files to add')
    proj_add.add_argument('--directory', help='Directory of files to add')

    proj_run = project_subparsers.add_parser('run', help='Run analysis pipeline on project')
    proj_run.add_argument('project_id', help='Project ID')
    proj_run.add_argument('--model', default=None, help='LLM model to use (default: gpt-5-mini)')
    proj_run.add_argument('--review', action='store_true', help='Enable human review pauses')

    proj_export = project_subparsers.add_parser('export', help='Export project results')
    proj_export.add_argument('project_id', help='Project ID')
    proj_export.add_argument('--format', choices=['json', 'csv', 'markdown'], default='json', help='Export format (default: json)')
    proj_export.add_argument('--output-file', help='Output file path (for json/markdown)')
    proj_export.add_argument('--output-dir', help='Output directory (for csv)')

    # Review command
    review_parser = subparsers.add_parser(
        'review',
        help='Review analysis results',
        description='Review and approve/reject codes and code applications'
    )
    review_parser.add_argument('project_id', help='Project ID')
    review_parser.add_argument(
        '--approve-all',
        action='store_true',
        help='Approve all pending codes'
    )
    review_parser.add_argument(
        '--file',
        help='JSON file with review decisions'
    )

    return parser

def main() -> int:
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle no command
    if args.command is None:
        parser.print_help()
        return 1
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Import commands here to avoid circular imports
        from qc_clean.core.cli.commands.analyze import handle_analyze_command
        from qc_clean.core.cli.commands.status import handle_status_command
        from qc_clean.core.cli.commands.server import handle_server_command

        # Route to appropriate command handler
        if args.command == 'analyze':
            return handle_analyze_command(args)
        elif args.command == 'status':
            return handle_status_command(args)
        elif args.command == 'server':
            return handle_server_command(args)
        elif args.command == 'project':
            from qc_clean.core.cli.commands.project import handle_project_command
            return handle_project_command(args)
        elif args.command == 'review':
            from qc_clean.core.cli.commands.review import handle_review_command
            return handle_review_command(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
            
    except ImportError as e:
        logger.error(f"Failed to import command handler: {e}")
        logger.error("This indicates missing CLI command modules. Please check installation.")
        return 1
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
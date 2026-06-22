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
  qc_cli bench <project_id>
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

    # Bench command
    bench_parser = subparsers.add_parser(
        'bench',
        help='Run evaluation-harness Phase 0 scorecard',
        description='Emit the deterministic Phase 0 benchmark scorecard for a project'
    )
    bench_parser.add_argument('project_id', help='Project ID to score')
    bench_parser.add_argument(
        '--d3-gold-file',
        help='Optional D3 application-validity gold JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--gold-file',
        help='Optional D7 disconfirmation gold JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--d7-baselines-file',
        help='Optional D7 baseline prediction JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--prompt-injection-file',
        help='Optional INV-7 prompt-injection fixture results JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--bias-counterfactual-file',
        help='Optional D6 counterfactual identity-swap outcome JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--codebook-quality-file',
        help='Optional D4 codebook-quality rubric outcome JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--gt-fidelity-file',
        help='Optional D8 GT-fidelity rubric outcome JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--interpretive-preference-file',
        help='Optional D9 blind forced-choice preference outcome JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--confidence-calibration-file',
        help='Optional confidence/correctness calibration JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--observability-db',
        help='Optional llm_client observability SQLite DB for D10 cost/latency'
    )
    bench_parser.add_argument(
        '--trace-id',
        help='Optional exact trace_id for D10 cost/latency; default uses project trace prefix'
    )
    bench_parser.add_argument('--output', help='Optional path to write the JSON scorecard')
    bench_parser.add_argument(
        '--artifact-dir',
        help='Optional root directory for a versioned Phase 0 benchmark artifact package'
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
    proj_create.add_argument('--phenomenon', help='Phenomenon or topic the analysis is scoped to')
    proj_create.add_argument('--population', help='Population or case universe claims may apply to')
    proj_create.add_argument('--sampling-frame', dest='sampling_frame', help='How documents/participants were selected')
    proj_create.add_argument(
        '--include',
        dest='inclusion_criteria',
        action='append',
        help='Inclusion criterion; repeat for multiple criteria',
    )
    proj_create.add_argument(
        '--exclude',
        dest='exclusion_criteria',
        action='append',
        help='Exclusion criterion; repeat for multiple criteria',
    )
    proj_create.add_argument('--notes', help='Additional scope caveats or notes')

    proj_list = project_subparsers.add_parser('list', help='List all projects')

    proj_show = project_subparsers.add_parser('show', help='Show project details')
    proj_show.add_argument('project_id', help='Project ID')

    proj_claims = project_subparsers.add_parser('claims', help='Show project claim ledger')
    proj_claims.add_argument('project_id', help='Project ID')
    proj_claims.add_argument('--limit', type=int, default=20, help='Maximum claims to show (default: 20)')

    proj_scope = project_subparsers.add_parser('scope', help='Show or update project corpus scope')
    proj_scope.add_argument('project_id', help='Project ID')
    proj_scope.add_argument('--phenomenon', help='Phenomenon or topic the analysis is scoped to')
    proj_scope.add_argument('--population', help='Population or case universe claims may apply to')
    proj_scope.add_argument('--sampling-frame', dest='sampling_frame', help='How documents/participants were selected')
    proj_scope.add_argument(
        '--include',
        dest='inclusion_criteria',
        action='append',
        help='Inclusion criterion; repeat for multiple criteria',
    )
    proj_scope.add_argument(
        '--exclude',
        dest='exclusion_criteria',
        action='append',
        help='Exclusion criterion; repeat for multiple criteria',
    )
    proj_scope.add_argument('--notes', help='Additional scope caveats or notes')

    proj_add = project_subparsers.add_parser('add-docs', help='Add documents to project')
    proj_add.add_argument('project_id', help='Project ID')
    proj_add.add_argument('--files', nargs='+', help='Files to add')
    proj_add.add_argument('--directory', help='Directory of files to add')

    proj_run = project_subparsers.add_parser('run', help='Run analysis pipeline on project')
    proj_run.add_argument('project_id', help='Project ID')
    proj_run.add_argument('--model', default=None, help='LLM model to use (default: gpt-5-mini)')
    proj_run.add_argument('--review', action='store_true', help='Enable human review pauses')
    proj_run.add_argument('--exhaustive', action='store_true',
                          help='Code every segment (examined-and-judged coverage, INV-8) instead of surfacing example quotes')

    proj_export = project_subparsers.add_parser('export', help='Export project results')
    proj_export.add_argument('project_id', help='Project ID')
    proj_export.add_argument('--format', choices=['json', 'csv', 'markdown', 'qdpx'], default='json', help='Export format (default: json)')
    proj_export.add_argument('--output-file', help='Output file path (for json/markdown/qdpx)')
    proj_export.add_argument('--output-dir', help='Output directory (for csv)')
    proj_export.add_argument('--audit-manifest', help='Optional export audit manifest output path')
    proj_export.add_argument(
        '--verify-audit-manifest',
        action='store_true',
        help='Immediately verify the written audit manifest against exported artifacts',
    )

    proj_adjudication = project_subparsers.add_parser(
        'adjudication-sample',
        help='Export an unlabeled adjudication sample package'
    )
    proj_adjudication.add_argument('project_id', help='Project ID')
    proj_adjudication.add_argument(
        '--output-file',
        required=True,
        help='Output JSON package path'
    )
    proj_adjudication.add_argument(
        '--limit-per-type',
        type=int,
        default=20,
        help='Maximum sample items per target type (default: 20)'
    )
    proj_adjudication.add_argument(
        '--context-chars',
        type=int,
        default=120,
        help='Characters of source context before/after anchored spans (default: 120)'
    )

    proj_irr = project_subparsers.add_parser('irr', help='Run inter-rater reliability analysis')
    proj_irr.add_argument('project_id', help='Project ID')
    proj_irr.add_argument('--passes', type=int, default=3, help='Number of coding passes (default: 3)')
    proj_irr.add_argument('--model', default=None, help='LLM model to use (default: gpt-5-mini)')
    proj_irr.add_argument('--models', nargs='+', help='Multiple models to rotate across passes')
    proj_irr.add_argument('--application-level', action='store_true',
                          help='Measure segment x code agreement (do passes code the same text the same way?) via exhaustive per-segment coding, not just codebook-discovery agreement')

    proj_stability = project_subparsers.add_parser('stability', help='Run multi-run stability analysis')
    proj_stability.add_argument('project_id', help='Project ID')
    proj_stability.add_argument('--runs', type=int, default=5, help='Number of identical runs (default: 5)')
    proj_stability.add_argument('--model', default=None, help='LLM model to use (default: gpt-5-mini)')

    proj_recode = project_subparsers.add_parser('recode', help='Incrementally code new documents')
    proj_recode.add_argument('project_id', help='Project ID')
    proj_recode.add_argument('--model', default=None, help='LLM model to use (default: gpt-5-mini)')

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
        elif args.command == 'bench':
            return handle_bench_command(args)
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

def handle_bench_command(args) -> int:
    """Run the Phase 0 benchmark scorecard through the canonical CLI."""
    from scripts import bench_phase0

    argv = [args.project_id]
    if args.d3_gold_file:
        argv.extend(["--d3-gold-file", args.d3_gold_file])
    if args.gold_file:
        argv.extend(["--gold-file", args.gold_file])
    if args.d7_baselines_file:
        argv.extend(["--d7-baselines-file", args.d7_baselines_file])
    if args.prompt_injection_file:
        argv.extend(["--prompt-injection-file", args.prompt_injection_file])
    if args.bias_counterfactual_file:
        argv.extend(["--bias-counterfactual-file", args.bias_counterfactual_file])
    if args.codebook_quality_file:
        argv.extend(["--codebook-quality-file", args.codebook_quality_file])
    if args.gt_fidelity_file:
        argv.extend(["--gt-fidelity-file", args.gt_fidelity_file])
    if args.interpretive_preference_file:
        argv.extend(["--interpretive-preference-file", args.interpretive_preference_file])
    if args.confidence_calibration_file:
        argv.extend(["--confidence-calibration-file", args.confidence_calibration_file])
    if args.observability_db:
        argv.extend(["--observability-db", args.observability_db])
    if args.trace_id:
        argv.extend(["--trace-id", args.trace_id])
    if args.output:
        argv.extend(["--output", args.output])
    if args.artifact_dir:
        argv.extend(["--artifact-dir", args.artifact_dir])
    return bench_phase0.main(argv)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

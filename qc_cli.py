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
  qc_cli bench-package phase0_package.json
  qc_cli write-phase0-adjudication-package <project_id> --output phase0_package.json --d3-gold-file d3_gold.json
  qc_cli validate-adjudication-protocol adjudication_protocol.json
  qc_cli adjudication-protocol-preflight adjudication_protocol.json sample.json
  qc_cli validate-adjudication-responses responses.json
  qc_cli adjudication-response-preflight adjudication_protocol.json sample.json responses.json
  qc_cli import-adjudication-responses responses.json --gold-set-id gold-001 --dataset-name "Study" --coder-count 2 --adjudicator expert --protocol "Expert consensus" --output-d3 d3_gold.json
  qc_cli validate-theoretical-sampling-protocol theoretical_sampling_protocol.json
  qc_cli theoretical-sampling-preflight theoretical_sampling_protocol.json --candidates-file candidates.json --results-file results.json
  qc_cli export-theoretical-sampling-candidates <project_id> --protocol theoretical_sampling_protocol.json --output candidates.json
  qc_cli export-theoretical-sampling-results theoretical_sampling_protocol.json --candidates-file candidates.json --selected-candidate-id candidate-1 --success-criterion-met "gap covered" --output results.json
  qc_cli validate-d4-codebook-quality-protocol d4_protocol.json
  qc_cli d4-codebook-quality-preflight d4_protocol.json --quality-file quality.json
  qc_cli validate-d6-bias-protocol d6_protocol.json
  qc_cli d6-bias-preflight d6_protocol.json --stratified-file stratified.json --counterfactual-file counterfactual.json
  qc_cli validate-d8-gt-fidelity-protocol d8_protocol.json
  qc_cli d8-gt-fidelity-preflight d8_protocol.json --gt-fidelity-file gt_fidelity.json
  qc_cli validate-sampling-frame-adequacy-protocol sampling_frame_protocol.json
  qc_cli sampling-frame-adequacy-preflight sampling_frame_protocol.json --adequacy-file adequacy.json
  qc_cli validate-d9-interpretive-preference-protocol d9_protocol.json
  qc_cli d9-interpretive-preference-preflight d9_protocol.json --preference-file preference.json
  qc_cli validate-confidence-calibration-protocol confidence_protocol.json
  qc_cli confidence-calibration-preflight confidence_protocol.json --calibration-file calibration.json
  qc_cli verify-phase0-benchmark-artifact benchmark_results/run/manifest.json
  qc_cli export-audit-manifest <project_id> --format markdown --artifact report.md --output manifest.json
  qc_cli verify-export-audit-manifest manifest.json
  qc_cli export-publish-preflight --manifest manifest.json
  qc_cli verify-export-audit-log events.jsonl
  qc_cli mirror-export-audit-db events.jsonl --db events.sqlite
  qc_cli verify-export-audit-db events.sqlite
  qc_cli lint-scope-phrasing <project_id> --input-file report.md
  qc_cli lint-prompt-overrides --root qc_clean
  qc_cli validate-d3-gold d3_gold.json
  qc_cli validate-d7-gold d7_gold.json
  qc_cli validate-d3-baseline-package d3_baseline.json
  qc_cli validate-d3-comparison-protocol d3_protocol.json
  qc_cli d3-comparison-preflight d3_protocol.json d3_gold.json baseline_a.json baseline_b.json
  qc_cli run-d7-retrieval <project_id> --output predictions.json
  qc_cli run-d7-live-baseline <project_id> --output live_baseline.json --model gpt-5-mini
  qc_cli validate-d7-baseline-package baseline.json
  qc_cli validate-d7-comparison-protocol d7_protocol.json
  qc_cli d7-comparison-preflight d7_protocol.json d7_gold.json lexical.json embedding.json
  qc_cli compare-d7-retrieval <project_id> --gold-file d7_gold.json --predictions-file predictions.json --artifact-dir benchmark_results
  qc_cli write-d7-comparison-package <project_id> --output d7_package.json --gold-file d7_gold.json --predictions-file predictions.json
  qc_cli compare-d7-package d7_comparison_package.json
  qc_cli verify-d7-comparison-artifact benchmark_results/run/manifest.json
  qc_cli run-inv7-fixtures --output inv7.json
  qc_cli run-inv7-live-fixtures --output inv7_live.json --model gpt-5-mini
  qc_cli validate-inv7-package inv7.json
  qc_cli validate-inv7-live-protocol inv7_protocol.json
  qc_cli inv7-live-preflight inv7_protocol.json inv7_live.json
  qc_cli compare-inv7-packages inv7_a.json inv7_b.json --output inv7_compare.json
  qc_cli project export <project_id> --format markdown --output-file report.md
  qc_cli project export <project_id> --format markdown --output-file report.md --audit-manifest manifest.json --publish-preflight --scope-lint
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
        '--d3-baselines-file',
        help='Optional D3 baseline prediction JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--d3-comparison-protocol-file',
        help='Optional D3 comparison protocol JSON file; preflights supplied D3 packages before scoring'
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
        '--inv7-live-protocol-file',
        help='Optional INV-7 live protocol JSON file; preflights supplied package before scoring'
    )
    bench_parser.add_argument(
        '--d6-bias-protocol-file',
        help='Optional D6 bias protocol JSON file; preflights supplied D6 rows before scoring'
    )
    bench_parser.add_argument(
        '--bias-counterfactual-file',
        help='Optional D6 counterfactual identity-swap outcome JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--bias-stratified-file',
        help='Optional D6 stratified correctness/error JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--d4-codebook-quality-protocol-file',
        help='Optional D4 codebook-quality protocol JSON file; preflights supplied D4 rows before scoring'
    )
    bench_parser.add_argument(
        '--codebook-quality-file',
        help='Optional D4 codebook-quality rubric outcome JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--d8-gt-fidelity-protocol-file',
        help='Optional D8 GT-fidelity protocol JSON file; preflights supplied D8 rows before scoring'
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
        '--d9-interpretive-preference-protocol-file',
        help='Optional D9 interpretive-preference protocol JSON file; preflights supplied D9 rows before scoring'
    )
    bench_parser.add_argument(
        '--confidence-calibration-file',
        help='Optional confidence/correctness calibration JSON file; applied in memory only'
    )
    bench_parser.add_argument(
        '--confidence-calibration-protocol-file',
        help='Optional confidence-calibration protocol JSON file; preflights supplied calibration rows before scoring'
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

    # Bench package command
    bench_package_parser = subparsers.add_parser(
        'bench-package',
        help='Run evaluation-harness Phase 0 from a package manifest',
        description='Run the deterministic Phase 0 scorecard from a strict package manifest',
    )
    bench_package_parser.add_argument(
        'package_file',
        help='Path to the Phase 0 benchmark package JSON manifest',
    )

    phase0_adjudication_package_writer_parser = subparsers.add_parser(
        'write-phase0-adjudication-package',
        help='Write a Phase 0 adjudication package manifest',
        description='Write a strict Phase 0 package manifest from validated D3/D7 adjudication gold',
    )
    phase0_adjudication_package_writer_parser.add_argument(
        'project_id',
        help='Project ID to score with the package',
    )
    phase0_adjudication_package_writer_parser.add_argument(
        '--output',
        required=True,
        help='Output Phase 0 package manifest path',
    )
    phase0_adjudication_package_writer_parser.add_argument(
        '--d3-gold-file',
        help='Optional versioned D3 adjudication gold package path',
    )
    phase0_adjudication_package_writer_parser.add_argument(
        '--d7-gold-file',
        '--gold-file',
        dest='d7_gold_file',
        help='Optional versioned D7 adjudication gold package path',
    )
    phase0_adjudication_package_writer_parser.add_argument(
        '--scorecard-output',
        help='Optional scorecard output path recorded in the package',
    )
    phase0_adjudication_package_writer_parser.add_argument(
        '--artifact-dir',
        help='Optional artifact root directory recorded in the package',
    )
    phase0_adjudication_package_writer_parser.add_argument(
        '--observability-db',
        help='Optional llm_client observability SQLite path for D10 scoring',
    )
    phase0_adjudication_package_writer_parser.add_argument(
        '--trace-id',
        help='Optional exact trace ID for D10 scoring',
    )

    adjudication_protocol_validator_parser = subparsers.add_parser(
        'validate-adjudication-protocol',
        help='Validate an adjudication protocol package',
        description='Validate a schema_version=1 adjudication protocol package',
    )
    adjudication_protocol_validator_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 adjudication protocol JSON package',
    )

    adjudication_protocol_preflight_parser = subparsers.add_parser(
        'adjudication-protocol-preflight',
        help='Preflight adjudication protocol/sample packages',
        description='Preflight an adjudication protocol package against a sample package',
    )
    adjudication_protocol_preflight_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 adjudication protocol JSON package',
    )
    adjudication_protocol_preflight_parser.add_argument(
        'sample',
        help='Path to a schema_version=1 adjudication sample JSON package',
    )

    adjudication_response_validator_parser = subparsers.add_parser(
        'validate-adjudication-responses',
        help='Validate completed adjudication responses',
        description='Validate a completed adjudication response package',
    )
    adjudication_response_validator_parser.add_argument(
        'package',
        help='Path to a completed adjudication response JSON package',
    )

    adjudication_response_preflight_parser = subparsers.add_parser(
        'adjudication-response-preflight',
        help='Preflight adjudication responses',
        description='Preflight completed adjudication responses against protocol and sample packages',
    )
    adjudication_response_preflight_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 adjudication protocol JSON package',
    )
    adjudication_response_preflight_parser.add_argument(
        'sample',
        help='Path to a schema_version=1 adjudication sample JSON package',
    )
    adjudication_response_preflight_parser.add_argument(
        'responses',
        help='Path to a completed adjudication response JSON package',
    )

    adjudication_import_parser = subparsers.add_parser(
        'import-adjudication-responses',
        help='Import adjudication responses into D3/D7 gold packages',
        description='Import completed adjudication responses through the canonical script',
    )
    adjudication_import_parser.add_argument(
        'package',
        help='Path to a completed adjudication response JSON package',
    )
    adjudication_import_parser.add_argument(
        '--output-d3',
        help='Optional D3 gold package output path',
    )
    adjudication_import_parser.add_argument(
        '--output-d7',
        help='Optional D7 gold package output path',
    )
    adjudication_import_parser.add_argument(
        '--gold-set-id',
        required=True,
        help='Stable gold-set ID',
    )
    adjudication_import_parser.add_argument(
        '--dataset-name',
        required=True,
        help='Human-readable dataset name',
    )
    adjudication_import_parser.add_argument(
        '--split',
        choices=['held_out', 'dev', 'public_comparator'],
        help='Evaluation split represented by generated packages',
    )
    adjudication_import_parser.add_argument(
        '--coder-count',
        required=True,
        type=int,
        help='Number of coders',
    )
    adjudication_import_parser.add_argument(
        '--adjudicator',
        required=True,
        help='Adjudicator identifier',
    )
    adjudication_import_parser.add_argument(
        '--protocol',
        required=True,
        help='Adjudication protocol summary',
    )
    adjudication_import_parser.add_argument(
        '--protocol-package',
        help='Optional adjudication protocol package used to preflight before import',
    )
    adjudication_import_parser.add_argument(
        '--sample-package',
        help='Optional adjudication sample package used to preflight before import',
    )
    adjudication_import_parser.add_argument(
        '--prompt-frozen',
        action='store_true',
        help='Mark prompts/models as frozen before scoring this split',
    )
    adjudication_import_parser.add_argument(
        '--contamination-checked',
        action='store_true',
        help='Mark train/test contamination as checked for this split',
    )
    adjudication_import_parser.add_argument(
        '--notes',
        help='Optional adjudication notes',
    )

    theoretical_sampling_protocol_validator_parser = subparsers.add_parser(
        'validate-theoretical-sampling-protocol',
        help='Validate a theoretical-sampling protocol package',
        description='Validate a schema_version=1 theoretical-sampling protocol package',
    )
    theoretical_sampling_protocol_validator_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 theoretical-sampling protocol JSON package',
    )

    theoretical_sampling_preflight_parser = subparsers.add_parser(
        'theoretical-sampling-preflight',
        help='Preflight theoretical-sampling packages',
        description='Preflight theoretical-sampling candidates/results against a protocol',
    )
    theoretical_sampling_preflight_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 theoretical-sampling protocol JSON package',
    )
    theoretical_sampling_preflight_parser.add_argument(
        '--candidates-file',
        required=True,
        help='Theoretical-sampling candidate package JSON file',
    )
    theoretical_sampling_preflight_parser.add_argument(
        '--results-file',
        help='Optional theoretical-sampling result package JSON file',
    )

    theoretical_sampling_candidates_parser = subparsers.add_parser(
        'export-theoretical-sampling-candidates',
        help='Export theoretical-sampling candidates',
        description='Export loaded-document theoretical-sampling candidate packages',
    )
    theoretical_sampling_candidates_parser.add_argument(
        'project_id',
        help='Project ID to export candidates for',
    )
    theoretical_sampling_candidates_parser.add_argument(
        '--projects-dir',
        help='Optional project store directory',
    )
    theoretical_sampling_candidates_parser.add_argument(
        '--protocol',
        required=True,
        help='Path to a schema_version=1 theoretical-sampling protocol JSON package',
    )
    theoretical_sampling_candidates_parser.add_argument(
        '--output',
        help='Optional JSON output path',
    )
    theoretical_sampling_candidates_parser.add_argument(
        '--candidate-name',
        action='append',
        dest='candidate_names',
        help='Optional loaded document name to consider; may be repeated',
    )
    theoretical_sampling_candidates_parser.add_argument(
        '--max-suggestions',
        type=int,
        help='Optional suggestion limit',
    )

    theoretical_sampling_results_parser = subparsers.add_parser(
        'export-theoretical-sampling-results',
        help='Export theoretical-sampling results',
        description='Export selected theoretical-sampling candidates as a result package',
    )
    theoretical_sampling_results_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 theoretical-sampling protocol JSON package',
    )
    theoretical_sampling_results_parser.add_argument(
        '--candidates-file',
        required=True,
        help='Theoretical-sampling candidate package JSON file',
    )
    theoretical_sampling_results_parser.add_argument(
        '--selected-candidate-id',
        action='append',
        required=True,
        dest='selected_candidate_ids',
        help='Selected candidate ID; may be repeated',
    )
    theoretical_sampling_results_parser.add_argument(
        '--success-criterion-met',
        action='append',
        required=True,
        dest='success_criteria_met',
        help='Pre-registered success criterion marked as met; may be repeated',
    )
    theoretical_sampling_results_parser.add_argument(
        '--stopped-by-rule',
        action='store_true',
        help='Mark the result package as stopped by the protocol stopping rule',
    )
    theoretical_sampling_results_parser.add_argument(
        '--output',
        help='Optional JSON output path',
    )

    d4_protocol_validator_parser = subparsers.add_parser(
        'validate-d4-codebook-quality-protocol',
        help='Validate a D4 codebook-quality protocol package',
        description='Validate a schema_version=1 D4 codebook-quality protocol package',
    )
    d4_protocol_validator_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 D4 codebook-quality protocol JSON',
    )

    d4_preflight_parser = subparsers.add_parser(
        'd4-codebook-quality-preflight',
        help='Preflight D4 codebook-quality results',
        description='Preflight D4 codebook-quality results against a registered protocol',
    )
    d4_preflight_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 D4 codebook-quality protocol JSON',
    )
    d4_preflight_parser.add_argument(
        '--quality-file',
        help='Optional D4 codebook-quality result JSON file',
    )

    d6_protocol_validator_parser = subparsers.add_parser(
        'validate-d6-bias-protocol',
        help='Validate a D6 bias protocol package',
        description='Validate a schema_version=1 D6 bias protocol package',
    )
    d6_protocol_validator_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 D6 bias protocol JSON',
    )

    d6_preflight_parser = subparsers.add_parser(
        'd6-bias-preflight',
        help='Preflight D6 bias results',
        description='Preflight D6 bias results against a registered protocol',
    )
    d6_preflight_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 D6 bias protocol JSON',
    )
    d6_preflight_parser.add_argument(
        '--stratified-file',
        help='Optional D6 stratified correctness/error result JSON file',
    )
    d6_preflight_parser.add_argument(
        '--counterfactual-file',
        help='Optional D6 counterfactual identity-swap result JSON file',
    )

    d8_protocol_validator_parser = subparsers.add_parser(
        'validate-d8-gt-fidelity-protocol',
        help='Validate a D8 GT-fidelity protocol package',
        description='Validate a schema_version=1 D8 GT-fidelity protocol package',
    )
    d8_protocol_validator_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 D8 GT-fidelity protocol JSON',
    )

    d8_preflight_parser = subparsers.add_parser(
        'd8-gt-fidelity-preflight',
        help='Preflight D8 GT-fidelity results',
        description='Preflight D8 GT-fidelity results against a registered protocol',
    )
    d8_preflight_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 D8 GT-fidelity protocol JSON',
    )
    d8_preflight_parser.add_argument(
        '--gt-fidelity-file',
        help='Optional D8 GT-fidelity result JSON file',
    )

    sampling_frame_protocol_validator_parser = subparsers.add_parser(
        'validate-sampling-frame-adequacy-protocol',
        help='Validate a sampling-frame adequacy protocol package',
        description='Validate a schema_version=1 sampling-frame adequacy protocol package',
    )
    sampling_frame_protocol_validator_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 sampling-frame adequacy protocol JSON',
    )

    sampling_frame_preflight_parser = subparsers.add_parser(
        'sampling-frame-adequacy-preflight',
        help='Preflight sampling-frame adequacy results',
        description='Preflight sampling-frame adequacy results against a registered protocol',
    )
    sampling_frame_preflight_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 sampling-frame adequacy protocol JSON',
    )
    sampling_frame_preflight_parser.add_argument(
        '--adequacy-file',
        help='Optional sampling-frame adequacy result JSON file',
    )

    d9_protocol_validator_parser = subparsers.add_parser(
        'validate-d9-interpretive-preference-protocol',
        help='Validate a D9 interpretive-preference protocol package',
        description='Validate a schema_version=1 D9 interpretive-preference protocol package',
    )
    d9_protocol_validator_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 D9 interpretive-preference protocol JSON',
    )

    d9_preflight_parser = subparsers.add_parser(
        'd9-interpretive-preference-preflight',
        help='Preflight D9 interpretive-preference results',
        description='Preflight D9 interpretive-preference results against a registered protocol',
    )
    d9_preflight_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 D9 interpretive-preference protocol JSON',
    )
    d9_preflight_parser.add_argument(
        '--preference-file',
        help='Optional D9 interpretive-preference result JSON file',
    )

    confidence_protocol_validator_parser = subparsers.add_parser(
        'validate-confidence-calibration-protocol',
        help='Validate a confidence-calibration protocol package',
        description='Validate a schema_version=1 confidence-calibration protocol package',
    )
    confidence_protocol_validator_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 confidence-calibration protocol JSON',
    )

    confidence_preflight_parser = subparsers.add_parser(
        'confidence-calibration-preflight',
        help='Preflight confidence-calibration results',
        description='Preflight confidence-calibration results against a registered protocol',
    )
    confidence_preflight_parser.add_argument(
        'protocol',
        help='Path to a schema_version=1 confidence-calibration protocol JSON',
    )
    confidence_preflight_parser.add_argument(
        '--calibration-file',
        help='Optional confidence-calibration result JSON file',
    )

    phase0_artifact_verifier_parser = subparsers.add_parser(
        'verify-phase0-benchmark-artifact',
        help='Verify a Phase 0 benchmark artifact package',
        description='Verify a Phase 0 benchmark artifact directory or manifest file',
    )
    phase0_artifact_verifier_parser.add_argument(
        'artifact',
        help='Phase 0 benchmark artifact directory or manifest.json path',
    )

    export_audit_manifest_parser = subparsers.add_parser(
        'export-audit-manifest',
        help='Write an export audit manifest',
        description='Write a local hash manifest for existing project export artifacts',
    )
    export_audit_manifest_parser.add_argument(
        'project_id',
        help='Project ID used to build the export',
    )
    export_audit_manifest_parser.add_argument(
        '--format',
        required=True,
        choices=['json', 'csv', 'markdown', 'qdpx'],
        help='Export format represented by the artifacts',
    )
    export_audit_manifest_parser.add_argument(
        '--artifact',
        action='append',
        required=True,
        help='Export artifact path; repeat for multi-file exports',
    )
    export_audit_manifest_parser.add_argument(
        '--output',
        required=True,
        help='Manifest JSON output path',
    )
    export_audit_manifest_parser.add_argument(
        '--base-dir',
        help='Optional base directory for relative artifact paths in the manifest',
    )
    export_audit_manifest_parser.add_argument(
        '--projects-dir',
        help='Optional project store directory',
    )
    export_audit_manifest_parser.add_argument(
        '--audit-log',
        help='Optional export audit event JSONL log to append a manifest_written event',
    )
    export_audit_manifest_parser.add_argument(
        '--audit-db',
        help='Optional SQLite mirror for the audit event log; requires --audit-log',
    )

    export_audit_manifest_verifier_parser = subparsers.add_parser(
        'verify-export-audit-manifest',
        help='Verify an export audit manifest',
        description='Verify a local hash manifest for project export artifacts',
    )
    export_audit_manifest_verifier_parser.add_argument(
        'manifest',
        help='Export audit manifest JSON path',
    )
    export_audit_manifest_verifier_parser.add_argument(
        '--base-dir',
        help='Optional base directory for resolving relative artifact paths',
    )
    export_audit_manifest_verifier_parser.add_argument(
        '--project-id',
        help='Optional project ID for project-state hash checking',
    )
    export_audit_manifest_verifier_parser.add_argument(
        '--projects-dir',
        help='Optional project store directory',
    )
    export_audit_manifest_verifier_parser.add_argument(
        '--audit-log',
        help='Optional export audit event JSONL log to append a manifest_verified event',
    )
    export_audit_manifest_verifier_parser.add_argument(
        '--audit-db',
        help='Optional SQLite mirror for the audit event log; requires --audit-log',
    )

    export_publish_preflight_parser = subparsers.add_parser(
        'export-publish-preflight',
        help='Run export publish preflight',
        description='Run strict local preflight for export publish or handoff',
    )
    export_publish_preflight_parser.add_argument(
        '--manifest',
        required=True,
        help='Export audit manifest path',
    )
    export_publish_preflight_parser.add_argument(
        '--base-dir',
        help='Optional base directory for resolving manifest artifact paths',
    )
    export_publish_preflight_parser.add_argument(
        '--project-id',
        help='Optional project ID for project-state hash checking',
    )
    export_publish_preflight_parser.add_argument(
        '--projects-dir',
        help='Optional project store directory',
    )
    export_publish_preflight_parser.add_argument(
        '--audit-log',
        help='Optional export audit event JSONL log to append a publish_preflight event',
    )
    export_publish_preflight_parser.add_argument(
        '--audit-db',
        help='Optional SQLite mirror for the audit event log; requires --audit-log',
    )
    export_publish_preflight_parser.add_argument(
        '--scope-lint',
        action='store_true',
        help='Also lint textual export artifacts for unsafe corpus-scope phrasing',
    )

    export_audit_log_verifier_parser = subparsers.add_parser(
        'verify-export-audit-log',
        help='Verify an export audit event log',
        description='Verify a local export audit event JSONL log',
    )
    export_audit_log_verifier_parser.add_argument(
        'log',
        help='Export audit event JSONL path',
    )

    export_audit_db_mirror_parser = subparsers.add_parser(
        'mirror-export-audit-db',
        help='Mirror export audit events into SQLite',
        description='Mirror a verified export audit event JSONL log into SQLite',
    )
    export_audit_db_mirror_parser.add_argument(
        'log',
        help='Export audit event JSONL path',
    )
    export_audit_db_mirror_parser.add_argument(
        '--db',
        required=True,
        help='SQLite audit event database path',
    )

    export_audit_db_verifier_parser = subparsers.add_parser(
        'verify-export-audit-db',
        help='Verify an export audit SQLite mirror',
        description='Verify a local SQLite export audit event mirror',
    )
    export_audit_db_verifier_parser.add_argument(
        'db',
        help='SQLite audit event database path',
    )

    scope_lint_parser = subparsers.add_parser(
        'lint-scope-phrasing',
        help='Lint report text for unsafe scope phrasing',
        description='Lint text or Markdown for corpus-scope-sensitive phrasing',
    )
    scope_lint_parser.add_argument(
        'project_id',
        help='Project ID whose corpus scope should govern linting',
    )
    scope_lint_input_group = scope_lint_parser.add_mutually_exclusive_group(required=True)
    scope_lint_input_group.add_argument(
        '--input-file',
        help='Text or Markdown file to lint',
    )
    scope_lint_input_group.add_argument(
        '--text',
        help='Inline text to lint',
    )
    scope_lint_parser.add_argument(
        '--projects-dir',
        help='Optional project store directory',
    )

    prompt_override_lint_parser = subparsers.add_parser(
        'lint-prompt-overrides',
        help='Check prompt override registry consistency',
        description='Check prompt override source uses against the central registry',
    )
    prompt_override_lint_parser.add_argument(
        '--root',
        help='Python source root to scan',
    )

    # D7 retrieval export command
    d7_retrieval_parser = subparsers.add_parser(
        'run-d7-retrieval',
        help='Export D7 retrieval predictions',
        description='Export disconfirmation retrieval candidates as D7 baseline predictions',
    )
    d7_retrieval_parser.add_argument('project_id', help='Project ID to export')
    d7_retrieval_parser.add_argument('--projects-dir', help='Optional project store directory')
    d7_retrieval_parser.add_argument('--output', help='Optional JSON output path')
    d7_retrieval_parser.add_argument('--name', help='Optional baseline name')
    d7_retrieval_parser.add_argument('--description', help='Optional baseline description')
    d7_retrieval_parser.add_argument('--max-targets', type=int)
    d7_retrieval_parser.add_argument('--candidates-per-claim', type=int)
    d7_retrieval_parser.add_argument('--retrieval-mode')
    d7_retrieval_parser.add_argument('--bm25-k1', type=float)
    d7_retrieval_parser.add_argument('--bm25-b', type=float)
    d7_retrieval_parser.add_argument('--contrary-cue-weight', type=float)
    d7_retrieval_parser.add_argument('--expanded-term-weight', type=float)
    d7_retrieval_parser.add_argument('--embedding-model')
    d7_retrieval_parser.add_argument('--embedding-dimensions', type=int)
    d7_retrieval_parser.add_argument('--semantic-weight', type=float)
    d7_retrieval_parser.add_argument('--min-semantic-similarity', type=float)
    d7_retrieval_parser.add_argument('--trace-id')
    d7_retrieval_parser.add_argument('--max-budget', type=float)

    # D7 live baseline export command
    d7_live_baseline_parser = subparsers.add_parser(
        'run-d7-live-baseline',
        help='Export live D7 baseline predictions',
        description='Export live candidate-selection predictions as a D7 baseline package',
    )
    d7_live_baseline_parser.add_argument('project_id', help='Project ID to export')
    d7_live_baseline_parser.add_argument('--projects-dir', help='Optional project store directory')
    d7_live_baseline_parser.add_argument('--output', help='Optional JSON output path')
    d7_live_baseline_parser.add_argument('--name', help='Optional baseline name')
    d7_live_baseline_parser.add_argument('--description', help='Optional baseline description')
    d7_live_baseline_parser.add_argument('--model', help='Live model name')
    d7_live_baseline_parser.add_argument('--max-targets', type=int)
    d7_live_baseline_parser.add_argument('--candidates-per-claim', type=int)
    d7_live_baseline_parser.add_argument('--retrieval-mode')
    d7_live_baseline_parser.add_argument('--bm25-k1', type=float)
    d7_live_baseline_parser.add_argument('--bm25-b', type=float)
    d7_live_baseline_parser.add_argument('--contrary-cue-weight', type=float)
    d7_live_baseline_parser.add_argument('--expanded-term-weight', type=float)
    d7_live_baseline_parser.add_argument('--embedding-model')
    d7_live_baseline_parser.add_argument('--embedding-dimensions', type=int)
    d7_live_baseline_parser.add_argument('--semantic-weight', type=float)
    d7_live_baseline_parser.add_argument('--min-semantic-similarity', type=float)
    d7_live_baseline_parser.add_argument('--trace-id')
    d7_live_baseline_parser.add_argument('--max-budget', type=float)

    # D7 retrieval comparison command
    d7_comparison_parser = subparsers.add_parser(
        'compare-d7-retrieval',
        help='Compare D7 retrieval prediction packages',
        description='Score D7 retrieval prediction packages against one gold file',
    )
    d7_comparison_parser.add_argument('project_id', help='Project ID to score')
    d7_comparison_parser.add_argument('--projects-dir', help='Optional project store directory')
    d7_comparison_parser.add_argument('--gold-file', required=True, help='D7 gold JSON file')
    d7_comparison_parser.add_argument(
        '--predictions-file',
        required=True,
        action='append',
        help='Retrieval prediction package JSON file; repeat to compare multiple packages',
    )
    d7_comparison_parser.add_argument('--output', help='Optional JSON report output path')
    d7_comparison_parser.add_argument(
        '--protocol-package',
        help='Optional D7 comparison protocol package used to preflight before scoring',
    )
    d7_comparison_parser.add_argument(
        '--artifact-dir',
        help='Optional root directory for a versioned D7 comparison artifact package',
    )

    d7_artifact_verifier_parser = subparsers.add_parser(
        'verify-d7-comparison-artifact',
        help='Verify a D7 comparison artifact package',
        description='Verify a D7 comparison artifact directory or manifest file',
    )
    d7_artifact_verifier_parser.add_argument(
        'artifact',
        help='D7 comparison artifact directory or manifest.json path',
    )

    d7_comparison_package_parser = subparsers.add_parser(
        'compare-d7-package',
        help='Run a D7 comparison package manifest',
        description='Run D7 retrieval comparison from a strict package manifest',
    )
    d7_comparison_package_parser.add_argument(
        'package_file',
        help='Path to the D7 comparison package JSON manifest',
    )

    d7_comparison_package_writer_parser = subparsers.add_parser(
        'write-d7-comparison-package',
        help='Write a D7 comparison package manifest',
        description='Write a strict D7 comparison package manifest from validated inputs',
    )
    d7_comparison_package_writer_parser.add_argument('project_id', help='Project ID to compare')
    d7_comparison_package_writer_parser.add_argument(
        '--projects-dir',
        help='Optional project store directory recorded in the package',
    )
    d7_comparison_package_writer_parser.add_argument(
        '--output',
        required=True,
        help='Output D7 comparison package manifest path',
    )
    d7_comparison_package_writer_parser.add_argument(
        '--gold-file',
        required=True,
        help='Versioned D7 gold package path',
    )
    d7_comparison_package_writer_parser.add_argument(
        '--predictions-file',
        required=True,
        action='append',
        help='Versioned D7 retrieval/live-baseline prediction package path; repeat for multiple packages',
    )
    d7_comparison_package_writer_parser.add_argument(
        '--protocol-package',
        help='Optional D7 comparison protocol package to preflight before writing',
    )
    d7_comparison_package_writer_parser.add_argument(
        '--comparison-output',
        help='Optional D7 comparison report output path recorded in the package',
    )
    d7_comparison_package_writer_parser.add_argument(
        '--artifact-dir',
        help='Optional artifact root directory recorded in the package',
    )
    d7_comparison_package_writer_parser.add_argument(
        '--verify-artifact',
        action='store_true',
        help='Ask the package runner to verify the artifact created by the comparison run',
    )

    # D3/D7 gold-set validation commands
    d3_gold_validator_parser = subparsers.add_parser(
        'validate-d3-gold',
        help='Validate a D3 gold-set package',
        description='Validate a versioned D3 application-validity gold-set package',
    )
    d3_gold_validator_parser.add_argument(
        'gold_set',
        help='Path to the D3 gold-set JSON file',
    )

    d7_gold_validator_parser = subparsers.add_parser(
        'validate-d7-gold',
        help='Validate a D7 gold-set package',
        description='Validate a versioned D7 disconfirmation gold-set package',
    )
    d7_gold_validator_parser.add_argument(
        'gold_set',
        help='Path to the D7 gold-set JSON file',
    )

    # D3 baseline package validation command
    d3_baseline_validator_parser = subparsers.add_parser(
        'validate-d3-baseline-package',
        help='Validate a D3 baseline prediction package',
        description='Validate a versioned D3 application-baseline prediction package',
    )
    d3_baseline_validator_parser.add_argument(
        'package_file',
        help='Path to the D3 baseline package JSON file',
    )

    d3_comparison_protocol_validator_parser = subparsers.add_parser(
        'validate-d3-comparison-protocol',
        help='Validate a D3 comparison protocol package',
        description='Validate a pre-run D3 baseline-comparison protocol package',
    )
    d3_comparison_protocol_validator_parser.add_argument(
        'protocol',
        help='Path to the D3 comparison protocol JSON file',
    )

    d3_comparison_preflight_parser = subparsers.add_parser(
        'd3-comparison-preflight',
        help='Preflight D3 comparison inputs',
        description='Preflight a D3 comparison protocol, gold package, and baseline packages',
    )
    d3_comparison_preflight_parser.add_argument(
        'protocol',
        help='Path to the D3 comparison protocol JSON file',
    )
    d3_comparison_preflight_parser.add_argument(
        'gold',
        help='Path to the D3 gold package JSON file',
    )
    d3_comparison_preflight_parser.add_argument(
        'predictions',
        nargs='+',
        help='One or more D3 baseline prediction package JSON files',
    )

    # D7 baseline package validation command
    d7_baseline_validator_parser = subparsers.add_parser(
        'validate-d7-baseline-package',
        help='Validate a D7 baseline prediction package',
        description='Validate a versioned D7 retrieval or live-baseline prediction package',
    )
    d7_baseline_validator_parser.add_argument(
        'package_file',
        help='Path to the D7 baseline package JSON file',
    )

    d7_comparison_protocol_validator_parser = subparsers.add_parser(
        'validate-d7-comparison-protocol',
        help='Validate a D7 comparison protocol package',
        description='Validate a pre-run D7 retrieval-comparison protocol package',
    )
    d7_comparison_protocol_validator_parser.add_argument(
        'protocol',
        help='Path to the D7 comparison protocol JSON file',
    )

    d7_comparison_preflight_parser = subparsers.add_parser(
        'd7-comparison-preflight',
        help='Preflight D7 comparison inputs',
        description='Preflight a D7 comparison protocol, gold package, and prediction packages',
    )
    d7_comparison_preflight_parser.add_argument(
        'protocol',
        help='Path to the D7 comparison protocol JSON file',
    )
    d7_comparison_preflight_parser.add_argument(
        'gold',
        help='Path to the D7 gold package JSON file',
    )
    d7_comparison_preflight_parser.add_argument(
        'predictions',
        nargs='+',
        help='One or more D7 retrieval or live-baseline prediction package JSON files',
    )

    # INV-7 prompt-injection fixture commands
    inv7_fixture_parser = subparsers.add_parser(
        'run-inv7-fixtures',
        help='Run structural INV-7 fixtures',
        description='Run deterministic INV-7 structural fixtures and write scorecard input JSON',
    )
    inv7_fixture_parser.add_argument(
        '--output',
        required=True,
        help='Path to write INV-7 fixture results JSON',
    )

    inv7_live_fixture_parser = subparsers.add_parser(
        'run-inv7-live-fixtures',
        help='Run live INV-7 fixtures',
        description='Run live INV-7 prompt-injection fixtures and write scorecard input JSON',
    )
    inv7_live_fixture_parser.add_argument(
        '--output',
        required=True,
        help='Path to write INV-7 live fixture results JSON',
    )
    inv7_live_fixture_parser.add_argument(
        '--fixtures',
        help='Optional schema_version=1 INV-7 live fixture manifest JSON',
    )
    inv7_live_fixture_parser.add_argument('--model', help='Live model name')
    inv7_live_fixture_parser.add_argument('--trace-id', help='llm_client trace ID prefix')
    inv7_live_fixture_parser.add_argument(
        '--max-budget',
        type=float,
        help='llm_client maximum budget for the live fixture run',
    )

    inv7_package_validator_parser = subparsers.add_parser(
        'validate-inv7-package',
        help='Validate an INV-7 prompt-injection package',
        description='Validate a schema_version=1 INV-7 prompt-injection package',
    )
    inv7_package_validator_parser.add_argument(
        'package_file',
        help='Path to the INV-7 package JSON file',
    )

    inv7_live_protocol_validator_parser = subparsers.add_parser(
        'validate-inv7-live-protocol',
        help='Validate an INV-7 live protocol package',
        description='Validate a schema_version=1 INV-7 live benchmark protocol',
    )
    inv7_live_protocol_validator_parser.add_argument(
        'protocol_file',
        help='Path to the INV-7 live protocol JSON file',
    )

    inv7_live_preflight_parser = subparsers.add_parser(
        'inv7-live-preflight',
        help='Preflight INV-7 live result package against protocol',
        description='Preflight an INV-7 live result package against a live protocol',
    )
    inv7_live_preflight_parser.add_argument(
        'protocol_file',
        help='Path to the INV-7 live protocol JSON file',
    )
    inv7_live_preflight_parser.add_argument(
        'package_file',
        help='Path to the INV-7 live result package JSON file',
    )

    inv7_package_comparison_parser = subparsers.add_parser(
        'compare-inv7-packages',
        help='Compare INV-7 package outcomes',
        description='Compare two or more schema_version=1 INV-7 prompt-injection packages',
    )
    inv7_package_comparison_parser.add_argument(
        'package_files',
        nargs='+',
        help='Two or more INV-7 package JSON files',
    )
    inv7_package_comparison_parser.add_argument(
        '--output',
        help='Optional path to write the comparison report JSON',
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
    proj_create.add_argument(
        '--auto-refresh-higher-order-on-recode',
        action='store_true',
        help='Default this project to higher-order refresh during incremental recode',
    )

    proj_list = project_subparsers.add_parser('list', help='List all projects')

    proj_show = project_subparsers.add_parser('show', help='Show project details')
    proj_show.add_argument('project_id', help='Project ID')

    proj_claims = project_subparsers.add_parser('claims', help='Show project claim ledger')
    proj_claims.add_argument('project_id', help='Project ID')
    proj_claims.add_argument('--limit', type=int, default=20, help='Maximum claims to show (default: 20)')
    proj_claims.add_argument('--offset', type=int, default=0, help='Number of claims to skip before showing rows')
    proj_claims.add_argument(
        '--show-anchors',
        action='store_true',
        help='Show bounded supporting/contrary anchor details for each displayed claim',
    )
    proj_claims.add_argument(
        '--show-scope',
        action='store_true',
        help='Show compact scope details for each displayed claim',
    )

    proj_patterns = project_subparsers.add_parser('patterns', help='Show descriptive observed patterns')
    proj_patterns.add_argument('project_id', help='Project ID')
    proj_patterns.add_argument('--limit', type=int, default=20, help='Maximum patterns to show (default: 20)')
    proj_patterns.add_argument('--offset', type=int, default=0, help='Number of patterns to skip before showing rows')
    proj_patterns.add_argument(
        '--show-anchors',
        action='store_true',
        help='Show bounded supporting anchor details for each displayed pattern',
    )

    proj_abductive = project_subparsers.add_parser(
        'abductive',
        help='Show provisional abductive candidate explanations',
    )
    proj_abductive.add_argument('project_id', help='Project ID')
    proj_abductive.add_argument('--limit', type=int, default=20, help='Maximum candidates to show (default: 20)')
    proj_abductive.add_argument('--offset', type=int, default=0, help='Number of candidates to skip before showing rows')

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

    proj_recode_policy = project_subparsers.add_parser(
        'recode-policy',
        help='Show or update project recode refresh policy',
    )
    proj_recode_policy.add_argument('project_id', help='Project ID')
    recode_policy_group = proj_recode_policy.add_mutually_exclusive_group()
    recode_policy_group.add_argument(
        '--enable-auto-refresh-higher-order',
        action='store_true',
        default=False,
        help='Enable project-level higher-order refresh by default during recode',
    )
    recode_policy_group.add_argument(
        '--disable-auto-refresh-higher-order',
        action='store_true',
        default=False,
        help='Disable project-level higher-order refresh by default during recode',
    )

    proj_add = project_subparsers.add_parser('add-docs', help='Add documents to project')
    proj_add.add_argument('project_id', help='Project ID')
    proj_add.add_argument('--files', nargs='+', help='Files to add')
    proj_add.add_argument('--directory', help='Directory of files to add')
    proj_add.add_argument(
        '--recode',
        action='store_true',
        help='After adding documents, incrementally code the new documents',
    )
    proj_add.add_argument(
        '--model',
        default=None,
        help='LLM model to use when --recode is supplied (default: project config)',
    )
    proj_add_refresh_group = proj_add.add_mutually_exclusive_group()
    proj_add_refresh_group.add_argument(
        '--refresh-higher-order',
        action='store_true',
        default=False,
        help=(
            'With --recode, refresh methodology-specific higher-order outputs '
            'after incremental coding'
        ),
    )
    proj_add_refresh_group.add_argument(
        '--no-refresh-higher-order',
        action='store_true',
        default=False,
        help='With --recode, force hard-invalidation mode for this run',
    )

    proj_run = project_subparsers.add_parser('run', help='Run analysis pipeline on project')
    proj_run.add_argument('project_id', help='Project ID')
    proj_run.add_argument('--model', default=None, help='LLM model to use (default: gpt-5-mini)')
    proj_run.add_argument('--review', action='store_true', help='Enable human review pauses')
    proj_run.add_argument('--exhaustive', action='store_true',
                          help='Code every segment (examined-and-judged coverage, INV-8) instead of surfacing example quotes')
    proj_run.add_argument('--abductive', action='store_true',
                          help='Enable provisional abductive candidate explanations from observed patterns')

    proj_export = project_subparsers.add_parser('export', help='Export project results')
    proj_export.add_argument('project_id', help='Project ID')
    proj_export.add_argument('--format', choices=['json', 'csv', 'markdown', 'qdpx'], default='json', help='Export format (default: json)')
    proj_export.add_argument('--output-file', help='Output file path (for json/markdown/qdpx)')
    proj_export.add_argument('--output-dir', help='Output directory (for csv)')
    proj_export.add_argument('--no-overwrite', action='store_true', help='Fail if any target export artifact already exists')
    proj_export.add_argument('--audit-manifest', help='Optional export audit manifest output path')
    proj_export.add_argument('--audit-log', help='Optional export audit event JSONL log path; requires --audit-manifest')
    proj_export.add_argument('--audit-db', help='Optional SQLite audit event mirror path; requires --audit-log')
    proj_export.add_argument(
        '--verify-audit-manifest',
        action='store_true',
        help='Immediately verify the written audit manifest against exported artifacts',
    )
    proj_export.add_argument(
        '--publish-preflight',
        action='store_true',
        help='Run export publish preflight after writing the audit manifest',
    )
    proj_export.add_argument(
        '--scope-lint',
        action='store_true',
        help='With --publish-preflight, lint textual artifacts for unsafe corpus-scope phrasing',
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
    proj_recode_refresh_group = proj_recode.add_mutually_exclusive_group()
    proj_recode_refresh_group.add_argument(
        '--refresh-higher-order',
        action='store_true',
        default=False,
        help=(
            'Refresh methodology-specific higher-order outputs after '
            'incremental coding'
        ),
    )
    proj_recode_refresh_group.add_argument(
        '--no-refresh-higher-order',
        action='store_true',
        default=False,
        help='Force hard-invalidation mode for this recode run',
    )

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
        elif args.command == 'bench-package':
            return handle_bench_package_command(args)
        elif args.command == 'write-phase0-adjudication-package':
            return handle_write_phase0_adjudication_package_command(args)
        elif args.command == 'validate-adjudication-protocol':
            return handle_validate_adjudication_protocol_command(args)
        elif args.command == 'adjudication-protocol-preflight':
            return handle_adjudication_protocol_preflight_command(args)
        elif args.command == 'validate-adjudication-responses':
            return handle_validate_adjudication_responses_command(args)
        elif args.command == 'adjudication-response-preflight':
            return handle_adjudication_response_preflight_command(args)
        elif args.command == 'import-adjudication-responses':
            return handle_import_adjudication_responses_command(args)
        elif args.command == 'validate-theoretical-sampling-protocol':
            return handle_validate_theoretical_sampling_protocol_command(args)
        elif args.command == 'theoretical-sampling-preflight':
            return handle_theoretical_sampling_preflight_command(args)
        elif args.command == 'export-theoretical-sampling-candidates':
            return handle_export_theoretical_sampling_candidates_command(args)
        elif args.command == 'export-theoretical-sampling-results':
            return handle_export_theoretical_sampling_results_command(args)
        elif args.command == 'validate-d4-codebook-quality-protocol':
            return handle_validate_d4_codebook_quality_protocol_command(args)
        elif args.command == 'd4-codebook-quality-preflight':
            return handle_d4_codebook_quality_preflight_command(args)
        elif args.command == 'validate-d6-bias-protocol':
            return handle_validate_d6_bias_protocol_command(args)
        elif args.command == 'd6-bias-preflight':
            return handle_d6_bias_preflight_command(args)
        elif args.command == 'validate-d8-gt-fidelity-protocol':
            return handle_validate_d8_gt_fidelity_protocol_command(args)
        elif args.command == 'd8-gt-fidelity-preflight':
            return handle_d8_gt_fidelity_preflight_command(args)
        elif args.command == 'validate-sampling-frame-adequacy-protocol':
            return handle_validate_sampling_frame_adequacy_protocol_command(args)
        elif args.command == 'sampling-frame-adequacy-preflight':
            return handle_sampling_frame_adequacy_preflight_command(args)
        elif args.command == 'validate-d9-interpretive-preference-protocol':
            return handle_validate_d9_interpretive_preference_protocol_command(args)
        elif args.command == 'd9-interpretive-preference-preflight':
            return handle_d9_interpretive_preference_preflight_command(args)
        elif args.command == 'validate-confidence-calibration-protocol':
            return handle_validate_confidence_calibration_protocol_command(args)
        elif args.command == 'confidence-calibration-preflight':
            return handle_confidence_calibration_preflight_command(args)
        elif args.command == 'verify-phase0-benchmark-artifact':
            return handle_verify_phase0_benchmark_artifact_command(args)
        elif args.command == 'export-audit-manifest':
            return handle_export_audit_manifest_command(args)
        elif args.command == 'verify-export-audit-manifest':
            return handle_verify_export_audit_manifest_command(args)
        elif args.command == 'export-publish-preflight':
            return handle_export_publish_preflight_command(args)
        elif args.command == 'verify-export-audit-log':
            return handle_verify_export_audit_log_command(args)
        elif args.command == 'mirror-export-audit-db':
            return handle_mirror_export_audit_db_command(args)
        elif args.command == 'verify-export-audit-db':
            return handle_verify_export_audit_db_command(args)
        elif args.command == 'lint-scope-phrasing':
            return handle_lint_scope_phrasing_command(args)
        elif args.command == 'lint-prompt-overrides':
            return handle_lint_prompt_overrides_command(args)
        elif args.command == 'run-d7-retrieval':
            return handle_run_d7_retrieval_command(args)
        elif args.command == 'run-d7-live-baseline':
            return handle_run_d7_live_baseline_command(args)
        elif args.command == 'compare-d7-retrieval':
            return handle_compare_d7_retrieval_command(args)
        elif args.command == 'verify-d7-comparison-artifact':
            return handle_verify_d7_comparison_artifact_command(args)
        elif args.command == 'compare-d7-package':
            return handle_compare_d7_package_command(args)
        elif args.command == 'write-d7-comparison-package':
            return handle_write_d7_comparison_package_command(args)
        elif args.command == 'validate-d3-gold':
            return handle_validate_d3_gold_command(args)
        elif args.command == 'validate-d7-gold':
            return handle_validate_d7_gold_command(args)
        elif args.command == 'validate-d3-baseline-package':
            return handle_validate_d3_baseline_package_command(args)
        elif args.command == 'validate-d3-comparison-protocol':
            return handle_validate_d3_comparison_protocol_command(args)
        elif args.command == 'd3-comparison-preflight':
            return handle_d3_comparison_preflight_command(args)
        elif args.command == 'validate-d7-baseline-package':
            return handle_validate_d7_baseline_package_command(args)
        elif args.command == 'validate-d7-comparison-protocol':
            return handle_validate_d7_comparison_protocol_command(args)
        elif args.command == 'd7-comparison-preflight':
            return handle_d7_comparison_preflight_command(args)
        elif args.command == 'run-inv7-fixtures':
            return handle_run_inv7_fixtures_command(args)
        elif args.command == 'run-inv7-live-fixtures':
            return handle_run_inv7_live_fixtures_command(args)
        elif args.command == 'validate-inv7-package':
            return handle_validate_inv7_package_command(args)
        elif args.command == 'validate-inv7-live-protocol':
            return handle_validate_inv7_live_protocol_command(args)
        elif args.command == 'inv7-live-preflight':
            return handle_inv7_live_preflight_command(args)
        elif args.command == 'compare-inv7-packages':
            return handle_compare_inv7_packages_command(args)
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
    if args.d3_baselines_file:
        argv.extend(["--d3-baselines-file", args.d3_baselines_file])
    if args.d3_comparison_protocol_file:
        argv.extend([
            "--d3-comparison-protocol-file",
            args.d3_comparison_protocol_file,
        ])
    if args.gold_file:
        argv.extend(["--gold-file", args.gold_file])
    if args.d7_baselines_file:
        argv.extend(["--d7-baselines-file", args.d7_baselines_file])
    if args.prompt_injection_file:
        argv.extend(["--prompt-injection-file", args.prompt_injection_file])
    if args.inv7_live_protocol_file:
        argv.extend(["--inv7-live-protocol-file", args.inv7_live_protocol_file])
    if args.d6_bias_protocol_file:
        argv.extend(["--d6-bias-protocol-file", args.d6_bias_protocol_file])
    if args.bias_counterfactual_file:
        argv.extend(["--bias-counterfactual-file", args.bias_counterfactual_file])
    if args.bias_stratified_file:
        argv.extend(["--bias-stratified-file", args.bias_stratified_file])
    if args.d4_codebook_quality_protocol_file:
        argv.extend([
            "--d4-codebook-quality-protocol-file",
            args.d4_codebook_quality_protocol_file,
        ])
    if args.codebook_quality_file:
        argv.extend(["--codebook-quality-file", args.codebook_quality_file])
    if args.d8_gt_fidelity_protocol_file:
        argv.extend(["--d8-gt-fidelity-protocol-file", args.d8_gt_fidelity_protocol_file])
    if args.gt_fidelity_file:
        argv.extend(["--gt-fidelity-file", args.gt_fidelity_file])
    if args.interpretive_preference_file:
        argv.extend(["--interpretive-preference-file", args.interpretive_preference_file])
    if args.d9_interpretive_preference_protocol_file:
        argv.extend([
            "--d9-interpretive-preference-protocol-file",
            args.d9_interpretive_preference_protocol_file,
        ])
    if args.confidence_calibration_file:
        argv.extend(["--confidence-calibration-file", args.confidence_calibration_file])
    if args.confidence_calibration_protocol_file:
        argv.extend([
            "--confidence-calibration-protocol-file",
            args.confidence_calibration_protocol_file,
        ])
    if args.observability_db:
        argv.extend(["--observability-db", args.observability_db])
    if args.trace_id:
        argv.extend(["--trace-id", args.trace_id])
    if args.output:
        argv.extend(["--output", args.output])
    if args.artifact_dir:
        argv.extend(["--artifact-dir", args.artifact_dir])
    return bench_phase0.main(argv)


def handle_bench_package_command(args) -> int:
    """Run a Phase 0 benchmark package through the canonical CLI."""
    from scripts import run_phase0_benchmark_package

    return run_phase0_benchmark_package.main([args.package_file])


def handle_write_phase0_adjudication_package_command(args) -> int:
    """Write a Phase 0 adjudication package through the canonical CLI."""
    from scripts import write_phase0_adjudication_package

    argv = [args.project_id, "--output", args.output]
    for attr, flag in [
        ("d3_gold_file", "--d3-gold-file"),
        ("d7_gold_file", "--d7-gold-file"),
        ("scorecard_output", "--scorecard-output"),
        ("artifact_dir", "--artifact-dir"),
        ("observability_db", "--observability-db"),
        ("trace_id", "--trace-id"),
    ]:
        value = getattr(args, attr)
        if value is not None:
            argv.extend([flag, str(value)])
    return write_phase0_adjudication_package.main(argv)


def handle_validate_adjudication_protocol_command(args) -> int:
    """Validate an adjudication protocol package through the canonical CLI."""
    from scripts import validate_adjudication_protocol

    return validate_adjudication_protocol.main([args.protocol])


def handle_adjudication_protocol_preflight_command(args) -> int:
    """Preflight an adjudication protocol/sample pair through the canonical CLI."""
    from scripts import preflight_adjudication_protocol_sample

    return preflight_adjudication_protocol_sample.main([args.protocol, args.sample])


def handle_validate_adjudication_responses_command(args) -> int:
    """Validate adjudication responses through the canonical CLI."""
    from scripts import validate_adjudication_responses

    return validate_adjudication_responses.main([args.package])


def handle_adjudication_response_preflight_command(args) -> int:
    """Preflight adjudication responses through the canonical CLI."""
    from scripts import preflight_adjudication_responses

    return preflight_adjudication_responses.main([
        args.protocol,
        args.sample,
        args.responses,
    ])


def handle_import_adjudication_responses_command(args) -> int:
    """Import adjudication responses through the canonical CLI."""
    from scripts import import_adjudication_responses

    argv = [args.package]
    for attr, flag in [
        ("output_d3", "--output-d3"),
        ("output_d7", "--output-d7"),
    ]:
        value = getattr(args, attr)
        if value is not None:
            argv.extend([flag, str(value)])
    argv.extend([
        "--gold-set-id",
        args.gold_set_id,
        "--dataset-name",
        args.dataset_name,
    ])
    if args.split is not None:
        argv.extend(["--split", args.split])
    argv.extend([
        "--coder-count",
        str(args.coder_count),
        "--adjudicator",
        args.adjudicator,
        "--protocol",
        args.protocol,
    ])
    for attr, flag in [
        ("protocol_package", "--protocol-package"),
        ("sample_package", "--sample-package"),
    ]:
        value = getattr(args, attr)
        if value is not None:
            argv.extend([flag, str(value)])
    if args.prompt_frozen:
        argv.append("--prompt-frozen")
    if args.contamination_checked:
        argv.append("--contamination-checked")
    if args.notes is not None:
        argv.extend(["--notes", args.notes])
    return import_adjudication_responses.main(argv)


def handle_validate_theoretical_sampling_protocol_command(args) -> int:
    """Validate a theoretical-sampling protocol through the canonical CLI."""
    from scripts import validate_theoretical_sampling_protocol

    return validate_theoretical_sampling_protocol.main([args.protocol])


def handle_theoretical_sampling_preflight_command(args) -> int:
    """Preflight theoretical-sampling packages through the canonical CLI."""
    from scripts import preflight_theoretical_sampling_protocol

    argv = [args.protocol, "--candidates-file", args.candidates_file]
    if args.results_file is not None:
        argv.extend(["--results-file", args.results_file])
    return preflight_theoretical_sampling_protocol.main(argv)


def handle_export_theoretical_sampling_candidates_command(args) -> int:
    """Export theoretical-sampling candidates through the canonical CLI."""
    from scripts import export_theoretical_sampling_candidates

    argv = [args.project_id]
    if args.projects_dir is not None:
        argv.extend(["--projects-dir", args.projects_dir])
    argv.extend(["--protocol", args.protocol])
    if args.output is not None:
        argv.extend(["--output", args.output])
    for candidate_name in args.candidate_names or []:
        argv.extend(["--candidate-name", candidate_name])
    if args.max_suggestions is not None:
        argv.extend(["--max-suggestions", str(args.max_suggestions)])
    return export_theoretical_sampling_candidates.main(argv)


def handle_export_theoretical_sampling_results_command(args) -> int:
    """Export theoretical-sampling results through the canonical CLI."""
    from scripts import export_theoretical_sampling_results

    argv = [args.protocol, "--candidates-file", args.candidates_file]
    for selected_candidate_id in args.selected_candidate_ids:
        argv.extend(["--selected-candidate-id", selected_candidate_id])
    for success_criterion_met in args.success_criteria_met:
        argv.extend(["--success-criterion-met", success_criterion_met])
    if args.stopped_by_rule:
        argv.append("--stopped-by-rule")
    if args.output is not None:
        argv.extend(["--output", args.output])
    return export_theoretical_sampling_results.main(argv)


def handle_validate_d4_codebook_quality_protocol_command(args) -> int:
    """Validate a D4 codebook-quality protocol through the canonical CLI."""
    from scripts import validate_d4_codebook_quality_protocol

    return validate_d4_codebook_quality_protocol.main([args.protocol])


def handle_d4_codebook_quality_preflight_command(args) -> int:
    """Preflight D4 codebook-quality results through the canonical CLI."""
    from scripts import preflight_d4_codebook_quality_protocol

    argv = [args.protocol]
    if args.quality_file is not None:
        argv.extend(["--quality-file", args.quality_file])
    return preflight_d4_codebook_quality_protocol.main(argv)


def handle_validate_d6_bias_protocol_command(args) -> int:
    """Validate a D6 bias protocol through the canonical CLI."""
    from scripts import validate_d6_bias_protocol

    return validate_d6_bias_protocol.main([args.protocol])


def handle_d6_bias_preflight_command(args) -> int:
    """Preflight D6 bias results through the canonical CLI."""
    from scripts import preflight_d6_bias_protocol

    argv = [args.protocol]
    if args.stratified_file is not None:
        argv.extend(["--stratified-file", args.stratified_file])
    if args.counterfactual_file is not None:
        argv.extend(["--counterfactual-file", args.counterfactual_file])
    return preflight_d6_bias_protocol.main(argv)


def handle_validate_d8_gt_fidelity_protocol_command(args) -> int:
    """Validate a D8 GT-fidelity protocol through the canonical CLI."""
    from scripts import validate_d8_gt_fidelity_protocol

    return validate_d8_gt_fidelity_protocol.main([args.protocol])


def handle_d8_gt_fidelity_preflight_command(args) -> int:
    """Preflight D8 GT-fidelity results through the canonical CLI."""
    from scripts import preflight_d8_gt_fidelity_protocol

    argv = [args.protocol]
    if args.gt_fidelity_file is not None:
        argv.extend(["--gt-fidelity-file", args.gt_fidelity_file])
    return preflight_d8_gt_fidelity_protocol.main(argv)


def handle_validate_sampling_frame_adequacy_protocol_command(args) -> int:
    """Validate a sampling-frame adequacy protocol through the canonical CLI."""
    from scripts import validate_sampling_frame_adequacy_protocol

    return validate_sampling_frame_adequacy_protocol.main([args.protocol])


def handle_sampling_frame_adequacy_preflight_command(args) -> int:
    """Preflight sampling-frame adequacy results through the canonical CLI."""
    from scripts import preflight_sampling_frame_adequacy_protocol

    argv = [args.protocol]
    if args.adequacy_file is not None:
        argv.extend(["--adequacy-file", args.adequacy_file])
    return preflight_sampling_frame_adequacy_protocol.main(argv)


def handle_validate_d9_interpretive_preference_protocol_command(args) -> int:
    """Validate a D9 interpretive-preference protocol through the canonical CLI."""
    from scripts import validate_d9_interpretive_preference_protocol

    return validate_d9_interpretive_preference_protocol.main([args.protocol])


def handle_d9_interpretive_preference_preflight_command(args) -> int:
    """Preflight D9 interpretive-preference results through the canonical CLI."""
    from scripts import preflight_d9_interpretive_preference_protocol

    argv = [args.protocol]
    if args.preference_file is not None:
        argv.extend(["--preference-file", args.preference_file])
    return preflight_d9_interpretive_preference_protocol.main(argv)


def handle_validate_confidence_calibration_protocol_command(args) -> int:
    """Validate a confidence-calibration protocol through the canonical CLI."""
    from scripts import validate_confidence_calibration_protocol

    return validate_confidence_calibration_protocol.main([args.protocol])


def handle_confidence_calibration_preflight_command(args) -> int:
    """Preflight confidence-calibration results through the canonical CLI."""
    from scripts import preflight_confidence_calibration_protocol

    argv = [args.protocol]
    if args.calibration_file is not None:
        argv.extend(["--calibration-file", args.calibration_file])
    return preflight_confidence_calibration_protocol.main(argv)


def handle_verify_phase0_benchmark_artifact_command(args) -> int:
    """Verify a Phase 0 benchmark artifact through the canonical CLI."""
    from scripts import verify_phase0_benchmark_artifact

    return verify_phase0_benchmark_artifact.main([args.artifact])


def handle_export_audit_manifest_command(args) -> int:
    """Write an export audit manifest through the canonical CLI."""
    from scripts import write_export_audit_manifest

    argv = [args.project_id, "--format", args.format]
    for artifact_path in args.artifact:
        argv.extend(["--artifact", artifact_path])
    argv.extend(["--output", args.output])
    for attr, flag in [
        ("base_dir", "--base-dir"),
        ("projects_dir", "--projects-dir"),
        ("audit_log", "--audit-log"),
        ("audit_db", "--audit-db"),
    ]:
        value = getattr(args, attr)
        if value is not None:
            argv.extend([flag, value])
    return write_export_audit_manifest.main(argv)


def handle_verify_export_audit_manifest_command(args) -> int:
    """Verify an export audit manifest through the canonical CLI."""
    from scripts import verify_export_audit_manifest

    argv = [args.manifest]
    for attr, flag in [
        ("base_dir", "--base-dir"),
        ("project_id", "--project-id"),
        ("projects_dir", "--projects-dir"),
        ("audit_log", "--audit-log"),
        ("audit_db", "--audit-db"),
    ]:
        value = getattr(args, attr)
        if value is not None:
            argv.extend([flag, value])
    return verify_export_audit_manifest.main(argv)


def handle_export_publish_preflight_command(args) -> int:
    """Run export publish preflight through the canonical CLI."""
    from scripts import export_publish_preflight

    argv = ["--manifest", args.manifest]
    for attr, flag in [
        ("base_dir", "--base-dir"),
        ("project_id", "--project-id"),
        ("projects_dir", "--projects-dir"),
        ("audit_log", "--audit-log"),
        ("audit_db", "--audit-db"),
    ]:
        value = getattr(args, attr)
        if value is not None:
            argv.extend([flag, value])
    if args.scope_lint:
        argv.append("--scope-lint")
    return export_publish_preflight.main(argv)


def handle_verify_export_audit_log_command(args) -> int:
    """Verify an export audit event log through the canonical CLI."""
    from scripts import verify_export_audit_event_log

    return verify_export_audit_event_log.main([args.log])


def handle_mirror_export_audit_db_command(args) -> int:
    """Mirror an export audit event log into SQLite through the canonical CLI."""
    from scripts import mirror_export_audit_event_log_db

    return mirror_export_audit_event_log_db.main([args.log, "--db", args.db])


def handle_verify_export_audit_db_command(args) -> int:
    """Verify an export audit SQLite mirror through the canonical CLI."""
    from scripts import verify_export_audit_event_db

    return verify_export_audit_event_db.main([args.db])


def handle_lint_scope_phrasing_command(args) -> int:
    """Lint scope-sensitive phrasing through the canonical CLI."""
    from scripts import lint_scope_phrasing

    argv = [args.project_id]
    if args.input_file is not None:
        argv.extend(["--input-file", args.input_file])
    if args.text is not None:
        argv.extend(["--text", args.text])
    if args.projects_dir is not None:
        argv.extend(["--projects-dir", args.projects_dir])
    return lint_scope_phrasing.main(argv)


def handle_lint_prompt_overrides_command(args) -> int:
    """Lint prompt override registry consistency through the canonical CLI."""
    from scripts import check_prompt_override_registry

    argv = []
    if args.root is not None:
        argv.extend(["--root", args.root])
    return check_prompt_override_registry.main(argv)


def handle_run_d7_retrieval_command(args) -> int:
    """Export D7 retrieval predictions through the canonical CLI."""
    from scripts import run_d7_retrieval

    argv = [args.project_id]
    for attr, flag in [
        ("projects_dir", "--projects-dir"),
        ("output", "--output"),
        ("name", "--name"),
        ("description", "--description"),
        ("max_targets", "--max-targets"),
        ("candidates_per_claim", "--candidates-per-claim"),
        ("retrieval_mode", "--retrieval-mode"),
        ("bm25_k1", "--bm25-k1"),
        ("bm25_b", "--bm25-b"),
        ("contrary_cue_weight", "--contrary-cue-weight"),
        ("expanded_term_weight", "--expanded-term-weight"),
        ("embedding_model", "--embedding-model"),
        ("embedding_dimensions", "--embedding-dimensions"),
        ("semantic_weight", "--semantic-weight"),
        ("min_semantic_similarity", "--min-semantic-similarity"),
        ("trace_id", "--trace-id"),
        ("max_budget", "--max-budget"),
    ]:
        value = getattr(args, attr)
        if value is not None:
            argv.extend([flag, str(value)])
    return run_d7_retrieval.main(argv)


def handle_run_d7_live_baseline_command(args) -> int:
    """Export live D7 baseline predictions through the canonical CLI."""
    from scripts import run_d7_live_baseline

    argv = [args.project_id]
    for attr, flag in [
        ("projects_dir", "--projects-dir"),
        ("output", "--output"),
        ("name", "--name"),
        ("description", "--description"),
        ("model", "--model"),
        ("max_targets", "--max-targets"),
        ("candidates_per_claim", "--candidates-per-claim"),
        ("retrieval_mode", "--retrieval-mode"),
        ("bm25_k1", "--bm25-k1"),
        ("bm25_b", "--bm25-b"),
        ("contrary_cue_weight", "--contrary-cue-weight"),
        ("expanded_term_weight", "--expanded-term-weight"),
        ("embedding_model", "--embedding-model"),
        ("embedding_dimensions", "--embedding-dimensions"),
        ("semantic_weight", "--semantic-weight"),
        ("min_semantic_similarity", "--min-semantic-similarity"),
        ("trace_id", "--trace-id"),
        ("max_budget", "--max-budget"),
    ]:
        value = getattr(args, attr)
        if value is not None:
            argv.extend([flag, str(value)])
    return run_d7_live_baseline.main(argv)


def handle_compare_d7_retrieval_command(args) -> int:
    """Compare D7 retrieval prediction packages through the canonical CLI."""
    from scripts import compare_d7_retrieval

    argv = [args.project_id, "--gold-file", args.gold_file]
    if args.projects_dir is not None:
        argv[1:1] = ["--projects-dir", args.projects_dir]
    for prediction_file in args.predictions_file:
        argv.extend(["--predictions-file", prediction_file])
    if args.output is not None:
        argv.extend(["--output", args.output])
    if args.protocol_package is not None:
        argv.extend(["--protocol-package", args.protocol_package])
    if args.artifact_dir is not None:
        argv.extend(["--artifact-dir", args.artifact_dir])
    return compare_d7_retrieval.main(argv)


def handle_verify_d7_comparison_artifact_command(args) -> int:
    """Verify a D7 comparison artifact through the canonical CLI."""
    from scripts import verify_d7_comparison_artifact

    return verify_d7_comparison_artifact.main([args.artifact])


def handle_compare_d7_package_command(args) -> int:
    """Run a D7 comparison package through the canonical CLI."""
    from scripts import run_d7_comparison_package

    return run_d7_comparison_package.main([args.package_file])


def handle_write_d7_comparison_package_command(args) -> int:
    """Write a D7 comparison package through the canonical CLI."""
    from scripts import write_d7_comparison_package

    argv = [args.project_id]
    if args.projects_dir is not None:
        argv.extend(["--projects-dir", args.projects_dir])
    argv.extend(["--output", args.output, "--gold-file", args.gold_file])
    for prediction_file in args.predictions_file:
        argv.extend(["--predictions-file", prediction_file])
    if args.protocol_package is not None:
        argv.extend(["--protocol-package", args.protocol_package])
    if args.comparison_output is not None:
        argv.extend(["--comparison-output", args.comparison_output])
    if args.artifact_dir is not None:
        argv.extend(["--artifact-dir", args.artifact_dir])
    if args.verify_artifact:
        argv.append("--verify-artifact")
    return write_d7_comparison_package.main(argv)


def handle_validate_d3_gold_command(args) -> int:
    """Validate a D3 gold-set package through the canonical CLI."""
    from scripts import validate_d3_gold_set

    return validate_d3_gold_set.main([args.gold_set])


def handle_validate_d7_gold_command(args) -> int:
    """Validate a D7 gold-set package through the canonical CLI."""
    from scripts import validate_d7_gold_set

    return validate_d7_gold_set.main([args.gold_set])


def handle_validate_d3_baseline_package_command(args) -> int:
    """Validate a D3 baseline package through the canonical CLI."""
    from scripts import validate_d3_baseline_package

    return validate_d3_baseline_package.main([args.package_file])


def handle_validate_d3_comparison_protocol_command(args) -> int:
    """Validate a D3 comparison protocol through the canonical CLI."""
    from scripts import validate_d3_comparison_protocol

    return validate_d3_comparison_protocol.main([args.protocol])


def handle_d3_comparison_preflight_command(args) -> int:
    """Preflight D3 comparison inputs through the canonical CLI."""
    from scripts import preflight_d3_comparison

    return preflight_d3_comparison.main([args.protocol, args.gold, *args.predictions])


def handle_validate_d7_baseline_package_command(args) -> int:
    """Validate a D7 baseline package through the canonical CLI."""
    from scripts import validate_d7_baseline_package

    return validate_d7_baseline_package.main([args.package_file])


def handle_validate_d7_comparison_protocol_command(args) -> int:
    """Validate a D7 comparison protocol through the canonical CLI."""
    from scripts import validate_d7_comparison_protocol

    return validate_d7_comparison_protocol.main([args.protocol])


def handle_d7_comparison_preflight_command(args) -> int:
    """Preflight D7 comparison inputs through the canonical CLI."""
    from scripts import preflight_d7_comparison

    return preflight_d7_comparison.main([args.protocol, args.gold, *args.predictions])


def handle_run_inv7_fixtures_command(args) -> int:
    """Run structural INV-7 fixtures through the canonical CLI."""
    from scripts import run_inv7_fixtures

    return run_inv7_fixtures.main(["--output", args.output])


def handle_run_inv7_live_fixtures_command(args) -> int:
    """Run live INV-7 fixtures through the canonical CLI."""
    from scripts import run_inv7_live_fixtures

    argv = ["--output", args.output]
    for attr, flag in [
        ("fixtures", "--fixtures"),
        ("model", "--model"),
        ("trace_id", "--trace-id"),
        ("max_budget", "--max-budget"),
    ]:
        value = getattr(args, attr)
        if value is not None:
            argv.extend([flag, str(value)])
    return run_inv7_live_fixtures.main(argv)


def handle_validate_inv7_package_command(args) -> int:
    """Validate an INV-7 prompt-injection package through the canonical CLI."""
    from scripts import validate_inv7_prompt_injection_package

    return validate_inv7_prompt_injection_package.main([args.package_file])


def handle_validate_inv7_live_protocol_command(args) -> int:
    """Validate an INV-7 live protocol through the canonical CLI."""
    from scripts import validate_inv7_live_protocol

    return validate_inv7_live_protocol.main([args.protocol_file])


def handle_inv7_live_preflight_command(args) -> int:
    """Preflight an INV-7 live package through the canonical CLI."""
    from scripts import preflight_inv7_live_package

    return preflight_inv7_live_package.main([args.protocol_file, args.package_file])


def handle_compare_inv7_packages_command(args) -> int:
    """Compare INV-7 packages through the canonical CLI."""
    from scripts import compare_inv7_packages

    argv = [*args.package_files]
    if args.output:
        argv.extend(["--output", args.output])
    return compare_inv7_packages.main(argv)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

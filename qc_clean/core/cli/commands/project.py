"""
Project management CLI command handlers.
"""

import asyncio
import logging
import sys
from pathlib import Path

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import Methodology, PipelineStatus, ProjectConfig, ProjectState

logger = logging.getLogger(__name__)


def handle_project_command(args) -> int:
    """Route project subcommands."""
    store = ProjectStore()

    if args.project_action == "create":
        return _create_project(store, args)
    elif args.project_action == "list":
        return _list_projects(store)
    elif args.project_action == "show":
        return _show_project(store, args)
    elif args.project_action == "add-docs":
        return _add_docs(store, args)
    elif args.project_action == "run":
        return _run_project(store, args)
    elif args.project_action == "export":
        return _export_project(store, args)
    elif args.project_action == "irr":
        return _run_irr(store, args)
    elif args.project_action == "stability":
        return _run_stability(store, args)
    else:
        print(f"Unknown project action: {args.project_action}", file=sys.stderr)
        return 1


def _create_project(store: ProjectStore, args) -> int:
    name = getattr(args, "name", "Untitled")
    methodology = getattr(args, "methodology", "default")

    try:
        meth = Methodology(methodology)
    except ValueError:
        meth = Methodology.DEFAULT

    state = ProjectState(
        name=name,
        config=ProjectConfig(methodology=meth),
    )
    path = store.save(state)
    print(f"Created project: {state.id}")
    print(f"  Name: {state.name}")
    print(f"  Methodology: {meth.value}")
    print(f"  Saved to: {path}")
    return 0


def _list_projects(store: ProjectStore) -> int:
    projects = store.list_projects()
    if not projects:
        print("No projects found.")
        return 0

    print(f"{'ID':<40} {'Name':<30} {'Status':<15} {'Updated'}")
    print("-" * 100)
    for p in projects:
        print(f"{p['id']:<40} {p['name']:<30} {p.get('pipeline_status', ''):<15} {p.get('updated_at', '')[:19]}")
    return 0


def _show_project(store: ProjectStore, args) -> int:
    project_id = args.project_id
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        print(f"Project not found: {project_id}", file=sys.stderr)
        return 1

    print(f"Project: {state.name}")
    print(f"  ID: {state.id}")
    print(f"  Methodology: {state.config.methodology.value}")
    print(f"  Pipeline: {state.pipeline_status.value}")
    print(f"  Documents: {state.corpus.num_documents}")
    print(f"  Codes: {len(state.codebook.codes)}")
    print(f"  Applications: {len(state.code_applications)}")
    print(f"  Iteration: {state.iteration}")
    print(f"  Updated: {state.updated_at}")

    if state.phase_results:
        print("\n  Phases:")
        for pr in state.phase_results:
            print(f"    - {pr.phase_name}: {pr.status.value}")

    return 0


def _add_docs(store: ProjectStore, args) -> int:
    project_id = args.project_id
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        print(f"Project not found: {project_id}", file=sys.stderr)
        return 1

    from qc_clean.core.cli.utils.file_handler import discover_files, read_file_content

    files = args.files or []
    if args.directory:
        files.extend(discover_files(args.directory))

    if not files:
        print("No files specified.", file=sys.stderr)
        return 1

    from qc_clean.schemas.domain import Document

    added = 0
    for file_path in files:
        try:
            content = read_file_content(file_path)
            doc = Document(name=Path(file_path).name, content=content)
            state.corpus.add_document(doc)
            added += 1
            print(f"  Added: {doc.name}")
        except Exception as e:
            print(f"  Failed to add {file_path}: {e}", file=sys.stderr)

    store.save(state)
    print(f"\nAdded {added} documents to project {state.name}")
    return 0


def _run_project(store: ProjectStore, args) -> int:
    """Run the analysis pipeline on a saved project."""
    project_id = args.project_id
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        print(f"Project not found: {project_id}", file=sys.stderr)
        return 1

    if state.corpus.num_documents == 0:
        print("No documents in project. Add documents first with 'project add-docs'.", file=sys.stderr)
        return 1

    if state.pipeline_status == PipelineStatus.COMPLETED:
        print("Pipeline already completed for this project.", file=sys.stderr)
        print("  To re-run, create a new project or reset the pipeline status.")
        return 1

    # Determine resume point
    resume_from = None
    if state.pipeline_status == PipelineStatus.PAUSED_FOR_REVIEW:
        from qc_clean.core.pipeline.review import ReviewManager
        rm = ReviewManager(state)
        if rm.can_resume():
            resume_from = rm.prepare_for_resume()
            print(f"Resuming pipeline from: {resume_from}")
        else:
            print("Pipeline is paused but cannot resume. Check review status.", file=sys.stderr)
            return 1

    # Build pipeline with save-after-each-stage callback
    from qc_clean.core.pipeline.pipeline_factory import create_pipeline

    async def save_callback(s):
        store.save(s)

    enable_review = getattr(args, "review", False)
    pipeline = create_pipeline(
        methodology=state.config.methodology.value,
        on_stage_complete=save_callback,
        enable_human_review=enable_review,
    )

    model_name = getattr(args, "model", None) or state.config.model_name
    config = {"model_name": model_name}

    print(f"Running pipeline on project: {state.name}")
    print(f"  Methodology: {state.config.methodology.value}")
    print(f"  Documents: {state.corpus.num_documents}")
    print(f"  Model: {model_name}")
    if enable_review:
        print("  Human review: enabled")
    print()

    try:
        state = asyncio.run(pipeline.run(state, config, resume_from=resume_from))
    except Exception as e:
        store.save(state)
        print(f"\nPipeline failed: {e}", file=sys.stderr)
        return 1

    store.save(state)

    # Print summary
    if state.pipeline_status == PipelineStatus.PAUSED_FOR_REVIEW:
        print(f"\nPipeline paused for human review after: {state.current_phase}")
        print(f"  Codes discovered: {len(state.codebook.codes)}")
        print(f"  Review in browser: http://localhost:8002/review/{project_id}")
        print(f"  Review with CLI:   qc_cli review {project_id}")
        print(f"  Then resume:       qc_cli project run {project_id}")
    elif state.pipeline_status == PipelineStatus.COMPLETED:
        print("\nPipeline completed successfully.")
        print(f"  Codes: {len(state.codebook.codes)}")
        print(f"  Applications: {len(state.code_applications)}")
        print(f"  Entities: {len(state.entities)}")
        if state.synthesis:
            print(f"  Key findings: {len(state.synthesis.key_findings)}")
            print(f"  Recommendations: {len(state.synthesis.recommendations)}")
        if state.core_categories:
            print(f"  Core categories: {len(state.core_categories)}")
        if state.theoretical_model:
            print(f"  Theoretical model: {state.theoretical_model.model_name}")
        print(f"\n  Export with: qc_cli project export {project_id} --format json")
    else:
        print(f"\nPipeline ended with status: {state.pipeline_status.value}")

    return 0


def _export_project(store: ProjectStore, args) -> int:
    """Export project results to a file."""
    project_id = args.project_id
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        print(f"Project not found: {project_id}", file=sys.stderr)
        return 1

    if len(state.codebook.codes) == 0 and state.pipeline_status == PipelineStatus.PENDING:
        print("No analysis results to export. Run the pipeline first.", file=sys.stderr)
        return 1

    from qc_clean.core.export.data_exporter import ProjectExporter

    fmt = getattr(args, "format", "json")
    output_file = getattr(args, "output_file", None)
    output_dir = getattr(args, "output_dir", None)

    try:
        exporter = ProjectExporter()

        if fmt == "json":
            path = exporter.export_json(state, output_file)
            print(f"Exported JSON to: {path}")
        elif fmt == "csv":
            paths = exporter.export_csv(state, output_dir)
            print("Exported CSV files:")
            for p in paths:
                print(f"  {p}")
        elif fmt == "markdown":
            path = exporter.export_markdown(state, output_file)
            print(f"Exported Markdown to: {path}")
        elif fmt == "qdpx":
            path = exporter.export_qdpx(state, output_file)
            print(f"Exported QDPX to: {path}")
            print("  Compatible with ATLAS.ti, NVivo, MAXQDA")
        else:
            print(f"Unsupported format: {fmt}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Export failed: {e}", file=sys.stderr)
        return 1

    return 0


def _run_irr(store: ProjectStore, args) -> int:
    """Run inter-rater reliability analysis on a project."""
    project_id = args.project_id
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        print(f"Project not found: {project_id}", file=sys.stderr)
        return 1

    if state.corpus.num_documents == 0:
        print("No documents in project. Add documents first.", file=sys.stderr)
        return 1

    from qc_clean.core.pipeline.irr import run_irr_analysis

    num_passes = getattr(args, "passes", 3)
    model_name = getattr(args, "model", None) or state.config.model_name
    models = getattr(args, "models", None)

    print(f"Running IRR analysis on project: {state.name}")
    print(f"  Methodology: {state.config.methodology.value}")
    print(f"  Passes: {num_passes}")
    print(f"  Model: {model_name}")
    if models:
        print(f"  Model rotation: {', '.join(models)}")
    print()

    try:
        result = asyncio.run(run_irr_analysis(
            state,
            num_passes=num_passes,
            model_name=model_name,
            models=models,
        ))
    except Exception as e:
        print(f"\nIRR analysis failed: {e}", file=sys.stderr)
        return 1

    state.irr_result = result
    store.save(state)

    # Print summary
    print("\nIRR Analysis Complete")
    print(f"  Passes: {result.num_passes}")
    print(f"  Aligned codes: {len(result.aligned_codes)}")
    print(f"  Unmatched codes: {len(result.unmatched_codes)}")
    print(f"  Percent agreement: {result.percent_agreement:.1%}")
    if result.cohens_kappa is not None:
        print(f"  Cohen's kappa: {result.cohens_kappa:.3f}")
    if result.fleiss_kappa is not None:
        print(f"  Fleiss' kappa: {result.fleiss_kappa:.3f}")
    print(f"  Interpretation: {result.interpretation}")

    return 0


def _run_stability(store: ProjectStore, args) -> int:
    """Run multi-run stability analysis on a project."""
    project_id = args.project_id
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        print(f"Project not found: {project_id}", file=sys.stderr)
        return 1

    if state.corpus.num_documents == 0:
        print("No documents in project. Add documents first.", file=sys.stderr)
        return 1

    from qc_clean.core.pipeline.irr import run_stability_analysis

    num_runs = getattr(args, "runs", 5)
    model_name = getattr(args, "model", None) or state.config.model_name

    print(f"Running stability analysis on project: {state.name}")
    print(f"  Methodology: {state.config.methodology.value}")
    print(f"  Runs: {num_runs}")
    print(f"  Model: {model_name}")
    print()

    try:
        result = asyncio.run(run_stability_analysis(
            state,
            num_runs=num_runs,
            model_name=model_name,
        ))
    except Exception as e:
        print(f"\nStability analysis failed: {e}", file=sys.stderr)
        return 1

    state.stability_result = result
    store.save(state)

    # Print summary
    print("\nStability Analysis Complete")
    print(f"  Runs: {result.num_runs}")
    print(f"  Model: {result.model_name}")
    print(f"  Overall stability: {result.overall_stability:.1%}")
    print(f"  Stable codes (>= 80%): {len(result.stable_codes)}")
    print(f"  Moderate codes (50-79%): {len(result.moderate_codes)}")
    print(f"  Unstable codes (< 50%): {len(result.unstable_codes)}")

    if result.stable_codes:
        print("\n  Stable codes:")
        for code in result.stable_codes:
            score = result.code_stability.get(code, 0)
            print(f"    - {code}: {score:.0%}")

    if result.unstable_codes:
        print("\n  Unstable codes (may not be reliable):")
        for code in result.unstable_codes:
            score = result.code_stability.get(code, 0)
            print(f"    - {code}: {score:.0%}")

    return 0

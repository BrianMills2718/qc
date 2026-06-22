"""
Project management CLI command handlers.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

from qc_clean.core.claims import summarize_claim_ledger, summarize_disconfirmation_coverage
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import (
    CorpusScope,
    Methodology,
    PipelineStatus,
    ProjectConfig,
    ProjectState,
)

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
    elif args.project_action == "claims":
        return _show_claims(store, args)
    elif args.project_action == "scope":
        return _show_or_update_scope(store, args)
    elif args.project_action == "add-docs":
        return _add_docs(store, args)
    elif args.project_action == "run":
        return _run_project(store, args)
    elif args.project_action == "export":
        return _export_project(store, args)
    elif args.project_action == "adjudication-sample":
        return _export_adjudication_sample(store, args)
    elif args.project_action == "irr":
        return _run_irr(store, args)
    elif args.project_action == "stability":
        return _run_stability(store, args)
    elif args.project_action == "recode":
        return _recode_project(store, args)
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
    state.corpus_scope = _scope_from_create_args(args)
    path = store.save(state)
    print(f"Created project: {state.id}")
    print(f"  Name: {state.name}")
    print(f"  Methodology: {meth.value}")
    if state.corpus_scope is not None:
        print("  Corpus scope: set")
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
    print(f"  Claims: {len(state.claims)}")
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
    if added == 0:
        return 1

    if getattr(args, "recode", False):
        print("\nRunning incremental recode for newly added documents...")
        recode_args = SimpleNamespace(
            project_id=project_id,
            model=getattr(args, "model", None),
            refresh_higher_order=getattr(args, "refresh_higher_order", False),
        )
        return _recode_project(store, recode_args)

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

    from qc_clean.core.pipeline.pipeline_engine import PipelineContext
    model_name = getattr(args, "model", None) or state.config.model_name
    exhaustive = bool(getattr(args, "exhaustive", False))
    ctx = PipelineContext(
        model_name=model_name,
        trace_id=f"qualitative_coding/project/{state.id}",
        exhaustive_coding=exhaustive,
    )
    run_started_at = datetime.now().isoformat()
    run_started_monotonic = perf_counter()

    print(f"Running pipeline on project: {state.name}")
    print(f"  Methodology: {state.config.methodology.value}")
    print(f"  Documents: {state.corpus.num_documents}")
    print(f"  Model: {model_name}")
    if exhaustive:
        print("  Exhaustive coding: every segment decided (INV-8)")
    if enable_review:
        print("  Human review: enabled")
    print()

    try:
        state = asyncio.run(pipeline.run(state, ctx, resume_from=resume_from))
    except Exception as e:
        _record_project_run_timing(
            state,
            started_at=run_started_at,
            duration_s=perf_counter() - run_started_monotonic,
            status=PipelineStatus.FAILED.value,
            trace_id=ctx.trace_id,
            model_name=model_name,
            exhaustive=exhaustive,
            resume_from=resume_from,
        )
        store.save(state)
        print(f"\nPipeline failed: {e}", file=sys.stderr)
        return 1

    _record_project_run_timing(
        state,
        started_at=run_started_at,
        duration_s=perf_counter() - run_started_monotonic,
        status=state.pipeline_status.value,
        trace_id=ctx.trace_id,
        model_name=model_name,
        exhaustive=exhaustive,
        resume_from=resume_from,
    )
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
    overwrite = not bool(vars(args).get("no_overwrite", False))
    audit_manifest = vars(args).get("audit_manifest")
    audit_log = vars(args).get("audit_log")
    audit_db = vars(args).get("audit_db")
    verify_audit_manifest = bool(vars(args).get("verify_audit_manifest", False))
    if verify_audit_manifest and not audit_manifest:
        print("--verify-audit-manifest requires --audit-manifest", file=sys.stderr)
        return 1
    if audit_log and not audit_manifest:
        print("--audit-log requires --audit-manifest", file=sys.stderr)
        return 1
    if audit_db and not audit_log:
        print("--audit-db requires --audit-log", file=sys.stderr)
        return 1

    try:
        exporter = ProjectExporter()
        artifact_paths: list[str] = []

        if fmt == "json":
            path = exporter.export_json(state, output_file, overwrite=overwrite)
            artifact_paths = [path]
            print(f"Exported JSON to: {path}")
        elif fmt == "csv":
            paths = exporter.export_csv(state, output_dir, overwrite=overwrite)
            artifact_paths = paths
            print("Exported CSV files:")
            for p in paths:
                print(f"  {p}")
        elif fmt == "markdown":
            path = exporter.export_markdown(state, output_file, overwrite=overwrite)
            artifact_paths = [path]
            print(f"Exported Markdown to: {path}")
        elif fmt == "qdpx":
            path = exporter.export_qdpx(state, output_file, overwrite=overwrite)
            artifact_paths = [path]
            print(f"Exported QDPX to: {path}")
            print("  Compatible with ATLAS.ti, NVivo, MAXQDA")
        else:
            print(f"Unsupported format: {fmt}", file=sys.stderr)
            return 1

        if audit_manifest:
            _write_and_optionally_verify_export_manifest(
                state,
                fmt,
                artifact_paths,
                audit_manifest,
                verify_audit_manifest,
                audit_log,
                audit_db,
            )
    except Exception as e:
        print(f"Export failed: {e}", file=sys.stderr)
        return 1

    return 0


def _write_and_optionally_verify_export_manifest(
    state: ProjectState,
    export_format: str,
    artifact_paths: list[str],
    manifest_output: str,
    verify: bool,
    audit_log: str | None = None,
    audit_db: str | None = None,
) -> None:
    """Write an export audit manifest and optionally verify it immediately."""
    from qc_clean.core.export.audit_event_log import (
        append_export_audit_event,
        mirror_export_audit_event_log_to_sqlite,
    )
    from qc_clean.core.export.audit_manifest import (
        build_export_audit_manifest,
        verify_export_audit_manifest_payload,
        write_export_audit_manifest,
    )

    manifest_path = Path(manifest_output)
    base_dir = manifest_path.parent if str(manifest_path.parent) else Path(".")
    manifest = build_export_audit_manifest(
        state,
        export_format=export_format,  # type: ignore[arg-type]
        artifact_paths=artifact_paths,
        base_dir=base_dir,
    )
    written = write_export_audit_manifest(manifest, manifest_path)
    print(f"Export audit manifest: {written}")
    if audit_log:
        append_export_audit_event(
            audit_log,
            event_type="manifest_written",
            event_status="success",
            manifest_path=manifest_path,
            payload=manifest.model_dump(mode="json"),
        )

    if verify:
        report = verify_export_audit_manifest_payload(
            manifest,
            base_dir=base_dir,
            state=state,
        )
        if audit_log:
            append_export_audit_event(
                audit_log,
                event_type="manifest_verified",
                event_status=report.status,
                manifest_path=manifest_path,
                payload=report.model_dump(mode="json"),
            )
        verification_error = None
        if report.status != "verified":
            messages = "; ".join(failure.message for failure in report.failures)
            verification_error = RuntimeError(
                f"Export audit manifest verification failed: {messages}"
            )
        else:
            print("Verified export audit manifest")
        if audit_log and audit_db:
            mirror_export_audit_event_log_to_sqlite(audit_log, audit_db)
            print(f"Export audit event DB: {audit_db}")
        if verification_error is not None:
            raise verification_error
    elif audit_log and audit_db:
        mirror_export_audit_event_log_to_sqlite(audit_log, audit_db)
        print(f"Export audit event DB: {audit_db}")
    if audit_log:
        print(f"Export audit event log: {audit_log}")


def _export_adjudication_sample(store: ProjectStore, args) -> int:
    """Export an unlabeled adjudication sample package for a project."""
    project_id = args.project_id
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        print(f"Project not found: {project_id}", file=sys.stderr)
        return 1

    from qc_clean.core.adjudication_sample import (
        build_adjudication_sample_package,
        write_adjudication_sample_package,
    )

    package = build_adjudication_sample_package(
        state,
        limit_per_type=getattr(args, "limit_per_type", 20),
        context_chars=getattr(args, "context_chars", 120),
    )
    output_file = getattr(args, "output_file", None)
    if not output_file:
        print("--output-file is required", file=sys.stderr)
        return 1

    path = write_adjudication_sample_package(package, output_file)
    print(f"Exported adjudication sample to: {path}")
    print(f"  Items: {package.item_counts['returned']['total']}")
    print("  Note: package is unlabeled input, not validity evidence.")
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
    application_level = bool(getattr(args, "application_level", False))

    print(f"Running IRR analysis on project: {state.name}")
    print(f"  Methodology: {state.config.methodology.value}")
    print(f"  Passes: {num_passes}")
    print(f"  Model: {model_name}")
    if models:
        print(f"  Model rotation: {', '.join(models)}")
    if application_level:
        print("  Application-level: exhaustive per-segment coding")
    print()

    try:
        result = asyncio.run(run_irr_analysis(
            state,
            num_passes=num_passes,
            model_name=model_name,
            models=models,
            application_level=application_level,
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
    if result.gwet_ac1 is not None:
        print(f"  Gwet's AC1: {result.gwet_ac1:.3f}")
    print(f"  Interpretation: {result.interpretation} (codebook-discovery agreement)")
    if result.application_level:
        print("\n  Application-level agreement:")
        print("    Positive code-application cells (segment x code):")
        print(f"      Units compared: {result.application_units} positive (segment, code) cells")
        if result.application_percent_agreement is not None:
            print(f"      Percent agreement: {result.application_percent_agreement:.1%}")
        if result.application_cohens_kappa is not None:
            print(f"      Cohen's kappa: {result.application_cohens_kappa:.3f}")
        if result.application_fleiss_kappa is not None:
            print(f"      Fleiss' kappa: {result.application_fleiss_kappa:.3f}")
        if result.application_gwet_ac1 is not None:
            print(f"      Gwet's AC1: {result.application_gwet_ac1:.3f}")
        print(f"      Interpretation: {result.application_interpretation}")

        print("    Segment decisions (coded / no_code / not_examined):")
        print(f"      Units compared: {result.segment_decision_units} segments")
        if result.segment_decision_percent_agreement is not None:
            print(f"      Percent agreement: {result.segment_decision_percent_agreement:.1%}")
        if result.segment_decision_cohens_kappa is not None:
            print(f"      Cohen's kappa: {result.segment_decision_cohens_kappa:.3f}")
        if result.segment_decision_fleiss_kappa is not None:
            print(f"      Fleiss' kappa: {result.segment_decision_fleiss_kappa:.3f}")
        if result.segment_decision_gwet_ac1 is not None:
            print(f"      Gwet's AC1: {result.segment_decision_gwet_ac1:.3f}")
        print(f"      Interpretation: {result.segment_decision_interpretation}")

    return 0


def _record_project_run_timing(
    state: ProjectState,
    *,
    started_at: str,
    duration_s: float,
    status: str,
    trace_id: str,
    model_name: str,
    exhaustive: bool,
    resume_from: str | None,
) -> None:
    """Record last-run wall-clock metadata for D10 reporting."""
    state.config.extra = dict(state.config.extra)
    state.config.extra["run_timing"] = {
        "schema_version": 1,
        "started_at": started_at,
        "completed_at": datetime.now().isoformat(),
        "duration_s": max(0.0, duration_s),
        "status": status,
        "trace_id": trace_id,
        "model": model_name,
        "exhaustive_coding": exhaustive,
        "resume_from": resume_from,
        "document_count": state.corpus.num_documents,
        "phase_result_count": len(state.phase_results),
    }


def _show_claims(store: ProjectStore, args) -> int:
    """Show a compact claim-ledger summary for a project."""
    project_id = args.project_id
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        print(f"Project not found: {project_id}", file=sys.stderr)
        return 1

    limit = max(0, int(getattr(args, "limit", 20)))
    summary = summarize_claim_ledger(state)
    disconfirmation = summarize_disconfirmation_coverage(state)
    print(f"Claim Ledger: {state.name}")
    print(f"  Total claims: {summary['total_claims']}")
    print(f"  Unsupported or needing anchors: {summary['unsupported_or_needing_anchor']}")
    print(
        "  Disconfirmation targets: "
        f"{disconfirmation['total_targets']} "
        f"({disconfirmation['challenged_targets']} challenged, "
        f"{disconfirmation['unchallenged_targets']} unchallenged, "
        f"{disconfirmation['challenged_rate']:.0%} challenged)"
    )
    print(f"  By kind: {summary['by_kind']}")
    print(f"  By stage: {summary['by_stage']}")
    print(f"  By adjudication: {summary['by_adjudication_status']}")
    print(f"  By support: {summary['by_support_status']}")

    if state.claims and limit:
        print("\n  Claims:")
        for claim in state.claims[:limit]:
            print(
                f"    - [{claim.claim_kind.value}/{claim.source_stage}/"
                f"{claim.support_status.value}] {claim.claim_text}"
            )
        if len(state.claims) > limit:
            print(f"    ... and {len(state.claims) - limit} more")

    return 0


def _show_or_update_scope(store: ProjectStore, args) -> int:
    """Show or update a project's corpus scope contract."""
    project_id = args.project_id
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        print(f"Project not found: {project_id}", file=sys.stderr)
        return 1

    if _scope_update_requested(args):
        current = state.corpus_scope or CorpusScope()
        state.corpus_scope = CorpusScope(
            phenomenon=(
                args.phenomenon
                if getattr(args, "phenomenon", None) is not None
                else current.phenomenon
            ),
            population=(
                args.population
                if getattr(args, "population", None) is not None
                else current.population
            ),
            sampling_frame=(
                args.sampling_frame
                if getattr(args, "sampling_frame", None) is not None
                else current.sampling_frame
            ),
            inclusion_criteria=(
                list(args.inclusion_criteria)
                if getattr(args, "inclusion_criteria", None) is not None
                else list(current.inclusion_criteria)
            ),
            exclusion_criteria=(
                list(args.exclusion_criteria)
                if getattr(args, "exclusion_criteria", None) is not None
                else list(current.exclusion_criteria)
            ),
            notes=(
                args.notes
                if getattr(args, "notes", None) is not None
                else current.notes
            ),
        )
        state.touch()
        store.save(state)

    _print_scope(state)
    return 0


def _scope_update_requested(args) -> bool:
    """Return True when any scope update flag was supplied."""
    return any(
        getattr(args, field, None) is not None
        for field in (
            "phenomenon",
            "population",
            "sampling_frame",
            "inclusion_criteria",
            "exclusion_criteria",
            "notes",
        )
    )


def _scope_from_create_args(args) -> CorpusScope | None:
    """Build a corpus scope for project creation when scope fields are supplied."""
    if not _scope_update_requested(args):
        return None

    return CorpusScope(
        phenomenon=getattr(args, "phenomenon", None) or "",
        population=getattr(args, "population", None) or "",
        sampling_frame=getattr(args, "sampling_frame", None) or "",
        inclusion_criteria=list(getattr(args, "inclusion_criteria", None) or []),
        exclusion_criteria=list(getattr(args, "exclusion_criteria", None) or []),
        notes=getattr(args, "notes", None) or "",
    )


def _print_scope(state: ProjectState) -> None:
    """Print a human-readable corpus scope summary."""
    print(f"Corpus Scope: {state.name}")
    scope = state.corpus_scope
    if scope is None:
        print("  Not set.")
        return

    print(f"  Phenomenon: {scope.phenomenon or '(not specified)'}")
    print(f"  Population: {scope.population or '(not specified)'}")
    print(f"  Sampling frame: {scope.sampling_frame or '(not specified)'}")
    if scope.inclusion_criteria:
        print("  Inclusion criteria:")
        for criterion in scope.inclusion_criteria:
            print(f"    - {criterion}")
    else:
        print("  Inclusion criteria: (not specified)")
    if scope.exclusion_criteria:
        print("  Exclusion criteria:")
        for criterion in scope.exclusion_criteria:
            print(f"    - {criterion}")
    else:
        print("  Exclusion criteria: (not specified)")
    print(f"  Notes: {scope.notes or '(not specified)'}")


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


def _recode_project(store: ProjectStore, args) -> int:
    """Incrementally code new documents added to a completed project."""
    project_id = args.project_id
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        print(f"Project not found: {project_id}", file=sys.stderr)
        return 1

    if len(state.codebook.codes) == 0:
        print("No existing codebook. Run the pipeline first with 'project run'.", file=sys.stderr)
        return 1

    uncoded = state.get_uncoded_doc_ids()
    if not uncoded:
        print("All documents are already coded. Add new documents first with 'project add-docs'.", file=sys.stderr)
        return 1

    refresh_higher_order = bool(getattr(args, "refresh_higher_order", False))
    if refresh_higher_order and state.config.methodology == Methodology.GROUNDED_THEORY:
        print(
            "--refresh-higher-order is only supported for default/thematic "
            "projects in this INV-11 slice; grounded-theory refresh requires a "
            "separate GT context reconstruction pipeline.",
            file=sys.stderr,
        )
        return 1

    from qc_clean.core.pipeline.pipeline_factory import create_incremental_pipeline

    async def save_callback(s):
        store.save(s)

    pipeline = create_incremental_pipeline(
        methodology=state.config.methodology.value,
        on_stage_complete=save_callback,
        refresh_higher_order=refresh_higher_order,
    )

    from qc_clean.core.pipeline.pipeline_engine import PipelineContext
    model_name = getattr(args, "model", None) or state.config.model_name
    ctx = PipelineContext(
        model_name=model_name,
        trace_id=f"qualitative_coding/project/{state.id}/recode/{state.iteration + 1}",
    )

    print(f"Incremental re-coding on project: {state.name}")
    print(f"  Methodology: {state.config.methodology.value}")
    print(f"  Existing codes: {len(state.codebook.codes)}")
    print(f"  Total documents: {state.corpus.num_documents}")
    print(f"  Uncoded documents: {len(uncoded)}")
    print(f"  Model: {model_name}")
    if refresh_higher_order:
        print("  Refresh higher-order: enabled (thematic perspective/relationship/synthesis)")
    print()

    # Reset pipeline status for the incremental run
    state.pipeline_status = PipelineStatus.PENDING

    try:
        state = asyncio.run(pipeline.run(state, ctx))
    except Exception as e:
        store.save(state)
        print(f"\nIncremental coding failed: {e}", file=sys.stderr)
        return 1

    store.save(state)

    print("\nIncremental coding complete.")
    print(f"  Codes: {len(state.codebook.codes)}")
    print(f"  Applications: {len(state.code_applications)}")
    print(f"  Iteration: {state.iteration}")

    return 0

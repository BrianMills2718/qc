"""
Review CLI command handlers.
"""

import json
import logging
import sys

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.pipeline.review import ReviewManager
from qc_clean.schemas.domain import HumanReviewDecision, ReviewAction

logger = logging.getLogger(__name__)


def handle_review_command(args) -> int:
    """Handle the review subcommand."""
    store = ProjectStore()
    project_id = args.project_id

    try:
        state = store.load(project_id)
    except FileNotFoundError:
        print(f"Project not found: {project_id}", file=sys.stderr)
        return 1

    rm = ReviewManager(state)

    if getattr(args, "approve_all", False):
        result = rm.approve_all_codes()
        store.save(state)
        print(f"Approved {result['applied']} codes.")
        return 0

    if getattr(args, "file", None):
        return _apply_decisions_from_file(rm, store, state, args.file)

    # Default: show review summary
    return _show_review_summary(rm, state)


def _show_review_summary(rm: ReviewManager, state) -> int:
    summary = rm.get_review_summary()

    print(f"Review Summary for project: {state.name}")
    print(f"  Pipeline status: {summary.pipeline_status}")
    print(f"  Current phase: {summary.current_phase or 'N/A'}")
    print(f"  Codes to review: {summary.codes_count}")
    print(f"  Applications to review: {summary.applications_count}")
    print(f"  Decisions already made: {summary.existing_decisions}")

    if summary.codes_count > 0:
        print("\nCodes:")
        for code in rm.get_pending_codes():
            print(f"  [{code.id}] {code.name} (mentions={code.mention_count}, conf={code.confidence:.2f})")
            print(f"    {code.description[:100]}")

    return 0


def _apply_decisions_from_file(rm, store, state, filepath: str) -> int:
    try:
        with open(filepath, "r") as f:
            raw = json.load(f)
    except Exception as e:
        print(f"Failed to read decisions file: {e}", file=sys.stderr)
        return 1

    decisions_data = raw if isinstance(raw, list) else raw.get("decisions", [])

    decisions = []
    for d in decisions_data:
        try:
            decision = HumanReviewDecision(
                target_type=d["target_type"],
                target_id=d["target_id"],
                action=ReviewAction(d["action"]),
                rationale=d.get("rationale", ""),
                new_value=d.get("new_value"),
            )
            decisions.append(decision)
        except Exception as e:
            print(f"Invalid decision entry: {e}", file=sys.stderr)

    result = rm.apply_decisions(decisions)
    store.save(state)
    print(f"Applied {result['applied']} decisions.")

    if rm.can_resume():
        print("Pipeline is paused for review. Run 'qc_cli review --project <id> --resume' to continue.")

    return 0

"""
Project management CLI command handlers.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import Methodology, ProjectConfig, ProjectState

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

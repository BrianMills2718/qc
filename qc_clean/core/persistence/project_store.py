"""
JSON file-based persistence for ProjectState.

Each project is stored as a single JSON file under a configurable directory.
File name: ``{project_id}.json``
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from qc_clean.schemas.domain import ProjectState

logger = logging.getLogger(__name__)

DEFAULT_PROJECTS_DIR = Path.home() / ".qc_projects"


class ProjectStore:
    """Save / load / list ProjectState objects as JSON files."""

    def __init__(self, projects_dir: Optional[Path] = None):
        self.projects_dir = projects_dir or DEFAULT_PROJECTS_DIR
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, state: ProjectState) -> Path:
        """Persist a ProjectState to disk. Returns the file path."""
        state.touch()
        path = self._path_for(state.id)
        path.write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info("Saved project %s to %s", state.id, path)
        return path

    def load(self, project_id: str) -> ProjectState:
        """Load a ProjectState by its id. Raises FileNotFoundError if missing."""
        path = self._path_for(project_id)
        if not path.exists():
            raise FileNotFoundError(f"No project file found: {path}")
        raw = path.read_text(encoding="utf-8")
        state = ProjectState.model_validate_json(raw)
        logger.info("Loaded project %s from %s", project_id, path)
        return state

    def list_projects(self) -> List[Dict[str, str]]:
        """Return summary dicts (id, name, updated_at) for every saved project."""
        summaries: List[Dict[str, str]] = []
        for path in sorted(self.projects_dir.glob("*.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                summaries.append({
                    "id": raw.get("id", path.stem),
                    "name": raw.get("name", "Untitled"),
                    "updated_at": raw.get("updated_at", ""),
                    "pipeline_status": raw.get("pipeline_status", "unknown"),
                })
            except Exception as exc:
                logger.warning("Skipping corrupt project file %s: %s", path, exc)
        return summaries

    def delete(self, project_id: str) -> bool:
        """Delete a project file. Returns True if deleted, False if not found."""
        path = self._path_for(project_id)
        if path.exists():
            path.unlink()
            logger.info("Deleted project %s", project_id)
            return True
        return False

    def exists(self, project_id: str) -> bool:
        """Check whether a project file exists."""
        return self._path_for(project_id).exists()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _path_for(self, project_id: str) -> Path:
        # Sanitise: only allow alphanumeric, dash, underscore
        safe_id = "".join(
            c for c in project_id if c.isalnum() or c in "-_"
        )
        if not safe_id:
            raise ValueError(f"Invalid project id: {project_id!r}")
        return self.projects_dir / f"{safe_id}.json"

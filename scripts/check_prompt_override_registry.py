#!/usr/bin/env python3
"""Check prompt override source uses against the central registry."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.prompt_override_registry import (  # noqa: E402
    PROMPT_OVERRIDE_SURFACES,
    validate_prompt_override_registry,
)


class PromptOverrideRegistryReport(BaseModel):
    """Machine-readable result for prompt override registry checks."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = Field(
        1,
        description="Report schema version",
    )
    package_type: Literal["prompt_override_registry_check"] = Field(
        "prompt_override_registry_check",
        description="Report type discriminator",
    )
    ok: bool = Field(
        description="True when source uses and registry declarations match",
    )
    source_root: str = Field(
        description="Source root scanned for prompt override uses",
    )
    registered_surfaces: list[str] = Field(
        description="Prompt override surfaces declared in the registry",
    )
    used_surfaces: list[str] = Field(
        description="Prompt override surfaces found in source code",
    )
    unregistered_surfaces: list[str] = Field(
        description="Source-used surfaces missing from the registry",
    )
    unused_registered_surfaces: list[str] = Field(
        description="Registry surfaces not found in source code",
    )
    use_locations: dict[str, list[str]] = Field(
        description="Source file and line locations for each discovered use",
    )
    errors: list[str] = Field(
        description="Human-readable registry/source mismatch errors",
    )
    caveat: str = Field(
        "This check governs custom-prompt surface declarations only; it is not "
        "prompt-injection robustness evidence or model-obedience evidence.",
        description="Claim-discipline caveat for this governance check",
    )


def check_prompt_override_registry(source_root: Path) -> PromptOverrideRegistryReport:
    """Return a registry/source consistency report for prompt override surfaces."""
    validate_prompt_override_registry()
    root = source_root.resolve()
    use_locations = _discover_prompt_override_uses(root)
    registered = sorted(PROMPT_OVERRIDE_SURFACES)
    used = sorted(use_locations)
    unregistered = sorted(set(used) - set(registered))
    unused = sorted(set(registered) - set(used))
    errors = [
        f"Prompt override surface used in source but not registered: {surface}"
        for surface in unregistered
    ]
    errors.extend(
        f"Prompt override surface registered but not used in source: {surface}"
        for surface in unused
    )
    return PromptOverrideRegistryReport(
        ok=not errors,
        source_root=str(root),
        registered_surfaces=registered,
        used_surfaces=used,
        unregistered_surfaces=unregistered,
        unused_registered_surfaces=unused,
        use_locations={key: sorted(value) for key, value in sorted(use_locations.items())},
        errors=errors,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the prompt override registry checker CLI."""
    parser = argparse.ArgumentParser(
        description="Check prompt override source uses against the central registry"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT / "qc_clean",
        help="Python source root to scan (default: qc_clean)",
    )
    args = parser.parse_args(argv)

    try:
        report = check_prompt_override_registry(args.root)
    except (OSError, SyntaxError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.ok else 1


def _discover_prompt_override_uses(source_root: Path) -> dict[str, list[str]]:
    """Find literal `prompt_overrides` key uses in Python source files."""
    if not source_root.exists():
        raise ValueError(f"Source root does not exist: {source_root}")
    if source_root.is_file():
        paths = [source_root]
        base = source_root.parent
    else:
        paths = sorted(source_root.rglob("*.py"))
        base = source_root

    uses: dict[str, list[str]] = {}
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            surface = _surface_from_prompt_override_node(node)
            if surface is None:
                continue
            relative = path.relative_to(base)
            uses.setdefault(surface, []).append(f"{relative}:{node.lineno}")
    return uses


def _surface_from_prompt_override_node(node: ast.AST) -> str | None:
    """Return a literal prompt override surface name from an AST node."""
    if isinstance(node, ast.Subscript) and _is_prompt_overrides_expr(node.value):
        return _literal_string_slice(node.slice)

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and _is_prompt_overrides_expr(node.func.value)
        and node.args
    ):
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            return first_arg.value
    return None


def _is_prompt_overrides_expr(node: ast.AST) -> bool:
    """Return true for direct attribute access to `*.prompt_overrides`."""
    return isinstance(node, ast.Attribute) and node.attr == "prompt_overrides"


def _literal_string_slice(node: ast.AST) -> str | None:
    """Return a subscript string literal or None for dynamic keys."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


if __name__ == "__main__":
    raise SystemExit(main())

"""Registry of supported custom prompt override surfaces.

Prompt overrides can expose protected data blocks and scalar metadata to
operator-authored templates. This registry keeps those exposure policies in one
place so new surfaces must declare what they expose before source code uses
them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptOverrideSurface:
    """Declared placeholder policy for one prompt override surface."""

    stage_name: str
    required_data_placeholders: frozenset[str]
    optional_data_placeholders: frozenset[str] = frozenset()
    metadata_placeholders: frozenset[str] = frozenset()

    @property
    def declared_placeholders(self) -> frozenset[str]:
        """Return every placeholder the surface is allowed to expose."""
        return (
            self.required_data_placeholders
            | self.optional_data_placeholders
            | self.metadata_placeholders
        )


PROMPT_OVERRIDE_SURFACES: Mapping[str, PromptOverrideSurface] = {
    "thematic_coding": PromptOverrideSurface(
        stage_name="thematic_coding",
        required_data_placeholders=frozenset({"combined_text"}),
        metadata_placeholders=frozenset({"num_interviews"}),
    ),
    "gt_constant_comparison": PromptOverrideSurface(
        stage_name="gt_constant_comparison",
        required_data_placeholders=frozenset({"segment_text"}),
        optional_data_placeholders=frozenset({"codebook_context"}),
        metadata_placeholders=frozenset({"doc_name", "seg_idx", "total_segments"}),
    ),
}


def get_prompt_override_surface(stage_name: str) -> PromptOverrideSurface:
    """Return the registered prompt override surface for a stage."""
    try:
        return PROMPT_OVERRIDE_SURFACES[stage_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported prompt override surface: {stage_name}") from exc


def validate_prompt_override_registry(
    registry: Mapping[str, PromptOverrideSurface] = PROMPT_OVERRIDE_SURFACES,
) -> None:
    """Fail loudly if prompt override surface declarations are inconsistent."""
    errors: list[str] = []
    for registry_key, surface in sorted(registry.items()):
        if registry_key != surface.stage_name:
            errors.append(
                f"{registry_key}: stage_name must match registry key "
                f"({surface.stage_name!r})"
            )
        overlap = sorted(
            (surface.required_data_placeholders | surface.optional_data_placeholders)
            & surface.metadata_placeholders
        )
        if overlap:
            errors.append(
                f"{registry_key}: placeholder(s) declared as both data and metadata: "
                f"{', '.join(overlap)}"
            )
        duplicate_data = sorted(
            surface.required_data_placeholders & surface.optional_data_placeholders
        )
        if duplicate_data:
            errors.append(
                f"{registry_key}: placeholder(s) declared as both required and "
                f"optional data: {', '.join(duplicate_data)}"
            )
        if not surface.declared_placeholders:
            errors.append(f"{registry_key}: at least one placeholder must be declared")

    if errors:
        raise ValueError("Invalid prompt override registry: " + "; ".join(errors))


validate_prompt_override_registry()

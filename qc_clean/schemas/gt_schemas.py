"""
Grounded Theory LLM output schemas.

These Pydantic models define the expected JSON shapes for LLM-extracted
grounded theory analysis results. Used by the GT pipeline stages and
converted to domain objects via adapters.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OpenCode(BaseModel):
    """A concept identified during open coding with hierarchical structure support."""
    code_name: str = Field(description="Name of the open code")
    description: str = Field(description="Description of what this code represents")
    properties: List[str] = Field(default_factory=list, description="Properties of this concept")
    dimensions: List[str] = Field(default_factory=list, description="Dimensional variations")
    supporting_quotes: List[str] = Field(default_factory=list, description="Quotes that support this code")
    frequency: int = Field(description="Number of occurrences")
    confidence: float = Field(description="Confidence in this code 0-1")
    reasoning: str = Field(
        default="",
        description="Brief explanation of why this code was created and what analytical decision led to it",
    )

    # Hierarchical structure fields
    parent_id: Optional[str] = Field(default=None, description="ID of parent code if this is a sub-code")
    level: int = Field(default=0, description="Hierarchy level (0 for top-level codes)")
    child_codes: List[str] = Field(default_factory=list, description="IDs of child codes")

    def to_hierarchical_dict(self) -> Dict[str, Any]:
        """Convert to dictionary preserving hierarchy information."""
        return {
            "code_name": self.code_name,
            "description": self.description,
            "properties": self.properties,
            "dimensions": self.dimensions,
            "supporting_quotes": self.supporting_quotes,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "parent_id": self.parent_id,
            "level": self.level,
            "child_codes": self.child_codes,
        }


class AxialRelationship(BaseModel):
    """A relationship identified during axial coding."""
    central_category: str = Field(description="The central category")
    related_category: str = Field(description="Related category")
    relationship_type: str = Field(description="Type of relationship (causal, contextual, intervening, etc.)")
    conditions: List[str] = Field(default_factory=list, description="Conditions that influence this relationship")
    consequences: List[str] = Field(default_factory=list, description="Consequences of this relationship")
    supporting_evidence: List[str] = Field(default_factory=list, description="Evidence supporting this relationship")
    strength: float = Field(description="Strength of relationship 0-1")


class CoreCategory(BaseModel):
    """The core category identified during selective coding."""
    category_name: str = Field(description="Name of the core category")
    definition: str = Field(description="Clear definition of the core category")
    central_phenomenon: str = Field(description="The central phenomenon this category explains")
    related_categories: List[str] = Field(default_factory=list, description="Categories that relate to this core category")
    theoretical_properties: List[str] = Field(default_factory=list, description="Theoretical properties")
    explanatory_power: str = Field(description="How this category explains the phenomenon")
    integration_rationale: str = Field(description="Why this is the core category")


class TheoreticalModel(BaseModel):
    """The final theoretical model from grounded theory analysis."""
    model_name: str = Field(description="Name of the theoretical model")
    core_categories: List[str] = Field(default_factory=list, description="The core categories that explain the phenomenon")
    theoretical_framework: str = Field(description="The theoretical framework developed")
    propositions: List[str] = Field(default_factory=list, description="Theoretical propositions")
    conceptual_relationships: List[str] = Field(default_factory=list, description="Key conceptual relationships")
    scope_conditions: List[str] = Field(default_factory=list, description="Conditions under which theory applies")
    implications: List[str] = Field(default_factory=list, description="Implications of the theory")
    future_research: List[str] = Field(default_factory=list, description="Suggested future research directions")
    analytical_memo: str = Field(
        default="",
        description="Analytical memo: record your reasoning, uncertainties, and emerging patterns",
    )

    @property
    def core_category(self) -> str:
        """Backward compatibility: return first core category as string."""
        return self.core_categories[0] if self.core_categories else ""

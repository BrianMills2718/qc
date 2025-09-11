"""
QCA (Qualitative Comparative Analysis) Schemas and Configuration
Post-processing pipeline for converting qualitative coding results to QCA analysis
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Literal
from enum import Enum

class CalibrationMethod(str, Enum):
    """Methods for calibrating codes to set memberships"""
    BINARY = "binary"  # 0/1 based on presence/absence
    FREQUENCY = "frequency"  # Based on frequency thresholds
    FUZZY = "fuzzy"  # Continuous 0-1 based on custom rules
    PERCENTILE = "percentile"  # Based on percentile distribution
    DIRECT = "direct"  # Direct assignment with explicit theoretical justification
    ANCHOR_POINTS = "anchor_points"  # Three-value calibration (non-member, crossover, full-member)
    INTERACTIVE = "interactive"  # Requires researcher validation of thresholds

class CalibrationRule(BaseModel):
    """Rule for calibrating a specific code to set membership"""
    method: CalibrationMethod = Field(description="Calibration method to use")
    
    # CRITICAL FIX: Theoretical justification required for all calibration decisions
    theoretical_justification: str = Field(
        description="Required theoretical or literature-based rationale for calibration choices"
    )
    
    # Binary calibration (presence/absence)
    binary_threshold: Optional[int] = Field(default=1, description="Minimum occurrences for membership=1")
    
    # Frequency-based calibration  
    frequency_thresholds: Optional[Dict[str, float]] = Field(
        default=None,
        description="Frequency ranges to membership scores, e.g., {'rare': 0.2, 'moderate': 0.5, 'frequent': 0.8}"
    )
    frequency_breakpoints: Optional[List[int]] = Field(
        default=None,
        description="Occurrence breakpoints for frequency ranges, e.g., [2, 5, 10]"
    )
    
    # Fuzzy calibration
    fuzzy_function: Optional[str] = Field(
        default=None,
        description="Python expression for fuzzy membership, use 'count' variable"
    )
    
    # Percentile calibration
    percentile_thresholds: Optional[List[float]] = Field(
        default=[0.33, 0.67],
        description="Percentile breakpoints for membership levels"
    )
    
    # CRITICAL FIX: New theoretically grounded calibration methods
    # Direct calibration with explicit thresholds
    direct_thresholds: Optional[Dict[str, float]] = Field(
        default=None,
        description="Direct threshold assignments: {'non_membership': 0.0, 'crossover': 0.5, 'full_membership': 1.0}"
    )
    
    # Anchor points calibration (recommended QCA practice)
    anchor_points: Optional[Dict[str, Union[int, float]]] = Field(
        default=None,
        description="Three-value calibration anchors: {'non_member': 0, 'crossover': 3, 'full_member': 6}"
    )
    
    # Interactive calibration settings
    require_validation: Optional[bool] = Field(
        default=False,
        description="Requires researcher review and approval of generated thresholds"
    )
    
    # Normalization settings (CRITICAL FIX: Address comparability issues)
    normalization_method: Optional[Literal["per_thousand_words", "per_speaker", "per_quote", "none"]] = Field(
        default="none",
        description="Method to normalize raw counts for meaningful comparison"
    )

class ConditionDefinition(BaseModel):
    """Definition of a condition for QCA analysis"""
    condition_id: str = Field(description="Unique condition identifier")
    name: str = Field(description="Human-readable condition name")
    description: str = Field(description="Description of what this condition represents")
    
    # Source of condition data
    source_type: Literal["code", "speaker_property", "entity", "relationship"] = Field(
        description="Type of extraction data this condition is based on"
    )
    source_id: str = Field(description="ID of the source (code_id, property_id, etc.)")
    
    # Calibration settings
    calibration: CalibrationRule = Field(description="How to calibrate this condition")

class OutcomeDefinition(BaseModel):
    """Definition of an outcome variable for QCA analysis"""
    outcome_id: str = Field(description="Unique outcome identifier")
    name: str = Field(description="Human-readable outcome name")
    description: str = Field(description="Description of what this outcome represents")
    
    # Outcome can be based on multiple conditions combined
    source_conditions: List[str] = Field(description="List of condition_ids that contribute to this outcome")
    combination_rule: str = Field(
        default="any",
        description="How to combine conditions: 'any', 'all', or Python expression using condition IDs"
    )
    
    # Calibration for the outcome itself
    calibration: CalibrationRule = Field(description="How to calibrate this outcome")

class QCAConfiguration(BaseModel):
    """Configuration for QCA post-processing pipeline"""
    
    # Input/Output settings
    input_dir: str = Field(description="Directory containing coded interview JSON files")
    output_dir: str = Field(default="qca_output", description="Directory for QCA analysis outputs")
    
    # QCA Analysis settings
    conditions: List[ConditionDefinition] = Field(description="Conditions to include in QCA")
    outcomes: List[OutcomeDefinition] = Field(description="Outcomes to analyze")
    
    # Phase control
    enable_calibration: bool = Field(default=True, description="Run Phase QCA-1: Code to Set Membership")
    enable_truth_table: bool = Field(default=True, description="Run Phase QCA-2: Truth Table Construction")
    enable_minimization: bool = Field(default=False, description="Run Phase QCA-3: Boolean Minimization")
    
    # Truth table mode (CRITICAL FIX: Preserve fuzzy information)
    truth_table_mode: Literal["crisp", "fuzzy", "dual"] = Field(
        default="dual", 
        description="Truth table construction mode: crisp (binary), fuzzy (preserve scores), dual (generate both)"
    )
    
    # Advanced settings
    case_id_field: str = Field(default="interview_id", description="Field to use as case identifier")
    minimum_membership_threshold: float = Field(default=0.5, description="Minimum membership for inclusion in analysis")
    
    # External tool integration
    r_qca_package: bool = Field(default=False, description="Export data for R QCA package")
    python_qca: bool = Field(default=False, description="Use pyQCA for analysis")
    neo4j_export: bool = Field(default=False, description="Export to Neo4j for graph analysis")

class CalibratedCondition(BaseModel):
    """A condition with calibrated membership score"""
    condition_id: str
    membership_score: float = Field(ge=0.0, le=1.0, description="Membership score 0-1")
    raw_value: Union[int, float, str] = Field(description="Original raw value before calibration")
    calibration_method: str = Field(description="Method used for calibration")

class CalibratedCase(BaseModel):
    """A case (interview) with all calibrated conditions and outcomes"""
    case_id: str = Field(description="Case identifier (usually interview_id)")
    conditions: List[CalibratedCondition] = Field(description="All calibrated conditions for this case")
    outcomes: List[CalibratedCondition] = Field(description="All calibrated outcomes for this case")
    
    # Metadata
    source_file: str = Field(description="Path to source coded interview file")
    total_quotes: int = Field(description="Total quotes in this case")
    total_codes: int = Field(description="Total code applications in this case")

class TruthTableRow(BaseModel):
    """A row in the QCA truth table"""
    configuration: Dict[str, float] = Field(description="Condition membership scores")
    outcome: float = Field(description="Outcome membership score")
    cases: List[str] = Field(description="Case IDs with this configuration")
    consistency: Optional[float] = Field(default=None, description="Consistency score for this configuration")
    coverage: Optional[float] = Field(default=None, description="Coverage score for this configuration")

class TruthTable(BaseModel):
    """Complete QCA truth table"""
    conditions: List[str] = Field(description="Condition IDs included in table")
    outcome: str = Field(description="Outcome ID analyzed")
    rows: List[TruthTableRow] = Field(description="All configurations in the truth table")
    
    # Truth table mode (CRITICAL FIX: Track whether this preserves fuzzy information)
    table_mode: Literal["crisp", "fuzzy"] = Field(
        description="Mode of this truth table: crisp (binary 0/1) or fuzzy (preserves membership scores)"
    )
    
    # Analysis metadata
    total_cases: int = Field(description="Total number of cases")
    configurations_found: int = Field(description="Number of unique configurations")
    logical_remainders: int = Field(description="Number of logically possible but unobserved configurations")

class QCAResults(BaseModel):
    """Complete QCA analysis results"""
    configuration: QCAConfiguration = Field(description="Configuration used for analysis")
    calibrated_cases: List[CalibratedCase] = Field(description="All cases with calibrated conditions")
    truth_tables: List[TruthTable] = Field(description="Truth tables for each outcome")
    
    # Analysis summary
    total_cases_analyzed: int = Field(description="Total cases included in analysis")
    conditions_analyzed: int = Field(description="Total conditions analyzed")
    outcomes_analyzed: int = Field(description="Total outcomes analyzed")
    
    # File outputs generated
    csv_files: List[str] = Field(default=[], description="CSV files generated")
    json_files: List[str] = Field(default=[], description="JSON files generated")
    r_scripts: List[str] = Field(default=[], description="R scripts generated for QCA package")
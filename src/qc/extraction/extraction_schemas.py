"""
Pydantic schemas for structured LLM extraction
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any

class ExtractedEntity(BaseModel):
    """Single extracted entity"""
    # Required fields with validation
    name: str = Field(..., description="Name or title of the entity")
    type: str = Field(..., description="Type of entity (Person, Organization, etc.)")
    
    # Optional fields with sensible defaults (no Field defaults for Gemini compatibility)
    id: str = ""
    confidence: float = 0.8
    context: str = ""
    quotes: List[str] = []
    type_definition: str = ""  # NEW: LLM-generated semantic definition
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Entity name cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('type')
    @classmethod
    def type_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Entity type cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('id')
    @classmethod
    def id_field_validation(cls, v):
        # ID can be empty (default), but if provided, should not be whitespace-only
        if v and not v.strip():
            return ""  # Convert whitespace-only to empty string
        return v.strip() if v else v
    
    @field_validator('confidence')
    @classmethod
    def confidence_must_be_valid(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Confidence must be a number')
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    @property
    def properties(self):
        """Backward compatibility property"""
        return {}
    
    @property  
    def metadata(self):
        """Backward compatibility property"""
        return {}
    
    def to_neo4j_dict(self) -> Dict[str, Any]:
        """Convert to Neo4j-compatible format"""
        data = self.model_dump()
        # Convert empty strings to None for Neo4j
        for key, value in data.items():
            if value == "":
                data[key] = None
        return data
    
    @classmethod
    def from_neo4j_dict(cls, data: Dict[str, Any]) -> 'ExtractedEntity':
        """Create from Neo4j data"""
        # Convert None values back to empty strings for Pydantic
        clean_data = {}
        for key, value in data.items():
            # Handle field name mapping from Neo4j
            if key == 'entity_type':
                clean_data['type'] = value
            elif value is None and key in ['id', 'context']:
                clean_data[key] = ""
            else:
                clean_data[key] = value
        return cls(**clean_data)

class ExtractedRelationship(BaseModel):
    """Single extracted relationship"""
    # Required fields with validation
    source_entity: str = Field(..., description="Name of source entity")
    target_entity: str = Field(..., description="Name of target entity")
    relationship_type: str = Field(..., description="Type of relationship")
    
    # Optional fields with sensible defaults (no Field defaults for Gemini compatibility)
    id: str = ""
    confidence: float = 0.8
    context: str = ""
    quotes: List[str] = []
    relationship_definition: str = ""  # NEW: LLM-generated semantic definition
    
    @field_validator('source_entity', 'target_entity', 'relationship_type')
    @classmethod
    def required_fields_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Required relationship fields cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('id')
    @classmethod
    def id_field_validation(cls, v):
        # ID can be empty (default), but if provided, should not be whitespace-only
        if v and not v.strip():
            return ""  # Convert whitespace-only to empty string
        return v.strip() if v else v
    
    @field_validator('confidence')
    @classmethod
    def confidence_must_be_valid(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Confidence must be a number')
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    @property  
    def metadata(self):
        """Backward compatibility property"""
        return {}
    
    def to_neo4j_dict(self) -> Dict[str, Any]:
        """Convert to Neo4j-compatible format"""
        data = self.model_dump()
        # Convert empty strings to None for Neo4j
        for key, value in data.items():
            if value == "":
                data[key] = None
        return data
    
    @classmethod
    def from_neo4j_dict(cls, data: Dict[str, Any]) -> 'ExtractedRelationship':
        """Create from Neo4j data"""
        # Convert None values back to empty strings for Pydantic
        clean_data = {}
        for key, value in data.items():
            if value is None and key in ['id', 'context']:
                clean_data[key] = ""
            else:
                clean_data[key] = value
        return cls(**clean_data)

class ExtractedCode(BaseModel):
    """Single extracted thematic code"""
    # Required fields with validation
    name: str = Field(..., description="Name of the thematic code")
    description: str = Field(..., description="Description of what this code represents")
    
    # Optional fields with sensible defaults (no Field defaults for Gemini compatibility)
    id: str = ""
    quotes: List[str] = []
    frequency: int = 1
    confidence: float = 0.8
    
    @field_validator('name', 'description')
    @classmethod
    def required_fields_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Required code fields cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('id')
    @classmethod
    def id_field_validation(cls, v):
        # ID can be empty (default), but if provided, should not be whitespace-only
        if v and not v.strip():
            return ""  # Convert whitespace-only to empty string
        return v.strip() if v else v
    
    @field_validator('confidence')
    @classmethod
    def confidence_must_be_valid(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Confidence must be a number')
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    @field_validator('frequency')
    @classmethod
    def frequency_must_be_valid(cls, v):
        if not isinstance(v, int):
            raise ValueError('Frequency must be an integer')
        if v < 0:
            raise ValueError('Frequency must be non-negative')
        return v
    
    def to_neo4j_dict(self) -> Dict[str, Any]:
        """Convert to Neo4j-compatible format"""
        data = self.model_dump()
        # Convert empty strings to None for Neo4j
        for key, value in data.items():
            if value == "":
                data[key] = None
        return data
    
    @classmethod
    def from_neo4j_dict(cls, data: Dict[str, Any]) -> 'ExtractedCode':
        """Create from Neo4j data"""
        # Convert None values back to empty strings for Pydantic
        clean_data = {}
        for key, value in data.items():
            if value is None and key == 'id':
                clean_data[key] = ""
            else:
                clean_data[key] = value
        return cls(**clean_data)

class ComprehensiveExtractionResult(BaseModel):
    """Complete structured extraction result from a single pass"""
    # Required field with validation
    summary: str = Field(..., description="Brief summary of extraction")
    
    # Optional fields with sensible defaults (no Field defaults for Gemini compatibility)
    entities: List[ExtractedEntity] = []
    relationships: List[ExtractedRelationship] = []
    codes: List[ExtractedCode] = []
    total_entities: int = 0
    total_relationships: int = 0
    total_codes: int = 0
    confidence_score: float = 0.8
    
    @field_validator('summary')
    @classmethod
    def summary_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Summary cannot be empty or whitespace')
        return v.strip()
    
    def to_neo4j_dict(self) -> Dict[str, Any]:
        """Convert to Neo4j-compatible format"""
        data = self.model_dump()
        # Convert empty strings to None for Neo4j  
        for key, value in data.items():
            if value == "":
                data[key] = None
        return data
    
    @classmethod
    def from_neo4j_dict(cls, data: Dict[str, Any]) -> 'ComprehensiveExtractionResult':
        """Create from Neo4j data"""
        # Convert None values back to empty strings for Pydantic
        clean_data = {}
        for key, value in data.items():
            if value is None and key in ['summary']:
                clean_data[key] = ""
            else:
                clean_data[key] = value
        return cls(**clean_data)

# Alias for backward compatibility
ExtractionRequestSchema = ComprehensiveExtractionResult


class QuoteRelationship(BaseModel):
    """Relationship found within a specific quote"""
    source_entity: str = Field(..., description="Source entity name")
    target_entity: str = Field(..., description="Target entity name")
    relationship_type: str = Field(..., description="Type of relationship")
    context: str = Field(..., description="Supporting context from the quote")
    confidence: float = 0.8
    
    @field_validator('source_entity', 'target_entity', 'relationship_type')
    @classmethod
    def fields_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Relationship fields cannot be empty or whitespace')
        return v.strip()


class ThemeQuote(BaseModel):
    """Quote that supports a specific theme with extracted entities"""
    text: str = Field(..., description="Exact quote text from interview")
    line_start: int = Field(..., description="Starting line number")
    line_end: int = Field(..., description="Ending line number")
    confidence: float = 0.8
    entities: List[str] = []  # Entity names found in this quote
    relationships: List[QuoteRelationship] = []  # Relationships found in this quote
    
    @field_validator('text')
    @classmethod
    def text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Quote text cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('line_start', 'line_end')
    @classmethod
    def line_numbers_must_be_positive(cls, v):
        if not isinstance(v, int) or v < 1:
            raise ValueError('Line numbers must be positive integers')
        return v
    
    @field_validator('confidence')
    @classmethod
    def confidence_must_be_valid(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Confidence must be a number')
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class ExtractedTheme(BaseModel):
    """Single thematic code with supporting evidence"""
    name: str = Field(..., description="Name of the thematic code")
    description: str = Field(..., description="What this theme represents")
    supporting_quotes: List[ThemeQuote] = []
    frequency: int = 1
    confidence: float = 0.8
    
    @field_validator('name', 'description')
    @classmethod
    def fields_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Theme name and description cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('frequency')
    @classmethod
    def frequency_must_be_positive(cls, v):
        if not isinstance(v, int) or v < 1:
            raise ValueError('Frequency must be a positive integer')
        return v
    
    @field_validator('confidence')
    @classmethod
    def confidence_must_be_valid(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Confidence must be a number')
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class CodeDrivenExtractionResult(BaseModel):
    """Code-driven extraction result with themes → quotes → entities hierarchy"""
    summary: str = Field(..., description="Brief summary of thematic analysis")
    themes: List[ExtractedTheme] = []
    total_themes: int = 0
    total_quotes: int = 0
    total_entities: int = 0
    confidence_score: float = 0.8
    
    @field_validator('summary')
    @classmethod
    def summary_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Summary cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('total_themes', 'total_quotes', 'total_entities')
    @classmethod
    def totals_must_be_non_negative(cls, v):
        if not isinstance(v, int) or v < 0:
            raise ValueError('Total counts must be non-negative integers')
        return v
    
    @field_validator('confidence_score')
    @classmethod
    def confidence_must_be_valid(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Confidence must be a number')
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    def to_neo4j_dict(self) -> Dict[str, Any]:
        """Convert to Neo4j-compatible format"""
        data = self.model_dump()
        # Convert empty strings to None for Neo4j  
        for key, value in data.items():
            if value == "":
                data[key] = None
        return data
    
    @classmethod
    def from_neo4j_dict(cls, data: Dict[str, Any]) -> 'CodeDrivenExtractionResult':
        """Create from Neo4j data"""
        # Convert None values back to empty strings for Pydantic
        clean_data = {}
        for key, value in data.items():
            if value is None and key in ['summary']:
                clean_data[key] = ""
            else:
                clean_data[key] = value
        return cls(**clean_data)
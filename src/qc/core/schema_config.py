"""
YAML-based Schema Configuration System

This module replaces the brittle string parsing with robust YAML configuration
for defining entity types, properties, and relationships.
"""

import yaml
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, field_validator, Field, ConfigDict


class PropertyType(str, Enum):
    """Supported property types"""
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ENUM = "enum"
    LIST = "list"
    REFERENCE = "reference"  # Reference to another entity


class RelationshipDirection(str, Enum):
    """Direction of relationships"""
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    BIDIRECTIONAL = "bidirectional"


class PropertyDefinition(BaseModel):
    """Definition of an entity property"""
    model_config = ConfigDict(use_enum_values=True)
    
    type: PropertyType
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None
    
    # Enum-specific fields
    values: Optional[List[str]] = None
    
    # List-specific fields
    item_type: Optional[PropertyType] = None
    
    # Reference-specific fields
    target_entity: Optional[str] = None
    
    # Validation fields
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    
    # Extraction hints
    extraction_hints: Optional[str] = None
    examples: Optional[List[str]] = None
    
    @field_validator('values')
    @classmethod
    def validate_enum_values(cls, v, info):
        if info.data.get('type') == PropertyType.ENUM and not v:
            raise ValueError("Enum properties must specify 'values'")
        return v
    
    @field_validator('target_entity')
    @classmethod
    def validate_reference_target(cls, v, info):
        if info.data.get('type') == PropertyType.REFERENCE and not v:
            raise ValueError("Reference properties must specify 'target_entity'")
        return v


class RelationshipDefinition(BaseModel):
    """Definition of a relationship between entities"""
    model_config = ConfigDict(use_enum_values=True)
    
    target_entity: str
    relationship_type: str
    direction: RelationshipDirection = RelationshipDirection.OUTGOING
    description: Optional[str] = None
    required: bool = False
    
    # Relationship properties
    properties: Dict[str, PropertyDefinition] = Field(default_factory=dict)
    
    # Extraction hints
    extraction_hints: Optional[str] = None
    examples: Optional[List[str]] = None


class EntityDefinition(BaseModel):
    """Complete definition of an entity type"""
    description: str
    
    # Entity properties
    properties: Dict[str, PropertyDefinition] = Field(default_factory=dict)
    
    # Relationships this entity can have
    relationships: Dict[str, RelationshipDefinition] = Field(default_factory=dict)
    
    # Extraction configuration
    extraction_hints: Optional[str] = None
    examples: Optional[List[str]] = None
    
    # Advanced configuration
    labels: Optional[List[str]] = None  # Additional Neo4j labels
    required_properties: Optional[List[str]] = None
    unique_properties: Optional[List[str]] = None


class SchemaConfiguration(BaseModel):
    """Complete schema configuration"""
    version: str = "1.0"
    name: Optional[str] = "Unnamed Schema"
    description: Optional[str] = None
    
    # Entity definitions
    entities: Dict[str, EntityDefinition]
    
    # Query examples (optional)
    query_examples: Optional[List[str]] = None
    
    # Global settings
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    def get_entity(self, entity_type: str) -> Optional[EntityDefinition]:
        """Get entity definition by type"""
        return self.entities.get(entity_type)
    
    def get_all_entity_types(self) -> List[str]:
        """Get all defined entity types"""
        return list(self.entities.keys())
    
    def validate_reference_integrity(self) -> List[str]:
        """Validate that all entity references exist"""
        errors = []
        entity_types = set(self.entities.keys())
        
        for entity_name, entity_def in self.entities.items():
            # Check property references
            for prop_name, prop_def in entity_def.properties.items():
                if prop_def.type == PropertyType.REFERENCE:
                    if prop_def.target_entity not in entity_types:
                        errors.append(
                            f"Entity '{entity_name}' property '{prop_name}' "
                            f"references unknown entity '{prop_def.target_entity}'"
                        )
            
            # Check relationship references
            for rel_name, rel_def in entity_def.relationships.items():
                if rel_def.target_entity not in entity_types:
                    errors.append(
                        f"Entity '{entity_name}' relationship '{rel_name}' "
                        f"references unknown entity '{rel_def.target_entity}'"
                    )
        
        return errors


class SchemaLoader:
    """Utility for loading and validating schemas"""
    
    @staticmethod
    def load_from_yaml(file_path: Union[str, Path]) -> SchemaConfiguration:
        """Load schema from YAML file"""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        return SchemaConfiguration(**data)
    
    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> SchemaConfiguration:
        """Load schema from dictionary"""
        return SchemaConfiguration(**data)
    
    @staticmethod
    def save_to_yaml(schema: SchemaConfiguration, file_path: Union[str, Path]):
        """Save schema to YAML file"""
        with open(file_path, 'w') as f:
            # Convert to dictionary with proper enum handling
            schema_dict = schema.model_dump()
            yaml.dump(schema_dict, f, default_flow_style=False, indent=2)


# Example schema configurations
def create_research_schema() -> SchemaConfiguration:
    """Create the default research schema configuration"""
    return SchemaLoader.load_from_yaml(
        str(Path(__file__).parent / "research_schema.yaml")
    )

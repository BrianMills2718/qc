"""
Dynamic schema validation for enforcing discovered schemas in Phase 4
"""
from typing import List, Dict, Any, Optional, Literal, get_args
from pydantic import BaseModel, Field, validator, create_model
from enum import Enum
import logging

logger = logging.getLogger(__name__)


def create_code_enum(codes: List[Dict[str, Any]]) -> type:
    """Create an Enum of valid code IDs from discovered taxonomy"""
    code_ids = {code['id']: code['id'] for code in codes}
    if not code_ids:
        # If no codes discovered, allow a placeholder
        code_ids = {'NO_CODES': 'NO_CODES'}
    return Enum('CodeID', code_ids)


def create_entity_type_enum(entity_types: List[Dict[str, Any]]) -> type:
    """Create an Enum of valid entity type IDs from discovered schema"""
    type_ids = {et['id']: et['id'] for et in entity_types}
    if not type_ids:
        # If no types discovered, allow a placeholder
        type_ids = {'NO_TYPES': 'NO_TYPES'}
    return Enum('EntityTypeID', type_ids)


def create_relationship_type_enum(relationship_types: List[Dict[str, Any]]) -> type:
    """Create an Enum of valid relationship type IDs from discovered schema"""
    type_ids = {rt['id']: rt['id'] for rt in relationship_types}
    if not type_ids:
        # If no types discovered, allow a placeholder
        type_ids = {'NO_RELATIONSHIPS': 'NO_RELATIONSHIPS'}
    return Enum('RelationshipTypeID', type_ids)


def create_speaker_property_fields(properties: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create field definitions for speaker properties from discovered schema"""
    fields = {
        'name': (str, Field(..., description="Speaker name")),
        'confidence': (float, Field(1.0, ge=0.0, le=1.0)),
        'identification_method': (str, Field("Unknown")),
        'quotes_count': (int, Field(0, ge=0))
    }
    
    # Add discovered properties as optional fields
    for prop in properties:
        prop_name = prop['name']
        # All custom properties are optional strings for flexibility
        fields[prop_name] = (Optional[str], Field(None, description=prop.get('description', '')))
    
    return fields


class ValidatedQuote(BaseModel):
    """Base model for validated quotes - will be customized with discovered codes"""
    id: str
    text: str
    speaker: Dict[str, Any]  # Will be validated separately
    code_ids: List[str]  # Will be constrained by enum
    location_start: Optional[int] = None
    location_end: Optional[int] = None
    location_type: Optional[str] = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    semantic_type: Optional[str] = None


class ValidatedEntity(BaseModel):
    """Base model for validated entities - will be customized with discovered types"""
    name: str
    type: str  # Will be constrained by enum
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    first_mention_quote_id: Optional[str] = None
    mention_count: int = 1
    contexts: List[str] = []


class ValidatedRelationship(BaseModel):
    """Base model for validated relationships - will be customized with discovered types"""
    source_entity: str
    relationship_type: str  # Will be constrained by enum
    target_entity: str
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    quote_ids: List[str] = []


def create_phase4_validators(
    code_taxonomy: Dict[str, Any],
    speaker_schema: Dict[str, Any],
    entity_schema: Dict[str, Any]
) -> tuple:
    """
    Create dynamic Pydantic models that enforce discovered schemas.
    Returns (ValidatedQuoteModel, ValidatedSpeakerModel, ValidatedEntityModel, ValidatedRelationshipModel)
    """
    
    # Create enums from discovered schemas
    CodeEnum = create_code_enum(code_taxonomy.get('codes', []))
    EntityTypeEnum = create_entity_type_enum(entity_schema.get('entity_types', []))
    RelationshipTypeEnum = create_relationship_type_enum(entity_schema.get('relationship_types', []))
    
    # Create speaker model with discovered properties
    speaker_fields = create_speaker_property_fields(speaker_schema.get('properties', []))
    ValidatedSpeaker = create_model('ValidatedSpeaker', **speaker_fields)
    
    # Create validated quote model with code constraints
    class ValidatedQuoteWithCodes(ValidatedQuote):
        code_ids: List[CodeEnum]
        
        @validator('code_ids', pre=True)
        def validate_code_ids(cls, v):
            """Ensure all code IDs are from discovered taxonomy"""
            if isinstance(v, list):
                valid_codes = [c.value for c in CodeEnum]
                invalid_codes = [code for code in v if code not in valid_codes]
                if invalid_codes:
                    logger.warning(f"Invalid code IDs will be filtered: {invalid_codes}")
                    # Filter out invalid codes
                    v = [code for code in v if code in valid_codes]
            return v
    
    # Create validated entity model with type constraints
    class ValidatedEntityWithTypes(ValidatedEntity):
        type: EntityTypeEnum
        
        @validator('type', pre=True)
        def validate_entity_type(cls, v):
            """Ensure entity type is from discovered schema"""
            valid_types = [t.value for t in EntityTypeEnum]
            if v not in valid_types:
                raise ValueError(f"Entity type '{v}' not in discovered schema. Valid types: {valid_types}")
            return v
    
    # Create validated relationship model with type constraints
    class ValidatedRelationshipWithTypes(ValidatedRelationship):
        relationship_type: RelationshipTypeEnum
        
        @validator('relationship_type', pre=True)
        def validate_relationship_type(cls, v):
            """Ensure relationship type is from discovered schema"""
            valid_types = [t.value for t in RelationshipTypeEnum]
            if v not in valid_types:
                raise ValueError(f"Relationship type '{v}' not in discovered schema. Valid types: {valid_types}")
            return v
    
    return (
        ValidatedQuoteWithCodes,
        ValidatedSpeaker,
        ValidatedEntityWithTypes,
        ValidatedRelationshipWithTypes
    )


def validate_extraction_results(
    extraction_data: Dict[str, Any],
    code_taxonomy: Dict[str, Any],
    speaker_schema: Dict[str, Any],
    entity_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate and clean extraction results to ensure they conform to discovered schemas.
    Returns cleaned data with violations removed.
    """
    
    # Create validators
    QuoteValidator, SpeakerValidator, EntityValidator, RelValidator = create_phase4_validators(
        code_taxonomy, speaker_schema, entity_schema
    )
    
    # Track violations for reporting
    violations = {
        'invalid_codes': set(),
        'invalid_entity_types': set(),
        'invalid_relationship_types': set(),
        'filtered_entities': [],
        'filtered_relationships': []
    }
    
    # Validate quotes and filter invalid codes
    validated_quotes = []
    for quote in extraction_data.get('quotes', []):
        try:
            # Validate and potentially filter code IDs
            validated_quote = QuoteValidator(**quote)
            validated_quotes.append(validated_quote.dict())
        except Exception as e:
            logger.warning(f"Quote validation error: {e}")
            # Still include quote but with filtered codes
            if 'code_ids' in quote:
                valid_codes = [c.value for c in create_code_enum(code_taxonomy.get('codes', []))]
                original_codes = quote['code_ids']
                quote['code_ids'] = [c for c in original_codes if c in valid_codes]
                violations['invalid_codes'].update(set(original_codes) - set(quote['code_ids']))
            validated_quotes.append(quote)
    
    # Validate speakers
    validated_speakers = []
    for speaker in extraction_data.get('speakers', []):
        try:
            validated_speaker = SpeakerValidator(**speaker)
            validated_speakers.append(validated_speaker.dict())
        except Exception as e:
            logger.warning(f"Speaker validation error: {e}")
            # Include basic speaker info even if properties are invalid
            validated_speakers.append({
                'name': speaker.get('name', 'Unknown'),
                'confidence': speaker.get('confidence', 1.0)
            })
    
    # Validate entities and filter invalid types
    validated_entities = []
    for entity in extraction_data.get('entities', []):
        try:
            validated_entity = EntityValidator(**entity)
            validated_entities.append(validated_entity.dict())
        except ValueError as e:
            # Entity type not in schema - skip this entity
            violations['invalid_entity_types'].add(entity.get('type', 'UNKNOWN'))
            violations['filtered_entities'].append(entity)
            logger.warning(f"Filtering entity '{entity.get('name')}' with invalid type '{entity.get('type')}'")
    
    # Validate relationships and filter invalid types
    validated_relationships = []
    entity_names = {e['name'] for e in validated_entities}
    
    for relationship in extraction_data.get('relationships', []):
        # First check if entities exist
        if (relationship.get('source_entity') not in entity_names or 
            relationship.get('target_entity') not in entity_names):
            violations['filtered_relationships'].append(relationship)
            continue
            
        try:
            validated_rel = RelValidator(**relationship)
            validated_relationships.append(validated_rel.dict())
        except ValueError as e:
            # Relationship type not in schema - skip this relationship
            violations['invalid_relationship_types'].add(relationship.get('relationship_type', 'UNKNOWN'))
            violations['filtered_relationships'].append(relationship)
            logger.warning(f"Filtering relationship with invalid type '{relationship.get('relationship_type')}'")
    
    # Log violation summary
    if any(violations.values()):
        logger.warning(f"Schema violations detected:")
        if violations['invalid_codes']:
            logger.warning(f"  - Invalid codes: {violations['invalid_codes']}")
        if violations['invalid_entity_types']:
            logger.warning(f"  - Invalid entity types: {violations['invalid_entity_types']}")
        if violations['invalid_relationship_types']:
            logger.warning(f"  - Invalid relationship types: {violations['invalid_relationship_types']}")
        if violations['filtered_entities']:
            logger.warning(f"  - Filtered {len(violations['filtered_entities'])} entities")
        if violations['filtered_relationships']:
            logger.warning(f"  - Filtered {len(violations['filtered_relationships'])} relationships")
    
    # Return cleaned data
    return {
        'quotes': validated_quotes,
        'speakers': validated_speakers,
        'entities': validated_entities,
        'relationships': validated_relationships,
        'violations': violations
    }
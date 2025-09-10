"""Fix relationships missing type fields by looking them up from entities"""

def fix_relationship_types(entities_and_relationships):
    """
    Fix relationships that are missing source_type or target_type fields
    by looking them up from the entities list.
    """
    # Build entity name to type mapping
    entity_type_map = {}
    for entity in entities_and_relationships.entities:
        # Handle both dict and model objects
        if isinstance(entity, dict):
            entity_type_map[entity['name']] = entity['type']
        else:
            entity_type_map[entity.name] = entity.type
    
    # Fix relationships
    fixed_relationships = []
    for rel in entities_and_relationships.relationships:
        # Handle both dict and model objects
        if isinstance(rel, dict):
            rel_dict = rel
        elif hasattr(rel, 'model_dump'):
            rel_dict = rel.model_dump()
        else:
            # Access attributes directly
            rel_dict = {
                'source_entity': rel.source_entity,
                'target_entity': rel.target_entity,
                'relationship_type': rel.relationship_type,
                'source_type': getattr(rel, 'source_type', None),
                'target_type': getattr(rel, 'target_type', None),
                'quote_id': getattr(rel, 'quote_id', None),
                'confidence': getattr(rel, 'confidence', 0.95)
            }
        
        # Add missing type fields by looking up from entities
        if 'source_type' not in rel_dict or not rel_dict.get('source_type'):
            source_name = rel_dict.get('source_entity')
            if source_name and source_name in entity_type_map:
                rel_dict['source_type'] = entity_type_map[source_name]
            else:
                # Skip this relationship if we can't determine the type
                continue
        
        if 'target_type' not in rel_dict or not rel_dict.get('target_type'):
            target_name = rel_dict.get('target_entity')
            if target_name and target_name in entity_type_map:
                rel_dict['target_type'] = entity_type_map[target_name]
            else:
                # Skip this relationship if we can't determine the type
                continue
        
        fixed_relationships.append(rel_dict)
    
    # Update the relationships
    entities_and_relationships.relationships = fixed_relationships
    entities_and_relationships.total_relationships = len(fixed_relationships)
    
    return entities_and_relationships
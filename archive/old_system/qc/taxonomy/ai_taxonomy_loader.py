"""
AI-Powered Taxonomy Loader

Accepts messy/informal taxonomy definitions in various formats and uses LLM
to parse them into structured TypeDefinitions for the validation system.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

from ..consolidation.consolidation_schemas import TypeDefinition
from ..llm.llm_handler import LLMHandler

logger = logging.getLogger(__name__)


class TaxonomyUpload(BaseModel):
    """User's uploaded taxonomy in any format"""
    content: str = Field(..., description="Raw content of uploaded file")
    filename: str = Field(..., description="Original filename for context")
    format_hint: Optional[str] = Field(None, description="User hint about format")


class ParsedTaxonomy(BaseModel):
    """LLM-parsed taxonomy structure"""
    entity_types: List[TypeDefinition] = Field(..., description="Extracted entity types")
    relationship_types: List[TypeDefinition] = Field(..., description="Extracted relationship types")
    code_categories: List[TypeDefinition] = Field(default=[], description="Predefined code categories if any")
    metadata: Dict[str, Any] = Field(default={}, description="Additional taxonomy metadata")
    confidence: float = Field(..., description="LLM confidence in parsing accuracy")
    parsing_notes: str = Field(..., description="Notes about parsing decisions made")


class AITaxonomyLoader:
    """
    Intelligent taxonomy loader that accepts various formats and converts
    them to structured TypeDefinitions using LLM understanding.
    """
    
    def __init__(self, llm_handler: LLMHandler):
        self.llm = llm_handler
        
    async def load_taxonomy(self, upload: TaxonomyUpload) -> ParsedTaxonomy:
        """
        Parse uploaded taxonomy using AI to handle various formats
        
        Args:
            upload: User's uploaded taxonomy content
            
        Returns:
            ParsedTaxonomy with structured types
        """
        
        # First, try to detect if it's a structured format
        structured_data = self._try_parse_structured(upload.content)
        
        if structured_data:
            # Even if structured, use LLM to enhance with definitions
            prompt = self._build_enhancement_prompt(structured_data, upload.filename)
        else:
            # Fully unstructured - need LLM to parse everything
            prompt = self._build_parsing_prompt(upload.content, upload.filename)
        
        try:
            # Use LLM to parse/enhance the taxonomy
            response = await self.llm.generate_structured_output(
                prompt=prompt,
                response_model=ParsedTaxonomy,
                temperature=0.3  # Lower temperature for consistency
            )
            
            logger.info(f"Successfully parsed taxonomy with {len(response.entity_types)} entities "
                       f"and {len(response.relationship_types)} relationships")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to parse taxonomy: {e}")
            # Return minimal fallback
            return self._create_fallback_taxonomy()
    
    def _try_parse_structured(self, content: str) -> Optional[Dict]:
        """Try to parse as JSON, YAML, or CSV"""
        
        # Try JSON
        try:
            return json.loads(content)
        except:
            pass
        
        # Try YAML
        try:
            return yaml.safe_load(content)
        except:
            pass
        
        # Try simple list format (one item per line)
        lines = content.strip().split('\n')
        if len(lines) > 2 and all(line.strip() for line in lines[:5]):
            return {"items": lines}
        
        return None
    
    def _build_parsing_prompt(self, content: str, filename: str) -> str:
        """Build prompt for parsing unstructured taxonomy"""
        
        return f"""You are a qualitative research assistant helping to parse a coding taxonomy/schema.

UPLOADED FILE: {filename}
CONTENT:
{content}

Your task is to extract a structured taxonomy from this content. Look for:

1. ENTITY TYPES: Types of things mentioned (people, organizations, concepts, tools, etc.)
   - Extract the type name
   - Generate a clear 1-2 sentence definition
   - Note any properties or attributes mentioned

2. RELATIONSHIP TYPES: How entities connect (works_at, uses, manages, causes, etc.)
   - Extract the relationship name  
   - Determine directionality (A relates to B)
   - Generate a clear definition
   
3. CODE CATEGORIES: Thematic categories or code groups if mentioned
   - Extract category names
   - Generate definitions
   - Note any hierarchical structure

PARSING RULES:
- Be inclusive - extract anything that looks like a type or category
- Generate clear, academic-style definitions even if not provided
- Standardize naming (e.g., "works at" → "WORKS_AT")
- If you see examples, infer the type from them
- If you see hierarchies (indentation, bullets), preserve the structure

EXAMPLES OF WHAT TO EXTRACT:
- "People in leadership roles" → Entity type: "Leader" with definition
- "uses/utilizing" → Relationship: "USES"
- "Challenges: Technical, Organizational" → Code categories

Return a structured taxonomy that researchers can use for deductive coding."""
    
    def _build_enhancement_prompt(self, structured_data: Dict, filename: str) -> str:
        """Build prompt for enhancing already-structured data"""
        
        return f"""You are a qualitative research assistant enhancing a coding taxonomy.

UPLOADED FILE: {filename}
PARSED STRUCTURE:
{json.dumps(structured_data, indent=2)}

Enhance this taxonomy by:

1. Adding clear academic definitions where missing
2. Standardizing type names (UpperCamelCase for entities, UPPER_SNAKE for relationships)
3. Inferring relationship directionality
4. Organizing any implicit hierarchies
5. Adding relevant properties for entity types

Maintain all original types but improve their clarity and usability."""
    
    def _create_fallback_taxonomy(self) -> ParsedTaxonomy:
        """Create minimal fallback taxonomy if parsing fails"""
        
        return ParsedTaxonomy(
            entity_types=[
                TypeDefinition(
                    type_name="Entity",
                    definition="Generic entity type - parsing failed",
                    frequency=0
                )
            ],
            relationship_types=[
                TypeDefinition(
                    type_name="RELATED_TO",
                    definition="Generic relationship - parsing failed",
                    frequency=0
                )
            ],
            confidence=0.1,
            parsing_notes="Failed to parse uploaded taxonomy, using minimal defaults"
        )


class TaxonomyExamples:
    """Example formats that users might upload"""
    
    MESSY_TEXT = """
    Interview Coding Scheme
    
    People types:
    - Managers (people who manage teams)
    - Engineers
    - Executives (C-level, VP)
    - Consultants
    
    Organizations mentioned:
    Tech companies, startups, enterprises, universities
    
    Relationships:
    - employment (who works where)
    - collaboration between people
    - people using tools/methods
    - skeptical/supportive attitudes
    
    Main themes to code:
    * Innovation challenges
    * Remote work impacts  
    * Technology adoption
    * Leadership styles
    """
    
    SIMPLE_LIST = """
    Person
    Organization
    Technology
    Method
    Challenge
    Opportunity
    """
    
    CSV_STYLE = """
    Type,Category,Definition
    CEO,Person,Chief Executive Officer
    CTO,Person,Chief Technology Officer  
    StartUp,Organization,Early stage company
    Enterprise,Organization,Large established company
    WORKS_AT,Relationship,Employment relationship
    PARTNERS_WITH,Relationship,Business partnership
    """
    
    ACADEMIC_YAML = """
    entities:
      person_types:
        - name: Researcher
          definition: Academic or industry researcher
        - name: Practitioner
          definition: Industry professional
      
      organizations:
        - ResearchInstitute
        - Corporation
        - Government
    
    relationships:
      - COLLABORATES
      - FUNDS
      - PUBLISHES
    
    themes:
      innovation:
        - disruption
        - incremental_change
      adoption:
        - early_adopter
        - laggard
    """
"""
FastAPI endpoint for AI-powered taxonomy upload and management
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from pathlib import Path

from ..taxonomy.ai_taxonomy_loader import AITaxonomyLoader, TaxonomyUpload, ParsedTaxonomy
from ..llm.llm_handler import LLMHandler
from ..consolidation.consolidation_schemas import TypeDefinition

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/taxonomy", tags=["taxonomy"])

# Store parsed taxonomies in memory (in production, use database)
active_taxonomies = {}


@router.post("/upload")
async def upload_taxonomy(
    file: UploadFile = File(...),
    format_hint: Optional[str] = Form(None, description="Optional hint about format (json, yaml, csv, text)"),
    project_id: Optional[str] = Form(None, description="Project ID to associate taxonomy with")
):
    """
    Upload a taxonomy file in any format and have AI parse it
    
    Accepts:
    - JSON, YAML, CSV files
    - Plain text descriptions
    - Word docs with coding schemes
    - Even screenshots of coding tables (if OCR is available)
    """
    
    try:
        # Read file content
        content = await file.read()
        
        # Handle different file types
        if file.filename.endswith(('.png', '.jpg', '.jpeg')):
            # Would need OCR here
            return JSONResponse(
                status_code=501,
                content={"error": "Image OCR not yet implemented"}
            )
        
        # Decode text content
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            # Try different encoding
            text_content = content.decode('latin-1')
        
        # Create upload object
        upload = TaxonomyUpload(
            content=text_content,
            filename=file.filename,
            format_hint=format_hint
        )
        
        # Initialize AI loader
        llm_handler = LLMHandler()  # This would use existing LLM configuration
        loader = AITaxonomyLoader(llm_handler)
        
        # Parse taxonomy using AI
        parsed = await loader.load_taxonomy(upload)
        
        # Store for project
        if project_id:
            active_taxonomies[project_id] = parsed
        
        # Return parsed taxonomy
        return {
            "success": True,
            "filename": file.filename,
            "parsed_taxonomy": {
                "entity_types": [
                    {
                        "name": t.type_name,
                        "definition": t.definition
                    } for t in parsed.entity_types
                ],
                "relationship_types": [
                    {
                        "name": t.type_name,
                        "definition": t.definition
                    } for t in parsed.relationship_types
                ],
                "code_categories": [
                    {
                        "name": t.type_name,
                        "definition": t.definition
                    } for t in parsed.code_categories
                ],
                "confidence": parsed.confidence,
                "notes": parsed.parsing_notes
            },
            "message": f"Successfully parsed {len(parsed.entity_types)} entity types and "
                      f"{len(parsed.relationship_types)} relationship types"
        }
        
    except Exception as e:
        logger.error(f"Failed to upload taxonomy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview")
async def preview_taxonomy(
    content: str = Form(..., description="Taxonomy content to preview"),
    format_hint: Optional[str] = Form(None)
):
    """
    Preview how AI would parse taxonomy content without saving
    Useful for testing and refinement
    """
    
    try:
        upload = TaxonomyUpload(
            content=content,
            filename="preview.txt",
            format_hint=format_hint
        )
        
        llm_handler = LLMHandler()
        loader = AITaxonomyLoader(llm_handler)
        
        parsed = await loader.load_taxonomy(upload)
        
        return {
            "preview": {
                "entity_types": [t.type_name for t in parsed.entity_types],
                "relationship_types": [t.type_name for t in parsed.relationship_types],
                "total_types": len(parsed.entity_types) + len(parsed.relationship_types),
                "confidence": parsed.confidence,
                "notes": parsed.parsing_notes
            }
        }
        
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples")
async def get_taxonomy_examples():
    """
    Get example taxonomy formats to help users
    """
    
    from ..taxonomy.ai_taxonomy_loader import TaxonomyExamples
    
    return {
        "examples": {
            "messy_text": {
                "description": "Informal text description",
                "content": TaxonomyExamples.MESSY_TEXT
            },
            "simple_list": {
                "description": "Simple list of types",
                "content": TaxonomyExamples.SIMPLE_LIST
            },
            "csv_format": {
                "description": "CSV with headers",
                "content": TaxonomyExamples.CSV_STYLE
            },
            "yaml_format": {
                "description": "Structured YAML",
                "content": TaxonomyExamples.ACADEMIC_YAML
            }
        },
        "tips": [
            "You can upload any text format - the AI will parse it",
            "Include definitions if you have them, but AI can generate them if missing",
            "Hierarchies and categories are preserved",
            "The more context you provide, the better the parsing"
        ]
    }


@router.get("/active/{project_id}")
async def get_active_taxonomy(project_id: str):
    """
    Get the active taxonomy for a project
    """
    
    if project_id not in active_taxonomies:
        raise HTTPException(status_code=404, detail="No taxonomy found for project")
    
    taxonomy = active_taxonomies[project_id]
    
    return {
        "project_id": project_id,
        "taxonomy": {
            "entity_types": [t.dict() for t in taxonomy.entity_types],
            "relationship_types": [t.dict() for t in taxonomy.relationship_types],
            "code_categories": [t.dict() for t in taxonomy.code_categories]
        }
    }
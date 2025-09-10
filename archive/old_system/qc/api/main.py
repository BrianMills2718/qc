"""
REST API interface for qualitative coding analysis.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import uuid4
import traceback

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..core.neo4j_manager import EnhancedNeo4jManager
from ..core.native_gemini_client import NativeGeminiClient
from ..extraction.multi_pass_extractor import MultiPassExtractor, InterviewContext
from ..monitoring.health import get_system_health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app configuration
app = FastAPI(
    title="Qualitative Coding Analysis API",
    description="REST API for extracting entities, relationships, and codes from qualitative research interviews",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for dependencies
neo4j_manager = None
llm_client = None
extractor = None

# In-memory job tracking (use Redis/database for production)
active_jobs: Dict[str, Dict[str, Any]] = {}


# Pydantic models for request/response
class AnalysisRequest(BaseModel):
    """Request model for interview analysis."""
    text: str = Field(..., description="Interview text to analyze", min_length=10)
    validation_mode: str = Field("hybrid", description="Validation mode: hybrid, academic, exploratory")
    session_id: Optional[str] = Field(None, description="Optional session ID for grouping analyses")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the interview")


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: processing, completed, failed")
    session_id: Optional[str] = Field(None, description="Session ID if provided")
    entities_found: int = Field(0, description="Number of entities extracted")
    relationships_found: int = Field(0, description="Number of relationships found")
    codes_found: int = Field(0, description="Number of codes identified")
    processing_time_seconds: Optional[float] = Field(None, description="Processing time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")


class JobStatus(BaseModel):
    """Model for job status information."""
    job_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    progress: float = Field(0.0, description="Progress percentage (0.0 to 1.0)")
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class QueryRequest(BaseModel):
    """Request model for natural language queries."""
    query: str = Field(..., description="Natural language query", min_length=3)
    session_id: Optional[str] = Field(None, description="Optional session ID to limit scope")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)


class QueryResponse(BaseModel):
    """Response model for query results."""
    query: str
    results: List[Dict[str, Any]]
    total_count: int
    execution_time_seconds: float


# Dependency injection functions
async def get_neo4j_manager():
    """Get Neo4j manager instance."""
    global neo4j_manager
    if neo4j_manager is None:
        neo4j_manager = EnhancedNeo4jManager()
        await neo4j_manager.connect()
    return neo4j_manager


async def get_llm_client():
    """Get LLM client instance."""
    global llm_client
    if llm_client is None:
        llm_client = NativeGeminiClient()
    return llm_client


async def get_extractor():
    """Get multi-pass extractor instance."""
    global extractor
    if extractor is None:
        neo4j = await get_neo4j_manager()
        llm = await get_llm_client()
        # Load the default schema configuration
        from ..core.schema_config import SchemaLoader
        schema = SchemaLoader.load_from_yaml("qc/core/research_schema.yaml")
        extractor = MultiPassExtractor(neo4j, schema, llm)
    return extractor


# Background task for analysis processing
async def process_analysis(
    job_id: str,
    text: str,
    validation_mode: str,
    session_id: Optional[str],
    metadata: Optional[Dict[str, Any]]
):
    """Background task to process interview analysis."""
    start_time = datetime.now(timezone.utc)
    
    try:
        # Update job status
        active_jobs[job_id].update({
            "status": "processing",
            "progress": 0.1,
            "started_at": start_time.isoformat()
        })
        
        # Get extractor instance
        extractor_instance = await get_extractor()
        
        # Create interview context
        context = InterviewContext(
            interview_id=job_id,
            session_id=session_id or str(uuid4()),
            interview_text=text,
            metadata=metadata or {}
        )
        
        # Update progress
        active_jobs[job_id]["progress"] = 0.3
        
        # Perform extraction
        results = await extractor_instance.extract_interview(context, validation_mode)
        
        # Update progress
        active_jobs[job_id]["progress"] = 0.9
        
        # Calculate processing time
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Update job with results
        active_jobs[job_id].update({
            "status": "completed",
            "progress": 1.0,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "processing_time_seconds": processing_time,
            "results": {
                "entities_found": len(results.get("entities", [])),
                "relationships_found": len(results.get("relationships", [])),
                "codes_found": len(results.get("codes", [])),
                "extraction_results": results
            }
        })
        
        logger.info(f"Analysis job {job_id} completed successfully in {processing_time:.2f}s")
        
    except Exception as e:
        error_msg = str(e)
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Update job with error
        active_jobs[job_id].update({
            "status": "failed",
            "progress": 0.0,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "processing_time_seconds": processing_time,
            "error_message": error_msg
        })
        
        logger.error(f"Analysis job {job_id} failed: {error_msg}")
        logger.error(traceback.format_exc())


# API endpoints
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint with basic information."""
    return {
        "message": "Qualitative Coding Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze",
            "status": "/jobs/{job_id}",
            "query": "/query",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_interview(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze interview text and extract structured data.
    
    This endpoint processes interview text in the background and returns a job ID
    for tracking progress. Use the /jobs/{job_id} endpoint to check status and results.
    """
    try:
        # Generate unique job ID
        job_id = str(uuid4())
        
        # Initialize job tracking
        active_jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "progress": 0.0,
            "session_id": request.session_id,
            "text_length": len(request.text),
            "validation_mode": request.validation_mode
        }
        
        # Add background task
        background_tasks.add_task(
            process_analysis,
            job_id,
            request.text,
            request.validation_mode,
            request.session_id,
            request.metadata
        )
        
        return AnalysisResponse(
            job_id=job_id,
            status="processing",
            session_id=request.session_id,
            entities_found=0,
            relationships_found=0,
            codes_found=0
        )
        
    except Exception as e:
        logger.error(f"Failed to start analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start analysis: {str(e)}"
        )


@app.get("/jobs/{job_id}", response_model=JobStatus, tags=["Jobs"])
async def get_job_status(job_id: str):
    """Get the status and results of an analysis job."""
    if job_id not in active_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job_data = active_jobs[job_id]
    
    return JobStatus(
        job_id=job_id,
        status=job_data["status"],
        created_at=job_data["created_at"],
        completed_at=job_data.get("completed_at"),
        progress=job_data.get("progress", 0.0),
        results=job_data.get("results"),
        error_message=job_data.get("error_message")
    )


@app.get("/jobs", tags=["Jobs"])
async def list_jobs(
    status_filter: Optional[str] = None,
    limit: int = 20
):
    """List recent analysis jobs with optional status filtering."""
    jobs = list(active_jobs.values())
    
    if status_filter:
        jobs = [job for job in jobs if job["status"] == status_filter]
    
    # Sort by creation time (most recent first)
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "jobs": jobs[:limit],
        "total_count": len(jobs),
        "filtered": status_filter is not None
    }


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_data(
    request: QueryRequest,
    neo4j: EnhancedNeo4jManager = Depends(get_neo4j_manager)
):
    """
    Query extracted data using natural language.
    
    This endpoint converts natural language queries into Cypher queries
    and executes them against the Neo4j database.
    """
    try:
        start_time = datetime.now(timezone.utc)
        
        # Natural language to Cypher conversion - requires query builder module
        # This is a future enhancement endpoint
        
        # Placeholder response
        results = []
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        return QueryResponse(
            query=request.query,
            results=results,
            total_count=len(results),
            execution_time_seconds=execution_time
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )


@app.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive system health check."""
    try:
        neo4j = await get_neo4j_manager()
        llm = await get_llm_client()
        
        health_data = await get_system_health(neo4j, llm)
        
        # Return appropriate HTTP status based on health
        if health_data["status"] == "healthy":
            return health_data
        elif health_data["status"] == "degraded":
            return JSONResponse(
                status_code=status.HTTP_206_PARTIAL_CONTENT,
                content=health_data
            )
        else:  # unhealthy
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=health_data
            )
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        )


@app.delete("/jobs/{job_id}", tags=["Jobs"])
async def cancel_job(job_id: str):
    """Cancel a running analysis job."""
    if job_id not in active_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = active_jobs[job_id]
    
    if job["status"] in ["completed", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {job['status']}"
        )
    
    # Mark job as cancelled
    active_jobs[job_id].update({
        "status": "cancelled",
        "completed_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": f"Job {job_id} cancelled successfully"}


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize application resources on startup."""
    logger.info("Starting Qualitative Coding Analysis API...")
    
    try:
        # Initialize core components
        await get_neo4j_manager()
        await get_llm_client()
        await get_extractor()
        
        logger.info("API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Qualitative Coding Analysis API...")
    
    try:
        # Close Neo4j connections
        if neo4j_manager:
            await neo4j_manager.close()
        
        logger.info("API shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.qc.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
#!/usr/bin/env python3
"""
QC API Server - Simplified API Server for GT Analysis

Provides REST API and WebSocket functionality for the API plugin.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

# Import schemas for structured output
from qc_clean.schemas.analysis_schemas import (
    CodeHierarchy, SpeakerAnalysis, EntityMapping, AnalysisSynthesis
)

logger = logging.getLogger(__name__)


class QCAPIServer:
    """Simplified API Server for QC Clean architecture"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_running = False
        self.background_processing_enabled = config.get('background_processing_enabled', False)
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.endpoints: List[Dict[str, Any]] = []
        self._logger = logging.getLogger(f"{__name__}.QCAPIServer")
        self._server = None
        self._app = None
    
    async def start_server(self, host: str, port: int) -> bool:
        """Start the API server"""
        try:
            # Check if FastAPI is available
            from fastapi import FastAPI, HTTPException, BackgroundTasks
            from fastapi.middleware.cors import CORSMiddleware
            import uvicorn
            
            # Create FastAPI app
            self._app = FastAPI(
                title="QC Clean API",
                description="REST API for Grounded Theory analysis",
                version="1.0.0",
                docs_url="/docs" if self.config.get('enable_docs', True) else None
            )
            
            # Add CORS middleware
            self._app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.get('cors_origins', ["*"]),
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            # Add static file serving
            from fastapi.staticfiles import StaticFiles
            import os
            ui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "UI_planning", "mockups")
            if os.path.exists(ui_path):
                self._app.mount("/ui", StaticFiles(directory=ui_path), name="ui")
                self._logger.info(f"Static files mounted at /ui from {ui_path}")
            else:
                self._logger.warning(f"UI path not found: {ui_path}")
            
            # Register default endpoints
            self._register_default_endpoints()
            
            # Start server
            self._logger.info(f"Starting FastAPI server on {host}:{port}")
            
            try:
                # Create uvicorn server configuration
                config = uvicorn.Config(
                    app=self._app,
                    host=host,
                    port=port,
                    log_level="info",
                    access_log=True
                )
                server = uvicorn.Server(config)
                
                # Store server reference for shutdown
                self._server = server
                self.is_running = True
                
                # Start server (this will block until server stops)
                self._logger.info("HTTP server starting...")
                await server.serve()
                
                return True
                
            except ImportError:
                self._logger.error("uvicorn not available. Install with: pip install uvicorn")
                return False
            except Exception as e:
                self._logger.error(f"Failed to start HTTP server: {e}")
                return False
            
        except Exception as e:
            self._logger.error(f"Failed to start server: {e}")
            return False
    
    def stop_server(self) -> bool:
        """Stop the API server"""
        try:
            self._logger.info("Stopping API server...")
            
            if self._server:
                # Stop the actual server if running
                self._server.should_exit = True
                if hasattr(self._server, 'force_exit'):
                    self._server.force_exit = True
            
            self.is_running = False
            self._logger.info("API server stopped")
            return True
            
        except Exception as e:
            self._logger.error(f"Error stopping server: {e}")
            return False
    
    
    def _register_default_endpoints(self) -> None:
        """Register default API endpoints"""
        if not self._app:
            return
        
        from fastapi import HTTPException, BackgroundTasks
        from pydantic import BaseModel
        
        # Health check endpoint
        @self._app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "server_version": "1.0.0"
            }
        
        # Job submission model
        class AnalysisRequest(BaseModel):
            interviews: List[Dict[str, Any]]
            config: Optional[Dict[str, Any]] = {}
        
        # Analysis endpoint
        @self._app.post("/analyze")
        async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
            if not self.background_processing_enabled:
                raise HTTPException(status_code=503, detail="Background processing not enabled")
            
            # Create job ID
            job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Store job info
            self.active_jobs[job_id] = {
                "id": job_id,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "interviews_count": len(request.interviews),
                "config": request.config
            }
            
            # Add to background tasks (always run when background processing is enabled)
            if self.background_processing_enabled:
                background_tasks.add_task(
                    self._process_analysis,
                    job_id,
                    request.interviews,
                    request.config
                )
            
            return {
                "job_id": job_id,
                "status": "accepted",
                "message": "Analysis job queued for processing"
            }
        
        # Job status endpoint
        @self._app.get("/jobs/{job_id}")
        async def get_job_status(job_id: str):
            if job_id not in self.active_jobs:
                raise HTTPException(status_code=404, detail="Job not found")
            
            return self.active_jobs[job_id]
        
        # Results endpoint - get detailed analysis results
        @self._app.get("/results/{job_id}")
        async def get_analysis_results(job_id: str):
            if job_id not in self.active_jobs:
                raise HTTPException(status_code=404, detail="Job not found")
            
            job = self.active_jobs[job_id]
            if job["status"] != "completed":
                raise HTTPException(status_code=400, detail=f"Job status is {job['status']}, not completed")
            
            return {
                "job_id": job_id,
                "status": job["status"],
                "created_at": job["created_at"],
                "completed_at": job.get("completed_at"),
                "results": job.get("results", {})
            }
        
        # Register natural language query endpoints
        try:
            from .query_endpoints import query_endpoints
            query_endpoints.register_endpoints(self._app)
            self._logger.info("Natural language query endpoints registered successfully")
        except Exception as e:
            self._logger.error(f"Failed to register query endpoints: {e}")
        
        self.endpoints = [
            {"method": "GET", "path": "/health", "description": "Health check"},
            {"method": "POST", "path": "/analyze", "description": "Start analysis"},
            {"method": "POST", "path": "/api/query/natural-language", "description": "Natural language to Cypher query"},
            {"method": "GET", "path": "/api/query/health", "description": "Query system health check"},
            {"method": "GET", "path": "/jobs/{job_id}", "description": "Get job status"}
        ]
    
    async def _process_analysis(self, job_id: str, interviews: List[Dict[str, Any]], config: Dict[str, Any]):
        """Process qualitative coding analysis in background"""
        try:
            # Update job status
            self.active_jobs[job_id]["status"] = "processing"
            self.active_jobs[job_id]["started_at"] = datetime.now().isoformat()

            self._logger.info(f"Starting qualitative coding analysis for job {job_id} with {len(interviews)} interviews")

            import time
            import asyncio
            start_time = time.time()

            # Initialize LLM handler for analysis
            from qc_clean.core.llm.llm_handler import LLMHandler
            llm_handler = LLMHandler(model_name="gpt-5-mini")

            # Combine all interview content and detect issues
            combined_text = ""
            data_warnings = []
            for interview in interviews:
                content = interview.get('content', '')
                combined_text += f"--- Interview: {interview.get('name', 'Unknown')} ---\n"
                combined_text += content + "\n\n"
                # Detect truncated interviews
                stripped = content.rstrip()
                if stripped and not stripped[-1] in '.!?"\')':
                    data_warnings.append(f"Interview '{interview.get('name', 'Unknown')}' appears truncated (ends mid-sentence)")

            num_interviews = len(interviews)
            is_single_speaker = num_interviews == 1

            # COMPREHENSIVE MULTI-PHASE QUALITATIVE CODING ANALYSIS
            self._logger.info("Phase 1: Open Code Discovery - analyzing hierarchical themes")

            # Phase 1: Open Code Discovery
            phase1_prompt = f"""You are a qualitative researcher analyzing {num_interviews} interview(s) to discover thematic codes.

ANALYTIC QUESTION: What are the key themes, patterns, and insights in these interviews?

CRITICAL INSTRUCTIONS:
1. Read through ALL interview content comprehensively
2. Distinguish between INTERVIEWER QUESTIONS and INTERVIEWEE RESPONSES — only code the interviewee's statements, not the interviewer's framing questions
3. Create a hierarchical code structure with up to 3 levels
4. Target 10-15 total codes (5-7 top-level themes with selective sub-codes). Merge overlapping themes rather than creating near-duplicates
5. Each code MUST have these fields:
   - id: Unique ID in CAPS_WITH_UNDERSCORES format
   - name: Clear human-readable name
   - description: 2-3 sentences explaining the code
   - semantic_definition: Clear definition of what qualifies for this code
   - parent_id: ID of parent code (null for top-level codes)
   - level: Hierarchy level (0=top, 1=sub, 2=detailed)
   - example_quotes: 1-3 VERBATIM quotes from the INTERVIEWEE (not the interviewer)
   - mention_count: Count how many distinct times this theme is mentioned or referenced across the interview(s). Be precise — count actual mentions, not estimates
   - discovery_confidence: Float 0.0-1.0 using the FULL range:
     * 0.0-0.3: Weakly supported (mentioned once, tangentially)
     * 0.3-0.6: Moderately supported (mentioned a few times, some detail)
     * 0.6-0.8: Strongly supported (discussed substantively, with examples)
     * 0.8-1.0: Very strongly supported (major theme with extensive discussion)

6. Hierarchy: Level 0 = main themes, Level 1 = sub-themes, Level 2 = detailed codes
7. Codes must be mutually distinct — if two codes would share >50% of their supporting quotes, merge them

INTERVIEW CONTENT:
{combined_text}

Generate a complete hierarchical taxonomy of codes."""

            phase1_response = await llm_handler.extract_structured(phase1_prompt, CodeHierarchy)
            phase1_text = str(phase1_response.model_dump_json(indent=2))

            self._logger.info("Phase 2: Speaker/Participant Analysis - identifying perspectives")

            # Phase 2: Speaker Analysis — adapted for single vs multi speaker
            if is_single_speaker:
                phase2_prompt = f"""Analyze the single interview participant's perspective in depth.

CRITICAL: This is a SINGLE-SPEAKER interview. Do NOT fabricate consensus or disagreement between multiple people.

INSTRUCTIONS:
1. Identify the speaker by name and role from the interview content
2. Analyze their perspective in relation to the discovered codes
3. For "codes_emphasized": list ONLY the top 5-7 code IDs this speaker discusses MOST, not every code
4. For "consensus_themes": list the speaker's strongest, most consistent positions (things they state firmly and repeatedly)
5. For "divergent_viewpoints": identify any INTERNAL tensions, ambivalences, or contradictions within the speaker's OWN views (e.g., "sees AI as useful but worries about IP"). If there are none, return an empty list — do NOT fabricate tensions
6. For "perspective_mapping": map the speaker's name to their top 5-7 most emphasized code IDs

PHASE 1 CODES (for reference):
{phase1_text}

INTERVIEW CONTENT:
{combined_text}

Provide detailed single-speaker analysis."""
            else:
                phase2_prompt = f"""Analyze the different participant perspectives across {num_interviews} interviews.

INSTRUCTIONS:
1. Identify each distinct speaker by name and role
2. Analyze how different perspectives relate to the discovered codes
3. For "codes_emphasized": list ONLY the top 5-7 code IDs each speaker discusses MOST
4. For "consensus_themes": identify genuine areas where multiple speakers AGREE
5. For "divergent_viewpoints": identify genuine areas where speakers DISAGREE or hold different positions
6. For "perspective_mapping": map each speaker's name to their top 5-7 most emphasized code IDs

PHASE 1 CODES (for reference):
{phase1_text}

INTERVIEW CONTENT:
{combined_text}

Provide detailed multi-speaker analysis."""

            phase2_response = await llm_handler.extract_structured(phase2_prompt, SpeakerAnalysis)
            phase2_text = str(phase2_response.model_dump_json(indent=2))

            self._logger.info("Phase 3: Entity and Concept Analysis - mapping relationships")

            # Phase 3: Entity Analysis
            phase3_prompt = f"""Identify key entities, concepts, and their relationships in the interview data.

INSTRUCTIONS:
1. Extract important entities (organizations, tools, concepts, methods, people)
2. Map meaningful relationships — only include relationships that have clear evidence in the text
3. Identify cause-effect chains grounded in what the interviewee(s) actually said
4. Limit to 10-15 most important relationships, not an exhaustive list
5. Relationship types should be specific verbs (e.g., "leads", "uses", "constrains") not vague labels

PREVIOUS ANALYSIS:
Phase 1 Codes: {phase1_text}
Phase 2 Speakers: {phase2_text}

INTERVIEW CONTENT:
{combined_text}

Provide focused entity relationship mapping."""

            phase3_response = await llm_handler.extract_structured(phase3_prompt, EntityMapping)
            phase3_text = str(phase3_response.model_dump_json(indent=2))

            self._logger.info("Phase 4: Synthesis and Recommendations - final qualitative analysis")

            # Phase 4: Final Synthesis
            phase4_prompt = f"""Synthesize all analysis phases into a final qualitative coding report.

CRITICAL RULES:
- Do NOT invent statistics, percentages, or numeric estimates that are not directly stated in the interviews
- Do NOT use language like "~70% prevalence" or "estimated frequency: 80%" — these are fabricated
- Instead, use qualitative descriptors: "frequently discussed", "mentioned once", "a major theme", "briefly touched on"
- The executive_summary should be 2-4 sentences, not a full paragraph
- Key findings should cite specific evidence from interviews
- Recommendations should be specific to the interview content, not generic consulting advice

COMPREHENSIVE ANALYSIS FROM PREVIOUS PHASES:
Phase 1 - Hierarchical Codes: {phase1_text}
Phase 2 - Speaker Analysis: {phase2_text}
Phase 3 - Entity Relationships: {phase3_text}

ORIGINAL INTERVIEW CONTENT:
{combined_text}

Provide final qualitative coding analysis with:
- Executive summary (2-4 sentences)
- Key findings with VERBATIM evidence (no fabricated statistics)
- Cross-cutting patterns
- Specific, actionable recommendations grounded in interview content
- Honest confidence assessments using the full 0.0-1.0 range"""

            phase4_response = await llm_handler.extract_structured(phase4_prompt, AnalysisSynthesis)
            analysis_text = str(phase4_response.model_dump_json(indent=2))

            # Combine all phases for complete analysis
            full_analysis = f"""=== COMPREHENSIVE QUALITATIVE CODING ANALYSIS ===

PHASE 1: HIERARCHICAL CODE DISCOVERY
{phase1_text}

PHASE 2: {"SINGLE-SPEAKER" if is_single_speaker else "MULTI-SPEAKER"} PERSPECTIVE ANALYSIS
{phase2_text}

PHASE 3: ENTITY AND RELATIONSHIP MAPPING
{phase3_text}

PHASE 4: SYNTHESIS AND FINAL ANALYSIS
{analysis_text}

=== END OF ANALYSIS ==="""

            # Create structured results from schema objects
            # Use actual code count, not model's self-reported total_codes
            actual_code_count = len(phase1_response.codes)

            codes_identified = [
                {
                    "code": code.name,
                    "mention_count": code.mention_count,
                    "confidence": code.discovery_confidence
                } for code in phase1_response.codes
            ]

            speakers_identified = [
                {
                    "name": participant.name,
                    "role": participant.role,
                    "perspective": participant.perspective_summary
                } for participant in phase2_response.participants
            ]

            key_relationships = [
                {
                    "entities": f"{rel.entity_1} -> {rel.entity_2}",
                    "type": rel.relationship_type,
                    "strength": rel.strength
                } for rel in phase3_response.relationships
            ]

            recommendations = [
                {
                    "title": rec.title,
                    "description": rec.description,
                    "priority": rec.priority
                } for rec in phase4_response.actionable_recommendations
            ]

            key_themes = phase4_response.key_findings

            processing_time = time.time() - start_time

            # Create structured analysis results
            structured_results = {
                "analysis_summary": f"Analyzed {num_interviews} interview(s) using structured qualitative coding",
                "total_interviews": num_interviews,
                "total_codes": actual_code_count,
                "single_speaker_mode": is_single_speaker,
                "codes_identified": codes_identified,
                "speakers_identified": speakers_identified,
                "key_relationships": key_relationships,
                "key_themes": key_themes,
                "recommendations": recommendations,
                "full_analysis": full_analysis,
                "processing_time_seconds": round(processing_time, 2),
                "model_used": llm_handler.model_name,
            }

            if data_warnings:
                structured_results["data_warnings"] = data_warnings

            # Update job with success
            self.active_jobs[job_id]["status"] = "completed"
            self.active_jobs[job_id]["results"] = structured_results
            self.active_jobs[job_id]["completed_at"] = datetime.now().isoformat()

            self._logger.info(f"Comprehensive 4-phase qualitative coding analysis completed successfully for job {job_id}")

        except Exception as e:
            # Update job with error
            self.active_jobs[job_id]["status"] = "failed"
            self.active_jobs[job_id]["error"] = str(e)
            self._logger.error(f"Analysis job {job_id} failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status"""
        return {
            "initialized": True,
            "running": self.is_running,
            "host": self.config.get('host', 'localhost'),
            "port": self.config.get('port', 8000),
            "background_processing": self.background_processing_enabled,
            "active_jobs": len(self.active_jobs),
            "endpoints_registered": len(self.endpoints)
        }
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """Get list of registered endpoints"""
        return self.endpoints.copy()
    
    def cleanup(self) -> None:
        """Cleanup server resources"""
        self._logger.info("Cleaning up API server resources...")
        
        # Clear job tracking
        self.active_jobs.clear()
        
        # Clear endpoints
        self.endpoints.clear()
        
        self._app = None
        self._server = None
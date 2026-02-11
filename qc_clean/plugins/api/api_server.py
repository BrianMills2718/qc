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
        
        # ----- Review endpoints -----
        @self._app.get("/projects/{project_id}/review")
        async def get_review_items(project_id: str):
            """Get pending review items for a project."""
            from qc_clean.core.persistence.project_store import ProjectStore
            from qc_clean.core.pipeline.review import ReviewManager
            store = ProjectStore()
            try:
                state = store.load(project_id)
            except FileNotFoundError:
                return {"error": f"Project not found: {project_id}"}
            rm = ReviewManager(state)
            return rm.get_review_summary()

        @self._app.post("/projects/{project_id}/review")
        async def submit_review_decisions(project_id: str, body: Dict):
            """Submit review decisions for a project."""
            from qc_clean.core.persistence.project_store import ProjectStore
            from qc_clean.core.pipeline.review import ReviewManager
            from qc_clean.schemas.domain import HumanReviewDecision, ReviewAction
            store = ProjectStore()
            try:
                state = store.load(project_id)
            except FileNotFoundError:
                return {"error": f"Project not found: {project_id}"}
            rm = ReviewManager(state)
            decisions = []
            for d in body.get("decisions", []):
                decisions.append(HumanReviewDecision(
                    target_type=d["target_type"],
                    target_id=d["target_id"],
                    action=ReviewAction(d["action"]),
                    rationale=d.get("rationale", ""),
                    new_value=d.get("new_value"),
                ))
            result = rm.apply_decisions(decisions)
            store.save(state)
            return result

        @self._app.post("/projects/{project_id}/resume")
        async def resume_pipeline(project_id: str):
            """Resume pipeline after human review."""
            from qc_clean.core.persistence.project_store import ProjectStore
            from qc_clean.core.pipeline.review import ReviewManager
            store = ProjectStore()
            try:
                state = store.load(project_id)
            except FileNotFoundError:
                return {"error": f"Project not found: {project_id}"}
            rm = ReviewManager(state)
            if not rm.can_resume():
                return {"error": "Pipeline is not paused for review"}
            resume_from = rm.prepare_for_resume()
            store.save(state)
            return {"resumed_from": resume_from, "status": "running"}

        self.endpoints = [
            {"method": "GET", "path": "/health", "description": "Health check"},
            {"method": "POST", "path": "/analyze", "description": "Start analysis"},
            {"method": "POST", "path": "/api/query/natural-language", "description": "Natural language to Cypher query"},
            {"method": "GET", "path": "/api/query/health", "description": "Query system health check"},
            {"method": "GET", "path": "/jobs/{job_id}", "description": "Get job status"},
            {"method": "GET", "path": "/projects/{project_id}/review", "description": "Get review items"},
            {"method": "POST", "path": "/projects/{project_id}/review", "description": "Submit review decisions"},
            {"method": "POST", "path": "/projects/{project_id}/resume", "description": "Resume pipeline after review"},
        ]
    
    async def _process_analysis(self, job_id: str, interviews: List[Dict[str, Any]], config: Dict[str, Any]):
        """Process qualitative coding analysis via the stage-based pipeline."""
        try:
            # Update job status
            self.active_jobs[job_id]["status"] = "processing"
            self.active_jobs[job_id]["started_at"] = datetime.now().isoformat()

            self._logger.info(f"Starting qualitative coding analysis for job {job_id} with {len(interviews)} interviews")

            import time
            start_time = time.time()

            # Run the pipeline
            from qc_clean.core.pipeline.pipeline_factory import create_pipeline
            from qc_clean.schemas.domain import ProjectState

            methodology = config.get("methodology", "default")
            model_name = config.get("model_name", "gpt-5-mini")

            pipeline = create_pipeline(methodology=methodology)
            state = ProjectState(name=f"job_{job_id}")

            pipeline_config = {
                "interviews": interviews,
                "model_name": model_name,
            }

            state = await pipeline.run(state, pipeline_config)

            # Build structured results from ProjectState (backward-compatible format)
            num_interviews = state.corpus.num_documents
            is_single_speaker = num_interviews == 1

            codes_identified = [
                {
                    "code": code.name,
                    "mention_count": code.mention_count,
                    "confidence": code.confidence,
                } for code in state.codebook.codes
            ]

            speakers_identified = []
            if state.perspective_analysis:
                speakers_identified = [
                    {
                        "name": p.name,
                        "role": p.role,
                        "perspective": p.perspective_summary,
                    } for p in state.perspective_analysis.participants
                ]

            key_relationships = [
                {
                    "entities": f"{ent_rel.entity_1_id} -> {ent_rel.entity_2_id}",
                    "type": ent_rel.relationship_type,
                    "strength": ent_rel.strength,
                } for ent_rel in state.entity_relationships
            ]

            recommendations = []
            key_themes = []
            if state.synthesis:
                recommendations = [
                    {
                        "title": rec.title,
                        "description": rec.description,
                        "priority": rec.priority,
                    } for rec in state.synthesis.recommendations
                ]
                key_themes = state.synthesis.key_findings

            processing_time = time.time() - start_time

            structured_results = {
                "analysis_summary": f"Analyzed {num_interviews} interview(s) using structured qualitative coding",
                "total_interviews": num_interviews,
                "total_codes": len(state.codebook.codes),
                "single_speaker_mode": is_single_speaker,
                "codes_identified": codes_identified,
                "speakers_identified": speakers_identified,
                "key_relationships": key_relationships,
                "key_themes": key_themes,
                "recommendations": recommendations,
                "processing_time_seconds": round(processing_time, 2),
                "model_used": model_name,
            }

            if state.data_warnings:
                structured_results["data_warnings"] = state.data_warnings

            # Update job with success
            self.active_jobs[job_id]["status"] = "completed"
            self.active_jobs[job_id]["results"] = structured_results
            self.active_jobs[job_id]["completed_at"] = datetime.now().isoformat()

            self._logger.info(f"Pipeline analysis completed successfully for job {job_id}")

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
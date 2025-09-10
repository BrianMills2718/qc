"""
WebSocket endpoint for real-time analysis progress updates
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AnalysisPhase(Enum):
    """Phases of Grounded Theory analysis"""
    INITIALIZATION = "initialization"
    OPEN_CODING = "open_coding"
    AXIAL_CODING = "axial_coding"
    SELECTIVE_CODING = "selective_coding"
    THEORY_INTEGRATION = "theory_integration"
    REPORT_GENERATION = "report_generation"
    COMPLETE = "complete"
    ERROR = "error"
    PAUSED = "paused"


class ProgressUpdate(BaseModel):
    """Progress update message structure"""
    phase: str
    progress: float  # 0.0 to 1.0
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str
    can_pause: bool = True
    can_view_partial: bool = False


class AnalysisSession:
    """Manages a single analysis session with pause/resume capability"""
    
    def __init__(self, session_id: str, interviews: list, config: dict):
        self.session_id = session_id
        self.interviews = interviews
        self.config = config
        self.current_phase = AnalysisPhase.INITIALIZATION
        self.progress = 0.0
        self.is_paused = False
        self.partial_results = {}
        self.error_count = 0
        self.max_retries = 3
        self.websocket: Optional[WebSocket] = None
        
    async def send_update(self, message: str, details: dict = None):
        """Send progress update to connected client"""
        if self.websocket:
            try:
                update = ProgressUpdate(
                    phase=self.current_phase.value,
                    progress=self.progress,
                    message=message,
                    details=details,
                    timestamp=datetime.now().isoformat(),
                    can_pause=self.current_phase not in [AnalysisPhase.COMPLETE, AnalysisPhase.ERROR],
                    can_view_partial=bool(self.partial_results)
                )
                await self.websocket.send_json(update.dict())
            except Exception as e:
                logger.error(f"Failed to send update: {e}")
    
    async def run_analysis(self):
        """Run the complete analysis with progress updates"""
        try:
            # Phase 1: Initialization
            self.current_phase = AnalysisPhase.INITIALIZATION
            self.progress = 0.1
            await self.send_update(
                "Initializing analysis system...",
                {"interviews_count": len(self.interviews)}
            )
            await self.check_pause()
            
            # Phase 2: Open Coding
            self.current_phase = AnalysisPhase.OPEN_CODING
            await self.run_open_coding()
            
            # Phase 3: Axial Coding
            self.current_phase = AnalysisPhase.AXIAL_CODING
            await self.run_axial_coding()
            
            # Phase 4: Selective Coding
            self.current_phase = AnalysisPhase.SELECTIVE_CODING
            await self.run_selective_coding()
            
            # Phase 5: Theory Integration
            self.current_phase = AnalysisPhase.THEORY_INTEGRATION
            await self.run_theory_integration()
            
            # Phase 6: Report Generation
            self.current_phase = AnalysisPhase.REPORT_GENERATION
            await self.generate_report()
            
            # Complete
            self.current_phase = AnalysisPhase.COMPLETE
            self.progress = 1.0
            await self.send_update("Analysis complete!", {"status": "success"})
            
        except Exception as e:
            await self.handle_error(e)
    
    async def run_open_coding(self):
        """Run open coding phase with live updates"""
        codes_found = []
        total_interviews = len(self.interviews)
        
        for i, interview in enumerate(self.interviews):
            await self.check_pause()
            
            # Update progress
            phase_progress = (i + 1) / total_interviews
            self.progress = 0.1 + (0.3 * phase_progress)  # 10% to 40% total
            
            await self.send_update(
                f"Processing interview {i+1}/{total_interviews}...",
                {
                    "current_interview": i + 1,
                    "codes_so_far": len(codes_found),
                    "interview_id": interview.get("id", f"Interview_{i+1}")
                }
            )
            
            try:
                # Simulate processing (would be actual GT workflow call)
                await asyncio.sleep(2)  # Replace with actual processing
                
                # Add discovered codes
                new_codes = ["code1", "code2", "code3"]  # Replace with actual codes
                codes_found.extend(new_codes)
                
                # Store partial results
                self.partial_results[f"open_coding_interview_{i}"] = new_codes
                
                # Send live update about new codes
                await self.send_update(
                    f"Found {len(new_codes)} new codes",
                    {
                        "new_codes": new_codes[:5],  # Show first 5
                        "total_codes": len(codes_found)
                    }
                )
                
            except Exception as e:
                # Handle errors with retry
                if self.error_count < self.max_retries:
                    self.error_count += 1
                    await self.send_update(
                        f"Error processing interview {i+1}, retrying... ({self.error_count}/{self.max_retries})",
                        {"error": str(e)}
                    )
                    await asyncio.sleep(2)  # Wait before retry
                    # Retry logic here
                else:
                    raise
        
        # Phase complete
        self.partial_results["open_codes"] = codes_found
        await self.send_update(
            f"Open coding complete: {len(codes_found)} codes discovered",
            {"codes_count": len(codes_found), "codes_sample": codes_found[:10]}
        )
    
    async def run_axial_coding(self):
        """Run axial coding phase"""
        await self.check_pause()
        self.progress = 0.5
        
        await self.send_update(
            "Finding relationships between codes...",
            {"codes_count": len(self.partial_results.get("open_codes", []))}
        )
        
        # Simulate processing
        await asyncio.sleep(3)
        
        # Store results
        categories = ["Category1", "Category2"]  # Replace with actual
        self.partial_results["categories"] = categories
        
        self.progress = 0.6
        await self.send_update(
            f"Identified {len(categories)} categories",
            {"categories": categories}
        )
    
    async def run_selective_coding(self):
        """Run selective coding phase"""
        await self.check_pause()
        self.progress = 0.7
        
        await self.send_update("Identifying core category...")
        
        # Simulate processing
        await asyncio.sleep(2)
        
        self.partial_results["core_category"] = "Central Phenomenon"
        
        self.progress = 0.8
        await self.send_update(
            "Core category identified",
            {"core_category": self.partial_results["core_category"]}
        )
    
    async def run_theory_integration(self):
        """Run theory integration phase"""
        await self.check_pause()
        self.progress = 0.85
        
        await self.send_update("Building theoretical model...")
        
        # Simulate processing
        await asyncio.sleep(2)
        
        self.partial_results["theory"] = {
            "name": "Emergent Theory",
            "description": "Theory description"
        }
        
        self.progress = 0.9
        await self.send_update("Theoretical model complete")
    
    async def generate_report(self):
        """Generate final report"""
        await self.check_pause()
        self.progress = 0.95
        
        await self.send_update("Generating report...")
        
        # Simulate processing
        await asyncio.sleep(1)
        
        self.partial_results["report_path"] = "/reports/analysis_complete.pdf"
    
    async def check_pause(self):
        """Check if analysis should pause"""
        while self.is_paused:
            await self.send_update("Analysis paused", {"paused": True})
            await asyncio.sleep(1)
    
    def pause(self):
        """Pause the analysis"""
        self.is_paused = True
        logger.info(f"Analysis {self.session_id} paused")
    
    def resume(self):
        """Resume the analysis"""
        self.is_paused = False
        logger.info(f"Analysis {self.session_id} resumed")
    
    async def handle_error(self, error: Exception):
        """Handle analysis errors"""
        self.current_phase = AnalysisPhase.ERROR
        error_msg = str(error)
        
        await self.send_update(
            f"Analysis failed: {error_msg}",
            {
                "error": error_msg,
                "phase_failed": self.current_phase.value,
                "partial_results_available": bool(self.partial_results)
            }
        )
        
        logger.error(f"Analysis {self.session_id} failed: {error}")


# Global session storage (in production, use Redis or database)
active_sessions: Dict[str, AnalysisSession] = {}


async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time progress updates
    
    Client connects and sends commands:
    - {"command": "start", "interviews": [...], "config": {...}}
    - {"command": "pause"}
    - {"command": "resume"}
    - {"command": "get_partial"}
    - {"command": "cancel"}
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive command from client
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "start":
                # Create new analysis session
                session = AnalysisSession(
                    session_id=session_id,
                    interviews=data.get("interviews", []),
                    config=data.get("config", {})
                )
                session.websocket = websocket
                active_sessions[session_id] = session
                
                # Start analysis in background
                asyncio.create_task(session.run_analysis())
                
            elif command == "pause":
                if session_id in active_sessions:
                    active_sessions[session_id].pause()
                    
            elif command == "resume":
                if session_id in active_sessions:
                    active_sessions[session_id].resume()
                    
            elif command == "get_partial":
                if session_id in active_sessions:
                    await websocket.send_json({
                        "type": "partial_results",
                        "data": active_sessions[session_id].partial_results
                    })
                    
            elif command == "cancel":
                if session_id in active_sessions:
                    # Clean up session
                    del active_sessions[session_id]
                    await websocket.close()
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        # Keep session alive for reconnection
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
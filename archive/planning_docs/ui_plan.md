# UI Development Plan for LLM-Native Grounded Theory

## Overview
This document outlines the development methodology to ensure seamless UI integration for the LLM-Native Grounded Theory system. By following these patterns from the start, we can build any UI (React, Streamlit, Jupyter) on top of the same backend without refactoring.

## Development Methodology for Seamless UI Integration

### 🎯 API-First Development Pattern

Build the core as if it's already serving a UI from day one:

```python
# Every core function returns UI-friendly data structures
class GroundedTheoryIterator:
    async def run_analysis(self) -> AnalysisResult:
        """Returns everything UI needs"""
        return AnalysisResult(
            status="in_progress",
            current_iteration=3,
            current_phase="axial_coding",
            progress_percentage=45,
            estimated_time_remaining=1200,  # seconds
            can_preview=True,
            preview_data={...},
            websocket_events=["iteration_complete", "phase_change"]
        )
```

### 📋 Event-Driven Architecture

Design for real-time UI updates from the start:

```python
# event_bus.py
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, List

class EventType(Enum):
    # Analysis Events
    ANALYSIS_STARTED = "analysis_started"
    ITERATION_STARTED = "iteration_started"
    ITERATION_COMPLETE = "iteration_complete"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETE = "phase_complete"
    SATURATION_UPDATE = "saturation_update"
    
    # Code Events
    CODE_DISCOVERED = "code_discovered"
    CODE_APPLIED = "code_applied"
    CATEGORY_FORMED = "category_formed"
    
    # Model Events
    MODEL_QUERY_STARTED = "model_query_started"
    MODEL_QUERY_COMPLETE = "model_query_complete"
    CONSENSUS_ACHIEVED = "consensus_achieved"

@dataclass
class Event:
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    correlation_id: str

class EventBus:
    """Central event system for UI updates"""
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        
    def emit(self, event: Event):
        """Emit event to all subscribers"""
        for subscriber in self._subscribers.get(event.type, []):
            subscriber(event)
            
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to events (UI will use this)"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
```

### 🧪 LLM-Aware Test-Driven Development

Traditional TDD doesn't work with non-deterministic LLMs. Here's our approach:

```python
# tests/test_patterns.py

class LLMTestPattern:
    """Base pattern for testing LLM functionality"""
    
    @pytest.fixture
    def mock_llm_response(self):
        """Fixture that provides realistic LLM responses"""
        return {
            "speaker_attribution": {
                "speaker": "Participant_1",
                "confidence": 0.85,
                "evidence": ["uses technical terms", "mentions 'my team'"]
            }
        }
    
    def test_contract_not_implementation(self):
        """Test the contract, not exact output"""
        result = await analyzer.identify_speaker(text)
        
        # Don't test exact values, test structure and ranges
        assert "speaker" in result
        assert 0.0 <= result["confidence"] <= 1.0
        assert isinstance(result["evidence"], list)
        assert len(result["evidence"]) > 0

class IntegrationTestPattern:
    """Test with real LLMs in CI/CD"""
    
    @pytest.mark.integration
    @pytest.mark.costly  # Run less frequently
    async def test_real_speaker_attribution(self):
        """Test with actual LLM calls"""
        result = await analyzer.identify_speaker(
            "As the CEO, I think we need to pivot our strategy..."
        )
        
        # Test semantic correctness
        assert "ceo" in result["speaker"].lower() or \
               result["evidence"] contains executive indicators
```

### 📦 Repository Pattern for UI Decoupling

Separate data access from business logic:

```python
# repositories/analysis_repository.py
from abc import ABC, abstractmethod

class AnalysisRepository(ABC):
    """Abstract interface for data storage"""
    
    @abstractmethod
    async def save_iteration(self, iteration: IterationResult) -> str:
        pass
    
    @abstractmethod
    async def get_analysis_history(self, project_id: str) -> List[IterationResult]:
        pass
    
    @abstractmethod
    async def get_current_state(self, project_id: str) -> AnalysisState:
        pass

class InMemoryAnalysisRepository(AnalysisRepository):
    """For testing and development"""
    
    def __init__(self):
        self._data = {}
    
    async def save_iteration(self, iteration: IterationResult) -> str:
        iteration_id = str(uuid.uuid4())
        self._data[iteration_id] = iteration
        return iteration_id

class PostgresAnalysisRepository(AnalysisRepository):
    """For production with UI"""
    
    async def save_iteration(self, iteration: IterationResult) -> str:
        async with self.db.acquire() as conn:
            result = await conn.fetchrow(
                "INSERT INTO iterations (...) VALUES (...) RETURNING id",
                iteration.dict()
            )
            return result["id"]
```

### 🎨 UI-Ready Data Models

Design data models that serialize nicely for UI:

```python
# models/ui_models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class UISerializable(BaseModel):
    """Base class for UI-friendly models"""
    
    class Config:
        # Ensure JSON serialization works
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    
    def to_ui_dict(self) -> Dict:
        """Convert to UI-friendly dictionary"""
        data = self.dict()
        # Add UI-specific fields
        data["_display_name"] = self.get_display_name()
        data["_icon"] = self.get_icon()
        data["_color"] = self.get_color()
        return data

class CodeApplicationUI(UISerializable):
    """Code application with UI metadata"""
    code_id: str
    code: str
    quote: str
    speaker: SpeakerUI
    location: str
    justification: str
    
    # UI-specific fields
    highlight_color: str = Field(default="yellow")
    is_selected: bool = Field(default=False)
    show_justification: bool = Field(default=False)
    
    def get_display_name(self) -> str:
        return f"{self.code} ({self.speaker.identifier})"
    
    def get_icon(self) -> str:
        return "🏷️"
```

### 🔌 Plugin Architecture for UI Features

Make features pluggable so UI can enable/disable:

```python
# plugins/base.py
class AnalysisPlugin(ABC):
    """Base class for analysis plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def ui_config(self) -> Dict:
        """UI configuration for this plugin"""
        pass
    
    @abstractmethod
    async def process(self, data: Any) -> Any:
        pass

# plugins/sentiment_analysis.py
class SentimentAnalysisPlugin(AnalysisPlugin):
    name = "sentiment_analysis"
    
    @property
    def ui_config(self):
        return {
            "display_name": "Sentiment Analysis",
            "icon": "😊",
            "color": "blue",
            "settings": {
                "enabled": {"type": "boolean", "default": True},
                "granularity": {
                    "type": "select",
                    "options": ["segment", "document", "project"],
                    "default": "segment"
                }
            }
        }
    
    async def process(self, segment: Segment) -> SentimentResult:
        # Implementation
        pass
```

### 📊 Streaming Results Pattern

Enable progressive UI updates:

```python
# streaming/analysis_stream.py
from typing import AsyncIterator

class AnalysisStreamer:
    """Stream analysis results as they're generated"""
    
    async def stream_analysis(
        self, 
        project_id: str
    ) -> AsyncIterator[AnalysisUpdate]:
        """Yield updates as analysis progresses"""
        
        async for event in self.event_bus.stream():
            if event.type == EventType.CODE_DISCOVERED:
                yield CodeUpdate(
                    type="code_discovered",
                    code=event.data["code"],
                    count=event.data["count"],
                    examples=event.data["examples"][:3]  # UI preview
                )
            
            elif event.type == EventType.SATURATION_UPDATE:
                yield SaturationUpdate(
                    type="saturation_update",
                    metrics=event.data["metrics"],
                    recommendation=event.data["recommendation"],
                    visualization_data=self._prepare_chart_data(event.data)
                )
```

### 🧪 Development Workflow

1. **Write UI Contract First**
```python
# contracts/analysis_contract.py
class AnalysisContract:
    """Contract between backend and UI"""
    
    @staticmethod
    def start_analysis_request():
        return {
            "project_id": str,
            "research_question": str,
            "options": {
                "max_iterations": int,
                "saturation_threshold": float,
                "plugins": List[str]
            }
        }
    
    @staticmethod
    def analysis_status_response():
        return {
            "status": Enum["queued", "running", "complete", "failed"],
            "progress": float,  # 0.0 to 1.0
            "current_action": str,
            "preview_available": bool,
            "estimated_completion": datetime
        }
```

2. **Implement with Mocked LLMs**
```python
# Use dependency injection
class GroundedTheoryIterator:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or MockLLMClient()
```

3. **Test UI Integration Points**
```python
@pytest.mark.asyncio
async def test_websocket_events_emitted():
    """Ensure UI receives expected events"""
    events_received = []
    
    def capture_event(event):
        events_received.append(event.type)
    
    event_bus.subscribe(EventType.ITERATION_COMPLETE, capture_event)
    
    await analyzer.run_iteration()
    
    assert EventType.ITERATION_COMPLETE in events_received
```

### 📐 Architecture Rules for UI-Ready Code

1. **No Blocking Operations**
   ```python
   # Bad
   def analyze(self):
       time.sleep(10)  # Blocks UI
   
   # Good  
   async def analyze(self):
       await asyncio.sleep(10)  # Non-blocking
   ```

2. **Progress Reporting Built-In**
   ```python
   async def process_documents(self, docs: List[Document]):
       total = len(docs)
       for i, doc in enumerate(docs):
           await self.process_one(doc)
           await self.emit_progress(i / total)
   ```

3. **Cancellable Operations**
   ```python
   class CancellableAnalysis:
       def __init__(self):
           self._cancelled = False
       
       async def analyze(self):
           for iteration in range(10):
               if self._cancelled:
                   raise AnalysisCancelled()
               await self.run_iteration()
       
       def cancel(self):
           self._cancelled = True
   ```

## UI Technology Options

### Option 1: Streamlit (Quick Prototype)
```python
import streamlit as st
import asyncio

# Main app
st.set_page_config(page_title="LLM-Native GT", layout="wide")

# Sidebar for project management
with st.sidebar:
    st.header("🗂️ Project")
    project_name = st.text_input("Project Name")
    uploaded_files = st.file_uploader("Upload Transcripts", 
                                    accept_multiple_files=True)
    research_question = st.text_area("Research Question")
    
    if st.button("🚀 Start Analysis"):
        asyncio.run(analyze_transcripts())

# Main area with tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "👥 Speakers", 
                                       "📝 Codes", "🔍 Theory", "📈 Progress"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Transcripts", "6")
    col2.metric("Codes", "47") 
    col3.metric("Saturation", "86%")
    
    # Real-time consensus view
    st.subheader("🤖 Multi-Model Consensus")
    consensus_df = st.dataframe(consensus_data, use_container_width=True)
```

### Option 2: React + FastAPI (Production Multi-User)

**Frontend Structure:**
```jsx
// App.jsx - Main Application Shell
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects" element={<ProjectList />} />
          <Route path="/project/:id" element={<ProjectAnalysis />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </div>
    </Router>
  );
}
```

**Backend Structure:**
```python
# main.py
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Project endpoints
@app.post("/api/projects")
async def create_project(project: ProjectCreate, user=Depends(get_current_user)):
    """Create new analysis project"""
    project_id = await create_project_in_db(project, user.id)
    return {"id": project_id}

@app.post("/api/projects/{project_id}/analyze")
async def start_analysis(project_id: str, user=Depends(get_current_user)):
    """Start grounded theory analysis"""
    # Queue analysis job
    await analysis_queue.put({
        "project_id": project_id,
        "user_id": user.id
    })
    return {"status": "queued"}

# WebSocket for real-time updates
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await websocket.accept()
    
    # Send updates as analysis progresses
    async for update in analysis_updates(project_id):
        await websocket.send_json(update)
```

### Option 3: Jupyter Notebook (Research-Friendly)
```python
# Cell 1: Setup
from interview31 import GroundedTheoryAnalyzer
analyzer = GroundedTheoryAnalyzer(research_question="...")

# Cell 2: Load and explore data
transcripts = analyzer.load_transcripts("./interviews/")
analyzer.explore_speakers()

# Cell 3: Run analysis with live updates
await analyzer.run_analysis()
# Shows progress bars, interim results

# Cell 4: Interactive exploration
analyzer.explore_codes(iteration=3)
# Interactive widgets for filtering, searching

# Cell 5: Theory visualization
analyzer.visualize_theory()
# D3.js powered interactive diagram
```

## Deployment Architecture

### Multi-User Think Tank Setup
```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   Auth      │  │   Projects   │  │   Analysis     │ │
│  │   Login     │  │   List/CRUD  │  │   Dashboard    │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │ WebSocket + REST API
┌────────────────────────┴────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │Auth/Sessions│  │ Project API  │  │ Analysis API   │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐│
│  │          GroundedTheoryIterator (Core)              ││
│  └─────────────────────────────────────────────────────┘│
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│   PostgreSQL            │        Redis                  │
│   - Projects            │        - Sessions             │
│   - Users               │        - Analysis Queue       │
│   - Results             │        - Progress Updates     │
└─────────────────────────┴────────────────────────────────┘
```

### Deployment Options

1. **Frontend (Vercel - Free)**
```bash
# Build React app
npm run build

# Deploy to Vercel
vercel --prod
```

2. **Backend (Railway - ~$10/month)**
```yaml
# railway.toml
[build]
builder = "DOCKERFILE"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"

[service]
internalPort = 8000
```

3. **Database (Railway PostgreSQL - ~$5/month)**
- Automatic backups
- SSL connections
- Easy scaling

## Key UI Features to Include

1. **Multi-Model Consensus View**
   - Show all 3 models' analyses side-by-side
   - Highlight agreements/disagreements
   - Confidence scores for each

2. **Inline Code Visualization**
   - Show QCoder-style markup in context
   - Click to see justification
   - Speaker attribution confidence

3. **Theory Evolution Timeline**
   - Scrubber to see how theory developed
   - What changed each iteration
   - Saturation progression

4. **Interactive Code Hierarchy**
   - Sunburst or tree diagram
   - Drag to reorganize
   - See example quotes on hover

5. **Real-time Progress**
   - Current iteration status
   - What's being analyzed now
   - ETA to completion

## Benefits of This Approach

1. **UI Can Be Built Independently** - Clear contracts
2. **Real-Time Updates** - Event system from day one  
3. **Testing Without LLMs** - Mock implementations
4. **Multiple UI Options** - Same backend, different frontends
5. **Progressive Enhancement** - Add features without breaking UI

## Implementation Timeline

1. **Phase 1**: Build core with UI contracts (Current)
2. **Phase 2**: Add event system and streaming
3. **Phase 3**: Create API endpoints
4. **Phase 4**: Build chosen UI (Streamlit → React)
5. **Phase 5**: Deploy for think tank use
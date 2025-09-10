# UI Implementation Plan - Practical Next Steps

## Immediate Action Items (Week 1)

### 1. Set Up Development Environment

```bash
# Create React app with TypeScript
npx create-react-app qualitative-coding-ui --template typescript
cd qualitative-coding-ui

# Install core dependencies
npm install axios react-router-dom 
npm install @ant-design/icons antd
npm install d3 @types/d3
npm install socket.io-client

# Development tools
npm install -D @types/react-router-dom
```

### 2. Create FastAPI Backend Wrapper

```python
# backend/main.py
from fastapi import FastAPI, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from src.qc.core.robust_cli_operations import RobustCLIOperations
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
import asyncio
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/projects")
async def create_project(name: str, description: str):
    """Create new analysis project"""
    # Implementation here
    
@app.post("/api/projects/{project_id}/interviews")
async def upload_interviews(project_id: str, files: List[UploadFile]):
    """Upload interview files"""
    # Implementation here
    
@app.post("/api/projects/{project_id}/analyze")
async def start_analysis(project_id: str, config: dict):
    """Start GT analysis"""
    # Implementation here
    
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket for real-time updates"""
    await websocket.accept()
    # Stream analysis progress
```

### 3. Create Basic React Components

```typescript
// src/components/ProjectDashboard.tsx
import React, { useEffect, useState } from 'react';
import { Card, Button, Row, Col } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

interface Project {
  id: string;
  name: string;
  created: string;
  status: string;
}

export const ProjectDashboard: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  
  return (
    <div>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Button 
              type="dashed" 
              icon={<PlusOutlined />}
              block
              style={{ height: 150 }}
            >
              New Project
            </Button>
          </Card>
        </Col>
        {projects.map(project => (
          <Col span={6} key={project.id}>
            <Card title={project.name}>
              {/* Project details */}
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};
```

## MVP Feature Set (Weeks 1-2)

### Essential Features Only

1. **Project Management**
   - Create project
   - Upload interviews (drag & drop)
   - List projects

2. **Analysis Execution**
   - Start analysis with default settings
   - Show progress bar
   - Display completion status

3. **Basic Results View**
   - List of codes with frequencies
   - List of quotes
   - Download JSON results

### File Structure

```
qualitative-coding-ui/
├── src/
│   ├── components/
│   │   ├── ProjectDashboard.tsx
│   │   ├── FileUpload.tsx
│   │   ├── AnalysisProgress.tsx
│   │   └── ResultsTable.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── websocket.ts
│   ├── types/
│   │   └── index.ts
│   └── App.tsx
└── package.json

backend/
├── main.py
├── routers/
│   ├── projects.py
│   ├── analysis.py
│   └── results.py
└── requirements.txt
```

## Week 2: Graph Visualization POC

### 1. Install Cytoscape.js (Easier than D3 for graphs)

```bash
npm install cytoscape cytoscape-fcose
npm install @types/cytoscape
```

### 2. Create Basic Graph Component

```typescript
// src/components/GraphVisualization.tsx
import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import fcose from 'cytoscape-fcose';

cytoscape.use(fcose);

interface GraphData {
  nodes: Array<{id: string, label: string, type: string}>;
  edges: Array<{source: string, target: string, weight: number}>;
}

export const GraphVisualization: React.FC<{data: GraphData}> = ({data}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!containerRef.current) return;
    
    const cy = cytoscape({
      container: containerRef.current,
      elements: [
        ...data.nodes.map(n => ({
          data: { id: n.id, label: n.label },
          classes: n.type
        })),
        ...data.edges.map(e => ({
          data: { 
            source: e.source, 
            target: e.target,
            weight: e.weight 
          }
        }))
      ],
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'background-color': '#2E7D32',
            'width': 30,
            'height': 30
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 'data(weight)',
            'line-color': '#ccc'
          }
        }
      ],
      layout: {
        name: 'fcose',
        animate: true
      }
    });
    
    // Add interactivity
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      console.log('Clicked:', node.data());
    });
    
    return () => cy.destroy();
  }, [data]);
  
  return <div ref={containerRef} style={{height: '600px'}} />;
};
```

## Week 3: Connect Everything

### 1. WebSocket Integration for Progress

```typescript
// src/hooks/useAnalysisProgress.ts
import { useEffect, useState } from 'react';
import io from 'socket.io-client';

export const useAnalysisProgress = (projectId: string) => {
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  
  useEffect(() => {
    const socket = io(`ws://localhost:8000/ws/${projectId}`);
    
    socket.on('progress', (data) => {
      setProgress(data.percentage);
      setPhase(data.phase);
    });
    
    socket.on('log', (message) => {
      setLogs(prev => [...prev, message]);
    });
    
    return () => {
      socket.disconnect();
    };
  }, [projectId]);
  
  return { progress, phase, logs };
};
```

### 2. File Upload with Progress

```typescript
// src/components/FileUpload.tsx
import React from 'react';
import { Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

const { Dragger } = Upload;

export const FileUpload: React.FC<{projectId: string}> = ({projectId}) => {
  const uploadProps = {
    name: 'file',
    multiple: true,
    action: `http://localhost:8000/api/projects/${projectId}/interviews`,
    onChange(info: any) {
      const { status } = info.file;
      if (status === 'done') {
        message.success(`${info.file.name} uploaded successfully.`);
      } else if (status === 'error') {
        message.error(`${info.file.name} upload failed.`);
      }
    },
    accept: '.docx,.doc'
  };
  
  return (
    <Dragger {...uploadProps}>
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">
        Click or drag interview files here
      </p>
      <p className="ant-upload-hint">
        Support for Word documents (.docx, .doc)
      </p>
    </Dragger>
  );
};
```

## Testing Strategy

### 1. Unit Tests (Jest + React Testing Library)

```typescript
// src/components/__tests__/ProjectDashboard.test.tsx
import { render, screen } from '@testing-library/react';
import { ProjectDashboard } from '../ProjectDashboard';

test('renders new project button', () => {
  render(<ProjectDashboard />);
  const button = screen.getByText(/New Project/i);
  expect(button).toBeInTheDocument();
});
```

### 2. Integration Tests (Cypress)

```javascript
// cypress/integration/analysis_workflow.spec.js
describe('Analysis Workflow', () => {
  it('completes full analysis', () => {
    cy.visit('/');
    cy.contains('New Project').click();
    cy.get('input[name="projectName"]').type('Test Project');
    cy.get('button[type="submit"]').click();
    
    // Upload files
    cy.get('input[type="file"]').attachFile('interview1.docx');
    
    // Start analysis
    cy.contains('Start Analysis').click();
    
    // Wait for completion
    cy.contains('Analysis Complete', { timeout: 180000 });
    
    // Check results
    cy.contains('View Results').click();
    cy.get('[data-testid="code-list"]').should('exist');
  });
});
```

## Deployment Strategy

### Development (Local)
```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd qualitative-coding-ui
npm start
```

### Staging (Docker)
```dockerfile
# Dockerfile.backend
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]

# Dockerfile.frontend
FROM node:18 as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
```

### Production (Cloud)
- Backend: Deploy to AWS Lambda or Google Cloud Run
- Frontend: Deploy to Vercel or Netlify
- Database: Neo4j Aura (managed cloud)
- File Storage: S3 or Google Cloud Storage

## Performance Targets

### Page Load
- Time to Interactive: <2s
- First Contentful Paint: <1s
- Largest Contentful Paint: <2.5s

### API Response Times
- List projects: <100ms
- Start analysis: <500ms
- Get results: <200ms

### Graph Rendering
- Initial render: <1s for 100 nodes
- Interaction response: <50ms
- Layout recalculation: <200ms

## Monitoring & Analytics

### Frontend Monitoring (Sentry)
```typescript
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "YOUR_SENTRY_DSN",
  integrations: [new Sentry.BrowserTracing()],
  tracesSampleRate: 1.0,
});
```

### Backend Monitoring (Prometheus + Grafana)
```python
from prometheus_client import Counter, Histogram
import time

analysis_counter = Counter('analysis_total', 'Total analyses')
analysis_duration = Histogram('analysis_duration_seconds', 'Analysis duration')

@analysis_duration.time()
async def run_analysis():
    analysis_counter.inc()
    # Analysis logic
```

## Success Criteria for MVP

### Week 1
- [ ] Basic project CRUD working
- [ ] File upload functional
- [ ] Backend API responding

### Week 2  
- [ ] Analysis can be triggered
- [ ] Progress updates via WebSocket
- [ ] Results displayed in table

### Week 3
- [ ] Graph visualization working
- [ ] Click interactions on nodes
- [ ] Export to JSON/CSV

### Week 4
- [ ] Deployed to staging
- [ ] 5 test users recruited
- [ ] Feedback collected

## Common Pitfalls to Avoid

1. **Over-engineering**: Start simple, iterate
2. **Ignoring mobile**: Test responsive design early
3. **Poor error handling**: Show clear error messages
4. **No loading states**: Users need feedback
5. **Forgetting accessibility**: Use semantic HTML, ARIA labels
6. **Not testing with real data**: Use actual interview files
7. **Premature optimization**: Profile first, optimize later

## Resources & References

- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Cytoscape.js Demos](https://js.cytoscape.org/demos/)
- [Ant Design Components](https://ant.design/components/overview/)
- [WebSocket with React](https://www.pluralsight.com/guides/using-web-sockets-in-your-reactredux-app)

## Questions to Answer Before Starting

1. **Authentication**: Do we need user accounts in MVP?
2. **Persistence**: How long do we keep analysis results?
3. **Concurrency**: How many simultaneous analyses?
4. **File Size**: Maximum interview file size?
5. **Browser Support**: Which browsers must we support?
6. **Offline**: Do we need offline capability?
7. **Collaboration**: Real-time or async sharing?

## Go/No-Go Checklist

Before starting development:
- [ ] Python backend environment working
- [ ] Neo4j database accessible
- [ ] Gemini API key configured
- [ ] Node.js 18+ installed
- [ ] Git repository created
- [ ] Domain/hosting decided
- [ ] User feedback plan ready
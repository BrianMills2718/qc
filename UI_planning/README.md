# Qualitative Coding Analysis System - UI Mockups

## Overview

This directory contains interactive HTML mockups for the Qualitative Coding Analysis System's web interface. These mockups demonstrate the visual design, user workflows, and interactive features planned for the application.

## Quick Start

To view the mockups, open any HTML file in your web browser:

```bash
# From the UI_planning/mockups directory
open 01_dashboard.html  # macOS
start 01_dashboard.html # Windows
xdg-open 01_dashboard.html # Linux
```

## Mockup Navigation

### 1. Dashboard (`01_dashboard.html`)
**Purpose**: Entry point for researchers to manage their qualitative analysis projects

**Key Features**:
- Project overview grid with status indicators
- Quick start wizard for new projects
- Drag-and-drop file upload interface
- Project status tracking (Draft, Processing, Complete)

**Interactive Elements**:
- "Create New Project" button opens modal dialog
- Project cards are clickable to navigate to workspace
- Drag-and-drop zone for interview files

**Next Steps**: Click any project card or create new → Project Workspace

---

### 2. Project Workspace (`02_project_workspace.html`)
**Purpose**: Main analysis interface with interactive graph visualization

**Key Features**:
- **Left Panel**: Filters and controls
  - Interview filter with checkboxes
  - Code category toggles
  - Analysis phase selection
- **Center Panel**: Interactive Cytoscape.js graph
  - Real-time graph manipulation
  - Zoom/pan controls
  - Node/edge visualization
- **Right Panel**: Context-sensitive details
  - Selected element information
  - Related quotes and codes
  - Quick actions

**Interactive Elements**:
- Working Cytoscape.js graph (try clicking nodes!)
- Category checkboxes toggle visibility
- View switcher (Graph/Timeline/Matrix)
- Export and settings buttons

**Navigation**:
- Codes panel → Codes Browser
- Graph nodes → Quote/Code details
- Export → Reports page

---

### 3. Codes Browser (`03_codes_browser.html`)
**Purpose**: Hierarchical exploration of the coding system

**Key Features**:
- Tree-view of code hierarchy
- Code statistics and metrics
- Example quotes for each code
- Visual indicators for:
  - Code frequency (quote count)
  - Theoretical importance (star ratings)
  - Category colors

**Interactive Elements**:
- Expandable/collapsible code tree
- Tab switching (Hierarchy/List/Network views)
- Search functionality
- Code relationship visualization

**Data Shown**:
- Open codes from initial coding
- Axial categories and relationships
- Core categories from selective coding
- Quote examples with context

---

### 4. Quotes Explorer (`04_quotes_explorer.html`)
**Purpose**: Deep dive into interview quotes and their coding

**Key Features**:
- Card-based quote display
- Rich metadata (interview, timestamp, phase)
- Multiple codes per quote
- Advanced filtering sidebar:
  - Interview selection
  - Code filtering
  - Date range
  - Coding phase

**Interactive Elements**:
- Quote cards with expand/collapse
- Multi-select filters
- Sort options (relevance, date, interview)
- View density toggle (compact/comfortable/expanded)

**Use Cases**:
- Finding all quotes with specific codes
- Reviewing coding consistency
- Extracting quotes for reports
- Cross-interview pattern analysis

---

### 5. Reports (`05_reports.html`)
**Purpose**: Generate and export analysis reports

**Key Features**:
- Multiple report formats:
  - Executive Summary
  - Full Analysis Report
  - Code Book
  - Theoretical Model
  - Audit Trail
- Export options (PDF, Word, Markdown)
- Report preview pane
- Customization settings

**Interactive Elements**:
- Report type selection
- Include/exclude sections checkboxes
- Preview/Edit toggle
- Export format dropdown

**Report Contents**:
- Key findings and insights
- Theoretical model visualization
- Code frequencies and relationships
- Supporting quotes and evidence
- Methodology documentation

---

## Design System

### Color Palette
- **Primary**: `#2E7D32` (Deep green - professional, analytical)
- **Secondary**: `#1565C0` (Deep blue - trust, depth)
- **Background**: `#FAFAFA` (Soft white)
- **Surface**: `#FFFFFF` (Pure white)
- **Text**: `#212121` (Near black)

### Visual Hierarchy
1. **Cards**: Primary content containers with subtle shadows
2. **Sidebars**: Secondary panels for filters and controls
3. **Headers**: Clear navigation and context
4. **Interactive Elements**: Consistent hover states and transitions

### Typography
- **Headers**: 600 weight for emphasis
- **Body**: 400 weight for readability
- **Code/Data**: Monospace for technical content

---

## Technical Implementation Notes

### Technologies Demonstrated
- **Cytoscape.js**: Graph visualization library (workspace mockup)
- **Responsive Grid**: CSS Grid and Flexbox layouts
- **Interactive JavaScript**: Event handlers and state management
- **Modern CSS**: Custom properties, transitions, shadows

### Browser Compatibility
- Tested in modern browsers (Chrome, Firefox, Safari, Edge)
- Requires JavaScript enabled for interactive features
- Responsive design adapts to different screen sizes

---

## Navigation Flow

```
Dashboard
    ├── Create New Project → Modal → Workspace
    └── Existing Project → Workspace
            ├── Graph View → Node Details
            ├── Codes Panel → Codes Browser
            ├── Quotes → Quotes Explorer
            └── Export → Reports
```

---

## Next Steps for Development

1. **Backend Integration**:
   - Connect to FastAPI endpoints
   - Implement WebSocket for real-time updates
   - Add authentication/authorization

2. **Frontend Framework**:
   - Convert to React components
   - Add state management (Redux/Zustand)
   - Implement routing

3. **Enhanced Features**:
   - Real-time collaboration
   - Advanced search with Elasticsearch
   - Machine learning insights
   - Export to qualitative analysis tools

---

## Viewing Instructions

### Local Viewing
1. Navigate to `UI_planning/mockups/`
2. Open `01_dashboard.html` in your browser
3. Use the navigation links to explore all mockups

### Features to Try
- **Dashboard**: Click "Create New Project" button
- **Workspace**: Interact with the Cytoscape graph
- **Codes Browser**: Expand/collapse the code tree
- **Quotes Explorer**: Try the filtering sidebar
- **Reports**: Switch between report types

### Known Limitations
These are static mockups with limited interactivity:
- Form submissions don't save data
- Filters show UI behavior but don't filter real data
- Export buttons demonstrate UI but don't generate files

---

## Feedback and Iteration

These mockups are designed to:
1. Validate the user interface design
2. Test navigation and workflow concepts
3. Gather stakeholder feedback
4. Guide frontend development

For the actual implementation, these mockups will be converted to a React application with full backend integration.
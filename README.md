# Advanced Qualitative Research & Network Analysis Tool

**Turn weeks of manual qualitative analysis into hours of automated insight discovery.**

Goes far beyond traditional qualitative coding - automatically extracts themes, maps entity relationships, identifies networks, and creates interactive visualizations from your interview transcripts.

## What This Does For You

### Before: Manual Qualitative Analysis
```
Week 1-2: Read through interviews, manually identify themes and code quotes
Week 3-4: Map relationships between concepts, track speaker characteristics
Week 5-6: Create network diagrams, identify organizational patterns by hand
Week 7-8: Build analysis framework, write findings, cross-check everything
Months: Still miss complex multi-interview patterns and network relationships
```

### After: Automated Network Analysis
```
Upload: Drop raw interview files - no preparation or annotation needed
Phase 1: Discovers themes across ALL interviews automatically
Phase 2: Identifies speakers, roles, attitudes, and expertise areas
Phase 3: Maps entities (people, organizations, processes, technologies) and relationships
Phase 4: Creates network graphs, builds comprehensive coded dataset
Result: Interactive network analysis, thematic coding, and relationship mapping ready for research
```

## Real Examples

**Input**: Raw interview transcript (no preparation needed)
```
"We tried implementing AI tools last year, but the team pushed back heavily. The problem wasn't the technology - it was that nobody trained us properly. That's a fair point. We definitely rushed the rollout without considering change management."
```

**What the System Discovers Automatically**:

**Themes Found**:
- *AI Implementation Challenges* - resistance, training gaps, change management issues
- *Organizational Barriers* - rushed rollout, insufficient planning and support
- *Technology Adoption Patterns* - user pushback, training importance, leadership reflection

**Speaker Intelligence**:
- *Sarah*: Management role, reflective attitude, organizational perspective, accepts feedback
- *Mike*: Technical role, direct communication, practical focus, problem-identifier  

**Entity Network Discovery**:
- **Organizations**: The company implementing AI, the team resisting change
- **Technologies**: AI tools being implemented, existing systems being replaced
- **Processes**: Training programs, rollout procedures, change management protocols
- **Outcomes**: Team pushback, implementation failure, lessons learned

**Relationship Networks**:
- Sarah **manages** → The team (hierarchical relationship)
- The team **uses** → AI tools (interaction relationship)  
- Poor training **causes** → User resistance (causal relationship)
- Implementation timeline **conflicts_with** → Team readiness (temporal relationship)
- Mike's feedback **influences** → Sarah's reflection (social relationship)

**Network Analysis Ready**:
- **Stakeholder Maps**: Who influences whom in the organization
- **Process Flows**: How decisions and changes propagate through systems
- **Causal Chains**: Multi-step cause-effect relationships across interviews
- **Conflict Networks**: Where tensions and disagreements cluster
- **Knowledge Networks**: Who has expertise and how it flows

**Key Features**: ✅ Automatic Speaker Detection | ✅ Entity Network Discovery | ✅ Neo4j Graph Analysis | ✅ Focus Group Integration

## Quick Start

### 1. Install & Configure
```bash
git clone <repository>
cd qualitative_coding
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Gemini API key
```

### 2. Run Analysis
```bash
# Put your interview files (.docx or .txt) in data/interviews/
python scripts/run_code_first_extraction.py config/extraction_config.yaml
```

### 3. View Results
```bash
python scripts/start_dashboard.py
# Opens web dashboard at http://localhost:8501
```

**That's it!** Your qualitative analysis is ready to explore.

## Use Cases

### Academic Research
- **Social Network Studies**: Map influence patterns and information flows
- **Organizational Research**: Analyze formal vs. informal networks, power dynamics, decision flows
- **Multi-site Studies**: Compare network structures and relationship patterns across locations
- **Dissertation Research**: Complete thematic + network analysis for thesis research

### Business Intelligence  
- **Stakeholder Mapping**: Identify key influencers, decision makers, and communication bottlenecks
- **Customer Journey Analysis**: Map touchpoints, pain points, and relationship networks
- **Employee Network Analysis**: Understand collaboration patterns, knowledge flows, informal networks
- **Market Research**: Analyze competitor relationships, customer influence networks, adoption patterns

### Organizational Consulting
- **Change Management**: Map resistance networks, influence pathways, adoption patterns
- **Communication Flow Analysis**: Identify information silos, bridge gaps, optimize flows
- **Leadership Network Assessment**: Understand informal leadership, influence patterns, coalition building
- **Process Optimization**: Analyze how decisions, approvals, and information flow through systems

### Policy & Social Science
- **Policy Network Analysis**: Map stakeholder relationships, influence patterns, coalition dynamics
- **Community Studies**: Analyze social networks, resource flows, support systems
- **Program Evaluation**: Assess intervention impacts on network structures and relationships
- **Conflict Analysis**: Map opposing factions, mediation opportunities, influence brokers

## How It Works

The tool uses a **smart 4-phase process** to automatically understand your interviews:

```
                    ADVANCED QUALITATIVE RESEARCH & NETWORK ANALYSIS SYSTEM

INPUT                   DISCOVERY PHASES                           APPLICATION                OUTPUT
┌─────────────────┐    ┌─────────────────────────────────────────────────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Interviews      │    │                4-PHASE DISCOVERY PIPELINE                  │    │ Phase 4         │    │ Comprehensive   │
│ (.docx/.txt)    │────┤ Phase 1: Theme   Phase 2: Speaker   Phase 3: Entity       │────│ Application     │────│ Analysis        │
│                 │    │ Discovery        Intelligence       Network Discovery       │    │                 │    │ ▶ Coded Quotes  │
│ ▶ Single-person │    │ ▶ Recurring      ▶ Role Detection   ▶ People, Orgs       │    │ ▶ Auto Speaker  │    │ ▶ Speaker Roles │
│ ▶ Multi-person  │    │   Themes         ▶ Attitude Maps    ▶ Technologies        │    │   Detection     │    │ ▶ Entity Maps   │
│ ▶ Focus Groups  │    │ ▶ Code           ▶ Expertise Areas  ▶ Processes           │    │ ▶ Dialogue Flow │    │ ▶ Relationships │
│ ▶ Auto-Detect   │    │   Hierarchies    ▶ Interaction      ▶ Relationship        │    │ ▶ Network       │    │ ▶ Neo4j Export  │
│   Format        │    │ ▶ Cross-Interview│   Patterns        │   Mapping           │    │   Integration   │    │ ▶ Thematic      │
└─────────────────┘    │   Patterns       │                  │ ▶ Causal Chains     │    │ ▶ Entity        │    │   Connections   │
                       └─────────────────────────────────────────────────────────────┘    │   Networks      │    └─────────────────┘
                                          │              │              │                   └─────────────────┘
                                          ▼              ▼              ▼                           │
                               ┌──────────────────────────────────────────────┐                    │
                               │          UNIFIED SCHEMAS (JSON)              │                    │
                               │ ▶ taxonomy.json    ▶ speaker_schema.json     │                    ▼
                               │ ▶ entity_schema.json (consistent framework)  │       ┌─────────────────────────────┐
                               └──────────────────────────────────────────────┘       │     NETWORK ANALYTICS       │
                                                                                      │                             │
                               ┌──────────────────────────────────────────────┐       │ ┌─────────────────────────┐ │
                               │            LiteLLM INTEGRATION               │       │ │   Neo4j Graph Export    │ │
                               │ ▶ Gemini 2.5 Flash (Primary)               │       │ │ ▶ Interactive Networks  │ │
                               │ ▶ Multi-provider Support                    │       │ │ ▶ Centrality Analysis   │ │
                               │ ▶ Structured JSON Output                    │       │ │ ▶ Community Detection  │ │
                               │ ▶ Automatic Fallback                        │       │ │ ▶ Influence Mapping     │ │
                               │ ▶ Parallel Processing                       │       │ └─────────────────────────┘ │
                               └──────────────────────────────────────────────┘       │ ┌─────────────────────────┐ │
                                                                                      │ │  Advanced Analytics     │ │
                                                                                      │ │ ▶ Social Networks       │ │
                                                                                      │ │ ▶ Process Flow Maps     │ │
                                                                                      │ │ ▶ Stakeholder Analysis  │ │
                                                                                      │ │ ▶ QCA Integration       │ │
                                                                                      │ └─────────────────────────┘ │
                                                                                      └─────────────────────────────┘

CAPABILITIES: Entity Network Discovery | Graph Analytics | Thematic Analysis | Speaker Intelligence
```

### Phase 1: Find All Themes
- Reads through **all** your interviews first
- Automatically discovers recurring themes and concepts  
- Creates a consistent coding scheme for your entire dataset
- **Example**: Finds themes like "training_challenges", "technology_adoption", "organizational_resistance"

### Phase 2: Understand Your Speakers
- Identifies different types of people in your interviews
- Figures out roles, expertise levels, and attitudes automatically
- **Example**: "Sarah = Manager, experienced, change-oriented" vs "Mike = Developer, technical, cautious"

### Phase 3: Map Relationships
- Discovers how concepts connect to each other
- Finds cause-effect relationships and dependencies
- **Example**: "Poor training → User resistance → Project failure"

### Phase 4: Code Everything Consistently  
- Applies what it learned to each individual interview
- Extracts quotes and assigns codes automatically
- Maintains speaker context and dialogue flow
- **Result**: Every interview coded with the same comprehensive framework

### What Makes This Smart
- **No Manual Setup**: Just upload your files and run
- **Automatic Speaker Detection**: Figures out who's talking without manual tagging
- **Focus Group Ready**: Handles complex multi-person conversations
- **Consistent Results**: Same coding scheme across all interviews
- **Relationship Mapping**: Connects related concepts automatically

## What You Get

After analysis, you'll have comprehensive qualitative research AND network analysis results:

### Complete Thematic Analysis
- **Discovered Themes**: Automatically identified recurring concepts across all interviews
- **Hierarchical Coding**: Themes organized into main categories and sub-themes
- **Evidence Grounding**: Every theme supported by specific quotes and examples
- **Cross-Interview Patterns**: Themes that appear across multiple participants
- **Frequency Analysis**: How often themes appear and in what contexts

### Speaker Intelligence & Roles
- **Automatic Speaker Detection**: System identifies who's talking without manual tagging
- **Role Classification**: Discovers participant roles (manager, developer, user, expert, etc.)
- **Attitude Analysis**: Identifies speaker attitudes (supportive, critical, neutral, evolving)
- **Expertise Mapping**: Determines areas of knowledge and experience for each speaker
- **Interaction Patterns**: How speakers respond to and build on each other's ideas

### Relationship & Connection Mapping
- **Cause-Effect Relationships**: "Poor training leads to user resistance"  
- **Supportive Connections**: Ideas that reinforce each other across interviews
- **Contradictory Relationships**: Conflicting viewpoints and disagreements
- **Thematic Evolution**: How concepts develop and change within conversations
- **Cross-Speaker Influences**: How participants respond to and build on others' ideas

### Entity & Network Analysis
- **Automatic Entity Discovery**: Identifies people, organizations, technologies, processes, and outcomes
- **Relationship Mapping**: Maps hierarchical, causal, temporal, social, and conflict relationships
- **Network Visualization**: Interactive Neo4j graphs showing stakeholder maps and process flows
- **Centrality Analysis**: Identifies key players, bottlenecks, and influence patterns
- **Network Clusters**: Discovers communities, coalitions, and information silos
- **Multi-Level Networks**: Individual, organizational, and system-level relationship patterns

### Focus Group Intelligence
- **Dialogue Context**: Maintains conversation flow and speaker interactions
- **Group Dynamics**: Identifies consensus, disagreement, and influence patterns  
- **Multi-Person Conversations**: Handles complex group discussions automatically
- **Turn-Taking Analysis**: Who speaks when and in response to what
- **Collective Themes**: Ideas that emerge from group interaction vs. individual perspectives

### Advanced Analytics Ready
- **Neo4j Graph Database**: Full network export for advanced graph analytics
- **Social Network Analysis**: Relationship mapping and influence flows
- **Organizational Network Analysis**: Formal vs. informal networks, communication patterns
- **Process Network Analysis**: How decisions, information, and problems flow through systems
- **Temporal Network Analysis**: How relationships and influences change over time

### Research-Ready Outputs
- **Academic Publications**: Network analysis + qualitative findings with methodological transparency
- **Organizational Consulting**: Stakeholder maps, influence networks, communication flow analysis
- **Policy Research**: Evidence-based recommendations with network-informed insights
- **Business Intelligence**: Customer journey networks, employee interaction patterns, decision flows
- **Interactive Dashboards**: Explore themes, visualize networks, search relationships

---

## Installation & Setup

### Requirements
- Python 3.11+
- Google Gemini API key (free tier available)
- 4GB+ RAM recommended for larger datasets

### Install
```bash
git clone <repository>
cd qualitative_coding
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Gemini API key
```

### Run Your First Analysis
```bash
# Put your .docx/.txt interview files in data/interviews/
python scripts/run_code_first_extraction.py config/extraction_config.yaml
python scripts/start_dashboard.py
# Open http://localhost:8501 to explore results
```

### Basic Configuration
```yaml
# config/extraction_config.yaml
analytic_question: "How do researchers experience AI tool integration?"
interview_files_dir: "data/interviews/"
coding_approach: open          # Automatically discover themes
speaker_approach: open         # Automatically discover speaker types  
entity_approach: open          # Automatically discover relationships
output_dir: "outputs"
llm_model: "gemini/gemini-2.5-flash"
```

### Advanced Options
- **Analysis Paradigms**: Choose theoretical lens (phenomenological, critical_theory, etc.)
- **Neo4j Export**: Automatic graph database import for network analysis
- **Parallel Processing**: Configure concurrent interview processing
- **Custom Schemas**: Use predefined codes/frameworks instead of discovery

## Methodology

### Grounded Theory Framework

This system implements **Strauss & Corbin's grounded theory methodology** for systematic qualitative analysis:

**Code Structure**:
- **Properties** = General characteristics of a concept (e.g., "Qualitative", "Economic analysis", "Technology-focused")
- **Dimensions** = Variations along a continuum within that concept (e.g., "High-to-low complexity", "Cost-effective-to-expensive", "User-friendly-to-technical")

**Hierarchical Coding**:
- **Level 0**: Top-level parent codes (major themes like "AI Adoption Challenges")
- **Level 1**: Child codes (specific aspects like "Training Gaps", "Resistance Patterns")  
- **Level 2**: Grandchild codes (detailed sub-aspects like "Technical Training", "Change Management Training")
- **Level 3+**: Further refinement as supported by data

**Analysis Phases**:
1. **Open Coding**: Identify concepts and organize into hierarchical categories
2. **Axial Coding**: Map relationships between categories with conditions and consequences
3. **Selective Coding**: Develop core categories that explain the central phenomenon
4. **Theory Integration**: Build theoretical model explaining the overall process

This systematic approach ensures methodological rigor while maintaining the flexibility needed for qualitative discovery.

## Need Help?

- **📚 [Full Documentation](docs/)** - Complete setup and configuration guides
- **🔧 [Technical Details](docs/technical-reference/)** - System architecture and API docs  
- **🚀 [Deployment Guide](docs/user-guides/DEPLOYMENT.md)** - Production deployment with Docker

## Advanced Features

**For Research Teams**:
- **QCA Pipeline**: Quantitative Comparative Analysis for outcome research
- **Network Analytics**: Neo4j integration for relationship visualization
- **Audit Trails**: Complete methodological transparency for publications

**For Enterprises**:
- **REST API**: Integration with existing research workflows
- **Docker Deployment**: Scalable production infrastructure
- **Multi-format Support**: Handle various interview formats automatically

## License

MIT - Use freely for academic and commercial research.
# LLM-First Approach Documentation

## 🤖 Philosophy: Leverage LLMs for All Decision-Making

**Core Principle**: Instead of hardcoding rules or using simple algorithms, use LLMs to make intelligent decisions about qualitative research processes.

---

## 🔍 LLM-Driven Text Processing

### 1. **Speaker Identification**
```python
async def identify_speakers(interview_text: str) -> List[Speaker]:
    """Use LLM to intelligently identify speakers in interview text"""
    
    prompt = f"""
    Analyze this interview text and identify all speakers.
    
    Look for patterns like:
    - "Name:" followed by speech
    - "[Speaker labels]" 
    - Interviewer vs participant patterns
    - Context clues about who is speaking
    
    Interview text:
    {interview_text}
    
    Return JSON with speakers and their speaking patterns.
    """
    
    response = await gemini_client.generate_content(prompt)
    return parse_speakers(response.text)
```

**Why LLM-first**: 
- Handles inconsistent formats ("Alice:", "[Participant 1]", "Interviewer", etc.)
- Understands context clues
- Adapts to new speaker formats without code changes

### 2. **Quote Attribution and Line Numbers**
```python
async def map_quotes_to_sources(quotes: List[str], interview_text: str) -> List[QuoteLocation]:
    """Use LLM to map extracted quotes back to their locations"""
    
    prompt = f"""
    Find the exact locations of these quotes in the interview text.
    
    Quotes to find:
    {json.dumps(quotes)}
    
    Interview text (with line numbers):
    {add_line_numbers(interview_text)}
    
    Return the line numbers, context, and any speaker information for each quote.
    Be precise about exact matches and handle paraphrases intelligently.
    """
    
    response = await gemini_client.generate_content(prompt)
    return parse_quote_locations(response.text)
```

### 3. **Content Structure Analysis**
```python
async def analyze_interview_structure(interview_text: str) -> InterviewStructure:
    """Use LLM to understand the structure and format of the interview"""
    
    prompt = f"""
    Analyze the structure of this interview text:
    
    1. What type of interview is this? (individual, focus group, notes, transcript)
    2. How are speakers indicated?
    3. Are there timestamps or other structural elements?
    4. What sections or topics are covered?
    5. Any special formatting or notes to preserve?
    
    Interview text:
    {interview_text[:5000]}...  # First 5K chars for structure analysis
    
    Provide detailed analysis to guide processing decisions.
    """
    
    response = await gemini_client.generate_content(prompt)
    return parse_structure_analysis(response.text)
```

---

## 📊 LLM-Driven Qualitative Coding Process

### Phase 1: Open Coding with LLM
```python
async def open_coding(interview_text: str, research_question: str) -> OpenCodingResult:
    """LLM performs initial open coding - discovering codes from data"""
    
    prompt = f"""
    Perform OPEN CODING on this interview transcript using grounded theory methodology.
    
    Research Question: {research_question}
    
    Instructions:
    1. Read the entire transcript carefully
    2. Identify meaningful segments related to experiences, feelings, challenges, strategies
    3. Create descriptive codes for each segment
    4. Write analytical memos explaining your coding decisions
    5. Focus on participant's perspective and meaning-making
    
    For each coded segment:
    - Extract the EXACT quote
    - Create descriptive code name
    - Write clear definition 
    - Add analytical memo explaining significance
    - Note any theoretical insights
    
    Interview text:
    {interview_text}
    
    Return comprehensive open coding results in JSON format.
    """
    
    response = await gemini_client.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    return OpenCodingResult.parse_raw(response.text)
```

### Phase 2: Axial Coding with LLM
```python
async def axial_coding(interview_text: str, open_codes: OpenCodingResult, 
                      existing_codebook: Optional[Codebook]) -> AxialCodingResult:
    """LLM performs axial coding - finding relationships between codes"""
    
    codebook_context = ""
    if existing_codebook:
        codebook_context = f"""
        Existing Codebook Context:
        {existing_codebook.to_context_string()}
        
        Consider how new codes relate to existing categories and themes.
        """
    
    prompt = f"""
    Perform AXIAL CODING to organize these open codes into categories and find relationships.
    
    {codebook_context}
    
    Open codes from this interview:
    {open_codes.to_json()}
    
    Instructions:
    1. Group related codes into substantive categories
    2. Identify properties and dimensions of each category
    3. Find relationships between categories:
       - Causal conditions (what leads to this?)
       - Context (what influences this?)
       - Intervening conditions (what facilitates/constrains?)
       - Action/interaction strategies (how do people respond?)
       - Consequences (what are the outcomes?)
    
    4. Develop theoretical connections between categories
    5. Write analytical memos about category development
    
    Build a hierarchical structure showing relationships.
    """
    
    response = await gemini_client.generate_content(prompt)
    return AxialCodingResult.parse_raw(response.text)
```

### Phase 3: Selective Coding with LLM
```python
async def selective_coding(interview_text: str, categories: AxialCodingResult,
                          existing_codebook: Optional[Codebook]) -> SelectiveCodingResult:
    """LLM performs selective coding - identifying core category and theory"""
    
    prompt = f"""
    Perform SELECTIVE CODING to identify the core category and theoretical story.
    
    Categories from axial coding:
    {categories.to_json()}
    
    Existing codebook context:
    {existing_codebook.to_context_string() if existing_codebook else "None"}
    
    Instructions:
    1. Identify the CENTRAL phenomenon that ties everything together
    2. Show how all other categories relate to this core category
    3. Develop the overall theoretical story the data tells
    4. Generate key theoretical insights
    5. Explain the process or experience at the heart of this data
    
    The core category should:
    - Appear frequently in the data
    - Connect to most other categories  
    - Have explanatory power
    - Be sufficiently abstract to be theoretical
    
    Provide a theoretical model explaining the core phenomenon.
    """
    
    response = await gemini_client.generate_content(prompt)
    return SelectiveCodingResult.parse_raw(response.text)
```

---

## 🔄 LLM-Driven Codebook Evolution

### Codebook Merging and Evolution
```python
async def evolve_codebook(current_codebook: Codebook, 
                         new_results: List[QCResult]) -> Codebook:
    """Use LLM to intelligently evolve the codebook with new discoveries"""
    
    prompt = f"""
    Evolve this qualitative coding codebook by integrating new findings.
    
    Current Codebook:
    {current_codebook.to_comprehensive_json()}
    
    New Coding Results:
    {[result.to_json() for result in new_results]}
    
    Instructions:
    1. Identify new codes that should be added to the codebook
    2. Find existing codes that should be merged or refined
    3. Determine if any categories or themes need restructuring
    4. Update code definitions based on new evidence
    5. Evolve theoretical understanding
    6. Maintain consistency across the growing dataset
    
    Consider:
    - Are new codes truly distinct or variants of existing ones?
    - Do new findings challenge existing theoretical understanding?
    - How can the codebook better capture the phenomenon?
    - What new relationships are emerging?
    
    Return evolved codebook with clear change documentation.
    """
    
    response = await gemini_client.generate_content(prompt)
    return Codebook.parse_raw(response.text)
```

### Theoretical Saturation Assessment
```python
async def assess_saturation(current_codebook: Codebook, 
                           new_codebook: Codebook,
                           batch_results: List[QCResult]) -> SaturationAssessment:
    """Use LLM to determine if theoretical saturation has been reached"""
    
    prompt = f"""
    Assess whether theoretical saturation has been reached in this qualitative study.
    
    Previous Codebook:
    {current_codebook.to_json()}
    
    Updated Codebook:
    {new_codebook.to_json()}
    
    Latest Batch Results:
    {[result.to_json() for result in batch_results]}
    
    Saturation Criteria:
    1. Are new interviews producing significantly new codes/categories?
    2. Are existing categories becoming more refined rather than fundamentally changed?
    3. Can new data be easily accommodated within existing framework?
    4. Are theoretical insights stabilizing?
    5. Is the core category well-developed and stable?
    
    Consider:
    - Percentage of new vs refined codes
    - Stability of category structure
    - Theoretical development completeness
    - Ability to explain new data with existing framework
    
    Provide detailed saturation assessment with recommendations.
    """
    
    response = await gemini_client.generate_content(prompt)
    return SaturationAssessment.parse_raw(response.text)
```

---

## 🎯 LLM-Driven Analysis Features

### Contradiction Detection
```python
async def detect_contradictions(all_results: List[QCResult]) -> List[Contradiction]:
    """Use LLM to identify contradictions and tensions in the data"""
    
    prompt = f"""
    Analyze these qualitative coding results to identify contradictions, tensions, or paradoxes.
    
    All Coding Results:
    {[result.summary_json() for result in all_results]}
    
    Look for:
    1. Direct contradictions between participants
    2. Internal contradictions within single interviews
    3. Tensions between different themes or categories
    4. Paradoxes that reveal complexity
    5. Conflicting perspectives on same phenomena
    
    For each contradiction found:
    - Describe the nature of the contradiction
    - Provide specific evidence from quotes
    - Analyze potential explanations
    - Consider if this reveals important complexity rather than error
    
    Focus on meaningful contradictions that add theoretical insight.
    """
    
    response = await gemini_client.generate_content(prompt)
    return parse_contradictions(response.text)
```

### Policy Brief Generation
```python
async def generate_policy_brief(final_analysis: FinalAnalysis) -> PolicyBrief:
    """Use LLM to generate actionable policy recommendations from QC analysis"""
    
    prompt = f"""
    Generate a policy brief based on this qualitative coding analysis.
    
    Analysis Results:
    {final_analysis.to_comprehensive_json()}
    
    Create a policy brief that:
    1. Summarizes key findings in policy-relevant terms
    2. Identifies actionable recommendations
    3. Prioritizes recommendations by impact and feasibility
    4. Provides evidence-based justification
    5. Considers implementation challenges
    6. Suggests metrics for success
    
    Structure:
    - Executive Summary
    - Key Findings
    - Policy Recommendations (prioritized)
    - Implementation Considerations  
    - Success Metrics
    
    Write for policy makers who need clear, actionable guidance.
    """
    
    response = await gemini_client.generate_content(prompt)
    return PolicyBrief.parse_raw(response.text)
```

---

## ⚙️ Configuration for LLM-First Approach

### Environment Variables
```bash
# LLM Configuration
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.3
GEMINI_MAX_OUTPUT_TOKENS=60000

# QC Process Configuration  
QC_BATCH_SIZE=3
QC_MAX_BATCHES=10
QC_SATURATION_THRESHOLD=0.15  # 15% new codes = not saturated
QC_RESEARCH_QUESTION="What are the key experiences and patterns?"

# LLM Decision Thresholds
SPEAKER_DETECTION_CONFIDENCE=0.8
CODE_SIMILARITY_THRESHOLD=0.85
SATURATION_CONFIDENCE=0.9
```

### Benefits of LLM-First Approach

1. **Adaptive**: Handles new formats without code changes
2. **Intelligent**: Makes nuanced decisions like human researchers
3. **Consistent**: Same decision-making framework across all text processing
4. **Scalable**: No need to manually handle edge cases
5. **Theoretically Grounded**: Applies qualitative research methodology correctly

This approach ensures that the system behaves like an expert qualitative researcher at every decision point.
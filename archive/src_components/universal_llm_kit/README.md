# Universal LLM Kit 🚀

**Educational examples and patterns for using LiteLLM structured output across all major providers.**

⚠️ **Important**: This kit is designed to **show examples** of how to use LiteLLM features, not as a production abstraction layer. Use these patterns to learn LiteLLM, then implement directly in your projects.

## 🎯 What This Demonstrates

- ✅ **All Major Providers**: OpenAI, Anthropic, Google, OpenRouter, etc.
- ✅ **Code Execution**: Native Gemini code execution support
- ✅ **Function Calling**: Unified interface across all providers
- ✅ **Structured Output**: Multiple approaches with Pydantic support
- ✅ **Smart Routing**: Cost-based, latency-based automatic model selection
- ✅ **Auto Fallbacks**: Provider fails → automatically tries next provider
- ✅ **Model Constraints**: Handles o1 models, token limits automatically
- ✅ **Maximum Tokens**: Auto-configured per model for optimal output

## 🚀 Quick Setup

1. **Copy this folder** to your project
2. **Install requirements**: `pip install -r requirements.txt`
3. **Setup API keys**: Copy `.env.template` to `.env` and add your keys
4. **Start using**: Import and go!

```python
from universal_llm import chat, code, reason

# Universal chat - auto-selects best model
response = chat("Explain quantum computing")

# Code execution with Gemini
result = code("Calculate fibonacci numbers")

# Complex reasoning with o1 models
solution = reason("Solve this complex math problem...")
```

## 📁 Files

- `universal_llm.py` - Main universal interface
- `demo.py` - Complete demonstration of all features
- `quick_examples.py` - Copy-paste examples for your code
- `.env.template` - API keys template
- `requirements.txt` - Dependencies

## 🔑 API Keys Setup

Copy `.env.template` to `.env` and fill in your keys:

```bash
# Required: At least one of these
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here  
GEMINI_API_KEY=your_key_here

# Optional: Additional providers
OPENROUTER_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

## 💻 Usage Examples

### Basic Chat
```python
from universal_llm import chat

response = chat("Write a Python function to reverse a string")
print(response)
```

### Code Execution
```python
from universal_llm import code

# Uses Gemini's native code execution
result = code("Create a bar chart of sales data: Q1=100, Q2=150, Q3=200")
print(result)
```

### Complex Reasoning
```python
from universal_llm import reason

# Uses o1 models for deep reasoning
solution = reason("Analyze the economic implications of AI automation")
print(solution)
```

### Structured Output
```python
from universal_llm import structured
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float
    category: str

# CONSERVATIVE APPROACH (used in this kit for compatibility)
result = structured("Create a product for an online store", Product)
print(result)  # Valid JSON matching schema

# ADVANCED APPROACH (direct LiteLLM - recommended for production)
import litellm
response = litellm.completion(
    model="gemini/gemini-2.5-flash",
    messages=[{"role": "user", "content": "Create a product for an online store"}],
    response_format=Product  # ← Direct Pydantic model support
)
print(response.choices[0].message.content)  # Guaranteed schema compliance
```

### Model Comparison
```python
from universal_llm import compare

results = compare("Write a haiku about coding", ["smart", "fast", "code"])
for model, response in results.items():
    print(f"{model}: {response}")
```

### Advanced Usage
```python
from universal_llm import UniversalLLM

llm = UniversalLLM()

# Function calling
tools = [{"type": "function", "function": {...}}]
response = llm.function_call("What's the weather?", tools)

# Custom parameters
response = llm.chat("Hello", model_type="smart", temperature=0.7)
```

## 🔄 Automatic Features

### Smart Routing
- **Cost-based**: Automatically uses cheapest model that meets requirements
- **Latency-based**: Routes to fastest responding models
- **Capability-based**: Selects models with required features (code, tools, etc.)

### Automatic Fallbacks
- Primary model fails → tries backup models
- Provider outage → switches to different provider
- Context limit exceeded → uses model with larger context window

### Model Constraints
- o1 models: Automatically removes temperature/tools (not supported)
- Token limits: Auto-configures maximum tokens per model
- Feature detection: Only uses models that support requested features

## 🎯 Model Types

- **`smart`**: Best general-purpose model (GPT-4o, Claude-3.5-Sonnet, Gemini-2.0-Flash)
- **`fast`**: Quick responses (GPT-4o-mini, Claude-3.5-Haiku)
- **`code`**: Code execution enabled (Gemini-2.5-Flash with codeExecution)
- **`reasoning`**: Deep thinking (o1-preview, o1-mini)
- **`thinking`**: Step-by-step reasoning (Gemini-2.0-Flash-Thinking)

## 🚨 Error Handling

The kit includes robust error handling:
- Provider failures → automatic fallback
- API key missing → clear error message
- Rate limits → automatic retry with backoff
- Invalid requests → graceful degradation

## 📊 Cost Optimization

- Uses cheapest available model by default
- Automatically routes expensive requests to capable models only
- Tracks usage and costs (via LiteLLM)
- Provides cost estimates before calls

## 📚 LiteLLM Structured Output Approaches

This kit demonstrates **multiple approaches** to structured output. Choose based on your needs:

### 1. Conservative JSON Mode (Used in This Kit)
```python
# Compatible across all models but uses prompt engineering
kwargs["response_format"] = {"type": "json_object"}
prompt = f"{prompt}\n\nRespond with valid JSON matching this schema: {schema.model_json_schema()}"
```
**Pros**: Works everywhere | **Cons**: Prompt-based, less reliable

### 2. Direct Pydantic Models (Recommended for Production)
```python
# Real schema enforcement - use this in your projects
import litellm
response = litellm.completion(
    model="gemini/gemini-2.5-flash",  # or gpt-4, claude-3-5-sonnet
    messages=[{"role": "user", "content": prompt}],
    response_format=YourPydanticModel
)
```
**Pros**: True schema enforcement | **Cons**: Model-dependent support

### 3. Explicit JSON Schema
```python
# For maximum control (may not work with all models)
response = litellm.completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    response_format={
        "type": "json_schema", 
        "json_schema": schema.model_json_schema(),
        "strict": True
    }
)
```
**Pros**: Maximum control | **Cons**: Limited model support

### 4. Client-Side Validation Fallback
```python
# Best of both worlds - schema enforcement with fallback
import litellm
litellm.enable_json_schema_validation = True

response = litellm.completion(
    model="any-model",
    messages=[{"role": "user", "content": prompt}],
    response_format=YourPydanticModel
)
```
**Pros**: Reliable + compatible | **Cons**: Slight performance overhead

## 🎯 Production Recommendations

**For Production Systems**: Use approach #2 (Direct Pydantic) or #4 (with validation fallback)

**For Learning/Prototyping**: Use this kit's conservative approach (#1)

**Why This Kit Uses Conservative Approach**: Maximum compatibility across all models and providers for educational purposes.

## 🔧 Customization

Extend the kit for your needs:

```python
# Add custom models
llm = UniversalLLM()
llm.router.model_list.append({
    "model_name": "custom",
    "litellm_params": {"model": "your-custom-model"}
})

# Change routing strategy
llm.router.routing_strategy = "latency-based"  # or "least-busy"
```

## 🎉 Run Demo

```bash
python demo.py
```

This runs all capabilities:
- Basic chat
- Code execution  
- Complex reasoning
- Function calling
- Structured output
- Model comparison
- Advanced features

Perfect for testing your setup and seeing all features in action!

## 🤖 Multi-Agent Consensus System

**NEW**: Advanced consensus system that runs problems through multiple LLMs to find convergence and track opinion dynamics.

### Consensus Features
- ✅ **Multi-Model Analysis**: Run problems through 3+ different LLMs
- ✅ **Convergence Tracking**: Monitor how opinions converge over rounds
- ✅ **Opinion Dynamics**: Track which models influence others
- ✅ **Intelligent Judging**: Claude Sonnet judges similarity and convergence
- ✅ **Configurable**: Customize models, rounds, thresholds
- ✅ **Analysis Tools**: Detailed reports and visualizations

### Quick Consensus Example
```python
from consensus_system import MultiAgentConsensus, ConsensusConfig

config = ConsensusConfig(
    participating_models=["gemini/gemini-2.5-flash", "gpt-4o-mini", "deepseek/deepseek-reasoner"],
    judge_model="claude-3-5-sonnet-20241022",
    max_rounds=5,
    convergence_threshold=0.8
)

consensus = MultiAgentConsensus(config)
result = consensus.run_consensus("What's the best sorting algorithm for 1M integers?")

print(f"Converged: {result['metadata']['converged']}")
print(f"Final positions: {result['final_positions']}")
```

### Consensus System Files
- `consensus_system.py` - Main consensus engine
- `consensus_demo.py` - Multiple demonstration scenarios  
- `consensus_analyzer.py` - Analysis and visualization tools
- `test_consensus.py` - Quick connectivity and functionality tests

### Run Consensus Tests
```bash
# Test system connectivity
python test_consensus.py

# Run technical problem demo
python consensus_demo.py technical

# Run all demo scenarios
python consensus_demo.py all

# Analyze results
python consensus_analyzer.py consensus_result_technical.json
```

---

## 🚨 Important Disclaimer

**This kit is for educational purposes and prototyping.** 

For production systems:
- **Use LiteLLM directly** with approach #2 or #4 from the structured output section
- **Don't add unnecessary abstraction layers** - LiteLLM is already a great abstraction
- **Copy the patterns you need** rather than importing this entire kit as a dependency

**Learn from these examples, then implement directly in your projects!** 🎯

---

**Use this kit to learn LiteLLM patterns, then graduate to direct LiteLLM usage for production!** 🚀
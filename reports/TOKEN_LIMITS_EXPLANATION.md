# Token Limits Explanation

## Why We Can't Remove max_tokens Entirely

The `max_tokens` parameter controls the **output length**, not input length:

- **Input tokens**: How much text you send TO the model (prompt + context)
- **Output tokens**: How much text the model can GENERATE in response

### Model Limits:

**Gemini 2.5 Flash:**
- Input: 1,048,576 tokens (1M) - This is huge! Can handle ~4M characters
- Output: 8,192 tokens - This is the hard limit for response generation

**Why 200,000 is Too High:**
- Gemini's maximum output is 8,192 tokens (~32,000 characters)
- Setting max_tokens=200,000 would be ignored by the API
- The model physically cannot generate that much output

## The Real Problem

Our issue isn't the token limit - it's that:

1. **JSON gets truncated** when extracting many entities
2. **Response parser fails** on incomplete JSON
3. **Enhanced client gives up** instead of handling partial results

## Better Solutions:

### 1. Use Streaming (Best for Large Extractions)
```python
# Stream the response and build JSON incrementally
response = client.complete_stream(
    messages=messages,
    model="gemini-2.5-flash",
    schema=schema,
    max_tokens=8192  # Use full capacity
)
```

### 2. Chunk the Interview
```python
# Process interview in sections
chunks = split_interview(full_text, chunk_size=10000)
all_entities = []
for chunk in chunks:
    entities = extract_entities(chunk)
    all_entities.extend(entities)
```

### 3. Simplify Output Format
```python
# Request only entity IDs first, then details
prompt = "List just the names of all people mentioned"
# Then fetch details in batches
```

### 4. Handle Partial JSON (Quick Fix)
```python
def parse_partial_entities(json_str):
    """Extract entities even from truncated JSON"""
    # Find all complete entity objects
    entities = []
    pattern = r'\{"id":\s*"[^"]+",\s*"name":\s*"[^"]+",\s*"type":\s*"[^"]+"[^}]*\}'
    matches = re.findall(pattern, json_str)
    for match in matches:
        try:
            entity = json.loads(match)
            entities.append(entity)
        except:
            pass
    return entities
```

## Recommended Approach

1. **Keep max_tokens=8192** (Gemini's actual limit)
2. **Implement partial JSON recovery** for truncated responses
3. **Use chunking** for very large interviews if needed
4. **Consider streaming** for real-time processing

The issue isn't that we need more tokens - it's that we need to handle the responses better!
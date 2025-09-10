"""Test real structured output with LiteLLM and Gemini"""
import asyncio
import litellm
from pydantic import BaseModel
from typing import List

class SimpleTest(BaseModel):
    name: str
    age: int
    hobbies: List[str]

async def test_structured():
    """Test if we can get real structured output"""
    
    # Method 1: Using response_model (what I tried)
    print("Method 1: response_model parameter")
    try:
        response = await litellm.acompletion(
            model="gemini/gemini-2.5-flash",
            messages=[{"role": "user", "content": "Create a person named John who is 30 and likes hiking and coding"}],
            response_model=SimpleTest
        )
        print(f"Success! Type: {type(response)}")
        if isinstance(response, SimpleTest):
            print(f"Got Pydantic model: {response.model_dump()}")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Method 2: Using response_format with schema
    print("\nMethod 2: response_format with schema")
    try:
        response = await litellm.acompletion(
            model="gemini/gemini-2.5-flash",
            messages=[{"role": "user", "content": "Create a person named John who is 30 and likes hiking and coding. Return as JSON with fields: name (string), age (int), hobbies (array of strings)"}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "person",
                    "schema": SimpleTest.model_json_schema()
                }
            }
        )
        print(f"Response type: {type(response)}")
        print(f"Content: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Method 3: Using instructor library (if available)
    print("\nMethod 3: Checking for instructor")
    try:
        import instructor
        print("Instructor is available")
        # Instructor can patch litellm for structured output
        client = instructor.from_litellm(litellm.acompletion)
        response = await client.chat.completions.create(
            model="gemini/gemini-2.5-flash",
            messages=[{"role": "user", "content": "Create a person named John who is 30 and likes hiking and coding"}],
            response_model=SimpleTest
        )
        print(f"Success with instructor! Type: {type(response)}")
    except ImportError:
        print("Instructor not installed")
    except Exception as e:
        print(f"Instructor failed: {e}")
    
    # Method 4: Just JSON mode (current approach)
    print("\nMethod 4: JSON mode (current)")
    response = await litellm.acompletion(
        model="gemini/gemini-2.5-flash",
        messages=[{"role": "user", "content": "Create a person named John who is 30 and likes hiking and coding. Return JSON with: name, age, hobbies"}],
        response_format={"type": "json_object"}
    )
    print(f"Response type: {type(response)}")
    import json
    data = json.loads(response.choices[0].message.content)
    print(f"Parsed data: {data}")
    person = SimpleTest(**data)
    print(f"Pydantic model: {person.model_dump()}")

if __name__ == "__main__":
    asyncio.run(test_structured())
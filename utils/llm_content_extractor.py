"""
LLM Content Extraction Helper
Properly extracts content from various LLM response formats
"""

import json
from typing import Any, Dict, Optional, Union


def extract_llm_content(response: Dict[str, Any]) -> Optional[str]:
    """
    Extract content from LLM response regardless of format
    
    Args:
        response: The response dictionary from UniversalModelClient
        
    Returns:
        The extracted content string or None if not found
    """
    if not response or "response" not in response:
        return None
    
    resp_obj = response["response"]
    
    # Method 1: Standard litellm ModelResponse with choices
    if hasattr(resp_obj, 'choices') and len(resp_obj.choices) > 0:
        choice = resp_obj.choices[0]
        
        # Try message.content first (chat models)
        if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
            return choice.message.content
        
        # Try text (completion models)
        elif hasattr(choice, 'text'):
            return choice.text
    
    # Method 2: Dictionary format
    elif isinstance(resp_obj, dict):
        if 'choices' in resp_obj and len(resp_obj['choices']) > 0:
            choice = resp_obj['choices'][0]
            
            # Chat format
            if 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
            
            # Completion format
            elif 'text' in choice:
                return choice['text']
    
    # Method 3: Direct content field
    elif hasattr(resp_obj, 'content'):
        return resp_obj.content
    
    # Fallback: convert to string
    return str(resp_obj)


def extract_json_from_content(content: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from content that might have markdown or other formatting
    
    Args:
        content: The content string that may contain JSON
        
    Returns:
        Parsed JSON dictionary or None if parsing fails
    """
    if not content:
        return None
    
    # Try direct parsing first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Remove markdown code blocks if present
    content = content.strip()
    
    # Handle ```json blocks
    if '```json' in content:
        start = content.find('```json') + 7
        end = content.find('```', start)
        if end > start:
            content = content[start:end].strip()
    elif '```' in content:
        # Handle generic code blocks
        start = content.find('```') + 3
        end = content.find('```', start)
        if end > start:
            content = content[start:end].strip()
    
    # Also handle case where content starts with ```
    if content.startswith('```json'):
        content = content[7:]
    elif content.startswith('```'):
        content = content[3:]
    
    if content.endswith('```'):
        content = content[:-3]
    
    content = content.strip()
    
    # Try to find JSON in the content
    json_start = content.find('{')
    json_end = content.rfind('}') + 1
    
    if json_start >= 0 and json_end > json_start:
        try:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Try to find array JSON
    array_start = content.find('[')
    array_end = content.rfind(']') + 1
    
    if array_start >= 0 and array_end > array_start:
        try:
            json_str = content[array_start:array_end]
            return {"entities": json.loads(json_str)}  # Wrap in expected format
        except json.JSONDecodeError:
            pass
    
    return None


def extract_entities_from_llm_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract entities from an LLM response
    
    Args:
        response: The response from UniversalModelClient
        
    Returns:
        Dictionary with entities array or error information
    """
    # Extract content
    content = extract_llm_content(response)
    
    if not content:
        return {
            "success": False,
            "error": "No content in LLM response",
            "entities": []
        }
    
    # Extract JSON
    json_data = extract_json_from_content(content)
    
    if not json_data:
        return {
            "success": False,
            "error": "Could not parse JSON from response",
            "content": content[:200] + "...",
            "entities": []
        }
    
    # Validate structure
    if "entities" not in json_data:
        # Check if the response is just an array of entities
        if isinstance(json_data, list):
            json_data = {"entities": json_data}
        else:
            return {
                "success": False,
                "error": "Response missing 'entities' field",
                "parsed_data": json_data,
                "entities": []
            }
    
    return {
        "success": True,
        "entities": json_data["entities"],
        "entity_count": len(json_data["entities"])
    }


def extract_full_llm_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract full structured data from an LLM response (entities, codes, relationships, etc.)
    
    Args:
        response: The response from UniversalModelClient
        
    Returns:
        Dictionary with all extracted data or error information
    """
    # Extract content
    content = extract_llm_content(response)
    
    if not content:
        return {
            "success": False,
            "error": "No content in LLM response",
            "data": {}
        }
    
    # Extract JSON
    json_data = extract_json_from_content(content)
    
    if not json_data:
        return {
            "success": False,
            "error": "Could not parse JSON from response",
            "content": content[:500] + "...",
            "data": {}
        }
    
    return {
        "success": True,
        "data": json_data,
        "entities": json_data.get("entities", []),
        "codes": json_data.get("codes", []),
        "relationships": json_data.get("relationships", [])
    }


# Test the helper functions
if __name__ == "__main__":
    # Test JSON extraction
    test_cases = [
        '{"entities": [{"name": "Test"}]}',
        '```json\n{"entities": [{"name": "Test"}]}\n```',
        'Here is the JSON: {"entities": [{"name": "Test"}]} end of response',
        '[{"name": "Test"}]',
        'Random text before {"entities": [{"name": "Test"}]} and after'
    ]
    
    print("Testing JSON extraction:")
    print("-" * 40)
    
    for i, test in enumerate(test_cases):
        result = extract_json_from_content(test)
        print(f"Test {i+1}: {'[OK]' if result else '[FAIL]'} - {result}")
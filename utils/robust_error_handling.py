"""
Robust Error Handling System for Phase 2.1
Handles real-world errors, malformed data, and edge cases
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import re
import traceback

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    LOW = "low"           # Continue processing with fallback
    MEDIUM = "medium"     # Warn user but continue
    HIGH = "high"         # Stop current operation, try recovery
    CRITICAL = "critical" # Stop all processing


class ErrorType(Enum):
    LLM_TIMEOUT = "llm_timeout"
    LLM_MALFORMED_JSON = "llm_malformed_json"
    LLM_EMPTY_RESPONSE = "llm_empty_response"
    NEO4J_CONNECTION = "neo4j_connection"
    NEO4J_QUERY_ERROR = "neo4j_query_error"
    SCHEMA_VALIDATION = "schema_validation"
    DATA_CORRUPTION = "data_corruption"
    TOKEN_LIMIT_EXCEEDED = "token_limit_exceeded"
    PARSING_ERROR = "parsing_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorDetails:
    """Detailed error information"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any]
    suggested_action: str
    recovery_attempted: bool = False
    recovery_successful: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass
class OperationResult:
    """Result wrapper with error handling"""
    success: bool
    data: Any = None
    errors: List[ErrorDetails] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error_type: ErrorType, severity: ErrorSeverity, 
                  message: str, context: Dict[str, Any] = None, 
                  suggested_action: str = ""):
        """Add error to result"""
        error = ErrorDetails(
            error_type=error_type,
            severity=severity,
            message=message,
            context=context or {},
            suggested_action=suggested_action
        )
        self.errors.append(error)
        
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.success = False
    
    def add_warning(self, message: str):
        """Add warning to result"""
        self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """Check if result has any errors"""
        return len(self.errors) > 0
    
    def has_critical_errors(self) -> bool:
        """Check if result has critical errors"""
        return any(e.severity == ErrorSeverity.CRITICAL for e in self.errors)


class RobustJSONParser:
    """Handles malformed JSON from LLM responses"""
    
    @staticmethod
    def parse_json_with_fallbacks(content: str) -> OperationResult:
        """Parse JSON with multiple fallback strategies"""
        result = OperationResult(success=False)
        
        if not content or not content.strip():
            result.add_error(
                ErrorType.LLM_EMPTY_RESPONSE,
                ErrorSeverity.HIGH,
                "LLM returned empty response",
                {"content": content},
                "Retry with different prompt or model"
            )
            return result
        
        # Strategy 1: Direct JSON parsing
        try:
            data = json.loads(content)
            result.success = True
            result.data = data
            return result
        except json.JSONDecodeError as e:
            result.add_warning(f"Direct JSON parsing failed: {e}")
        
        # Strategy 2: Extract JSON from markdown blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                data = json.loads(match)
                result.success = True
                result.data = data
                result.add_warning("Extracted JSON from markdown block")
                return result
            except json.JSONDecodeError:
                continue
        
        # Strategy 3: Find JSON-like objects
        json_objects = re.findall(r'\{[^{}]*\}', content)
        for obj_str in json_objects:
            try:
                data = json.loads(obj_str)
                result.success = True
                result.data = data
                result.add_warning("Extracted simple JSON object")
                return result
            except json.JSONDecodeError:
                continue
        
        # Strategy 4: Manual structure extraction
        manual_result = RobustJSONParser._extract_manual_structure(content)
        if manual_result:
            result.success = True
            result.data = manual_result
            result.add_warning("Used manual structure extraction")
            return result
        
        # All strategies failed
        result.add_error(
            ErrorType.LLM_MALFORMED_JSON,
            ErrorSeverity.HIGH,
            "Could not parse JSON from LLM response",
            {"content": content[:500] + "..." if len(content) > 500 else content},
            "Check prompt format or try different model"
        )
        return result
    
    @staticmethod
    def _extract_manual_structure(content: str) -> Optional[Dict]:
        """Manual extraction for common patterns"""
        # Look for entity lists
        entity_pattern = r'(?:entity|person|organization).*?:\s*([^\n]+)'
        entities = re.findall(entity_pattern, content, re.IGNORECASE)
        
        # Look for relationship patterns
        rel_pattern = r'(\w+)\s+(?:works at|manages|collaborates with)\s+(\w+)'
        relationships = re.findall(rel_pattern, content, re.IGNORECASE)
        
        if entities or relationships:
            return {
                "entities": [{"name": e.strip(), "type": "Unknown"} for e in entities],
                "relationships": [{"source": r[0], "target": r[1], "type": "RELATED_TO"} 
                               for r in relationships]
            }
        
        return None


class RobustLLMClient:
    """LLM client with comprehensive error handling"""
    
    def __init__(self, base_client):
        self.base_client = base_client
        self.max_retries = 3
        self.retry_delay = 2.0
        self.json_parser = RobustJSONParser()
    
    async def complete_with_retry(self, messages: List[Dict], 
                                max_tokens: int = 4000,
                                temperature: float = 0.1) -> OperationResult:
        """Complete with comprehensive error handling and retries"""
        result = OperationResult(success=False)
        
        for attempt in range(self.max_retries):
            try:
                # Attempt LLM call
                response = self.base_client.complete(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Extract content
                content = self._extract_content(response)
                if not content:
                    result.add_error(
                        ErrorType.LLM_EMPTY_RESPONSE,
                        ErrorSeverity.MEDIUM,
                        f"Empty response on attempt {attempt + 1}",
                        {"attempt": attempt + 1},
                        "Retry with different parameters"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                
                # Try to parse as JSON
                json_result = self.json_parser.parse_json_with_fallbacks(content)
                if json_result.success:
                    result.success = True
                    result.data = json_result.data
                    result.warnings.extend(json_result.warnings)
                    result.metadata["attempts"] = attempt + 1
                    result.metadata["raw_content"] = content
                    return result
                else:
                    # JSON parsing failed, but we have content
                    result.errors.extend(json_result.errors)
                    if attempt < self.max_retries - 1:
                        result.add_warning(f"JSON parsing failed on attempt {attempt + 1}, retrying")
                        await asyncio.sleep(self.retry_delay)
                        continue
                
            except Exception as e:
                error_msg = f"LLM call failed on attempt {attempt + 1}: {str(e)}"
                result.add_error(
                    ErrorType.LLM_TIMEOUT if "timeout" in str(e).lower() else ErrorType.UNKNOWN_ERROR,
                    ErrorSeverity.MEDIUM if attempt < self.max_retries - 1 else ErrorSeverity.HIGH,
                    error_msg,
                    {"attempt": attempt + 1, "exception": str(e)},
                    "Check network connection and model availability"
                )
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    continue
        
        # All retries failed
        result.add_error(
            ErrorType.LLM_TIMEOUT,
            ErrorSeverity.CRITICAL,
            f"LLM failed after {self.max_retries} attempts",
            {"max_retries": self.max_retries},
            "Check service status or try later"
        )
        return result
    
    def _extract_content(self, response) -> Optional[str]:
        """Extract content from various response formats"""
        if hasattr(response, 'choices') and response.choices:
            if hasattr(response.choices[0], 'message'):
                return response.choices[0].message.content
            elif hasattr(response.choices[0], 'text'):
                return response.choices[0].text
        
        if hasattr(response, 'content'):
            return response.content
        
        if isinstance(response, dict):
            return response.get('content') or response.get('text')
        
        if isinstance(response, str):
            return response
        
        return None


class RobustNeo4jHandler:
    """Neo4j operations with comprehensive error handling"""
    
    def __init__(self, neo4j_manager):
        self.neo4j = neo4j_manager
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def create_entity_safe(self, entity_data: Dict) -> OperationResult:
        """Create entity with error handling"""
        result = OperationResult(success=False)
        
        # Validate entity data
        validation_result = self._validate_entity_data(entity_data)
        if not validation_result.success:
            result.errors.extend(validation_result.errors)
            return result
        
        # Attempt creation with retries
        for attempt in range(self.max_retries):
            try:
                # Clean and prepare data
                clean_data = self._clean_entity_data(entity_data)
                
                # Create entity
                await self.neo4j.create_entity(clean_data)
                result.success = True
                result.data = clean_data
                result.metadata["attempts"] = attempt + 1
                return result
                
            except Exception as e:
                error_msg = f"Entity creation failed on attempt {attempt + 1}: {str(e)}"
                severity = ErrorSeverity.MEDIUM if attempt < self.max_retries - 1 else ErrorSeverity.HIGH
                
                result.add_error(
                    ErrorType.NEO4J_QUERY_ERROR,
                    severity,
                    error_msg,
                    {"attempt": attempt + 1, "entity_data": entity_data, "exception": str(e)},
                    "Check Neo4j connection and data format"
                )
                
                # Check if it's a connection error
                if "connection" in str(e).lower() or "timeout" in str(e).lower():
                    result.errors[-1].error_type = ErrorType.NEO4J_CONNECTION
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
        
        return result
    
    def _validate_entity_data(self, entity_data: Dict) -> OperationResult:
        """Validate entity data before creation"""
        result = OperationResult(success=True)
        
        # Required fields
        required_fields = ['id', 'name', 'entity_type']
        for field in required_fields:
            if field not in entity_data:
                result.add_error(
                    ErrorType.SCHEMA_VALIDATION,
                    ErrorSeverity.HIGH,
                    f"Missing required field: {field}",
                    {"entity_data": entity_data},
                    f"Add {field} field to entity data"
                )
        
        # Data type validation
        if 'properties' in entity_data and not isinstance(entity_data['properties'], dict):
            result.add_error(
                ErrorType.SCHEMA_VALIDATION,
                ErrorSeverity.MEDIUM,
                "Properties must be a dictionary",
                {"properties_type": type(entity_data['properties'])},
                "Ensure properties is a dict object"
            )
        
        return result
    
    def _clean_entity_data(self, entity_data: Dict) -> Dict:
        """Clean and prepare entity data"""
        from neo4j_v2 import EntityNode
        
        # Extract and clean fields
        entity_id = str(entity_data.get('id', 'unknown'))
        name = str(entity_data.get('name', 'Unknown'))
        entity_type = str(entity_data.get('entity_type', 'Entity')).replace('/', '_').replace(' ', '_')
        properties = entity_data.get('properties', {})
        
        # Ensure properties is dict and clean values
        if not isinstance(properties, dict):
            properties = {}
        
        # Clean property values
        clean_properties = {}
        for key, value in properties.items():
            if isinstance(value, (str, int, float, bool)):
                clean_properties[str(key)] = value
            elif value is None:
                continue  # Skip None values
            else:
                clean_properties[str(key)] = str(value)
        
        return EntityNode(
            id=entity_id,
            name=name,
            entity_type=entity_type,
            properties=clean_properties
        )


# Test the robust error handling system
async def test_error_handling():
    """Test comprehensive error handling capabilities"""
    print("=== ROBUST ERROR HANDLING TEST ===")
    print("=" * 35)
    
    # Test 1: JSON parsing with malformed data
    print("\n1. Testing JSON parsing with malformed data...")
    
    test_cases = [
        "",  # Empty
        "Invalid JSON content",  # No JSON
        '{"entities": [{"name": "test"}}',  # Malformed JSON
        '```json\n{"entities": [{"name": "Dr. Smith"}]}\n```',  # Markdown wrapped
        'Here are the entities: {"entities": [{"name": "Bob"}]} and more text',  # Mixed content
    ]
    
    parser = RobustJSONParser()
    for i, test_case in enumerate(test_cases):
        print(f"\n   Test case {i+1}: '{test_case[:50]}...'")
        result = parser.parse_json_with_fallbacks(test_case)
        
        print(f"   Success: {result.success}")
        if result.success:
            print(f"   Data: {result.data}")
        if result.warnings:
            print(f"   Warnings: {result.warnings}")
        if result.errors:
            print(f"   Errors: {[e.message for e in result.errors]}")
    
    # Test 2: Entity validation
    print("\n2. Testing entity data validation...")
    
    from universal_model_client import UniversalModelClient
    from neo4j_v2 import EnhancedNeo4jManager
    
    neo4j = EnhancedNeo4jManager(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="changeme123"
    )
    await neo4j.connect()
    
    robust_neo4j = RobustNeo4jHandler(neo4j)
    
    invalid_entities = [
        {},  # Empty
        {"name": "Test"},  # Missing ID and type
        {"id": "test", "name": "Test", "entity_type": "Person", "properties": "invalid"},  # Invalid properties
        {"id": "test", "name": "Test", "entity_type": "Person", "properties": {"valid": "data"}},  # Valid
    ]
    
    for i, entity_data in enumerate(invalid_entities):
        print(f"\n   Entity test {i+1}: {entity_data}")
        result = await robust_neo4j.create_entity_safe(entity_data)
        
        print(f"   Success: {result.success}")
        if result.errors:
            for error in result.errors:
                print(f"   Error: {error.message} (Severity: {error.severity.value})")
        if result.warnings:
            print(f"   Warnings: {result.warnings}")
    
    await neo4j.close()
    
    print("\n" + "=" * 35)
    print("ERROR HANDLING TEST COMPLETE")
    print("=" * 35)


if __name__ == "__main__":
    asyncio.run(test_error_handling())
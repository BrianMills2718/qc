# Evidence: AI Query Generation Quality Assessment

**Assessment Date**: 2025-09-10 06:15:45
**Total Tests**: 80
**Successful Tests**: 0
**Overall Success Rate**: 0.0%

## Executive Summary

DO NOT PROCEED - AI quality insufficient for research use (syntactic: 0.0%, best semantic: 0.0%)

## Detailed Results

### Syntactic Correctness Rates
```json
{
  "openai_direct": 0.0,
  "openai_schema_aware": 0.0,
  "anthropic_direct": 0.0,
  "anthropic_schema_aware": 0.0
}
```

### Semantic Accuracy by Complexity
```json
{
  "openai_direct": {
    "simple": 0.0,
    "moderate": 0.0,
    "complex": 0.0
  },
  "openai_schema_aware": {
    "simple": 0.0,
    "moderate": 0.0,
    "complex": 0.0
  },
  "anthropic_direct": {
    "simple": 0.0,
    "moderate": 0.0,
    "complex": 0.0
  },
  "anthropic_schema_aware": {
    "simple": 0.0,
    "moderate": 0.0,
    "complex": 0.0
  }
}
```

### Provider Comparison
```json
{
  "openai": {
    "syntactic_correctness": 0.0,
    "semantic_quality": 0.0,
    "avg_time_ms": 0.5142688751220703
  },
  "anthropic": {
    "syntactic_correctness": 0.0,
    "semantic_quality": 0.0,
    "avg_time_ms": 0.9992122650146484
  }
}
```

### Performance Characteristics
```json
{
  "openai_direct": {
    "mean_time_ms": 0.5159378051757812,
    "median_time_ms": 0.5159378051757812,
    "max_time_ms": 0.518798828125
  },
  "openai_schema_aware": {
    "mean_time_ms": 0.5109310150146484,
    "median_time_ms": 0.5109310150146484,
    "max_time_ms": 0.5109310150146484
  },
  "anthropic_direct": {
    "mean_time_ms": 0.9984970092773438,
    "median_time_ms": 0.9984970092773438,
    "max_time_ms": 0.9984970092773438
  },
  "anthropic_schema_aware": {
    "mean_time_ms": 0.9999275207519531,
    "median_time_ms": 0.9999275207519531,
    "max_time_ms": 0.9999275207519531
  }
}
```

### Error Patterns
```json
{
  "openai_direct": [
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query"
  ],
  "openai_schema_aware": [
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query"
  ],
  "anthropic_direct": [
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query"
  ],
  "anthropic_schema_aware": [
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query",
    "Failed to generate query"
  ]
}
```

## Complete Test Results
```json
{
  "openai_direct": [
    {
      "question": "What do senior people say about AI?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.5130767822265625,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show me all organizations",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Find quotes about innovation",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "List all people in the dataset",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show me themes about technology",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "What are the main codes?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Find all interviews",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show organizations by size",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Which people work at large organizations?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do different roles view automation?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "What themes connect across interviews?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Which people discuss similar topics?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.518798828125,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do senior staff view change management?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "What do people from small organizations say about efficiency?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Which themes appear most frequently by division?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do public sector views differ from private?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Find people who bridge different conceptual areas",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Show sentiment patterns by organizational role",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Identify conceptual evolution across time",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Which people influence cross-divisional thinking?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    }
  ],
  "openai_schema_aware": [
    {
      "question": "What do senior people say about AI?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show me all organizations",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Find quotes about innovation",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "List all people in the dataset",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.5109310150146484,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show me themes about technology",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "What are the main codes?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Find all interviews",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show organizations by size",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Which people work at large organizations?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do different roles view automation?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "What themes connect across interviews?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Which people discuss similar topics?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do senior staff view change management?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "What do people from small organizations say about efficiency?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Which themes appear most frequently by division?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do public sector views differ from private?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Find people who bridge different conceptual areas",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Show sentiment patterns by organizational role",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Identify conceptual evolution across time",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Which people influence cross-divisional thinking?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    }
  ],
  "anthropic_direct": [
    {
      "question": "What do senior people say about AI?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show me all organizations",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Find quotes about innovation",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "List all people in the dataset",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show me themes about technology",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "What are the main codes?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Find all interviews",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show organizations by size",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Which people work at large organizations?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do different roles view automation?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.9984970092773438,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "What themes connect across interviews?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Which people discuss similar topics?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do senior staff view change management?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "What do people from small organizations say about efficiency?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Which themes appear most frequently by division?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do public sector views differ from private?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Find people who bridge different conceptual areas",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Show sentiment patterns by organizational role",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Identify conceptual evolution across time",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Which people influence cross-divisional thinking?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    }
  ],
  "anthropic_schema_aware": [
    {
      "question": "What do senior people say about AI?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show me all organizations",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Find quotes about innovation",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "List all people in the dataset",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show me themes about technology",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "What are the main codes?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Find all interviews",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Show organizations by size",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "simple"
    },
    {
      "question": "Which people work at large organizations?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do different roles view automation?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "What themes connect across interviews?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Which people discuss similar topics?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do senior staff view change management?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "What do people from small organizations say about efficiency?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Which themes appear most frequently by division?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "How do public sector views differ from private?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.9999275207519531,
      "error": "Failed to generate query",
      "complexity_level": "moderate"
    },
    {
      "question": "Find people who bridge different conceptual areas",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Show sentiment patterns by organizational role",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Identify conceptual evolution across time",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    },
    {
      "question": "Which people influence cross-divisional thinking?",
      "generated_cypher": null,
      "syntactic_correct": false,
      "semantic_quality": 0.0,
      "execution_time_ms": 0.0,
      "error": "Failed to generate query",
      "complexity_level": "complex"
    }
  ]
}
```

## Methodology

- **Test Corpus**: 20 research questions across 3 complexity levels
- **Providers Tested**: openai, anthropic
- **Strategies Tested**: direct, schema_aware
- **Evaluation Criteria**: 
  - Syntactic Correctness: Valid Cypher syntax
  - Semantic Quality: Automated heuristic scoring (0.0-1.0)
  - Performance: Query generation time

## Quality Thresholds

- **Success Threshold**: >85% syntactic correctness, >70% semantic accuracy
- **Proceed Threshold**: 0/80 = 0.0%
- **Recommendation**: Based on combined syntactic and semantic performance

---
*Generated by investigation_ai_quality_assessment.py*

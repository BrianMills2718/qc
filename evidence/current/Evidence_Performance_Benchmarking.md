# Evidence: Performance Benchmarking

**Benchmark Date**: 2025-09-10 05:48:53
**Total Queries**: 40
**Successful Queries**: 37
**Overall Success Rate**: 92.5%

## Executive Summary

DO NOT PROCEED - Performance inadequate for interactive use (62.2% queries <2s)

## Performance Analysis

### Performance by Complexity Level
```json
{
  "simple": {
    "times": [
      48.59410154644001,
      64.97415948016005,
      55.87523431710277,
      113.98970147920504,
      110.02162419103215,
      141.03252648738695,
      279.10815453810613,
      279.2665933593996,
      220.43974407264824,
      897.9038333787894,
      593.8414509326673,
      801.3309927655854
    ],
    "mean": 300.53150971237693,
    "median": 180.7361352800176,
    "max": 897.9038333787894
  },
  "moderate": {
    "times": [
      268.47002766884583,
      274.41397453428397,
      278.14994733897214,
      519.3052852711991,
      628.167491916981,
      599.7253260699672,
      850.4628701879801,
      1222.9110334067677,
      1097.293340338212,
      3384.7095913749254,
      2586.426959209523,
      4043.9778355231842
    ],
    "mean": 1312.83447357007,
    "median": 739.3151810524805,
    "max": 4043.9778355231842
  },
  "complex": {
    "times": [
      697.1286987925654,
      1057.90031367064,
      2795.179626477439,
      2272.762750035767,
      4593.258429048772,
      3807.8331363466473,
      15293.06357966006,
      15630.709286319387
    ],
    "mean": 5768.4794775439095,
    "median": 3301.506381412043,
    "max": 15630.709286319387
  },
  "pathological": {
    "times": [
      6301.9040975142,
      5451.820300552766,
      14971.288644020933,
      39848.78947175278,
      39970.50298249102
    ],
    "mean": 21308.86109926634,
    "median": 14971.288644020933,
    "max": 39970.50298249102
  }
}
```

### User Experience Impact
```json
{
  "excellent": 6,
  "acceptable": 17,
  "problematic": 9,
  "unacceptable": 5
}
```

### Scalability Trends
```json
{
  "find_people": [
    [
      "small",
      48.59410154644001
    ],
    [
      "medium",
      113.98970147920504
    ],
    [
      "large",
      279.10815453810613
    ],
    [
      "xl",
      897.9038333787894
    ]
  ],
  "find_senior_people": [
    [
      "small",
      64.97415948016005
    ],
    [
      "medium",
      110.02162419103215
    ],
    [
      "large",
      279.2665933593996
    ],
    [
      "xl",
      593.8414509326673
    ]
  ],
  "organization_list": [
    [
      "small",
      55.87523431710277
    ],
    [
      "medium",
      141.03252648738695
    ],
    [
      "large",
      220.43974407264824
    ],
    [
      "xl",
      801.3309927655854
    ]
  ],
  "people_topics": [
    [
      "small",
      268.47002766884583
    ],
    [
      "medium",
      519.3052852711991
    ],
    [
      "large",
      850.4628701879801
    ],
    [
      "xl",
      3384.7095913749254
    ]
  ],
  "org_people_count": [
    [
      "small",
      274.41397453428397
    ],
    [
      "medium",
      628.167491916981
    ],
    [
      "large",
      1222.9110334067677
    ],
    [
      "xl",
      2586.426959209523
    ]
  ],
  "cross_division_themes": [
    [
      "small",
      278.14994733897214
    ],
    [
      "medium",
      599.7253260699672
    ],
    [
      "large",
      1097.293340338212
    ],
    [
      "xl",
      4043.9778355231842
    ]
  ],
  "conceptual_bridges": [
    [
      "small",
      697.1286987925654
    ],
    [
      "medium",
      2795.179626477439
    ],
    [
      "large",
      4593.258429048772
    ],
    [
      "xl",
      15293.06357966006
    ]
  ],
  "influence_networks": [
    [
      "small",
      1057.90031367064
    ],
    [
      "medium",
      2272.762750035767
    ],
    [
      "large",
      3807.8331363466473
    ],
    [
      "xl",
      15630.709286319387
    ]
  ],
  "unbounded_traversal": [
    [
      "small",
      6301.9040975142
    ],
    [
      "large",
      39848.78947175278
    ]
  ],
  "cartesian_product": [
    [
      "small",
      5451.820300552766
    ],
    [
      "medium",
      14971.288644020933
    ],
    [
      "large",
      39970.50298249102
    ]
  ]
}
```

### Problematic Queries
```json
[
  [
    "medium",
    "unbounded_traversal",
    "Query timeout or memory limit exceeded"
  ],
  [
    "xl",
    "unbounded_traversal",
    "Query timeout or memory limit exceeded"
  ],
  [
    "xl",
    "cartesian_product",
    "Query timeout or memory limit exceeded"
  ]
]
```

## Dataset Specifications

### Synthetic Datasets
```json
[
  {
    "name": "small",
    "interviews": 100,
    "nodes": 10000,
    "relationships": 50000,
    "description": "Small research project"
  },
  {
    "name": "medium",
    "interviews": 500,
    "nodes": 50000,
    "relationships": 250000,
    "description": "Medium longitudinal study"
  },
  {
    "name": "large",
    "interviews": 2000,
    "nodes": 200000,
    "relationships": 1000000,
    "description": "Large multi-site study"
  },
  {
    "name": "xl",
    "interviews": 5000,
    "nodes": 500000,
    "relationships": 2500000,
    "description": "Enterprise-scale analysis"
  }
]
```

### Query Test Suite
```json
[
  {
    "name": "find_people",
    "cypher": "MATCH (p:Person) RETURN p.name LIMIT 10",
    "complexity": "simple",
    "expected_result_count": 10,
    "description": "Basic entity retrieval"
  },
  {
    "name": "find_senior_people",
    "cypher": "MATCH (p:Person {seniority: 'senior'}) RETURN p.name LIMIT 10",
    "complexity": "simple",
    "expected_result_count": 10,
    "description": "Filtered entity retrieval"
  },
  {
    "name": "organization_list",
    "cypher": "MATCH (o:Organization) RETURN o.name, o.size ORDER BY o.name LIMIT 20",
    "complexity": "simple",
    "expected_result_count": 20,
    "description": "Basic organization listing"
  },
  {
    "name": "people_topics",
    "cypher": "MATCH (p:Person)-[:DISCUSSES]->(c:Code) RETURN p.name, count(c) as topics ORDER BY topics DESC LIMIT 10",
    "complexity": "moderate",
    "expected_result_count": 10,
    "description": "Person-topic frequency analysis"
  },
  {
    "name": "org_people_count",
    "cypher": "MATCH (p:Person)-[:WORKS_AT]->(o:Organization) RETURN o.name, count(p) as employee_count ORDER BY employee_count DESC",
    "complexity": "moderate",
    "expected_result_count": 0,
    "description": "Organization size analysis"
  },
  {
    "name": "cross_division_themes",
    "cypher": "MATCH (p1:Person)-[:DISCUSSES]->(c:Code)<-[:DISCUSSES]-(p2:Person) WHERE p1.division <> p2.division RETURN c.name, count(*) as cross_div_count ORDER BY cross_div_count DESC LIMIT 15",
    "complexity": "moderate",
    "expected_result_count": 15,
    "description": "Cross-divisional theme analysis"
  },
  {
    "name": "conceptual_bridges",
    "cypher": "MATCH (p:Person)-[:DISCUSSES]->(c:Code)\n                   WITH p, collect(DISTINCT c.name) as topics\n                   WHERE size(topics) > 3\n                   RETURN p.name, topics, size(topics) as bridge_score\n                   ORDER BY bridge_score DESC LIMIT 10",
    "complexity": "complex",
    "expected_result_count": 10,
    "description": "Cross-cutting conceptual analysis"
  },
  {
    "name": "influence_networks",
    "cypher": "MATCH (p1:Person)-[:DISCUSSES]->(c:Code)<-[:DISCUSSES]-(p2:Person)\n                   WHERE p1 <> p2\n                   WITH p1, collect(DISTINCT p2.name) as connections\n                   RETURN p1.name, size(connections) as network_size, connections\n                   ORDER BY network_size DESC LIMIT 10",
    "complexity": "complex",
    "expected_result_count": 10,
    "description": "Social influence network analysis"
  },
  {
    "name": "unbounded_traversal",
    "cypher": "MATCH (a)-[*1..10]-(b) RETURN count(*) as path_count",
    "complexity": "pathological",
    "expected_result_count": 1,
    "description": "Potentially expensive unbounded traversal"
  },
  {
    "name": "cartesian_product",
    "cypher": "MATCH (p:Person), (o:Organization) RETURN count(*) as combinations",
    "complexity": "pathological",
    "expected_result_count": 1,
    "description": "Dangerous cartesian product"
  }
]
```

## Complete Benchmark Results
```json
{
  "small": [
    {
      "dataset": "small",
      "query": "find_people",
      "execution_time_ms": 48.59410154644001,
      "memory_usage_mb": 81.94040930790257,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "small",
      "query": "find_senior_people",
      "execution_time_ms": 64.97415948016005,
      "memory_usage_mb": 53.74762089548403,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "small",
      "query": "organization_list",
      "execution_time_ms": 55.87523431710277,
      "memory_usage_mb": 32.95496405677909,
      "result_count": 20,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "small",
      "query": "people_topics",
      "execution_time_ms": 268.47002766884583,
      "memory_usage_mb": 64.11084208496938,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "small",
      "query": "org_people_count",
      "execution_time_ms": 274.41397453428397,
      "memory_usage_mb": 22.299668844967677,
      "result_count": 0,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "small",
      "query": "cross_division_themes",
      "execution_time_ms": 278.14994733897214,
      "memory_usage_mb": 65.8733005502326,
      "result_count": 15,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "small",
      "query": "conceptual_bridges",
      "execution_time_ms": 697.1286987925654,
      "memory_usage_mb": 95.98138142084957,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "small",
      "query": "influence_networks",
      "execution_time_ms": 1057.90031367064,
      "memory_usage_mb": 33.999191818308354,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "small",
      "query": "unbounded_traversal",
      "execution_time_ms": 6301.9040975142,
      "memory_usage_mb": 27.51078663474021,
      "result_count": 1,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "small",
      "query": "cartesian_product",
      "execution_time_ms": 5451.820300552766,
      "memory_usage_mb": 55.46617193388448,
      "result_count": 1,
      "success": true,
      "error_message": null
    }
  ],
  "medium": [
    {
      "dataset": "medium",
      "query": "find_people",
      "execution_time_ms": 113.98970147920504,
      "memory_usage_mb": 71.70376296671094,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "medium",
      "query": "find_senior_people",
      "execution_time_ms": 110.02162419103215,
      "memory_usage_mb": 80.44526852341765,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "medium",
      "query": "organization_list",
      "execution_time_ms": 141.03252648738695,
      "memory_usage_mb": 59.90407584940316,
      "result_count": 20,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "medium",
      "query": "people_topics",
      "execution_time_ms": 519.3052852711991,
      "memory_usage_mb": 58.56557671968857,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "medium",
      "query": "org_people_count",
      "execution_time_ms": 628.167491916981,
      "memory_usage_mb": 51.77907160468352,
      "result_count": 0,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "medium",
      "query": "cross_division_themes",
      "execution_time_ms": 599.7253260699672,
      "memory_usage_mb": 91.76685563491324,
      "result_count": 15,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "medium",
      "query": "conceptual_bridges",
      "execution_time_ms": 2795.179626477439,
      "memory_usage_mb": 48.73213274326602,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "medium",
      "query": "influence_networks",
      "execution_time_ms": 2272.762750035767,
      "memory_usage_mb": 66.6793680012865,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "medium",
      "query": "unbounded_traversal",
      "execution_time_ms": 30000,
      "memory_usage_mb": 52.52846044297806,
      "result_count": 0,
      "success": false,
      "error_message": "Query timeout or memory limit exceeded"
    },
    {
      "dataset": "medium",
      "query": "cartesian_product",
      "execution_time_ms": 14971.288644020933,
      "memory_usage_mb": 98.91760635986405,
      "result_count": 1,
      "success": true,
      "error_message": null
    }
  ],
  "large": [
    {
      "dataset": "large",
      "query": "find_people",
      "execution_time_ms": 279.10815453810613,
      "memory_usage_mb": 40.91884401696757,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "large",
      "query": "find_senior_people",
      "execution_time_ms": 279.2665933593996,
      "memory_usage_mb": 64.18443528849237,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "large",
      "query": "organization_list",
      "execution_time_ms": 220.43974407264824,
      "memory_usage_mb": 76.76896885572097,
      "result_count": 20,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "large",
      "query": "people_topics",
      "execution_time_ms": 850.4628701879801,
      "memory_usage_mb": 32.54533479706744,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "large",
      "query": "org_people_count",
      "execution_time_ms": 1222.9110334067677,
      "memory_usage_mb": 75.47638374073864,
      "result_count": 0,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "large",
      "query": "cross_division_themes",
      "execution_time_ms": 1097.293340338212,
      "memory_usage_mb": 41.571174949531965,
      "result_count": 15,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "large",
      "query": "conceptual_bridges",
      "execution_time_ms": 4593.258429048772,
      "memory_usage_mb": 27.541874511407517,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "large",
      "query": "influence_networks",
      "execution_time_ms": 3807.8331363466473,
      "memory_usage_mb": 86.40648842974625,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "large",
      "query": "unbounded_traversal",
      "execution_time_ms": 39848.78947175278,
      "memory_usage_mb": 56.332872762225094,
      "result_count": 1,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "large",
      "query": "cartesian_product",
      "execution_time_ms": 39970.50298249102,
      "memory_usage_mb": 96.47094598645091,
      "result_count": 1,
      "success": true,
      "error_message": null
    }
  ],
  "xl": [
    {
      "dataset": "xl",
      "query": "find_people",
      "execution_time_ms": 897.9038333787894,
      "memory_usage_mb": 91.40072150840919,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "xl",
      "query": "find_senior_people",
      "execution_time_ms": 593.8414509326673,
      "memory_usage_mb": 99.7714501390548,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "xl",
      "query": "organization_list",
      "execution_time_ms": 801.3309927655854,
      "memory_usage_mb": 56.37290975583307,
      "result_count": 20,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "xl",
      "query": "people_topics",
      "execution_time_ms": 3384.7095913749254,
      "memory_usage_mb": 45.42356502367728,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "xl",
      "query": "org_people_count",
      "execution_time_ms": 2586.426959209523,
      "memory_usage_mb": 92.44375195229,
      "result_count": 0,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "xl",
      "query": "cross_division_themes",
      "execution_time_ms": 4043.9778355231842,
      "memory_usage_mb": 83.99421785770713,
      "result_count": 15,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "xl",
      "query": "conceptual_bridges",
      "execution_time_ms": 15293.06357966006,
      "memory_usage_mb": 75.21037840112011,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "xl",
      "query": "influence_networks",
      "execution_time_ms": 15630.709286319387,
      "memory_usage_mb": 56.387663363161586,
      "result_count": 10,
      "success": true,
      "error_message": null
    },
    {
      "dataset": "xl",
      "query": "unbounded_traversal",
      "execution_time_ms": 30000,
      "memory_usage_mb": 20.018537325483322,
      "result_count": 0,
      "success": false,
      "error_message": "Query timeout or memory limit exceeded"
    },
    {
      "dataset": "xl",
      "query": "cartesian_product",
      "execution_time_ms": 30000,
      "memory_usage_mb": 55.29404295979285,
      "result_count": 0,
      "success": false,
      "error_message": "Query timeout or memory limit exceeded"
    }
  ]
}
```

## Performance Thresholds

### User Experience Categories
- **Excellent**: <200ms (immediate response)
- **Acceptable**: 200-2000ms (good interactive experience)  
- **Problematic**: 2-10 seconds (noticeable delay)
- **Unacceptable**: >10 seconds (poor user experience)

### Success Criteria
- **Target**: >90% of queries complete in <2 seconds on medium dataset
- **Actual**: 23/37 = 62.2% good performance

## Methodology

### Benchmark Framework
- **4 Dataset Sizes**: Small (100 interviews) → XL (5000 interviews)
- **10 Query Types**: Simple (3) → Pathological (2)
- **Performance Metrics**: Execution time, result count, success rate

### Dataset Generation
- **Entities**: Person, Organization, Code (synthetic research data)
- **Relationships**: WORKS_AT, DISCUSSES (realistic distribution)
- **Scale Factor**: 10:1:20 ratio (people:orgs:codes)

### Limitations
- **Synthetic Data**: May not reflect real-world query patterns
- **Single Environment**: Performance varies by hardware/network
- **Mock Neo4j**: Evidence generated with synthetic results where Neo4j unavailable

---
*Generated by investigation_performance_benchmarking.py*

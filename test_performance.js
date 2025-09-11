/**
 * Performance and Stress Testing for Natural Language Query System
 * Tests response times, concurrency, and system limits
 */

const BASE_URL = 'http://127.0.0.1:8002';

// Test queries of varying complexity
const PERFORMANCE_QUERIES = [
    {
        category: 'Simple',
        queries: [
            'Show me all people',
            'List organizations',
            'Display codes'
        ],
        targetTime: 2000  // ms
    },
    {
        category: 'Medium',
        queries: [
            'Find people who work at large organizations',
            'Show senior staff members',
            'Which codes appear most frequently'
        ],
        targetTime: 2500  // ms
    },
    {
        category: 'Complex',
        queries: [
            'Find senior researchers in large organizations with high confidence codes',
            'Show the relationship between people, their organizations, and the codes they discuss',
            'Identify patterns in how different seniority levels discuss various organizational topics'
        ],
        targetTime: 3500  // ms
    }
];

async function runPerformanceTests() {
    console.log('⚡ Performance Testing Starting...');
    console.log('=' .repeat(50));
    
    const results = {
        total: 0,
        passed: 0,
        failed: 0,
        tests: [],
        metrics: {
            totalRequests: 0,
            totalTime: 0,
            averageTime: 0,
            minTime: Infinity,
            maxTime: 0,
            timeouts: 0,
            errors: 0
        }
    };

    // Test 1: Single Request Performance
    for (const category of PERFORMANCE_QUERIES) {
        await runPerformanceCategory(results, category);
    }

    // Test 2: Concurrent Request Performance
    await runConcurrencyTest(results);

    // Test 3: Sustained Load Performance
    await runSustainedLoadTest(results);

    // Test 4: Memory and Resource Usage
    await runResourceTest(results);

    // Summary
    console.log('\n' + '=' .repeat(50));
    console.log('⚡ Performance Test Results');
    console.log('=' .repeat(50));
    console.log(`✅ Total Tests: ${results.total}`);
    console.log(`✅ Passed: ${results.passed}`);
    console.log(`❌ Failed: ${results.failed}`);
    console.log(`📊 Success Rate: ${((results.passed / results.total) * 100).toFixed(1)}%`);
    
    // Performance metrics
    if (results.metrics.totalRequests > 0) {
        results.metrics.averageTime = results.metrics.totalTime / results.metrics.totalRequests;
        
        console.log('\n📈 Performance Metrics:');
        console.log(`  Total Requests: ${results.metrics.totalRequests}`);
        console.log(`  Average Response Time: ${results.metrics.averageTime.toFixed(0)}ms`);
        console.log(`  Min Response Time: ${results.metrics.minTime}ms`);
        console.log(`  Max Response Time: ${results.metrics.maxTime}ms`);
        console.log(`  Timeouts: ${results.metrics.timeouts}`);
        console.log(`  Errors: ${results.metrics.errors}`);
        
        // Performance rating
        let rating = 'EXCELLENT';
        if (results.metrics.averageTime > 3000) rating = 'POOR';
        else if (results.metrics.averageTime > 2000) rating = 'FAIR';
        else if (results.metrics.averageTime > 1500) rating = 'GOOD';
        
        console.log(`  Performance Rating: ${rating}`);
    }
    
    if (results.failed > 0) {
        console.log('\n❌ Failed Tests:');
        results.tests.filter(t => !t.passed).forEach(test => {
            console.log(`  - ${test.name}: ${test.error}`);
        });
        
        console.log('\n🚨 Performance testing FAILED');
        process.exit(1);
    } else {
        console.log('\n🎉 All performance tests PASSED!');
        console.log('⚡ System performance meets requirements');
        process.exit(0);
    }
}

async function runPerformanceCategory(results, category) {
    await runPerformanceTest(results, `${category.category} Queries Performance`, async () => {
        const times = [];
        let slowQueries = [];
        
        for (const query of category.queries) {
            const startTime = Date.now();
            
            try {
                const response = await fetch(`${BASE_URL}/api/query/natural-language`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Origin': BASE_URL
                    },
                    body: JSON.stringify({ query, context: {} })
                });
                
                if (response.status !== 200) {
                    results.metrics.errors++;
                    throw new Error(`HTTP ${response.status} for "${query}"`);
                }
                
                const data = await response.json();
                if (!data.success) {
                    results.metrics.errors++;
                    throw new Error(`Query failed: "${query}" - ${data.error}`);
                }
                
                const responseTime = Date.now() - startTime;
                times.push(responseTime);
                
                // Track metrics
                results.metrics.totalRequests++;
                results.metrics.totalTime += responseTime;
                results.metrics.minTime = Math.min(results.metrics.minTime, responseTime);
                results.metrics.maxTime = Math.max(results.metrics.maxTime, responseTime);
                
                if (responseTime > category.targetTime) {
                    slowQueries.push({ query, time: responseTime });
                }
                
            } catch (error) {
                results.metrics.errors++;
                throw error;
            }
        }
        
        const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
        const maxTime = Math.max(...times);
        
        if (slowQueries.length > 0) {
            throw new Error(`${slowQueries.length} queries exceeded ${category.targetTime}ms target (max: ${maxTime}ms)`);
        }
        
        return `Avg: ${avgTime.toFixed(0)}ms, Max: ${maxTime}ms, Target: <${category.targetTime}ms`;
    });
}

async function runConcurrencyTest(results) {
    await runPerformanceTest(results, 'Concurrent Request Handling', async () => {
        const concurrency = 5;
        const testQuery = 'Show me all people';
        const promises = [];
        
        for (let i = 0; i < concurrency; i++) {
            promises.push(fetch(`${BASE_URL}/api/query/natural-language`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Origin': BASE_URL
                },
                body: JSON.stringify({ query: testQuery, context: {} })
            }));
        }
        
        const startTime = Date.now();
        const responses = await Promise.all(promises);
        const totalTime = Date.now() - startTime;
        
        // Validate all responses
        let successCount = 0;
        for (const response of responses) {
            if (response.status === 200) {
                const data = await response.json();
                if (data.success) successCount++;
            }
        }
        
        results.metrics.totalRequests += concurrency;
        results.metrics.totalTime += totalTime;
        
        if (successCount !== concurrency) {
            throw new Error(`Only ${successCount}/${concurrency} concurrent requests succeeded`);
        }
        
        const avgTimePerRequest = totalTime / concurrency;
        if (avgTimePerRequest > 4000) {  // Allow more time for concurrent requests
            throw new Error(`Concurrent requests too slow: ${avgTimePerRequest}ms average`);
        }
        
        return `${concurrency} requests in ${totalTime}ms (${avgTimePerRequest.toFixed(0)}ms avg)`;
    });
}

async function runSustainedLoadTest(results) {
    await runPerformanceTest(results, 'Sustained Load Performance', async () => {
        const duration = 10000;  // 10 seconds
        const interval = 500;    // Request every 500ms
        const testQuery = 'Show me all people';
        
        const startTime = Date.now();
        const times = [];
        let requestCount = 0;
        let errorCount = 0;
        
        while (Date.now() - startTime < duration) {
            try {
                const requestStart = Date.now();
                
                const response = await fetch(`${BASE_URL}/api/query/natural-language`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Origin': BASE_URL
                    },
                    body: JSON.stringify({ query: testQuery, context: {} })
                });
                
                if (response.status === 200) {
                    const data = await response.json();
                    if (data.success) {
                        times.push(Date.now() - requestStart);
                    } else {
                        errorCount++;
                    }
                } else {
                    errorCount++;
                }
                
                requestCount++;
                results.metrics.totalRequests++;
                
                // Wait for next interval
                const elapsed = Date.now() - requestStart;
                if (elapsed < interval) {
                    await new Promise(resolve => setTimeout(resolve, interval - elapsed));
                }
                
            } catch (error) {
                errorCount++;
                results.metrics.errors++;
            }
        }
        
        if (times.length === 0) {
            throw new Error('No successful requests during sustained load test');
        }
        
        const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
        const successRate = ((requestCount - errorCount) / requestCount) * 100;
        
        results.metrics.totalTime += times.reduce((a, b) => a + b, 0);
        
        if (successRate < 95) {
            throw new Error(`Success rate too low: ${successRate.toFixed(1)}%`);
        }
        
        if (avgTime > 3000) {
            throw new Error(`Sustained load performance degraded: ${avgTime}ms average`);
        }
        
        return `${requestCount} requests, ${successRate.toFixed(1)}% success, ${avgTime.toFixed(0)}ms avg`;
    });
}

async function runResourceTest(results) {
    await runPerformanceTest(results, 'Resource Usage Validation', async () => {
        // Test large query processing
        const largeQuery = 'Find all relationships between senior people in large organizations who discuss codes with high confidence levels and work in research divisions with complex organizational structures';
        
        const startTime = Date.now();
        
        const response = await fetch(`${BASE_URL}/api/query/natural-language`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': BASE_URL
            },
            body: JSON.stringify({ query: largeQuery, context: {} })
        });
        
        const responseTime = Date.now() - startTime;
        
        if (response.status !== 200) {
            throw new Error(`Large query failed: HTTP ${response.status}`);
        }
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(`Large query processing failed: ${data.error}`);
        }
        
        results.metrics.totalRequests++;
        results.metrics.totalTime += responseTime;
        results.metrics.minTime = Math.min(results.metrics.minTime, responseTime);
        results.metrics.maxTime = Math.max(results.metrics.maxTime, responseTime);
        
        // Should handle large queries within reasonable time
        if (responseTime > 5000) {
            throw new Error(`Large query too slow: ${responseTime}ms`);
        }
        
        return `Large query processed in ${responseTime}ms`;
    });
}

async function runPerformanceTest(results, name, testFn) {
    results.total++;
    process.stdout.write(`⚡ ${name}... `);
    
    try {
        const startTime = Date.now();
        const result = await testFn();
        const duration = Date.now() - startTime;
        
        results.passed++;
        results.tests.push({ name, passed: true, result, duration });
        
        console.log(`✅ (${duration}ms)`);
        if (result) {
            console.log(`   ${result}`);
        }
    } catch (error) {
        results.failed++;
        results.tests.push({ name, passed: false, error: error.message });
        
        console.log(`❌ ${error.message}`);
    }
}

// Check if fetch is available
if (typeof fetch === 'undefined') {
    console.error('❌ fetch not available. Please use Node.js 18+ or install node-fetch');
    process.exit(1);
}

// Run performance tests
runPerformanceTests().catch(console.error);
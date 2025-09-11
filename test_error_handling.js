/**
 * Comprehensive Error Handling Validation Test
 * Tests various error scenarios and edge cases to ensure graceful failure handling
 */

const BASE_URL = 'http://127.0.0.1:8002';

// Comprehensive error test scenarios
const ERROR_SCENARIOS = [
    {
        category: 'Input Validation',
        tests: [
            {
                name: 'Empty Query',
                payload: { query: '', context: {} },
                expectation: 'graceful_handling'
            },
            {
                name: 'Whitespace Only Query',
                payload: { query: '   \t\n   ', context: {} },
                expectation: 'graceful_handling'
            },
            {
                name: 'Null Query',
                payload: { query: null, context: {} },
                expectation: 'error_response'
            },
            {
                name: 'Missing Query Field',
                payload: { context: {} },
                expectation: 'error_response'
            },
            {
                name: 'Invalid Context Type',
                payload: { query: 'test', context: 'invalid' },
                expectation: 'error_response'
            }
        ]
    },
    {
        category: 'Malformed Requests',
        tests: [
            {
                name: 'Invalid JSON',
                payload: '{"query": "test", invalid json}',
                expectation: 'error_response'
            },
            {
                name: 'Wrong Content Type',
                payload: { query: 'test', context: {} },
                headers: { 'Content-Type': 'text/plain' },
                expectation: 'error_response'
            },
            {
                name: 'Missing Content Type',
                payload: { query: 'test', context: {} },
                headers: {},
                expectation: 'error_response'
            }
        ]
    },
    {
        category: 'Edge Cases',
        tests: [
            {
                name: 'Very Long Query',
                payload: { 
                    query: 'Find ' + 'people '.repeat(1000) + 'in organizations',
                    context: {} 
                },
                expectation: 'graceful_handling'
            },
            {
                name: 'Special Characters Query',
                payload: { 
                    query: 'Find people with names like "John\'s & Mary\'s" with 100% confidence',
                    context: {} 
                },
                expectation: 'graceful_handling'
            },
            {
                name: 'Unicode Characters Query',
                payload: { 
                    query: 'Find people with names containing émojis 🔍 and special chars ñáéíóú',
                    context: {} 
                },
                expectation: 'graceful_handling'
            },
            {
                name: 'Query with SQL Injection Attempt',
                payload: { 
                    query: "'; DROP TABLE Person; --",
                    context: {} 
                },
                expectation: 'graceful_handling'
            }
        ]
    },
    {
        category: 'HTTP Method Errors',
        tests: [
            {
                name: 'GET Method (Should be POST)',
                method: 'GET',
                endpoint: '/api/query/natural-language',
                expectation: 'method_error'
            },
            {
                name: 'PUT Method (Should be POST)',
                method: 'PUT',
                payload: { query: 'test', context: {} },
                expectation: 'method_error'
            },
            {
                name: 'DELETE Method (Should be POST)', 
                method: 'DELETE',
                expectation: 'method_error'
            }
        ]
    },
    {
        category: 'CORS Errors',
        tests: [
            {
                name: 'Blocked Origin',
                payload: { query: 'test', context: {} },
                headers: { 'Origin': 'https://malicious-site.com' },
                expectation: 'cors_handling'
            },
            {
                name: 'Missing Origin Header',
                payload: { query: 'test', context: {} },
                headers: { 'Origin': undefined },
                expectation: 'graceful_handling'
            }
        ]
    }
];

async function runErrorHandlingTests() {
    console.log('🛡️ Error Handling Validation Starting...');
    console.log('=' .repeat(55));
    
    const results = {
        total: 0,
        passed: 0,
        failed: 0,
        tests: [],
        categories: {}
    };

    // Test each error category
    for (const category of ERROR_SCENARIOS) {
        results.categories[category.category] = { total: 0, passed: 0, failed: 0 };
        
        console.log(`\n🧪 Testing ${category.category}:`);
        console.log('-' .repeat(30));
        
        for (const test of category.tests) {
            await runErrorTest(results, category.category, test);
        }
    }

    // Additional comprehensive tests
    console.log(`\n🧪 Testing System Resilience:`);
    console.log('-' .repeat(30));
    
    // Test server overload recovery
    // Initialize System Resilience category
    results.categories['System Resilience'] = { total: 0, passed: 0, failed: 0 };
    
    await runErrorTest(results, 'System Resilience', {
        name: 'Server Overload Recovery',
        testFunction: testServerOverloadRecovery,
        expectation: 'graceful_degradation'
    });

    // Summary
    console.log('\n' + '=' .repeat(55));
    console.log('🛡️ Error Handling Validation Results');
    console.log('=' .repeat(55));
    console.log(`✅ Total Tests: ${results.total}`);
    console.log(`✅ Passed: ${results.passed}`);
    console.log(`❌ Failed: ${results.failed}`);
    console.log(`📊 Success Rate: ${((results.passed / results.total) * 100).toFixed(1)}%`);
    
    // Category breakdown
    console.log('\n📋 Results by Category:');
    for (const [category, stats] of Object.entries(results.categories)) {
        const successRate = ((stats.passed / stats.total) * 100).toFixed(1);
        const status = stats.failed === 0 ? '✅' : '❌';
        console.log(`  ${status} ${category}: ${stats.passed}/${stats.total} (${successRate}%)`);
    }
    
    if (results.failed > 0) {
        console.log('\n❌ Failed Tests:');
        results.tests.filter(t => !t.passed).forEach(test => {
            console.log(`  - ${test.category}/${test.name}: ${test.error}`);
        });
        
        console.log('\n🚨 Error handling validation FAILED');
        console.log('❗ System may not handle edge cases gracefully');
        process.exit(1);
    } else {
        console.log('\n🎉 All error handling tests PASSED!');
        console.log('🛡️ System demonstrates robust error handling');
        console.log('✅ Ready for production use with confidence');
        process.exit(0);
    }
}

async function runErrorTest(results, category, test) {
    results.total++;
    results.categories[category].total++;
    
    process.stdout.write(`🛡️ ${test.name}... `);
    
    try {
        const startTime = Date.now();
        let result;
        
        if (test.testFunction) {
            result = await test.testFunction();
        } else {
            result = await executeErrorScenario(test);
        }
        
        const duration = Date.now() - startTime;
        
        // Validate result matches expectation
        const validation = validateErrorResponse(result, test.expectation);
        if (!validation.valid) {
            throw new Error(validation.message);
        }
        
        results.passed++;
        results.categories[category].passed++;
        results.tests.push({ 
            category, 
            name: test.name, 
            passed: true, 
            result: validation.message, 
            duration 
        });
        
        console.log(`✅ (${duration}ms)`);
        console.log(`   ${validation.message}`);
    } catch (error) {
        results.failed++;
        results.categories[category].failed++;
        results.tests.push({ 
            category, 
            name: test.name, 
            passed: false, 
            error: error.message 
        });
        
        console.log(`❌ ${error.message}`);
    }
}

async function executeErrorScenario(test) {
    const endpoint = test.endpoint || '/api/query/natural-language';
    const method = test.method || 'POST';
    const url = `${BASE_URL}${endpoint}`;
    
    const headers = {
        'Content-Type': 'application/json',
        'Origin': BASE_URL,
        ...test.headers
    };
    
    // Remove undefined headers
    Object.keys(headers).forEach(key => {
        if (headers[key] === undefined) {
            delete headers[key];
        }
    });
    
    const options = {
        method,
        headers
    };
    
    // Add body for methods that support it
    if (method === 'POST' || method === 'PUT') {
        if (typeof test.payload === 'string') {
            options.body = test.payload;
        } else if (test.payload) {
            options.body = JSON.stringify(test.payload);
        }
    }
    
    try {
        const response = await fetch(url, options);
        let data = null;
        
        try {
            data = await response.json();
        } catch {
            // Response might not be JSON
        }
        
        return {
            status: response.status,
            headers: response.headers,
            data,
            networkError: false
        };
        
    } catch (error) {
        return {
            networkError: true,
            error: error.message
        };
    }
}

function validateErrorResponse(result, expectation) {
    if (result.networkError) {
        return {
            valid: false,
            message: `Network error: ${result.error}`
        };
    }
    
    switch (expectation) {
        case 'graceful_handling':
            // Should return 200 with success/error structure or proper error status
            if (result.status === 200) {
                if (result.data && typeof result.data.success === 'boolean') {
                    return {
                        valid: true,
                        message: `Gracefully handled: ${result.data.success ? 'Success' : 'Handled as failure'}`
                    };
                }
            } else if (result.status >= 400 && result.status < 500) {
                return {
                    valid: true,
                    message: `Proper error response: HTTP ${result.status}`
                };
            }
            return {
                valid: false,
                message: `Expected graceful handling, got: HTTP ${result.status}`
            };
            
        case 'error_response':
            // Should return 4xx error
            if (result.status >= 400 && result.status < 500) {
                return {
                    valid: true,
                    message: `Proper error response: HTTP ${result.status}`
                };
            }
            return {
                valid: false,
                message: `Expected 4xx error, got: HTTP ${result.status}`
            };
            
        case 'method_error':
            // Should return 405 Method Not Allowed or similar
            if (result.status === 405 || result.status === 422) {
                return {
                    valid: true,
                    message: `Proper method error: HTTP ${result.status}`
                };
            }
            return {
                valid: false,
                message: `Expected method error (405/422), got: HTTP ${result.status}`
            };
            
        case 'cors_handling':
            // Should handle CORS appropriately
            const corsOrigin = result.headers.get('access-control-allow-origin');
            if (result.status === 200 && corsOrigin) {
                return {
                    valid: true,
                    message: `CORS handled: Origin ${corsOrigin}`
                };
            } else if (result.status >= 400) {
                return {
                    valid: true,
                    message: `CORS blocked: HTTP ${result.status}`
                };
            }
            return {
                valid: false,
                message: `CORS handling unclear: HTTP ${result.status}`
            };
            
        case 'graceful_degradation':
            // Should maintain some level of functionality
            if (result.successfulRequests > result.totalRequests * 0.5) {
                return {
                    valid: true,
                    message: `Graceful degradation: ${result.successfulRequests}/${result.totalRequests} succeeded`
                };
            }
            return {
                valid: false,
                message: `Poor degradation: only ${result.successfulRequests}/${result.totalRequests} succeeded`
            };
            
        default:
            return {
                valid: false,
                message: `Unknown expectation: ${expectation}`
            };
    }
}

async function testServerOverloadRecovery() {
    // Send many concurrent requests to test overload handling
    const concurrency = 10;
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
    
    const responses = await Promise.all(promises);
    
    let successfulRequests = 0;
    for (const response of responses) {
        if (response.status === 200) {
            try {
                const data = await response.json();
                if (data.success) successfulRequests++;
            } catch {
                // Response not JSON, count as failure
            }
        }
    }
    
    return {
        totalRequests: concurrency,
        successfulRequests
    };
}

// Check if fetch is available
if (typeof fetch === 'undefined') {
    console.error('❌ fetch not available. Please use Node.js 18+ or install node-fetch');
    process.exit(1);
}

// Run error handling tests
runErrorHandlingTests().catch(console.error);
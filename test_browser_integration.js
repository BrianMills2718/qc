/**
 * Browser Integration Test for Natural Language Query System
 * Tests the complete browser-to-server workflow using Node.js fetch
 */

const BASE_URL = 'http://127.0.0.1:8002';

async function testBrowserIntegration() {
    console.log('🧪 Browser Integration Test Starting...');
    console.log('=' .repeat(50));

    const results = {
        total: 0,
        passed: 0,
        failed: 0,
        tests: []
    };

    // Test 1: Health Check
    await runTest(results, 'Health Check', async () => {
        const response = await fetch(`${BASE_URL}/health`, {
            method: 'GET',
            headers: {
                'Origin': `${BASE_URL}`,
                'Accept': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.status !== 200) throw new Error(`Status: ${response.status}`);
        if (!data.status || data.status !== 'healthy') throw new Error('Invalid health response');
        if (!data.timestamp) throw new Error('Missing timestamp');
        
        return `Health: ${data.status}, Version: ${data.server_version}`;
    });

    // Test 2: Static File Access
    await runTest(results, 'Static File Access', async () => {
        const response = await fetch(`${BASE_URL}/ui/02_project_workspace.html`, {
            method: 'GET',
            headers: {
                'Origin': `${BASE_URL}`,
                'Accept': 'text/html'
            }
        });
        
        if (response.status !== 200) throw new Error(`Status: ${response.status}`);
        if (!response.headers.get('content-type').includes('text/html')) {
            throw new Error('Invalid content type');
        }
        
        const content = await response.text();
        if (!content.includes('Natural Language Query')) {
            throw new Error('UI content missing');
        }
        
        return `Size: ${content.length} bytes, HTML content verified`;
    });

    // Test 3: Simple Query Processing
    await runTest(results, 'Simple Query Processing', async () => {
        const response = await fetch(`${BASE_URL}/api/query/natural-language`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': `${BASE_URL}`,
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                query: 'Show me all people',
                context: {}
            })
        });
        
        if (response.status !== 200) throw new Error(`Status: ${response.status}`);
        
        const data = await response.json();
        if (!data.success) throw new Error(`Query failed: ${data.error}`);
        if (!data.cypher) throw new Error('Missing Cypher query');
        if (!data.data || !Array.isArray(data.data)) throw new Error('Missing data array');
        
        return `Cypher: "${data.cypher}", Results: ${data.data.length} items`;
    });

    // Test 4: Complex Query Processing  
    await runTest(results, 'Complex Query Processing', async () => {
        const response = await fetch(`${BASE_URL}/api/query/natural-language`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': `${BASE_URL}`,
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                query: 'Find people who work at large organizations',
                context: {}
            })
        });
        
        if (response.status !== 200) throw new Error(`Status: ${response.status}`);
        
        const data = await response.json();
        if (!data.success) throw new Error(`Query failed: ${data.error}`);
        if (!data.cypher) throw new Error('Missing Cypher query');
        
        return `Cypher: "${data.cypher}", Results: ${data.data.length} items`;
    });

    // Test 5: CORS Validation
    await runTest(results, 'CORS Validation', async () => {
        const response = await fetch(`${BASE_URL}/api/query/natural-language`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': `${BASE_URL}`,
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                query: 'Test CORS query',
                context: {}
            })
        });
        
        const corsOrigin = response.headers.get('access-control-allow-origin');
        const corsCredentials = response.headers.get('access-control-allow-credentials');
        
        if (!corsOrigin) throw new Error('Missing CORS origin header');
        if (corsCredentials !== 'true') throw new Error('CORS credentials not enabled');
        
        return `CORS Origin: ${corsOrigin}, Credentials: ${corsCredentials}`;
    });

    // Test 6: Error Handling
    await runTest(results, 'Error Handling', async () => {
        const response = await fetch(`${BASE_URL}/api/query/natural-language`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': `${BASE_URL}`,
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                query: '',  // Empty query to test validation
                context: {}
            })
        });
        
        // This should either succeed or return a structured error
        const data = await response.json();
        
        if (response.status === 200) {
            // If it succeeds, check the structure is valid
            if (typeof data.success !== 'boolean') {
                throw new Error('Invalid success field');
            }
            return `Empty query handled: ${data.success ? 'Success' : 'Handled gracefully'}`;
        } else {
            // If it fails, check we get a proper error structure
            if (!data.detail && !data.error) {
                throw new Error('No error message provided');
            }
            return `Error properly handled: ${data.detail || data.error}`;
        }
    });

    // Summary
    console.log('\n' + '=' .repeat(50));
    console.log('🧪 Browser Integration Test Results');
    console.log('=' .repeat(50));
    console.log(`✅ Total Tests: ${results.total}`);
    console.log(`✅ Passed: ${results.passed}`);
    console.log(`❌ Failed: ${results.failed}`);
    console.log(`📊 Success Rate: ${((results.passed / results.total) * 100).toFixed(1)}%`);
    
    if (results.failed > 0) {
        console.log('\n❌ Failed Tests:');
        results.tests.filter(t => !t.passed).forEach(test => {
            console.log(`  - ${test.name}: ${test.error}`);
        });
        process.exit(1);
    } else {
        console.log('\n🎉 All browser integration tests passed!');
        console.log('✅ Ready for manual browser testing');
        process.exit(0);
    }
}

async function runTest(results, name, testFn) {
    results.total++;
    process.stdout.write(`🧪 ${name}... `);
    
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

// Check if fetch is available (Node.js 18+)
if (typeof fetch === 'undefined') {
    console.error('❌ fetch not available. Please use Node.js 18+ or install node-fetch');
    process.exit(1);
}

// Run the test
testBrowserIntegration().catch(console.error);
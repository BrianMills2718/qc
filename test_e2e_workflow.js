/**
 * End-to-End Workflow Validation Test
 * Tests the complete user journey: UI access → Query input → API processing → Result visualization
 */

const BASE_URL = 'http://127.0.0.1:8002';

// Test data simulating various user queries
const TEST_SCENARIOS = [
    {
        name: 'Basic Person Query',
        query: 'Show me all people',
        expectedCypherPattern: /MATCH.*Person.*RETURN/i,
        expectedResults: { minCount: 1, properties: ['name'] }
    },
    {
        name: 'Organization Relationship Query',  
        query: 'Find people who work at large organizations',
        expectedCypherPattern: /MATCH.*Person.*Organization/i,
        expectedResults: { minCount: 0, properties: ['name'] }
    },
    {
        name: 'Code Frequency Query',
        query: 'Which codes appear most frequently',
        expectedCypherPattern: /MATCH.*Code/i,
        expectedResults: { minCount: 0, properties: ['name', 'label'] }
    },
    {
        name: 'Senior Staff Query',
        query: 'Show senior staff members',
        expectedCypherPattern: /WHERE.*senior/i,
        expectedResults: { minCount: 0, properties: ['name'] }
    },
    {
        name: 'Research Division Query',
        query: 'Who works in research',
        expectedCypherPattern: /(WHERE.*research|Organization.*Research)/i,
        expectedResults: { minCount: 0, properties: ['name'] }
    }
];

async function validateE2EWorkflow() {
    console.log('🔄 End-to-End Workflow Validation Starting...');
    console.log('=' .repeat(60));
    
    const results = {
        total: 0,
        passed: 0, 
        failed: 0,
        scenarios: []
    };

    // Step 1: Validate UI Accessibility
    await runWorkflowStep(results, 'UI Accessibility', async () => {
        const response = await fetch(`${BASE_URL}/ui/02_project_workspace.html`);
        if (response.status !== 200) throw new Error(`UI not accessible: ${response.status}`);
        
        const html = await response.text();
        
        // Check for required UI components
        const requiredElements = [
            'natural-query',  // Query input textarea
            'execute-query',  // Execute button
            'Natural Language Query',  // Section title
            'processNaturalLanguageQuery',  // JavaScript function
            'updateGraphWithQueryResults'  // Result handler function
        ];
        
        const missing = requiredElements.filter(el => !html.includes(el));
        if (missing.length > 0) {
            throw new Error(`Missing UI elements: ${missing.join(', ')}`);
        }
        
        return `All UI components present, HTML size: ${html.length} bytes`;
    });

    // Step 2: Validate API Readiness
    await runWorkflowStep(results, 'API System Readiness', async () => {
        // Check health
        const healthResponse = await fetch(`${BASE_URL}/health`);
        if (healthResponse.status !== 200) throw new Error('Health check failed');
        
        const health = await healthResponse.json();
        if (health.status !== 'healthy') throw new Error('System not healthy');
        
        // Check query endpoint availability  
        const queryResponse = await fetch(`${BASE_URL}/api/query/health`);
        if (queryResponse.status !== 200) throw new Error('Query system not ready');
        
        const queryHealth = await queryResponse.json();
        if (queryHealth.status !== 'healthy') {
            throw new Error(`Query system: ${queryHealth.status}`);
        }
        
        return `Health: ${health.status}, Query system: ${queryHealth.status}`;
    });

    // Step 3: Process Each Test Scenario
    for (const scenario of TEST_SCENARIOS) {
        await runWorkflowStep(results, `Scenario: ${scenario.name}`, async () => {
            return await processQueryScenario(scenario);
        });
    }

    // Step 4: Performance Validation
    await runWorkflowStep(results, 'Performance Validation', async () => {
        const testQuery = 'Show me all people';
        const iterations = 3;
        const times = [];
        
        for (let i = 0; i < iterations; i++) {
            const startTime = Date.now();
            
            const response = await fetch(`${BASE_URL}/api/query/natural-language`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Origin': BASE_URL
                },
                body: JSON.stringify({ query: testQuery, context: {} })
            });
            
            if (response.status !== 200) throw new Error(`Request ${i+1} failed`);
            await response.json();
            
            times.push(Date.now() - startTime);
        }
        
        const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
        const maxTime = Math.max(...times);
        
        if (avgTime > 3000) {
            throw new Error(`Average response time too slow: ${avgTime}ms`);
        }
        
        return `Avg: ${avgTime.toFixed(0)}ms, Max: ${maxTime}ms, Target: <3000ms`;
    });

    // Step 5: Error Handling Validation
    await runWorkflowStep(results, 'Error Handling Validation', async () => {
        const errorTests = [
            { query: '', name: 'Empty Query' },
            { query: '   ', name: 'Whitespace Query' },
            { query: 'INVALID SYNTAX ###', name: 'Invalid Syntax' }
        ];
        
        let handledCount = 0;
        
        for (const test of errorTests) {
            try {
                const response = await fetch(`${BASE_URL}/api/query/natural-language`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Origin': BASE_URL
                    },
                    body: JSON.stringify({ query: test.query, context: {} })
                });
                
                const data = await response.json();
                
                // Either succeeds gracefully or fails gracefully
                if (response.status === 200) {
                    if (typeof data.success === 'boolean') handledCount++;
                } else {
                    if (data.detail || data.error) handledCount++;
                }
            } catch (error) {
                // Network errors are not acceptable
                throw new Error(`${test.name} caused network error: ${error.message}`);
            }
        }
        
        if (handledCount !== errorTests.length) {
            throw new Error(`Only ${handledCount}/${errorTests.length} errors handled properly`);
        }
        
        return `All ${errorTests.length} error scenarios handled gracefully`;
    });

    // Summary
    console.log('\n' + '=' .repeat(60));
    console.log('🔄 End-to-End Workflow Validation Results');
    console.log('=' .repeat(60));
    console.log(`✅ Total Steps: ${results.total}`);
    console.log(`✅ Passed: ${results.passed}`);
    console.log(`❌ Failed: ${results.failed}`);
    console.log(`📊 Success Rate: ${((results.passed / results.total) * 100).toFixed(1)}%`);
    
    // Show scenario results
    if (results.scenarios.length > 0) {
        console.log('\n📋 Scenario Results:');
        results.scenarios.forEach(scenario => {
            const status = scenario.passed ? '✅' : '❌';
            console.log(`  ${status} ${scenario.name}: ${scenario.result || scenario.error}`);
        });
    }
    
    if (results.failed > 0) {
        console.log('\n❌ Failed Steps:');
        results.scenarios.filter(s => !s.passed).forEach(step => {
            console.log(`  - ${step.name}: ${step.error}`);
        });
        
        console.log('\n🚨 End-to-end workflow validation FAILED');
        process.exit(1);
    } else {
        console.log('\n🎉 End-to-end workflow validation PASSED!');
        console.log('🌐 Complete integration ready for manual browser testing');
        console.log(`\n📖 Access the UI at: ${BASE_URL}/ui/02_project_workspace.html`);
        process.exit(0);
    }
}

async function processQueryScenario(scenario) {
    const response = await fetch(`${BASE_URL}/api/query/natural-language`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Origin': BASE_URL
        },
        body: JSON.stringify({
            query: scenario.query,
            context: {}
        })
    });
    
    if (response.status !== 200) {
        throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    if (!data.success) {
        throw new Error(`Query failed: ${data.error}`);
    }
    
    // Validate Cypher pattern
    if (!scenario.expectedCypherPattern.test(data.cypher || '')) {
        throw new Error(`Cypher pattern mismatch: "${data.cypher}"`);
    }
    
    // Validate result structure
    if (!Array.isArray(data.data)) {
        throw new Error('Results not an array');
    }
    
    if (data.data.length < scenario.expectedResults.minCount) {
        throw new Error(`Too few results: ${data.data.length} < ${scenario.expectedResults.minCount}`);
    }
    
    // Validate result properties (if we have results)
    if (data.data.length > 0) {
        const firstResult = data.data[0];
        const missingProps = scenario.expectedResults.properties.filter(
            prop => !(prop in firstResult)
        );
        if (missingProps.length > 0) {
            throw new Error(`Missing properties: ${missingProps.join(', ')}`);
        }
    }
    
    return `Cypher: "${data.cypher}", Results: ${data.data.length}`;
}

async function runWorkflowStep(results, name, stepFn) {
    results.total++;
    process.stdout.write(`🔄 ${name}... `);
    
    try {
        const startTime = Date.now();
        const result = await stepFn();
        const duration = Date.now() - startTime;
        
        results.passed++;
        results.scenarios.push({ name, passed: true, result, duration });
        
        console.log(`✅ (${duration}ms)`);
        if (result && result.length < 100) {
            console.log(`   ${result}`);
        }
    } catch (error) {
        results.failed++;
        results.scenarios.push({ name, passed: false, error: error.message });
        
        console.log(`❌ ${error.message}`);
    }
}

// Check if fetch is available
if (typeof fetch === 'undefined') {
    console.error('❌ fetch not available. Please use Node.js 18+ or install node-fetch');
    process.exit(1);
}

// Run the validation
validateE2EWorkflow().catch(console.error);
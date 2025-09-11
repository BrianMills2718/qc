/**
 * Automation Viewer JavaScript Components
 * 
 * Interactive components for exploring automated qualitative coding results
 * including quotes, entities, codes, and their relationships with confidence scores.
 */

class AutomationDashboard {
    constructor() {
        this.neo4jData = null;
        this.selectedInterview = null;
        this.searchCache = new Map();
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }
    
    setupEventListeners() {
        // Search functionality
        const searchForm = document.getElementById('search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.performSearch();
            });
        }
        
        // Real-time search as user types
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    if (e.target.value.length >= 3) {
                        this.performSearch();
                    }
                }, 300);
            });
        }
    }
    
    async loadInitialData() {
        try {
            const response = await fetch('/api/automation-summary');
            this.neo4jData = await response.json();
            this.updateDashboardStats();
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load automation summary');
        }
    }
    
    async loadAutomationSummary() {
        try {
            const response = await fetch('/api/automation-summary');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.neo4jData = data;
            this.updateDashboardStats();
            return data;
        } catch (error) {
            console.error('Error loading automation summary:', error);
            this.showError('Failed to load automation summary');
            throw error;
        }
    }
    
    updateDashboardStats() {
        if (!this.neo4jData) return;
        
        // Update statistics cards if they exist
        this.updateStatCard('quotes-extracted', this.neo4jData.statistics.quotes_extracted);
        this.updateStatCard('quote-nodes', this.neo4jData.statistics.quote_nodes);
        this.updateStatCard('entities-detected', this.neo4jData.statistics.entities_detected);
        this.updateStatCard('entity-relationships', this.neo4jData.statistics.entity_relationships);
        
        // Update confidence distribution
        this.updateConfidenceDistribution(this.neo4jData.confidence_distribution);
    }
    
    updateStatCard(cardId, value) {
        const element = document.getElementById(cardId);
        if (element) {
            element.textContent = value || 0;
        }
    }
    
    updateConfidenceDistribution(distribution) {
        if (!distribution) return;
        
        const high = distribution.high || 0;
        const medium = distribution.medium || 0;
        const low = distribution.low || 0;
        const total = high + medium + low;
        
        if (total === 0) return;
        
        // Update progress bar if it exists
        const progressBar = document.querySelector('.confidence-progress');
        if (progressBar) {
            const highPercent = (high / total * 100).toFixed(1);
            const mediumPercent = (medium / total * 100).toFixed(1);
            const lowPercent = (low / total * 100).toFixed(1);
            
            progressBar.innerHTML = `
                <div class="progress-bar bg-success" style="width: ${highPercent}%">${highPercent}%</div>
                <div class="progress-bar bg-warning" style="width: ${mediumPercent}%">${mediumPercent}%</div>
                <div class="progress-bar bg-danger" style="width: ${lowPercent}%">${lowPercent}%</div>
            `;
        }
    }
    
    async performSearch() {
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;
        
        const query = searchInput.value.trim();
        if (query.length < 3) {
            this.clearSearchResults();
            return;
        }
        
        // Check cache first
        if (this.searchCache.has(query)) {
            this.displaySearchResults(this.searchCache.get(query), query);
            return;
        }
        
        try {
            this.showSearchLoading();
            
            const params = new URLSearchParams({
                q: query,
                min_confidence: '0.0'
            });
            
            const response = await fetch(`/api/search?${params}`);
            if (!response.ok) {
                throw new Error(`Search failed: ${response.statusText}`);
            }
            
            const results = await response.json();
            
            // Cache results
            this.searchCache.set(query, results);
            
            this.displaySearchResults(results, query);
        } catch (error) {
            console.error('Search error:', error);
            this.showSearchError('Search failed. Please try again.');
        }
    }
    
    displaySearchResults(results, query) {
        // Create or update search results modal/dropdown
        let resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) {
            resultsContainer = this.createSearchResultsContainer();
        }
        
        if (results.count === 0) {
            resultsContainer.innerHTML = `
                <div class="alert alert-info">
                    No quotes found for "${query}"
                </div>
            `;
        } else {
            let html = `
                <div class="search-results-header">
                    <h6>Search Results for "${query}" (${results.count} found)</h6>
                </div>
                <div class="search-results-list">
            `;
            
            results.results.forEach(quote => {
                const confidenceIcon = this.getConfidenceIcon(quote.confidence);
                html += `
                    <div class="search-result-item">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <h6 class="mb-1">
                                    <a href="/quotes/${quote.interview_id}#quote-${quote.id}">
                                        Quote ${quote.id}
                                    </a>
                                </h6>
                                <p class="mb-1">"${this.highlightSearchTerm(quote.text, query)}"</p>
                                <small class="text-muted">
                                    ${quote.interview_id} | Lines ${quote.line_start}-${quote.line_end}
                                    ${confidenceIcon} ${quote.confidence ? quote.confidence.toFixed(2) : 'N/A'}
                                </small>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            resultsContainer.innerHTML = html;
        }
        
        resultsContainer.style.display = 'block';
    }
    
    createSearchResultsContainer() {
        const container = document.createElement('div');
        container.id = 'search-results';
        container.className = 'search-results-container';
        container.style.cssText = `
            position: absolute;
            top: 100%;
            right: 0;
            width: 400px;
            max-height: 400px;
            overflow-y: auto;
            background: white;
            border: 1px solid #ddd;
            border-radius: 0.375rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            z-index: 1000;
            display: none;
        `;
        
        // Append to search form or navbar
        const searchForm = document.getElementById('search-form');
        if (searchForm) {
            searchForm.style.position = 'relative';
            searchForm.appendChild(container);
        }
        
        return container;
    }
    
    highlightSearchTerm(text, term) {
        const regex = new RegExp(`(${term})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }
    
    getConfidenceIcon(confidence) {
        if (!confidence) return '⚪';
        if (confidence >= 0.8) return '🟢';
        if (confidence >= 0.6) return '🟡';
        return '🔴';
    }
    
    showSearchLoading() {
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="text-center p-3">
                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                        <span class="visually-hidden">Searching...</span>
                    </div>
                    <small class="d-block mt-2">Searching quotes...</small>
                </div>
            `;
            resultsContainer.style.display = 'block';
        }
    }
    
    showSearchError(message) {
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="alert alert-danger m-2">
                    ${message}
                </div>
            `;
            resultsContainer.style.display = 'block';
        }
    }
    
    clearSearchResults() {
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }
    }
    
    showError(message) {
        // Show error toast or alert
        console.error(message);
        // Could implement toast notifications here
    }
}


class QuoteExplorer {
    constructor() {
        this.currentQuotes = [];
        this.filters = {
            confidence: 0.0,
            lineRange: null,
            hasEntities: null,
            hasCodes: null
        };
        this.init();
    }
    
    init() {
        this.setupFilterListeners();
        this.loadCurrentQuotes();
    }
    
    setupFilterListeners() {
        // Confidence filter
        const confidenceFilter = document.getElementById('confidence-filter');
        if (confidenceFilter) {
            confidenceFilter.addEventListener('change', () => {
                this.filters.confidence = parseFloat(confidenceFilter.value);
                this.applyFilters();
            });
        }
        
        // Line range filter
        const lineRangeFilter = document.getElementById('line-range-filter');
        if (lineRangeFilter) {
            lineRangeFilter.addEventListener('input', () => {
                this.filters.lineRange = lineRangeFilter.value.trim() || null;
                this.applyFilters();
            });
        }
        
        // Entity filter
        const entityFilter = document.getElementById('entity-filter');
        if (entityFilter) {
            entityFilter.addEventListener('change', () => {
                this.filters.hasEntities = entityFilter.value === '' ? null : entityFilter.value === 'true';
                this.applyFilters();
            });
        }
        
        // Code filter
        const codeFilter = document.getElementById('code-filter');
        if (codeFilter) {
            codeFilter.addEventListener('change', () => {
                this.filters.hasCodes = codeFilter.value === '' ? null : codeFilter.value === 'true';
                this.applyFilters();
            });
        }
    }
    
    loadCurrentQuotes() {
        const quoteCards = document.querySelectorAll('.quote-card');
        this.currentQuotes = Array.from(quoteCards);
    }
    
    applyFilters() {
        let visibleCount = 0;
        
        this.currentQuotes.forEach(quoteCard => {
            let visible = true;
            
            // Confidence filter
            const confidence = parseFloat(quoteCard.dataset.confidence) || 0;
            if (confidence < this.filters.confidence) {
                visible = false;
            }
            
            // Line range filter
            if (this.filters.lineRange && visible) {
                const [startRange, endRange] = this.filters.lineRange.split('-').map(s => parseInt(s.trim()));
                const lineStart = parseInt(quoteCard.dataset.lineStart);
                const lineEnd = parseInt(quoteCard.dataset.lineEnd);
                
                if (startRange && (lineStart < startRange || lineEnd < startRange)) {
                    visible = false;
                }
                if (endRange && (lineStart > endRange || lineEnd > endRange)) {
                    visible = false;
                }
            }
            
            // Entity filter
            if (this.filters.hasEntities !== null && visible) {
                const hasEntities = quoteCard.dataset.hasEntities === 'true';
                if (this.filters.hasEntities !== hasEntities) {
                    visible = false;
                }
            }
            
            // Code filter
            if (this.filters.hasCodes !== null && visible) {
                const hasCodes = quoteCard.dataset.hasCodes === 'true';
                if (this.filters.hasCodes !== hasCodes) {
                    visible = false;
                }
            }
            
            quoteCard.style.display = visible ? 'block' : 'none';
            if (visible) visibleCount++;
        });
        
        this.updateFilteredCount(visibleCount);
    }
    
    updateFilteredCount(count) {
        const filteredSpan = document.getElementById('filtered-count');
        if (filteredSpan) {
            if (count < this.currentQuotes.length) {
                filteredSpan.textContent = `(${count} visible after filtering)`;
            } else {
                filteredSpan.textContent = '';
            }
        }
    }
    
    renderQuoteDetails(quote) {
        const confidenceIcon = this.getConfidenceIcon(quote.confidence);
        
        return `
            <div class="quote-details">
                <div class="quote-header">
                    <h6>📝 Quote ${quote.id}</h6>
                    <span class="badge bg-secondary">Lines ${quote.line_start}-${quote.line_end}</span>
                    ${quote.speaker ? `<span class="badge bg-info">${quote.speaker}</span>` : ''}
                    ${quote.confidence ? `<span class="badge">${confidenceIcon} ${quote.confidence.toFixed(2)}</span>` : ''}
                </div>
                <blockquote class="blockquote">
                    <p>"${quote.text}"</p>
                </blockquote>
                ${quote.context ? `<small class="text-muted">Context: ${quote.context}</small>` : ''}
                ${this.renderEntityAssignments(quote.entities)}
                ${this.renderCodeAssignments(quote.codes)}
            </div>
        `;
    }
    
    renderEntityAssignments(entities) {
        if (!entities || entities.length === 0) return '';
        
        let html = '<div class="entity-assignments mt-3"><h6 class="text-primary">🔗 Entity Assignments:</h6>';
        entities.forEach(entity => {
            html += `
                <span class="badge bg-primary me-2">
                    ${entity.name} (${entity.entity_type})
                    ${entity.confidence ? ` - ${entity.confidence.toFixed(2)}` : ''}
                </span>
            `;
        });
        html += '</div>';
        return html;
    }
    
    renderCodeAssignments(codes) {
        if (!codes || codes.length === 0) return '';
        
        let html = '<div class="code-assignments mt-3"><h6 class="text-success">📋 Code Assignments:</h6>';
        codes.forEach(code => {
            html += `
                <span class="badge bg-success me-2">
                    ${code.name} (${code.code_type || 'code'})
                    ${code.confidence ? ` - ${code.confidence.toFixed(2)}` : ''}
                </span>
            `;
        });
        html += '</div>';
        return html;
    }
    
    renderProvenanceChain(finding) {
        if (!finding.evidence_chain || finding.evidence_chain.length === 0) {
            return '<div class="alert alert-warning">No evidence found in provenance chain.</div>';
        }
        
        let html = `
            <div class="provenance-chain">
                <h6>Finding: ${finding.finding.name} (${finding.finding_type})</h6>
                <p class="text-muted">Evidence Count: ${finding.evidence_count}</p>
                <div class="evidence-list">
        `;
        
        finding.evidence_chain.forEach((evidence, index) => {
            const confidenceIcon = this.getConfidenceIcon(evidence.confidence);
            html += `
                <div class="evidence-item">
                    <h6>Quote ${evidence.quote_id}</h6>
                    <p>"${evidence.text}"</p>
                    <small class="text-muted">
                        ${evidence.interview_id} | Lines ${evidence.line_range} | 
                        ${confidenceIcon} ${evidence.confidence.toFixed(2)} | 
                        ${evidence.relationship_type || 'N/A'}
                    </small>
                </div>
            `;
        });
        
        html += '</div></div>';
        return html;
    }
    
    getConfidenceIcon(confidence) {
        if (!confidence) return '⚪';
        if (confidence >= 0.8) return '🟢';
        if (confidence >= 0.6) return '🟡';
        return '🔴';
    }
}


class NetworkVisualization {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.networkData = null;
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.warn(`Network visualization container '${this.containerId}' not found`);
            return;
        }
        
        // Initialize network visualization (would use D3.js or Cytoscape.js in full implementation)
        this.setupPlaceholder();
    }
    
    setupPlaceholder() {
        this.container.innerHTML = `
            <div class="text-center p-4">
                <h5>🌐 Network Visualization</h5>
                <p class="text-muted">Interactive network diagrams will be implemented in Phase 3 (Advanced Visualization)</p>
                <div class="placeholder-network">
                    <div class="network-node">Entity 1</div>
                    <div class="network-edge">---</div>
                    <div class="network-node">Quote</div>
                    <div class="network-edge">---</div>
                    <div class="network-node">Entity 2</div>
                </div>
            </div>
        `;
    }
    
    renderEntityCodeQuoteNetwork(data) {
        // Placeholder for D3.js or Cytoscape.js implementation
        console.log('Network data:', data);
        this.networkData = data;
        
        // In full implementation, this would:
        // 1. Process data into nodes and edges
        // 2. Create interactive network diagram
        // 3. Apply force-directed layout
        // 4. Add zoom and pan capabilities
        // 5. Implement confidence-based edge weighting
        // 6. Add real-time filtering
    }
}


// Global instances
let dashboard = null;
let quoteExplorer = null;

// Initialize components when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard if on dashboard page
    if (document.querySelector('.dashboard, #automation-summary')) {
        dashboard = new AutomationDashboard();
    }
    
    // Initialize quote explorer if on quote browser page
    if (document.querySelector('.quote-card')) {
        quoteExplorer = new QuoteExplorer();
    }
    
    // Close search results when clicking outside
    document.addEventListener('click', function(event) {
        const searchResults = document.getElementById('search-results');
        const searchForm = document.getElementById('search-form');
        
        if (searchResults && searchForm && !searchForm.contains(event.target)) {
            searchResults.style.display = 'none';
        }
    });
});

// Export for use in other scripts
window.AutomationViewer = {
    AutomationDashboard,
    QuoteExplorer,
    NetworkVisualization
};
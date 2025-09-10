# Analytics Module for Qualitative Coding
from .quote_aggregator import (
    QuoteAggregation,
    CrossInterviewAggregation, 
    QuoteDensityAnalysis,
    AdvancedQuoteAggregator,
    QuickAggregator
)

# Alias for compatibility
QuoteAggregator = AdvancedQuoteAggregator

__all__ = [
    'QuoteAggregation',
    'CrossInterviewAggregation', 
    'QuoteDensityAnalysis',
    'AdvancedQuoteAggregator',
    'QuickAggregator',
    'QuoteAggregator'  # Compatibility alias
]
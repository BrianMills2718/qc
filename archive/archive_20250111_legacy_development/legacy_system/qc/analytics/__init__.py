"""
Quote-Based Analytics Module

This module provides advanced analytics capabilities for the quote-centric
qualitative coding system.
"""

from .advanced_quote_analytics import (
    QuotePatternAnalyzer,
    ContradictionMapper,
    QuoteFrequencyAnalyzer,
    QuoteEvolutionTracker
)

from .quote_aggregator import (
    AdvancedQuoteAggregator,
    QuickAggregator
)

__all__ = [
    'QuotePatternAnalyzer',
    'ContradictionMapper', 
    'QuoteFrequencyAnalyzer',
    'QuoteEvolutionTracker',
    'AdvancedQuoteAggregator',
    'QuickAggregator'
]
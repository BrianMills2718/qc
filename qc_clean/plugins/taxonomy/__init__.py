#!/usr/bin/env python3
"""
AI Taxonomy Plugin Package

Provides AI taxonomy enhancement functionality as a plugin
for the QC Clean architecture.
"""

from .taxonomy_plugin import AITaxonomyPlugin
from .taxonomy_engine import TaxonomyEngine

__all__ = ['AITaxonomyPlugin', 'TaxonomyEngine']
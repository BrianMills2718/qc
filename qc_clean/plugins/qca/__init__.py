#!/usr/bin/env python3
"""
QCA Analysis Plugin Package

Provides Qualitative Comparative Analysis functionality as a plugin
for the QC Clean architecture.
"""

from .qca_plugin import QCAAnalysisPlugin
from .qca_engine import QCAEngine, QCAConfiguration, QCAResults

__all__ = ['QCAAnalysisPlugin', 'QCAEngine', 'QCAConfiguration', 'QCAResults']
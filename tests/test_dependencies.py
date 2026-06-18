"""
Smoke tests for runtime dependencies used by advertised entrypoints.
"""

import importlib


def test_document_parser_dependencies_importable():
    """Advertised document formats should have their parser libraries installed."""
    for module_name in ("docx", "striprtf.striprtf", "pypdf"):
        importlib.import_module(module_name)


def test_cli_web_dependency_importable():
    """The legacy CLI web entrypoint should be importable when dependencies are installed."""
    importlib.import_module("flask")

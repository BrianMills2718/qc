"""Tests for environment-backed server configuration."""

from __future__ import annotations

from qc_clean.core.config.env_config import DEFAULT_CORS_ORIGINS, EnvironmentConfig


def test_cors_origins_default_to_local_development_hosts(monkeypatch) -> None:
    """The default API CORS policy should not allow every origin."""
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    assert EnvironmentConfig().cors_origins == DEFAULT_CORS_ORIGINS


def test_cors_origins_parse_comma_separated_environment(monkeypatch) -> None:
    """Deployment origins can be configured explicitly through the environment."""
    monkeypatch.setenv("CORS_ORIGINS", "https://example.test, https://admin.example.test ,,")

    assert EnvironmentConfig().cors_origins == [
        "https://example.test",
        "https://admin.example.test",
    ]

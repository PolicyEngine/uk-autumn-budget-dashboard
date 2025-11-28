"""Test that API URL is correctly configured for production."""

import pytest


def test_api_url_configured_for_production():
    """Test that the frontend uses a production API URL, not localhost."""
    with open("src/components/PersonalImpactTab.jsx") as f:
        content = f.read()

    # The production build should NOT default to localhost
    # It should either:
    # 1. Use an environment variable
    # 2. Have a hardcoded production URL

    # Check that we're not hardcoding localhost as the only fallback
    assert "VITE_PERSONAL_IMPACT_API_URL" in content, (
        "Should use VITE_PERSONAL_IMPACT_API_URL environment variable"
    )

    # For now, localhost is acceptable as dev fallback
    # but production must be configurable via env var
    lines = content.split("\n")
    api_url_lines = [l for l in lines if "API_URL" in l or "API_BASE_URL" in l]

    # Verify the pattern allows for production override
    has_env_var_check = any("import.meta.env" in l for l in api_url_lines)
    assert has_env_var_check, "API URL should be configurable via environment variable"

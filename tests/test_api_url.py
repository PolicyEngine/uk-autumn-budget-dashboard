"""Test that PersonalImpactTab uses the correct lifecycle URL."""


def test_lifecycle_url_configured():
    """Test that the frontend embeds the lifecycle calculator correctly."""
    with open("src/components/PersonalImpactTab.jsx") as f:
        content = f.read()

    # The component should embed the lifecycle calculator iframe
    assert (
        "uk-autumn-budget-lifecycle.vercel.app" in content
    ), "Should embed the lifecycle calculator from vercel.app"

    # Should use an iframe element
    assert "<iframe" in content, "Should use an iframe to embed the calculator"

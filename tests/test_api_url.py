"""Test that PersonalImpactTab uses the integrated lifecycle calculator."""


def test_lifecycle_calculator_integrated():
    """Test that the frontend uses the native lifecycle calculator component."""
    with open("src/components/PersonalImpactTab.jsx") as f:
        content = f.read()

    # The component should import and use the LifecycleCalculator component
    assert "LifecycleCalculator" in content, (
        "Should import and use the LifecycleCalculator component"
    )

    # Should NOT use an iframe anymore
    assert "<iframe" not in content, (
        "Should use native component instead of iframe"
    )


def test_lifecycle_calculator_exists():
    """Test that the LifecycleCalculator component file exists."""
    with open("src/components/LifecycleCalculator.jsx") as f:
        content = f.read()

    # Should have key elements of the lifecycle calculator
    assert "lifecycle-calculator" in content, (
        "Should have lifecycle-calculator class"
    )
    assert "REFORMS" in content, "Should define policy reforms"
    assert "fetchData" in content, "Should have data fetching logic"

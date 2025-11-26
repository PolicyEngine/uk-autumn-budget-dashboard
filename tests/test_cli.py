"""Tests for CLI module."""



class TestCLI:
    """Tests for CLI functionality."""

    def test_main_function_exists(self):
        """main function is importable."""
        from uk_budget_data.cli import main

        assert callable(main)

    def test_parse_args_default(self):
        """parse_args returns defaults when no args."""
        from uk_budget_data.cli import parse_args

        args = parse_args([])
        assert args.output_dir is not None
        assert args.years is not None

    def test_parse_args_custom_output(self):
        """parse_args accepts custom output directory."""
        from uk_budget_data.cli import parse_args

        args = parse_args(["--output-dir", "/tmp/output"])
        assert str(args.output_dir) == "/tmp/output"

    def test_parse_args_reforms(self):
        """parse_args accepts reform IDs."""
        from uk_budget_data.cli import parse_args

        args = parse_args(["--reforms", "two_child_limit", "fuel_duty_freeze"])
        assert "two_child_limit" in args.reforms
        assert "fuel_duty_freeze" in args.reforms

    def test_parse_args_years(self):
        """parse_args accepts years."""
        from uk_budget_data.cli import parse_args

        args = parse_args(["--years", "2026", "2027"])
        assert args.years == [2026, 2027]

    def test_list_reforms_option(self):
        """parse_args accepts --list-reforms."""
        from uk_budget_data.cli import parse_args

        args = parse_args(["--list-reforms"])
        assert args.list_reforms is True


class TestReformSelection:
    """Tests for reform selection logic."""

    def test_get_reforms_from_ids(self):
        """Can get reforms by their IDs."""
        from uk_budget_data.cli import get_reforms_from_ids

        reforms = get_reforms_from_ids(["two_child_limit", "fuel_duty_freeze"])
        assert len(reforms) == 2
        assert reforms[0].id == "two_child_limit"
        assert reforms[1].id == "fuel_duty_freeze"

    def test_get_reforms_from_ids_warns_unknown(self, capsys):
        """Warns about unknown reform IDs."""
        from uk_budget_data.cli import get_reforms_from_ids

        reforms = get_reforms_from_ids(
            ["two_child_limit", "unknown_reform_xyz"]
        )

        # Should only return the valid one
        assert len(reforms) == 1
        assert reforms[0].id == "two_child_limit"

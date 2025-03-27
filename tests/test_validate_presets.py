import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pyfakefs.fake_filesystem_unittest import Patcher
from pytest import FixtureRequest

sys.path.insert(0, str(Path(__file__).parent.parent / ".github" / "scripts"))
from validate_presets import main, parse_json, validate_presets


class TestValidatePresets:
    @pytest.fixture(scope="function")  # type: ignore
    def valid_presets(self, request: FixtureRequest) -> dict[str, Any]:
        return {
            "debug": {"toolchain": "gcc", "artifact": {"path": ["build/tests", "!build/tests/broken_tests"], "retention_days": 7}},
            "release": {},
            "macos": {"runs-on": "macos-latest"},
        }

    @pytest.fixture(scope="function")  # type: ignore
    def invalid_presets(self, request: FixtureRequest) -> dict[str, Any]:
        return {"int": 1, "bool": True}

    @pytest.fixture(scope="function")  # type: ignore
    def nested_invalid_presets(self, request: FixtureRequest) -> dict[str, Any]:
        return {
            "debug": {
                "toolchain": "gcc",
                "artifact": {
                    "path": 123,  # This should be a list, not a number
                    "retention_days": 7,
                },
            },
        }

    def test_parse_json_valid(self) -> None:
        valid_json = '{"key": "value"}'
        result = parse_json(valid_json)
        assert result == {"key": "value"}

    def test_parse_json_invalid(self) -> None:
        invalid_json = "{key: value}"
        with pytest.raises(ValueError):
            parse_json(invalid_json)

    def test_validate_presets_valid(self, valid_presets: dict[str, Any]) -> None:
        validate_presets(valid_presets)

    def test_validate_presets_invalid(self, invalid_presets: dict[str, Any]) -> None:
        with pytest.raises(ValueError) as e:
            validate_presets(invalid_presets)
        assert "Preset validation error @ int: 1 is not of type 'object'" in str(e.value)

    def test_validate_presets_nested_invalid(self, nested_invalid_presets: dict[str, Any]) -> None:
        with pytest.raises(ValueError) as e:
            validate_presets(nested_invalid_presets)
        assert "Preset validation error @ debug -> artifact -> path: 123 is not of type 'array'" in str(e.value)

    @patch("sys.argv", ["validate_presets.py", "--presets", "{}"])
    @patch("sys.stderr")
    @patch("sys.exit")
    def test_main_invalid_json(self, mock_exit: Any, mock_stderr: Any) -> None:
        main()
        assert any("Error: Preset validation error:" in args[0] for args, _ in mock_stderr.write.call_args_list)
        mock_exit.assert_called_with(1)

    @patch("sys.argv", ["validate_presets.py", "--presets", '{"debug": {}}'])
    @patch("validate_presets.validate_presets")
    @patch("sys.stdout")
    def test_main_valid(self, mock_stdout: Any, mock_validate: Any) -> None:
        main()
        mock_validate.assert_called_once()
        assert any("Presets validation successful" in str(call_args) for call_args, _ in mock_stdout.write.call_args_list)

    def test_validate_presets_schema_not_found(self) -> None:
        with Patcher():
            with pytest.raises(ValueError) as e:
                validate_presets({})
            assert "Schema file not found" in str(e.value)

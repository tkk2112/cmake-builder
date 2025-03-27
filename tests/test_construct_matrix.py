import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pytest import FixtureRequest

sys.path.insert(0, str(Path(__file__).parent.parent / ".github" / "scripts"))
from construct_matrix import construct_matrix, main, parse_json


class TestConstructMatrix:
    @pytest.fixture(scope="function")  # type: ignore
    def presets_data(self, request: FixtureRequest) -> dict[str, dict[str, Any]]:
        return {
            "preset1": {"runs-on": "ubuntu-latest", "toolchain": "gcc"},
            "preset2": {"toolchain": "clang"},
            "preset3": {"runs-on": "windows-latest", "artifact": {"path": ["build/artifacts"], "retention_days": 14}},
        }

    def test_parse_json_valid(self) -> None:
        valid_json = '{"key": "value"}'
        result = parse_json(valid_json)
        assert result == {"key": "value"}

    def test_parse_json_invalid(self) -> None:
        invalid_json = "{key: value}"
        with pytest.raises(ValueError):
            parse_json(invalid_json)

    def test_construct_matrix(self, presets_data: dict[str, dict[str, Any]]) -> None:
        default_runs_on = "macos-latest"
        default_toolchain = "default-tc"

        matrix = construct_matrix(presets_data, default_runs_on, default_toolchain)

        # Check matrix format
        assert "include" in matrix
        assert len(matrix["include"]) == 3

        # Check preset1
        preset1_entry = next(entry for entry in matrix["include"] if entry["preset"] == "preset1")
        assert preset1_entry["runs-on"] == "ubuntu-latest"
        assert preset1_entry["toolchain"] == "gcc"

        # Check preset2 with default runs-on
        preset2_entry = next(entry for entry in matrix["include"] if entry["preset"] == "preset2")
        assert preset2_entry["runs-on"] == default_runs_on
        assert preset2_entry["toolchain"] == "clang"

        # Check preset3 with artifact
        preset3_entry = next(entry for entry in matrix["include"] if entry["preset"] == "preset3")
        assert preset3_entry["runs-on"] == "windows-latest"
        assert preset3_entry["toolchain"] == default_toolchain
        assert "artifact" in preset3_entry

        assert preset3_entry["artifact"]["path"] == ["build/artifacts"]
        assert preset3_entry["artifact"]["retention_days"] == 14

    @patch(
        "sys.argv",
        [
            "construct_matrix.py",
            "--default-runs-on",
            "ubuntu-latest",
            "--default-toolchain",
            "gcc",
            "--presets",
            '{"preset1": {"runs-on": "windows-latest"}}',
        ],
    )
    @patch("sys.stdout")
    def test_main(self, mock_stdout: Any) -> None:
        main()

        # Fix: Check if any of the output lines contain 'matrix='
        output_lines = [args[0] for args, _ in mock_stdout.write.call_args_list]
        matrix_line = next((line for line in output_lines if "matrix=" in line), None)
        assert matrix_line is not None, "No output line contains 'matrix='"

        # Parse the matrix JSON from the line containing 'matrix='
        matrix_json = matrix_line.split("matrix=", 1)[1].strip()
        matrix = json.loads(matrix_json)

        # Verify structure
        assert "include" in matrix
        assert len(matrix["include"]) == 1
        assert matrix["include"][0]["preset"] == "preset1"
        assert matrix["include"][0]["runs-on"] == "windows-latest"
        assert matrix["include"][0]["toolchain"] == "gcc"

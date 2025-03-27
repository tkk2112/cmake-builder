import json
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from cmakepresets import CMakePresets
from pyfakefs.fake_filesystem_unittest import Patcher

sys.path.insert(0, str(Path(__file__).parent.parent / ".github" / "scripts"))
from generate_steps import get_related_preset_names, main


class TestGenerateSteps:
    @pytest.fixture(scope="function")  # type: ignore
    def valid_presets(self) -> Generator[None]:
        with Patcher():
            project_root = Path("/fake/path")
            project_root.mkdir(parents=True, exist_ok=True)

            # Create a realistic CMakePresets.json file
            presets_content = {
                "version": 6,
                "configurePresets": [
                    {"name": "test-preset", "generator": "Ninja", "binaryDir": "${sourceDir}/build/${presetName}"},
                    {"name": "config"},
                    {"name": "config_build"},
                    {"name": "config_build_test"},
                    {"name": "config_build_test_package", "binaryDir": "/shared_build/project/${presetName}"},
                ],
                "buildPresets": [
                    {"name": "test-build", "configurePreset": "test-preset"},
                    {"name": "config_build", "configurePreset": "config_build"},
                    {"name": "config_build_test", "configurePreset": "config_build_test"},
                    {"name": "config_build_test_package", "configurePreset": "config_build_test_package"},
                ],
                "testPresets": [
                    {"name": "test-test", "configurePreset": "test-preset"},
                    {"name": "config_build_test", "configurePreset": "config_build_test"},
                    {"name": "config_build_test_package", "configurePreset": "config_build_test_package"},
                ],
                "packagePresets": [
                    {"name": "test-package", "configurePreset": "test-preset"},
                    {"name": "config_build_test_package", "configurePreset": "config_build_test_package"},
                ],
            }

            cmake_presets_path = project_root / "CMakePresets.json"
            with open(cmake_presets_path, "w") as f:
                json.dump(presets_content, f)

            presets = CMakePresets(cmake_presets_path)
            yield presets

    @pytest.fixture(scope="function")  # type: ignore
    def empty_presets(self) -> Generator[None]:
        with Patcher():
            # Create a fake project directory with CMakePresets.json
            project_root = Path("/fake/path")
            project_root.mkdir(parents=True, exist_ok=True)

            # Create a realistic CMakePresets.json file
            presets_content = {"version": 2}

            cmake_presets_path = project_root / "CMakePresets.json"
            with open(cmake_presets_path, "w") as f:
                json.dump(presets_content, f)

            presets = CMakePresets(cmake_presets_path)
            yield presets

    @pytest.fixture(scope="function")  # type: ignore
    def fake_fs(self) -> Generator[None]:
        with Patcher() as patcher:
            # Create a fake project directory with CMakePresets.json
            project_root = Path("/fake/path")
            project_root.mkdir(parents=True, exist_ok=True)
            yield patcher

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "INVALID",  # Invalid boolean value
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "test-preset",
        ],
    )
    @patch("sys.stdout")
    @patch("sys.exit")
    def test_parse_boolean_invalid(self, mock_exit: Any, mock_stdout: Any) -> None:
        from generate_steps import parse_arguments

        parse_arguments()
        assert any("'INVALID' is not a valid boolean value" in args[0] for args, _ in mock_stdout.write.call_args_list)
        mock_exit.assert_called_with(2)

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "true",
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "test-preset",
            "--artifact",
            "{invalid_json}",  # Invalid artifact
        ],
    )
    @patch("sys.stdout")
    @patch("sys.exit")
    def test_parse_invalid_artifact_json(self, mock_exit: Any, mock_stdout: Any) -> None:
        from generate_steps import parse_arguments

        parse_arguments()
        assert any("Error parsing --artifact:" in args[0] for args, _ in mock_stdout.write.call_args_list)
        mock_exit.assert_called_with(2)

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/not/the/path/in/fake/fs",
            "--default-store-artifact",
            "true",
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "test-preset",
        ],
    )
    @patch("sys.stderr")
    @patch("sys.exit")
    def test_main_with_presets_not_found(self, mock_exit: Any, mock_stderr: Any) -> None:
        main()
        mock_stderr.write.assert_called_with("Error: File not found: None\n")
        mock_exit.assert_called_with(1)

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "true",
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "nonexistent-preset",
        ],
    )
    @patch("sys.stderr")
    @patch("sys.exit")
    def test_main_with_nonexistent_preset(self, mock_exit: Any, mock_stderr: Any, empty_presets: Any) -> None:
        main()
        mock_stderr.write.assert_called_with("Error: Preset 'nonexistent-preset' not found in the CMake project\n")
        mock_exit.assert_called_with(1)

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "false",  # Default is false but providing artifacts
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "test-preset",
            "--artifact",
            "",  # empty artifacts
        ],
    )
    @patch("sys.stdout")
    def test_main_with_empty_artifacts(self, mock_stdout: Any, valid_presets: Any) -> None:
        main()

        output = mock_stdout.write.call_args_list
        artifact_lines = [args[0] for args, _ in output if "artifact=" == args[0]]
        assert len(artifact_lines) == 1

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "false",  # Default is false but providing artifacts
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "test-preset",
            "--artifact",
            '{"path": ["custom/path"]}',  # Only path, no retention_days
        ],
    )
    @patch("sys.stdout")
    def test_main_with_partial_artifacts_only_path(self, mock_stdout: Any, valid_presets: Any) -> None:
        main()

        output = mock_stdout.write.call_args_list
        artifact_lines = [args[0] for args, _ in output if "artifact=" in args[0]]
        assert len(artifact_lines) > 0

        artifact_str = artifact_lines[0].split("=", 1)[1]
        artifact_config = json.loads(artifact_str)

        assert "custom/path" == artifact_config["path"]
        assert artifact_config["retention_days"] == 7  # Uses default

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "false",  # Default is false but providing artifacts
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "test-preset",
            "--artifact",
            '{"retention_days": 1}',  # Only retention_days, no path
        ],
    )
    @patch("sys.stdout")
    def test_main_with_partial_artifacts_only_retention_days(self, mock_stdout: Any, valid_presets: Any) -> None:
        main()

        output = mock_stdout.write.call_args_list
        artifact_lines = [args[0] for args, _ in output if "artifact=" in args[0]]
        assert len(artifact_lines) > 0

        artifact_str = artifact_lines[0].split("=", 1)[1]
        artifact_config = json.loads(artifact_str)

        assert artifact_config["retention_days"] == 1
        # Verify that the output contains the expected resolved relative binaryDir from the preset
        assert "build/test-preset" == artifact_config["path"]

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "true",
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "test-preset",
        ],
    )
    @patch("sys.stdout")
    def test_main_with_default_artifacts(self, mock_stdout: Any, valid_presets: Any) -> None:
        main()

        output = mock_stdout.write.call_args_list
        artifact_lines = [args[0] for args, _ in output if "artifact=" in args[0]]
        assert len(artifact_lines) > 0

        artifact_str = artifact_lines[0].split("=", 1)[1]
        artifact_config = json.loads(artifact_str)
        # Verify that the output contains the expected resolved relative binaryDir from the preset
        assert "build/test-preset" == artifact_config["path"]

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "true",
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "test-preset",
        ],
    )
    @patch("sys.stdout")
    def test_main_with_GITHUB_WORKSPACE(self, mock_stdout: Any, valid_presets: Any) -> None:
        with patch.dict("os.environ", {"GITHUB_WORKSPACE": "/fake"}):
            main()

            output = mock_stdout.write.call_args_list
            artifact_lines = [args[0] for args, _ in output if "artifact=" in args[0]]
            assert len(artifact_lines) > 0

            artifact_str = artifact_lines[0].split("=", 1)[1]
            artifact_config = json.loads(artifact_str)
            assert "path/build/test-preset" == artifact_config["path"]

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "true",
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "test-preset",
        ],
    )
    @patch("sys.stdout")
    def test_main_with_garbage_GITHUB_WORKSPACE(self, mock_stdout: Any, valid_presets: Any) -> None:
        with patch.dict("os.environ", {"GITHUB_WORKSPACE": "!!!!"}):
            main()

            output = mock_stdout.write.call_args_list
            artifact_lines = [args[0] for args, _ in output if "artifact=" in args[0]]
            assert len(artifact_lines) > 0

            artifact_str = artifact_lines[0].split("=", 1)[1]
            artifact_config = json.loads(artifact_str)
            assert "build/test-preset" == artifact_config["path"]

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "true",
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "config_build_test_package",
        ],
    )
    @patch("sys.stdout")
    def test_main_with_absolute_binarydir_and_GITHUB_WORKSPACE(self, mock_stdout: Any, valid_presets: Any) -> None:
        with patch.dict("os.environ", {"GITHUB_WORKSPACE": "/fake"}):
            main()

            output = mock_stdout.write.call_args_list
            artifact_lines = [args[0] for args, _ in output if "artifact=" in args[0]]
            assert len(artifact_lines) > 0

            artifact_str = artifact_lines[0].split("=", 1)[1]
            artifact_config = json.loads(artifact_str)
            assert "/shared_build/project/config_build_test_package" == artifact_config["path"]

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "true",
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "config_build_test_package",
        ],
    )
    @patch("sys.stdout")
    def test_main_with_absolute_binarydir(self, mock_stdout: Any, valid_presets: Any) -> None:
        main()

        output = mock_stdout.write.call_args_list
        artifact_lines = [args[0] for args, _ in output if "artifact=" in args[0]]
        assert len(artifact_lines) > 0

        artifact_str = artifact_lines[0].split("=", 1)[1]
        artifact_config = json.loads(artifact_str)
        assert "/shared_build/project/config_build_test_package" == artifact_config["path"]

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "false",
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "test-preset",
            "--artifact",
            '{"path": ["custom/path"], "retention_days": 14}',
        ],
    )
    @patch("sys.stdout")
    def test_main_with_custom_artifacts(self, mock_stdout: Any, valid_presets: Any) -> None:
        main()

        # Look for the artifact output with custom settings
        output = mock_stdout.write.call_args_list
        artifact_lines = [args[0] for args, _ in output if "artifact=" in args[0]]
        assert len(artifact_lines) > 0

        # Extract and parse the artifact configuration
        artifact_str = artifact_lines[0].split("=", 1)[1]
        artifact_config = json.loads(artifact_str)

        # Verify the custom path and retention days
        assert "custom/path" in artifact_config["path"]
        assert artifact_config["retention_days"] == 14

    def test_get_related_preset_names_empty(self, empty_presets: Any) -> None:
        result = get_related_preset_names(empty_presets, "test-preset")
        assert result == {}

    def test_get_related_preset_names(self, valid_presets: Any) -> None:
        result = get_related_preset_names(valid_presets, "test-preset")
        assert "build" in result
        assert result["build"] == ["test-build"]
        assert "test" in result
        assert result["test"] == ["test-test"]
        assert "package" in result
        assert result["package"] == ["test-package"]

    @patch(
        "sys.argv",
        [
            "generate_steps.py",
            "--cmake-project-root",
            "/fake/path",
            "--default-store-artifact",
            "false",
            "--default-artifact-retention-days",
            "7",
            "--preset",
            "test-preset",
        ],
    )
    @patch("sys.stdout")
    def test_all_step_outputs(self, mock_stdout: Any, valid_presets: Any) -> None:
        main()
        config_preset = sys.argv[-1]
        result = get_related_preset_names(valid_presets, config_preset)
        assert any(f"configure=cmake --preset {config_preset}" in args[0] for args, _ in mock_stdout.write.call_args_list)
        assert any(f"build=cmake --build --preset {''.join(result['build'])}" in args[0] for args, _ in mock_stdout.write.call_args_list)
        assert any(f"test=ctest --preset {''.join(result['test'])}" in args[0] for args, _ in mock_stdout.write.call_args_list)
        assert any(f"package=cmake --build --preset {''.join(result['package'])} --target package" in args[0] for args, _ in mock_stdout.write.call_args_list)

    @pytest.mark.parametrize(
        "preset_name, expected_steps",
        [
            (
                "config",
                {"configure": True, "build": False, "test": False, "package": False},
            ),
            (
                "config_build",
                {"configure": True, "build": True, "test": False, "package": False},
            ),
            (
                "config_build_test",
                {"configure": True, "build": True, "test": True, "package": False},
            ),
            (
                "config_build_test_package",
                {"configure": True, "build": True, "test": True, "package": True},
            ),
        ],
    )  # type: ignore
    def test_all_step_combinations(self, preset_name: str, expected_steps: dict[str, bool], valid_presets: Any) -> None:
        with (
            patch(
                "sys.argv",
                [
                    "generate_steps.py",
                    "--cmake-project-root",
                    "/fake/path",
                    "--default-store-artifact",
                    "false",
                    "--default-artifact-retention-days",
                    "7",
                    "--preset",
                    preset_name,
                ],
            ),
            patch("sys.stdout") as mock_stdout,
        ):
            main()

            output_lines = [args[0] for args, _ in mock_stdout.write.call_args_list]

            for step, should_have_content in expected_steps.items():
                matching_lines = [line for line in output_lines if line.startswith(f"{step}=")]
                assert len(matching_lines) > 0, f"No output line for {step}"
                content = matching_lines[0].split("=", 1)[1]
                if should_have_content:
                    assert content.strip(), f"Step {step} should have content but was empty"
                else:
                    assert not content.strip(), f"Step {step} should be empty but had content: {content}"

#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Final, cast

from cmakepresets import CMakePresets
from cmakepresets.constants import CONFIGURE
from cmakepresets.paths import CMakeRoot


def get_related_preset_names(presets: CMakePresets, preset: str) -> dict[str, list[str]]:
    all_related = presets.find_related_presets(preset)

    result: dict[str, list[str]] = {}
    if all_related:
        for preset_type, presets_list in all_related.items():
            preset_names = [p.get("name") for p in presets_list if p.get("name")]
            result[preset_type] = preset_names

    return result


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate build steps from preset")

    parser.add_argument(
        "--cmake-project-root",
        required=True,
        type=Path,
        help="Root directory of the CMake project",
    )

    def parse_boolean(x: str) -> bool:
        positive_values = ["true", "1", "yes", "y", "on"]
        negative_values = ["false", "0", "no", "n", "off"]

        value_lower = x.lower()
        if value_lower in positive_values:
            return True
        elif value_lower in negative_values:
            return False
        else:
            print(f"\n\nWarning: '{x}' is not a valid boolean value. Expected one of: {positive_values + negative_values}\n\n")
            raise argparse.ArgumentTypeError(f"Invalid boolean value: '{x}'")

    parser.add_argument(
        "--default-store-artifact",
        type=parse_boolean,
        help="Default boolean value whether to store artifacts (true/false/yes/no/1/0)",
    )

    parser.add_argument(
        "--default-artifact-retention-days",
        required=True,
        type=int,
        help="Default retention days for artifacts",
    )
    parser.add_argument("--preset", required=True, type=str, help="The preset to use")

    artifact_help: Final[str] = '\n\nThe artifact configuration as JSON (e.g., {"path": ["dir1", "dir2", "!dir1/**/*.md"], "retention_days": 5})\n\n'

    def parse_artifact(x: str) -> dict[str, list[str] | int]:
        if str(x).strip() == "" or str(x).strip() == "''":
            x = "{}"
        try:
            return cast(dict[str, Any], json.loads(x))
        except Exception:
            print(f"Error parsing --artifact: {artifact_help}")
            raise

    parser.add_argument("--artifact", type=parse_artifact, default={}, help=artifact_help)

    return parser.parse_args()


def generate_steps(related_presets: dict[str, list[str]]) -> dict[str, str]:
    steps: dict[str, str] = {"build": "", "test": "", "package": ""}
    if "build" in related_presets and related_presets["build"]:
        build_preset = related_presets["build"][0]
        steps["build"] = f"cmake --build --preset {build_preset}"

    if "test" in related_presets and related_presets["test"]:
        test_preset = related_presets["test"][0]
        steps["test"] = f"ctest --preset {test_preset}"

    if "package" in related_presets and related_presets["package"]:
        package_preset = related_presets["package"][0]
        steps["package"] = f"cmake --build --preset {package_preset} --target package"
    return steps


def get_binary_dir_path(presets: CMakePresets, preset_name: str, root: CMakeRoot) -> str:
    """Get the binary directory path relative to workspace or project root."""
    resolved = presets.resolve_macro_values(CONFIGURE, preset_name)
    binary_dir = Path(resolved.get("binaryDir", "build"))

    if "GITHUB_WORKSPACE" in os.environ:
        workspace_path = Path(os.environ["GITHUB_WORKSPACE"])
        try:
            return str(binary_dir.relative_to(workspace_path))
        except ValueError:
            pass
    return cast(str, root.get_relative_path(binary_dir))


def main() -> None:
    try:
        args: argparse.Namespace = parse_arguments()
        root = CMakeRoot(args.cmake_project_root)
        presets = CMakePresets(root)

        config_preset = presets.get_preset_by_name(CONFIGURE, args.preset)

        if config_preset:
            related_presets: dict[str, list[str]] = get_related_preset_names(presets, args.preset)
            configure_cmd = f"cmake --preset {args.preset}"
        else:
            raise ValueError(f"Preset '{args.preset}' not found in the CMake project")

        steps = generate_steps(related_presets)

        relative_path = get_binary_dir_path(presets, args.preset, root)

        default_artifact_config: dict[str, Any] = {
            "path": [relative_path],
            "retention_days": args.default_artifact_retention_days,
        }

        artifact_config = None

        if args.artifact or args.default_store_artifact:
            if "path" in args.artifact:
                default_artifact_config["path"] = args.artifact["path"]
            if "retention_days" in args.artifact:
                default_artifact_config["retention_days"] = args.artifact["retention_days"]

            default_artifact_config["path"] = "\n".join(default_artifact_config["path"])

            artifact_config = default_artifact_config

        outputs = {
            "configure": configure_cmd or "",
            "build": steps["build"],
            "test": steps["test"],
            "package": steps["package"],
            "artifact": json.dumps(artifact_config) if artifact_config else "",
        }

        for key, value in outputs.items():
            print(f"{key}={value}")

    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

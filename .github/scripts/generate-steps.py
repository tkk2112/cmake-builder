#!/usr/bin/env python3

import argparse
import json
import sys
from typing import Dict, List, Final, Optional, Union
from pathlib import Path
from cmakepresets import CMakePresets


def get_related_preset_names(preset: str, cmake_project_root: Path) -> Dict[str, List[str]]:
    presets = CMakePresets(cmake_project_root)
    all_related = presets.find_related_presets(preset)

    result: Dict[str, List[str]] = {}
    if all_related:
        for preset_type, presets_list in all_related.items():
            preset_names = [p.get("name") for p in presets_list if p.get("name")]
            result[preset_type] = preset_names

    return result


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate build steps from preset")

    parser.add_argument(
        "--cmake-project-root", required=True, type=Path,
        help="Root directory of the CMake project"
    )
    def parse_boolean(x: str) -> bool:
        positive_values = ['true', '1', 'yes', 'y', 'on']
        negative_values = ['false', '0', 'no', 'n', 'off']

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
        help="Default boolean value whether to store artifacts (true/false/yes/no/1/0)"
    )

    default_artifact_path_help: Final[str] = "\n\nDefault artifact path (e.g., 'path/to/artifacts' or 'path1,path2' or '!path/to/exclude')\n\n"
    def parse_artifact_path(x: str) -> List[str]:
        try:
            return [p.strip() for p in x.replace(',', ' ').split() if p.strip()]
        except Exception as e:
            print(f"Error parsing --default-artifact-path: {default_artifact_path_help}")
            raise
    parser.add_argument(
        "--default-artifact-path", required=True,
        type=parse_artifact_path,
        help=default_artifact_path_help
    )
    parser.add_argument(
        "--default-artifact-retention-days", required=True, type=int,
        help="Default retention days for artifacts"
    )
    parser.add_argument(
        "--preset", required=True, type=str,
        help="The preset to use"
    )

    artifacts_help: Final[str] = "\n\nThe artifacts configuration as JSON (e.g., {\"path\": [\"dir1\", \"dir2\", \"!dir1/**/*.md\"], \"retention_days\": 5})\n\n"
    def parse_artifacts(x: Optional[str]) -> Dict[str, Union[List[str], int]]:
        if not x:
            return {}
        try:
            return json.loads(x)
        except Exception:
            print(f"Error parsing --artifacts: {artifacts_help}")
            raise

    parser.add_argument(
        "--artifacts",
        type=parse_artifacts,
        help=artifacts_help
    )

    return parser.parse_args()


def main() -> None:
    args: argparse.Namespace = parse_arguments()
    try:
        related_presets: Dict[str, List[str]] = get_related_preset_names(args.preset, args.cmake_project_root)

        configure_cmd = f"cmake --preset {args.preset}"

        build_cmd = None
        if "buildPresets" in related_presets and related_presets["buildPresets"]:
            build_preset = related_presets["buildPresets"][0]
            build_cmd = f"cmake --build --preset {build_preset}"

        test_cmd = None
        if "testPresets" in related_presets and related_presets["testPresets"]:
            test_preset = related_presets["testPresets"][0]
            test_cmd = f"ctest --preset {test_preset}"

        package_cmd = None
        if "testPresets" in related_presets and related_presets["packagePresets"]:
            test_preset = related_presets["packagePresets"][0]
            test_cmd = f"cmake --build --preset {test_preset} --target package"

        artifact_config = {
            "path": "|\n            " + "\n            ".join(args.default_artifact_path),
            "retention_days": args.default_artifact_retention_days
        }
        default_should_store_artifact = args.default_store_artifact

        if args.artifacts:
            if "path" in args.artifacts:
                artifact_config["path"] = "|\n            " + "\n            ".join(args.artifacts["path"])
            if "retention_days" in args.artifacts:
                artifact_config["retention_days"] = args.artifacts["retention_days"]

        elif not default_should_store_artifact:
            artifact_config = {}

        outputs = {
            "configure": configure_cmd or "",
            "build": build_cmd or "",
            "test": test_cmd or "",
            "package": package_cmd or "",
            "artifact": json.dumps(artifact_config) if artifact_config else ""
        }

        for key, value in outputs.items():
            print(f"{key}={value}")

    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

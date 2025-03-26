#!/usr/bin/env python3

import argparse
import json
import sys
from typing import Any, Dict, List, cast


def parse_json(json_str: str) -> Dict[str, Any]:
    try:
        return cast(Dict[str, Any], json.loads(json_str))
    except json.JSONDecodeError as err:
        raise ValueError(f"JSON decode error: {err}")


def construct_matrix(presets: Dict[str, Dict[str, Any]], default_runs_on: str, default_toolchain: str) -> Dict[str, List[Dict[str, Any]]]:
    include_list = []

    for name, config in presets.items():
        runs_on = config.get("runs-on", default_runs_on)
        toolchain = config.get("toolchain", default_toolchain)

        entry = {"preset": name, "runs-on": runs_on, "toolchain": toolchain}

        if "artifact" in config:
            entry["artifact"] = json.dumps(config["artifact"])

        include_list.append(entry)

    return {"include": include_list}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Construct build matrix from inputs")

    parser.add_argument("--default-runs-on", required=True, help="Default runs-on parameter")
    parser.add_argument("--default-toolchain", required=True, help="Default toolchain parameter")
    parser.add_argument("--presets", required=True, help="Presets json object")

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    try:
        presets_data = parse_json(args.presets)

        matrix = construct_matrix(presets_data, args.default_runs_on, args.default_toolchain)

        matrix_json = json.dumps(matrix)
        print(f"matrix={matrix_json}")

    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

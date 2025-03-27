#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

import jsonschema


def parse_json(json_str: str) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], json.loads(json_str))
    except json.JSONDecodeError as err:
        raise ValueError(f"JSON decode error: {err}")


def validate_presets(presets_data: dict[str, Any]) -> None:
    schema_path = Path(__file__).parent / "preset-schema.json"

    try:
        with open(schema_path) as schema_file:
            preset_schema = json.load(schema_file)
    except FileNotFoundError:
        raise ValueError(f"Schema file not found: {schema_path}")

    try:
        jsonschema.validate(instance=presets_data, schema=preset_schema)
    except jsonschema.ValidationError as err:
        error_path = ""
        if hasattr(err, "absolute_path") and err.absolute_path:
            error_path = f" @ {' -> '.join(str(x) for x in err.absolute_path)}"
        raise ValueError(f"Preset validation error{error_path}: {err}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate presets against schema")
    parser.add_argument("--presets", required=True, help="Presets json object")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    try:
        presets_data = parse_json(args.presets)
        validate_presets(presets_data)
        print("Presets validation successful")
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

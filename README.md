[//]: # (x-release-please-start-version)
# CMake Builder 0.2.0
[//]: # (x-release-please-end)

A reusable GitHub workflow for building CMake-based projects with using presets.

## Usage

To use this workflow in your project, add a workflow file like this:

[//]: # (x-release-please-start-version)
```yaml
name: Build

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    uses: tkk2112/cmake-builder/.github/workflows/cmake-builder.yml@0.2.0
    with:
      runs-on: ubuntu-latest
      toolchain: gcc
      presets: |
        {
          "debug": { "artifact" : { "path" : [ "build/tests", "!build/tests/broken_tests" ] }},
          "release": {},
          "macos": { "runs-on": "macos-latest" }
        }
```
[//]: # (x-release-please-end)

### Inputs

- `runs-on`: Default runner to use (default: "ubuntu-latest")
- `toolchain`: Default toolchain to use (default: "gcc")
- `store_artifact`: Should artifacts be stored (default: false)
- `artifact_retention_days`: Number of days to store artifacts (default: 5)
- `cmake_project_root`: CMakePresets.json directory (default: .)
- `presets`: JSON configuration of build presets (**required**)

[presets schema](.github/scripts/preset-schema.json)


## License

[MIT](LICENSE)

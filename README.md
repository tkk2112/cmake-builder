# CMake Builder

A reusable GitHub workflow for building CMake-based projects with using presets.

## Usage

To use this workflow in your project, add a workflow file like this:

```yaml
name: Build

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    uses: tkk2112/cmake-builder/.github/workflows/cmake-builder.yml@main
    with:
      runs-on: ubuntu-latest
      toolchain: gcc
      presets: |
        {
          "debug": {},
          "release": {},
          "macos": { "runs-on": "macos-latest" }
        }
    secrets: inherit
```

### Inputs

- `runs-on`: Default runner to use (default: "ubuntu-latest")
- `toolchain`: Default toolchain to use (default: "gcc")
- `artifact_store`: Should artifacts be stored (default: false)
- `artifact_retention_days`: Number of days to store artifacts (default: 5)
- `artifact_path`: Artifact store path (default: "build")
- `presets`: JSON configuration of build presets (**required**)

## License

[MIT](LICENSE)

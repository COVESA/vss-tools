# VSS Tools

[![License](https://img.shields.io/badge/License-MPL%202.0-blue.svg)](https://opensource.org/licenses/MPL-2.0)
[![Build Status](https://github.com/COVESA/vss-tools/actions/workflows/buildcheck.yml/badge.svg)](https://github.com/COVESA/vss-tools/actions/workflows/buildcheck.yml?query=branch%3Amaster)

The overall goal of VSS Tools is to provide a set of tools that can be used to convert or verify Vehicle Signal Specifications defined by the format specified by the [COVESA VSS project](https://github.com/COVESA/vehicle_signal_specification).
VSS Tools is developed in parallel with VSS, please visit the [COVESA VSS project](https://github.com/COVESA/vehicle_signal_specification) for information on how to contribute.
If any questions arise, please check out the [FAQ](FAQ.md) for more information.

## Installation

There are several ways of installing `vss-tools`.
If you would like to contribute then please follow the [contribute](#contributing) section instead.
All of them are recommended to be done in an activated python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

### PyPI

```bash
pip install vss-tools
```

### From source

```bash
# default branch
pip install git+https://github.com/COVESA/vss-tools.git
# explicit branch
pip install git+https://github.com/COVESA/vss-tools.git@master
# commit
pip install git+https://github.com/COVESA/vss-tools.git@1234567
```

See [usage](#usage) for how to start using it.

## Usage

General CLI help should be used for up-to-date info of how to use the tools.

```bash
# Help for toplevel options and lists sub commands
vspec --help

# Help for export sub command options and lists sub commands
vspec export --help

# Help for json exporter options
vspec export json --help
```

Please check [here](./docs/vspec.md) for generic info about exporters and their arguments
as well as [here](./docs/vspec_arch.md) for design decision, architecture and limitations.

## Compatibility with VSS

The [COVESA VSS project repository](https://github.com/COVESA/vehicle_signal_specification) includes vss-tools as a submodule.
The vss-tools version linked by the VSS repository is the preferred vss-tools version to use for that particular version of the VSS repository.
It is not guaranteed that newer or older versions of vss-tools can successfully handle that particular version of the VSS repository.
The table below gives an overview of basic version support for e.g. `vspec export json`.
Other exporters may have stricter requirements.

| VSS-tools version | Supported VSS catalog versions | Comments |
| ----------------- | ------------------------------ | -------- |
| `v3.0`            | `v3.0` - `v3.1.1`              |
| `v3.1`            | `v3.0` -`v4.0`                 |
| `v4.0`            | `v4.0`                         |
| `v4.1`            | `v4.0` -                       |
| `4.2`             | `v4.0` -                       |
| `5.0`             | `v5.0` -                       |
| `<latest source>` | `v5.0` -                       |

### Changes affecting compatibility

Examples on changes affecting compatibility

- Somewhat stricter control in VSS-tools 5.0 onwards,
  minor changes required in VSS 4.X catalogs to make it pass the control.
- VSS version `v4.1` introduced a new syntax for the unit files that cannot be handled by `vss-tools < v4.1`
- From `v4.0` vss-tools expects unit file to be explicitly specified or provided in the same directory as the VSS input.
  VSS `v3.1` is the first VSS version including a unit file in the VSS repository.
  This means vss-tools from `v4.0` onwards cannot handle VSS-versions prior to VSS `v3.1`
- VSS-tools `v3.1` only supported `default` for attributes, resulting in that newer VSS-versions is not supported.
- VSS-tools `v4.0` requires case-sensitive for type, resulting in that VSS versions `v3.1` and earlier is not supported.

## Contributing

### UV

We are using [uv](https://docs.astral.sh/uv/) as a python package and project manager.
Therefore, a requirement to develop is to install `uv` on your host machine.
Check [here](https://docs.astral.sh/uv/#getting-started) for official installation instructions. The recommended one is the following, however installing it through pip/pipx works as well:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

You can then use the following command in the root directory of `vss-tools` to install all dependencies:

```bash
uv sync
```

It will create a `.venv` in the root of the project.
You can use the `venv` like you would without the usage of `uv`:

```bash
source .venv/bin/activate
vspec --help
```

Alternatively you can use `uv` to run the `vspec` tool:

```bash
uv run vspec --help
```

If you have a working setup of [direnv](https://direnv.net/), navigating into the directory
activates the `venv` (after an initial `uv sync` and `direnv allow`)

```bash
vspec --help
```

`uv` can manage independent python versions.
If you would like to use a specific python version (e.g. `python3.12`):

```bash
# Python 3.12
uv sync -p python3.12
# From the activated env:
python --version # --> Python 3.12.7

# Python 3.13
uv sync -p python3.13
python --version # --> Python 3.13.0
```

### Pre-commit

This project uses [pre-commit](https://pre-commit.com/) which helps to format the source code in a streamlined way.
It is very recommended to use it.
To install hooks you can do `pre-commit install` from an [activated environment](#uv).
Hooks will then run every time you do a `git commit` on changed files.
If you would like to run all hooks on all files you can do `pre-commit run --all`.
Since `pre-commit` dependencies are installed in the virtual environment, it needs
to be activated to be able to run them on a commit.

### Installing additional tools

If you intend to run test cases related to `vspec` proto exporter you need to install the protobuf compiler.
Please follow [official instructions](https://github.com/protocolbuffers/protobuf) for your OS. For Debian systems it would be:

```bash
sudo apt update
sudo apt install -y golang-go protobuf-compiler
protoc --version  # Ensure compiler version is 3+
```

## Release

Things to do for maintainers:

- Change `## Unreleased` in [CHANGELOG](CHANGELOG.md) to the desired version
- Bump the version using `bump-my-version` which is in the dev dependencies with `pre_l`
- Commit and push the changes
- Tag the commit with the new version

  ```bash
  TAG=$(grep 'current_version' .bumpversion.toml | sed 's/.*current_version = "\(.*\)"/\1/') && git tag -f v$TAG && git push origin v$TAG
  ```

- Build the artifacts

  ```bash
  uv build
  ```

  - Upload the artifacts

  ```bash
  twine upload dist/*
  ```

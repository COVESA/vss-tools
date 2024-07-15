# VSS Tools


[![License](https://img.shields.io/badge/License-MPL%202.0-blue.svg)](https://opensource.org/licenses/MPL-2.0)
[![Build Status](https://github.com/COVESA/vss-tools/actions/workflows/buildcheck.yml/badge.svg)](https://github.com/COVESA/vss-tools/actions/workflows/buildcheck.yml?query=branch%3Amaster)

The overall goal of VSS Tools is to provide a set of tools that can be used to convert or verify Vehicle Signal Specifications defined by the format specified by the [COVESA VSS project](https://github.com/COVESA/vehicle_signal_specification).
VSS Tools is developed in parallel with VSS, please visit the [COVESA VSS project](https://github.com/COVESA/vehicle_signal_specification) for information on how to contribute.
If any questions arise, please check out the [FAQ](FAQ.md) for more information.

## Available Tools

This repository contains three categories of tools:
* Community Supported Tools are tools that are actively maintained by the VSS community.
  They are run as part of the Continuous Integration process for both this repository and for the [COVESA VSS project repository](https://github.com/COVESA/vehicle_signal_specification),
  and pull request will normally not be merged if any of the tools fails. That assures that the tools always are compatible with the latest version of the COVESA VSS.
* Contributed Tools are tools that are not actively maintained by the VSS community.
  Instead they are maintained by individual contributors, or not maintained at all.
  Even if many of them are run as part of the continuous integration process,
  it is not a requirement that they must run successfully on the latest VSS version and a change in VSS may be merged even if it cause some contributed tools to fail.
* Obsolete Tools are tools that are not maintained and not functional.

A tool in the Contributed Tools category may be moved to the Obsolete category if it has been non-functional for at least 6 months.
Tools in the Obsolete Tools category may be deleted after 12 months.

Examples on tool usage can be found in the [VSS Makefile](https://github.com/COVESA/vehicle_signal_specification/blob/master/Makefile) and in tool-specific documentation, if existing.

General CLI help should be used for up to date info of how to use the tools.

```bash
vspec2x --help
vspec2x json --help
# ...
```

Please check [here](./docs/vspec2x.md) for generic infos about exporters and their arguments
as well as [here](./docs/vspec2x_arch.md) for design decision, architecture and limitations.


## Compatibility with VSS

The [COVESA VSS project repository](https://github.com/COVESA/vehicle_signal_specification) includes vss-tools as a submodule.
The vss-tools version linked by the VSS repository is the preferred vss-tools version to use for that particular version of the VSS repository.
It is not guaranteed that newer or older versions of vss-tools can successfully handle that particular version of the VSS repository.
The table below gives an overview of basic version support for e.g. `vspec2x json`.
Other exporters may have stricter requirements.

VSS-tools version | Supported VSS versions | Comments
-----------------|------------------------|----------------
`v3.0`| `v3.0` - `v3.1.1`
`v3.1`| `v3.0` -`v4.0`
`v4.0`| `v4.0`
`v4.1`| `v4.0` -
`<latest source>`| `v4.0` -

### Changes affecting compatibility

Examples on changes affecting compatibility

* VSS version `v4.1` introduced a new syntax for the unit files that cannot be handled by `vss-tools < v4.1`
* From `v4.0` vss-tools expects unit file to be explicitly specified or provided in the same directory as the VSS input.
  VSS `v3.1` is the first VSS version including a unit file in the VSS repository.
  This means vss-tools from `v4.0` onwards cannot handle VSS-versions prior to VSS `v3.1`
* VSS-tools `v3.1` only supported `default` for attributes, resulting in that newer VSS-versions is not supported.
* VSS-tools `v4.0` requires case-sensitive for type, resulting in that VSS versions `v3.1` and earlier is not supported.

## Contributing

### Prerequisites

* If your environment behind a (corporate) proxy, the following environments variables must typically be set: `http_proxy` and `https_proxy` (including authentication e.g., `http://${proxy_username):$(proxy_password)@yourproxy.yourdomain`).
* If using `apt` and you are behind a proxy, you may also need to configure proxy in `/etc/apt/apt.conf.d/proxy.conf`.

### Poetry

We are using [poetry](https://python-poetry.org/docs/) or a package and venv handling system.
Therefore a requirement to develop a tool is to install poetry on your host machine. For that you will need Python > 3 as well as pip.
Check [here](https://python-poetry.org/docs/#installation) for official installation instructions. The recommended one is the following, however installing it through pip/pipx works aswell:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

You can then use the following command to install all dependencies and the `vss-tools` package:

```bash
poetry install
```

The call will create an `.venv` directory but does not automatically activate it.
You can do that in various ways:
- `poetry shell`: Spawns a new subshell with the appropriate environment activated. After that you can directly call tools
- `poetry run <tool>`: Runs the given tool in the virtual environment but does return to the current environment after that
- `. $(poetry env info --path)/bin/activate`: Enables the virtual environment. Since we do store virtual envs directly with the tool the command can be simplified to `. .venv/bin/activate`. See [here](https://python-poetry.org/docs/basic-usage/#using-poetry-run) for more detailed information how to run poetry e.g. for Windows and how to exit/deactive it.
- We also have an `.envrc` that automatically sources the `.venv` when available. Check [direnv](https://direnv.net/) for how to set it up.


## Installing additional tools

If you intend to run testcases related to `vspec2protobuf.py` you need to install the protobuf compiler.
Please follow official instructions for your OS. For Debian systems it would be:

```sh
sudo apt update
sudo apt install -y golang-go protobuf-compiler
protoc --version  # Ensure compiler version is 3+
```

## Pre-commit set up
This repository is set up to use pre-commit hooks. After you clone the project, run `pre-commit install` to install pre-commit into your git hooks.
pre-commit will now run on every commit. Every time you clone a project using pre-commit running pre-commit install should always be the first thing you do.

## Building and installing with Pip

For usage of VSS-Tools with Pip (PyPI) please see [README-PYPI.md](README-PYPI.md)

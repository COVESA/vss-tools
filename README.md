# VSS Tools


[![License](https://img.shields.io/badge/License-MPL%202.0-blue.svg)](https://opensource.org/licenses/MPL-2.0)
[![Build Status](https://github.com/COVESA/vss-tools/actions/workflows/buildcheck.yml/badge.svg)](https://github.com/COVESA/vss-tools/actions/workflows/buildcheck.yml?query=branch%3Amaster)

The overall goal of VSS Tools is to provide a set of tools that can be used to convert or verify Vehicle Signal Specifications defined by the format specified by the [COVESA VSS project](https://github.com/COVESA/vehicle_signal_specification). VSS Tools is developed in parallel with VSS, please visit the [COVESA VSS project](https://github.com/COVESA/vehicle_signal_specification) for information on how to contribute. If any questions arise, please check out the [FAQ](FAQ.md) for more information.

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

 Tool | Description | Tool Category         | Documentation                                                                                                         |
| ------------------ | ----------- |-----------------------|-----------------------------------------------------------------------------------------------------------------------|
[vspec2csv.py](vspec2csv.py) | Generating CSV output | Community Supported   | Check [vspec2x documentation](docs/vspec2x.md)                                                                        |
[vspec2ddsidl.py](vspec2ddsidl.py) | Generating DDS-IDL output | Community Supported   | [VSS2DDSIDL Documentation](docs/VSS2DDSIDL.md). For general parameters check [vspec2x documentation](docs/vspec2x.md) |
[vspec2json.py](vspec2json.py) |  Generating JSON output | Community Supported   | Check [vspec2x documentation](docs/vspec2x.md)                                                                        |
[vspec2yaml.py](vspec2yaml.py) | Generating flattened YAML output | Community Supported   | Check [vspec2x documentation](docs/vspec2x.md)                                                                        |
[vspec2binary.py](vspec2binary.py) | The binary toolset consists of a tool that translates the VSS YAML specification to the binary file format (see below), and two libraries that provides methods that are likely to be needed by a server that manages the VSS tree, one written in C, and one in Go | Community Supported   | [vspec2binary Documentation](binary/README.md). For general parameters check [vspec2x documentation](docs/vspec2x.md) |
[vspec2franca.py](vspec2franca.py) | Parses and expands a VSS and generates a Franca IDL specification | Community Supported   | Check [vspec2x documentation](docs/vspec2x.md)                                                                        |
[vspec2c.py](obsolete/vspec2c.py) | The vspec2c tooling allows a vehicle signal specification to be translated from its source YAML file to native C code that has the entire specification encoded in it. | Obsolete (2022-11-01) | [Documentation](obsolete/vspec2c/README.md)                                                                           |
[vspec2ocf.py](obsolete/ocf/vspec2ocf.py) | Parses and expands a VSS and generates a OCF specification | Obsolete (2022-11-01) | -                                                                                                                     |
[vspec2protobuf.py](vspec2protobuf.py) | Parses and expands a VSS tree and generates a Protobuf message definition | Contrib               | [Documentation](docs/vspec2proto.md)                                                                                                                     |
[vspec2ttl.py](contrib/vspec2ttl/vspec2ttl.py) | Parses and expands a VSS and generates a TTL specification | Contrib               | -                                                                                                                     |
[vspec2graphql.py](vspec2graphql.py) | Parses and expands a VSS and generates a GraphQL specification | Community Supported   | [Documentation](docs/VSS2GRAPHQL.md)                                                                                  |
[vspec2id.py](vspec2id.py) | Generates and validates static UIDs for a VSS | WIP                   | [vspec2id Documentation](./docs/vspec2id.md)                                                                          |

## Tool Architecture

All current tools are based on common Python functionality in the `vspec` folder to read, parse and expand a Vehicle Signal Specification files(*.vspec files). As an example, if the standard [VSS root file](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/VehicleSignalSpecification.vspec) is given as input then the Python tooling will read all included files, do a validation of the content, expand any instances used and create an in-memory representation which then can be used by specialized tools to generate the wanted output.

## Compatibility with VSS

The [COVESA VSS project repository](https://github.com/COVESA/vehicle_signal_specification) includes vss-tools as a submodule.
The vss-tools version linked by the VSS repository is the preferred vss-tools version to use for that particular version of the VSS repository. It is not guaranteed that newer or older versions of vss-tools can successfully handle that particular version of the VSS repository. The table below gives an overview of basic version support for`vspec2json.py`,
other exporters may have stricter requirements.

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

## Getting started

## Prerequisites

* If your environment behind a (corporate) proxy, the following environments variables must typically be set: `http_proxy` and `https_proxy` (including authentication e.g., `http://${proxy_username):$(proxy_password)@yourproxy.yourdomain`).
* If using `apt` and you are behind a proxy, you may also need to configure proxy in `/etc/apt/apt.conf.d/proxy.conf`.


## Environment and Python Version

This repository use the Github `ubuntu-latest` [runner-image](https://github.com/actions/runner-images) for continuous nntegration.
The Python version used is typically the [default version](https://packages.ubuntu.com/search?keywords=python3) for that Ubuntu release,
currently Python `3.10.6`.
Other environments and Python versions may be supported, but are not tested as part of continuous integration or relase testing.

## Setup using venv

If you want to run the tools with a specific Python version, or you do not want to change your current/global Python configuration you can use pyenv/pipenv.
If you use a custom pip installation directory, set the `PYTHONPATH` environment variable to the directory that you set in the `pip.ini` file.
[pipenv](https://pypi.org/project/pipenv/) is a tool that manages a virtual environment and install the package and its dependencies, making the process much simpler and predictable, since the `Pipfile` states the dependencies, while `Pipfile.lock` freezes the exact version in use.

The setup example shown below is based on a fresh minimal install of Ubuntu 22.04.

The first step is to make sure that pyenv and the wanted Python version (in the example 3.10.6) is installed

```sh
# Install dependencies, to be able to use curl and build python from source
sudo apt update
sudo apt install make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Fetch and install pyenv and update variables
curl https://pyenv.run | bash
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Build and install wanted python version, shall match the version specified in Pipfile
pyenv install 3.10.6
```

Install this project and its dependencies in the local `.venv` folder in this project, then use it (`pipenv shell`):

```sh
export PIPENV_VENV_IN_PROJECT=1 # will create a local `.venv` in the project, otherwise uses global location
sudo apt update && sudo apt install pipenv
export PATH=/home/${USER}/.local/bin:${PATH}
pipenv install --dev # install the development dependencies as well
```

Then the virtual environment can be started and tested using (`pipenv shell`):

```sh
user@ubuntu:~/vss-tools$ pipenv shell
Launching subshell in virtual environment...
user@ubuntu:~/vss-tools$  . /home/user/vss-tools/.venv/bin/activate
(vss-tools) user@ubuntu:~/vss-tools$ ./vspec2yaml.py
usage: vspec2yaml.py [-h] [-I dir] [-e EXTENDED_ATTRIBUTES] [-s] [--abort-on-unknown-attribute] [--abort-on-name-style] [--format format] [--uuid]
                     [--no-uuid]  [-o overlays] [-u unit_file] [--json-all-extended-attributes] [--json-pretty] [--yaml-all-extended-attributes]
                     [-v version] [--all-idl-features] [--gqlfield GQLFIELD GQLFIELD]
                     <vspec_file> <output_file>
vspec2yaml.py: error: the following arguments are required: <vspec_file>, <output_file>
```

## Native Setup

It is also possible to run the tools in native setup if you have a matching Python environment.
The setup example shown below is based on a fresh minimal install of Ubuntu 22.04.

The first step is to make sure that python and required dependencies are installed. A possible installation flow is shown below.


```sh
# Install Python, in this case Python 3.10 as that is a version available on the update sites of Ununtu 22.04
sudo apt update
sudo apt install python3.10

# For convenience make Python 3.10 available as default Python
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.10 100

# Install required dependencies, running pip without sudo means that a user installation will be performed
sudo apt install pip
pip install anytree deprecation graphql-core
```

The environment can be tested by calling one of the tools without arguments, then usage instructions shall be printed similar to below.

```sh
user@ubuntu:~/vss-tools$ ./vspec2csv.py
usage: vspec2csv.py [-h] [-I dir] [-e EXTENDED_ATTRIBUTES] [-s] [--abort-on-unknown-attribute] [--abort-on-name-style] [--format format] [--uuid]
                    [--no-uuid] [-o overlays] [-u unit_file] [--json-all-extended-attributes] [--json-pretty] [--yaml-all-extended-attributes]
                    [-v version] [--all-idl-features] [--gqlfield GQLFIELD GQLFIELD]
                    <vspec_file> <output_file>
vspec2csv.py: error: the following arguments are required: <vspec_file>, <output_file>

```

## Installing additional tools

If you intend to run testcases related to `vspec2protobuf.py` you need to install the protobuf compiler

```sh
sudo apt update
sudo apt install -y golang-go protobuf-compiler
protoc --version  # Ensure compiler version is 3+
```

## Pre-commit set up
This repository is set up to use pre-commit hooks. After you clone the project, run `pre-commit install` to install pre-commit into your git hooks. pre-commit will now run on every commit. Every time you clone a project using pre-commit running pre-commit install should always be the first thing you do.

## Building and installing with Pip

For usage of VSS-Tools with Pip (PyPI) please see [README-PYPI.md](README-PYPI.md)

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

 Tool | Description | Tool Category | Documentation |
| ------------------ | ----------- | -------------------- |-------------------- |
| [vspec2x.py](vspec2x.py) | Parses and expands VSS into different text based output formats. Currently supports `json`, `yaml`,`csv`,`idl`  | Community Supported | Try `./vspec2x --help` or check [vspec2x documentation](docs/vspec2x.md) |
[vspec2csv.py](vspec2csv.py) | Shortcut for [vspec2x.py](vspec2x.py) generating CSV output | Community Supported |  Check [vspec2x documentation](docs/vspec2x.md) |
[vspec2ddsidl.py](vspec2ddsidl.py) | Shortcut for [vspec2x.py](vspec2x.py) generating DDS-IDL output | Community Supported | [VSS2DDSIDL Documentation](docs/VSS2DDSIDL.md). For general parameters check [vspec2x documentation](docs/vspec2x.md) |
[vspec2json.py](vspec2json.py) |  Shortcut for [vspec2x.py](vspec2x.py) generating JSON output | Community Supported | Check [vspec2x documentation](docs/vspec2x.md) |
[vspec2yaml.py](vspec2yaml.py) | Shortcut for [vspec2x.py](vspec2x.py) generating flattened YAML output | Community Supported | Check [vspec2x documentation](docs/vspec2x.md) |
[vspec2binary.py](vspec2binary.py) | The binary toolset consists of a tool that translates the VSS YAML specification to the binary file format (see below), and two libraries that provides methods that are likely to be needed by a server that manages the VSS tree, one written in C, and one in Go | Community Supported | [vspec2binary Documentation](binary/README.md). For general parameters check [vspec2x documentation](docs/vspec2x.md) | 
[vspec2franca.py](vspec2franca.py) | Parses and expands a VSS and generates a Franca IDL specification | Community Supported | Check [vspec2x documentation](docs/vspec2x.md) |
[vspec2c.py](contrib/vspec2c.py) | The vspec2c tooling allows a vehicle signal specification to be translated from its source YAML file to native C code that has the entire specification encoded in it. | Obsolete (2022-11-01) | [Documentation](obsolete/vspec2c/README.md) |
[vspec2ocf.py](contrib/ocf/vspec2ocf.py) | Parses and expands a VSS and generates a OCF specification | Obsolete (2022-11-01) | - |
[vspec2proto.py](contrib/vspec2protobuf.py) | Parses and expands a VSS and generates a Protobuf specification | Contrib | - |
[vspec2ttl.py](contrib/vspec2ttl/vspec2ttl.py) | Parses and expands a VSS and generates a TTL specification | Contrib  | - |
[vspec2graphql.py](contrib/vspec2graphql.py) | Parses and expands a VSS and generates a GraphQL specification | Community Supported  | [Documentation](docs/VSS2GRAPHQL.md) |

## Tool Architecture

All current tools are based on common Python functionality in the `vspec` folder to read, parse and expand a Vehicle Signal Specification files(*.vspec files). As an example, if the standard [VSS root file](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/VehicleSignalSpecification.vspec) is given as input then the Python tooling will read all included files, do a validation of the content, expand any instances used and create an in-memory representation which then can be used by specialized tools to generate the wanted output.

## Getting started

### Prerequisites
* Python 3.8.12 installed
* If the installation (pip install) is executed behind a (corporate) proxy, the following environments variables must be set: `http_proxy` and `https_proxy` (including authentication e.g., `http://${proxy_username):$(proxy_password)@yourproxy.yourdomain`)
* If you do not run with administration rights, you may need to configure pip target path to write to your user home directory or consider [using the `pipenv` method](#setup-with-pipenv).

```
On Unix and Mac OS X the configuration file is: $HOME/.pip/pip.conf
If the file does not exist, create an empty file with that name.

Add or replace the following lines:
[global]
target=/somedir/where/your/account/can/write/to

On Windows, the configuration file is: %HOME%\pip\pip.ini 
If the file does not exist, create an empty file with that name.

Add or replace the following lines:
[global]
target=C:\SomeDir\Where\Your\Account\Can\Write\To
```
### Project Setup

* Checkout vss-tools as submodule of the Vehicle Signal Specification repository (`git clone --recurse-submodules -j8 https://github.com/COVESA/vehicle_signal_specification.git`)
* If you use a custom pip installation directory, set the `PYTHONPATH` environment variable to the directory that you set in the `pip.ini` file.

### Setup with `pipenv`
[pipenv](https://pypi.org/project/pipenv/) is a tool that manages a virtual environment and install the package and its dependencies, making the process much simpler and predictable, since the `Pipfile` states the dependencies, while `Pipfile.lock` freezes the exact version in use.

If [`pyenv` shell command](https://github.com/pyenv/pyenv) is not installed, use its [installer](https://github.com/pyenv/pyenv-installer) to get it:

```sh
curl https://pyenv.run | bash  # download and install
exec $SHELL                    # restart your shell using the new $PATH
```

Make sure Python version 3.8.12 is installed:
```sh
pyenv install 3.8.12  # install the versions required by Pipfile
```

Install this project and its dependencies in the local `.venv` folder in this project, then use it (`pipenv shell`):
```sh
export PIPENV_VENV_IN_PROJECT=1 # will create a local `.venv` in the project, otherwise uses global location
pipenv install --dev # install the development dependencies as well
pipenv shell         # starts a shell configured to use the virtual environment
```

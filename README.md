# VSS Tools


[![License](https://img.shields.io/badge/License-MPL%202.0-blue.svg)](https://opensource.org/licenses/MPL-2.0)
[![Build Status](https://github.com/COVESA/vss-tools/actions/workflows/buildcheck.yml/badge.svg)](https://github.com/COVESA/vss-tools/actions/workflows/buildcheck.yml?query=branch%3Amaster)

The overall goal of VSS Tools is to provide a set of tools that can be used to convert or verify Vehicle Signal Specifications defined by the format specified by the [COVESA VSS project](https://github.com/COVESA/vehicle_signal_specification). VSS Tools is developed in parallel with VSS, please visit the [COVESA VSS project](https://github.com/COVESA/vehicle_signal_specification) for information on how to contribute.

## Available Tools

This repository contains two types of tools. Community Supported Tools are tools that are actively maintained by the VSS community. They are run as part of the Continuous Integration process for both this repository and for the [COVESA VSS project repository](https://github.com/COVESA/vehicle_signal_specification), and pull request will normally not be merged if any of the tools fails. That assures that the tools always are compatible with the latest version of the COVESA VSS.

In addition this repository also contains contributed tools. These are tools that are not actively maintained by the VSS community. Instead they are maintained by individual contributors, or not maintained at all. Even if many of them are run as part of the continuous integration process, it is not a requirement that they must run successfully on the latest VSS version and a change in VSS may be merged even if it cause some contributed tools to fail. 

Examples on tool usage can be found in the [VSS Makefile](https://github.com/COVESA/vehicle_signal_specification/blob/master/Makefile) and in tool-specific documentation, if existing.

 Tool | Description | Type of Tool | Documentation |
| ------------------ | ----------- | -------------------- |-------------------- |
| [vspec2binary.py](vspec2binary.py) | The binary toolset consists of a tool that translates the VSS YAML specification to the binary file format (see below), and two libraries that provides methods that are likely to be needed by a server that manages the VSS tree, one written in C, and one in Go | Community Supported | [Documentation](binary/README.md) | 
[vspec2csv.py](vspec2csv.py) | Parses and expands a VSS and generates a text file with comma separated values, one line for each signal | Community Supported | - |
[vspec2franca.py](vspec2franca.py) | Parses and expands a VSS and generates a Franca IDL specification | Community Supported | - |
[vspec2json.py](vspec2json.py) | Parses and expands a VSS and generates a JSON specification | Community Supported | - |
[test_contants.py](tests/model/test_contants.py) | Tool used for internal testing  | Community Supported | - |
[test_vsstree.py](tests/model/test_vsstree.py) | Tool used for internal testing | Community Supported | - |
[vspec2yaml.py](vspec2yaml.py) | This tool converts the vspec files into a single YAML file with all instances expanded and UUID added. | Community Supported | - |
[vspec2c.py](contrib/vspec2c.py) | The vspec2c tooling allows a vehicle signal specification to be translated from its source YAML file to native C code that has the entire specification encoded in it. | Contrib (Obsolete, no longer functional) | [Documentation](contrib/vspec2c/README.md) |
[vspec2ocf.py](contrib/ocf/vspec2ocf.py) | Parses and expands a VSS and generates a OCF specification | Contrib (Obsolete, no longer functional)  | - |
[vspec2proto.py](contrib/vspec2protobuf.py) | Parses and expands a VSS and generates a Protobuf specification | Contrib (Beta)  | - |
[vspec2ttl.py](contrib/vspec2ttl/vspec2ttl.py) | Parses and expands a VSS and generates a TTL specification | Contrib  | - |
[vspec2graphql.py](contrib/vspec2graphql.py) | Parses and expands a VSS and generates a GraphQL specification | Contrib  | - |

## Tool Architecture

All current tools are based on common Python functionality in the `vspec` folder to read, parse and expand a Vehicle Signal Specification files(*.vspec files). As an example, if the standard [VSS root file](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/VehicleSignalSpecification.vspec) is given as input then the Python tooling will read all included files, do a validation of the content, expand any instances used and create an in-memory representation which then can be used by specialized tools to generate the wanted output.

## Getting started

### Prerequisites
* Python 3.7 installed
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

Make sure Python version 3.8.5 is installed:
```sh
pyenv install 3.8.5  # install the versions required by Pipfile
```

Install this project and its dependencies in the local `.venv` folder in this project, then use it (`pipenv shell`):
```sh
export PIPENV_VENV_IN_PROJECT=1 # will create a local `.venv` in the project, otherwise uses global location
pipenv install --dev # install the development dependencies as well
pipenv shell         # starts a shell configured to use the virtual environment
```

### Setup using plain `pip install`
* RUN  ```pip install -e .``` from the vss-tools project root directory
* Run  ```pip install -r requirements.txt```  from the vss-tools project root directory


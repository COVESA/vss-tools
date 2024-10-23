# VSS-Tools Changelog

The intention of this document is to highlight major changes in VSS-Tools.
It shall include all changes that affect backward compatibility or may be important to know when upgrading from one version to another.
It includes changes that are included in released version, but also changes planned for upcoming releases.

*This document only contain changes introduced in VSS-Tools 3.0 or later!*


## Implemented changes for VSS-Tools 6.0

### Change in UUID handling.

As the tool [vspec2id](docs/id.md) has been added the VSS-project has agreed that there no longer is a need to support
the legacy uuid functionality.

* The parameters `--uuid`/`--no-uuid` are now removed.

Columns (or similar) for UUID in generated output has also been removed.
An exception is binary output which still contain a byte for UUID, however always 0.

## VSS-Tools 5.0

### Major restructure of repository structure and CLI

The vss-tools repository content structure and CLI has changed significantly
For more information see [vspec documentation](docs/vspec.md)

### Change in UUID handling.

As the tool [vspec2id](docs/id.md) has been added the VSS-project has agreed that there no longer is a need to support
the legacy uuid functionality.

* The parameter `--uuid` is now deprecated and a warning is given if used.

*No warning given any longer if `--no-uuid` is used due to refactored cli interface*

### Tools installed as binaries without `.py` extension

The project has been switched to poetry and all tools are available in your PATH once vss-tools is installed via pip.

### Logging arguments

General args have been extended with logging arguments `--log-level` and `--log-file`.

## SAMM Exporter added

See [documentation](https://github.com/COVESA/vss-tools/blob/master/docs/samm.md)

## APIGEAR Exporter added

See [documentation](https://github.com/COVESA/vss-tools/blob/master/docs/apigear.md)

## VSS-Tools 4.2

No significant changes in vss-tools


## VSS-Tools 4.1

### Struct support in vspec2ddsidl

The vspec2ddsidl tool now supports structs

### Jsonschema tool added

A new tool vspec2jsonschema has been added

### Id generator tool added

A new tool vspec2id has been added. It can be used to generate and maintain unique identifiers for signals.

### Unit files and quantity files

A new syntax has been introduced for unit files. The old syntax is still supported.
Domains have now been renamed to Quantities.
In addition to this a quantity file format has been defined, and the tool will inform
if units refer to a quantity that has not been defined an information message will be printed.


## VSS-Tools 4.0

### Struct support feature

In VSS-Tools 4.0 structs are supported in the following exporters:

* JSON
* Yaml
* CSV
* Protobuf

Other exporters do not support structs.

It is possible to use specify muliple type files with `--types`, and to use types in combination with overlays.
For more information see [vspec documentation](docs/vspec.md)

### Change in UUID handling.

For VSS-Tools 4.0 the following behavior is implemented:

* By default no UUIDs are generated.
* The parameter `--no-uuid` is now considered deprecated, and a warning is given if `--no-uuid` is used.
* No warning is given if neither `--uuid` nor `--no-uuid` is used.
* If both `--uuid` and `--no-uuid` is used an error is given.

### Default unit file removed from vss-tools

The default unit file `config.yaml`
has been removed from VSS-tools. This means that either a file `units.yaml` in the same directory as the `*.vspec`
file must exist, or a unit file must be specified by `-u`.
From now on, if new units are needed for the VSS catalog they shall be added to the
[VSS catalog file](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/units.yaml).


## VSS-Tools 3.1

[Complete release notes including VSS-Tools changes](https://github.com/COVESA/vehicle_signal_specification/releases/tag/v3.1)

### Struct Support

Support for defining signals with struct type added.
For VSS 3.1 as experimental feature only supported by JSON exporter.
For more information see [vspec documentation](docs/vspec.md)

### Change in UUID handling.

As of today most tools in this repository add UUIDs to generated output by default. An parameter `--no-uuid` exists to suppress output of UUIDs.
It has been decided in VSS-project to change default behavior so that default is to not generate UUIDs.
The change will be gradually introduced over multiple releases.

For VSS-Tools 3.1 the following behavior is implemented:

* Generation of UUIDs is still default.
* A new parameter `--uuid` has been introduced to explicitly request that UUIDs shall be generated.
* If neither `--uuid` nor `--no-uuid` is used a warning will be given informing that default behavior will change in the future.
* If both `--uuid` and `--no-uuid` is used an error will be given.

### The tools vspec2c and vspec2ocf are now obsolete

The tools vspec2c and vspec2ocf in the contrib folder has been moved to the obsolete folder.
The background is that they have been broken for a long period and no one has volunteered to fix them.

### Support for specifying unit files

Add new parameter `-u` has been introduced, see [documentation](https://github.com/COVESA/vss-tools/blob/master/docs/vspec.md#handling-of-units).
Use of default unit file deprecated.
At the same time a unit file has been added to [VSS](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/units.yaml),
allowing VSS tooling to control their own units rather than relying on units in VSS-tools.
Default behavior for units have changed, if there is a file `units.yaml` in the same directory as the `*.vspec`
file it will be used, only if not existing `config.yaml` in vss-tools will be used.

## VSS-Tools 3.0

[Complete release notes including VSS-Tools changes](https://github.com/COVESA/vehicle_signal_specification/releases/tag/v3.0)

### Overlay Support

Overlays introduced to allow customization of VSS. See [documentation](https://covesa.github.io/vehicle_signal_specification/rule_set/overlay/).
See [vss-tools documentation](https://github.com/COVESA/vss-tools/blob/master/docs/vspec.md) on how to include overlays when transforming VSS.

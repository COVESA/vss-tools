# VSS-Tools Changelog

The intention of this document is to highlight major changes in VSS-Tools.
It shall include all changes that affect backward compatibility or may be important to know when upgrading from one version to another.
It includes changes that are included in released version, but also changes planned for upcoming releases.

*This document only contain changes introduced in VSS-Tools 3.0 or later!*



## VSS-Tools 3.0

[Complete release notes including VSS-Tools changes](https://github.com/COVESA/vehicle_signal_specification/releases/tag/v3.0)

### Overlay Support

Overlays introduced to allow customization of VSS. See [documentation](https://covesa.github.io/vehicle_signal_specification/rule_set/overlay/).
See [vss-tools documentation](https://github.com/COVESA/vss-tools/blob/master/docs/vspec2x.md) on how to include overlays when transforming VSS.

## VSS-Tools 3.1 (Latest Release)

[Complete release notes including VSS-Tools changes](https://github.com/COVESA/vehicle_signal_specification/releases/tag/v3.1)

### Struct Support

Support for defining signals with struct type added.
For VSS 3.1 as experimental feature only supported by JSON exporter.
For more information see [vspec2x documentation](docs/vspec2x.md)

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

Add new parameter `-u` has been introduced, see [documentation](https://github.com/COVESA/vss-tools/blob/master/docs/vspec2x.md#handling-of-units).
Use of default unit file deprecated.
At the same time a unit file has been added to [VSS](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/units.yaml),
allowing VSS tooling to control their own units rather than relying on units in VSS-tools.
Default behavior for units have changed, if there is a file `units.yaml` in the same directory as the `*.vspec`
file it will be used, only if not existing `config.yaml` in vss-tools will be used.

## VSS-Tools 4.0

### Struct support feature

In VSS-Tools 4.0 structs are supported in the following exporters:

* JSON
* Yaml
* CSV
* Protobuf

Other exporters do not support structs.

It is possible to use specify muliple type files with `-vt`, and to use types in combination with overlays.
For more information see [vspec2x documentation](docs/vspec2x.md)

### Change in UUID handling.

For VSS-Tools 4.0 the following behavior is implemented:

* By default no UUIDs are generated.
* The parameter `--no-uuid` is now considered deprecated, and a warning is given if `--no-uuid` is used.
* No warning is given if neither `--uuid` nor `--no-uuid` is used.
* If both `--uuid` and `--no-uuid` is used an error is given.

### Default unit fileremoved from vss-tools

The default unit file `config.yaml`
has been removed from VSS-tools. This means that either a file `units.yaml` in the same directory as the `*.vspec`
file must exist, or a unit file must be specified by `-u`.
From now on, if new units are needed for the VSS catalog they shall be added to the
[VSS catalog file](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/units.yaml).

## Planned Changes VSS-Tools 4.1

Adding of struct support for exporters currently not supporting structs.

## Planned Changes VSS-Tools 5.0


### Change in UUID handling.

For VSS-Tools 5.0 the following behavior shall be implemented:

* The parameter `--no-uuid` shall now be removed, and an error shall be given if `--no-uuid` is used.

# VSS-Tools Changelog

The intention of this document is to highlight major changes in VSS-Tools.
It shall include all changes that affect backward compatibility or may be important to know when upgrading from one version to another.
It includes changes that are included in released version, but also changes planned for upcoming releases.

*This document only contain changes introduced in VSS-Tools 3.0 or later!*



## VSS-Tools 3.0 (Latest Release)

[Complete release notes including VSS-Tools changes](https://github.com/COVESA/vehicle_signal_specification/releases/tag/v3.0)



### Overlay Support

Overlays introduced to allow customization of VSS. See [documentation](https://covesa.github.io/vehicle_signal_specification/rule_set/overlay/).
See [vss-tools documentation](https://github.com/COVESA/vss-tools/blob/master/docs/vspec2x.md) on how to include overlays when transforming VSS.

## Planned Changes VSS-Tools 3.1

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

## Planned Changes VSS-Tools 4.0

### Change in UUID handling.

For VSS-Tools 4.0 the following behavior shall be implemented:

* By default no UUIDs shall be generated.
* The parameter `--no-uuid` is now considered deprecated, and a warning shall be given if `--no-uuid` is used.
* No warning shall be given if neither `--uuid` nor `--no-uuid` is used.
* If both `--uuid` and `--no-uuid` is used an error shall be given.


## Planned Changes VSS-Tools 5.0


### Change in UUID handling. 

For VSS-Tools 5.0 the following behavior shall be implemented:

* The parameter `--no-uuid` shall now be removed, and an error shall be given if `--no-uuid` is used.


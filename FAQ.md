# Frequently asked questions

## How to include my own units?

Standard VSS units are specified in the vehicle_signal_specification at the
(data_unit_types)[https://github.com/COVESA/vehicle_signal_specification/blob/master/docs-gen/content/rule_set/data_entry/data_unit_types.md] file.
Tooling use by default the file (config.yaml)[https://github.com/COVESA/vss-tools/blob/master/vspec/config.yaml]
which should correspond to the definition in VSS.

It is possible to replace the default units by the `-u` parameter, see [vspec2x documentation](../doc/vspec2x.md).

The syntax of the file with units shall follow this pattern:

```
units:
  puncheon:
    label: Puncheon
    description: Volume measure in puncheons (1 puncheon = 318 liters)
    domain: volume
  hogshead:
    label: Hogshead
    description: Volume measure in hogsheads (1 hogshead = 238 liters)
    domain: volume
```

# Frequently asked questions

## How to include my own units?

VSS standard catalog uses the units defined in [this file](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/units.yaml).
They are also described in the [VSS documentation](https://github.com/COVESA/vehicle_signal_specification/blob/master/docs-gen/content/rule_set/data_entry/data_unit_types.md).

It is possible to replace the default units by the `-u` parameter, see [vspec2x documentation](docs/vspec2x.md).

The syntax of the file with units shall follow this pattern:

```
puncheon:
  definition: Volume measure in puncheons (1 puncheon = 318 liters)
  unit: Puncheon
  quantity: volume
  allowed_datatypes: ['uint16', 'int16']
hogshead:
  definition: Volume measure in hogsheads (1 hogshead = 238 liters)
  unit: Hogshead
  quantity: volume
  allowed_datatypes: ['numeric']
```


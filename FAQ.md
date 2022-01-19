# Frequently asked questions

### How to include my own units?

Standard units are located at the vehicle_signal_specification at the
(data_unit_types)[https://github.com/COVESA/vehicle_signal_specification/blob/master/docs-gen/content/rule_set/data_entry/data_unit_types.md]
file. It's not possible to overwrite current units, but if you want to add extra
units you can create a new file using the same pattern as the current
(config.yaml)[https://github.com/COVESA/vss-tools/blob/master/vspec/config.yaml].


Suppose I have this file called `my_config.yaml`:
```yaml
units:
  lx:
    label: lux
    description: Illuminance measured in lux
    domain: illuminance
```

The main use is in the `Unit.add_config(my_units)` call.
Here follows a code that you can use in your part to add units:

```python
import yaml
from typing import TextIO, Dict
from vspec.model.constants import Unit

def get_config_dict(yaml_file: TextIO, key: str) -> Dict[str, Dict[str, str]]:
    yaml_config = yaml.safe_load(yaml_file)
    configs = yaml_config.get(key, {})
    return configs


with open('my_config.yaml') as my_yaml_file:
    my_units = get_config_dict(my_yaml_file, 'units')
    Unit.add_config(my_units)
```

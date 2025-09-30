# Tree Exporter

The `tree` exporter wraps [Anytree RenderTree](https://anytree.readthedocs.io/en/latest/api/anytree.render.html#anytree.render.RenderTree).
Additionally it can include information you are interested in of the `VSSData` of every node.
By default, the rendered tree will only print node names.
The output file specified via `--output/-o` will be a simple text file containing the rendered tree.

Example:
```yaml
Vehicle:
  type: branch
  description: Vehicle

Vehicle.Door:
  type: branch
  description: Door
  instances:
  - Row[1,2]
  - Column[1,2]

Vehicle.Door.Row1.Column1:
  custom: foo
```

Result:
```
Vehicle
└── Door
    ├── Row1
    │   ├── Column1
    │   └── Column2
    └── Row2
        ├── Column1
        └── Column2
```

If we also want to see the `description` of every node we can pass `--attr description`.

Result:
```
Vehicle
description='Vehicle'
└── Door
    description='Door'
    ├── Row1
    │   description='Door'
    │   ├── Column1
    │   │   description='Door'
    │   └── Column2
    │       description='Door'
    └── Row2
        description='Door'
        ├── Column1
        │   description='Door'
        └── Column2
            description='Door'
```

If we also want to show the custom attribute `custom` we can add another `-a custom`.

Result:
```
Vehicle
description='Vehicle'
└── Door
    description='Door'
    ├── Row1
    │   description='Door'
    │   ├── Column1
    │   │   description='Door'
    │   │   custom='foo'
    │   └── Column2
    │       description='Door'
    └── Row2
        description='Door'
        ├── Column1
        │   description='Door'
        └── Column2
            description='Door'
```

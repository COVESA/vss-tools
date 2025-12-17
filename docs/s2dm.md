# S2DM Exporter

This exporter converts a given specification written in `vspec` into the [GraphQL Schema Definition Language (`SDL`)](https://graphql.org/learn/schema/) format.
It uses `SDL` in a way that is compatible with the [Simplified Semantic Data Modeling (`S2DM`)](https://github.com/COVESA/s2dm) approach.

> [!NOTE] The output of this exporter does not target a GraphQL API itself. It aims to use the semantics of the `SDL` language as a way to formalize the data of a domain with more features than what the `vspec` currently offers.

> [!WARNING] `SDL` is a language that has more expressiveness than `vspec`, which implies:
> - All the features from `vspec` are mappable to `SDL`.
> - Not all the features of `SDL` are mappable back to `vspec`.

## What is S2DM?

[Simplified Semantic Data Modeling (`S2DM`)](https://github.com/COVESA/s2dm) is a pragmatic approach to data modeling that uses [GraphQL `SDL`](https://graphql.org/learn/schema/) as a the core modeling language.
It aims to balance:
- **Semantic rigor** (what `vspec` lacks), and
- **Usability for non-modelers** (what `vspec` offers)

## What does the S2DM exporter do?

The S2DM exporter takes a given `vspec` specification and generates a GraphQL schema that is compatible with the `S2DM` approach and its tools.
Some of the aspects that are covered in this conversion are, for example:

- **Moving from the `vspec` one-tree structure to GraphQL type system** - One can then arbitrarily model in a graph structure.
- **Preserving all `vspec` information** - Every metadata from the given `vspec` specification is kept using dedicated directives, mapping of datatypes, units, etc.
- **Supporting instances as re-usable types instead of plain text** - Creates proper GraphQL types for re-usable multi-dimensional instantiation of entities.


### Complete VSS traceability
Elements in the generated GraphQL schema can include a `@vspec` directive that tells you exactly where it came from:

```graphql
"""All in-cabin components, including doors."""
type Vehicle_Cabin @vspec(source: {kind: FQN, value: "Vehicle.Cabin"}, vspecType: BRANCH) {
    """The position of the driver seat in row 1."""
    driverPosition: Vehicle_Cabin_DriverPosition_Enum
      @vspec(
        source: {kind: FQN, value: "Vehicle.Cabin.DriverPosition"},
        vspecType: ATTRIBUTE,
        comment: "Driver seat position configuration"
      )
}
```
In this example, the metadata shows that the `Vehicle_Cabin` type was derived from the Fully-Qualified Name (FQN) `Vehicle.Cabin`, and that is was a `BRANCH`.
Likewise, the `driverPosition` was derived from `Vehicle.Cabin.DriverPosition` and it was an `ATTRIBUTE`.

### VSS Data Types Support
The exporter handles all `vspec` data types as follows:
- **Strings** → GraphQL String
- **Numbers** → GraphQL Int, Float, or custom scalars (Int8, UInt16, etc.)
- **Booleans** → GraphQL Boolean
- **Arrays** → GraphQL Lists
- **Allowed values** → GraphQL Enums

### VSS Instances Become GraphQL Structures
When your `vspec` has instances (like multiple seats), the exporter creates proper GraphQL types:

```graphql
# From vspec instances: ['Row[1,2]', ['DriverSide', 'PassengerSide']]
type Vehicle_Cabin_Seat_InstanceTag @instanceTag {
    dimension1: Vehicle_Cabin_Seat_InstanceTag_Dimension1  # Row1, Row2
    dimension2: Vehicle_Cabin_Seat_InstanceTag_Dimension2  # DriverSide, PassengerSide
}

enum Vehicle_Cabin_Seat_InstanceTag_Dimension1 {
  Row1
  Row2
}

enum Vehicle_Cabin_Seat_InstanceTag_Dimension2 {
  DriverSide
  PassengerSide
}
```
Such an structure is then usable by any other type like:
```graphql
type Vehicle_Cabin_Seat {
  instanceTag: Vehicle_Cabin_Seat_InstanceTag
  ...
}
```

### Range Constraints Preserved

The `min` and `max` values become GraphQL `@range` directives:

```graphql
temperature: Float @range(min: -40, max: 85)
```

### Unit Support
Units are handled as enums, which are used as field arguments:

```graphql
speed(unit: VelocityUnitEnum = "KILOMETERS_PER_HOUR"): Float
```
```graphql
enum VelocityUnitEnum {
  KILOMETERS_PER_HOUR
  MILES_PER_HOUR
}
```

## Usage
For up-to-date instructions, assuming the virtual environment is active, simply consult the help in the vss-tools CLI with this command:
```shell
vspec export s2dm --help
```





## Example

Given the following `vspec`:

```yaml
Vehicle:
  type: branch
  description: High-level vehicle data.

Vehicle.Speed:
  datatype: float
  type: sensor
  unit: km/h
  description: Vehicle speed.
  min: 0
  max: 300
```

The exporter generates:

```graphql
"""High-level vehicle data."""
type Vehicle @vspec(source: {kind: FQN, value: "Vehicle"}, vspecType: BRANCH) {
  """Vehicle speed."""
  speed(unit: VelocityUnitEnum = "KILOMETERS_PER_HOUR"): Float @range(min: 0, max: 300) @vspec(
    source: {kind: FQN, value: "Vehicle.Speed"},
    vspecType: SENSOR
  )
}

enum VelocityUnitEnum {
  KILOMETERS_PER_HOUR @vspec(source: {kind: UNIT, value: "km/h"})
  METERS_PER_SECOND @vspec(source: {kind: UNIT, value: "m/s"})
  MILES_PER_HOUR @vspec(source: {kind: UNIT, value: "mph"})
}
```

## Output Structures

The S2DM exporter supports three output modes:

### 1. Single File (Default)

Generates one complete GraphQL schema file.

```bash
vspec export s2dm --vspec spec.vspec --output schema.graphql
```

**Output:**
```
schema.graphql    # Complete schema in one file
```

**Use when:**
- Working with small to medium specifications
- You want everything in one place
- Simplicity is preferred

---

### 2. Modular Flat

Splits schema into multiple files with flat directory structure. Files use full concatenated type names.

```bash
vspec export s2dm --vspec spec.vspec --output output_dir/ --modular
```

**Output:**
```
output_dir/
├── other/
│   ├── directives.graphql       # Custom directives (@vspec, @range, @instanceTag)
│   ├── scalars.graphql          # Custom scalars (Int8, UInt16, etc.)
│   ├── queries.graphql          # Root Query type
│   └── units.graphql            # Unit enums
├── domain/
│   ├── Vehicle.graphql
│   ├── Vehicle_Cabin.graphql
│   ├── Vehicle_Cabin_Door.graphql
│   ├── Vehicle_Cabin_Seat.graphql
│   └── Vehicle_Cabin_Seat_Airbag.graphql
└── instances/
    └── Vehicle_Cabin_Seat_InstanceTag.graphql
```

**Characteristics:**
- All domain types in one folder
- File names match GraphQL type names exactly
- Perfect alphabetical grouping (all `Vehicle_Cabin_*` together)
- Easy to search and navigate

**Use when:**
- Schema is large but you want simple navigation
- You prefer flat structures over deep nesting
- Alphabetical ordering is important

---

### 3. Modular Nested

Splits schema into hierarchical folder structure. Root types use `_` prefix, child types use immediate names only.

```bash
vspec export s2dm --vspec spec.vspec --output output_dir/ --modular --nested-domains
```

**Output:**
```
output_dir/
├── other/
│   ├── directives.graphql
│   ├── scalars.graphql
│   ├── queries.graphql
│   └── units.graphql
├── domain/
│   └── Vehicle/
│       ├── _Vehicle.graphql              # Root type (underscore sorts first)
│       ├── VehicleIdentification.graphql # Direct child (Vehicle_VehicleIdentification)
│       └── Cabin/
│           ├── _Cabin.graphql            # Root type (Vehicle_Cabin)
│           ├── Door.graphql              # Child type (Vehicle_Cabin_Door)
│           └── Seat/
│               ├── _Seat.graphql         # Root type (Vehicle_Cabin_Seat)
│               ├── Airbag.graphql        # Child type (Vehicle_Cabin_Seat_Airbag)
│               └── Occupant.graphql      # Child type (Vehicle_Cabin_Seat_Occupant)
└── instances/
    └── Vehicle_Cabin_Seat_InstanceTag.graphql
```

**Characteristics:**
- Hierarchical folder structure mirrors VSS tree
- Root types use `_` prefix to sort first in folder
- File names show only immediate type (folder provides context)
- Logical grouping by domain

**Use when:**
- Schema is very large and benefits from logical grouping
- You prefer hierarchical organization
- Different teams own different domains

---

### Allowed Value Enums

In all modular modes, allowed value enums are embedded in the same file as the type that uses them:

```graphql
# In domain/Vehicle/Cabin/_Cabin.graphql

type Vehicle_Cabin {
  driverPosition: Vehicle_Cabin_DriverPosition_Enum
}

enum Vehicle_Cabin_DriverPosition_Enum {
  LEFT_HAND_DRIVE
  RIGHT_HAND_DRIVE
}
```

This keeps related enums with their types for better maintainability.


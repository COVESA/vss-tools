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
type Vehicle_Cabin @vspec(element: BRANCH, fqn: "Vehicle.Cabin") {
    """The position of the driver seat in row 1."""
    driverPosition: Vehicle_Cabin_DriverPosition_Enum
      @vspec(
        element: ATTRIBUTE,
        fqn: "Vehicle.Cabin.DriverPosition",
        metadata: [{key: "comment", value: "Driver seat position configuration"}]
      )
}
```
In this example, the metadata shows that the `Vehicle_Cabin` type was derived from the Fully-Qualified Name (FQN) `Vehicle.Cabin`, and that is was a `BRANCH`.
Likewise, the `driverPosition` was derived from `Vehicle.Cabin.DriverPosition` and it was an `ATTRIBUTE`.

The `@vspec` directive is also used to annotate original names when they have been modified for GraphQL compliance (for example, see [Enum Value Sanitization](#enum-value-sanitization)).

### VSS Data Types Support
The exporter handles all `vspec` data types as follows:
- **Strings** → GraphQL String
- **Numbers** → GraphQL Int, Float, or custom scalars (Int8, UInt16, etc.)
- **Booleans** → GraphQL Boolean
- **Arrays** → GraphQL Lists
- **Allowed values** → GraphQL Enums

#### Enum Value Sanitization

GraphQL enum values must follow strict naming rules (alphanumeric + underscore only, cannot start with a digit). The S2DM exporter automatically sanitizes VSS enum values to comply with GraphQL requirements:

- **Spaces & special characters** → Converted to underscores (`"some value"` → `SOME_VALUE`)
- **CamelCase** → Converted to SCREAMING_SNAKE_CASE (`"HTTPSProtocol"` → `HTTPS_PROTOCOL`)
- **Leading digits** → Prefixed with underscore (`"123abc"` → `_123ABC`)

When enum values are modified, the original VSS value is preserved using `@vspec` metadata:

```graphql
enum Vehicle_Connection_Protocol_Enum @vspec(element: SENSOR, fqn: "Vehicle.Connection.Protocol", metadata: [{key: "allowed", value: "['HTTPSProtocol', 'TCPProtocol']"}]) {
  HTTPS_PROTOCOL @vspec(metadata: [{key: "originalName", value: "HTTPSProtocol"}])
  TCP_PROTOCOL @vspec(metadata: [{key: "originalName", value: "TCPProtocol"}])
}
```

This ensures complete traceability between the VSS source and the generated GraphQL schema.

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

The S2DM exporter requires the output parameter to be a **directory path** (not a file). The output directory will contain the GraphQL schema file(s) and a `vspec_reference/` subdirectory with complete traceability information.

For up-to-date instructions, consult the help:
```shell
vspec export s2dm --help
```

### Basic Usage

```shell
# Export to a directory (creates myOutput/ if it doesn't exist)
vspec export s2dm --vspec spec.vspec --output myOutput/
```

**Output structure:**
```
myOutput/
├── myOutput.graphql                # Complete GraphQL schema
└── vspec_reference/
    ├── README.md                   # Documentation and provenance info
    ├── vspec_lookup_spec.yaml      # Complete VSS tree (fully expanded)
    ├── vspec_units.yaml            # Units used (if provided via -u or implicit)
    └── vspec_quantities.yaml       # Quantities used (if provided via -q or implicit)
```

### VSS Reference Files

The `vspec_reference/` directory provides complete traceability:

- **README.md** - Documents the vss-tools version used, describes each file, and provides a command to regenerate the schema
- **vspec_lookup_spec.yaml** - Complete VSS specification tree (fully processed and expanded) in YAML format
- **vspec_units.yaml** - Unit definitions used during generation (included if units were provided via `-u` flag or implicitly loaded)
- **vspec_quantities.yaml** - Quantity definitions used during generation (included if quantities were provided via `-q` flag or implicitly loaded)

These files allow you to:
1. Trace GraphQL elements back to their VSS source using the FQN in `@vspec` directives
2. Reproduce the exact GraphQL schema by re-running the exporter
3. Understand which input files were used for generation





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
type Vehicle @vspec(element: BRANCH, fqn: "Vehicle") {
  """Vehicle speed."""
  speed(unit: VelocityUnitEnum = "KILOMETERS_PER_HOUR"): Float @range(min: 0, max: 300) @vspec(
    element: SENSOR,
    fqn: "Vehicle.Speed"
  )
}

enum VelocityUnitEnum @vspec(element: QUANTITY_KIND, metadata: [{key: "quantity", value: "velocity"}]) {
  KILOMETERS_PER_HOUR @vspec(element: UNIT, metadata: [{key: "unit", value: "km/h"}])
  METERS_PER_SECOND @vspec(element: UNIT, metadata: [{key: "unit", value: "m/s"}])
  MILES_PER_HOUR @vspec(element: UNIT, metadata: [{key: "unit", value: "mph"}])
}
```

## Output Structures

The S2DM exporter supports three output modes. All modes generate a `vspec_reference/` directory for traceability.

### 1. Single File (Default)

Generates one complete GraphQL schema file in the output directory.

```bash
vspec export s2dm --vspec spec.vspec --output myOutput/
```

**Output:**
```
myOutput/
├── myOutput.graphql                # Complete schema
└── vspec_reference/
    ├── README.md                   # Provenance documentation
    ├── vspec_lookup_spec.yaml      # VSS reference
    ├── vspec_units.yaml            # (if units provided or implicit)
    └── vspec_quantities.yaml       # (if quantities provided or implicit)
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
├── instances/
│   └── Vehicle_Cabin_Seat_InstanceTag.graphql
└── vspec_reference/
    ├── README.md
    ├── vspec_lookup_spec.yaml
    ├── vspec_units.yaml            # (if units provided or implicit)
    └── vspec_quantities.yaml       # (if quantities provided or implicit)
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
├── instances/
│   └── Vehicle_Cabin_Seat_InstanceTag.graphql
└── vspec_reference/
    ├── README.md
    ├── vspec_lookup_spec.yaml
    ├── vspec_units.yaml            # (if units provided or implicit)
    └── vspec_quantities.yaml       # (if quantities provided or implicit)
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


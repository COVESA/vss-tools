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

#### Extended Attributes

If the VSpec model uses extended attributes (custom metadata), the exporter add them to `@vspec` metadata annotations.

**Example VSS with extended attributes `source` and `quality`:**
```yaml
Vehicle.Speed:
  datatype: float
  type: sensor
  unit: km/h
  source: ecu0xAA        # Extended attribute
  quality: 100           # Extended attribute
```

**Generated GraphQL:**
```graphql
type Vehicle {
  speed(unit: VelocityUnitEnum = KILOMETERS_PER_HOUR): Float
    @vspec(
      element: SENSOR,
      fqn: "Vehicle.Speed",
      metadata: [
        {key: "source", value: "ecu0xAA"},
        {key: "quality", value: "100"}
      ]
    )
}
```

Extended attributes work on all VSS elements: branches, sensors, actuators, attributes, and structs.

### VSS Data Types Support
The exporter handles all `vspec` data types as follows:
- **Strings** → GraphQL String
- **Numbers** → GraphQL Int, Float, or custom scalars (Int8, UInt16, etc.)
- **Booleans** → GraphQL Boolean
- **Arrays** → GraphQL Lists (with natural plural field names)
- **Allowed values** → GraphQL Enums

#### List Field Names (Automatic Pluralization)

When VSS branches have instances (like `Seat` with multiple rows/positions), the parent type gets a list field. The S2DM exporter automatically generates **natural plural names** using the inflect library:

- `seat` → `seats: [Vehicle_Cabin_Seat]`
- `door` → `doors: [Vehicle_Cabin_Door]`
- `window` → `windows: [Vehicle_Cabin_Window]`
- `battery` → `batteries: [Vehicle_Battery]`
- `mirror` → `mirrors: [Vehicle_Body_Mirror]`

This improves GraphQL schema readability by following common naming conventions instead of using mechanical suffixes like `_s`.

**Example:**
```graphql
type Vehicle_Cabin {
  """Cabin seats for passengers."""
  seats: [Vehicle_Cabin_Seat]

  """Cabin doors."""
  doors: [Vehicle_Cabin_Door]
}
```

**Tracking:** All pluralized field names are logged to `vspec_reference/pluralized_field_names.yaml` showing the original VSS FQN, the plural field name used, and its location in the GraphQL schema.

#### Enum Value Sanitization

GraphQL enum values must follow strict naming rules (alphanumeric + underscore only, cannot start with a digit). The S2DM exporter automatically sanitizes VSS enum values to comply with GraphQL requirements:

- **Spaces & special characters** → Converted to underscores (`"some value"` → `SOME_VALUE`)
- **CamelCase** → Converted to SCREAMING_SNAKE_CASE (`"HTTPSProtocol"` → `HTTPS_PROTOCOL`)
- **Leading digits** → Prefixed with underscore (`"123abc"` → `_123ABC`)

When enum values are modified, the original VSS value is preserved using `@vspec` metadata for complete traceability. This applies to both **allowed value enums** and **instance dimension enums**.

**Allowed Value Enum Example:**
```graphql
enum Vehicle_Connection_Protocol_Enum @vspec(element: SENSOR, fqn: "Vehicle.Connection.Protocol", metadata: [{key: "allowed", value: "['HTTPSProtocol', 'TCPProtocol']"}]) {
  HTTPS_PROTOCOL @vspec(metadata: [{key: "originalName", value: "HTTPSProtocol"}])
  TCP_PROTOCOL @vspec(metadata: [{key: "originalName", value: "TCPProtocol"}])
}
```

**Instance Dimension Enum Example:**
```graphql
enum Vehicle_Cabin_Seat_InstanceTag_Dimension2 {
  DRIVER_SIDE @vspec(metadata: [{key: "originalName", value: "DriverSide"}])
  PASSENGER_SIDE @vspec(metadata: [{key: "originalName", value: "PassengerSide"}])
}
```

This ensures complete traceability between the VSS source and the generated GraphQL schema.

### GraphQL Type Naming: Short Names with Collision Resolution

**By default**, the S2DM exporter generates **clean, short GraphQL type names** using the last segment of the VSS path:

- `Vehicle.Cabin.Door.Window` → `type Window`
- `Vehicle.Body.Lights` → `type Lights`
- `Vehicle.Chassis.Axle` → `type Axle`

This improves readability and follows GraphQL best practices for concise type names.

#### Progressive Qualification for Name Collisions

Since VSS does not enforce branch name uniqueness (only Fully Qualified Names are unique), the exporter uses **progressive qualification** when collisions are detected:

1. **Try short name first**: `Window`
2. **If collision, add parent**: `Door_Window`, `Windshield_Window`
3. **If still collision, add more ancestors**: `Cabin_Door_Window`, `Body_Windshield_Window`
4. **Last resort: use full FQN**: `Vehicle_Cabin_Door_Window`

**Example from real VSS collisions:**

```graphql
# Vehicle.Cabin.Door.Shade and Vehicle.Cabin.Sunroof.Shade both have short name "Shade"
# Resolution: qualify with parent name
type Door_Shade @vspec(element: BRANCH, fqn: "Vehicle.Cabin.Door.Shade") {
  position: Int
}

type Sunroof_Shade @vspec(element: BRANCH, fqn: "Vehicle.Cabin.Sunroof.Shade") {
  position: Int
}
```

**Console Output:** During export, collision statistics are logged:

```
[INFO] Short name collision resolution:
  ✓ 245 types use short names (no collisions)
  ⚠ 8 types qualified with parent (e.g., Parent_Name)
  ⚠ 2 types qualified with multiple ancestors (e.g., GrandParent_Parent_Name)
  → See vspec_reference/short_name_collisions.yaml for 5 collision groups
```

**Collision Report:** The `vspec_reference/short_name_collisions.yaml` file documents all name collisions and resolutions in a compact format:

```yaml
# Short Name Collision Resolution Report
#
# This file documents how VSS branch names were converted to GraphQL type names.
# Resolution strategy: Progressive parent qualification
#   1. Try short name (e.g., 'Window')
#   2. If collision: add parent (e.g., 'Door_Window', 'Windshield_Window')
#   3. If still collision: add more ancestors (e.g., 'Cabin_Door_Window')
#   4. Last resort: use full FQN with underscores

summary:
  total_branches: 137
  no_collisions: 120
  parent_qualified: 15
  multi_ancestor_qualified: 2
  full_fqn_fallback: 0

# Collisions resolved by adding immediate parent name (e.g., Parent_Name)
parent_qualified:
  - { fqn: Vehicle.Body.Windshield.Shade, type: Windshield_Shade }
  - { fqn: Vehicle.Cabin.Door.Shade, type: Door_Shade }
  - { fqn: Vehicle.Cabin.Sunroof.Shade, type: Sunroof_Shade }

# Collisions resolved by adding multiple ancestor names (e.g., GrandParent_Parent_Name)
multi_ancestor_qualified:
  - { fqn: Vehicle.Powertrain.Engine.Brake, type: Engine_Brake }
  - { fqn: Vehicle.Chassis.Axle.Wheel.Brake, type: Axle_Wheel_Brake }

# Detailed collision groups: branches that share the same short name
collision_groups:
  Axle:  # 4 branches share this name
    - { fqn: Vehicle.Chassis.Axle, type: Chassis_Axle }
    - { fqn: Vehicle.Trailer.Axle, type: Trailer_Axle }
    - { fqn: Vehicle.Chassis.Axle.Wheel.Axle, type: Wheel_Axle }
    - { fqn: Vehicle.Body.Hood.Axle, type: Hood_Axle }
  Shade:  # 2 branches share this name
    - { fqn: Vehicle.Cabin.Door.Shade, type: Door_Shade }
    - { fqn: Vehicle.Cabin.Sunroof.Shade, type: Sunroof_Shade }
```

#### Opting Out: Full FQN Names

To use traditional fully-qualified names with underscores (legacy behavior), use the `--fqn-type-names` flag:

```bash
vspec export s2dm --vspec spec.vspec --output myOutput/ --fqn-type-names
```

This generates:
- `Vehicle.Cabin.Door.Window` → `type Vehicle_Cabin_Door_Window`
- `Vehicle.Body.Lights` → `type Vehicle_Body_Lights`

**When to use `--fqn-type-names`:**
- You need backward compatibility with existing schemas
- Your tooling expects the old naming convention
- You prefer explicit full paths over short names

### GraphQL Naming Convention Warnings

GraphQL best practices recommend using **singular names for types** (e.g., `User` not `Users`, `Product` not `Products`). The S2DM exporter automatically detects VSS branches with plural names and generates warnings to help identify potential naming convention violations.

**Detection:** The exporter uses the inflect library to identify potential plural type names. It maintains a whitelist of known exceptions (acronyms like "ADAS", "ABS", Latin words like "Status", "Chassis") to reduce false positives.

**Warning Output:** When plural type names are detected, two files are generated in `vspec_reference/`:

1. **`plural_type_warnings.yaml`** - Lists all detected plural type names:
   ```yaml
   # WARNING: These elements in the reference model seem to have a plural name...

   Vehicle.Cabin.Lights:
     singular: Light
     currentNameInGraphQLModel: Lights  # or Vehicle_Cabin_Lights if using --fqn-type-names

   Vehicle.Body.Mirrors:
     singular: Mirror
     currentNameInGraphQLModel: Mirrors  # or Vehicle_Body_Mirrors if using --fqn-type-names

   # Whitelisted words (excluded from plural detection):
   whitelisted_non_plurals:
     - ADAS
     - ABS
     - Status
     - Chassis
     # ... etc
   ```

2. **Console warnings:** During export, warnings are logged for immediate visibility:
   ```
   WARNING: Type 'Lights' uses potential plural name 'Lights'.
            Suggested singular: 'Light' (VSS FQN: Vehicle.Cabin.Lights)
   ```

**Review Process:** These warnings help VSS maintainers identify:
- **True plurals** - VSS branches that should be renamed to singular form
- **False positives** - Words that end in 's' but aren't actually plural (add to whitelist)
- **Acceptable exceptions** - Cases where plural names are intentional

### VSS Instances Become GraphQL Structures
When your `vspec` has instances (like multiple seats), the exporter creates proper GraphQL types:

```graphql
# From vspec instances: ['Row[1,2]', ['DriverSide', 'PassengerSide']]
type Vehicle_Cabin_Seat_InstanceTag @instanceTag {
    dimension1: Vehicle_Cabin_Seat_InstanceTag_Dimension1  # Row1, Row2
    dimension2: Vehicle_Cabin_Seat_InstanceTag_Dimension2  # DriverSide, PassengerSide
}

enum Vehicle_Cabin_Seat_InstanceTag_Dimension1 {
  ROW1 @vspec(metadata: [{key: "originalName", value: "Row1"}])
  ROW2 @vspec(metadata: [{key: "originalName", value: "Row2"}])
}

enum Vehicle_Cabin_Seat_InstanceTag_Dimension2 {
  DRIVER_SIDE @vspec(metadata: [{key: "originalName", value: "DriverSide"}])
  PASSENGER_SIDE @vspec(metadata: [{key: "originalName", value: "PassengerSide"}])
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
    ├── vspec_quantities.yaml       # Quantities used (if provided via -q or implicit)
    ├── short_name_collisions.yaml  # Name collision resolutions (if any detected)
    ├── plural_type_warnings.yaml   # Plural type names detected (if any)
    └── pluralized_field_names.yaml # Fields changed to plural form (if any instances)
```

### VSS Reference Files

The `vspec_reference/` directory provides complete traceability:

- **README.md** - Documents the vss-tools version used, describes each file, and provides a command to regenerate the schema
- **vspec_lookup_spec.yaml** - Complete VSS specification tree (fully processed and expanded) in YAML format
- **vspec_units.yaml** - Unit definitions used during generation (included if units were provided via `-u` flag or implicitly loaded)
- **vspec_quantities.yaml** - Quantity definitions used during generation (included if quantities were provided via `-q` flag or implicitly loaded)
- **short_name_collisions.yaml** - Branch name collisions and progressive qualification resolutions (generated if collisions detected)
- **plural_type_warnings.yaml** - VSS branches with plural type names that may violate GraphQL naming conventions (generated if any detected)
- **pluralized_field_names.yaml** - Fields whose names were changed to plural form for list fields (generated if any instances exist)

These files allow you to:
1. Trace GraphQL elements back to their VSS source using the FQN in `@vspec` directives
2. Reproduce the exact GraphQL schema by re-running the exporter
3. Understand which input files were used for generation
4. Review naming convention warnings and pluralization changes





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

**Note:** Type names use short names by default (`Vehicle` instead of `Vehicle`). For types deeper in the tree like `Vehicle.Cabin.Door.Window`, the short name `Window` is used unless a collision is detected. Use `--fqn-type-names` to get fully-qualified names like `Vehicle_Cabin_Door_Window`.

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


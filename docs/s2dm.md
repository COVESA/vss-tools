# S2DM Exporter

The S2DM exporter generates GraphQL schemas in the Schema Definition Language (SDL) from Vspec specifications.
It is specifically designed for compatibility with the [Simplified Semantic Data Modeling (S2DM)](https://github.com/COVESA/s2dm) approach.
While it produces GraphQL SDL syntax output, its purpose differs from traditional GraphQL APIs: it focuses purely on the modeling language as a mechanism to formalize domain expertise, not on API implementation.
The S2DM exporter transforms VSS (Vehicle Signal Specification) into a GraphQL schema that maintains complete traceability back to the original VSS elements through specialized directives.

## What is S2DM?

S2DM is a pragmatic data modeling approach that balances semantic rigor and usability for non-modelers.
It aims to enhance the Vspec language to be more aligned with existing tools and communities outside COVESA.

## Key Features

### 1. VSS Traceability with `@vspec` Directives

The most distinctive feature of the S2DM exporter is its comprehensive use of `@vspec` directives, which provide complete traceability from every element in the generated GraphQL schema back to its origin in the VSS specification:

```graphql
"""All in-cabin components, including doors."""
type Vehicle_Cabin @vspec(source: {kind: FQN, value: "Vehicle.Cabin"}, vspecType: BRANCH) {
    """The position of the driver seat in row 1."""
    driverPosition: Vehicle_Cabin_DriverPosition_Enum @vspec(
        source: {kind: FQN, value: "Vehicle.Cabin.DriverPosition"},
        vspecType: ATTRIBUTE,
        comment: "Some signals use DriverSide and PassengerSide as instances..."
    )
    seats: [Vehicle_Cabin_Seat]
}
```

Each `@vspec` directive includes:
- **source**: Information about the VSS element origin
- **vspecType**: The VSS type (BRANCH, ATTRIBUTE, SENSOR, ACTUATOR)
- **comment**: Original VSS comments, when present
- **defaultValue**: Default values from VSS, when specified

### 2. Comprehensive Source Mapping

The `source` parameter in `@vspec` directives uses a structured approach to identify different types of VSS elements:

- **FQN** (Fully Qualified Name): Maps to the complete VSS path
- **UNIT**: References unit definitions from VSS `units.yaml`
- **QUANTITY_KIND**: References quantity kinds from VSS `quantities.yaml`
- **INSTANCE_LABEL**: Maps to instance labels from VSS instances
- **ALLOWED_VALUE**: Maps to individual allowed values in enums

Example of allowed value mapping:
```graphql
enum Vehicle_Cabin_DriverPosition_Enum {
    LEFT @vspec(source: {kind: ALLOWED_VALUE, value: "LEFT"})
    MIDDLE @vspec(source: {kind: ALLOWED_VALUE, value: "MIDDLE"})
    RIGHT @vspec(source: {kind: ALLOWED_VALUE, value: "RIGHT"})
}
```

### 3. VSS Data Type Support

The exporter provides comprehensive support for VSS data types through custom GraphQL scalars:

- **Standard Types**: String, Boolean, Float (for float and double)
- **Integer Types**: Int8, UInt8, Int16, UInt16, UInt32, Int64, UInt64
- **Special Types**: ID for unique identifiers

### 4. Instance Handling

VSS instances are modeled using specialized instance tag types that preserve the dimensional structure:

```graphql
"""Instance tag for Vehicle_Cabin_Seat with dimensional information."""
type Vehicle_Cabin_Seat_InstanceTag @instanceTag {
    dimension1: Vehicle_Cabin_Seat_InstanceTag_Dimension1
    dimension2: Vehicle_Cabin_Seat_InstanceTag_Dimension2
}

"""Dimensional enum for VSS instance dimension 1."""
enum Vehicle_Cabin_Seat_InstanceTag_Dimension1 {
    Row1
    Row2
}

"""Dimensional enum for VSS instance dimension 2."""
enum Vehicle_Cabin_Seat_InstanceTag_Dimension2 {
    DriverSide
    PassengerSide
}
```

### 5. Range Constraints

Numeric constraints from VSS are preserved using `@range` directives:

```graphql
"""Heating or cooling requested for the item."""
heatingCooling: Int8 @range(min: -100, max: 100) @vspec(
    source: {kind: FQN, value: "Vehicle.Cabin.Seat.HeatingCooling"},
    vspecType: ACTUATOR
)
```

## Usage

### Command-Line Interface

```bash
vss-tools export s2dm --vspec <input.vspec> --output <output.graphql> [options]
```

**Options:**
- `--vspec`: Path to the VSS specification file
- `--output`: Path for the generated GraphQL schema
- `--include-dirs`: Additional directories to search for included files
- `--strict`: Enable strict validation mode
- `--overlays`: Apply overlay files to modify the specification
- `--quantities`: Custom quantities definition file
- `--units`: Custom units definition file
- `--extended-attributes`: Include additional VSS attributes in processing

### Example

```bash
vss-tools export s2dm \
    --vspec vehicle.vspec \
    --output vehicle_s2dm.graphql \
    --quantities quantities.yaml \
    --units units.yaml
```

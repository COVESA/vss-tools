# S2DM Exporter

The S2DM exporter converts VSS (Vehicle Signal Specification) files into GraphQL schema format. This makes VSS data models more accessible to developers familiar with GraphQL while maintaining full traceability back to the original VSS specification.

## What is S2DM?

S2DM (Simplified Semantic Data Modeling) is a pragmatic approach to data modeling that uses GraphQL as a modeling language. It focuses on making domain expertise more accessible to developers and tools outside the automotive industry.

## What the Exporter Does

The S2DM exporter takes your VSS specification and generates a GraphQL schema that:

1. **Converts VSS structure to GraphQL types** - Each VSS branch becomes a GraphQL type
2. **Preserves all VSS information** - Every piece of data from your VSS file is kept using special `@vspec` directives
3. **Handles VSS data types** - Maps VSS data types to appropriate GraphQL types
4. **Supports VSS instances** - Creates proper GraphQL structures for multi-dimensional VSS instances
5. **Includes constraints** - Range limits and allowed values are preserved

## Key Features

### Complete VSS Traceability

Every element in the generated GraphQL schema includes an `@vspec` directive that tells you exactly where it came from in the original VSS file:

```graphql
"""All in-cabin components, including doors."""
type Vehicle_Cabin @vspec(source: {kind: FQN, value: "Vehicle.Cabin"}, vspecType: BRANCH) {
    """The position of the driver seat in row 1."""
    driverPosition: Vehicle_Cabin_DriverPosition_Enum @vspec(
        source: {kind: FQN, value: "Vehicle.Cabin.DriverPosition"},
        vspecType: ATTRIBUTE,
        comment: "Driver seat position configuration"
    )
}
```

### VSS Data Types Support

The exporter handles all VSS data types:
- **Strings** → GraphQL String
- **Numbers** → GraphQL Int, Float, or custom scalars (Int8, UInt16, etc.)
- **Booleans** → GraphQL Boolean
- **Arrays** → GraphQL Lists
- **Allowed values** → GraphQL Enums

### VSS Instances Become GraphQL Structures

When your VSS has instances (like multiple seats), the exporter creates proper GraphQL types:

```graphql
# From VSS instances: ['Row[1,2]', ['DriverSide', 'PassengerSide']]
type Vehicle_Cabin_Seat_InstanceTag {
    dimension1: Vehicle_Cabin_Seat_InstanceTag_Dimension1  # Row1, Row2
    dimension2: Vehicle_Cabin_Seat_InstanceTag_Dimension2  # DriverSide, PassengerSide
}
```

### Range Constraints Preserved

VSS min/max values become GraphQL `@range` directives:

```graphql
temperature: Float @range(min: -40, max: 85) @vspec(...)
```

### Unit Support

VSS units are converted to GraphQL enums with proper arguments:

```graphql
speed(unit: VelocityUnitEnum = "km/h"): Float
```

## Usage

### Basic Command

```bash
vss-tools export s2dm --vspec input.vspec --output output.graphql
```

### Common Options

```bash
vss-tools export s2dm \
    --vspec vehicle.vspec \
    --output vehicle_schema.graphql \
    --include-dirs ./includes \
    --units units.yaml \
    --quantities quantities.yaml
```

### Available Options

- `--vspec` - Your VSS specification file (required)
- `--output` - Where to save the GraphQL schema (required)
- `--include-dirs` - Folders with additional VSS files to include
- `--units` - Custom units definition file
- `--quantities` - Custom quantities definition file
- `--overlays` - VSS overlay files to apply modifications
- `--strict` - Enable strict validation mode
- `--extended-attributes` - Include additional VSS attributes

## Output Example

Given a simple VSS file:

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
  speed(unit: VelocityUnitEnum = "km/h"): Float @range(min: 0, max: 300) @vspec(
    source: {kind: FQN, value: "Vehicle.Speed"},
    vspecType: SENSOR
  )
}

enum VelocityUnitEnum {
  KM_H @vspec(source: {kind: UNIT, value: "km/h"})
  M_S @vspec(source: {kind: UNIT, value: "m/s"})
  MPH @vspec(source: {kind: UNIT, value: "mph"})
}
```

This makes your VSS data model accessible to GraphQL tools while keeping all the original VSS information intact.

# Go lang struct exporter

This exporter produces type struct definitions for the [go](https://go.dev/) programming language.

## Exporter specific arguments

### `--package`

The name of the package the generated sources (output and types output) will have.

# Example

Input model:
```yaml
# model.vspec
Vehicle:
  type: branch
  description: Vehicle
Vehicle.Speed:
  type: sensor
  description: Speed
  datatype: uint16
Vehicle.Location:
  type: sensor
  description: Location
  datatype: Types.GPSLocation
```

Input type definitions:
```yaml
# types.vspec
Types:
  type: branch
  description: Custom Types
Types.GPSLocation:
  type: struct
  description: GPS Location
Types.GPSLocation.Longitude:
  type: property
  description: Longitude
  datatype: float
Types.GPSLocation.Latitude:
  type: property
  description: Latitude
  datatype: float
```

Generator call:
```bash
vspec export go --vspec model.vspec --types types.vspec --package vss --output vss.go
```

Generated file:
```go
// vss.go
package vss

type Vehicle struct {
	Speed uint16
	Location GPSLocation
}
type GPSLocation struct {
	Longitude float32
	Latitude float32
}
```

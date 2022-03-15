## What does vspec2graphql do?

This allows to automatically generate a graphql schema that can represent VSS data.
The resulting schema does only allow querying information. Mutations are not supported.

The resulting schema will look something like this:
```
type Query {
  vehicle(
    """VIN of the vehicle that you want to request data for."""
    id: String!

    """
    Filter data to only provide information that was sent from the vehicle after that timestamp.
    """
    after: String
  ): Vehicle
}

"""Highlevel vehicle data."""
type Vehicle {
  """Attributes that identify a vehicle"""
  vehicleIdentification: Vehicle_VehicleIdentification
  ...
}

type Vehicle_VehicleIdentification {
  ...
}
...
```

Leaves look like this:
```
"""Vehicle brand or manufacturer"""
type Vehicle_VehicleIdentification_Brand {
  """Value: Vehicle brand or manufacturer"""
  value: String

  """Source system: Vehicle brand or manufacturer"""
  source: String

  """Collecting channel: Vehicle brand or manufacturer"""
  channel: String

  """Timestamp: Vehicle brand or manufacturer"""
  timestamp: String
}
```

Every leaf has a timestamp. This is supposed to contain the date of the last modification of the value. 
Queries can then filter data that has been recorded after a given timestamp.

After adjusting the vspec path in the makefile you should be able to execute 
`make graphql` in `vss-tools/vspec2graphql`.
The generated schema can then be found in: `vss-tools/vspec2graphql/generated/result.graphql`


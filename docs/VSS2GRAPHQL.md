## vspec2graphql

This exporter allows to automatically generate a graphql schema that can represent VSS data.
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

  """Timestamp: Vehicle brand or manufacturer"""
  timestamp: String
}
```

Every leaf has a timestamp. This is supposed to contain the date of the last modification of the value. 
Queries can then filter data that has been recorded after a given timestamp.

### Additional leaf parameters

As for `timestamp` in some scenarios it makes sense to add certain metadata like the `source` of a
served signal or additional privacy information. Therefore the tool has an additional calling parameter
`--gqlfield <name> <description>`, which takes the name and description of the additional field, like:

```
--gqlfield "source" "Source System"
```

Resulting in the following leaf in the schema:

```
"""Vehicle brand or manufacturer"""
type Vehicle_VehicleIdentification_Brand {
  """Value: Vehicle brand or manufacturer."""
  value: String

  """Timestamp: Vehicle brand or manufacturer."""
  timestamp: String

  """ Source System: Vehicle brand or manufacturer."""
  source: String
}
```

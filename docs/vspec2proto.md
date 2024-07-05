# vspec2proto - vspec Protocol Buffer generator

The vspec2proto.py script generates [Protocol Buffer message definitions](https://protobuf.dev) for all nodes in the tree. You can use these proto definitions to serialize the data of a VSS tree, e.g., as part of a gRPC API.

## Example

```bash
vspec2protobuf outputIds_v2.vspec indentity.proto -q spec/quantities.yaml -u spec/units.yaml -e staticUID --static-uid --add-optional
```

This example assumes that you checked out the COVESA VSS repository next to the vss-tools repository.

## Exporter specific arguments

In addition, to the general arguments of each exporter, the vspec2proto exporter supports the following arguments:

```bash
--static-uid          Expect staticUID attribute in the vspec input and use it as field number.
--add-optional        Set each field to optional
```

## Field Numbers and Backwards Compatibility

Part of the serialization with protocol buffers is the replacement of the field identifier with a field number. It is possible to set the used field number in the protobuf file. For instance, the field 'Speed' in the message 'Vehicle' could get the identifier 5:

```proto
message Vehicle {
  ...
  float Speed = 5
  ...
}
```

An encoded speed value of 20, would look something like this:

```bash
5: 20
```

Instead of sending the complete signal path like 'Vehicle.Speed', the serialization only contains the field number to reduce the amount of data to send. However, using field numbers as identifiers requires the same mapping between field numbers and fields on the encoding and decoding side.

The vspec2proto generator supports two approaches for setting the field numbers with different advantages and drawbacks.

### Incremental Field Numbers

By default, the generator numbers the fields from a single branch, which it represents as a message in protobuf, starting with 1. As an example, for the  `Vehicle` node we would get a message like this:

```proto
message Vehicle {
  VehicleVersionVSS VersionVSS = 1;
  VehicleVehicleIdentification VehicleIdentification = 2;
  string LowVoltageSystemState = 3;
  VehicleLowVoltageBattery LowVoltageBattery = 4;
  float Speed = 5;
  float TraveledDistance = 6;
  ...
}
```

We could create a newer version of the vspec-file with an additional signal like `MyNewSignal`. This addition may happen locally through a custom overlay or upstream in a new minor version of VSS. Either way, we would expect backward compatibility of the model with the same major version of the VSS model, even if the decoding side does not know about the updates. However, the resulting protobuf could be something like:

```proto
message Vehicle {
VehicleVersionVSS VersionVSS = 1;
  ...
  VehicleLowVoltageBattery LowVoltageBattery = 4;
  float Speed = 5;
  float MyNewSignal = 6;
  float TraveledDistance = 7;
  ...
}
```

Since the proto generator did not know the field numbers which it assigned to the fields in previous runs, it sorted `MyNewSignal` together with the old signals. As a result, the field numbers for the fields following the new signal have changed.

Thus, when using this protobuf file, the generator may introduce breaking changes even if the underlying vspec does not contain breaking changes. Hence, we recommend using the exact same proto file for en- and decoding, which leads to a stronger coupling between both sides.

### static-uid as Field Number

One solution to overcome breaking changes in the serialization caused by non-breaking changes in the VSS model is to define the numeric identifiers within the VSS model. This way, the proto generator is able to reuse these identifiers as field numbers and does not have to come up with its own numbers. However, such identifiers are not part of the upstream VSS model yet.

But there is the option to generate static uids with the [`vspec2id`](./vspec2id.md).
By adding the flag `--static-uid` you can instruct the proto generator to expect static uids in the input file and use them as field numbers.

This comes with the following drawbacks:

* **no bi-directional mapping between static-uid and protobuf field number**: The static uid is 32-bit long, and the length of a field number in proto files cannot exceed 29-bit.
Because of that, the generator cuts off the three least significant bits, which removes the option to map a field number back to the static-uid.
* **potential collisions**: The id generator uses a hashing algorithm to compute the 32-bit long id. This hashing may lead to id collisions. The proto generator increases the collision probability since it cuts the id to 29-bit to be compatible with the maximum size of a protobuf field number.
Because of that, the proto generator re-checks for collisions. In case of a detected collision, the id and the proto generator stop and request the user to change the input model until no collisions occur.
In addition, protobuf reserves the field numbers 19.000 to 20.000. The proto generator thus treats field numbers in this range like a collision.
* **overhead on the wire**: The [protobuf documentation](https://protobuf.dev/programming-guides/proto3/#assigning) recommends using field numbers that are as low as possible to reduce the number of required bytes for encoding the number.
For the incrementally assigned field numbers, we only need a few bits per number, while the id-based field number, in most cases, requires the full 4 bytes for 29 bits.

## Mark field as optional

In proto3, one can mark a field as `optional` to change the behavior of how to deal with values that are not present during the encoding. By default, the fields are not optional, and you can use the flag `--add-optional` to make all fields optional.

See the [Protocol Buffers Language Guide](https://protobuf.dev/programming-guides/proto3/#field-labels) for the implications of using `optional`.

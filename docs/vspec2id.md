# vspecID - vspec static UID generator and validator

The vspecID.py script is used to generate and validate static UIDs for all nodes in the tree.
They will be used as unique identifiers to transmit data between nodes. The static UIDs are
implemented to replace long strings like `Vehicle.Body.Lights.DirectionIndicator.Right.IsSignaling`
with a 4-byte identifier.

## General usage

```bash
usage: vspec2id.py [-h] [-I dir] [-e EXTENDED_ATTRIBUTES] [-s] [--abort-on-unknown-attribute] [--abort-on-name-style] [--format format] [--uuid] [--no-expand] [-o overlays] [-u unit_file]
                   [-vt vspec_types_file] [-ot <types_output_file>] [--json-all-extended-attributes] [--json-pretty] [--yaml-all-extended-attributes] [-v version] [--all-idl-features]
                   [--gqlfield GQLFIELD GQLFIELD] [--gen-layer-id-offset GEN_LAYER_ID_OFFSET] [--validate-static-uid VALIDATE_STATIC_UID] [--only-validate-no-export]
                   <vspec_file> <output_file>

Convert vspec to other formats.

positional arguments:
  <vspec_file>          The vehicle specification file to convert.
  <output_file>         The file to write output to.

...

IDGEN arguments:                                                             

  --gen-layer-id-offset GEN_LAYER_ID_OFFSET
                        Define layer ID in case you want to use 3 bytes for hashing and 1 byte for layer ID.If you don't
                        specify a layer ID it will default to zero which means that we will use4 bytes for the FNV-1 hash.
  --validate-static-uid VALIDATE_STATIC_UID
                        Path to validation file.
  --only-validate-no-export
                        For pytests and pipelines you can skip the export of the <output_file>
```

## Example

To initially run this you will need a vehicle signal specification, e.g.
[COVESA Vehicle Signal Specification](https://github.com/COVESA/vehicle_signal_specification). If you are just starting
to use static UIDs the first run is simple. You will only use the static UID generator by running the command below.
Please note that we are not using a layer identifier here, so `--gen-layer-id-offset` will default to 0.
However, you can set one by using the command line argument. Please note that in that case we will only use a
3-byte FNV-1 hash (instead 4-byte hash) because we will use 1-byte for the layer.

```bash
cd path/to/your/vss-tools
./vspecID.py ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec ../output_id_v1.vspec --gen-layer-ID-offset 99
```

Great, you generated your first overlay that will also be used as your validation file as soon as you update your
vehicle specification file.

### Option 1: Generate e.g. yaml file with static UIDs

Now if you just want to generate a new e.g. yaml file including your static UIDs, please use the overlay function of
vspec2x by running the following command:

```bash
./vspec2yaml.py ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec -o ../output_id_v1.vspec -e staticUID vehicle_specification_with_uids.yaml
```

### Option 2: Validate changes on your vehicle specification with validation file

In this case you want to validate changes of your vehicle specification. If you are doing a dry run try temporarily
renaming a node or changing the node's datatype, unit, description, or other. You will get warnings depending on your
changes in the vehicle signal specification.

The validation step compares your current changes of the vehicle signal specification to a previously generated file,
here we named it `../output_id_v1.vspec`. There are two types of changes `BREAKING CHANGES` and `NON-BREAKING CHANGES`.
A `BREAKING CHANGE` will generate a new hash for a node. A `NON-BREAKING CHANGE` will throw a warning, but the static
ID will remain the same. A `BREAKING CHANGE` is triggered when you change name/path, unit, datatype, enum values
(allowed), or minimum/maximum. These attributes are part of the hash so they a `BREAKING CHANGE` automatically
generates a new hash for a static UID.
In case you want to keep the same ID but rename a node, this we call a `SEMANTIC CHANGE`, you can add an attribute
called `fka` in the vspec (which is a list of strings) and add a list of names to it as shown below for `A.B.NewName`.
The same holds for path changes, if you move a node between layers you can add the `fka` attribute containing the
full path as shown below.

Before renaming `A.B.NewName` its name was `A.B.OldName`.

```
A.B.NewName:
  datatype: string
  type: actuator
  allowed: ["YES", "NO"]
  description: A.B.NewName's old name is 'OldName'. And its even older name is 'OlderName'.
  fka: ['A.B.OldName', 'A.B.OlderName']
```

As stated if you want to rename the node `A.B.NewName` to `A.NewName` you can also write the `fka` attribute
stating its legacy path.

Now you should know about all possible changes. To run the validation step, please do:

```bash
./vspecID.py ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec ../output_id_v2.vspec --validate-static-uid ../output_id_v1.vspec
```

Depending on what you changed in the vehicle signal specification the corresponding errors will be triggered.

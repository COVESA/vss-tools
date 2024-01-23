# vspec2id - vspec static UID generator and validator

The vspec2id.py script is used to generate and validate static UIDs for all nodes in the tree.
They will be used as unique identifiers to transmit data between nodes. The static UIDs are
implemented to replace long strings like `Vehicle.Body.Lights.DirectionIndicator.Right.IsSignaling`
with a 4-byte identifier.

## General usage

```bash
usage: vspec2id.py [-h] [-I dir] [-e EXTENDED_ATTRIBUTES] [-s] [--abort-on-unknown-attribute] [--abort-on-name-style] [--format format] [--uuid] [--no-expand] [-o overlays] [-u unit_file]
                   [-q quantity_file] [-vt vspec_types_file] [-ot <types_output_file>] [--json-all-extended-attributes] [--json-pretty] [--yaml-all-extended-attributes] [-v version] [--all-idl-features]
                   [--gqlfield GQLFIELD GQLFIELD] [--jsonschema-all-extended-attributes] [--jsonschema-disallow-additional-properties] [--jsonschema-require-all-properties] [--jsonschema-pretty]
                   [--validate-static-uid VALIDATE_STATIC_UID] [--only-validate-no-export] [--strict-mode]
                   <vspec_file> <output_file>

Convert vspec to other formats.

positional arguments:
  <vspec_file>          The vehicle specification file to convert.
  <output_file>         The file to write output to.

...

IDGEN arguments:

  --validate-static-uid VALIDATE_STATIC_UID
                        Path to validation file.
  --only-validate-no-export
                        For pytests and pipelines you can skip the export of the <output_file>
  --strict-mode         Strict mode means that the generation of static UIDs is case-sensitive.
```

## Example

To initially run this you will need a vehicle signal specification, e.g.
[COVESA Vehicle Signal Specification](https://github.com/COVESA/vehicle_signal_specification). If you are just starting
to use static UIDs the first run is simple. You will only use the static UID generator by running the command below.

```bash
cd path/to/your/vss-tools
./vspec2id.py ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec ../output_id_v1.vspec
```

Great, you generated your first overlay that will also be used as your validation file as soon as you update your
vehicle signal specification file.

If needed you can make the static UID generation case-sensitive using the command line argument `--strict-mode`. It
will default to false.

### Generate e.g. yaml file with static UIDs

Now if you just want to generate a new e.g. yaml file including your static UIDs, please use the overlay function of
vspec2x by running the following command:

```bash
cd path/to/your/vss-tools
./vspec2yaml.py ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec -o ../output_id_v1.vspec -e staticUID vehicle_specification_with_uids.yaml
```

### Validation

In this case you want to validate changes of your vehicle specification. If you are doing a dry run try temporarily
renaming a node or changing the node's datatype, unit, description, or other. You will get warnings depending on your
changes in the vehicle signal specification.

The validation step compares your current changes of the vehicle signal specification to a previously generated file,
here we named it `../output_id_v1.vspec`. There are two types of changes `BREAKING CHANGES` and `NON-BREAKING CHANGES`.
A `BREAKING CHANGE` will generate a new hash for a node. A `NON-BREAKING CHANGE` will throw a warning, but the static
ID will remain the same. A `BREAKING CHANGE` is triggered when you change name/path, unit, type, datatype, enum values
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

To summarize these are the `BREAKING CHANGES` that affect the hash and `NON-BREAKING CHANGES` that throw
warnings only:

| BREAKING CHANGES      |     | NON-BREAKING CHANGES |
|-----------------------|-----|----------------------|
| Qualified name        |     | Added attribute      |
| Data type             |     | Deprecation          |
| Type (i.e. node type) |     | Deleted Attribute    |
| Unit                  |     | Change description   |
| Enum values (allowed) |     |                      |
| Minimum               |     |                      |
| Maximum               |     |                      |

Now you should know about all possible changes. To run the validation step, please do:

```bash
./vspecID.py ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec ../output_id_v2.vspec --validate-static-uid ../output_id_v1.vspec
```

Depending on what you changed in the vehicle signal specification the corresponding errors will be triggered.

Now, if the warning logs correspond to what you have changed since the last validation, you can continue to generate
e.g. a yaml file with your validated changes as described in the `Generate e.g. yaml file with static UIDs` step above.

### Tests

If you want to run the tests for the vspec2id implementation, please do

```bash
cd path/to/vss-tools
export PYTHONPATH=${PWD}
pytest tests/vspec/test_static_uids
```

Depending on how you are using the implementation you might have to activate your virtual environment as described on
the top README.

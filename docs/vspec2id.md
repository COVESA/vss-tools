# vspecID - vspec static UID generator and validator

The vspecID.py script is used to generate and validate static UIDs for all nodes in the tree.
They will be used as unique identifiers to transmit data between nodes. The static UIDs are
implemented to replace long strings like `Vehicle.Body.Lights.DirectionIndicator.Right.IsSignaling`
with a 4-byte identifier.

ToDo what kind of data does each byte represent using latex

## General usage

```bash
usage: vspecID.py [-h] [-I dir] [-e EXTENDED_ATTRIBUTES] [-s] [--abort-on-unknown-attribute] [--abort-on-name-style] [--format format] [--uuid] [--no-expand] [-o overlays]
                  [-u unit_file] [-vt vspec_types_file] [-ot <types_output_file>] [--json-all-extended-attributes] [--json-pretty] [--yaml-all-extended-attributes] [-v version]
                  [--all-idl-features] [--gqlfield GQLFIELD GQLFIELD] [--gen-ID-offset GEN_ID_OFFSET] [--gen-layer-ID-offset GEN_LAYER_ID_OFFSET] [--gen-no-layer] [--gen-decimal-ID]
                  [--validate-static-uid VALIDATE_STATIC_UID] [--validate-automatic-mode] [--only-validate-no-export]
                  <vspec_file> <output_file>
```

## Example

To initially run this you will need a vehicle signal specification, e.g.
[COVESA Vehicle Signal Specification](https://github.com/COVESA/vehicle_signal_specification). If you are just starting
to use static UIDs the first run is simple. You will only use the static UID generator by running the command below.
Please note that we are using an arbitrary layer ID offset of `99` here.

```bash
cd path/to/your/vss-tools
./vspecID.py ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec ../output_id_v1.vspec --gen-layer-ID-offset 99
```

Great, you generated your first overlay that will also be used as your validation file as soon as you update your
vehicle
specification file.

### Option 1: Generate e.g. yaml file with static UIDs

Now if you just want to generate a new e.g. yaml file including your static UIDs, please use the overlay function of
vspec2x by running the following command:

```bash
./vspec2yaml.py ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec -o ../output_id_v1.vspec -e staticUID vehicle_specification_with_uids.yaml
```

### Option 2: Validate changes on your vehicle specification with validation file

In this case you want to validate changes of your vehicle specification, if you are doing a dry run try temporarily
renaming a node or changing the node's datatype, unit, description, or other. You will get warnings depending on what
you changed in your vehicle specification.

The validation step has two separate modes, you can either run it in *automatic mode* using `--validate-automatic-mode`
or in manual mode. *Automatic mode* will automatically assign new IDs for breaking changes in your vehicle signal
specification. *Manual mode* will ask you what you want to do in most cases you will be able to decide between 1), 2)
and 3) which looks like this

```
WARNING  What would you like to do?
1) Assign new ID
2) Overwrite ID with validation ID
3) Skip
```

In most cases you want to assign a new ID! But the more you use this there can be cases in which you want to keep using
the validation ID or Skip this node e.g. for deprecated nodes. Maybe we will even need more cases here in the future,
let's see.

There are different cases of changes:

* `ADD NEW ATTRIBUTE`: non-breaking change-> ToDo
* `DEPRECATED ATTRIBUTE`: non-breaking change -> ToDo
* `DELETED ATTRIBUTE`: **breaking change** -> ToDo
* `VSS PATH MISMATCH`: non-breaking change -> a node was moved in the tree
* `SEMANTIC CHANGES` -> see more detailed explanation below
* `DESCRIPTION MISMATCH`: non-breaking change -> description of a node was updated
* `UNIT MISMATCH`: **breaking change** -> the unit of a node was updated
* `ADDED UNIT TO ATTRIBUTE`: potentially breaking change -> ToDo
* `DATATYPE MISMATCH`: **breaking change** -> the datatype of a node was updated
* `ADDED ENUM` or `RENAME ENUM`: **breaking change** -> ToDo
* `DELETED ENUM`: **breaking change** -> ToDo
* `UPDATED MIN/MAX`: **breaking change** -> ToDo

Also, we try to detect **semantic** changes of a node, to do that we try to match the **full path and static UID** of a
node with another. The following "truth table" shows how we detect semantic changes.

| CASE | matched names | matched uids | result                                                         | name           |
|:----:|:-------------:|:------------:|----------------------------------------------------------------|----------------|
|  1   |       0       |      0       | node was added after last validation                           | NODE ADDED     |
|  2   |       1       |      0       | uid has changed in vspec                                       | UID CHANGE     |
|  3   |       0       |      1       | name has changed in vspec                                      | NAME CHANGE    |
|  4   |       1       |      1       | no change -> continue with other checks                        | NO CHANGE      |
|  5   |      >1       |      1       | duplicated node with same names                                | NAME DUPLICATE |
|  6   |       1       |      >1      | multiple UIDs but same name -> consequence of breaking change? | UID DUPLICATE  |
|  7   |      >1       |      >1      | duplicates if cross matched names and uids                     | NODE DUPLICATE |

Now you should know about all possible changes. To run the validation step, please do:

```bash
./vspecID.py ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec ../output_id_v2.vspec --gen-layer-ID-offset 99 --validate-static-uid ../output_id_v1.vspec
```

As mentioned earlier you can use `--validate-automatic-mode` to skip the user interaction and use the best possible
answer, but please keep in mind that this could potentially overwrite a static UID that you want to keep for this
iteration of the vehicle signal specification.

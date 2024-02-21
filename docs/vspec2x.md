# Vspec2x-based generators

[vspec2x](../vspec/vspec2x.py) is a generator framework that offers functionality to parse one or more vspec files and
transform that to an internal VSS model, which can be used as input for generators.

Vspec2x-based generators have a number of common arguments.
It is partially configurable which arguments that shall be available for each generator,
so all arguments described in this documents are not available for all generators.
In addition to this generator-specific arguments may be supported

You can get a description of supported commandline arguments by running `<toolname> --help`, e.g. `vss2json.py --help`.
In this document `vspec2json.py` is generally used as example, but the same syntax is typically available also for other tools.

The supported arguments might look like this

```
$ vspec2json.py --help
usage: vspec2json.py [-h] [-I dir] [-e EXTENDED_ATTRIBUTES] [-s] [--abort-on-unknown-attribute] [--abort-on-name-style] [--uuid] [--no-expand]
                     [-o overlays] [-q quantity_file] [-u unit_file] [-vt vspec_types_file]
                     [-ot <types_output_file>] [--json-all-extended-attributes] [--json-pretty]
                     <vspec_file> <output_file>
```

An example command line to convert the VSS standard catalog into a JSON file is

```
$ vspec2json.py -I ../spec -u ../vehicle_signal_specification/spec/units.yaml ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec vss.json
INFO     Known extended attributes:
INFO     Added 29 quantities from /home/erik/vehicle_signal_specification/spec/quantities.yaml
INFO     Added 61 units from ../vehicle_signal_specification/spec/units.yaml
INFO     Loading vspec from ../vehicle_signal_specification/spec/VehicleSignalSpecification.vspec...
INFO     Calling exporter...
INFO     Generating JSON output...
INFO     Serializing compact JSON...
INFO     All done.

```

This assumes you checked out the [COVESA Vehicle Signal Specification](https://github.com/covesa/vehicle_signal_specification) which contains vss-tools as a submodule.

The `-I` parameter adds a directory to search for includes referenced in you `.vspec` files. `-I` can be used multiple times to specify more include directories. The `-u` parameter specifies the unit file(s) to use. The `-q` parameter specifies quantity file(s) to use.

The first positional argument - `../spec/VehicleSignalSpecification.vspec` in the example  - gives the (root) `.vspec` file to be converted. The second positional argument  - `vss.json` in the example - is the output file.

It is the file `vspec2json.py` that specified which generator to use, i.e. which output to generate.

## General parameters

### --abort-on-unknown-attribute
Terminates parsing when an unknown attribute is encountered, that is an attribute that is not defined in the [VSS standard catalogue](https://covesa.github.io/vehicle_signal_specification/rule_set/), and not whitelisted using the extended attribute parameter `-e` (see below).

*Note*: Here an *attribute* refers to VSS signal metadata such as "datatype", "min", "max", ... and not to the VSS signal type attribute

###  --abort-on-name-style
Terminates parsing, when the name of a signal does not follow [VSS Naming Conventions](https://covesa.github.io/vehicle_signal_specification/rule_set/basics/#naming-conventions) for the VSS standard catalog.

### --strict
Equivalent to setting `--abort-on-unknown-attribute` and `--abort-on-name-style`

### --uuid
Request the exporter to output UUIDs. The UUID generated is an RFC 4122 Version 5 UUID created from the qualified name
of the node and the UUID of the namespace `vehicle_signal_specification`.

This setting may not apply to all exporters, some exporters will never output uuids.

### --no-expand

By default all tools expand instance information so that instance information like "Row1" become a branch just like
any other branch. If this argument is used and the exporter supports it no expansion will take place.
Instead instance information will be kept as additional information for the branch.

## Handling of Data Types

COVESA supports a number of pre-defined types, see [VSS documentation](https://covesa.github.io/vehicle_signal_specification/rule_set/data_entry/data_types/).
In addition to this COVESA is introducing a concept to support user-defined types.
This is currently limited to specifying struct-types. For more information on syntax see VSS documentation.

*Note: Struct support is not yet supported by all exporters, currently supported by JSON; CSV, Yaml and Protobuf exporters!*

To use user-defined types the types must be put in a separate file and given to the tool with the `-vt` argument.
When a signal is defined the tooling will check if the `datatype` specified is either a predefined type or
a user-defined type. If no matching type is found an error will be given.
It is possible to use `-vt <file>` multiple times. Any additional files after the first one is then treated similar
to overlay files, i.e. they are merged into previous file and it is if needed possible to redefine already defined types.

Depending on exporter, type definitions may either be transformed to a separate file with structure similar to the
"normal" output file, or integrated into the "normal" output file. If type output is given to a separate file then
the name of that file can be specified by the `-ot`argument.

Below is an example using user-defined types for JSON generation.
Please see [test cases](https://github.com/COVESA/vss-tools/tree/master/tests/vspec/test_structs) for more details.

```bash
python vspec2json.py --json-pretty -vt VehicleDataTypes.vspec -ot VehicleDataTypes.json test.vspec out.json
```

Current status for exportes:

* CSV, JSON, YAML, Protobuf: Supported!
* All other exporters: Not supported!

The export format is similar to the export format of VSS signals. The below table illustrates the exporting of the new nodes introduced in the data type tree:

| Data                     | CSV    | JSON | YAML |
| ------------------------ | ------ | ---- | ---- |
| Struct Node Attribute    | Column | Key  | Key  |
| Property Node Attribute  | Column | Key  | Key  |

The YAML exporter maintains the file structure of the vspec file being exported.

**NOTE:** For YAML and JSON, if a separate output file is not provided, the complex data types are exported under the key - `ComplexDataTypes`. See the snippets below for illustration.

**CSV snippet**
```csv
"Node","Type","DataType","Deprecated","Unit","Min","Max","Desc","Comment","Allowed","Default"
"<BranchName>","branch","","<Deprecation>","","","","<Description>","<Comment>","",""
"<StructName>","struct","","<Deprecation>","","","","<Description>","<Comment>","",""
"<PropertyName>","property","<DataType>","<Deprecation>","<Unit>","<Min>","<Max>","<Description>","<Comment>","<Allowed values>","<Default Value>"
```

**JSON snippet (data types are exported to a separate file)**
```json
{
  "VehicleDataTypes": {
    "children": {
      "<Branch>": {
        "children": {
          "<Struct>": {
            "children": {
              "<Property>": {
                "type": "property",
                "datatype": "<Data Type>",
                "description": "<Description",
                ...
              }
            },
            "description": "<Description>",
            "type": "struct"
          }
        }
        "description": "<Description>",
        "type": "branch"
      }
    }
  }
}
```

**JSON snippet (signals and data types are exported to a single file)**
```json
{
  "Vehicle": {
    "type": "branch"
    // Signal tree
  },
  "ComplexDataTypes": {
    "VehicleDataTypes": {
      // complex data type tree
      "children": {
        "<Branch>": {
          "children": {
            "<Struct>": {
              "children": {
                "<Property>": {
                  "type": "property",
                  "datatype": "<Data Type>",
                  "description": "<Description",
                  //                  ...
                }
              },
              "description": "<Description>",
              "type": "struct"
            }
          }
          "description": "<Description>",
          "type": "branch"
        }
      }
    }
  }
}
```

## Handling of units

The tooling verifies that only pre-defined units are used, like `kPa`and `percent`.

COVESA maintains a [unit file](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/units.yaml) for the standard VSS catalog.

It is possible to specify your own unit file(s) by the `-u <file>` parameter.
`-u` can be used multiple times to specify additional files like in the example below:

```bash
python ./vss-tools/vspec2csv.py -I ./spec -u vss-tools/vspec/config.yaml -u vss-tools/vspec/extra.yaml ./spec/VehicleSignalSpecification.vspec output.csv
```

When deciding which units to use the tooling use the following logic:

* If `-u <file>` is used then the specified unit files will be used. Default units will not be considered.
* If `-u` is not used the tool will check for a unit file in the same directory as the root `*.vspec` file.

See the [FAQ](../FAQ.md) for more information on how to define own units.

### Handling of quantities

For units it is required to define `quantity`, previously called `domain`.
COVESA maintains a [quantity file](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/quantities.yaml) for the standard VSS catalog.

When deciding which quantities to use the tooling use the following logic:

* If `-q <file>` is used then the specified quantity files will be used. Default quantities will not be considered.
* If `-q` is not used the tool will check for a file called `quantities.yaml` in the same directory as the root `*.vspec` file.

As of today use of quantity files is optional, and tooling will only give a warning if a unit use a quantity not specified in a quantity file.

## Handling of overlays and extensions
The generator framework allows composition of several overlays on top of a base vspec, to extend the model or overwrite certain metadata. Check [VSS documentation](https://covesa.github.io/vehicle_signal_specification/introduction/) on the concept of overlays.

Overlays are in general injected before the VSS tree is expanded. Expansion is the process where branches with instances are transformed into multiple branches.
An example is the `Vehicle.Cabin.Door` branch which during expansion get transformed into `Vehicle.Cabin.Door.Row1.Left`, `Vehicle.Cabin.Door.Row1.Right`, `Vehicle.Cabin.Door.Row2.Left`and `Vehicle.Cabin.Door.Row2.Right`.

If you in an overlay for example wants to add a new signal to all door instances but only wants to specify the new signal once, then you could create an overlay like below and inject it using the `-o` or `--overlay` parameter.

```
Vehicle.Cabin.Door.NewSignal:
  datatype: int8
  type: sensor
  unit: km
  description: A new signal for all doors.
```

This will result in that the following new signals are created

* `Vehicle.Cabin.Door.Row1.Left.NewSignal`
* `Vehicle.Cabin.Door.Row1.Right.NewSignal`
* `Vehicle.Cabin.Door.Row2.Left.NewSignal`
* `Vehicle.Cabin.Door.Row2.Right.NewSignal`

If you only want to add the new signal to one of the doors, then you can create an overlay like below.

```
Vehicle.Cabin.Door.Row1.Left.NewSignal:
  datatype: int8
  type: sensor
  unit: km
  description: A new signal for the left door on first row.
```

The tooling will recognize that `Row1.Left` refers to an instance of `Door` and will not expand the signal.
Even if a row not existing in standard instantiation is used (like `Row5`) the tool will recognize it as an "already expanded"
signal and not expand it further. If using an overlay to redefine a specific signal then data specified in overlays for extended signals
(like `Vehicle.Cabin.Door.Row1.Left.IsChildLockActive`) has precedence over data specified for not yet extended signals
(like `Vehicle.Cabin.Door.IsChildLockActive`).

*Note: If using `--no-expand` together with overlays for specific instances then the result will be a combination*
*of expanded and unexpanded paths. For the example above `Vehicle.Cabin.Door.Row1.Left.NewSignal` will be expanded*
*but all other signals in `Vehicle.Cabin.Door` will remain unexpanded!*

It is possible to use `-o` multiple times, e.g.

```
python vspec2yaml.py ../spec/VehicleSignalSpecification.vspec -o o1.vspec -o o2.vspec -oae o3.vspec -oae o4.vspec result.yml
```

You can also use overlays to inject custom metadata not used in the standard VSS catalog, for example if your custom VSS model includes `source` and `quality` metadata for sensors.
As an example consider the following `overlay.vspec`:

```yaml
#
# Example overlay
#
Vehicle:
  type: branch

Vehicle.Speed:
    quality: 100
    source: "ecu0xAA"
```

This will give a warning about unknown attributes, or even terminate the parsing when `-s`, `--strict`  or `--abort-on-unknown-attribute` is used.

```
% python vspec2json.py -I ../spec ../spec/VehicleSignalSpecification.vspec --strict -o overlay.vspec test.json
Output to json format
Known extended attributes:
Loading vspec from ../spec/VehicleSignalSpecification.vspec...
Applying VSS overlay from overlay.vspec...
Warning: Attribute(s) quality, source in element Speed not a core or known extended attribute.
You asked for strict checking. Terminating.
```

You can whitelist extended metadata attributes using the `-e` parameter with a comma separated list of attributes:

```
python vspec2json.py -I ../spec ../spec/VehicleSignalSpecification.vspec -e quality,source -o overlay.vspec test.json
```

In this case the expectation is, that the generated output will contain the whitelisted extended metadata attributes, if the exporter supports them.

__Note: Not all exporters (need to) support (all) extended metadata attributes!__ Currently, the `yaml` and `json` exporters support arbitrary metadata.

## JSON exporter notes

### --json-all-extended-attributes
Lets the exporter generate _all_ extended metadata attributes found in the model. By default the exporter is generating only those given by the `-e`/`--extended-attributes` parameter.

### --json-pretty
If the paramter is set it will pretty-print the JSON output, otherwise you will get a minimized version

## JSONSCHEMA exporter notes

### --jsonschema-all-extended-attributes
Lets the exporter generate _all_ extended metadata attributes found in the model. By default the exporter is generating only those given by the `-e`/`--extended-attributes` parameter. This will also add unconverted VSS standard attribtues into the schema using the following attributes

| VSS attribute | in schema     |
|---------------|---------------|
| type          | x-VSStype     |
| datatype      | x-datatype    |
| deprecation   | x-deprecation |
| aggregate     | x-aggregate   |
| comment       | x-comment     |
| uuid          | x-uuid        |

Not that strict JSON schema validators might not accept jsonschemas whoch such extra, non-standard entries.

### --jsonschema-disallow-additional-properties
Do not allow properties not defined in VSS tree, when elements are validated agains the schema, what this basically does is setting

```json
"additionalProperties": false
```
for all defined objects. See: https://json-schema.org/draft/2020-12/json-schema-core#additionalProperties

###  --jsonschema-require-all-properties
Require all elements defined in VSS tree for a valid object, i.e. this populates the `required` list with all childs. See: https://json-schema.org/draft/2020-12/json-schema-validation#name-required

### --jsonschema-pretty
If the paramter is set it will pretty-print the JSON output, otherwise you will get a minimized version

## YAML exporter notes

### --yaml-all-extended-attributes
Lets the exporter generate _all_ extended metadata attributes found in the model. By default the exporter is generating only those given by the `-e`/`--extended-attributes` parameter.

## DDS-IDL exporter notes
The DDS-IDL exporter never generates uuid, i.e. the `--uuid` option has no effect.

## Graphql exporter notes
The Graphql exporter never generates uuid, i.e. the `--uuid` option has no effect.

### --all-idl-features
Will also generate non-payload const attributes such as unit/datatype. Default is not to generate them/comment them out because at least Cyclone DDS and FastDDS do not support const. For more information check the [DDS-IDL exporter docs](VSS2DDSIDL.md).

## GRAPHQL exporter notes

### --gqlfield GQLFIELD GQLFIELD
Add additional fields to the nodes in the graphql schema. use: <field_name> <description>


## Writing your own generator

This is done by creating a subclass of `class Vss2X`, see [vss2x.py](../vspec/vss2x.py).
You need at least to implement the abstract method `generate`.
In addition you may want to customize which generic arguments that shall be used and add
generator specific arguments, if needed.


A generic implementation example is available as a [test case](../tests/generators).


Please see [vspec2x architecture document](vspec2x_arch.md).

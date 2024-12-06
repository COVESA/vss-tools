# Vspec Exporters

`vspec export` is a tool to export a given vss model into another format.

For the most up do date usage information, please call the tool help via:

```bash
vspec export --help

 Usage: vspec export [OPTIONS] COMMAND [ARGS]...
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help                                              Show this message and exit.                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ apigear       Export to ApiGear.                                                                                     │
│ binary        Export to Binary.                                                                                      │
│ csv           Export as CSV.                                                                                         │
│ ddsidl        Export as DDSIDL.                                                                                      │
│ franca        Export as Franca.                                                                                      │
│ graphql       Export as GraphQL.                                                                                     │
│ id            Export as IDs.                                                                                         │
│ json          Export as JSON.                                                                                        │
│ jsonschema    Export as a jsonschema.                                                                                │
│ protobuf      Export as protobuf.                                                                                    │
| samm          Export as Eclipse Semantic Modeling Framework (ESMF) - Semantic Aspect Meta Model (SAMM) - .ttl files. |
│ yaml          Export as YAML.                                                                                        │
│ tree          Export as Tree.                                                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```


A complete example call with the `json` exporter and its output could look like this:

```bash
vspec export json --vspec spec/VehicleSignalSpecification.vspec --output vss.json
[16:40:03] INFO     Added 29 quantities from                                               __init__.py:895
                    /Users/Foo/workspace/vehicle_signal_specification/spec/quantities.
                    yaml
           INFO     Added 62 units from                                                    __init__.py:923
                    /Users/Bar/workspace/vehicle_signal_specification/spec/units.yaml
           INFO     Loading vspec from spec/VehicleSignalSpecification.vspec...                utils.py:81
[16:40:04] INFO     Check type usage                                                       __init__.py:117
           INFO     Generating JSON output...                                                  json.py:142
           INFO     Serializing compact JSON...                                                json.py:148

```
## Exporter Specific Documentation

- [apigear](./apigear.md)
- [binary](../binary/README.md)
- [ddsidl](./ddsidl.md)
- [go](./go.md)
- [graphql](./graphql.md)
- [id](./id.md)
- [protobuf](./protobuf.md)
- [samm](./samm.md)
- [tree](./tree.md)

## Argument Explanations

Here is a list of more in depth Explanations of the arguments.
Please note that not all arguments are available for all exporters.
That is either a technical limitation of the exported format or has just not implemented yet.

### --log-level
Controls the verbosity of the output the tool generates. The default is "INFO" which
will print things interesting for most users. If you want to hide those you can pass
`--log-level WARNING` which will hide debug and info prints and will print warnings and errors.

### --log-file
Also writes log messages into the given file. Note that the format used for writing into a file is slightly different.

### --aborts unknown-attribute
Terminates parsing when an unknown attribute is encountered, that is an attribute that is not defined in the [VSS standard catalogue](https://covesa.github.io/vehicle_signal_specification/rule_set/), and not whitelisted using the extended attribute parameter `-e` (see below).

> [!NOTE]
> Here an *attribute* refers to VSS signal metadata such as "datatype", "min", "max",
> ... and not to the VSS signal type attribute

### --aborts name-style
Terminates parsing, when the name of a signal does not follow [VSS Naming Conventions](https://covesa.github.io/vehicle_signal_specification/rule_set/basics/#naming-conventions) for the VSS standard catalog.

### --strict/--no-strict
Enables `--aborts unknown-attribute` and `--aborts name-style`

### --expand/--no-expand

By default all tools expand instance information so that instance information like "Row1" become a branch just like
any other branch. If this argument is used and the exporter supports it no expansion will take place.
Instead instance information will be kept as additional information for the branch.

### -e, --extended-attributes

See section on [overlays](vspec.md#handling-of-overlays-and-extensions) below

## Handling of Data Types

COVESA supports a number of pre-defined types, see [VSS documentation](https://covesa.github.io/vehicle_signal_specification/rule_set/data_entry/data_types/).
In addition to this COVESA is introducing a concept to support user-defined types.
This is currently limited to specifying struct-types. For more information on syntax see VSS documentation.

> [!WARNING]
> Struct support is not yet supported by all exporters, currently supported by JSON; CSV, Yaml and Protobuf exporters!

To use user-defined types the types must be put in a separate file and given to the tool with the `--types/-t` argument.
When a signal is defined the tooling will check if the `datatype` specified is either a predefined type or
a user-defined type. If no matching type is found an error will be given.
It is possible to use `--types/-t <file>` multiple times. Any additional files after the first one is then treated similar
to overlay files, i.e. they are merged into previous file and it is if needed possible to redefine already defined types.

Depending on exporter, type definitions may either be transformed to a separate file with structure similar to the
"normal" output file, or integrated into the "normal" output file. If type output is given to a separate file then
the name of that file can be specified by the `--types-output` argument.

Below is an example using user-defined types for JSON generation.
Please see [test cases](https://github.com/COVESA/vss-tools/tree/master/tests/vspec/test_structs) for more details.

```bash
vspec export json --pretty --types VehicleDataTypes.vspec --types-output VehicleDataTypes.json --vspec test.vspec --output out.json
```

Current status for exporters:

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

It is possible to specify your own unit file(s) by the `--units/-u <file>` parameter.
`--units/-u` can be used multiple times to specify additional files like in the example below:

```bash
vspec export csv -I ./spec -u vss-tools/vspec/config.yaml -u vss-tools/vspec/extra.yaml --vspec ./spec/VehicleSignalSpecification.vspec --output output.csv
```

When deciding which units to use the tooling use the following logic:

* If `--units/-u <file>` is used then the specified unit files will be used. Default units will not be considered.
* If `--units/-u` is not used the tool will check for a unit file in the same directory as the root `*.vspec` file.

See the [FAQ](../FAQ.md) for more information on how to define own units.

### Handling of quantities

For units it is required to define `quantity`, previously called `domain`.
COVESA maintains a [quantity file](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/quantities.yaml) for the standard VSS catalog.

When deciding which quantities to use the tooling use the following logic:

* If `--quantities/-q <file>` is used then the specified quantity files will be used. Default quantities will not be considered.
* If `--quantities/-q <file>` is not used the tool will check for a file called `quantities.yaml` in the same directory as the root `*.vspec` file.

As of today use of quantity files is optional, and tooling will only give a warning if a unit use a quantity not specified in a quantity file.

## Handling of overlays and extensions
The generator framework allows composition of several overlays on top of a base vspec, to extend the model or overwrite certain metadata. Check [VSS documentation](https://covesa.github.io/vehicle_signal_specification/introduction/) on the concept of overlays.

Overlays are in general injected before the VSS tree is expanded. Expansion is the process where branches with instances are transformed into multiple branches.
An example is the `Vehicle.Cabin.Door` branch which during expansion get transformed into `Vehicle.Cabin.Door.Row1.Left`, `Vehicle.Cabin.Door.Row1.Right`, `Vehicle.Cabin.Door.Row2.Left`and `Vehicle.Cabin.Door.Row2.Right`.

If you in an overlay for example wants to add a new signal to all door instances but only wants to specify the new signal once, then you could create an overlay like below and inject it using the `-l` or `--overlay` parameter.

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

It is possible to use `-l` multiple times, e.g.

```bash
vspec export yaml --vspec ../spec/VehicleSignalSpecification.vspec -l o1.vspec -l o2.vspec -l o3.vspec -l o4.vspec --output result.yml
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

This will give a warning about unknown attributes, or even terminate the parsing when `--strict`  or `--aborts unknown-attribute` is used.

```bash
vspec export json -I spec --vspec spec/VehicleSignalSpecification.vspec --strict -l overlay.vspec --output test.json
Output to json format
Known extended attributes:
Loading vspec from spec/VehicleSignalSpecification.vspec...
Applying VSS overlay from overlay.vspec...
Warning: Attribute(s) quality, source in element Speed not a core or known extended attribute.
You asked for strict checking. Terminating.
```

You can whitelist extended metadata attributes using the `-e` / `--extended-attributes` argument.

```bash
vspec export json -I spec -s spec/VehicleSignalSpecification.vspec -e quality -e source -l overlay.vspec -o test.json
vspec export json -I spec --vspec spec/VehicleSignalSpecification.vspec --extended-attributes quality --extended-attributes source --overlays overlay.vspec --output test.json
```

> [!NOTE]
> A comma separated list of attributes can no longer be used to specify extended attributes!
> Instead of using for example `-e a1,a2` you must use `-e a1 -e a2`!

In this case the expectation is, that the generated output will contain the whitelisted extended metadata attributes, if the exporter supports them.

> [!WARNING]
> Not all exporters (need to) support (all) extended metadata attributes!
> Currently, the `yaml` and `json` exporters support arbitrary metadata.

## JSON exporter notes

### --extended-all-attributes
Lets the exporter generate _all_ extended metadata attributes found in the model. By default the exporter is generating only those given by the `-e`/`--extended-attributes` parameter.

### --pretty
If the parameter is set it will pretty-print the JSON output, otherwise you will get a minimized version

## JSONSCHEMA exporter notes

### --extended-all-attributes
Lets the exporter generate _all_ extended metadata attributes found in the model. By default the exporter is generating only those given by the `-e`/`--extended-attributes` parameter. This will also add unconverted VSS standard attributes into the schema using the following attributes

| VSS attribute | in schema     |
|---------------|---------------|
| type          | x-VSStype     |
| datatype      | x-datatype    |
| deprecation   | x-deprecation |
| aggregate     | x-aggregate   |
| comment       | x-comment     |

Not that strict JSON schema validators might not accept jsonschemas with such extra, non-standard entries.

### --no-additional-properties
Do not allow properties not defined in VSS tree, when elements are validated against the schema, what this basically does is setting

```json
"additionalProperties": false
```
for all defined objects. See: https://json-schema.org/draft/2020-12/json-schema-core#additionalProperties

###  --require-all-properties
Require all elements defined in VSS tree for a valid object, i.e. this populates the `required` list with all children. See: https://json-schema.org/draft/2020-12/json-schema-validation#name-required

### --pretty
If the paramter is set it will pretty-print the JSON output, otherwise you will get a minimized version

## YAML exporter notes

### --extended-all-attributes
Lets the exporter generate _all_ extended metadata attributes found in the model. By default the exporter is generating only those given by the `-e`/`--extended-attributes` parameter.

### --all-idl-features
Will also generate non-payload const attributes such as unit/datatype. Default is not to generate them/comment them out because at least Cyclone DDS and FastDDS do not support const. For more information check the [DDS-IDL exporter docs](ddsidl.md).

## GRAPHQL exporter notes

### --gql-fields name,description
Add additional fields to the nodes in the graphql schema. use: <field_name>,<description>.
Can be used more than once.


## Writing your own generator

Just have a look at current implementations of exporters.
Start by copy pasting the `def cli()`. Think about parameters the exporter supports.


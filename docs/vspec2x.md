# vspec2x converters

vspec2x is a family of VSS converters that share a common codebase.

As a consequence it provides general commndline parameters guidng the parsing of vspec, as well as paramters specific to specific output formats.

You can get a description of supported commandlines parameters by running `vspec2x.py --help`.

This documentation will give some examples and elaborate more on specific parameters.

The supported arguments might look like this
 ```
usage: vspec2x.py [-h] [-I dir] [-e EXTENDED_ATTRIBUTES] [-s] [--abort-on-unknown-attribute] [--abort-on-name-style]
                  [--format format] [--uuid] [--no-uuid] [-o overlays] [--json-all-extended-attributes] [--json-pretty]
                  [--yaml-all-extended-attributes] [-v version] [--all-idl-features] [--gqlfield GQLFIELD GQLFIELD]
                  <vspec_file> <output_file>
```

A common commandline to convert the VSS standard catalogue into a JSON file is

```
% python vspec2x.py --format json  -I ../spec ../spec/VehicleSignalSpecification.vspec vss.js
on
Output to json format
Known extended attributes: 
Loading vspec from ../spec/VehicleSignalSpecification.vspec...
Calling exporter...
Generating JSON output...
Serializing compact JSON...
All done.
```

This assumes you checked out the [COVESA Vehicle Singal Specification](https://github.com/covesa/vehicle_signal_specification) which contains vss-tools including vspec2x as a submodule.

The `-I` parameter adds a directory to search for includes referenced in you `.vspec` files. `-I` can be used multiple times to specify more include directories.

The first positional argument - `../spec/VehicleSignalSpecification.vspec` in the example  - gives the (root) `.vspec` file to be converted. The second positional argument  - `vss.json` in the example - is the output file.

The `--format` parameter determines the output format, `JSON` in our example. If format is omitted `vspec2x` tries to guess the correct output format based on the extension of the second positional argument. Alternatively vss-tools supports *shortcuts* for community supported exporters, e.g. `vspec2json.py` for generating JSON. The shortcuts really only add the `--format` parameter for you, so 

```
python vspec2json.py  json  -I ../spec ../spec/VehicleSignalSpecification.vspec vss.js
```

is equivalent to the example above.

## General parameters

### --abort-on-unknown-attribute
Terminates parsing when an unknown attribute is encountered, that is an attribute that is not defined in the [VSS standard catalogue](https://covesa.github.io/vehicle_signal_specification/rule_set/), and not whitelisted using the extended attribute parameter `-e` (see below).

*Note*: Here an *attribute* refers to VSS signal metadata sich as "datatype", "min", "max", ... and not to the VSS signal type attribute

###  --abort-on-name-style
Terminates parsing, when the name of a signal does not follow [VSS recomendations](https://covesa.github.io/vehicle_signal_specification/rule_set/basics/#naming-conventions).

### --strict
Equivalent to setting `--abort-on-unknown-attribute` and `--abort-on-name-style` 

### --uuid
Request the exporter to output uuids. This setting may not apply to all exporters, some exporters will never output uuids.
This is currently the default behavior. From VSS 4.0 `--no-uuid` will be the default behavior.

### --no-uuid
Request the exporter to not utput uuids.
From VSS 4.0 this will be the default behavior and then this parameter will be deprecated.

## Handling of overlays and extensions
`vspec2x` allows composition of several overlays on top of a base vspec, to extend the model or overwrite certain metadata. Check [VSS documentation](https://covesa.github.io/vehicle_signal_specification/introduction/) on the concept of overlays. 

To add overlays add one or more `-o` or  `--overlays` parameters, e.g.

```
python vspec2yaml.py -I ../spec ../spec/VehicleSignalSpecification.vspec  -o overlay.vspec  withoverlay.yml
```

You can also use VSS specifications with custom metadata not used in the standard catalogue, for example if your VSS model includes a `source` or `quality` metadata for sensors.

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

Will give a warning about unknown attributes, or even terminate the parsing when `-s`, `--strict`  or `--abort-on-unknown-attribute` is used

```
% python vspec2json.py -I ../spec ../spec/VehicleSignalSpecification.vspec --strict -o overlay.vspec   test.json
Output to json format
Known extended attributes: 
Loading vspec from ../spec/VehicleSignalSpecification.vspec...
Applying VSS overlay from overlay.vspec...
Warning: Attribute(s) quality, source, lol in element Speed not a core or known extended attribute.
You asked for strict checking. Terminating.
```

You can whitelist extended metadata attributes using the `-e` parameter with a comma sperated list of attributes

```
python vspec2json.py -I ../spec ../spec/VehicleSignalSpecification.vspec -e quality,source -o overlay.vspec   test.json
```

In this case the expectation is, that the general expectation is, that the generated output will contain the whitelisted extended metadata attributes, if the exporter supports them.

__Note: Not all exporters (need to) support (all) extended metadata attributes!__ Currently, the `yaml` and `json` exporters support arbitrary metadata.

## JSON exporter notes

### --json-all-extended-attributes
Lets the exporter generate _all_ extended metadata attributes found in the model. By default the exporter is generating only those given by the `-e`/`--extended-attributes` parameter.

### --json-pretty
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


## Writing your own exporter
This is easy. Put the code in file in the [vssexporters directory](../vssexporters/). 

Mandatory functions to be implemented are
```python
def add_arguments(parser: argparse.ArgumentParser):
```

and

```python
def export(config: argparse.Namespace, root: VSSNode):
```
See one of the existing exporters for an example.

Add your exporter module to the `Exporter` class in [vspec2x.py](../vspec2x.py). 
 
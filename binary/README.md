# Binary Toolset
The binary toolset consists of a tool that translates the VSS YAML specification to the binary file format (see below),
and two libraries that provides methods that are likely to be needed by a server that manages the VSS tree, one written in C, and one in Go.<br>

## Binary Parser Usage
The translation tool can be invoked via the make file available on the VSS repo (https://github.com/COVESA/vehicle_signal_specification):

```bash
make binary
```
or, by invoking all tools:

```bash
make all
```

To **run the binary tool without using the make file**, the binary tool library must first be built in the
binary directory, then the binary exporter of `vspec exporter` is executed in the root directory:

```bash
cd binary
gcc -shared -o binarytool.so -fPIC binarytool.c
cd <vss-root>
vspec export binary -u spec/units.yaml --vspec spec/VehicleSignalSpecification.vspec -o vss.binary -b binary/binarytool.so
```

where `vss.binary` is the tree file in binary format.

Current version is found at https://github.com/COVESA/vehicle_signal_specification/blob/master/VERSION.

### Validation
Access Control of the signals can be supported by including the extended attribute validate in each of the nodes.
This attribute is used by the VISSv2 specification.
More information can be found in:
[VISS Access Control](https://www.w3.org/TR/viss2-core/#access-control-selection).
In case the validate attribute is added to the nodes, it must be specified when invoking the tool
using the extended attributes flag `-e`:

```bash
cd ..  # continue from the previous example
vspec export binary -e validate -u ./spec/units.yaml --vspec ./spec/VehicleSignalSpecification.vspec -o vss.binary -b binary/binarytool.so
```


## Tool Functionalities
The two libraries provides the same set of methods, such as:

- to read the file into memory,
- to write it back to file,
- to search the tree for a given path (with usage of wildcard in the path expression),
- to create a JSON file of the leaf node paths of the VSS tree,
- to traverse the tree (up/down/left/right),
- and more.

Each library is also complemented with a testparser that uses the library to traverse the tree, make searches to it, etc.

A textbased UI presents different parser commands, that is then executed and the results are presented.

### C parser
To build the testparser from the c_parser directory:

```bash
cc testparser.c cparserlib.c -o ctestparser
```
When starting it, the path to the binary file must be provided. If started from the c_parser directory,
and assuming a binary tree file has been created in the VSS parent directory:

```bash
./ctestparser ../../../vss_rel_<current version>.binary
```

### Go parser
To build the testparser from the go_parser directory:

```bash
go build -o gotestparser testparser.go
```
When starting it, the path to the binary file must be provided. If started from the go_parser directory,
and assuming a binary tree file has been created in the VSS parent directory:

```bash
./gotestparser ../../../vss_rel_<current version>.binary
```

## Encoding

The binary node file format is as follows:<br>
    Name        | Datatype  | #bytes<br>
    ---------------------------------------<br>
    NameLen     | uint8     | 1<br>
    Name        | chararray | NameLen<br>
    NodeTypeLen | uint8     | 1<br>
    NodeType    | chararray | NodeTypeLen<br>
    UuidLen     | uint8     | 1<br>
    Uuid        | chararray | UuidLen<br>
    DescrLen    | uint8     | 1<br>
    Description | chararray | DescrLen<br>
    DatatypeLen | uint8     | 1<br>
    Datatype    | chararray | DatatypeLen<br>
    MinLen      | uint8     | 1<br>
    Min         | chararray | MinLen<br>
    MaxLen      | uint8     | 1<br>
    Max         | chararray | MaxLen<br>
    UnitLen     | uint8     | 1<br>
    Unit        | chararray | UnitLen<br>
    AllowedLen  | uint8     | 1<br>
    Allowed     | chararray | AllowedLen<br>
    DefaultLen  | uint8     | 1<br>
    Default     | chararray | AllowedLen<br>
    ValidateLen | uint8     | 1<br>
    Validate    | chararray | ValidateLen<br>
    Children    | uint8     | 1<br><br>

The Allowed string contains an array of allowed, each Allowed is preceeded by two characters holding the size of the Allowed sub-string.
The size is in hex format, with values from "01" to "FF". An example is "03abc0A012345678902cd" which contains the three Alloweds "abc", "0123456789", and "cd".<br><br>

The nodes are written into the file in the order given by a recursive method as shown in the following pseudocode:

```python
def traverseAndWriteNode(thisNode):
	writeNode(thisNode)
	for i = 0 ; i < thisNode.Children ; i++:
		traverseAndWriteNode(thisNode.Child[i])
```

When reading the file the same recursive pattern must be used to generate the correct VSS tree, as is the case for all the described tools.

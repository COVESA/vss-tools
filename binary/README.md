# Binary Toolset
The binary toolset consists of a tool that translates the VSS YAML specification to the binary file format (see below),
and two libraries that provides methods that are likely to be needed by a server that manages the VSS tree, one written in C, and one in Go.

## Binary Parser Usage

```bash
vspec export binary -u spec/units.yaml --vspec spec/VehicleSignalSpecification.vspec -o vss.binary
```

where `vss.binary` is the tree file in binary format.

### Validation

Access Control of the signals can be supported by including the extended attribute validate in each of the nodes.
This attribute is used by the VISSv2 specification.
More information can be found in:
[VISS Access Control](https://www.w3.org/TR/viss2-core/#access-control-selection).
In case the validate attribute is added to the nodes, it must be specified when invoking the tool
using the extended attributes flag `-e`:

```bash
vspec export binary -e validate -u ./spec/units.yaml --vspec ./spec/VehicleSignalSpecification.vspec -o vss.binary
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

The binary node file format is as follows:

Name        | Datatype  | #bytes
------------|-----------|--------------
NameLen     | uint8     | 1
Name        | chararray | NameLen
NodeTypeLen | uint8     | 1
NodeType    | chararray | NodeTypeLen
UuidLen     | uint8     | 1
Uuid        | chararray | UuidLen
DescrLen    | uint8     | 1
Description | chararray | DescrLen
DatatypeLen | uint8     | 1
Datatype    | chararray | DatatypeLen
MinLen      | uint8     | 1
Min         | chararray | MinLen
MaxLen      | uint8     | 1
Max         | chararray | MaxLen
UnitLen     | uint8     | 1
Unit        | chararray | UnitLen
AllowedLen  | uint8     | 1
Allowed     | chararray | AllowedLen
DefaultLen  | uint8     | 1
Default     | chararray | AllowedLen
ValidateLen | uint8     | 1
Validate    | chararray | ValidateLen
Children    | uint8     | 1

The Allowed string contains an array of allowed, each Allowed is preceeded by two characters holding the size of the Allowed sub-string.
The size is in hex format, with values from "01" to "FF". An example is "03abc0A012345678902cd" which contains the three Alloweds "abc", "0123456789", and "cd".

The nodes are written into the file in the order given by a recursive method as shown in the following pseudocode:

```python
def traverseAndWriteNode(thisNode):
   writeNode(thisNode)
   for i = 0 ; i < thisNode.Children ; i++:
      traverseAndWriteNode(thisNode.Child[i])
```

When reading the file the same recursive pattern must be used to generate the correct VSS tree, as is the case for all the described tools.

<h1> Binary Toolset </h1>
The binary toolset consists of a tool that translates the VSS YAML specification to the binary file format (see below), 
and two libraries that provides methods that are likely to be needed by a server that manages the VSS tree, one written in C, and one in Go.<br>

<h3>Binary Parser Usage </h3>
The translation tool can be invoked via the make file available on the VSS repo (https://github.com/COVESA/vehicle_signal_specification):

```
$ make binary
```
or, by invoking all tools:

```
$ make all
```

To <b>run the binary tool without using the make file</b>, the binary tool library must first be built in the binary directory, then the vspec2binary.py is executed in the root directory:

```
$ cd binary
/binary$ gcc -shared -o binarytool.so -fPIC binarytool.c
$ cd ..
$ vspec2binary.py -u ./spec/units.yaml ./spec/VehicleSignalSpecification.vspec vss.binary
```
where vss_rel_<current version>.binary is the tre file in binary format.
<br><br>
Current version is found at https://github.com/COVESA/vehicle_signal_specification/blob/master/VERSION.
<br>

<h4> Validation </h4>
Access Control of the signals can be supported by including the extended attribute validate in each of the nodes. This attribute is used by the VISSv2 specification. More information can be found in: <a href="https://www.w3.org/TR/viss2-core/#access-control-selection">VISS Access Control. </a>In case the validate attribute is added to the nodes, it must be specified when invoking the tool using the extended attributes flag (-e): 

```
$ vspec2binary.py -e validate -u ./spec/units.yaml ./spec/VehicleSignalSpecification.vspec vss.binary
```


<h3>Tool Functionalities </h3>
The two libraries provides the same set of methods, such as:
<ul>
<li>to read the file into memory,</li>
<li>to write it back to file,</li>
<li>to search the tree for a given path (with usage of wildcard in the path expression),</li>
<li>to create a JSON file of the leaf node paths of the VSS tree,</li>
<li>to traverse the tree (up/down/left/right),</li>
<li>and more.</li>
</ul>

Each library is also complemented with a testparser that uses the library to traverse the tree, make searches to it, etc.
<br>
A textbased UI presents the different options, with following results.<br>

<h5>C parser</h5>
To build the testparser from the c_parser directory:

```
$ cc testparser.c cparserlib.c -o ctestparser
```
When starting it, the path to the binary file must be provided. If started from the c_parser directory:

```
$ ./ctestparser ../../vss_rel_<current version>.binary
```

<h5>Go parser </h5>
To build the testparser from the go_parser directory:

```
$ go build -o gotestparser testparser.go 
```
When starting it, the path to the binary file must be provided. If started from the go_parser directory:

```
$ ./gotestparser ../../vss_rel_<current version>.binary
```

<h3>Encoding</h3>
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

The nodes are written into the file in the order given by an iterative method as shown in the following pseudocode:
```
def traverseAndWriteNode(thisNode):
	writeNode(thisNode)
	for i = 0 ; i < thisNode.Children ; i++:
		traverseAndWriteNode(thisNode.Child[i])
```

When reading the file the same iterative pattern must be used to generate the correct VSS tree, as is the case for all the described tools.


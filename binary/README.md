The binary toolset consists of a tool that translates the VSS YAML specification to the binary file format (see below), 
and two libraries that provides methods that are likely to be needed by a server that manages the VSS tree, one written in C, and one in Go.<br>

The translation tool can be invoked via the make file available on the VSS repo (https://github.com/COVESA/vehicle_signal_specification):<br>
$ make binary<br>
or, by invoking all tools:<br>
$ make all<br>
To run the binary tool without using the make file, the binary tool libray must first be built in the binary directory:<br>
$ gcc -shared -o binarytool.so -fPIC binarytool.c<br>
then the vspec2binary.py is executed in the root directory:<br>
$ vspec2binary.py -i:./spec/VehicleSignalSpecification.id ./spec/VehicleSignalSpecification.vspec vss_rel_<current version>.binary<br>
where vss_rel_<current version>.binary is the tre file in binary format.<br>
Current version is found at https://github.com/COVESA/vehicle_signal_specification/blob/master/VERSION.<br>

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
A textbased UI presents the different options, with following results.<br>

To build the testparser from the c_parser directory:<br>
$ cc testparser.c cparserlib.c -o ctestparser<br>
When starting it, the path to the binary file must be provided. If started from the c_parser directory:<br>
$ ./ctestparser ../../vss_rel_<current version>.binary<br>

To build the testparser from the go_parser directory:<br>
$ go build testparser.go  -o gotestparser<br>
When starting it, the path to the binary file must be provided. If started from the go_parser directory:<br>
$ ./gotestparser ../../vss_rel_<current version>.binary<br><br>

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

The nodes are written into the file in the order given by an iterative method as shown in the following pseudocode.<br>
def traverseAndWriteNode(thisNode):<br>
	writeNode(thisNode)<br>
	for i = 0 ; i < thisNode.Children ; i++:<br>
		traverseAndWriteNode(thisNode.Child[i])<br><br>

When reading the file the same iterative pattern must be used to generate the correct VSS tree, as is the case for all the described tools.


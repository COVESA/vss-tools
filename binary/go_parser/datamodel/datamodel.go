/**
* (C) 2020 Geotab Inc
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
*
* Go binary format VSS data model.
**/

package datamodel

import "fmt"

type NodeTypes_t uint8

const (   // allowed elements of nodeTypes_t
    SENSOR = 1
    ACTUATOR = 2
    ATTRIBUTE = 3
    BRANCH = 4
)

type NodeDatatypes_t uint8

const (   // allowed elements of nodeDatatypes_t
    INT8 = 1
    UINT8 = 2
    INT16 = 3
    UINT16 = 4
    INT32 = 5
    UINT32 = 6
    DOUBLE = 6
    FLOAT = 8
    BOOLEAN = 9
    STRING = 10
    INT8ARRAY = 11
    UINT8ARRAY = 12
    INT16ARRAY = 13
    UINT16ARRAY = 14
    INT32ARRAY = 15
    UINT32ARRAY = 16
    DOUBLEARRAY = 17
    FLOATARRAY = 18
    BOOLEANARRAY = 19
    STRINGARRAY = 20
)

type Node_t struct {
    Name string
    NodeType NodeTypes_t
    Uuid string
    Description string
    Datatype NodeDatatypes_t
    Min string
    Max string
    Unit string
    Allowed uint8
    AllowedDef []string
    DefaultAllowed string
    Validate uint8
    Children uint8
    Parent *Node_t
    Child []*Node_t
}

func StringToNodetype(nodeType string) uint8 {
    if (nodeType == "sensor") {
        return SENSOR
    }
    if (nodeType == "actuator") {
        return ACTUATOR
    }
    if (nodeType == "attribute") {
        return ATTRIBUTE
    }
    if (nodeType == "branch") {
        return BRANCH
    }
    fmt.Printf("Unknown type! |%s|\n", nodeType);
    return 0
}

func StringToDataType(datatype string) uint8 {
    if (datatype == "int8") {
        return INT8
    }
    if (datatype == "uint8") {
        return UINT8
    }
    if (datatype == "int16") {
        return INT16
    }
    if (datatype == "uint16") {
        return UINT16
    }
    if (datatype == "int32") {
        return INT32
    }
    if (datatype == "uint32") {
        return UINT32
    }
    if (datatype == "double") {
        return DOUBLE
    }
    if (datatype == "float") {
        return FLOAT
    }
    if (datatype == "boolean") {
        return BOOLEAN
    }
    if (datatype == "string") {
        return STRING
    }
    if (datatype == "int8[]") {
        return INT8ARRAY
    }
    if (datatype == "uint8[]") {
        return UINT8ARRAY
    }
    if (datatype == "int16[]") {
        return INT16ARRAY
    }
    if (datatype == "uint16[]") {
        return UINT16ARRAY
    }
    if (datatype == "int32[]") {
        return INT32ARRAY
    }
    if (datatype == "uint32[]") {
        return UINT32ARRAY
    }
    if (datatype == "double[]") {
        return DOUBLEARRAY
    }
    if (datatype == "float[]") {
        return FLOATARRAY
    }
    if (datatype == "boolean[]") {
        return BOOLEANARRAY
    }
    if (datatype == "string[]") {
        return STRINGARRAY
    }
    fmt.Printf("Unknown datatype! |%s|\n", datatype)
    return 0
}

func ValidateToInt(validate string) uint8 {
    if (validate == "write-only") {
        return 1
    }
    if (validate == "read-write") {
        return 2
    }
    return 0
}

func NodetypeToString(nodeType NodeTypes_t) string {
    if (nodeType == SENSOR) {
        return "sensor"
    }
    if (nodeType == ACTUATOR) {
        return "actuator"
    }
    if (nodeType == ATTRIBUTE) {
        return "attribute"
    }
    if (nodeType == BRANCH) {
        return "branch"
    }
    fmt.Printf("Unknown type! |%d|\n", nodeType);
    return ""
}

func DataTypeToString(datatype NodeDatatypes_t) string {
    if (datatype == INT8) {
        return "int8"
    }
    if (datatype == UINT8) {
        return "uint8"
    }
    if (datatype == INT16) {
        return "int16"
    }
    if (datatype == UINT16) {
        return "uint16"
    }
    if (datatype == INT32) {
        return "int32"
    }
    if (datatype == UINT32) {
        return "uint32"
    }
    if (datatype == DOUBLE) {
        return "double"
    }
    if (datatype == FLOAT) {
        return "float"
    }
    if (datatype == BOOLEAN) {
        return "boolean"
    }
    if (datatype == STRING) {
        return "string"
    }
    if (datatype == INT8ARRAY) {
        return "int8[]"
    }
    if (datatype == UINT8ARRAY) {
        return "uint8[]"
    }
    if (datatype == INT16ARRAY) {
        return "int16[]"
    }
    if (datatype == UINT16ARRAY) {
        return "uint16[]"
    }
    if (datatype == INT32ARRAY) {
        return "int32[]"
    }
    if (datatype == UINT32ARRAY) {
        return "uint32[]"
    }
    if (datatype == DOUBLEARRAY) {
        return "double[]"
    }
    if (datatype == FLOATARRAY) {
        return "float[]"
    }
    if (datatype == BOOLEANARRAY) {
        return "boolean[]"
    }
    if (datatype == STRINGARRAY) {
        return "string[]"
    }
    fmt.Printf("Unknown datatype! |%d|\n", datatype)
    return ""
}

func ValidateToString(validate uint8) string {
    if (validate == 1) {
        return "write-only"
    }
    if (validate == 2) {
        return "read-write"
    }
    return ""
}


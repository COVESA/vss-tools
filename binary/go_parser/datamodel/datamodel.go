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
    STRUCT = 5
    PROPERTY = 6
)

type Node_t struct {
    Name string
    NodeType NodeTypes_t
    Uuid string
    Description string
    Datatype string
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
    if (nodeType == "branch") {
        return BRANCH
    }
    if (nodeType == "sensor") {
        return SENSOR
    }
    if (nodeType == "actuator") {
        return ACTUATOR
    }
    if (nodeType == "attribute") {
        return ATTRIBUTE
    }
    if (nodeType == "struct") {
        return STRUCT
    }
    if (nodeType == "propery") {
        return PROPERTY
    }
    fmt.Printf("Unknown type! |%s|\n", nodeType);
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
    if (nodeType == BRANCH) {
        return "branch"
    }
    if (nodeType == SENSOR) {
        return "sensor"
    }
    if (nodeType == ACTUATOR) {
        return "actuator"
    }
    if (nodeType == ATTRIBUTE) {
        return "attribute"
    }
    if (nodeType == STRUCT) {
        return "struct"
    }
    if (nodeType == PROPERTY) {
        return "propery"
    }
    fmt.Printf("Unknown type! |%d|\n", nodeType);
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

/**
* (C) 2020 Geotab Inc
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
*
* Test parser for the binary VSS tree.
**/

package main

import (
    def "github.com/COVESA/vss-tools/binary/go_parser/datamodel"
    parser "github.com/COVESA/vss-tools/binary/go_parser/parserlib"
    "os"
//    "strings"
    "fmt"
)

var root *def.Node_t

func getTypeName(nodeType def.NodeTypes_t) string {
    switch (nodeType) { 
        case def.SENSOR:
            return "SENSOR"
        case def.ACTUATOR:
            return "ACTUATOR"
        case def.ATTRIBUTE:
            return "ATTRIBUTE"
        case def.BRANCH:
            return "BRANCH"
        default:
            fmt.Printf("getTypeName: unknown type(%d)\n", nodeType)
            return "unknown"
    } // switch
}

func showNodeData(currentNode *def.Node_t, currentChild int) {
        fmt.Printf("\nNode: name = %s, type = %s, uuid = %s, validate = %d, children = %d,\ndescription = %s\n", parser.VSSgetName(currentNode), getTypeName(parser.VSSgetType(currentNode)), parser.VSSgetUUID(currentNode), parser.VSSgetValidation(currentNode), parser.VSSgetNumOfChildren(currentNode), parser.VSSgetDescr(currentNode))
        if (parser.VSSgetNumOfChildren(currentNode) > 0) {
            fmt.Printf("Node child[%d]=%s\n", currentChild, parser.VSSgetName(parser.VSSgetChild(currentNode, currentChild)))
        }
        for i := 0 ; i < parser.VSSgetNumOfAllowedElements(currentNode) ; i++ {
            fmt.Printf("Allowed[%d]=%s\n", i, parser.VSSgetAllowedElement(currentNode, i))
        }
        dtype := parser.VSSgetDatatype(currentNode)
        if (dtype != 0) {
            fmt.Printf("Datatype = %d\n", dtype)
        }
        tmp := parser.VSSgetUnit(currentNode)
        if (len(tmp) != 0) {
            fmt.Printf("Unit = %s\n", tmp)
        }
}

func main() {
    if len(os.Args) != 2 {
        fmt.Printf("testparser command line: ./testparser filename\n")
	os.Exit(1)
    }
    root = parser.VSSReadTree(os.Args[1])
    fmt.Printf("VSS tree root name = %s\n", parser.VSSgetName(root))
    var traverse string
    fmt.Printf("\nTo traverse the tree, 'u'(p)p/'d'(own)/'l'(eft)/'r'(ight)/s(earch)/m(etadata subtree)/n(odelist)/(uu)i(dlist)/w(rite to file)/h(elp), or any other to quit\n")
    currentNode := root
    currentChild := 0
    for {
        fmt.Printf("\n'u'/'d'/'l'/'r'/'s'/'m'/'n'/'i'/'w'/'h', or any other to quit: ")
        fmt.Scanf("%s", &traverse)
        switch (traverse[0]) {
            case 'u':  //up
                if (parser.VSSgetParent(currentNode) != nil) {
                    currentNode = parser.VSSgetParent(currentNode)
                    currentChild = 0
                }
                showNodeData(currentNode, currentChild)
            case 'd':  //down
                if (parser.VSSgetChild(currentNode, currentChild) != nil) {
                    currentNode = parser.VSSgetChild(currentNode, currentChild)
                    currentChild = 0
                }
                showNodeData(currentNode, currentChild)
            case 'l':  //left
                if (currentChild > 0) {
                    currentChild--
                }
                showNodeData(currentNode, currentChild)
            case 'r':  //right
                if (currentChild < parser.VSSgetNumOfChildren(currentNode)-1) {
                    currentChild++
                }
                showNodeData(currentNode, currentChild)
            case 's':  //search for nodes matching path
            {
                var searchPath string
                fmt.Printf("\nPath to resource(s): ")
                fmt.Scanf("%s", &searchPath)
                searchData, foundResponses := parser.VSSsearchNodes(searchPath, root, parser.MAXFOUNDNODES, true, true, 0, nil, nil)
                fmt.Printf("\nNumber of elements found=%d\n", foundResponses)
                for i := 0 ; i < foundResponses ; i++ {
                    fmt.Printf("Found node type=%s\n", getTypeName(parser.VSSgetType(searchData[i].NodeHandle)))
                    fmt.Printf("Found node datatype=%d\n", parser.VSSgetDatatype(searchData[i].NodeHandle))
                    fmt.Printf("Found path=%s\n", searchData[i].NodePath)
                }
            }
            case 'n':  //create node list file "nodelist.txt"
            {
                numOfNodes := parser.VSSGetLeafNodesList(root, "nodelist.txt")
                fmt.Printf("\nLeaf node list with %d nodes found in nodelist.txt\n", numOfNodes)
            }
            break;
            case 'i':  //create node list file "uuidlist.txt"
            {
                numOfNodes := parser.VSSGetUuidList(root, "uuidlist.txt")
                fmt.Printf("\nUUID list with %d nodes found in uuidlist.txt\n", numOfNodes)
            }
            case 'm':  //subtree metadata
            {
                var subTreePath string
                fmt.Printf("\nPath to subtree node: ")
                fmt.Scanf("%s", &subTreePath)
                var depth int
                fmt.Printf("\nSubtree depth: ")
                fmt.Scanf("%d", &depth)
                searchData, foundResponses := parser.VSSsearchNodes(subTreePath, root, parser.MAXFOUNDNODES, false, false, 0, nil, nil)
                subtreeNode := searchData[foundResponses-1].NodeHandle
                subTreeRootName := parser.VSSgetName(searchData[foundResponses-1].NodeHandle)
                for i := 1 ; i < depth ; i++ {
                    subTreeRootName += ".*"
                }
                fmt.Printf("\nsubTreeRootName=%s\n", subTreeRootName)
                searchData, foundResponses = parser.VSSsearchNodes(subTreeRootName, subtreeNode, parser.MAXFOUNDNODES, false, false, 0, nil, nil)
                fmt.Printf("\nNumber of elements found=%d\n", foundResponses)
                for i := 0 ; i < foundResponses ; i++ {
                    fmt.Printf("Node type=%d\n", parser.VSSgetType(searchData[i].NodeHandle))
                    fmt.Printf("Node path=%s\n", searchData[i].NodePath)
                    fmt.Printf("Node validation=%d\n", parser.VSSgetValidation(searchData[i].NodeHandle))
                }
            }
            case 'h':  //help
                fmt.Printf("\nTo traverse the tree, 'u'(p)p/'d'(own)/'l'(eft)/'r'(ight)/s(earch)/m(etadata subtree)/n(odelist)/(uu)i(dlist)/w(rite to file)/h(elp), or any other to quit\n")
            case 'w':  //write to file
                parser.VSSWriteTree(os.Args[1], root)
            default:
                os.Exit(0)
        }  //switch
    } //for

}

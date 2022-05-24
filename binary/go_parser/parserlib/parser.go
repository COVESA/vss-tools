/**
* (C) 2020 Geotab Inc
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
*
* Go binary VSS tree parser.
**/

package parserlib

import (
    def "github.com/COVESA/vss-tools/binary/go_parser/datamodel"
    "os"
    "strings"
    "fmt"
)

var treeFp *os.File

type ReadTreeMetadata_t struct {
    CurrentDepth int
    MaxTreeDepth int
    TotalNodes int
}
var readTreeMetadata ReadTreeMetadata_t

var isGetLeafNodeList bool
var isGetUuidList bool

const MAXFOUNDNODES = 1500
type SearchData_t struct {
    NodePath string
    NodeHandle *def.Node_t
}

type SearchContext_t struct {
	RootNode *def.Node_t
	MaxFound int
	LeafNodesOnly bool
	MaxDepth int
	SearchPath string
	MatchPath string
	CurrentDepth int  // depth in tree from rootNode, and also depth (in segments) in searchPath
	SpeculationIndex int  // inc/dec when pathsegment in focus is wildcard
	SpeculativeMatches [20]int  // inc when matching node is saved
	MaxValidation int
	NumOfMatches int
	SearchData []SearchData_t
	ListSize int
	NoScopeList []string
	ListFp *os.File
}

func initReadMetadata() {
	readTreeMetadata.CurrentDepth = 0
	readTreeMetadata.MaxTreeDepth = 0
	readTreeMetadata.TotalNodes = 0
}

func updateReadMetadata(increment bool) {
	if (increment == true) {
		readTreeMetadata.TotalNodes++
		readTreeMetadata.CurrentDepth++
		if (readTreeMetadata.CurrentDepth > readTreeMetadata.MaxTreeDepth) {
			readTreeMetadata.MaxTreeDepth++
		}
	} else {
		readTreeMetadata.CurrentDepth--
	}
}

func printReadMetadata() {
	fmt.Printf("\nTotal number of nodes in VSS tree = %d\n", readTreeMetadata.TotalNodes)
	fmt.Printf("Max depth of VSS tree = %d\n", readTreeMetadata.MaxTreeDepth)
}

func countAllowedElements(allowedStr string) int {  // allowed string has format "XXallowed1XXallowed2...XXallowedx", where XX are hex values; X=[0-9,A-F]
    nrOfAllowed := 0
    index := 0
    for  index < len(allowedStr) {
        hexLen := allowedStr[index:index+2]
        allowedLen := hexToInt(byte(hexLen[0])) * 16 + hexToInt(byte(hexLen[1]))
        index += allowedLen + 2
        nrOfAllowed++
    }
    return nrOfAllowed
}

func hexToInt(hexDigit byte) int {
    if (hexDigit <= '9') {
        return (int)(hexDigit - '0')
    }
    return (int)(hexDigit - 'A' + 10)
}

func intToHex(intVal int) []byte {
    if (intVal > 255) {
        return nil
    }
    hexVal := make([]byte, 2)
    hexVal[0] = hexDigit(intVal/16)
    hexVal[1] = hexDigit(intVal%16)
    return hexVal
}

func hexDigit(value int) byte {
    if (value < 10) {
        return byte(value + '0')
    }
    return byte(value - 10 + 'A')
}

func extractAllowedElement(allowedBuf string, elemIndex int) string {
    var allowedstart int
    var allowedend int
    bufIndex := 0
    for alloweds := 0 ; alloweds <= elemIndex ; alloweds++ {
        hexLen := allowedBuf[bufIndex:bufIndex+2]
        allowedLen := hexToInt(byte(hexLen[0])) * 16 + hexToInt(byte(hexLen[1]))
        allowedstart = bufIndex + 2
        allowedend = allowedstart + allowedLen
        bufIndex += allowedLen + 2
    }
    return allowedBuf[allowedstart:allowedend]
}

func traverseAndReadNode(parentNode *def.Node_t) *def.Node_t {
	var thisNode def.Node_t
	updateReadMetadata(true)
	populateNode(&thisNode)
	thisNode.Parent = parentNode
	if (thisNode.Children > 0) {
               thisNode.Child = make([]*def.Node_t, thisNode.Children)
	}
	var childNo uint8
	for childNo = 0 ; childNo < thisNode.Children ; childNo++ {
		thisNode.Child[childNo] = traverseAndReadNode(&thisNode)
	}
	updateReadMetadata(false)
	return &thisNode
}

func traverseAndWriteNode(node *def.Node_t) {
	writeNode(node)
	var childNo uint8
	for childNo = 0 ; childNo < node.Children ; childNo++ {
		traverseAndWriteNode(node.Child[childNo])
	}
}

func traverseNode(thisNode *def.Node_t, context *SearchContext_t) int {
	speculationSucceded := 0

	incDepth(thisNode, context)
//	fmt.Printf("before compareNodeName():VSSnodename=%s, pathnodename=%s\n", VSSgetName(thisNode), getPathSegment(0, context))
	if (compareNodeName(VSSgetName(thisNode), getPathSegment(0, context)) == true) {
		var done bool
		speculationSucceded = saveMatchingNode(thisNode, context, &done)
		if (done == false) {
			numOfChildren := VSSgetNumOfChildren(thisNode)
			childPathName := getPathSegment(1, context)
			for i := 0 ; i < numOfChildren ; i++ {
				if (compareNodeName(VSSgetName(VSSgetChild(thisNode, i)), childPathName) == true) {
					speculationSucceded += traverseNode(VSSgetChild(thisNode, i), context)
				}
			}
		}
	}
	decDepth(speculationSucceded, context)
	return speculationSucceded
}

func saveMatchingNode(thisNode *def.Node_t, context *SearchContext_t, done *bool) int {
	if (getPathSegment(0, context) == "*") {
		context.SpeculationIndex++
	}
	if (VSSgetValidation(thisNode) > context.MaxValidation) {
		context.MaxValidation = VSSgetValidation(thisNode)  // TODO handle speculative setting?
	}
	if (VSSgetType(thisNode) != def.BRANCH || context.LeafNodesOnly == false) {
		if ( isGetLeafNodeList == false && isGetUuidList == false) {
			context.SearchData[context.NumOfMatches].NodePath = context.MatchPath
			context.SearchData[context.NumOfMatches].NodeHandle = thisNode
		} else {
			if (isGetLeafNodeList == true) {
			    if (context.NumOfMatches == 0) {
				    context.ListFp.Write([]byte("\""))
			    } else {
				    context.ListFp.Write([]byte(", \""))
			    }
			    context.ListFp.Write([]byte(context.MatchPath))
			    context.ListFp.Write([]byte("\""))
			} else {
			    if (context.NumOfMatches == 0) {
				    context.ListFp.Write([]byte("{\"path\":\""))
			    } else {
				    context.ListFp.Write([]byte(", {\"path\":\""))
			    }
			    context.ListFp.Write([]byte(context.MatchPath))
			    context.ListFp.Write([]byte("\", \"uuid\":\""))
			    uuid := VSSgetUUID(thisNode)
			    context.ListFp.Write([]byte(uuid))
			    context.ListFp.Write([]byte("\"}"))
			}
		}
		context.NumOfMatches++
		if (context.SpeculationIndex >= 0) {
			context.SpeculativeMatches[context.SpeculationIndex]++
		}
	}
	if (VSSgetNumOfChildren(thisNode) == 0 || context.CurrentDepth == context.MaxDepth  || isEndOfScope(context) == true) {
		*done = true
	} else {
		*done = false
	}
	if (context.SpeculationIndex >= 0 && ((VSSgetNumOfChildren(thisNode) == 0 && context.CurrentDepth >= countSegments(context.SearchPath)) || context.CurrentDepth == context.MaxDepth)) {
		return 1
	}
	return 0
}

func isEndOfScope(context *SearchContext_t) bool {
    if (context.ListSize == 0) {
        return false
    }
    for i := 0 ; i < context.ListSize ; i++ {
        if (context.MatchPath == context.NoScopeList[i]) {
            return true
        }
    }
    return false
}

func compareNodeName(nodeName string, pathName string) bool {
	//fmt.Printf("compareNodeName(): nodeName=%s, pathName=%s\n", nodeName, pathName)
	if (nodeName == pathName || pathName == "*") {
		return true
	}
	return false
}

func pushPathSegment(name string, context *SearchContext_t) {
	if (context.CurrentDepth > 0) {
		context.MatchPath += "."
	}
	context.MatchPath += name
}

func popPathSegment(context *SearchContext_t) {
	delim := strings.LastIndex(context.MatchPath, ".")
	if (delim == -1) {
		context.MatchPath = ""
	} else {
		context.MatchPath = context.MatchPath[:delim]
	}
}

func getPathSegment(offset int, context *SearchContext_t) string {
	frontDelimiter := 0
	for i := 1 ; i < context.CurrentDepth + offset ; i++ {
		frontDelimiter += strings.Index(context.SearchPath[frontDelimiter+1:], ".") + 1
		if (frontDelimiter == -1) {
			if (context.SearchPath[len(context.SearchPath)-1] == '*' && context.CurrentDepth < context.MaxDepth) {
				return "*"
			} else {
				return ""
			}
		}
	}
	endDelimiter := strings.Index(context.SearchPath[frontDelimiter+1:], ".") + frontDelimiter + 1
	if (endDelimiter == frontDelimiter) {
		endDelimiter = len(context.SearchPath)
	}
	if (context.SearchPath[frontDelimiter] == '.') {
		frontDelimiter++
	}
	return context.SearchPath[frontDelimiter:endDelimiter]
}

func incDepth(thisNode *def.Node_t, context *SearchContext_t) {
	pushPathSegment(VSSgetName(thisNode), context)
	context.CurrentDepth++
}

/**
 * decDepth() shall reverse speculative wildcard matches that have failed, and also decrement currentDepth.
 **/
func decDepth(speculationSucceded int, context *SearchContext_t) {
	//fmt.Printf("decDepth():speculationSucceded=%d\n", speculationSucceded)
	if (context.SpeculationIndex >= 0 && context.SpeculativeMatches[context.SpeculationIndex] > 0) {
		if (speculationSucceded == 0) {  // it failed so remove a saved match
			context.NumOfMatches--
			context.SpeculativeMatches[context.SpeculationIndex]--
		}
	}
	if (getPathSegment(0, context) == "*") {
		context.SpeculationIndex--
	}
	popPathSegment(context)
	context.CurrentDepth--
}

func readBytes(numOfBytes uint32) []byte {
	if (numOfBytes > 0) {
	    buf := make([]byte, numOfBytes)
	    treeFp.Read(buf)
	    return buf
	}
	return nil
}

// The reading order must be synchronized with the writing order in the binary tool
func populateNode(thisNode *def.Node_t) {
	NameLen := deSerializeUInt(readBytes(1)).(uint8)
	thisNode.Name = string(readBytes((uint32)(NameLen)))

	NodeTypeLen := deSerializeUInt(readBytes(1)).(uint8)
	NodeType := string(readBytes((uint32)(NodeTypeLen)))
	thisNode.NodeType = (def.NodeTypes_t)(def.StringToNodetype(NodeType))

	UuidLen := deSerializeUInt(readBytes(1)).(uint8)
	thisNode.Uuid = string(readBytes((uint32)(UuidLen)))

	DescrLen := deSerializeUInt(readBytes(2)).(uint16)
	thisNode.Description = string(readBytes((uint32)(DescrLen)))

	DatatypeLen := deSerializeUInt(readBytes(1)).(uint8)
	Datatype := string(readBytes((uint32)(DatatypeLen)))
	if (thisNode.NodeType != def.BRANCH) {
	    thisNode.Datatype = (def.NodeDatatypes_t)(def.StringToDataType(Datatype))
	}

	MinLen := deSerializeUInt(readBytes(1)).(uint8)
	thisNode.Min = string(readBytes((uint32)(MinLen)))

	MaxLen := deSerializeUInt(readBytes(1)).(uint8)
	thisNode.Max = string(readBytes((uint32)(MaxLen)))

	UnitLen := deSerializeUInt(readBytes(1)).(uint8)
	thisNode.Unit = string(readBytes((uint32)(UnitLen)))

	allowedStrLen := deSerializeUInt(readBytes(2)).(uint16)
	allowedStr := string(readBytes((uint32)(allowedStrLen)))
	thisNode.Allowed = (uint8)(countAllowedElements(allowedStr))
	if (thisNode.Allowed > 0) {
            thisNode.AllowedDef = make([]string, thisNode.Allowed)
        }
	for i := 0 ; i < (int)(thisNode.Allowed) ; i++ {
	    thisNode.AllowedDef[i] = extractAllowedElement(allowedStr, i)
	}

	DefaultLen := deSerializeUInt(readBytes(1)).(uint8)
	thisNode.DefaultAllowed = string(readBytes((uint32)(DefaultLen)))

	ValidateLen := deSerializeUInt(readBytes(1)).(uint8)
	Validate := string(readBytes((uint32)(ValidateLen)))
	thisNode.Validate = def.ValidateToInt(Validate)

	thisNode.Children = deSerializeUInt(readBytes(1)).(uint8)

//	fmt.Printf("populateNode: %s\n", thisNode.Name)
}

// The reading order must be synchronized with the writing order in the binary tool
func writeNode(thisNode *def.Node_t) {
    treeFp.Write(serializeUInt((uint8)(len(thisNode.Name))))
    treeFp.Write([]byte(thisNode.Name))

    NodeType := def.NodetypeToString(thisNode.NodeType)
    treeFp.Write(serializeUInt((uint8)(len(NodeType))))
    treeFp.Write([]byte(NodeType))

    treeFp.Write(serializeUInt((uint8)(len(thisNode.Uuid))))
    treeFp.Write([]byte(thisNode.Uuid))

    treeFp.Write(serializeUInt((uint16)(len(thisNode.Description))))
    treeFp.Write([]byte(thisNode.Description))

    Datatype := def.DataTypeToString(thisNode.Datatype)
    treeFp.Write(serializeUInt((uint8)(len(Datatype))))
    if (len(Datatype) > 0) {
        treeFp.Write([]byte(Datatype))
    }

    treeFp.Write(serializeUInt((uint8)(len(thisNode.Min))))
    if (len(thisNode.Min) > 0) {
        treeFp.Write([]byte(thisNode.Min))
    }

    treeFp.Write(serializeUInt((uint8)(len(thisNode.Max))))
    if (len(thisNode.Max) > 0) {
        treeFp.Write([]byte(thisNode.Max))
    }

    treeFp.Write(serializeUInt((uint8)(len(thisNode.Unit))))
    if (len(thisNode.Unit) > 0) {
        treeFp.Write([]byte(thisNode.Unit))
    }

    allowedStrLen := calculatAllowedStrLen(thisNode.AllowedDef)
    treeFp.Write(serializeUInt((uint16)(allowedStrLen)))
    if (thisNode.Allowed > 0) {
	for i := 0 ; i < (int)(thisNode.Allowed) ; i++ {
	    allowedWrite(thisNode.AllowedDef[i])
	}
    }

    treeFp.Write(serializeUInt((uint8)(len(thisNode.DefaultAllowed))))
    if (len(thisNode.DefaultAllowed) > 0) {
        treeFp.Write([]byte(thisNode.DefaultAllowed))
    }

    Validate := def.ValidateToString(thisNode.Validate)
    treeFp.Write(serializeUInt((uint8)(len(Validate))))
    if (len(Validate) > 0) {
        treeFp.Write([]byte(Validate))
    }

    treeFp.Write(serializeUInt((uint8)(thisNode.Children)))

//    fmt.Printf("writeNode: %s\n", thisNode.Name)
}

func calculatAllowedStrLen(allowedDef []string) int {
    strLen := 0
    for i := 0 ; i < len(allowedDef) ; i++ {
        strLen += len(allowedDef[i]) + 2
    }
    return strLen
}

func allowedWrite(allowed string) {
    treeFp.Write(intToHex(len(allowed)))
fmt.Printf("allowedHexLen: %s\n", string(intToHex(len(allowed))))
    treeFp.Write([]byte(allowed))
}

func serializeUInt(intVal interface{}) []byte {
    switch intVal.(type) {
      case uint8:
        buf := make([]byte, 1)
        buf[0] = intVal.(byte)
        return buf
      case uint16:
        buf := make([]byte, 2)
        buf[1] = byte((intVal.(uint16) & 0xFF00)/256)
        buf[0] = byte(intVal.(uint16) & 0x00FF)
        return buf
      case uint32:
        buf := make([]byte, 4)
        buf[3] = byte((intVal.(uint32) & 0xFF000000)/16777216)
        buf[2] = byte((intVal.(uint32) & 0xFF0000)/65536)
        buf[1] = byte((intVal.(uint32) & 0xFF00)/256)
        buf[0] = byte(intVal.(uint32) & 0x00FF)
        return buf
      default:
        fmt.Println(intVal, "is of an unknown type")
        return nil
    }
}

func deSerializeUInt(buf []byte) interface{} {
    switch len(buf) {
      case 1:
        var intVal uint8
        intVal = (uint8)(buf[0])
        return intVal
      case 2:
        var intVal uint16
        intVal = (uint16)((uint16)((uint16)(buf[1])*256) + (uint16)(buf[0]))
        return intVal
      case 4:
        var intVal uint32
        intVal = (uint32)((uint32)((uint32)(buf[3])*16777216) + (uint32)((uint32)(buf[2])*65536) + (uint32)((uint32)(buf[1])*256) + (uint32)(buf[0]))
        return intVal
      default:
        fmt.Printf("Buffer length=%d is of an unknown size", len(buf))
        return nil
    }
}

func countSegments(path string) int {
    count := strings.Count(path, ".")
    return count + 1
}

func initContext(context *SearchContext_t, searchPath string, rootNode *def.Node_t, maxFound int, searchData []SearchData_t, anyDepth bool, leafNodesOnly bool, listSize int, noScopeList []string) {
	context.SearchPath = searchPath
	/*    if (anyDepth == true && context.SearchPath[len(context.SearchPath)-1] != '*') {
		  context.SearchPath = append(context.SearchPath, ".*")
		  } */
	context.RootNode = rootNode
	context.MaxFound = maxFound
	context.SearchData = searchData
	if (anyDepth == true) {
		context.MaxDepth = 100  //jan 2020 max tree depth = 8
	} else {
		context.MaxDepth = countSegments(context.SearchPath)
	}
	context.LeafNodesOnly = leafNodesOnly
	context.ListSize = listSize
 	context.NoScopeList = nil
	if (listSize > 0) {
  	    context.NoScopeList = noScopeList
	}
	context.MaxValidation = 0
	context.CurrentDepth = 0
	context.MatchPath = ""
	context.NumOfMatches = 0
	context.SpeculationIndex = -1
	for i := 0 ; i < 20 ; i++ {
		context.SpeculativeMatches[i] = 0
	}
}

func initContext_LNL(context *SearchContext_t, searchPath string, rootNode *def.Node_t, anyDepth bool, leafNodesOnly bool, listSize int, noScopeList []string) {
	context.SearchPath = searchPath
	context.RootNode = rootNode
	context.MaxFound = 0
	context.SearchData = nil
	context.ListFp = treeFp
	if (anyDepth == true) {
		context.MaxDepth = 100  //jan 2020 max tree depth = 8
	} else {
		context.MaxDepth = countSegments(context.SearchPath)
	}
	context.LeafNodesOnly = leafNodesOnly
	context.ListSize = listSize
 	context.NoScopeList = nil
	if (listSize > 0) {
  	    context.NoScopeList = noScopeList
	}
	context.MaxValidation = 0
	context.CurrentDepth = 0
	context.MatchPath = ""
	context.NumOfMatches = 0
	context.SpeculationIndex = -1
	for i := 0 ; i < 20 ; i++ {
		context.SpeculativeMatches[i] = 0
	}
}

func VSSsearchNodes(searchPath string, rootNode *def.Node_t, maxFound int, anyDepth bool, leafNodesOnly bool, listSize int, noScopeList []string, validation *int) ([]SearchData_t, int) {
	var context SearchContext_t
	searchData := make([]SearchData_t, maxFound)
	isGetLeafNodeList = false
	isGetUuidList = false

	initContext(&context, searchPath, rootNode, maxFound, searchData, anyDepth, leafNodesOnly, listSize, noScopeList)
	traverseNode(rootNode, &context)
	if (validation != nil) {
		*validation = context.MaxValidation
	}
	return searchData, context.NumOfMatches
}

func VSSGetLeafNodesList(rootNode *def.Node_t, listFname string) int {
    var context SearchContext_t
    isGetLeafNodeList = true
    var err error
    treeFp, err = os.OpenFile(listFname, os.O_RDWR|os.O_CREATE, 0755)
    if (err != nil) {
	fmt.Printf("Could not open %s for writing tree data\n", listFname)
	return 0
    }
    treeFp.Write([]byte("{\"leafpaths\":["))
    initContext_LNL(&context, "Vehicle.*", rootNode, true, true, 0, nil)  // anyDepth = true, leafNodesOnly = true
    traverseNode(rootNode, &context)
    treeFp.Write([]byte("]}"))
    treeFp.Close()

    return context.NumOfMatches
}

func VSSGetUuidList(rootNode *def.Node_t, listFname string) int {
    var context SearchContext_t
    isGetUuidList = true
    var err error
    treeFp, err = os.OpenFile(listFname, os.O_RDWR|os.O_CREATE, 0755)
    if (err != nil) {
	fmt.Printf("Could not open %s for writing tree data\n", listFname)
	return 0
    }
    treeFp.Write([]byte("{\"leafuuids\":["))
    initContext_LNL(&context, "Vehicle.*", rootNode, true, true, 0, nil)  // anyDepth = true, leafNodesOnly = true
    traverseNode(rootNode, &context)
    treeFp.Write([]byte("]}"))
    treeFp.Close()
    return context.NumOfMatches
}

func VSSReadTree(fname string) *def.Node_t {
    var err error
    treeFp, err = os.OpenFile(fname, os.O_RDONLY, 0644)
    if (err != nil) {
        fmt.Printf("Could not open %s for writing of tree. Error= %s\n", fname, err)
        return nil
    }
    initReadMetadata()
    var root *def.Node_t = traverseAndReadNode(nil)
    printReadMetadata()
    treeFp.Close()
    return root
}

func VSSWriteTree(fname string, root *def.Node_t) {
    var err error
    treeFp, err = os.OpenFile(fname, os.O_RDWR|os.O_CREATE, 0755)
    if (err != nil) {
	fmt.Printf("Could not open %s for writing tree data\n", fname)
	return
    }
    traverseAndWriteNode(root)
    treeFp.Close()
}

func VSSgetName(nodeHandle *def.Node_t) string {
	return nodeHandle.Name
}

func VSSgetParent(nodeHandle *def.Node_t) *def.Node_t {
	return nodeHandle.Parent
}

func VSSgetNumOfChildren(nodeHandle *def.Node_t) int {
	return (int)(nodeHandle.Children)
}

func VSSgetChild(nodeHandle *def.Node_t, childNo int) *def.Node_t {
	if (VSSgetNumOfChildren(nodeHandle) > childNo) {
		return nodeHandle.Child[childNo]
	}
	return nil
}

func VSSgetType(nodeHandle *def.Node_t) def.NodeTypes_t {
	return (def.NodeTypes_t)(nodeHandle.NodeType)
}

func VSSgetDatatype(nodeHandle *def.Node_t) def.NodeDatatypes_t{
	nodeType := VSSgetType(nodeHandle)
	if (nodeType != def.BRANCH) {
		return (def.NodeDatatypes_t)(nodeHandle.Datatype)
	}
	return 0
}

func VSSgetUUID(nodeHandle *def.Node_t) string {
	return nodeHandle.Uuid;
}

func VSSgetValidation(nodeHandle *def.Node_t) int {
	return (int)(nodeHandle.Validate)
}

func VSSgetDescr(nodeHandle *def.Node_t) string {
	return nodeHandle.Description
}

func VSSgetNumOfAllowedElements(nodeHandle *def.Node_t) int {
	nodeType := VSSgetType(nodeHandle);
	if (nodeType != def.BRANCH) {
		return (int)(nodeHandle.Allowed)
	}
	return 0
}

func VSSgetAllowedElement(nodeHandle *def.Node_t, index int) string {
	return nodeHandle.AllowedDef[index]
}

func VSSgetUnit(nodeHandle *def.Node_t) string {
	nodeType := VSSgetType(nodeHandle)
	if (nodeType != def.BRANCH) {
		return nodeHandle.Unit
	}
	return ""
}


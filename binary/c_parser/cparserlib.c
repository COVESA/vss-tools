/**
 * (C) 2020 Geotab Inc
 * (C) 2018 Volvo Cars
 *
 * All files and artifacts in this repository are licensed under the
 * provisions of the license provided by the LICENSE file in this repository.
 *
 * 
 * Parser library for a C binary format VSS tree.
 **/
 
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <stdbool.h>
#include <fcntl.h>
#include "cparserlib.h"

FILE* treeFp;

typedef struct readTreeMetadata_t {
    int currentDepth;
    int maxTreeDepth;
    int totalNodes;
} ReadTreeMetadata_t;
ReadTreeMetadata_t readTreeMetadata;

bool isGetLeafNodeList;
bool isGetUuidList;

int ret;  // to silence compiler...

typedef struct SearchContext_t {
	long rootNode;
	int maxFound;
	bool leafNodesOnly;
	int maxDepth;
	char* searchPath;
	path_t matchPath;
	int currentDepth;  // depth in tree from rootNode, and also depth (in segments) in searchPath
	int speculationIndex;  // inc/dec when pathsegment in focus is wildcard
	int speculativeMatches[20];  // inc when matching node is saved
	int maxValidation;
	int numOfMatches;
	searchData_t* searchData;
	int listSize;
	noScopeList_t* noScopeList;
	FILE* listFp;
} SearchContext_t;

void initReadMetadata() {
	readTreeMetadata.currentDepth = 0;
	readTreeMetadata.maxTreeDepth = 0;
	readTreeMetadata.totalNodes = 0;
}

void updateReadMetadata(bool increment) {
	if (increment == true) {
		readTreeMetadata.totalNodes++;
		readTreeMetadata.currentDepth++;
		if (readTreeMetadata.currentDepth > readTreeMetadata.maxTreeDepth)
			readTreeMetadata.maxTreeDepth++;
	} else {
		readTreeMetadata.currentDepth--;
	}
}

void printReadMetadata() {
	printf("\nTotal number of nodes in VSS tree = %d\n", readTreeMetadata.totalNodes);
	printf("Max depth of VSS tree = %d\n", readTreeMetadata.maxTreeDepth);
}

nodeTypes_t stringToNodeType(char* type) {
    if (strcmp(type, "sensor") == 0)
        return SENSOR;
    if (strcmp(type, "actuator") == 0)
        return ACTUATOR;
    if (strcmp(type, "attribute") == 0)
        return ATTRIBUTE;
    if (strcmp(type, "branch") == 0)
        return BRANCH;
    printf("Unknown type! |%s|\n", type);
    return UNKNOWN;
}

char* nodeTypeToString(nodeTypes_t type) {
    if (type == SENSOR)
        return "sensor";
    if (type == ACTUATOR)
        return "actuator";
    if (type == ATTRIBUTE)
        return "attribute";
    if (type == BRANCH)
        return "branch";
    printf("Unknown type! |%d|\n", type);
    return "";
}

nodeDatatypes_t stringToDataType(char* datatype) {
    if (strcmp(datatype, "int8") == 0)
        return INT8;
    if (strcmp(datatype, "uint8") == 0)
        return UINT8;
    if (strcmp(datatype, "int16") == 0)
        return INT16;
    if (strcmp(datatype, "uint16") == 0)
        return UINT16;
    if (strcmp(datatype, "int32") == 0)
        return INT32;
    if (strcmp(datatype, "uint32") == 0)
        return UINT32;
    if (strcmp(datatype, "double") == 0)
        return DOUBLE;
    if (strcmp(datatype, "float") == 0)
        return FLOAT;
    if (strcmp(datatype, "boolean") == 0)
        return BOOLEAN;
    if (strcmp(datatype, "string") == 0)
        return STRING;

    if (strcmp(datatype, "int8[]") == 0)
        return INT8ARRAY;
    if (strcmp(datatype, "uint8[]") == 0)
        return UINT8ARRAY;
    if (strcmp(datatype, "int16[]") == 0)
        return INT16ARRAY;
    if (strcmp(datatype, "uint16[]") == 0)
        return UINT16ARRAY;
    if (strcmp(datatype, "int32[]") == 0)
        return INT32ARRAY;
    if (strcmp(datatype, "uint32[]") == 0)
        return UINT32ARRAY;
    if (strcmp(datatype, "double[]") == 0)
        return DOUBLEARRAY;
    if (strcmp(datatype, "float[]") == 0)
        return FLOATARRAY;
    if (strcmp(datatype, "boolean[]") == 0)
        return BOOLEANARRAY;
    if (strcmp(datatype, "string[]") == 0)
        return STRINGARRAY;
    printf("Unknown datatype! |%s|\n", datatype);
    return UNKNOWN;
}

char* dataTypeToString(nodeDatatypes_t datatype) {
    if (datatype == INT8)
        return "int8";
    if (datatype == UINT8)
        return "uint8";
    if (datatype == INT16)
        return "int16";
    if (datatype == UINT16)
        return "uint16";
    if (datatype == INT32)
        return "int32";
    if (datatype == UINT32)
        return "uint32";
    if (datatype == DOUBLE)
        return "double";
    if (datatype == FLOAT)
        return "float";
    if (datatype == BOOLEAN)
        return "boolean";
    if (datatype == STRING)
        return "string";

    if (datatype == INT8ARRAY)
        return "int8[]";
    if (datatype == UINT8ARRAY)
        return "uint8[]";
    if (datatype == INT16ARRAY)
        return "int16[]";
    if (datatype == UINT16ARRAY)
        return "uint16[]";
    if (datatype == INT32ARRAY)
        return "int32[]";
    if (datatype == UINT32ARRAY)
        return "uint32[]";
    if (datatype == DOUBLEARRAY)
        return "double[]";
    if (datatype == FLOATARRAY)
        return "float[]";
    if (datatype == BOOLEANARRAY)
        return "boolean[]";
    if (datatype == STRINGARRAY)
        return "string[]";
    printf("Unknown datatype! |%d|\n", datatype);
    return "";
}

uint8_t validateToUint8(char* validate) {
    if (strcmp(validate, "write-only") == 0) {
        return 1;
    }
    if (strcmp(validate, "read-write") == 0) {
        return 2;
    }
    return 0;
}

char* validateToString(uint8_t validate) {
    if (validate == 1) {
        return "write-only";
    }
    if (validate == 2) {
        return "read-write";
    }
    return "";
}

void pushPathSegment(char* name, SearchContext_t* context) {
	if (context->currentDepth > 0) {
		strcat(context->matchPath, ".");
	}
	strcat(context->matchPath, name);
}

void popPathSegment(SearchContext_t* context) {
	char* delim = strrchr(context->matchPath, '.');
	if (delim == NULL) {
		context->matchPath[0] = 0;
	} else {
		*delim = 0;
	}
}

void incDepth(long thisNode, SearchContext_t* context) {
	//printf("incDepth()\n");
	pushPathSegment(VSSgetName(thisNode), context);
	context->currentDepth++;
}

char getPathSegmentBuf[100];  // modified by getPathSegment() only
char* getPathSegment(int offset, SearchContext_t* context) {
	char* frontDelimiter = &(context->searchPath[0]);
	char* endDelimiter;
	for (int i = 1 ; i < context->currentDepth + offset ; i++) {
		frontDelimiter = strchr(frontDelimiter+1, '.');
		if (frontDelimiter == NULL) {
			if (context->searchPath[strlen(context->searchPath)-1] == '*' && context->currentDepth < context->maxDepth) {
				return "*";
			} else {
				return "";
			}
		}
	}
	endDelimiter = strchr(frontDelimiter+1, '.');
	if (endDelimiter == NULL) {
		endDelimiter = &(context->searchPath[strlen(context->searchPath)]);
	}
	if (frontDelimiter[0] == '.') {
		frontDelimiter++;
	}
	strncpy(getPathSegmentBuf, frontDelimiter, (int)(endDelimiter-frontDelimiter));
	getPathSegmentBuf[(int)(endDelimiter-frontDelimiter)] = 0;
	return getPathSegmentBuf;
}

int countSegments(char* path) {
	int i;
	if (strlen(path) == 0) {
		return 0;
	}
	char* delim = strchr(path, '.');
	for (i = 0 ; i < 100 ; i++) {
		if (delim == NULL) {
			break;
		}
		delim = strchr(delim+1, '.');
	}
	return i+1;
}

bool compareNodeName(char* nodeName, char* pathName) {
	//printf("compareNodeName(): nodeName=%s, pathName=%s\n", nodeName, pathName);
	if (strcmp(nodeName, pathName) == 0 || strcmp(pathName, "*") == 0) {
		return true;
	}
	return false;
}

bool isEndOfScope(SearchContext_t* context) {
    int i;
    if (context->listSize == 0) {
        return false;
    }
    for (i = 0 ; i < context->listSize ; i++) {
        char* noScopePath = context->noScopeList[i].path;
        if (strcmp(context->matchPath, noScopePath) == 0) {
            return true;
        }
    }
    return false;
}

int saveMatchingNode(long thisNode, SearchContext_t* context, bool* done) {
	if (strcmp(getPathSegment(0, context), "*") == 0) {
		context->speculationIndex++;
	}
	if (VSSgetValidation(thisNode) > context->maxValidation) {
		context->maxValidation = VSSgetValidation(thisNode);  // TODO handle speculative setting
	}
	if (VSSgetType(thisNode) != BRANCH || context->leafNodesOnly == false) {
		if ( isGetLeafNodeList == false && isGetUuidList == false) {
			strcpy(context->searchData[context->numOfMatches].responsePaths, context->matchPath);
			context->searchData[context->numOfMatches].foundNodeHandles = thisNode;
		} else {
			if (isGetLeafNodeList == true) {
			    if (context->numOfMatches == 0) {
				    fwrite("\"", 1, 1, context->listFp);
			    } else {
				    fwrite(", \"", 3, 1, context->listFp);
			    }
			    fwrite(context->matchPath, strlen(context->matchPath), 1, context->listFp);
			    fwrite("\"", 1, 1, context->listFp);
			} else {
			    if (context->numOfMatches == 0) {
				    fwrite("{\"", 2, 1, context->listFp);
			    } else {
				    fwrite(", {\"", 4, 1, context->listFp);
			    }
			    fwrite(context->matchPath, strlen(context->matchPath), 1, context->listFp);
			    fwrite("\", \"", 4, 1, context->listFp);
			    char uuid[32+1];
			    strcpy(uuid, VSSgetUUID(thisNode));
			    fwrite(uuid, strlen(uuid), 1, context->listFp);
			    fwrite("\"}", 2, 1, context->listFp);
			}
		}
		context->numOfMatches++;
		if (context->speculationIndex >= 0) {
			context->speculativeMatches[context->speculationIndex]++;
		}
	}
	if (VSSgetNumOfChildren(thisNode) == 0 || context->currentDepth == context->maxDepth || isEndOfScope(context) == true) {
		*done = true;
	} else {
		*done = false;
	}
	if (context->speculationIndex >= 0 && ((VSSgetNumOfChildren(thisNode) == 0 && context->currentDepth >= countSegments(context->searchPath)) || context->currentDepth == context->maxDepth)) {
		return 1;
	}
	return 0;
}

/**
 * decDepth() shall reverse speculative wildcard matches that have failed, and also decrement currentDepth.
 **/
void decDepth(int speculationSucceded, SearchContext_t* context) {
	//printf("decDepth():speculationSucceded=%d\n", speculationSucceded);
	if (context->speculationIndex >= 0 && context->speculativeMatches[context->speculationIndex] > 0) {
		if (speculationSucceded == 0) {  // it failed so remove a saved match
			context->numOfMatches--;
			context->speculativeMatches[context->speculationIndex]--;
		}
	}
	if (strcmp(getPathSegment(0, context), "*") == 0) {
		context->speculationIndex--;
	}
	popPathSegment(context);
	context->currentDepth--;
}

int hexToInt(char hexDigit) {
    if (hexDigit <= '9') {
        return (int)(hexDigit - '0');
    }
    return (int)(hexDigit - 'A' + 10);
}

int countEnumElements(char* enumStr) {  // enum string has format "XXenum1XXenum2...XXenumx", where XX are hex values; X=[0-9,A-F]
    int enums = 0;
    for (int index = 0 ; index < strlen(enumStr) ; ) {
        char* hexLen = &(enumStr[index]);
        int enumLen = hexToInt(hexLen[0]) * 16 + hexToInt(hexLen[1]);
        index += enumLen + 2;
        enums++;
    }
    return enums;
}

char hexDigit(int value) {
    if (value < 10) {
        return (char)(value + '0');
    }
    return (char)(value - 10 + 'A');
}

char hexVal[3];  // only used by intToHex
char* intToHex(int intVal) {
    if (intVal > 255) {
        return NULL;
    }
    hexVal[0] = hexDigit(intVal/16);
    hexVal[1] = hexDigit(intVal%16);
    hexVal[2] = 0;
    return hexVal;
}

enum_t enumElement;  // only used by extractEnumElement
char* extractEnumElement(char* enumBuf, int elemIndex) {
    int enumstart;
    int enumLen;
    int bufIndex = 0;
    for (int enums = 0 ; enums <= elemIndex ; enums++) {
        char* hexLen = &(enumBuf[bufIndex]);
        enumLen = hexToInt(hexLen[0]) * 16 + hexToInt(hexLen[1]);
        enumstart = bufIndex + 2;
        bufIndex += enumLen + 2;
    }
    strncpy(enumElement, &(enumBuf[enumstart]), enumLen);
    enumElement[enumLen] = 0;
    return (char*)&enumElement;
}

void populateNode(node_t* thisNode) {
	ret = fread(&(thisNode->nameLen), sizeof(uint8_t), 1, treeFp);
	thisNode->name = (char*) malloc(sizeof(char)*(thisNode->nameLen+1));
	ret = fread(thisNode->name, sizeof(char)*thisNode->nameLen, 1, treeFp);
	thisNode->name[thisNode->nameLen] = '\0';

	uint8_t typeLen;
	ret = fread(&typeLen, sizeof(uint8_t), 1, treeFp);
	char* type = (char*) malloc(sizeof(char)*(typeLen+1));
	ret = fread(type, sizeof(char)*typeLen, 1, treeFp);
	type[typeLen] = '\0';
	thisNode->type = stringToNodeType(type);
printf("type: %s\n", type);
	free(type);

	ret = fread(&(thisNode->uuidLen), sizeof(uint8_t), 1, treeFp);
	thisNode->uuid = (char*) malloc(sizeof(char)*(thisNode->uuidLen+1));
	ret = fread(thisNode->uuid, sizeof(char)*thisNode->uuidLen, 1, treeFp);
	thisNode->uuid[thisNode->uuidLen] = '\0';
printf("uuid: %s\n", thisNode->uuid);

	ret = fread(&(thisNode->descrLen), sizeof(uint8_t), 1, treeFp);
	thisNode->description = (char*) malloc(sizeof(char)*(thisNode->descrLen+1));
	ret = fread(thisNode->description, sizeof(char)*thisNode->descrLen, 1, treeFp);
	thisNode->description[thisNode->descrLen] = '\0';
printf("description: %s\n", thisNode->description);

	uint8_t dataTypeLen;
	ret = fread(&dataTypeLen, sizeof(uint8_t), 1, treeFp);
	if (dataTypeLen > 0) {
		char* dataType = (char*) malloc(sizeof(char)*(dataTypeLen+1));
		ret = fread(dataType, sizeof(char)*dataTypeLen, 1, treeFp);
		dataType[dataTypeLen] = '\0';
		thisNode->datatype = (uint8_t)stringToDataType(dataType);
printf("datatype: %s\n", dataType);
		free(dataType);
	}

	ret = fread(&(thisNode->minLen), sizeof(uint8_t), 1, treeFp);
	if (thisNode->minLen > 0) {
		thisNode->min = (char*) malloc(sizeof(char)*(thisNode->minLen+1));
		ret = fread(thisNode->min, sizeof(char)*thisNode->minLen, 1, treeFp);
		thisNode->min[thisNode->minLen] = '\0';
printf("min: %s\n", thisNode->min);
	}

	ret = fread(&(thisNode->maxLen), sizeof(uint8_t), 1, treeFp);
	if (thisNode->maxLen > 0) {
		thisNode->max = (char*) malloc(sizeof(char)*(thisNode->maxLen+1));
		ret = fread(thisNode->max, sizeof(char)*thisNode->maxLen, 1, treeFp);
		thisNode->max[thisNode->maxLen] = '\0';
printf("max: %s\n", thisNode->max);
	}

	ret = fread(&(thisNode->unitLen), sizeof(uint8_t), 1, treeFp);
	if (thisNode->unitLen > 0) {
		thisNode->unit = (char*) malloc(sizeof(char)*(thisNode->unitLen+1));
		ret = fread(thisNode->unit, sizeof(char)*thisNode->unitLen, 1, treeFp);
		thisNode->unit[thisNode->unitLen] = '\0';
printf("unit: %s\n", thisNode->unit);
	}

	uint8_t enumLen;
	ret = fread(&enumLen, sizeof(uint8_t), 1, treeFp);
	if (enumLen > 0) {
		char* enumStr = (char*) malloc(sizeof(char)*(enumLen+1));
		ret = fread(enumStr, sizeof(char)*enumLen, 1, treeFp);
		enumStr[enumLen] = '\0';
 	        thisNode->enums = (uint8_t)countEnumElements(enumStr);
	        if (thisNode->enums > 0) {
		        thisNode->enumDef = (enum_t*) malloc(sizeof(enum_t)*(thisNode->enums));
                }
	        for (int i = 0 ; i < thisNode->enums ; i++) {
	            strcpy(thisNode->enumDef[i], extractEnumElement(enumStr, i));
	        }
	} else {
	    thisNode->enums = 0;
	}

	ret = fread(&(thisNode->defaultLen), sizeof(uint8_t), 1, treeFp);
	if (thisNode->defaultLen > 0) {
		thisNode->defaultEnum = (char*) malloc(sizeof(char)*(thisNode->defaultLen+1));
		ret = fread(thisNode->defaultEnum, sizeof(char)*thisNode->defaultLen, 1, treeFp);
		thisNode->defaultEnum[thisNode->defaultLen] = '\0';
printf("default: %s\n", thisNode->defaultEnum);
	}

	uint8_t validateLen;
	ret = fread(&validateLen, sizeof(uint8_t), 1, treeFp);
	if (validateLen > 0) {
		char validate[50];
		ret = fread(validate, sizeof(char)*validateLen, 1, treeFp);
		validate[validateLen] = '\0';
		thisNode->validate = validateToUint8(validate);
printf("validate: %s\n", validate);
	} else {
	    thisNode->validate = 0;
	}

	ret = fread(&(thisNode->children), sizeof(uint8_t), 1, treeFp);
printf("children: %d\n", thisNode->children);

	printf("populateNode: %s\n", thisNode->name);
}

int calculatEnumStrLen(uint8_t enums, enum_t* enumDef) {
    int strLen = 0;
    for (int i = 0 ; i < enums ; i++) {
        strLen += strlen((char*)(enumDef[i])) + 2;
    }
    return strLen;
}

void enumWrite(char* theEnum) {
    fwrite(intToHex(strlen(theEnum)), 2, 1, treeFp);
    fwrite(theEnum, sizeof(char)*strlen(theEnum), 1, treeFp);
}

void writeNode(struct node_t* node) {
	fwrite(&(node->nameLen), sizeof(uint8_t), 1, treeFp);
	fwrite(node->name, sizeof(char)*node->nameLen, 1, treeFp);

        char nodeType[50];
        strcpy(nodeType, nodeTypeToString(node->type));
        uint8_t nodeTypeLen = (uint8_t)strlen(nodeType);
	fwrite(&nodeTypeLen, sizeof(uint8_t), 1, treeFp);
        if (nodeTypeLen > 0) {
	    fwrite(nodeType, sizeof(char)*nodeTypeLen, 1, treeFp);
	}
printf("type: %s\n", nodeType);

	fwrite(&(node->uuidLen), sizeof(uint8_t), 1, treeFp);
	fwrite(node->uuid, sizeof(char)*node->uuidLen, 1, treeFp);
printf("uuid: %s\n", node->uuid);

	fwrite(&(node->descrLen), sizeof(uint8_t), 1, treeFp);
	fwrite(node->description, sizeof(char)*node->descrLen, 1, treeFp);
printf("uuid: %s\n", node->uuid);

        char dataType[50];
        strcpy(dataType, dataTypeToString(node->datatype));
        uint8_t dataTypeLen = (uint8_t)strlen(dataType);
	fwrite(&dataTypeLen, sizeof(uint8_t), 1, treeFp);
        if (dataTypeLen > 0) {
	    fwrite(dataType, sizeof(char)*dataTypeLen, 1, treeFp);
	}
printf("dataType: %s\n", dataType);

	fwrite(&(node->minLen), sizeof(uint8_t), 1, treeFp);
	if (node->minLen > 0) {
		fwrite(node->min, sizeof(char)*node->minLen, 1, treeFp);
	}

	fwrite(&(node->maxLen), sizeof(uint8_t), 1, treeFp);
	if (node->maxLen > 0) {
		fwrite(node->max, sizeof(char)*node->maxLen, 1, treeFp);
	}

	fwrite(&(node->unitLen), sizeof(uint8_t), 1, treeFp);
	if (node->unitLen > 0) {
		fwrite(node->unit, sizeof(char)*node->unitLen, 1, treeFp);
	}

        int enumStrLen = 0;
        if (node->enums > 0) {
            enumStrLen = calculatEnumStrLen(node->enums, node->enumDef);
            fwrite(&enumStrLen, sizeof(uint8_t), 1, treeFp);
printf("enumStrLen: %d\n", enumStrLen);
	    for (int i = 0 ; i < node->enums ; i++) {
	        enumWrite((char*)(node->enumDef[i]));
	    }
        } else {
            fwrite(&enumStrLen, sizeof(uint8_t), 1, treeFp);
        }

	fwrite(&(node->defaultLen), sizeof(uint8_t), 1, treeFp);
	if (node->defaultLen > 0) {
		fwrite(node->defaultEnum, sizeof(char)*node->defaultLen, 1, treeFp);
	}

	char* validate = validateToString(node->validate);
	int validateLen = strlen(validate);
	fwrite(&validateLen, sizeof(uint8_t), 1, treeFp);
	if (validateLen > 0) {
	    fwrite(validate, sizeof(char)*validateLen, 1, treeFp);
	}

	fwrite(&(node->children), sizeof(uint8_t), 1, treeFp);
printf("children: %d\n", node->children);

        printf("writeNode: %s\n", node->name);
}

struct node_t* traverseAndReadNode(struct node_t* parentNode) {
	node_t* thisNode = (node_t*) malloc(sizeof(node_t));
	updateReadMetadata(true);
	populateNode(thisNode);

	thisNode->parent = parentNode;

	if (thisNode->children > 0)
		thisNode->child = (node_t**) malloc(sizeof(node_t**)*thisNode->children);
	for (int childNo = 0 ; childNo < thisNode->children ; childNo++) {
		thisNode->child[childNo] = traverseAndReadNode(thisNode);
	}
	updateReadMetadata(false);
	return thisNode;
}

void traverseAndWriteNode(struct node_t* node) {
	printf("Node name = %s, type=%d\n", node->name, node->type);
	writeNode(node);
	for (int childNo = 0 ; childNo < node->children ; childNo++) {
		traverseAndWriteNode(node->child[childNo]);
	}
}

int traverseNode(long thisNode, SearchContext_t* context) {
	int speculationSucceded = 0;

	incDepth(thisNode, context);
	//printf("before compareNodeName():VSSnodename=%s, pathnodename=%s\n", VSSgetName(thisNode), getPathSegment(0, context));
	if (compareNodeName(VSSgetName(thisNode), getPathSegment(0, context)) == true) {
		bool done;
		speculationSucceded = saveMatchingNode(thisNode, context, &done);
		if (done == false) {
			int numOfChildren = VSSgetNumOfChildren(thisNode);
			char* childPathName = getPathSegment(1, context);
			for (int i = 0 ; i < numOfChildren ; i++) {
				if (compareNodeName(VSSgetName(VSSgetChild(thisNode, i)), childPathName) == true) {
					speculationSucceded += traverseNode(VSSgetChild(thisNode, i), context);
				}
			}
		}
	}
	decDepth(speculationSucceded, context);
	return speculationSucceded;
}

void initContext(SearchContext_t* context, char* searchPath, long rootNode, int maxFound, searchData_t* searchData, bool anyDepth, bool leafNodesOnly, int listSize, noScopeList_t* noScopeList) {
	context->searchPath = searchPath;
	/*    if (anyDepth == true && context->searchPath[strlen(context->searchPath)-1] != '*') {
		  strcat(context->searchPath, ".*");
		  } */
	context->rootNode = rootNode;
	context->maxFound = maxFound;
	context->searchData = searchData;
	if (anyDepth == true) {
		context->maxDepth = 100;  //jan 2020 max tree depth = 8
	} else {
		context->maxDepth = countSegments(context->searchPath);
	}
	context->leafNodesOnly = leafNodesOnly;
	context->listSize = listSize;
 	context->noScopeList = NULL;
	if (listSize > 0) {
  	    context->noScopeList = noScopeList;
	}
	context->maxValidation = 0;
	context->currentDepth = 0;
	context->matchPath[0] = 0;
	context->numOfMatches = 0;
	context->speculationIndex = -1;
	for (int i = 0 ; i < 20 ; i++) {
		context->speculativeMatches[i] = 0;
	}
}

//used for VSSGetLeafNodeList
void initContext_LNL(SearchContext_t* context, char* searchPath, long rootNode, FILE* listFp, bool anyDepth, bool leafNodesOnly, int listSize, noScopeList_t* noScopeList) {
	context->searchPath = searchPath;
	context->rootNode = rootNode;
	context->maxFound = 0;
	context->searchData = NULL;
	context->listFp = listFp;
	if (anyDepth == true) {
		context->maxDepth = 100;  //jan 2020 max tree depth = 8
	} else {
		context->maxDepth = countSegments(context->searchPath);
	}
	context->leafNodesOnly = leafNodesOnly;
	context->listSize = listSize;
 	context->noScopeList = NULL;
	if (listSize > 0) {
  	    context->noScopeList = noScopeList;
	}
	context->maxValidation = 0;
	context->currentDepth = 0;
	context->matchPath[0] = 0;
	context->numOfMatches = 0;
	context->speculationIndex = -1;
	for (int i = 0 ; i < 20 ; i++) {
		context->speculativeMatches[i] = 0;
	}
}

long VSSReadTree(char* filePath) {
	treeFp = fopen(filePath, "r");
	if (treeFp == NULL) {
		printf("Could not open file for reading tree data\n");
		return 0;
	}
	initReadMetadata();
	intptr_t root = (intptr_t)traverseAndReadNode(NULL);
	printReadMetadata();
	fclose(treeFp);
	return (long)root;
}

int VSSSearchNodes(char* searchPath, long rootNode, int maxFound, searchData_t* searchData, bool anyDepth,  bool leafNodesOnly, int listSize, noScopeList_t* noScopeList, int* validation) {
	//    intptr_t root = (intptr_t)rootNode;
	struct SearchContext_t searchContext;
	struct SearchContext_t* context = &searchContext;
	isGetLeafNodeList = false;
	isGetUuidList = false;

	initContext(context, searchPath, rootNode, maxFound, searchData, anyDepth, leafNodesOnly, listSize, noScopeList);
	traverseNode(rootNode, context);
	if (validation != NULL) {
		*validation = context->maxValidation;
	}
	return context->numOfMatches;
}

int VSSGetLeafNodesList(long rootNode, char* listFname) {
	struct SearchContext_t searchContext;
	struct SearchContext_t* context = &searchContext;
	isGetLeafNodeList = true;

	FILE* listFp = fopen(listFname, "w+");
	fwrite("{\"leafpaths\":[", 14, 1, listFp);
	initContext_LNL(context, "Vehicle.*", rootNode, listFp, true, true, 0, NULL);  // anyDepth = true, leafNodesOnly = true
	traverseNode(rootNode, context);
	fwrite("]}", 2, 1, listFp);
	fclose(listFp);

	return context->numOfMatches;
}

int VSSGetUuidList(long rootNode, char* listFname) {
	struct SearchContext_t searchContext;
	struct SearchContext_t* context = &searchContext;
	isGetUuidList = true;

	FILE* listFp = fopen(listFname, "w+");
	fwrite("{\"leafuuids\":[", 14, 1, listFp);
	initContext_LNL(context, "Vehicle.*", rootNode, listFp, true, true, 0, NULL);  // anyDepth = true, leafNodesOnly = true
	traverseNode(rootNode, context);
	//    int len = strlen(leafNodeList);
	//    leafNodeList[len-2] = '\0';
	fwrite("]}", 2, 1, listFp);
	fclose(listFp);

	return context->numOfMatches;
}

void VSSWriteTree(char* filePath, long rootHandle) {
	treeFp = fopen(filePath, "w");
	if (treeFp == NULL) {
		printf("Could not open file for writing tree data\n");
		return;
	}
	traverseAndWriteNode((struct node_t*)((intptr_t)rootHandle));
	fclose(treeFp);
}


// the intptr_t castings below are needed to avoid compiler warnings

long VSSgetParent(long nodeHandle) {
	return (long)((intptr_t)((node_t*)((intptr_t)nodeHandle))->parent);
}

int VSSgetNumOfChildren(long nodeHandle) {
	return (int)((intptr_t)((node_t*)((intptr_t)nodeHandle))->children);
}

long VSSgetChild(long nodeHandle, int childNo) {
	if (VSSgetNumOfChildren(nodeHandle) > childNo)
		return (long)((intptr_t)((node_t*)((intptr_t)nodeHandle))->child[childNo]);
	return 0;
}

nodeTypes_t VSSgetType(long nodeHandle) {
	return ((node_t*)((intptr_t)nodeHandle))->type;
}

nodeDatatypes_t VSSgetDatatype(long nodeHandle) {
	nodeTypes_t type = VSSgetType(nodeHandle);
	if (type != BRANCH)
		return ((node_t*)((intptr_t)nodeHandle))->datatype;
	return -1;
}

char* VSSgetName(long nodeHandle) {
	return ((node_t*)((intptr_t)nodeHandle))->name;
}

char* VSSgetUUID(long nodeHandle) {
	return ((node_t*)((intptr_t)nodeHandle))->uuid;
}

int VSSgetValidation(long nodeHandle) {
	return (int)((intptr_t)((node_t*)((intptr_t)nodeHandle))->validate);
}

char* VSSgetDescr(long nodeHandle) {
	return ((node_t*)((intptr_t)nodeHandle))->description;
}

int VSSgetNumOfEnumElements(long nodeHandle) {
	nodeTypes_t type = VSSgetType(nodeHandle);
	if (type != BRANCH)
		return (int)(((node_t*)((intptr_t)nodeHandle))->enums);
	return 0;
}

char* VSSgetEnumElement(long nodeHandle, int index) {
	return (char*)(((node_t*)((intptr_t)nodeHandle))->enumDef[index]);
}

char* VSSgetUnit(long nodeHandle) {
	nodeTypes_t type = VSSgetType(nodeHandle);
	if (type != BRANCH)
		return ((node_t*)((intptr_t)nodeHandle))->unit;
	return NULL;
}


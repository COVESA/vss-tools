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
#include <assert.h>
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

// Access control values: none=0, write-only=1. read-write=2, consent +=10
// matrix preserving inherited value with read-write having priority over write-only and consent over no consent
uint8_t validationMatrix[5][5] = {{0,1,2,11,12}, {1,1,2,11,12}, {2,2,2,12,12}, {11,11,12,11,12}, {12,12,12,12,12}};

uint8_t getMaxValidation(uint8_t newValidation, uint8_t currentMaxValidation) {
	return validationMatrix[translateToMatrixIndex(newValidation)][translateToMatrixIndex(currentMaxValidation)];
}

uint8_t translateToMatrixIndex(uint8_t index) {
	switch (index) {
		case 0: return 0;
		case 1: return 1;
		case 2: return 2;
		case 11: return 3;
		case 12: return 4;
	}
	return 0;
}

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
    if (strcmp(type, "branch") == 0)
        return BRANCH;
    if (strcmp(type, "sensor") == 0)
        return SENSOR;
    if (strcmp(type, "actuator") == 0)
        return ACTUATOR;
    if (strcmp(type, "attribute") == 0)
        return ATTRIBUTE;
    if (strcmp(type, "struct") == 0)
        return STRUCT;
    if (strcmp(type, "property") == 0)
        return PROPERTY;
    printf("Unknown type! |%s|\n", type);
    return UNKNOWN;
}

char* nodeTypeToString(nodeTypes_t type) {
    if (type == BRANCH)
        return "branch";
    if (type == SENSOR)
        return "sensor";
    if (type == ACTUATOR)
        return "actuator";
    if (type == ATTRIBUTE)
        return "attribute";
    if (type == STRUCT)
        return "struct";
    if (type == PROPERTY)
        return "property";
    printf("Unknown type! |%d|\n", type);
    return "";
}

uint8_t validateToUint8(char* validate) {
    uint8_t validation = 0;
    if (strstr(validate, "write-only") != NULL) {
        validation = 1;
    } else if (strstr(validate, "read-write") != NULL) {
        validation = 2;
    }
    if (strstr(validate, "consent") != NULL) {
        validation += 10;
    }
    return validation;
}

void validateToString(uint8_t validate, char *validation) {
    if (validate%10 == 1) {
        strcpy(validation, "write-only");
    } else if (validate%10 == 2) {
        strcpy(validation, "read-write");
    }
    if (validate/10 == 1) {
        strcat(validation, "+consent");
    }
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
	context->maxValidation = getMaxValidation(VSSgetValidation(thisNode), context->maxValidation);
	if ((VSSgetType(thisNode) != BRANCH && VSSgetType(thisNode) != STRUCT) || context->leafNodesOnly == false) {
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

int countAllowedElements(char* allowedStr) {  // allowed string has format "XXallowed1XXallowed2...XXallowedx", where XX are hex values; X=[0-9,A-F]
    int allowed = 0;
    for (int index = 0 ; index < (int)strlen(allowedStr) ; ) {
        assert(index >= 0);
        char* hexLen = &(allowedStr[index]);
        int allowedLen = hexToInt(hexLen[0]) * 16 + hexToInt(hexLen[1]);
        index += allowedLen + 2;
        allowed++;
    }
    return allowed;
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

allowed_t allowedElement;  // only used by extractAllowedElement
char* extractAllowedElement(char* allowedBuf, int elemIndex) {
    int allowedstart;
    int allowedLen;
    int bufIndex = 0;
    for (int alloweds = 0 ; alloweds <= elemIndex ; alloweds++) {
        char* hexLen = &(allowedBuf[bufIndex]);
        allowedLen = hexToInt(hexLen[0]) * 16 + hexToInt(hexLen[1]);
        allowedstart = bufIndex + 2;
        bufIndex += allowedLen + 2;
    }
    strncpy(allowedElement, &(allowedBuf[allowedstart]), allowedLen);
    allowedElement[allowedLen] = 0;
    return (char*)&allowedElement;
}

void populateNode(node_t* thisNode) {
    uint8_t nameLen;
    ret = fread(&nameLen, sizeof(uint8_t), 1, treeFp);
    thisNode->nameLen = nameLen;
	thisNode->name = (char*) malloc(sizeof(char)*(thisNode->nameLen+1));
	ret = fread(thisNode->name, sizeof(char)*thisNode->nameLen, 1, treeFp);
	thisNode->name[thisNode->nameLen] = '\0';

	uint8_t typeLen;
	ret = fread(&typeLen, sizeof(uint8_t), 1, treeFp);
	char* type = (char*) malloc(sizeof(char)*(typeLen+1));
	ret = fread(type, sizeof(char)*typeLen, 1, treeFp);
	type[typeLen] = '\0';
	thisNode->type = stringToNodeType(type);
	free(type);

	ret = fread(&(thisNode->uuidLen), sizeof(uint8_t), 1, treeFp);
	thisNode->uuid = (char*) malloc(sizeof(char)*(thisNode->uuidLen+1));
	ret = fread(thisNode->uuid, sizeof(char)*thisNode->uuidLen, 1, treeFp);
	thisNode->uuid[thisNode->uuidLen] = '\0';

	ret = fread(&(thisNode->descrLen), sizeof(uint16_t), 1, treeFp);
	thisNode->description = (char*) malloc(sizeof(char)*(thisNode->descrLen+1));
	ret = fread(thisNode->description, sizeof(char)*thisNode->descrLen, 1, treeFp);
	thisNode->description[thisNode->descrLen] = '\0';

	ret = fread(&(thisNode->datatypeLen), sizeof(uint8_t), 1, treeFp);
	if (thisNode->datatypeLen > 0) {
		thisNode->datatype = (char*) malloc(sizeof(char)*(thisNode->datatypeLen+1));
		ret = fread(thisNode->datatype, sizeof(char)*thisNode->datatypeLen, 1, treeFp);
		thisNode->datatype[thisNode->datatypeLen] = '\0';
	}

	ret = fread(&(thisNode->minLen), sizeof(uint8_t), 1, treeFp);
	if (thisNode->minLen > 0) {
		thisNode->min = (char*) malloc(sizeof(char)*(thisNode->minLen+1));
		ret = fread(thisNode->min, sizeof(char)*thisNode->minLen, 1, treeFp);
		thisNode->min[thisNode->minLen] = '\0';
	}

	ret = fread(&(thisNode->maxLen), sizeof(uint8_t), 1, treeFp);
	if (thisNode->maxLen > 0) {
		thisNode->max = (char*) malloc(sizeof(char)*(thisNode->maxLen+1));
		ret = fread(thisNode->max, sizeof(char)*thisNode->maxLen, 1, treeFp);
		thisNode->max[thisNode->maxLen] = '\0';
	}

	ret = fread(&(thisNode->unitLen), sizeof(uint8_t), 1, treeFp);
	if (thisNode->unitLen > 0) {
		thisNode->unit = (char*) malloc(sizeof(char)*(thisNode->unitLen+1));
		ret = fread(thisNode->unit, sizeof(char)*thisNode->unitLen, 1, treeFp);
		thisNode->unit[thisNode->unitLen] = '\0';
	}

	uint16_t allowedLen;
	ret = fread(&allowedLen, sizeof(uint16_t), 1, treeFp);
	if (allowedLen > 0) {
		char* allowedStr = (char*) malloc(sizeof(char)*(allowedLen+1));
		ret = fread(allowedStr, sizeof(char)*allowedLen, 1, treeFp);
		allowedStr[allowedLen] = '\0';
 	        thisNode->allowed = (uint8_t)countAllowedElements(allowedStr);
	        if (thisNode->allowed > 0) {
		        thisNode->allowedDef = (allowed_t*) malloc(sizeof(allowed_t)*(thisNode->allowed));
                }
	        for (int i = 0 ; i < thisNode->allowed ; i++) {
	            strcpy(thisNode->allowedDef[i], extractAllowedElement(allowedStr, i));
	        }
	} else {
	    thisNode->allowed = 0;
	}

	ret = fread(&(thisNode->defaultLen), sizeof(uint8_t), 1, treeFp);
	if (thisNode->defaultLen > 0) {
		thisNode->defaultAllowed = (char*) malloc(sizeof(char)*(thisNode->defaultLen+1));
		ret = fread(thisNode->defaultAllowed, sizeof(char)*thisNode->defaultLen, 1, treeFp);
		thisNode->defaultAllowed[thisNode->defaultLen] = '\0';
	}

	uint8_t validateLen;
	ret = fread(&validateLen, sizeof(uint8_t), 1, treeFp);
	if (validateLen > 0) {
		char validate[50];
		ret = fread(validate, sizeof(char)*validateLen, 1, treeFp);
		validate[validateLen] = '\0';
		thisNode->validate = validateToUint8(validate);
	} else {
	    thisNode->validate = 0;
	}

	ret = fread(&(thisNode->children), sizeof(uint8_t), 1, treeFp);

//	printf("populateNode: %s\n", thisNode->name);
}

int calculatAllowedStrLen(uint8_t alloweds, allowed_t* allowedDef) {
    int strLen = 0;
    for (int i = 0 ; i < alloweds ; i++) {
        strLen += strlen((char*)(allowedDef[i])) + 2;
    }
    return strLen;
}

void allowedWrite(char* theAllowed) {
    fwrite(intToHex(strlen(theAllowed)), 2, 1, treeFp);
    fwrite(theAllowed, sizeof(char)*strlen(theAllowed), 1, treeFp);
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

	fwrite(&(node->uuidLen), sizeof(uint8_t), 1, treeFp);
	fwrite(node->uuid, sizeof(char)*node->uuidLen, 1, treeFp);

	fwrite(&(node->descrLen), sizeof(uint16_t), 1, treeFp);
	fwrite(node->description, sizeof(char)*node->descrLen, 1, treeFp);

	fwrite(&(node->datatypeLen), sizeof(uint8_t), 1, treeFp);
        if (node->datatypeLen > 0) {
	    fwrite(node->datatype, sizeof(char)*node->datatypeLen, 1, treeFp);
	}

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

        int allowedStrLen = 0;
        if (node->allowed > 0) {
            allowedStrLen = calculatAllowedStrLen(node->allowed, node->allowedDef);
            fwrite(&allowedStrLen, sizeof(uint16_t), 1, treeFp);
	    for (int i = 0 ; i < node->allowed ; i++) {
	        allowedWrite((char*)(node->allowedDef[i]));
	    }
        } else {
            fwrite(&allowedStrLen, sizeof(uint16_t), 1, treeFp);
        }

	fwrite(&(node->defaultLen), sizeof(uint8_t), 1, treeFp);
	if (node->defaultLen > 0) {
		fwrite(node->defaultAllowed, sizeof(char)*node->defaultLen, 1, treeFp);
	}

	char validate[10+1+7+1];  // access control + consent data
	validateToString(node->validate, (char*)&validate);
	int validateLen = strlen(validate);
	fwrite(&validateLen, sizeof(uint8_t), 1, treeFp);
	if (validateLen > 0) {
	    fwrite(validate, sizeof(char)*validateLen, 1, treeFp);
	}

	fwrite(&(node->children), sizeof(uint8_t), 1, treeFp);

//        printf("writeNode: %s\n", node->name);
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
	writeNode(node);
	for (int childNo = 0 ; childNo < node->children ; childNo++) {
		traverseAndWriteNode(node->child[childNo]);
	}
}

int traverseNode(long thisNode, SearchContext_t* context) {
	int speculationSucceded = 0;

	incDepth(thisNode, context);
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

long VSSReadTree(const char* filePath) {
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

int VSSGetLeafNodesList(long rootNode, const char* listFname) {
	struct SearchContext_t searchContext;
	struct SearchContext_t* context = &searchContext;
	isGetLeafNodeList = true;

	FILE* listFp = fopen(listFname, "w+");
	fwrite("{\"leafpaths\":[", 14, 1, listFp);
	initContext_LNL(context, "*", rootNode, listFp, true, true, 0, NULL);  // anyDepth = true, leafNodesOnly = true
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
	initContext_LNL(context, "*", rootNode, listFp, true, true, 0, NULL);  // anyDepth = true, leafNodesOnly = true
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

char* VSSgetDatatype(long nodeHandle) {
	nodeTypes_t type = VSSgetType(nodeHandle);
	if (type != BRANCH && type != STRUCT)
		return ((node_t*)((intptr_t)nodeHandle))->datatype;
	return NULL;
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

int VSSgetNumOfAllowedElements(long nodeHandle) {
	nodeTypes_t type = VSSgetType(nodeHandle);
	if (type != BRANCH && type != STRUCT)
		return (int)(((node_t*)((intptr_t)nodeHandle))->allowed);
	return 0;
}

char* VSSgetAllowedElement(long nodeHandle, int index) {
	return (char*)(((node_t*)((intptr_t)nodeHandle))->allowedDef[index]);
}

char* VSSgetDefault(long nodeHandle) {
    node_t* node = ((node_t*)((intptr_t)nodeHandle));
    return node->defaultAllowed;
}

char* VSSgetUnit(long nodeHandle) {
	nodeTypes_t type = VSSgetType(nodeHandle);
	if (type != BRANCH && type != STRUCT)
		return ((node_t*)((intptr_t)nodeHandle))->unit;
	return NULL;
}

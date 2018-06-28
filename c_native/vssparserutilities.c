/**
* (C) 2018 Volvo Cars
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
* 
* Parser utilities for a native format VSS tree.
**/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <stdbool.h>
#include "nativeCnodeDef.h"
#include "vssparserutilities.h"

struct node_t* traverseAndReadNode(struct node_t* parentPtr) {
    int staticChunk = NODESTATICSIZE;
    struct node_t* buf = (struct node_t*)malloc(staticChunk);
    if (buf == NULL) {
        printf("traverseAndReadNode: 1st malloc failed\n");
        return NULL;
    }
if (parentPtr != NULL) {
  printf("parent node name = %s, ", parentPtr->name);
}
    int read = fread(buf, staticChunk, 1, treeFp);
    struct node_t* node = (struct node_t*)malloc(sizeof(node_t)-(MAXCHILDREN-buf->children)*sizeof(node_t*));
    if (node == NULL) {
        printf("traverseAndReadNode: 2nd malloc failed\n");
        free(buf);
        return NULL;
    }
    strcpy(node->name, buf->name);
    node->type = buf->type;
    node->children = buf->children; 
    node->descrLen = buf->descrLen; 
    node->numOfEnumElements = buf->numOfEnumElements; 
    node->id = buf->id; 
    node->min = buf->min; 
    node->max = buf->max; 
    strcpy(node->unit, buf->unit);
    free(buf);
    node->parent = parentPtr;
    node->description = (char*) malloc(sizeof(char)*node->descrLen);
    if (node->description == NULL) {
        printf("traverseAndReadNode: 3rd malloc failed\n");
        free(node);
        return NULL;
    }
    fread(node->description, sizeof(char)*node->descrLen, 1, treeFp);
printf("Description = %s\n", node->description);
    if (node->numOfEnumElements > 0) {
        node->enumeration = (enum_t*) malloc(sizeof(enum_t)*node->numOfEnumElements);
        if (node->enumeration == NULL) {
            printf("traverseAndReadNode: 4th malloc failed\n");
            free(node->description);
            free(node);
            return NULL;
        }
        fread(node->enumeration, sizeof(enum_t)*node->numOfEnumElements, 1, treeFp);
for (int i = 0 ; i < node->numOfEnumElements ; i++)
  printf("Enum[%d]=%s\n", i, (char*)node->enumeration[i]);
    }
    int childNo = 0;
    while(childNo < node->children) {
        node->child[childNo++] = traverseAndReadNode(node);
    }
    return node;
}

struct node_t* VSSReadTree() {
    return traverseAndReadNode(NULL);
}

char tmpNodeName[MAXNAMELEN];
char* getNodeName(int stepNo, char* path) {
printf("getNodeName:step=%d\n", stepNo);
    tmpNodeName[0] = '\0';
    char* ptr = strchr(path, '.');
    if (ptr != NULL) {
        if (stepNo == 0) {
            strncpy(tmpNodeName, path, (int)(ptr-path));
            tmpNodeName[(int)(ptr-path)] = '\0';
            return tmpNodeName;
        }
        char* front;
        for (int i = 0 ; i < stepNo ; i++) {
            front = ptr+1;
            ptr = strchr(ptr+1, '.');
            if (ptr == NULL) {
                if (i == stepNo-1) {
                    ptr =&path[strlen(path)];
                    break;
                } else
                    return tmpNodeName;
            }
        }
        strncpy(tmpNodeName, front, (int)(ptr-front));
        tmpNodeName[(int)(ptr-front)] = '\0';
    } else {
        if (stepNo == 0)
            strcpy(tmpNodeName, path);
    }
printf("getNodeName:step=%d, name=%s\n", stepNo, tmpNodeName);
    return tmpNodeName;
}

int getNumOfPathSteps(char* path) {
    int numofelements = 0;
    char* ptr= strchr(path, '.');
    if (ptr == NULL) {
        return 1;
    } else {
        numofelements++;
        while (ptr != NULL) {
            numofelements++;
            ptr= strchr(ptr+1, '.');
        }
printf("getNumOfPathSteps=%d\n", numofelements);
        return numofelements;
    }
}

void copySteps(char* newPath, char* oldPath, int stepNo) {
    char* ptr = strchr(oldPath, '.');
    for (int i = 0 ; i < stepNo-1 ; i++) {
        if (ptr != NULL)
            ptr = strchr(ptr+1, '.');
    }
    if (ptr != NULL) {
        strncpy(newPath, oldPath, (int)(ptr - oldPath));
        newPath[(int)(ptr - oldPath)] = '\0';
    }
}

struct node_t* stepToNextNode(struct node_t* ptr, int stepNo, char* searchPath, int maxFound, int* foundResponses, path_t* responsePaths, struct node_t** foundNodePtrs) {
printf("ptr->name=%s, stepNo=%d, responsePaths[%d]=%s\n",ptr->name, stepNo, *foundResponses, responsePaths[*foundResponses]);
    if (*foundResponses >= maxFound-1)
        return NULL; // found buffers full
    char pathNodeName[MAXNAMELEN];
    strcpy(pathNodeName, getNodeName(stepNo, searchPath));
    if (stepNo == getNumOfPathSteps(searchPath)-1) { // at leave node, so save ptr and return success
        foundNodePtrs[*foundResponses] = ptr;
        return ptr;
    }
    strcpy(pathNodeName, getNodeName(stepNo+1, searchPath));  // get name of next step in path
    if (strcmp(pathNodeName, "*") != 0) {  // try to match with one of the children
        for (int i = 0 ; i < ptr->children ; i++) {
printf("ptr->child[i]->name=%s\n", ptr->child[i]->name);
            if (strcmp(pathNodeName, ptr->child[i]->name) == 0) {
                if (strlen(responsePaths[*foundResponses]) > 0) // always true?
                    strcat(responsePaths[*foundResponses], ".");
                strcat(responsePaths[*foundResponses], pathNodeName);
                return stepToNextNode(ptr->child[i], stepNo+1, searchPath, maxFound, foundResponses, responsePaths,  foundNodePtrs);
            }
        }
        return NULL;
    } else {  // wildcard, try to match with all children
        struct node_t* responsePtr = NULL;
        for (int i = 0 ; (i < ptr->children) && (*foundResponses < maxFound) ; i++) {
printf("Wildcard:ptr->child[%d]->name=%s\n", i, ptr->child[i]->name);
            strcat(responsePaths[*foundResponses], ".");
            strcat(responsePaths[*foundResponses], ptr->child[i]->name);
            struct node_t* ptr2 = stepToNextNode(ptr->child[i], stepNo+1, searchPath, maxFound, foundResponses, responsePaths,  foundNodePtrs);
            if (ptr2 == NULL) {
                copySteps(responsePaths[*foundResponses], responsePaths[*foundResponses], stepNo+1);
            } else {
                if (i < ptr->children && foundNodePtrs[*foundResponses] != NULL) {
                    (*foundResponses)++;
                    copySteps(responsePaths[*foundResponses], responsePaths[*foundResponses-1], stepNo+1);
                } else
                    copySteps(responsePaths[*foundResponses], responsePaths[*foundResponses], stepNo+1);
                responsePtr = ptr2;
            }
        }
        return responsePtr;
    }
}


int VSSGetNodes(char* searchPath, struct node_t* rootNode, int maxFound, path_t* responsePaths, struct node_t** foundNodePtrs) {
    struct node_t* ptr = rootNode;
    int stepNo = 0;
    int foundResponses = 0;
    /* 
     * This is a workaround to the fact that with X multiple wildcards, 
     * there are "(X-1)*numberofrealresults" bogus results added.
     * It seems stepToNextNode returns non-NULL when it should not in those cases?
     * See NULL check in wildcard code in stepToNextNode. 
     */
    for (int i = 0 ; i < maxFound ; i++)
        foundNodePtrs[i] = NULL;

    strcpy(responsePaths[0], ptr->name); // root node name needs to be written initially
    stepToNextNode(ptr, stepNo, searchPath, maxFound, &foundResponses, responsePaths, foundNodePtrs);

    if (strchr(searchPath, '*') == NULL)
        foundResponses++;

    return foundResponses;
}



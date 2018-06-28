/**
* (C) 2018 Volvo Cars
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
* 
* Write native format to file.
**/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <stdbool.h>
#include <limits.h>
#include "nativeCnodeDef.h"

FILE* treeFp;

int stringToTypeDef(char* type) {
    if (strcmp(type, "Int8") == 0)
        return INT8;
    if (strcmp(type, "UInt8") == 0)
        return UINT8;
    if (strcmp(type, "Int16") == 0)
        return INT16;
    if (strcmp(type, "UInt16") == 0)
        return UINT16;
    if (strcmp(type, "Int32") == 0)
        return INT32;
    if (strcmp(type, "UInt32") == 0)
        return UINT32;
    if (strcmp(type, "Double") == 0)
        return DOUBLE;
    if (strcmp(type, "Float") == 0)
        return FLOAT;
    if (strcmp(type, "Boolean") == 0)
        return BOOLEAN;
    if (strcmp(type, "String") == 0)
        return STRING;
    if (strcmp(type, "branch") == 0)
        return BRANCH;
    printf("Unknown type! |%s|\n", type);
    return -1;
}

int countEnumElements(char* enums) {
    int delimiters = 0;
    for (int i = 0 ; i < strlen(enums) ; i++) {
        if (enums[i] == '/')
            delimiters++;
    }
    if (delimiters == 0)
        return 0;
    return delimiters-1;
}

char* getEnumElement(char* enums, int index, char* buf) {
    char* enumstart = enums;
    char* enumend  = NULL;
    for (int i = 0 ; i < index+1 ; i++) {
        enumend = strchr(enumstart+1, '/');
        if (enumend == NULL)
            return NULL;
        if (i < index)
            enumstart = enumend;
    }
    strncpy(buf, enumstart+1, (int)(enumend-(enumstart+1)));
    buf[(int)(enumend-(enumstart+1))] = '\0';
    return buf;
}

void writeNodeData(char* name, char* id, char* type, int children, char* descr, char* min, char* max, char* unit, char* enums) {
printf("Name=%s, ID=%s, Type=%s, children=%d, Descr=%s, min=%s, max=%s Unit=%s, Enums=%s\n", name, id, type, children, descr, min, max, unit, enums);
    node_t node;
    strcpy(node.name, name);
    if (strlen(id) == 0)
        node.id = -1;
    else
        node.id = atoi(id);
    node.type = stringToTypeDef(type);
    node.children = children;
    if (strlen(min) == 0)
        node.min = INT_MAX;
    else
        node.min = atoi(min);
    if (strlen(max) == 0)
        node.max = INT_MIN;
    else
        node.max = atoi(max);
    strcpy(node.unit, unit);
    node.descrLen = strlen(descr);
    node.numOfEnumElements = countEnumElements(enums);
printf("Num of enum elements=%d\n", node.numOfEnumElements);
    node.enumeration = malloc(sizeof(enum_t)*node.numOfEnumElements);
    if (node.enumeration == NULL) {
        printf("traverseAndSaveNode:malloc failed\n");
        return;
    }
    char enumElementBuf[MAXENUMELEMENTLEN];
    for (int i = 0 ; i < node.numOfEnumElements ; i++) {
        strcpy((char*)(node.enumeration[i]), getEnumElement(enums, i, enumElementBuf));
    }
    fwrite(&node, NODESTATICSIZE, 1, treeFp);
    fwrite(descr, sizeof(char)*node.descrLen, 1, treeFp);
    fwrite(node.enumeration, sizeof(enum_t)*node.numOfEnumElements, 1, treeFp);
}

void createNativeCnode(char* name, char* id, char* type, int children, char* descr, char* min, char* max, char* unit, char* enums) {
    treeFp = fopen("../vss_rel_1.0.cnative", "a");
    if (treeFp == NULL) {
        printf("Could not open file for writing of tree.\n");
        return;
    }
    writeNodeData(name, id, type, children, descr, min, max, unit, enums);
    fclose(treeFp);
}



/**
* (C) 2020 Geotab Inc
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
#include "vssparserutilities.h"  //nativeCnodeDef.h uses it. Maybe some methods could be used also?
#include "nativeCnodeDef.h"

FILE* treeFp;
int objectType = -1;  // declared at this level to propagate type from rbranch context to its element children contexts

int stringToTypeDef(char* type) {
    if (strcmp(type, "sensor") == 0)
        return SENSOR;
    if (strcmp(type, "actuator") == 0)
        return ACTUATOR;
    if (strcmp(type, "attribute") == 0)
        return ATTRIBUTE;
    if (strcmp(type, "branch") == 0)
        return BRANCH;
    printf("Unknown type! |%s|\n", type);
    return -1;
}

int stringToDataTypeDef(char* datatype) {
    if (strcmp(datatype, "Int8") == 0 || strcmp(datatype, "int8") == 0)
        return INT8;
    if (strcmp(datatype, "Uint8") == 0 || strcmp(datatype, "uint8") == 0 || strcmp(datatype, "UInt8") == 0)
        return UINT8;
    if (strcmp(datatype, "Int16") == 0 || strcmp(datatype, "int16") == 0)
        return INT16;
    if (strcmp(datatype, "Uint16") == 0 || strcmp(datatype, "uint16") == 0 || strcmp(datatype, "UInt16") == 0)
        return UINT16;
    if (strcmp(datatype, "Int32") == 0 || strcmp(datatype, "int32") == 0)
        return INT32;
    if (strcmp(datatype, "Uint32") == 0 || strcmp(datatype, "uint32") == 0 || strcmp(datatype, "UInt32") == 0)
        return UINT32;
    if (strcmp(datatype, "Double") == 0 || strcmp(datatype, "double") == 0)
        return DOUBLE;
    if (strcmp(datatype, "Float") == 0 || strcmp(datatype, "float") == 0)
        return FLOAT;
    if (strcmp(datatype, "Bool") == 0 || strcmp(datatype, "bool") == 0 || strcmp(datatype, "boolean") == 0)
        return BOOLEAN;
    if (strcmp(datatype, "String") == 0 || strcmp(datatype, "string") == 0)
        return STRING;

    if (strcmp(datatype, "Int8[]") == 0 || strcmp(datatype, "int8[]") == 0)
        return INT8ARRAY;
    if (strcmp(datatype, "Uint8[]") == 0 || strcmp(datatype, "uint8[]") == 0 || strcmp(datatype, "UInt8[]") == 0)
        return UINT8ARRAY;
    if (strcmp(datatype, "Int16[]") == 0 || strcmp(datatype, "int16[]") == 0)
        return INT16ARRAY;
    if (strcmp(datatype, "Uint16[]") == 0 || strcmp(datatype, "uint16[]") == 0 || strcmp(datatype, "UInt16[]") == 0)
        return UINT16ARRAY;
    if (strcmp(datatype, "Int32[]") == 0 || strcmp(datatype, "int32[]") == 0)
        return INT32ARRAY;
    if (strcmp(datatype, "Uint32[]") == 0 || strcmp(datatype, "uint32[]") == 0 || strcmp(datatype, "UInt32[]") == 0)
        return UINT32ARRAY;
    if (strcmp(datatype, "Double[]") == 0 || strcmp(datatype, "double[]") == 0)
        return DOUBLEARRAY;
    if (strcmp(datatype, "Float[]") == 0 || strcmp(datatype, "float[]") == 0)
        return FLOATARRAY;
    if (strcmp(datatype, "Bool[]") == 0 || strcmp(datatype, "bool[]") == 0 || strcmp(datatype, "boolean[]") == 0)
        return BOOLEANARRAY;
    if (strcmp(datatype, "String[]") == 0 || strcmp(datatype, "string[]") == 0)
        return STRINGARRAY;
    printf("Unknown datatype! |%s|\n", datatype);
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

char* extractEnumElement(char* enums, int index, char* buf) {
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

void writeCommonPart(char* name, char* type, char* uuid, int validate, char* descr, int children) {
    common_node_data_t commonData;

    commonData.nameLen  = strlen(name);
    commonData.type = stringToTypeDef(type);
    commonData.uuidLen  = strlen(uuid);
    commonData.validate  = validate;
    commonData.descrLen = strlen(descr);
    commonData.children = children;

    fwrite(&commonData, sizeof(common_node_data_t), 1, treeFp);
    fwrite(name, sizeof(char)*commonData.nameLen, 1, treeFp);
    fwrite(uuid, sizeof(char)*commonData.uuidLen, 1, treeFp);
    fwrite(descr, sizeof(char)*commonData.descrLen, 1, treeFp);
}

void writeNodeData(char* name, char* type, char* uuid, int validate, char* descr, int children, char* datatype, char* min, char* max, char* unit, char* enums, char* function) {
//printf("Name=%s, Type=%s, uuid=%s, validate=%d, children=%d, Descr=%s, datatype=%s, min=%s, max=%s Unit=%s, Enums=%s, function=%s\n", name, type, uuid, validate, children, descr, datatype, min, max, unit, enums, function);
    writeCommonPart(name, type, uuid, validate, descr, children);
    int dtype = -1;
    if (strlen(datatype) != 0)
        dtype = stringToDataTypeDef(datatype);
    fwrite(&dtype, sizeof(int), 1, treeFp);
    int nodeMin = INT_MAX;
    if (strlen(min) != 0)
        nodeMin = atoi(min);
    fwrite(&nodeMin, sizeof(int), 1, treeFp);
    int nodeMax = INT_MIN;
    if (strlen(max) != 0)
        nodeMax = atoi(max);
    fwrite(&nodeMax, sizeof(int), 1, treeFp);
    int unitLen = (int)strlen(unit);
    fwrite(&unitLen, sizeof(int), 1, treeFp);
    if (unitLen > 0)
        fwrite(unit, sizeof(char)*unitLen, 1, treeFp);
    int numOfEnumElements = countEnumElements(enums);
//printf("Num of enum elements=%d\n", numOfEnumElements);
    fwrite(&numOfEnumElements, sizeof(int), 1, treeFp);
    if (numOfEnumElements > 0) {
        enum_t* enumeration;
        enumeration = malloc(sizeof(enum_t)*numOfEnumElements);
        if (enumeration == NULL) {
            printf("traverseAndSaveNode:malloc failed\n");
            return;
        }
        char enumElementBuf[MAXENUMELEMENTLEN];
        for (int i = 0 ; i < numOfEnumElements ; i++) {
            strncpy((char*)(enumeration[i]), extractEnumElement(enums, i, enumElementBuf), MAXENUMELEMENTLEN);
            enumeration[i][MAXENUMELEMENTLEN-1] = '\0';
        }
        fwrite(enumeration, sizeof(enum_t)*numOfEnumElements, 1, treeFp);
        free(enumeration);
    }
    int functionLen = (int)strlen(function);
    fwrite(&functionLen, sizeof(int), 1, treeFp);
    if (functionLen > 0)
        fwrite(function, sizeof(char)*functionLen, 1, treeFp);
}

void createNativeCnode(char*fname, char* name, char* type, char* uuid, int validate, char* descr, int children, char* datatype, char* min, char* max, char* unit, char* enums, char* function) {
    treeFp = fopen(fname, "a");
    if (treeFp == NULL) {
        printf("Could not open file for writing of tree.\n");
        return;
    }
    writeNodeData(name, type, uuid, validate, descr, children, datatype, min, max, unit, enums, function);
    fclose(treeFp);
}


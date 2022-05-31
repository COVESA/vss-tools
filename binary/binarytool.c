/**
* (C) 2020 Geotab Inc
* (C) 2018 Volvo Cars
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
*
* Write VSS tree node in binary format to file.
**/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <stdbool.h>
#include <limits.h>

FILE* treeFp;

void writeNodeData(char* name, char* type, char* uuid, char* descr, char* datatype, char* min, char* max, char* unit, char* allowed, char* defaultAllowed, char* validate, int children) {
//printf("Name=%s, Type=%s, uuid=%s, validate=%s, children=%d, Descr=%s, datatype=%s, min=%s, max=%s Unit=%s, Allowed=%s\n", name, type, uuid, validate, children, descr, datatype, min, max, unit, allowed);
    uint8_t nameLen  = (uint8_t)strlen(name);
    uint8_t typeLen = (uint8_t)strlen(type);
    uint8_t uuidLen  = (uint8_t)strlen(uuid);
    uint16_t descrLen = (uint16_t)strlen(descr);
    uint8_t datatypeLen = (uint8_t)strlen(datatype);
    uint8_t minLen = (uint8_t)strlen(min);
    uint8_t maxLen = (uint8_t)strlen(max);
    uint8_t unitLen = (uint8_t)strlen(unit);
    uint16_t allowedLen = (uint16_t)strlen(allowed);
    uint8_t defaultAllowedLen = (uint8_t)strlen(defaultAllowed);
    uint8_t validateLen = (uint8_t)strlen(validate);
    
    fwrite(&nameLen, sizeof(uint8_t), 1, treeFp);
    fwrite(name, sizeof(char)*nameLen, 1, treeFp);
    fwrite(&typeLen, sizeof(uint8_t), 1, treeFp);
    fwrite(type, sizeof(char)*typeLen, 1, treeFp);
    fwrite(&uuidLen, sizeof(uint8_t), 1, treeFp);
    fwrite(uuid, sizeof(char)*uuidLen, 1, treeFp);
    fwrite(&descrLen, sizeof(uint16_t), 1, treeFp);
    fwrite(descr, sizeof(char)*descrLen, 1, treeFp);
    fwrite(&datatypeLen, sizeof(uint8_t), 1, treeFp);
    if (datatypeLen > 0) {
        fwrite(datatype, sizeof(char)*datatypeLen, 1, treeFp);
    }
    fwrite(&minLen, sizeof(uint8_t), 1, treeFp);
    if (minLen > 0) {
        fwrite(min, sizeof(char)*minLen, 1, treeFp);
    }
    fwrite(&maxLen, sizeof(uint8_t), 1, treeFp);
    if (maxLen > 0) {
        fwrite(max, sizeof(char)*maxLen, 1, treeFp);
    }
    fwrite(&unitLen, sizeof(uint8_t), 1, treeFp);
    if (unitLen > 0) {
        fwrite(unit, sizeof(char)*unitLen, 1, treeFp);
    }
    fwrite(&allowedLen, sizeof(uint16_t), 1, treeFp);
    if (allowedLen > 0) {
        fwrite(allowed, sizeof(char)*allowedLen, 1, treeFp);
    }
    fwrite(&defaultAllowedLen, sizeof(uint8_t), 1, treeFp);
    if (defaultAllowedLen > 0) {
        fwrite(defaultAllowed, sizeof(char)*defaultAllowedLen, 1, treeFp);
    }
    fwrite(&validateLen, sizeof(uint8_t), 1, treeFp);
    if (validateLen > 0) {
        fwrite(validate, sizeof(char)*validateLen, 1, treeFp);
    }
    fwrite(&children, sizeof(uint8_t), 1, treeFp);
}

void createBinaryCnode(char*fname, char* name, char* type, char* uuid, char* descr, char* datatype, char* min, char* max, char* unit, char* allowed, char* defaultAllowed, char* validate, int children) {
    treeFp = fopen(fname, "a");
    if (treeFp == NULL) {
        printf("Could not open file=%s for writing of tree.\n", fname);
        return;
    }
    writeNodeData(name, type, uuid, descr, datatype, min, max, unit, allowed, defaultAllowed, validate, children);
    fclose(treeFp);
}



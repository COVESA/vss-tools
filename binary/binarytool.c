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

void writeNodeData(char* name, char* type, char* uuid, char* descr, char* datatype, char* min, char* max, char* unit, char* enums, char* defaultEnum, char* validate, int children) {
printf("Name=%s, Type=%s, uuid=%s, validate=%s, children=%d, Descr=%s, datatype=%s, min=%s, max=%s Unit=%s, Enums=%s\n", name, type, uuid, validate, children, descr, datatype, min, max, unit, enums);
    uint8_t nameLen  = (uint8_t)strlen(name);
    uint8_t typeLen = (uint8_t)strlen(type);
    uint8_t uuidLen  = (uint8_t)strlen(uuid);
    uint8_t descrLen = (uint8_t)strlen(descr);
    uint8_t datatypeLen = (uint8_t)strlen(datatype);
    uint8_t minLen = (uint8_t)strlen(min);
    uint8_t maxLen = (uint8_t)strlen(max);
    uint8_t unitLen = (uint8_t)strlen(unit);
    uint8_t enumsLen = (uint8_t)strlen(enums);
    uint8_t defaultEnumLen = (uint8_t)strlen(defaultEnum);
    uint8_t validateLen = (uint8_t)strlen(validate);
    
    if (descrLen > 255) {
        printf("Description length=%d, is larger than 255.\n", descrLen);
        descrLen = 255;
    }
    if (enumsLen > 255) {
        printf("Enums length=%d, is larger than 255.\n", enumsLen);
        enumsLen = 255;
    }

    fwrite(&nameLen, sizeof(uint8_t), 1, treeFp);
    fwrite(name, sizeof(char)*nameLen, 1, treeFp);
    fwrite(&typeLen, sizeof(uint8_t), 1, treeFp);
    fwrite(type, sizeof(char)*typeLen, 1, treeFp);
    fwrite(&uuidLen, sizeof(uint8_t), 1, treeFp);
    fwrite(uuid, sizeof(char)*uuidLen, 1, treeFp);
    fwrite(&descrLen, sizeof(uint8_t), 1, treeFp);
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
    fwrite(&enumsLen, sizeof(uint8_t), 1, treeFp);
    if (enumsLen > 0) {
        fwrite(enums, sizeof(char)*enumsLen, 1, treeFp);
    }
    fwrite(&defaultEnumLen, sizeof(uint8_t), 1, treeFp);
    if (defaultEnumLen > 0) {
        fwrite(defaultEnum, sizeof(char)*defaultEnumLen, 1, treeFp);
    }
    fwrite(&validateLen, sizeof(uint8_t), 1, treeFp);
    if (validateLen > 0) {
        fwrite(validate, sizeof(char)*enumsLen, 1, treeFp);
    }
    fwrite(&children, sizeof(uint8_t), 1, treeFp);
}

void createBinaryCnode(char*fname, char* name, char* type, char* uuid, char* descr, char* datatype, char* min, char* max, char* unit, char* enums, char* defaultEnum, char* validate, int children) {
    treeFp = fopen(fname, "a");
    if (treeFp == NULL) {
        printf("Could not open file for writing of tree.\n");
        return;
    }
    writeNodeData(name, type, uuid, descr, datatype, min, max, unit, enums, defaultEnum, validate, children);
    fclose(treeFp);
}



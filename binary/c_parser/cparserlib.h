/**
* (C) 2020 Geotab Inc
* (C) 2018 Volvo Cars
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
*
* Parser library for a  C binary format VSS tree.
**/

#define UNKNOWN 0
typedef enum {SENSOR=1, ACTUATOR, ATTRIBUTE, BRANCH } nodeTypes_t;
typedef enum {INT8=1, UINT8, INT16, UINT16, INT32, UINT32, DOUBLE, FLOAT, BOOLEAN, STRING, INT8ARRAY, UINT8ARRAY, INT16ARRAY, UINT16ARRAY, INT32ARRAY, UINT32ARRAY, DOUBLEARRAY, FLOATARRAY, BOOLEANARRAY, STRINGARRAY} nodeDatatypes_t;

#define MAXALLOWEDELEMENTLEN 64
typedef char allowed_t[MAXALLOWEDELEMENTLEN];

typedef struct node_t {
    uint16_t nameLen;
    char* name;
    nodeTypes_t type;
    uint8_t uuidLen;
    char* uuid;
    uint16_t descrLen;
    char* description;
    nodeDatatypes_t datatype;
    uint8_t maxLen;
    char* max;
    uint8_t minLen;
    char* min;
    uint8_t unitLen;
    char* unit;
    uint8_t allowed;
    allowed_t *allowedDef;
    uint8_t defaultLen;
    char* defaultAllowed;
    uint8_t validate;
    uint8_t children;
    struct node_t* parent;
    struct node_t** child;
} node_t;

#define MAXCHARSPATH 512
typedef char path_t[MAXCHARSPATH];

#define MAXFOUNDNODES 1500   //may need to be revised when tree size grows
typedef struct searchData_t {
    path_t responsePaths;
    long foundNodeHandles;
} searchData_t;

typedef struct noScopeList_t {
    path_t path;
} noScopeList_t;

long VSSReadTree(char* filePath);
void VSSWriteTree(char* filePath, long rootHandle);
int VSSSearchNodes(char* searchPath, long rootNode, int maxFound, searchData_t* searchData, bool anyDepth,  bool leafNodesOnly, int listSize, noScopeList_t* noScopeList, int* validation);
int VSSGetLeafNodesList(long rootNode, char* listFname);
int VSSGetUuidList(long rootNode, char* listFname);

long VSSgetParent(long nodeHandle);
long VSSgetChild(long nodeHandle, int childNo);
int VSSgetNumOfChildren(long nodeHandle);
nodeTypes_t VSSgetType(long nodeHandle);
nodeDatatypes_t VSSgetDatatype(long nodeHandle);
char* VSSgetName(long nodeHandle);
char* VSSgetUUID(long nodeHandle);
int VSSgetValidation(long nodeHandle);
char* VSSgetDescr(long nodeHandle);
int VSSgetNumOfAllowedElements(long nodeHandle);
char* VSSgetAllowedElement(long nodeHandle, int index);
char* VSSgetUnit(long nodeHandle);


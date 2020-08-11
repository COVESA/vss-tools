/**
* (C) 2020 Geotab Inc
* (C) 2018 Volvo Cars
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
*
* Parser utilities for a native format VSS tree.
**/

#define MAXENUMELEMENTLEN 20
typedef enum { INT8, UINT8, INT16, UINT16, INT32, UINT32, DOUBLE, FLOAT, BOOLEAN, STRING, SENSOR, ACTUATOR, STREAM, ATTRIBUTE, BRANCH } nodeTypes_t;
typedef char enum_t[MAXENUMELEMENTLEN];

#define ELEMENT_STRING_MAXLEN 125
typedef char elementRef_t[ELEMENT_STRING_MAXLEN];

#define MAXCHARSPATH 512
typedef char path_t[MAXCHARSPATH];
#define MAXFOUNDNODES 1500

typedef struct searchData_t {
    path_t responsePaths;
    long foundNodeHandles;
} searchData_t;

long VSSReadTree(char* filePath);
void VSSWriteTree(char* filePath, int rootHandle);

long getParent(long nodeHandle);
long getChild(long nodeHandle, int childNo);
int getNumOfChildren(long nodeHandle);
nodeTypes_t VSSgetType(long nodeHandle);
nodeTypes_t VSSgetDatatype(long nodeHandle);
char* getName(long nodeHandle);
char* VSSgetUUID(long nodeHandle);
int getValidation(long nodeHandle);
char* getDescr(long nodeHandle);
int getNumOfEnumElements(long nodeHandle);
char* getEnumElement(long nodeHandle, int index);
char* getUnit(long nodeHandle);
char* getFunction(long nodeHandle);

int VSSSearchNodes(char* searchPath, long rootNode, int maxFound, searchData_t* searchData, bool anyDepth, bool leafNodesOnly, int* validation);
int VSSGetLeafNodesList(long rootNode, char* listFname);
int VSSGetUuidList(long rootNode, char* listFname);


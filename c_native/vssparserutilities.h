/**
* (C) 2018 Volvo Cars
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
*
* Parser utilities for a native format VSS tree.
**/

#define MAXENUMELEMENTLEN 20
typedef enum { INT8, UINT8, INT16, UINT16, INT32, UINT32, DOUBLE, FLOAT, BOOLEAN, STRING, SENSOR, ACTUATOR, STREAM, ATTRIBUTE, BRANCH, RBRANCH, ELEMENT } nodeTypes_t;
typedef char enum_t[MAXENUMELEMENTLEN];

typedef enum { MEDIACOLLECTION, MEDIAITEM } objectTypes_t;
#define ELEMENT_STRING_MAXLEN 125
typedef char elementRef_t[ELEMENT_STRING_MAXLEN];

#define MAXCHARSPATH 512
typedef char path_t[MAXCHARSPATH];
#define MAXFOUNDNODES 150

int VSSReadTree(char* filePath);
void VSSWriteTree(char* filePath, int rootHandle);

int getParent(int nodeHandle);
int getChild(int nodeHandle, int childNo);
int getNumOfChildren(int nodeHandle);
nodeTypes_t getType(int nodeHandle);
nodeTypes_t getDatatype(int nodeHandle);
char* getName(int nodeHandle);
char* getDescr(int nodeHandle);
int getNumOfEnumElements(int nodeHandle);
char* getEnumElement(int nodeHandle, int index);
char* getUnit(int nodeHandle);
char* getFunction(int nodeHandle);
int getResource(int nodeHandle);
int getObjectType(int resourceHandle);
int getMediaCollectionNumOfItems(int resourceHandle);
char* getMediaCollectionItemRef(int resourceHandle, int i);

int VSSSearchNodes(char* searchPath, int rootNode, int maxFound, path_t* responsePaths, int* foundNodeHandles);

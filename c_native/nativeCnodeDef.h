/**
* (C) 2018 Volvo Cars
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
* 
* Definition of native format.
**/

#define MAXNAMELEN 28
#define MAXPROPNAMELEN 30
#define MAXPROPDESCRLEN 50
#define MAXPROPFORMATLEN 15
#define MAXPROPUNITLEN 15
#define MAXPROPVALUELEN 50


/**
* There are three different node structures defined below: 
 * node_t, rbranch_node_t, element_node_t
 * They have a common part, and a unique part.
 * The common part consists of:
 *   int nameLen;
 *   char* name;
 *   nodeTypes_t type;
 *   int descrLen;
 *   char* description;
 *   int children;
 *   struct node_t* parent;
 *   struct node_t** child;
 * This common part must be identical in all three structures, and be positioned before any unique parts.
 * When reading/writing the tree from/to file, the common part is read/written first, 
 * then from analysis of its data, further reading/writing is done.
 * The size of the common part is defined by sizeof(common_node_data_t), which contains the parameters above, except the pointers.
 * Data pointed to by the name and description pointers, with size defined by the associated length parameters, 
 * is read/written following the common part.
**/

typedef struct node_t {
    int nameLen;
    char* name;
    nodeTypes_t type;
    int descrLen;
    char* description;
    int children;
    struct node_t* parent;
    struct node_t** child;
    int max;
    int min;
    int unitLen;
    char* unit;
    int numOfEnumElements;
    enum_t* enumeration;
    int functionLen;
    char* function;
} node_t;

typedef struct {
    char propName[MAXNAMELEN];
    char propDescr[MAXPROPDESCRLEN];
    nodeTypes_t propType;  // branch, rbranch, resource not allowed
    char propFormat[MAXPROPFORMATLEN];
    char propUnit[MAXPROPUNITLEN];
    char propValue[MAXPROPVALUELEN];
} propertyDefinition_t;

typedef struct element_node_t { // only fixed part defined here
    int nameLen;
    char* name;
    nodeTypes_t type;   // must be element
    int descrLen;
    char* description;
    int children;      // must be zero
    struct node_t* parent;
    struct node_t** child;  // not used, so set to NULL
    void* uniqueObject;
} element_node_t;

typedef struct rbranch_node_t {
    int nameLen;
    char* name;
    nodeTypes_t type;   // must be rbranch
    int descrLen;
    char* description;
    int children;
    struct node_t* parent;
    struct element_node_t** child;
    int childTypeLen;
    char* childType;
    int numOfProperties;
    propertyDefinition_t* propertyDefinition;
} rbranch_node_t;

typedef struct {
    int nameLen;
    nodeTypes_t type;
    int descrLen;
    int children;
} common_node_data_t;

typedef struct {
    int objectType;
} resourceObject_t;  // generic type only used for generic access to the object type

typedef struct {
    int objectType;  // this must be first element in any object struct declaration
    char id[ELEMENT_STRING_MAXLEN];
    char name[ELEMENT_STRING_MAXLEN];
    char uri[ELEMENT_STRING_MAXLEN];
    int numOfItems;
    elementRef_t* items;
} mediaCollectionObject_t;

typedef struct {
    int objectType;  // this must be first element in any object struct declaration
    char id[ELEMENT_STRING_MAXLEN];
    char name[ELEMENT_STRING_MAXLEN];
    char uri[ELEMENT_STRING_MAXLEN];
} mediaItemObject_t;



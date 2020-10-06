/**
* (C) 2020 Geotab Inc
* (C) 2018 Volvo Cars
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
* 
* Native C data structures representing the YAML key-value pairs defined in VSS.
**/

#define MAXNAMELEN 28
#define MAXPROPNAMELEN 30
#define MAXPROPDESCRLEN 50
#define MAXPROPFORMATLEN 15
#define MAXPROPUNITLEN 15
#define MAXPROPVALUELEN 50


typedef struct node_t {
    int nameLen;
    char* name;
    nodeTypes_t type;
    int uuidLen;
    char* uuid;
    int validate;
    int descrLen;
    char* description;
    int children;
    struct node_t* parent;
    struct node_t** child;
    nodeDatatypes_t datatype;
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
    int nameLen;
    nodeTypes_t type;
    int uuidLen;
    int validate;
    int descrLen;
    int children;
} common_node_data_t;


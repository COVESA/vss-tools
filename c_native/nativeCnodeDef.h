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
#define MAXUNITLEN 11
#define MAXENUMELEMENTS 16
#define MAXENUMELEMENTLEN 13
#define MAXCHILDREN 75


typedef enum { INT8, UINT8, INT16, UINT16, INT32, UINT32, DOUBLE, FLOAT, BOOLEAN, STRING, BRANCH } nodeTypes_t;

typedef char enum_t[MAXENUMELEMENTLEN];

typedef struct node_t {
    char name[MAXNAMELEN];
    nodeTypes_t type;
    int children;
    int descrLen;
    int max;
    int min;
    char unit[MAXUNITLEN];
    int numOfEnumElements;
    int id;
    char* description;
    enum_t* enumeration;
    struct node_t* parent;
    struct node_t* child[MAXCHILDREN];
} node_t;

#define NODESTATICSIZE (sizeof(char)*(MAXNAMELEN+MAXUNITLEN)+sizeof(nodeTypes_t)+6*sizeof(int))

/**
* (C) 2018 Volvo Cars
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
* 
* Parser utilities for a native format VSS tree.
**/

#define MAXCHARSPATH 512

typedef char path_t[MAXCHARSPATH];

FILE* treeFp;

struct node_t* VSSReadTree();

int VSSGetNodes(char* searchPath, struct node_t* rootNode, int maxFound, path_t* responsePaths, struct node_t** foundNodePtrs);



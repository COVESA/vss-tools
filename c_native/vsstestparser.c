/**
* (C) 2018 Volvo Cars
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
* 
* Example of parser for a native format VSS tree.
**/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <stdbool.h>
#include "nativeCnodeDef.h"
#include "vssparserutilities.h"

#define MAXTREEDEPTH 8
#define MAXFOUNDNODES 150


struct node_t* parserNode;
struct node_t* rootNode;

char* getTypeName(nodeTypes_t type) {
    switch (type) { 
        case BRANCH:
                return "BRANCH";
        case BOOLEAN:
                return "BOOLEAN";
        case UINT8:
                return "UINT8";
        case INT8:
                return "INT8";
        case UINT16:
                return "UINT16";
        case INT16:
                return "INT16";
        case UINT32:
                return "UINT32";
        case INT32:
                return "INT32";
        case DOUBLE:
            return "DOUBLE";
        case FLOAT:
            return "FLOAT";
        case STRING:
            return "STRING";
        default:
            printf("getTypeName: unknown type\n");
            return "unknown";
        break;
    } // switch
}

int main(void) {

    treeFp = fopen("../../vss_rel_1.0.cnative", "r");
    if (treeFp == NULL) {
        printf("Could not open file for reading tree data\n");
        return 0;
    }
    rootNode = VSSReadTree();
    fclose(treeFp);


    char traverse[10];
    printf("\nTo traverse the tree: 'u'(p)/'d'(own)/'l'(eft)/'r'(ight)/g(et)/h(elp), or any other to quit\n");
    parserNode = rootNode;
    int currentChild = 0;
    while (true) {
        printf("\n'u'/'d'/'l'/'r'/'g'/'h', or any other to quit: ");
        scanf("%s", traverse);
        switch (traverse[0]) {
            case 'u':  //up
                if (parserNode->parent != NULL) {
                    parserNode = parserNode->parent;
                    currentChild = 0;
                }
            break;
            case 'd':  //down
                if (parserNode->child[currentChild] != NULL) {
                    parserNode = parserNode->child[currentChild];
                    currentChild = 0;
                }
            break;
            case 'l':  //left
                if (currentChild > 0)
                    currentChild--;
            break;
            case 'r':  //right
                if (currentChild < parserNode->children -1)
                    currentChild++;
            break;
            case 'g':  //get nodes matching path
            {
                char searchPath[MAXCHARSPATH];
                printf("\nPath to resource(s): ");
                scanf("%s", searchPath);
                path_t responsePaths[MAXFOUNDNODES];
                struct node_t* foundNodePtrs[MAXFOUNDNODES];
                int foundResponses = VSSGetNodes(searchPath, rootNode, MAXFOUNDNODES, responsePaths, foundNodePtrs);
                printf("\nNumber of elements found=%d\n", foundResponses);
                for (int i = 0 ; i < foundResponses ; i++) {
                    printf("Found node name=%s\n", foundNodePtrs[i]->name);
                    printf("Found path=%s\n", responsePaths[i]);
                }
            }
            break;
            case 'h':  //help
                printf("\nTo traverse the tree, 'u'(p)p/'d'(own)/'l'(eft)/'r'(ight)/g(et)/h(elp), or any other to quit\n");
            break;
            default:
                return 0;
        }  //switch
        printf("\nNode name = %s, Node type = %s, Node children = %d\nNode description = %s\n", parserNode->name, getTypeName(parserNode->type), parserNode->children, parserNode->description);
        if (parserNode->children > 0)
            printf("Node child[%d]=%s\n", currentChild, parserNode->child[currentChild]->name);
    } //while


    return 0;
} // main



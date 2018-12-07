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
#include "vssparserutilities.h"

int currentNode;
int rootNode;
char vspecfile[] = "../../vss_rel_1.0.cnative";

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
        case RBRANCH:
            return "RBRANCH";
        case ELEMENT:
            return "ELEMENT";
        default:
            printf("getTypeName: unknown type\n");
            return "unknown";
        break;
    } // switch
}

void showNodeData(int currentNode, int currentChild) {
        printf("\nNode name = %s, Node type = %s, Node children = %d\nNode description = %s\n", getName(currentNode), getTypeName(getType(currentNode)), getNumOfChildren(currentNode), getDescr(currentNode));
        if (getNumOfChildren(currentNode) > 0)
            printf("Node child[%d]=%s\n", currentChild, getName(getChild(currentNode, currentChild)));
        for (int i = 0 ; i < getNumOfEnumElements(currentNode) ; i++)
            printf("Enum[%d]=%s\n", i, getEnumElement(currentNode, i));
        nodeTypes_t dtype = getDatatype(currentNode);
        if (dtype != -1)
            printf("Datatype = %d\n", dtype);
        char* tmp = getUnit(currentNode);
        if (tmp != NULL)
            printf("Unit = %s\n", tmp);
        tmp = getFunction(currentNode);
        if (tmp != NULL)
            printf("Function = %s\n", tmp);
        if (getType(currentNode) == ELEMENT) {
            // as all objectdefinitions start with objectType, this is ok. But only for reading the objectType
            uint32_t resourceHandle = getResource(currentNode); 
            printf("Node object type=%d\n", getObjectType(resourceHandle));
            if (getObjectType(resourceHandle) == MEDIACOLLECTION) {
                for (int i = 0 ; i < getMediaCollectionNumOfItems(resourceHandle) ; i++) {
                    printf("Items ref[%d]=%s\n", i, getMediaCollectionItemRef(resourceHandle, i));
                }
            }
        }
}

int main(void) {

    rootNode = VSSReadTree(vspecfile);

    char traverse[10];
    printf("\nTo traverse the tree: 'u'(p)/'d'(own)/'l'(eft)/'r'(ight)/g(et)/w(rite)/h(elp), or any other to quit\n");
    currentNode = rootNode;
    int currentChild = 0;
    while (true) {
        printf("\n'u'/'d'/'l'/'r'/'g'/'w'/'h', or any other to quit: ");
        scanf("%s", traverse);
        switch (traverse[0]) {
            case 'u':  //up
                if (getParent(currentNode) != 0) {
                    currentNode = getParent(currentNode);
                    currentChild = 0;
                }
                showNodeData(currentNode, currentChild);
            break;
            case 'd':  //down
                if (getChild(currentNode, currentChild) != 0) {
                    currentNode = getChild(currentNode, currentChild);
                    currentChild = 0;
                }
                showNodeData(currentNode, currentChild);
            break;
            case 'l':  //left
                if (currentChild > 0) {
                    currentChild--;
                }
                showNodeData(currentNode, currentChild);
            break;
            case 'r':  //right
                if (currentChild < getNumOfChildren(currentNode)-1) {
                    currentChild++;
                }
                showNodeData(currentNode, currentChild);
            break;
            case 'g':  //get nodes matching path
            {
                char searchPath[MAXCHARSPATH];
                printf("\nPath to resource(s): ");
                scanf("%s", searchPath);
                path_t responsePaths[MAXFOUNDNODES];
                int foundNodes[MAXFOUNDNODES];
                int foundResponses = VSSSearchNodes(searchPath, rootNode, MAXFOUNDNODES, responsePaths, foundNodes);
                printf("\nNumber of elements found=%d\n", foundResponses);
                for (int i = 0 ; i < foundResponses ; i++) {
                    printf("Found node type=%s\n", getTypeName(getType(foundNodes[i])));
                    printf("Found path=%s\n", responsePaths[i]);
                }
            }
            break;
            case 'h':  //help
                printf("\nTo traverse the tree, 'u'(p)p/'d'(own)/'l'(eft)/'r'(ight)/g(et)/h(elp), or any other to quit\n");
            break;
            case 'w':  //write to file
                VSSWriteTree(vspecfile, rootNode);
            break;
            default:
                return 0;
        }  //switch
    } //while


    return 0;
} // main



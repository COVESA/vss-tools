/**
* (C) 2020 Geotab Inc
* (C) 2018 Volvo Cars
*
* All files and artifacts in this repository are licensed under the
* provisions of the license provided by the LICENSE file in this repository.
*
* 
* Example of parser for a binary format VSS tree.
**/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <stdbool.h>
#include "cparserlib.h"

long currentNode;
long rootNode;
char* vspecfile;

char* getTypeName(nodeTypes_t type) {
    switch (type) { 
        case SENSOR:
            return "SENSOR";
        case ACTUATOR:
            return "ACTUATOR";
        case ATTRIBUTE:
            return "ATTRIBUTE";
        case BRANCH:
            return "BRANCH";
        default:
            printf("getTypeName: unknown type(%d)\n", type);
            return "unknown";
        break;
    } // switch
}

void showNodeData(long currentNode, int currentChild) {
        printf("\nNode: name = %s, type = %s, uuid = %s, validate = %d, children = %d,\ndescription = %s\n", VSSgetName(currentNode), getTypeName(VSSgetType(currentNode)), VSSgetUUID(currentNode), VSSgetValidation(currentNode), VSSgetNumOfChildren(currentNode), VSSgetDescr(currentNode));
        if (VSSgetNumOfChildren(currentNode) > 0)
            printf("Node child[%d]=%s\n", currentChild, VSSgetName(VSSgetChild(currentNode, currentChild)));
//        for (int i = 0 ; i < VSSgetNumOfAllowedElements(currentNode) ; i++)
//            printf("Allowed[%d]=%s\n", i, VSSgetAllowedElement(currentNode, i));
        printf("#allowed=%d\n", VSSgetNumOfAllowedElements(currentNode));
        char* dtype = VSSgetDatatype(currentNode);
        if (dtype != NULL)
            printf("Datatype = %s\n", dtype);
        char* tmp = VSSgetUnit(currentNode);
        if (tmp != NULL)
            printf("Unit = %s\n", tmp);
}

int main(int argc, char** argv) {

    vspecfile = argv[1];
    rootNode = VSSReadTree(vspecfile);

    char traverse[10];
    currentNode = rootNode;
    int currentChild = 0;
    showNodeData(currentNode, currentChild);
    printf("\nThe following parser commands are available: 'u'(p)p/'d'(own)/'l'(eft)/'r'(ight)/s(earch)/m(etadata subtree)/n(odelist)/(uu)i(dlist)/w(rite to file)/h(elp), or any other to quit\n");
    while (true) {
        printf("\n'u'/'d'/'l'/'r'/'s'/'m'/'n'/'i'/'w'/'h', or any other to quit: ");
        scanf("%s", traverse);
        switch (traverse[0]) {
            case 'u':  //up
                if (VSSgetParent(currentNode) != 0) {
                    currentNode = VSSgetParent(currentNode);
                    currentChild = 0;
                }
                showNodeData(currentNode, currentChild);
            break;
            case 'd':  //down
                if (VSSgetChild(currentNode, currentChild) != 0) {
                    currentNode = VSSgetChild(currentNode, currentChild);
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
                if (currentChild < VSSgetNumOfChildren(currentNode)-1) {
                    currentChild++;
                }
                showNodeData(currentNode, currentChild);
            break;
            case 's':  //search for nodes matching path
            {
                char searchPath[MAXCHARSPATH];
                printf("\nPath to resource(s): ");
                scanf("%s", searchPath);
                searchData_t searchData[MAXFOUNDNODES];
                int foundResponses = VSSSearchNodes(searchPath, rootNode, MAXFOUNDNODES, searchData, true, true, 0, NULL, NULL);
                printf("\nNumber of elements found=%d\n", foundResponses);
                for (int i = 0 ; i < foundResponses ; i++) {
                    printf("Found node type=%s\n", getTypeName(VSSgetType((long)(&(searchData[i]))->foundNodeHandles)));
                    printf("Found node datatype=%s\n", VSSgetDatatype((long)(&(searchData[i]))->foundNodeHandles));
                    printf("Found path=%s\n", (char*)(&(searchData[i]))->responsePaths);
                }
            }
            break;
            case 'n':  //create node list file "nodelist.txt"
            {
                int numOfNodes = VSSGetLeafNodesList(rootNode, "nodelist.txt");
                printf("\nLeaf node list with %d nodes found in nodelist.txt\n", numOfNodes);
            }
            break;
            case 'i':  //create node list file "uuidlist.txt"
            {
                int numOfNodes = VSSGetUuidList(rootNode, "uuidlist.txt");
                printf("\nUUID list with %d nodes found in uuidlist.txt\n", numOfNodes);
            }
            break;
            case 'm':  //subtree metadata
            {
                char subTreePath[MAXCHARSPATH];
                printf("\nPath to subtree node: ");
                scanf("%s", subTreePath);
                int depth;
                printf("\nSubtree depth: ");
                scanf("%d", &depth);
                searchData_t searchData[MAXFOUNDNODES];
                int foundResponses = VSSSearchNodes(subTreePath, rootNode, MAXFOUNDNODES, searchData, false, false, 0, NULL, NULL);
                long subtreeNode = (long)(&(searchData[foundResponses-1]))->foundNodeHandles;
                char subTreeRootName[MAXCHARSPATH];
                strcpy(subTreeRootName, VSSgetName((long)(&(searchData[foundResponses-1]))->foundNodeHandles));
                for (int i = 1 ; i < depth ; i++) {
                    strcat(subTreeRootName, ".*");
                }
                foundResponses = VSSSearchNodes(subTreeRootName, subtreeNode, MAXFOUNDNODES, searchData, false, false, 0, NULL, NULL);
                printf("\nNumber of elements found=%d\n", foundResponses);
                for (int i = 0 ; i < foundResponses ; i++) {
                    printf("Node type=%s\n", getTypeName(VSSgetType((long)(&(searchData[i]))->foundNodeHandles)));
                    printf("Node path=%s\n", (char*)(&(searchData[i]))->responsePaths);
                    printf("Node validation=%d\n", VSSgetValidation((long)(&(searchData[i]))->foundNodeHandles));
                }
            }
            break;
            case 'h':  //help
                printf("\nTo traverse the tree, 'u'(p)p/'d'(own)/'l'(eft)/'r'(ight)/s(earch)/m(etadata subtree)/n(odelist)/(uu)i(dlist)/w(rite to file)/h(elp), or any other to quit\n");
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



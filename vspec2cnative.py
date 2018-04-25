#!/usr/bin/python

#
# (C) 2018 Volvo Cars
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
# 
# Convert vspec file to a platform native format.
#  

import sys
import vspec
import json
import getopt
import ctypes

def usage():
    print "Usage:", sys.argv[0], "[-I include_dir] ... [-i prefix:id_file:start_id] vspec_file franca_file"
    print "  -I include_dir              Add include directory to search for included vspec"
    print "                              files. Can be used multiple timees."
    print
    print "  -i prefix:id_file:start_id  Add include directory to search for included vspec"
    print "                              files. Can be used multiple timees."
    print
    print " vspec_file                   The vehicle specification file to parse."     
    print " franca_file                  The file to output the Franca IDL spec to."     
    sys.exit(255)

_cnative = ctypes.CDLL('/home/ubjorken/proj/vehicle_signal_specification/tools/c_native/cnativenodelib.so')
#_cnative.createNativeCnode.argtypes = (ctypes.POINTER(ctypes.c_char),ctypes.POINTER(ctypes.c_char),ctypes.POINTER(ctypes.c_char),ctypes.c_int,ctypes.POINTER(ctypes.c_char),ctypes.POINTER(ctypes.c_char),ctypes.POINTER(ctypes.c_char),ctypes.POINTER(ctypes.c_char),ctypes.POINTER(ctypes.c_char))

_cnative.createNativeCnode.argtypes = (ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p)

def createRootNode():
    # create root node above Attribute/Signal/Private nodes !!! if add/delete nodes on this level nodechildren below must follow !!!
    nodename = "Root"
    nodetype = "branch"
    nodedescription = "VSS tree root node"
    nodeid = ""
    nodechildren = 3
    nodemin = ""
    nodemax = ""
    nodeunit = ""
    nodeenum = ""
    b_nodename = nodename.encode('utf-8')
    b_nodetype = nodetype.encode('utf-8')
    b_nodedescription = nodedescription.encode('utf-8')
    b_nodeid = nodeid.encode('utf-8')
    b_nodemin = nodemin.encode('utf-8')
    b_nodemax = nodemax.encode('utf-8')
    b_nodeunit = nodeunit.encode('utf-8')
    b_nodeenum = nodeenum.encode('utf-8')

    createNativeCnode(b_nodename,b_nodeid,b_nodetype,nodechildren,b_nodedescription,b_nodemin,b_nodemax,b_nodeunit,b_nodeenum)


def createNativeCnode(nodename, nodeid, nodetype, children, description, nodemin, nodemax, unit, enums):
    global _cnative
    _cnative.createNativeCnode(nodename, nodeid, nodetype, children, description, nodemin, nodemax, unit, enums)

def enumString(enumList):
    enumStr = "/"
    for elem in enumList:
        enumStr += elem + "/"
    return enumStr

def create_node(key, val):
    nodename = key
    b_nodename = nodename.encode('utf-8')
    nodetype = val['type']
    b_nodetype = nodetype.encode('utf-8')
    nodedescription = val['description']
    b_nodedescription = nodedescription.encode('utf-8')
    nodeid = ""
    nodechildren = 0
    nodemin = ""
    nodemax = ""
    nodeunit = ""
    nodeenum = ""
    
    if val.has_key("id"):
        nodeid = val["id"]

    if val.has_key("children"):
        nodechildren = len(val["children"].keys())

    if val.has_key("min"):
        nodemin = str(val["min"])

    if val.has_key("max"):
        nodemax = str(val["max"])

    if val.has_key("unit"):
        nodeunit = val["unit"]

    if val.has_key("enum"):
        nodeenum = enumString(val["enum"])

    b_nodeid = nodeid.encode('utf-8')
    b_nodemin = nodemin.encode('utf-8')
    b_nodemax = nodemax.encode('utf-8')
    b_nodeunit = nodeunit.encode('utf-8')
    b_nodeenum = nodeenum.encode('utf-8')

#    print ("Name=%s, Type=%s, Description=%s, Id=%s, Min=%s, Max=%s, Unit=%s, Enum=%s, Children=%d\n" % (nodename,nodetype,nodedescription,nodeid,nodemin,nodemax,nodeunit,nodeenum,nodechildren))

    createNativeCnode(b_nodename,b_nodeid,b_nodetype,nodechildren,b_nodedescription,b_nodemin,b_nodemax,b_nodeunit,b_nodeenum)



def traverse_tree(tree):
    # Traverse all elemnts in tree.
    for key, val in tree.iteritems():
        # Is this a branch?
        if val.has_key("children"):
            # Yes. Recurse
            create_node(key, val)
            traverse_tree(val['children'])
            continue
        create_node(key, val)            


if __name__ == "__main__":
    # 
    # Check that we have the correct arguments
    #
    opts, args= getopt.getopt(sys.argv[1:], "I:i:v:")

    # Always search current directory for include_file
    vss_version = "unspecified version"
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        elif o == "-v":
            vss_version = a
        elif o == "-i":
            id_spec = a.split(":")
            if len(id_spec) != 3:
                print "ERROR: -i needs a 'prefix:id_file:start_id' argument."
                usage()

            [prefix, file_name, start_id] = id_spec
            vspec.db_mgr.create_signal_db(prefix, file_name, int(start_id))
        else:
            usage()

    if len(args) != 2:
        usage()

    try:
        tree = vspec.load(args[0], include_dirs)
    except vspec.VSpecError as e:
        print "Error: {}".format(e)
        exit(255)

    createRootNode()    

    traverse_tree(tree)



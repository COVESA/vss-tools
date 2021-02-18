#!/usr/bin/env python3

#
# (c) 2016 Jaguar Land Rover
# (c) 2021 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Concert vspec file to JSON
#

import sys
import vspec
import json
import getopt
import re

from model.vsstree import VSSNode, VSSType


def usage():
    print("Usage:", sys.argv[0], "[-I include_dir] ... [-i prefix:id_file] vspec_file proto_file")
    print("  -I include_dir       Add include directory to search for included vspec")
    print("                       files. Can be used multiple timees.")
    print()
    print("  -i prefix:uuid_file  File to use for storing generated UUIDs for signals with")
    print("                       a given path prefix. Can be used multiple times to store")
    print("                       UUIDs for signal sub-trees in different files.")
    print()
    print(" vspec_file            The vehicle specification file to parse.")
    print(" json_file             The file to output the JSON objects to.")
    sys.exit(255)



def getDataType(node):
    um =  re.compile('uint.*')
    sm =  re.compile('int.*')
    m64 = re.compile('.int64')

    if str(node.data_type.value) == "boolean":
        return "bool"
    
    elif m64.match(str(node.data_type.value)) != None:
        return str(node.data_type.value)
        
    elif um.match(str(node.data_type.value)) != None:
        return "uint32"

    elif sm.match(str(node.data_type.value)) != None:
        return "int32"
           
    elif str(node.data_type.value) == "float":
        return "float"
    elif str(node.data_type.value) == "double":
        return "double"
    elif str(node.data_type.value) == "string":
        return "string"
    elif str(node.data_type.value) == "string[]": #probably need more generic array handling
        return "repeated string"
    else:
        print("Unsupported datatype "+str(node.data_type.value))
        return None



def createMessage(file, prefix, node):
    dt = getDataType(node)
    if dt is None:
        print("Skipping "+node.name)
        return

    file.write("message "+prefix+" {\n")
    file.write("    "+dt+" value = 1;\n")
    file.write("}\n\n")
    

def export_node(file, prefix, node):
    if node.type == VSSType.SENSOR or node.type == VSSType.ATTRIBUTE:
        createMessage(file, prefix, node)
    elif node.type == VSSType.BRANCH:
        file.write("message "+prefix+" {\n")
        for child in node.children:
            export_node(file, prefix+"_"+child.name, child)
        file.write("}\n\n")


 


def export_proto(file, root):
    file.writelines('//simple VSS .proto mapping\n')
    file.writelines('syntax = "proto3";\n')
    export_node(file, "Vehicle", root)
    file.close()

if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args= getopt.getopt(sys.argv[1:], "I:i:")

    # Always search current directory for include_file
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        elif o == "-i":
            id_spec = a.split(":")
            if len(id_spec) != 2:
                print("ERROR: -i needs a 'prefix:id_file' argument.")
                usage()

            [prefix, file_name] = id_spec
            vspec.db_mgr.create_signal_uuid_db(prefix, file_name)
        else:
            usage()

    if len(args) != 2:
        usage()

    json_out = open (args[1], "w")


    try:
        print("Loading vspec...")
        tree = vspec.load_tree(args[0], include_dirs)
        print("Recursing tree and creating Proto...")
        export_proto(json_out,tree)
        print("All done.")
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        exit(255)

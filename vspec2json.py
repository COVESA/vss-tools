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
from model.vsstree import VSSNode, VSSType


def usage():
    print("Usage:", sys.argv[0], "[-I include_dir] ... [-i prefix:id_file] vspec_file json_file")
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



def export_node(json_dict, node):
    
    json_dict[node.name]={}

    if node.type == VSSType.SENSOR or node.type == VSSType.ACTUATOR or node.type == VSSType.ATTRIBUTE:
        json_dict[node.name]["datatype"]=str(node.data_type.value)

    json_dict[node.name]["type"]=str(node.type.value)

    #many optional attributes are initilized to "" in vsstree.py
    if node.min != "":
        json_dict[node.name]["min"]=node.min
    if node.max != "":
        json_dict[node.name]["max"]=node.max
    if node.enum != "":
        json_dict[node.name]["enum"]=node.enum
    if node.default_value != "":
        json_dict[node.name]["default"]=node.default_value
    if node.value != "":
        json_dict[node.name]["value"]=node.value
    if node.deprecation != "":
        json_dict[node.name]["deprecation"]=node.deprecation

   
    #in case of unit or aggregate, the attribute will be missing
    try: 
        json_dict[node.name]["unit"]=str(node.unit.value)
    except AttributeError:
        pass
    try: 
        json_dict[node.name]["aggregate"]=node.aggregate
    except AttributeError:
        pass



    json_dict[node.name]["description"]=node.description
    json_dict[node.name]["uuid"]=node.uuid
    
    #Might be better to not generate child dict, if there are no children
    #if node.type == VSSType.BRANCH and len(node.children) != 0:
    #    json_dict[node.name]["children"]={}

    #But old JSON code always generates children, so lets do so to
    if node.type == VSSType.BRANCH:
        json_dict[node.name]["children"]={}


    for child in node.children:
        export_node(json_dict[node.name]["children"], child)

    

def export_json(file, root):
    json_dict={}
    export_node(json_dict,root)
    json.dump(json_dict,file, indent=2, sort_keys=True)


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
        print("Recursing tree and creating JSON...")
        export_json(json_out,tree)
        print("All done.")
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        exit(255)

#!/usr/bin/env python3

# (c) 2021 BMW Group
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec tree to franca



import argparse
from vspec.model.vsstree import VSSNode, VSSType
from anytree import PreOrderIter
    
def add_arguments(parser: argparse.ArgumentParser):
   #no additional output for Franca at this moment
   parser.description="The Franca exporter does not currently support the no-uuid option."
   parser.add_argument('-v', metavar='version', help=" Add version information to franca file.")

#Write the header line
def print_franca_header(file, version="unknown"):
    file.write(f"""
// Copyright (C) 2022, COVESA
//
// This program is licensed under the terms and conditions of the
// Mozilla Public License, version 2.0.  The full text of the
// Mozilla Public License is at https://www.mozilla.org/MPL/2.0/

const UTF8String VSS_VERSION = "{version}"

struct SignalSpec {{
    UInt32 id
    String name
    String type
    String description
    String datatype
    String unit
    Double min
    Double max
}}

const SignalSpec[] signal_spec = [
""")


#Write the data lines
def print_franca_content(file, tree):
    output = ""
    for tree_node in PreOrderIter(tree):
        if tree_node.parent:
            if output:
                output += ",\n{"
            else:
                output += "{"
            output += f"\tname: \"{tree_node.qualified_name('.')}\""
            output += f",\n\ttype: \"{tree_node.type.value}\""
            output += f",\n\tdescription: \"{tree_node.description}\""
            if tree_node.has_datatype():
                output += f",\n\tdatatype: \"{tree_node.datatype.value}\""
            output += f",\n\tuuid: \"{tree_node.uuid}\""
            if tree_node.has_unit():
                output += f",\n\tunit: \"{tree_node.unit.value}\""
            if tree_node.min:
                output += f",\n\tmin: {tree_node.min}"
            if tree_node.max:
                output += f",\n\tmax: {tree_node.max}"
            if tree_node.allowed:
                output += f",\n\tallowed: {tree_node.allowed}"
            
            output += "\n}"
    file.write(f"{output}")

def export(config: argparse.Namespace, root: VSSNode):
    print("Generating Franca output...")
    outfile=open(config.output_file,'w')
    print_franca_header(outfile, config.v)
    print_franca_content(outfile, root)
    outfile.write("\n]")
    outfile.close()

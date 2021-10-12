#!/usr/bin/env python3

# Copyright (c) 2021 GENIVI Alliance
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Generate code that can convert VSS signals to Android Automotive
# vehicle properties.
#

import sys
import os
import getopt
import type_hal_parser
import read_mapping_layer
import jinja2
import vspec_helper

myDir= os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(myDir, "../.."))
import vspec
from vspec.model.vsstree import VSSNode, VSSType

# Set up Jinja
jinja_env = jinja2.Environment(
        # Use the subdirectory 'templates' relative to this file's location
        loader =
        jinja2.FileSystemLoader(myDir + '/templates'),

        # Templates with these extension gets automatic autoescape for HTML
        # It's more annoying for code generation, so passing empty list for now.
        autoescape = jinja2.select_autoescape([])
        )

# This is important. We want the control blocks in the template to NOT
# result in any extra white space when rendering templates.
# However, this might be a choice made by each generator, so then we need
# to export the ability to keep these public for the using code to modify
# them.
jinja_env.trim_blocks = True
jinja_env.lstrip_blocks = True

default_templates = {}

# Exception:
class GeneratorError(BaseException):
   def __init__(self, m):
       self.msg = m

def generate_from_tree(node, second=None):
   if type(node) == list or type(node) == tuple:
       # Generate each node and return a list of results.
       # A list is not intended to be printed directly as output, but to be
       # processed by a jinja filter, such as |join(', ')
       return [generate_from_tree(x, second) for x in node]

   # OK, now dispatch gen() depending on the input type
   if second is None:          # No explicit template -> use default for the node type
       return _gen_type(node)
   elif type(second) == str:   # Explicit template -> use it
       return _gen_tmpl(node, second)
   else:
      print(f'node is of type {type(node)}, second arg is of type {type(second)}  ({type(second).__class__}, {type(second).__class__.__name__})')
      raise GeneratorError(f'Wrong use of gen() function! Usage: pass the node as first argument (you passed a {type(node)}), and optionally template name (str) as second argument. (You passed a {second.__name__})')

# If no template is specified, use the default template for the node type.
# A default template must be defined for this node type to use the function
# this way.
def _gen_type(node):
    nodetype=type(node).__name__
    tpl = default_templates.get(nodetype)
    if tpl is None:
       raise GeneratorError(f'gen() function called with node of type {nodetype} but no default template is defined for the type {nodetype}')
    else:
       return get_template(tpl).render({ 'item' : node})

# If template name directly specified, just use it.
def _gen_tmpl(node, templatefile: str):
    return get_template(templatefile).render({ 'item' : node})

# Get template with given name (search path should be handled by the loader)
def get_template(filename):
    return jinja_env.get_template(filename)

def usage():
    print(
        """Usage: vspec2aaprop.py [-I include_dir] vspec_file mapping_file types_hal_file template_file output_file
  -I include_dir       Add include directory to search for included vspec
                       files. Can be used multiple times.
  vspec_file           The top-level vehicle specification file to parse.
  mapping_file         The VSS-layer that defines mapping between VSS and AA properties
  types_hal_file       The Android types.hal header file for VHAL type information.
  template_file        Jinja2 template for the code generation without path.
  output_file          The primary file name to write C++ generated code to.)

  example:vss-tools$ python3 contrib/vspec2aaproperties/vspec2aaprop.py \
      ../spec/VehicleSignalSpecification.vspec \
      contrib/vspec2aaproperties/vspec2prop_mapping.yml \
      contrib/vspec2aaproperties/types.hal \
      android_vhal_mapping_cpp.tpl \
      test.cpp
"""
    )
    sys.exit(255)

if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args = getopt.getopt(sys.argv[1:], "I:i:")

    # Always search current directory for include_file
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        else:
            usage()

    if len(args) != 5:
        usage()

    # Create cross-reference map between VSS and Android from the YAML file.
    map_tree = read_mapping_layer.load_tree(args[1])
    # Create Android type table from the Android type.hal header file.
    type_table = type_hal_parser.type_table(args[2])

    try:
        vss_tree = vspec_helper.VSpecHelper(vspec.load_tree(args[0], include_dirs))
        # vss_tree = vspec.load_tree(args[0], include_dirs)
    except vspec.VSpecError as e:
        print("Error: {}".format(e))
        exit(255)

    #MAP the trees for the Jinja
    jinja_env.globals.update(
    gen=generate_from_tree,
    vss_tree=vss_tree,
    map_tree=map_tree,
    type_table=type_table,
    str=str
    )

    #Generate the output CPP file using Jinja2 generator (vss_tree, map_tree, type_table):
    with open(args[4], "w") as output_file:
        print(generate_from_tree(map_tree, args[3]),file=output_file)
        output_file.write("//DONE\n")

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
"""
C++ Generator from COVESA Vehicle Signal Specification to Android VHAL representation.
"""

import sys
import os
import argparse

myDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(myDir, "../.."))

import type_hal_parser
import read_mapping_layer
import jinja2
import vspec_helper
import read_type_layer
from vss_tools.vspec.model.vsstree import VSSNode, VSSType
import vss_tools.vspec as vspec



# Set up Jinja
jinja_env = jinja2.Environment(
    # Use the subdirectory 'templates' relative to this file's location
    loader=jinja2.FileSystemLoader(myDir + '/templates'),

    # Templates with these extension gets automatic autoescape for HTML
    # It's more annoying for code generation, so passing empty list for now.
    autoescape=jinja2.select_autoescape([])
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
    """
    General exception for the generator.
    """
    def __init__(self, m):
        self.msg = m


def generate_from_tree(node, second=None):
    """
    VSS Tree generator.
    """
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
        print(
            f'node is of type {type(node)}, second arg is of type {type(second)}  ({type(second).__class__}, {type(second).__class__.__name__})')
        raise GeneratorError(
            f'Wrong use of gen() function! Usage: pass the node as first argument (you passed a {type(node)}), and optionally template name (str) as second argument. (You passed a {second.__name__})')

# If no template is specified, use the default template for the node type.
# A default template must be defined for this node type to use the function
# this way.


def _gen_type(node):
    """
    _gen_type
    """
    nodetype = type(node).__name__
    tpl = default_templates.get(nodetype)
    if tpl is None:
        raise GeneratorError(
            f'gen() function called with node of type {nodetype} but no default template is defined for the type {nodetype}')
    else:
        return get_template(tpl).render({'item': node})

# If template name directly specified, just use it.


def _gen_tmpl(node, templatefile: str):
    return get_template(templatefile).render({'item': node})

# Get template with given name (search path should be handled by the loader)


def get_template(filename):
    return jinja_env.get_template(filename)

if __name__ == "__main__":
    """
    Generator main routine.
    - Parse arguments
    - Read and parse map (vspec2prop_mapping.yml) to map_tree
      - uses read_mapping_layer.py function load_tree()
    - Read and parse Android VHAL header (types.hal) to vhal_type
      - uses type_hal_parser.py class VhalType
    - Read and parse VSS (../../../spec/VehicleSignalSpecification.vspec) to vss_tree
      - uses vspec_helper.py wrapper class VSpecHelper for direct access to VSS items (anytree.Resolver)
    - Creates TypeMaptypemap helper class by reading (typemap.yml) and combining all other classes under typemap
      - uses read_type_layer.py TypeMap helper class which provides helper functions for Jinja
    - Creates Jinja2 environment with provided maps.
    - Creates output with selected Jinja2 file (android_vhal_mapping_cpp.tpl)
    - Writes out single .cpp file (AndroidVssConverter.cpp)
    """
    #
    # Check that we have the correct arguments
    #
    parser = argparse.ArgumentParser(
        prog="vspec2aaprop",
        description="Convert vss specification to Android Auto properties according to the input map file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("output", nargs="?", type=str,
                        default="AndroidVssConverter.cpp", help="Ouput .cpp file name")
    parser.add_argument("-v", "--vspec", type=str,
                        default="../../../spec/VehicleSignalSpecification.vspec", help="Vehicle Signal Specification")
    parser.add_argument("-m", "--map", type=str,
                        default="vspec2prop_mapping.yml", help="Conversion Item Map File")
    parser.add_argument("-a", "--android", type=str, default="types.hal",
                        help="Android Type Mapping (Android types.hal file)")
    parser.add_argument("-t", "--typemap", type=str,
                        default="typemap.yml", help="VSS/VHAL/Android CPP type mapping")
    parser.add_argument("-j", "--jinja", type=str,
                        default="android_vhal_mapping_cpp.tpl", help="Jinja2 generator file")
    parser.add_argument("-I", "--include", nargs="+", type=str,
                        default=["templates"], help="Include directories")
    args = parser.parse_args()

    # Always search current directory for include_file
    include_dirs = ["."]
    include_dirs.extend(args.include)

    # Create cross-reference map between VSS and Android from the YAML file.
    map_tree = read_mapping_layer.load_tree(args.map)
    # Create Android type table from the Android type.hal header file.
    vhal_type = type_hal_parser.VhalType(args.android)

#    try:
    vss_tree = vspec_helper.VSpecHelper(
            vspec.load_tree(args.vspec, include_dirs))
        # vss_tree = vspec.load_tree(args[0], include_dirs)
#    except vspec.VSpecError as e:
#        print("Error: {}".format(e))
#        exit(255)

    typemap = read_type_layer.TypeMap(
        map_tree, args.typemap, vss_tree, vhal_type)

    # MAP the trees for the Jinja
    jinja_env.globals.update(
        gen=generate_from_tree,
        vss_tree=vss_tree,
        map_tree=map_tree,
        vhal_type=vhal_type,
        typemap=typemap,
    )

    # Generate the output CPP file using Jinja2 generator (vss_tree, map_tree, type_table):
    with open(args.output, "w") as output_file:
        print(generate_from_tree(map_tree, args.jinja), file=output_file)
        output_file.write("//DONE\n")

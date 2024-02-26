from __future__ import annotations
import yaml
'''
YAML loader for the mapping table.
'''
# Copyright (c) 2021 GENIVI Alliance
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Generate code that can convert VSS signals to Android Automotive
# vehicle properties.
#

def load_tree(filepath):
    """
    load_tree(filepath)
    Loads and returns the yaml map file filepath
    Mapping file maps the VSS signals to VHAL signals with possible conversions.
    Breaks the possible elements in conversion formulas to the tree structure for easier utilization in Jinja.
    """
    with open(filepath, "r") as f:
        tree = yaml.load(f.read(), Loader=yaml.SafeLoader)
        # Create input items for the complex yaml formulas - remove arithmetic from the formula for variable evaluation.
        translator=str.maketrans({"/":" ","*":" ","+":" ","(":" ",")":" ","!":" ","&":" ","%":" ","^":" ","|":" ","\t":" "})
        for key,item in tree.items():
            if "translation" in item:
                if "complex" in item["translation"]:
                    formula_elements=item["translation"]["complex"].translate(translator).split()
                    item["translation"]["input"]=[element[1:] for element in formula_elements if element[0]=="$"]
    return tree

if __name__ == "__main__":
    """
    Simple main program to load the example map to the tree (very basic test)
    """
    tree=load_tree("vspec2prop_mapping.yml")
    print(tree)

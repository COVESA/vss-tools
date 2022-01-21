from __future__ import annotations
import yaml
'''
Jinja2 helper for the type mapping.
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

class TypeMap:
    """
    TypeMap helper class for type conversions.
    Reads typemap yaml file from filepath
    Stores locally inside the class
    self.map_tree: map_tree, Parser actual VSS-VHAL map file with possible conversions
    self.typemap: filepath, Reads and parses the filepath yaml file for individual type mapping between VSS/VHAL/CPP.
    self.vss_tree: parsed Vehicle Signal Specification (helper class)
    self.vhal_type: parsed VHAL types map
    """
    def __init__(self,map_tree,filepath,vss_tree,vhal_type):
        self.map_tree=map_tree
        with open(filepath, "r") as f:
            self.typemap = yaml.load(f.read(), Loader=yaml.SafeLoader)
        self.vss_tree=vss_tree
        self.vhal_type=vhal_type

    def __getitem__(self,name):
        """
        Simple item parser. Returns dict that contains the actual mapping.
        name = VSS Type
        """
        return self.typemap[name]

    def vss2cpp(self,key):
        """
        Returns c++ type definition of the VSS item.
        key = VSS Item name
        """
        return self.typemap[self.vss_tree.vsstype(key)]["cpp"]

    def vhal2cpp(self,item):
        """
        Returns c++ type definition of the VHAL item.
        item = VHAL Item name.
        """
        if type(item) is dict:
            return self.typemap[self.vhal_type[item['aospId']]]["cpp"]
        else:
            return self.typemap[self.vhal_type[self.map_tree[item]['aospId']]]["cpp"]

    def vss2vhal(self,key,item=None):
        """
        Returns VHAL type definition of the VSS item.
        key = VSS Item name.
        item = Optional VHAL target type.
        """
        if item is None:
            return self.typemap[self.vss_tree.vsstype(key)]["to"][self.vhal_type[self.map_tree[key]['aospId']]]
        else:
            return self.typemap[self.vss_tree.vsstype(key)]["to"][self.vhal_type[item['aospId']]]

    def vss_from_string(self,key):
        """
        Return c++ type conversion from string to target type.
        key = VSS Item name.
        """
        #typemap[(str(vss_tree[key].data_type).split(".")[-1])]["from"]["string"].replace("_val_","value")
        return self.typemap[str(self.vss_tree[key].data_type).split(".")[-1]]["from"]["string"].replace("_val_","value")

    def vhal_prop(self,item):
        """
        Return VHAL typing for the VehicleProperty.value union.
        """
        if type(item) is dict:
            return "prop.value."+self.typemap[self.vhal_type[item['aospId']]]["vhal"]+"Values"
        else:
            return "prop.value."+self.typemap[self.vhal_type[self.map_tree[item]['aospId']]]["vhal"]+"Values"

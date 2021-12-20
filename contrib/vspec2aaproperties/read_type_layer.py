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

class TypeMap:
    def __init__(self,map_tree,filepath,vss_tree,vhal_type):
        self.map_tree=map_tree
        with open(filepath, "r") as f:
            self.typemap = yaml.load(f.read(), Loader=yaml.SafeLoader)
        self.vss_tree=vss_tree
        self.vhal_type=vhal_type

    def __getitem__(self,name):
        return self.typemap[name]

    def vss2cpp(self,key):
        return self.typemap[self.vss_tree.vsstype(key)]["cpp"]

    def vhal2cpp(self,item):
        if type(item) is dict:
            return self.typemap[self.vhal_type[item['aospId']]]["cpp"]
        else:
            return self.typemap[self.vhal_type[self.map_tree[item]['aospId']]]["cpp"]

    def vss2vhal(self,key,item=None):
        if item is None:
            return self.typemap[self.vss_tree.vsstype(key)]["to"][self.vhal_type[self.map_tree[key]['aospId']]]
        else:
            return self.typemap[self.vss_tree.vsstype(key)]["to"][self.vhal_type[item['aospId']]]

    def vss_from_string(self,key):
        #typemap[(str(vss_tree[key].data_type).split(".")[-1])]["from"]["string"].replace("_val_","value")
        return self.typemap[str(self.vss_tree[key].data_type).split(".")[-1]]["from"]["string"].replace("_val_","value")

    def vhal_prop(self,item):
        if type(item) is dict:
            return "prop.value."+self.typemap[self.vhal_type[item['aospId']]]["vhal"]+"Values"
        else:
            return "prop.value."+self.typemap[self.vhal_type[self.map_tree[item]['aospId']]]["vhal"]+"Values"

if __name__ == "__main__":
    typemap=load_map("typemap.yml")
    print(typemap)

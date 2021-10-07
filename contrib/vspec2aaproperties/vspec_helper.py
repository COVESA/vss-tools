from anytree import Resolver
'''
vspec helper class to support tree[full.vspec.definition] for Jinja.
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

class VSpecHelper:
    #__init__ input the vspec tree and stores it inside the helper class.
    def __init__(self,tree):
        self.tree=tree
        #Create resolver for the anytree "name" tree.
        self.r=Resolver("name")
    def __getitem__(self,item):
        #Currently vspec uses hardcoded "/" as separator while YAML defines "." separated values. Map between these for the resolver.
        return self.r.get(self.tree,f'/{item.replace(".","/")}')


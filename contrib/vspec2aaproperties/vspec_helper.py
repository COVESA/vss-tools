'''
vspec helper class to support tree[full.vspec.definition] for Jinja.
'''
import os
import sys
myDir= os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(myDir, "../.."))
from vspec import ChildResolverError
from anytree import Resolver
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
    '''
    VSpecHelper class is a wrapper class for the vspec to enable tree[full.vspec.definition] for Jinja.
    '''

    #__init__ input the vspec tree and stores it inside the helper class.
    def __init__(self,vss_tree):
        '''
        tree: vspec tree to wrap
        usage: vss_tree = vspec_helper.VSpecHelper(vspec.load_tree(args[0], include_dirs))
        '''
        self.vss_tree=vss_tree
        #Create resolver for the anytree "name" tree.
        self.r=Resolver("name")

    def vsstype(self,key):
        return str(self[key].data_type).split(".")[-1]

    def __getitem__(self,item):
        '''
        item: Ascii representation of the vspec item. e.g. "Vehicle.Chassis.Axle.Row2.Wheel.Left.Tire.Pressure"
        returns vspec anytree object.
        '''
        #Currently vspec uses hardcoded "/" as separator while YAML defines "." separated values. Map between these for the resolver.
        result=None
        try:
            result=self.r.get(self.vss_tree,f'/{item.replace(".","/")}')
        except ChildResolverError as c:
            print(item,"ERROR: not found in VSpec. Terminating.")
            sys.exit(1)
        return result


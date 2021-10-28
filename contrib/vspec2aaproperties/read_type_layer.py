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

def load_map(filepath):
    with open(filepath, "r") as f:
        typemap = yaml.load(f.read(), Loader=yaml.SafeLoader)
    return typemap

if __name__ == "__main__":
    typemap=load_map("typemap.yml")
    print(typemap)

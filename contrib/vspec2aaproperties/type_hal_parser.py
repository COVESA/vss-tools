import re
import anytree
'''
Android types.hal parser to create the Android VHAL item type table.
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

class VhalType:
    #__init__ reads the types.hal file and uses regex to convert the header file to type table.
    def __init__(self,file):
        with open(file,"r") as f:
            content=f.read()
        #Regex for removing all the comments from the header file.
        pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
        regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
        def _replacer(match):
            if match.group(2) is not None:
                return "" #remove comment
            else:
                return match.group(1) #return code
        #Remove all the comments from the header file to avoid incorrect regex with the code.
        content=regex.sub(_replacer, content)

        #Find the VehicleProperties {} structure from the header file.
        propertyblock=re.search("enum VehicleProperty : int32_t {(.+?)}",content,re.DOTALL | re.MULTILINE)
        #Parse the VehicleProperties with the id and type definitions.
        propertytypes=re.findall("^ *([A-Z_0-9]*) = \(.*?VehiclePropertyType:([A-Z_0-9]*)[ \,]*$",propertyblock[1],re.DOTALL | re.MULTILINE)
        #Keep the table inside the class to provide the __getitem__ for the Jinja (table[AndroidId])
        self.table={item:value for item,value in propertytypes}

    #Implement __getitem__ to support easy access to the Android types with table[AndroidId]
    def __getitem__(self,name):
        typestr=self.table[name.split(":")[-1]]
        return typestr

    def __iter__(self):
        return iter(self.table)

#Standalone test main function to test the table evaluation.
if __name__ == "__main__":
    table = type_table("types.hal")
    for item in table:
        print(f'{item} type is {table[item]}')

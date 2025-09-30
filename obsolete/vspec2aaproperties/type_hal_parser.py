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
    """
    Class to embed the VHAL header mapping.
    Stores VHAL constants and related variable type to the table.
    """
    #__init__ reads the types.hal file and uses regex to convert the header file to type table.
    def __init__(self,file):
        """
        __init__(self,file)
        Initializes the class by reading the given file to the class table self.table
        """
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
        """
        __getitem__(self,name)
        Enables direct access to single VHAL constant type.
        Returns type that is related to the VHAL constant name.
        """
        typestr=self.table[name.split(":")[-1]]
        return typestr

    def __iter__(self):
        """
        __iter__(self)
        Enables iteration of the VHAL constant types.
        """
        return iter(self.table)

#Standalone test main function to test the table evaluation.
if __name__ == "__main__":
    """
    Simple main program to load and map the types.hal file (simple test)
    """
    table = VhalType("types.hal")
    for item in table:
        print(f'{item} type is {table[item]}')

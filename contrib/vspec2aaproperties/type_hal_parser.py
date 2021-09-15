import re
import anytree

    
class type_table:
    def __init__(self,file):
        with open(file,"r") as f:
            content=f.read()
        pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
        regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
        def _replacer(match):
            if match.group(2) is not None:
                return "" #remove comment
            else: 
                return match.group(1) #return code
        content=regex.sub(_replacer, content)

        propertyblock=re.search("enum VehicleProperty : int32_t {(.+?)}",content,re.DOTALL | re.MULTILINE)
        propertytypes=re.findall("^ *([A-Z_0-9]*) = \(.*?VehiclePropertyType:([A-Z_0-9]*)[ \,]*$",propertyblock[1],re.DOTALL | re.MULTILINE)
        self.table={item:value for item,value in propertytypes}

    def __getitem__(self,name):
        typestr=self.table[name.split(":")[-1]]
        print("getitem:",name,":",typestr)
        return typestr


if __name__ == "__main__":
    get_vehicleproperty("contrib/vspec2aaproperties/types.hal")
import re
def get_vehicleproperty(file):
    with open(file,"r") as f:
        content=f.read()
    propertyblock=re.search("enum VehicleProperty : int32_t {(.+?)}",content,re.DOTALL | re.MULTILINE)
    propertytypes=re.findall("^ *([A-Z_0-9]*) = \(.*?VehiclePropertyType:([A-Z_0-9]*?)$",propertyblock[1],re.DOTALL | re.MULTILINE)
    return propertytypes

if __name__ == "__main__":
    get_vehicleproperty("contrib/vspec2aaproperties/types.hal")
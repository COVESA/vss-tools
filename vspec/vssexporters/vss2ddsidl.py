#!/usr/bin/env python3

#
# (c) 2022 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec files to DDS-IDL
#

import argparse
import keyword

from vspec.model.vsstree import VSSNode, VSSType


def add_arguments(parser: argparse.ArgumentParser):
    parser.description = "The DDS-IDL exporter"
    parser.add_argument('--all-idl-features', action='store_true',
                        help='Generate all features based on DDS IDL 4.2 specification')


c_keywords = [
    "auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else", "enum", "extern", "float",
    "for", "goto", "if", "int", "long", "register", "return", "short", "signed", "sizeof", "static", "struct", "switch",
    "typedef", "union", "unsigned", "void", "volatile", "while"
    ]

# Based on http://www.omg.org/spec/IDL/4.2/
idl_keywords = [
    "abstract", "any", "alias", "attribute", "bitfield", "bitmask", "bitset", "boolean", "case", "char", "component",
    "connector", "const", "consumes", "context", "custom", "default", "double", "exception", "emits", "enum",
    "eventtype", "factory", "FALSE", "finder", "fixed", "float", "getraises", "home", "import", "in", "inout",
    "interface", "local", "long", "manages", "map", "mirrorport", "module", "multiple", "native", "Object", "octet",
    "oneway", "out", "primarykey", "private", "port", "porttype", "provides", "public", "publishes", "raises",
    "readonly", "setraises", "sequence", "short", "string", "struct", "supports", "switch", "TRUE", "truncatable",
    "typedef", "typeid", "typename", "typeprefix", "unsigned", "union", "uses", "ValueBase", "valuetype", "void",
    "wchar", "wstring", "int8", "uint8", "int16", "int32", "int64", "uint16", "uint32", "uint64"
    ]


def getAllowedName(name):
    if (
        name.lower() in c_keywords
        or name.lower() in idl_keywords
        or keyword.iskeyword(name.lower)
    ):
        return "_"+name
    else:
        return name


def get_allowed_enum_literal(name: str):
    """
    Check if this is is an allowed literal name, if not add prefix.

    Background:

    In VSS '123' is a perfectly fine string literal, usable as allowed value for a string.
    The current exporter (this file) translated it previously to 123 which is not a valid DSS IDL literal.
    Adding an underscore as prefix makes the generated IDL ok, but then gives problems if generating for example
    Python code by Eclipse Cyclone DDS idlc Python Backend.
    By that reason we now add a regular character instead.
    """
    if name[0].isdigit():
        return "d" + name
    return name


idlFileBuffer = []

dataTypesMap_covesa_dds = {"uint8": "octet",
                           "int8": "octet",
                           "uint16": "unsigned short",
                           "int16": "short",
                           "uint32": "unsigned long",
                           "int32": "long",
                           "uint64": "unsigned long long",
                           "int64": "long long",
                           "boolean": "boolean",
                           "float": "float",
                           "double": "double",
                           "string": "string"
                           }


def export_node(node, generate_uuid, generate_all_idl_features):
    """
    This method is used to traverse VSS node and to create corresponding DDS IDL buffer string
    """
    global idlFileBuffer
    datatype = None
    unit = None
    min = None
    max = None
    defaultValue = None
    allowedValues = None
    arraysize = None

    if node.type == VSSType.BRANCH:
        idlFileBuffer.append("module "+getAllowedName(node.name))
        idlFileBuffer.append("{")
        for child in node.children:
            export_node(child, generate_uuid, generate_all_idl_features)
        idlFileBuffer.append("};")
        idlFileBuffer.append("")
    else:
        isEnumCreated = False
        # check if there is a need to create enum (based on the usage of allowed values)
        if node.allowed != "":
            """
            enum should be enclosed under module block to avoid namespec conflict
            module name for enum is chosen as the node name +
            """
            if (node.datatype.value in ["string", "string[]"]):
                idlFileBuffer.append("module "+getAllowedName(node.name)+"_M")
                idlFileBuffer.append("{")
                idlFileBuffer.append("enum " + getAllowedName(node.name) +
                                     "Values{"+str(",".join(get_allowed_enum_literal(item) for item in node.allowed)) +
                                     "};")
                isEnumCreated = True
                idlFileBuffer.append("};")
                allowedValues = str(node.allowed)
            else:
                print(f"Warning: VSS2IDL can only handle allowed values for string type, "
                      f"signal {node.name} has type {node.datatype.value}")

        idlFileBuffer.append("struct "+getAllowedName(node.name))
        idlFileBuffer.append("{")
        if generate_uuid:
            idlFileBuffer.append("string uuid;")
        # fetching value of datatype and obtaining the equivalent DDS type
        try:
            if str(node.datatype.value) in dataTypesMap_covesa_dds:
                datatype = str(dataTypesMap_covesa_dds[str(node.datatype.value)])
            elif '[' in str(node.datatype.value):
                nodevalueArray = str(node.datatype.value).split("[", 1)
                if str(nodevalueArray[0]) in dataTypesMap_covesa_dds:
                    datatype = str(dataTypesMap_covesa_dds[str(nodevalueArray[0])])
                    arraysize = '['+str(arraysize)+nodevalueArray[1]

        except AttributeError:
            pass
        # fetching value of unit
        try:
            unit = str(node.unit.value)
        except AttributeError:
            pass

        if node.min != "":
            min = str(node.min)
        if node.max != "":
            max = str(node.max)
        if node.default != "":
            defaultValue = node.default
            if isinstance(defaultValue, str) and not isEnumCreated:
                defaultValue = "\""+defaultValue+"\""

        if datatype is not None:
            # adding range if min and max are specified in vspec file
            if min is not None and max is not None and generate_all_idl_features:
                idlFileBuffer.append("@range(min="+str(min)+" ,max="+str(max)+")")

            if allowedValues is None:
                if defaultValue is None:
                    idlFileBuffer.append(("sequence<"+datatype+"> value" if (arraysize is not None) else
                                          datatype+" value")+";")
                else:
                    # default values in IDL file are not accepted by CycloneDDS/FastDDS :
                    # these values can be generated if --all-idl-features is set as True
                    idlFileBuffer.append(("sequence<"+datatype+"> value" if arraysize is not None else
                                          datatype + " value") +
                                         ("  default " + str(defaultValue) if generate_all_idl_features else "") + ";")
            else:
                # this is the case where allowed values are provided, accordingly contents are converted to enum
                if defaultValue is None:
                    idlFileBuffer.append(getAllowedName(node.name)+"_M::"+getAllowedName(node.name)+"Values value;")
                else:
                    # default values in IDL file are not accepted by CycloneDDS/FastDDS :
                    # these values can be generated if --all-idl-features is set as True
                    idlFileBuffer.append(getAllowedName(node.name) + "_M::"+getAllowedName(node.name) + "Values value" +
                                         (" " + str(defaultValue) if generate_all_idl_features else "") + ";")

        if unit is not None:
            idlFileBuffer.append(("" if generate_all_idl_features else "//") + "const string unit=\"" + unit + "\";")

        idlFileBuffer.append(("" if generate_all_idl_features else "//") + "const string type =\"" +
                             str(node.type.value) + "\";")

        idlFileBuffer.append(("" if generate_all_idl_features else "//") + "const string description=\"" +
                             node.description + "\";")
        idlFileBuffer.append("};")


def export_idl(file, root, generate_uuids=True, generate_all_idl_features=False):
    """This method is used to traverse through the root VSS node to build
       -> DDS IDL equivalent string buffer and to serialize it acccordingly into a file
    """
    export_node(root, generate_uuids, generate_all_idl_features)
    file.write('\n'.join(idlFileBuffer))
    print("IDL file generated at location : "+file.name)


def export(config: argparse.Namespace, root: VSSNode, print_uuid):
    print("Generating DDS-IDL output...")
    idl_out = open(config.output_file, 'w')
    export_idl(idl_out, root, print_uuid, config.all_idl_features)

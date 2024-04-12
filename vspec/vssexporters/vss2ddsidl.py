#!/usr/bin/env python3

# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

#
# Convert vspec files to DDS-IDL
#

import argparse
import keyword
import logging
from typing import Optional

from vspec.model.vsstree import VSSNode, VSSType
from vspec.vss2x import Vss2X
from vspec.vspec2vss_config import Vspec2VssConfig

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
        return "_" + name
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
        idlFileBuffer.append("module " + getAllowedName(node.name))
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
                idlFileBuffer.append("module " + getAllowedName(node.name) + "_M")
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

        idlFileBuffer.append("struct " + getAllowedName(node.name))
        idlFileBuffer.append("{")
        if generate_uuid:
            idlFileBuffer.append("string uuid;")
        # fetching value of datatype and obtaining the equivalent DDS type
        try:
            datatype_str = node.get_datatype()
            if node.has_datatype():
                if datatype_str in dataTypesMap_covesa_dds:
                    datatype = str(dataTypesMap_covesa_dds[datatype_str])
                elif '[' in datatype_str:
                    nodevalueArray = datatype_str.split("[", 1)
                    if str(nodevalueArray[0]) in dataTypesMap_covesa_dds:
                        datatype = str(dataTypesMap_covesa_dds[str(nodevalueArray[0])])
                        arraysize = '[' + str(arraysize) + nodevalueArray[1]
            else:  # no primitive type. this is custom
                datatype = datatype_str.replace(".", "::")  # custom data type

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
                idlFileBuffer.append("@range(min=" + str(min) + " ,max=" + str(max) + ")")

            if allowedValues is None:
                if defaultValue is None:
                    idlFileBuffer.append(
                        ("sequence<" + datatype + "> value" if arraysize is not None else datatype + " value") + ";")
                else:
                    # default values in IDL file are not accepted by CycloneDDS/FastDDS :
                    # these values can be generated if --all-idl-features is set as True
                    idlFileBuffer.append(
                        ("sequence<" + datatype + "> value" if arraysize is not None else datatype + " value") +
                        ("  default " + str(defaultValue) if generate_all_idl_features else "") + ";")
            else:
                # this is the case where allowed values are provided, accordingly contents are converted to enum
                if defaultValue is None:
                    idlFileBuffer.append(getAllowedName(node.name)+"_M::"+getAllowedName(node.name)+"Values value;")
                else:
                    # default values in IDL file are not accepted by CycloneDDS/FastDDS :
                    # these values can be generated if --all-idl-features is set as True
                    idlFileBuffer.append(
                        getAllowedName(node.name) + "_M::" + getAllowedName(node.name) +
                        "Values value" + (" " + str(defaultValue) if generate_all_idl_features else "") + ";")

        if unit is not None:
            idlFileBuffer.append(("" if generate_all_idl_features else "//") + "const string unit=\"" + unit + "\";")

        idlFileBuffer.append(("" if generate_all_idl_features else "//") + "const string type =\"" +
                             str(node.type.value) + "\";")

        idlFileBuffer.append(("" if generate_all_idl_features else "//") + "const string description=\"" +
                             node.description + "\";")
        idlFileBuffer.append("};")


class StructExporter(object):
    """
    Helper class used for generating export output for struct data types.
    """

    def __init__(self):
        self.str_buf = ""
        self.structs_seen = []

    def export(self, root) -> str:
        self.str_buf = ""
        self.structs_seen = []
        self.export_data_type_node(root)
        return self.str_buf

    def export_data_type_node(self, node):
        """
        This method is used to traverse VSS node and to create corresponding DDS IDL buffer string
        """

        prefix = ""
        suffix = ""
        if node.is_branch():
            prefix = f"module {getAllowedName(node.name)}" + " {\n"
            suffix = "};\n"
        elif node.is_struct():
            # check if the properties use structs that have not been seen before
            # if not, add a forward declaration
            fwds = []
            for c in node.children:
                # primtive type
                if c.has_datatype():
                    continue

                datatype_str = c.get_datatype().replace('.', '::').split("[", 1)[0]
                if datatype_str not in self.structs_seen:
                    base_type = datatype_str.split("::")[-1]
                    fwds.append(base_type)

            fwds.sort()
            for f in set(fwds):
                prefix += f"struct {f};\n"

            prefix += f"struct {getAllowedName(node.name)}" + " {\n"
            suffix = "};\n"
            self.structs_seen.append(node.qualified_name("::").split("[", 1)[0])
        else:
            datatype_str = node.get_datatype().replace('.', '::').split("[", 1)[0]
            is_seq = '[' in node.get_datatype()
            if is_seq:
                self.str_buf += f"sequence<{datatype_str}> {getAllowedName(node.name)};\n"
            else:
                self.str_buf += (f"{datatype_str} {getAllowedName(node.name)};\n")

        self.str_buf += (f"{prefix}")

        for child in node.children:
            self.export_data_type_node(child)
        self.str_buf += suffix


def export_idl(file, root, generate_uuids=True, generate_all_idl_features=False):
    """This method is used to traverse through the root VSS node to build
       -> DDS IDL equivalent string buffer and to serialize it acccordingly into a file
    """
    export_node(root, generate_uuids, generate_all_idl_features)
    file.write('\n'.join(idlFileBuffer))
    logging.info("IDL file generated at location : " + file.name)


class Vss2DdsIdl(Vss2X):

    def __init__(self, vspec2vss_config: Vspec2VssConfig):
        vspec2vss_config.no_expand_option_supported = False

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.description = "The DDS-IDL exporter"
        parser.add_argument('--all-idl-features', action='store_true',
                            help='Generate all features based on DDS IDL 4.2 specification')

    def generate(self, config: argparse.Namespace, signal_root: VSSNode, vspec2vss_config: Vspec2VssConfig,
                 data_type_root: Optional[VSSNode] = None) -> None:
        logging.info("Generating DDS-IDL output...")

        if data_type_root is not None:
            exporter = StructExporter()
            with open(config.output_file, 'w') as idl_out:
                idl_out.write(exporter.export(data_type_root))

        with open(config.output_file, 'a' if data_type_root is not None else 'w') as idl_out:
            export_idl(idl_out, signal_root, vspec2vss_config.generate_uuid, config.all_idl_features)

    def __del__(self):
        idlFileBuffer.clear()

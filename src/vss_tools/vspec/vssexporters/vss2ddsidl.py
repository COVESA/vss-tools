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

import keyword
from pathlib import Path

import rich_click as click

import vss_tools.vspec.cli_options as clo
from vss_tools import log
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.model import VSSDataBranch, VSSDataStruct
from vss_tools.vspec.tree import VSSNode
from vss_tools.vspec.utils.misc import getattr_nn

c_keywords = [
    "auto",
    "break",
    "case",
    "char",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "extern",
    "float",
    "for",
    "goto",
    "if",
    "int",
    "long",
    "register",
    "return",
    "short",
    "signed",
    "sizeof",
    "static",
    "struct",
    "switch",
    "typedef",
    "union",
    "unsigned",
    "void",
    "volatile",
    "while",
]

# Based on http://www.omg.org/spec/IDL/4.2/
idl_keywords = [
    "abstract",
    "any",
    "alias",
    "attribute",
    "bitfield",
    "bitmask",
    "bitset",
    "boolean",
    "case",
    "char",
    "component",
    "connector",
    "const",
    "consumes",
    "context",
    "custom",
    "default",
    "double",
    "exception",
    "emits",
    "enum",
    "eventtype",
    "factory",
    "FALSE",
    "finder",
    "fixed",
    "float",
    "getraises",
    "home",
    "import",
    "in",
    "inout",
    "interface",
    "local",
    "long",
    "manages",
    "map",
    "mirrorport",
    "module",
    "multiple",
    "native",
    "Object",
    "octet",
    "oneway",
    "out",
    "primarykey",
    "private",
    "port",
    "porttype",
    "provides",
    "public",
    "publishes",
    "raises",
    "readonly",
    "setraises",
    "sequence",
    "short",
    "string",
    "struct",
    "supports",
    "switch",
    "TRUE",
    "truncatable",
    "typedef",
    "typeid",
    "typename",
    "typeprefix",
    "unsigned",
    "union",
    "uses",
    "ValueBase",
    "valuetype",
    "void",
    "wchar",
    "wstring",
    "int8",
    "uint8",
    "int16",
    "int32",
    "int64",
    "uint16",
    "uint32",
    "uint64",
]


def getAllowedName(name):
    if name.lower() in c_keywords or name.lower() in idl_keywords or keyword.iskeyword(name.lower):
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


idl_file_buffer = []

dataTypesMap_covesa_dds = {
    "uint8": "octet",
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
    "string": "string",
}


def export_node(node: VSSNode, generate_uuid: bool, generate_all_idl_features: bool) -> None:
    """
    This method is used to traverse VSS node and to create corresponding DDS IDL buffer string
    """
    global idl_file_buffer
    arraysize = getattr(node.data, "arraysize", None)
    allowed_values = None

    if isinstance(node.data, VSSDataBranch):
        idl_file_buffer.append("module " + getAllowedName(node.name))
        idl_file_buffer.append("{")
        for child in node.children:
            export_node(child, generate_uuid, generate_all_idl_features)
        idl_file_buffer.append("};")
        idl_file_buffer.append("")
    else:
        enum_created = False
        # check if there is a need to create enum (based on the usage of allowed values)
        allowed = getattr(node.data, "allowed")
        datatype = getattr(node.data, "datatype")
        if allowed:
            """
            enum should be enclosed under module block to avoid namespec conflict
            module name for enum is chosen as the node name +
            """
            if datatype in ["string", "string[]"]:
                idl_file_buffer.append("module " + getAllowedName(node.name) + "_M")
                idl_file_buffer.append("{")
                idl_file_buffer.append(
                    "enum "
                    + getAllowedName(node.name)
                    + "Values{"
                    + str(",".join(get_allowed_enum_literal(item) for item in allowed))
                    + "};"
                )
                enum_created = True
                idl_file_buffer.append("};")
                allowed_values = str(allowed)
            else:
                print(
                    f"Warning: VSS2IDL can only handle allowed values for string type, "
                    f"signal {node.name} has type {datatype}"
                )

        idl_file_buffer.append("struct " + getAllowedName(node.name))
        idl_file_buffer.append("{")
        if generate_uuid:
            idl_file_buffer.append("string uuid;")
        # fetching value of datatype and obtaining the equivalent DDS type
        try:
            if datatype:
                if datatype in dataTypesMap_covesa_dds:
                    datatype = str(dataTypesMap_covesa_dds[datatype])
                elif "[" in datatype:
                    nodevalueArray = datatype.split("[", 1)
                    if str(nodevalueArray[0]) in dataTypesMap_covesa_dds:
                        datatype = str(dataTypesMap_covesa_dds[str(nodevalueArray[0])])
                        arraysize = "[" + str(arraysize) + nodevalueArray[1]
                else:  # no primitive type. this is custom
                    datatype = datatype.replace(".", "::")  # custom data type

        except AttributeError:
            pass
        # fetching value of unit
        unit = getattr(node.data, "unit")
        min = getattr(node.data, "min")
        max = getattr(node.data, "max")

        default = getattr(node.data, "default")
        if default:
            if isinstance(default, str) and not enum_created:
                default = '"' + default + '"'

        if datatype is not None:
            # adding range if min and max are specified in vspec file
            if min is not None and max is not None and generate_all_idl_features:
                idl_file_buffer.append("@range(min=" + str(min) + " ,max=" + str(max) + ")")

            if allowed_values is None:
                if default is None:
                    idl_file_buffer.append(
                        ("sequence<" + datatype + "> value" if arraysize is not None else datatype + " value") + ";"
                    )
                else:
                    # default values in IDL file are not accepted by CycloneDDS/FastDDS :
                    # these values can be generated if --all-idl-features is set as True
                    idl_file_buffer.append(
                        ("sequence<" + datatype + "> value" if arraysize is not None else datatype + " value")
                        + ("  default " + str(default) if generate_all_idl_features else "")
                        + ";"
                    )
            else:
                # this is the case where allowed values are provided, accordingly contents are converted to enum
                if default is None:
                    idl_file_buffer.append(
                        getAllowedName(node.name) + "_M::" + getAllowedName(node.name) + "Values value;"
                    )
                else:
                    # default values in IDL file are not accepted by CycloneDDS/FastDDS :
                    # these values can be generated if --all-idl-features is set as True
                    idl_file_buffer.append(
                        getAllowedName(node.name)
                        + "_M::"
                        + getAllowedName(node.name)
                        + "Values value"
                        + (" " + str(default) if generate_all_idl_features else "")
                        + ";"
                    )

        if unit is not None:
            idl_file_buffer.append(("" if generate_all_idl_features else "//") + 'const string unit="' + unit + '";')

        data = node.get_vss_data()
        idl_file_buffer.append(
            ("" if generate_all_idl_features else "//") + 'const string type ="' + str(data.type.value) + '";'
        )

        idl_file_buffer.append(
            ("" if generate_all_idl_features else "//") + 'const string description="' + data.description + '";'
        )
        idl_file_buffer.append("};")


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

    def export_data_type_node(self, node: VSSNode):
        """
        This method is used to traverse VSS node and to create corresponding DDS IDL buffer string
        """

        prefix = ""
        suffix = ""
        if isinstance(node.data, VSSDataBranch):
            prefix = f"module {getAllowedName(node.name)}" + " {\n"
            suffix = "};\n"
        elif isinstance(node.data, VSSDataStruct):
            # check if the properties use structs that have not been seen before
            # if not, add a forward declaration
            fwds = []
            for c in node.children:
                datatype = getattr_nn(c.data, "datatype", "")
                if not datatype.startswith("Types."):
                    continue

                datatype_str = datatype(".", "::").split("[", 1)[0]
                if datatype_str not in self.structs_seen:
                    base_type = datatype_str.split("::")[-1]
                    fwds.append(base_type)

            fwds.sort()
            for f in set(fwds):
                prefix += f"struct {f};\n"

            prefix += f"struct {getAllowedName(node.name)}" + " {\n"
            suffix = "};\n"
            self.structs_seen.append(node.get_fqn("::").split("[", 1)[0])
        else:
            datatype = getattr_nn(node.data, "datatype", "")
            datatype_str = datatype.replace(".", "::").split("[", 1)[0]
            is_seq = "[" in datatype
            if is_seq:
                self.str_buf += f"sequence<{datatype_str}> {getAllowedName(node.name)};\n"
            else:
                self.str_buf += f"{datatype_str} {getAllowedName(node.name)};\n"

        self.str_buf += f"{prefix}"

        for child in node.children:
            self.export_data_type_node(child)
        self.str_buf += suffix


def export_idl(file, root, generate_uuids=True, generate_all_idl_features=False):
    """This method is used to traverse through the root VSS node to build
    -> DDS IDL equivalent string buffer and to serialize it acccordingly into a file
    """
    export_node(root, generate_uuids, generate_all_idl_features)
    file.write("\n".join(idl_file_buffer))
    log.info("IDL file generated at location : " + file.name)


@click.command()
@clo.vspec_opt
@clo.output_required_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.uuid_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@click.option(
    "--all-idl-features",
    is_flag=True,
    help="Generate all features based on DDS IDL 4.2 Spec",
)
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    uuid: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    all_idl_features: bool,
):
    """
    Export as DDSIDL.
    """
    tree, datatype_tree = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        uuid=uuid,
        quantities=quantities,
        units=units,
        types=types,
        overlays=overlays,
    )
    log.info("Generating DDS-IDL output...")

    if datatype_tree is not None:
        exporter = StructExporter()
        with open(output, "w") as idl_out:
            idl_out.write(exporter.export(datatype_tree))

    with open(output, "a" if datatype_tree is not None else "w") as idl_out:
        export_idl(
            idl_out,
            tree,
            uuid,
            all_idl_features,
        )

# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to ApiGear


import abc
import os
import typing
import rich_click as click
import vss_tools.vspec.cli_options as clo

from enum import Enum, Flag, auto
from vss_tools import log
from vss_tools.vspec.model.vsstree import VSSNode, VSSType
from vss_tools.vspec.model.constants import VSSDataType
from vss_tools.vspec.vssexporters.utils import get_trees
from pathlib import Path

SOLUTION_FILENAME = "{}.solution.yaml"
SOLUTION_TEMPLATE_START =\
    """schema: \"apigear.solution/1.0\"
name: {}
version: \"1.0\"

layers:
"""
SOLUTION_TEMPLATE_LAYER_UNREAL =\
    """  - name: unreal
    inputs:
      - {module_name}
    output: {output_path}
    template: apigear-io/template-unreal
"""
SOLUTION_TEMPLATE_LAYER_CPP =\
    """  - name: cpp
    inputs:
      - {module_name}
    output: {output_path}
    template: apigear-io/template-cpp14
    features:
      - examples_olink
"""
SOLUTION_TEMPLATE_LAYER_QT5 =\
    """  - name: qt5
    inputs:
      - {module_name}
    output: {output_path}
    template: apigear-io/template-qt5
"""
SOLUTION_TEMPLATE_LAYER_QT6 =\
    """  - name: qt6
    inputs:
      - {module_name}
    output: {output_path}
    template: apigear-io/template-qtcpp
"""
MODULE_FILENAME = "{}.module.yaml"
MODULE_TEMPLATE_START =\
    """schema: apigear.module/1.0
name: {}
version: \"1.0\"

"""


class SolutionLayers(Flag):
    UNREAL = auto()
    CPP = auto()
    QT5 = auto()
    QT6 = auto()


class ApiGearBasicType(Enum):
    BOOL = "bool"
    INT32 = "int32"
    INT64 = "int64"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    STRING = "string"


class ApiGearComplexType(abc.ABC):
    def __init__(self, name):
        super().__init__()

        self.name = name


class ApiGearStructure(ApiGearComplexType):
    def __init__(self, name: str):
        super().__init__(name)

        self.properties: typing.Dict[str, ApiGearProperty] = {}


class ApiGearEnumeration(ApiGearComplexType):
    def __init__(self, name: str):
        super().__init__(name)

        # TODO: allow using custom values for variants?
        self.variants: typing.List[str] = []


class ApiGearType():
    def __init__(self, type: str):
        super().__init__()

        self.is_array = False
        self.type = type

    @classmethod
    def array(cls, type: str):
        t = cls(type)
        t.is_array = True
        return t


class ApiGearProperty():
    def __init__(self, type: ApiGearType):
        super().__init__()

        self.type = type
        self.description: typing.Optional[str] = None


class ApiGearInterface:
    def __init__(self, name: str):
        super().__init__()

        self.name: str = name
        self.properties: typing.Dict[str, ApiGearProperty] = {}

        # TODO: implement handling for operations
        # self.operations

        # TODO: implement handling for signals
        # self.signals


class ApiGearModule:
    def __init__(self):
        super().__init__()

        self.interfaces: typing.List[ApiGearInterface] = []
        self.enumerations: typing.List[ApiGearEnumeration] = []
        self.structures: typing.List[ApiGearStructure] = []


def get_allowed_enum_literal(name: str) -> str:
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


def get_apigear_datatype(t: str) -> typing.Optional[ApiGearType]:
    is_array = False
    apigear_type = None
    if t.endswith("[]"):
        is_array = True
        t = t[0:-2]

    if t in ["int8", "int16", "int32", "uint8", "uint16", "uint32"]:
        apigear_type = ApiGearType(ApiGearBasicType.INT32.value)
    elif t in ["int64", "uint64"]:
        apigear_type = ApiGearType(ApiGearBasicType.INT64.value)
    elif t == "float":
        apigear_type = ApiGearType(ApiGearBasicType.FLOAT32.value)
    elif t == "double":
        apigear_type = ApiGearType(ApiGearBasicType.FLOAT64.value)
    elif t == "boolean":
        apigear_type = ApiGearType(ApiGearBasicType.BOOL.value)
    elif t == "string":
        apigear_type = ApiGearType(ApiGearBasicType.STRING.value)
    else:
        apigear_type = ApiGearType(t.replace(".", "_"))

    if is_array and apigear_type is not None:
        apigear_type.is_array = True

    return apigear_type


def node_name(node: VSSNode) -> str:
    return node.qualified_name().replace(".", "_")


def export_node(node: VSSNode, module: ApiGearModule, interface: ApiGearInterface = None):
    log.debug(f"Node {node.qualified_name()}")
    if node.type == VSSType.BRANCH:
        new_interface_name = node_name(node)
        new_interface = ApiGearInterface(new_interface_name)
        module.interfaces.append(new_interface)

        for child in node.children:
            export_node(child, module, new_interface)
    else:
        if node.allowed != "":
            if (node.datatype in [VSSDataType.STRING, VSSDataType.STRING_ARRAY]):
                enum_name = f"{node_name(node)}_Value"
                enum = ApiGearEnumeration(enum_name)
                log.debug(f"Creating a new enum: {enum_name}")

                for element in node.allowed:
                    variant = get_allowed_enum_literal(element)
                    enum.variants.append(variant)
                    log.debug(f"  New variant: {variant}")

                property = ApiGearProperty(ApiGearType(enum_name))
                if node.description != "":
                    property.description = node.description
                interface.properties[node.name] = property
                module.enumerations.append(enum)
            else:
                log.warning(f"Warning: VSS2Apigear can only handle allowed values for string type, "
                            f"signal {node.name} has type {node.datatype.value}")
        else:
            if node.has_datatype():
                type = get_apigear_datatype(node.datatype.value)

                if type is None:
                    log.warning(f"Datatype {node.datatype.value} of node {node.name} currently not supported")
                    return

                property = ApiGearProperty(type)
                if node.description != "":
                    property.description = node.description
                interface.properties[node.name] = property
            else:
                if hasattr(node, "data_type_str"):
                    type = get_apigear_datatype(node.data_type_str)

                    if type is None:
                        log.warning(f"Datatype {node.data_type_str} of node {node.name} currently not supported")
                        return

                    property = ApiGearProperty(type)
                    if node.description != "":
                        property.description = node.description
                    interface.properties[node.name] = property
                else:
                    log.warning(f"Node {node.qualified_name()} does not have a datatype")


def export_data_type_node(node: VSSNode, module: ApiGearModule, structure: ApiGearStructure = None):
    """This method is used to traverse through the root VSS Data Types node to build
       -> ApiGear equivalent string buffer and to serialize it accordingly into a module
    """
    if node is None:
        return

    log.debug(f"Node [{node.type}] {node.qualified_name()}")

    if node.type == VSSType.BRANCH:
        for child in node.children:
            export_data_type_node(child, module)
    elif node.type == VSSType.STRUCT:
        struct_name = node_name(node)
        struct = ApiGearStructure(struct_name)
        log.debug(f"Creating a new structure {struct_name}")

        for child in node.children:
            export_data_type_node(child, module, struct)

        module.structures.append(struct)
    else:
        if node.has_datatype():
            type = get_apigear_datatype(node.datatype.value)

            if type is None:
                log.warning(f"Datatype {node.datatype.value} of node {node.name} currently not supported")
                return

            property = ApiGearProperty(type)
            if node.description != "":
                property.description = node.description
            structure.properties[node.name] = property
        else:
            if hasattr(node, "data_type_str"):
                type = get_apigear_datatype(node.data_type_str)

                if type is None:
                    log.warning(f"Datatype {node.data_type_str} of node {node.name} currently not supported")
                    return

                property = ApiGearProperty(type)
                if node.description != "":
                    property.description = node.description
                structure.properties[node.name] = property
            else:
                log.warning(f"Node {node.qualified_name()} does not have a datatype")


def generate_solution(directory: Path, module_filename: str, module_name: str,
                      layers: typing.Dict[SolutionLayers, str]):
    log.info("Generating solution file")

    path = os.path.join(directory, SOLUTION_FILENAME.format(module_name))
    file = open(path, "w")

    file.write(SOLUTION_TEMPLATE_START.format(module_name))

    if (SolutionLayers.UNREAL in layers):
        file.write(SOLUTION_TEMPLATE_LAYER_UNREAL
                   .format(module_name=module_filename, output_path=layers[SolutionLayers.UNREAL]))
    if (SolutionLayers.CPP in layers):
        file.write(SOLUTION_TEMPLATE_LAYER_CPP
                   .format(module_name=module_filename, output_path=layers[SolutionLayers.CPP]))
    if (SolutionLayers.QT5 in layers):
        file.write(SOLUTION_TEMPLATE_LAYER_QT5
                   .format(module_name=module_filename, output_path=layers[SolutionLayers.QT5]))
    if (SolutionLayers.QT6 in layers):
        file.write(SOLUTION_TEMPLATE_LAYER_QT6
                   .format(module_name=module_filename, output_path=layers[SolutionLayers.QT6]))

    log.info("Solution file generated at location : " + path)


def generate_module(file, module: ApiGearModule, module_name: str):
    file.write(MODULE_TEMPLATE_START.format(module_name))
    file.write("interfaces:\n")

    for interface in module.interfaces:
        if len(interface.properties) == 0:
            continue

        file.write(f"  - name: {interface.name}\n")
        file.write("    properties:\n")

        for prop_key, prop_value in interface.properties.items():
            file.write(f"      - name: {prop_key}\n")
            if prop_value.description is not None:
                file.write(f"        description: \"{prop_value.description}\"\n")
            file.write(f"        type: {prop_value.type.type}\n")
            if prop_value.type.is_array:
                file.write("        array: true\n")

    if len(module.enumerations) > 0:
        file.write("\n")
        file.write("enums:\n")

        for enumeration in module.enumerations:
            file.write(f"  - name: {enumeration.name}\n")
            file.write("    members:\n")

            for variant in enumeration.variants:
                file.write(f"      - name: {variant}\n")

    if len(module.structures) > 0:
        file.write("\n")
        file.write("structs:\n")

        for structure in module.structures:
            file.write(f"  - name: {structure.name}\n")
            file.write("    fields:\n")

            for prop_key, prop_value in structure.properties.items():
                file.write(f"      - name: {prop_key}\n")
                if prop_value.description is not None:
                    file.write(f"        description: \"{prop_value.description}\"\n")
                file.write(f"        type: {prop_value.type.type}\n")
                if prop_value.type.is_array:
                    file.write("        array: true\n")


def export_apigear(directory: Path, root: VSSNode, data_type_tree: VSSNode | None,
                   layers: typing.Dict[SolutionLayers, str]):
    """This method is used to traverse through the root VSS node to build
       -> ApiGear equivalent string buffer and to serialize it accordingly into a file
    """
    module = ApiGearModule()
    module_name = root.name
    module_filename = MODULE_FILENAME.format(module_name)
    module_path = os.path.join(directory, module_filename)

    log.info(f"directory: {directory}")
    log.info(f"Module name: {module_name}")
    log.info(f"Module filename: {module_filename}")
    log.info(f"Module Path: {module_path}")

    if (not layers):
        layers = {SolutionLayers.CPP: "../cppservice"}
        log.warning(f"No layers provided! Defaulting to CPP in {layers[SolutionLayers.CPP]}")

    log.debug(layers)

    export_node(root, module)
    export_data_type_node(data_type_tree, module)
    generate_solution(directory, module_filename, module_name, layers)
    with open(module_path, "w") as file:
        generate_module(file, module, module_name)
        log.info(f"Generated module file at {module_path}")

    log.info("Apigear files generated at location : " + file.name)


@click.command()
@clo.vspec_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.uuid_opt
@clo.expand_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@clo.types_output_opt
@click.option(
    "--output-dir",
    required=True,
    type=click.Path(file_okay=False, readable=True, writable=True, path_type=Path),
    help="Output directory for the solution and module files",
)
@click.option(
    "--apigear-template-unreal-path",
    type=click.Path(file_okay=False, readable=True, writable=True, path_type=Path),
    help="Add Unreal layer to solution file at the specified path",
)
@click.option(
    "--apigear-template-cpp-path",
    type=click.Path(file_okay=False, readable=True, writable=True, path_type=Path),
    help="Add Cpp14 layer to solution file at the specified path",
)
@click.option(
    "--apigear-template-qt5-path",
    type=click.Path(file_okay=False, readable=True, writable=True, path_type=Path),
    help="Add Qt5 layer to solution file at the specified path",
)
@click.option(
    "--apigear-template-qt6-path",
    type=click.Path(file_okay=False, readable=True, writable=True, path_type=Path),
    help="Add Qt6 layer to solution file at the specified path",
)
def cli(
    vspec: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    uuid: bool,
    expand: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    types_output: Path,
    output_dir: Path,
    apigear_template_unreal_path: Path,
    apigear_template_cpp_path: Path,
    apigear_template_qt5_path: Path,
    apigear_template_qt6_path: Path,
):
    """
    Export as ApiGear.
    """
    tree, data_type_tree = get_trees(
        include_dirs,
        aborts,
        strict,
        extended_attributes,
        uuid,
        quantities,
        vspec,
        units,
        types,
        types_output,
        overlays,
        expand,
    )
    log.info("Generating ApiGear output...")
    if output_dir.exists():
        log.error("Directory already exists. Aborting..")
        return
    output_dir.mkdir(exist_ok=True, parents=True)

    layers = {}
    if (apigear_template_unreal_path is not None):
        layers[SolutionLayers.UNREAL] = apigear_template_unreal_path
    if (apigear_template_cpp_path is not None):
        layers[SolutionLayers.CPP] = apigear_template_cpp_path
    if (apigear_template_qt5_path is not None):
        layers[SolutionLayers.QT5] = apigear_template_qt5_path
    if (apigear_template_qt6_path is not None):
        layers[SolutionLayers.QT6] = apigear_template_qt6_path

    export_apigear(output_dir, tree, data_type_tree, layers)

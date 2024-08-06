# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to ApiGear


import abc
import typing
import yaml
import rich_click as click
import vss_tools.vspec.cli_options as clo

from enum import Enum, Flag, auto
from vss_tools import log
from vss_tools.vspec.tree import VSSNode
from vss_tools.vspec.model import VSSDataBranch, VSSDataStruct, VSSDataDatatype
from vss_tools.vspec.datatypes import Datatypes
from vss_tools.vspec.main import get_trees
from pathlib import Path
from math import inf


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

        self.variants: typing.List[tuple[str, int | None]] = []


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

        """
        All the defined types by VSS are best described with ApiGear properties.
        The VSS specification doesn't provide any types that can be translated into ApiGear operations,
        (which are functions that may be executed on the interface), or ApiGear signals (which are more like events).
        """


class ApiGearModule:
    def __init__(self):
        super().__init__()

        self.interfaces: typing.List[ApiGearInterface] = []
        self.enumerations: typing.List[ApiGearEnumeration] = []
        self.structures: typing.List[ApiGearStructure] = []


def starts_with_number(name: str) -> bool:
    return name[0].isdigit()


def hex_to_dec(number: str) -> int | None:
    if starts_with_number(number):
        try:
            return int(number, 16)
        except ValueError:
            return None
    return None


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
    if starts_with_number(name):
        return "d" + name.replace(".", "_")
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
    data = node.get_vss_data()
    name = node.get_fqn("_")
    if data.deprecation:
        return f"{name}_Deprecated"
    else:
        return name


def generate_property(node: VSSNode, datatype: str) -> ApiGearProperty | None:
    apigear_type = get_apigear_datatype(datatype)
    data = node.get_vss_data()

    if apigear_type is None:
        log.warning(f"Datatype {datatype} of node {node.name} currently not supported")
        return None

    property = ApiGearProperty(apigear_type)
    if data.description != "":
        property.description = data.description
    return property


def export_node(node: VSSNode, module: ApiGearModule, interface: ApiGearInterface | None = None):
    log.debug(f"Node {node.get_fqn()}")
    data = node.get_vss_data()
    name = f"{node.name}_Deprecated" if data.deprecation else node.name
    if data.deprecation:
        log.info(f"Node name {node.name} changed to {name} as its deprecated, reason: {data.deprecation}")
    if isinstance(node.data, VSSDataBranch):
        new_interface_name = node_name(node)
        new_interface = ApiGearInterface(new_interface_name)
        module.interfaces.append(new_interface)

        for child in node.children:
            export_node(child, module, new_interface)
    else:
        allowed = getattr(data, "allowed")
        if allowed:
            enum_name = f"{node_name(node)}_Value"
            enum = ApiGearEnumeration(enum_name)
            log.debug(f"Creating a new enum: {enum_name}")

            for element in allowed:
                element_str = str(element)
                element_dec = hex_to_dec(element_str)
                variant = get_allowed_enum_literal(element_str)
                log.debug(f"  New variant: {variant}")
                datatype = getattr(data, "datatype")
                if datatype == Datatypes.FLOAT[0]:
                    enum.variants.append((variant, None))
                else:
                    enum.variants.append((variant, element_dec))

            property = ApiGearProperty(ApiGearType(enum_name))
            if data.description != "":
                property.description = data.description
            if interface is not None:
                interface.properties[name] = property
                module.enumerations.append(enum)
        elif isinstance(node.data, VSSDataDatatype):
            datatype = getattr(data, "datatype")
            prop = generate_property(node, datatype)
            if prop is not None and interface is not None:
                interface.properties[name] = prop


def export_data_type_node(node: VSSNode | None, module: ApiGearModule, structure: ApiGearStructure | None = None):
    """This method is used to traverse through the root VSS Data Types node to build
       -> ApiGear equivalent string buffer and to serialize it accordingly into a module
    """
    if node is None:
        return

    data = node.get_vss_data()
    log.debug(f"Node [{data.type}] {node.get_fqn()}")
    name = f"{node.name}_Deprecated" if data.deprecation else node.name
    if data.deprecation:
        log.info(f"Node name {node.name} changed to name as its deprecated, reason: {data.deprecation}")

    if isinstance(node.data, VSSDataBranch):
        for child in node.children:
            export_data_type_node(child, module)
    elif isinstance(node.data, VSSDataStruct):
        struct_name = node_name(node)
        struct = ApiGearStructure(struct_name)
        log.debug(f"Creating a new structure {struct_name}")

        for child in node.children:
            export_data_type_node(child, module, struct)

        module.structures.append(struct)
    elif isinstance(node.data, VSSDataDatatype):
        datatype = getattr(data, "datatype")
        prop = generate_property(node, datatype)
        if prop is not None and structure is not None:
            structure.properties[name] = prop


def generate_module(directory: Path, module: ApiGearModule, module_name: str, module_filename: str):
    log.debug("Generating module file")

    yaml_dict: typing.Dict[str, typing.Any] = {
        "schema": "apigear.module/1.0",
        "name": module_name,
        "version": "1.0",
        "interfaces": []
    }

    for interface in module.interfaces:
        if len(interface.properties) == 0:
            continue

        interface_yaml: typing.Dict[str, typing.Any] = {
            "name": interface.name,
            "properties": [],
        }

        for prop_key, prop_value in interface.properties.items():
            property_yaml: typing.Dict[str, typing.Any] = {
                "name": prop_key,
                "type": prop_value.type.type,
            }
            if prop_value.description is not None:
                property_yaml["description"] = prop_value.description
            if prop_value.type.is_array:
                property_yaml["array"] = True
            interface_yaml["properties"].append(property_yaml)

        yaml_dict["interfaces"].append(interface_yaml)

    if len(module.enumerations) > 0:
        yaml_dict["enums"] = []

        for enumeration in module.enumerations:
            enum_yaml: typing.Dict[str, typing.Any] = {
                "name": enumeration.name,
                "members": [],
            }

            for variant, value in enumeration.variants:
                member_yaml: typing.Dict[str, typing.Any] = {
                    "name": variant,
                }
                if value is not None:
                    member_yaml["value"] = value
                enum_yaml["members"].append(member_yaml)

            yaml_dict["enums"].append(enum_yaml)

    if len(module.structures) > 0:
        yaml_dict["structs"] = []

        for structure in module.structures:
            struct_yaml: typing.Dict[str, typing.Any] = {
                "name": structure.name,
                "fields": [],
            }

            for prop_key, prop_value in structure.properties.items():
                field_yaml: typing.Dict[str, typing.Any] = {
                    "name": prop_key,
                    "type": prop_value.type.type,
                }
                if prop_value.description is not None:
                    field_yaml["description"] = prop_value.description
                if prop_value.type.is_array:
                    field_yaml["array"] = True
                struct_yaml["fields"].append(field_yaml)

            yaml_dict["structs"].append(struct_yaml)

    module_path = directory / module_filename
    export_yaml(module_path, yaml_dict)
    log.info(f"Module file generated at location: {module_path}")


def generate_solution(directory: Path, module_filename: str, module_name: str,
                      layers: typing.Dict[SolutionLayers, Path]):
    log.debug("Generating solution file")

    yaml_dict: typing.Dict[str, typing.Any] = {
        "schema": "apigear.solution/1.0",
        "name": module_name,
        "version": "1.0",
        "layers": []
    }
    unreal: typing.Dict[str, typing.Any] = {
        "name": "unreal",
        "inputs": [module_filename],
        "template": "apigear-io/template-unreal",
        "features": ["stubs", "plugin"],
    }
    cpp14: typing.Dict[str, typing.Any] = {
        "name": "cpp",
        "inputs": [module_filename],
        "template": "apigear-io/template-cpp14",
        "features": ["stubs"],
    }
    qt5: typing.Dict[str, typing.Any] = {
        "name": "qt5",
        "inputs": [module_filename],
        "template": "apigear-io/template-qt5",
        "features": ["stubs", "qmlplugin"],
    }
    qt6: typing.Dict[str, typing.Any] = {
        "name": "qt6",
        "inputs": [module_filename],
        "template": "apigear-io/template-qtcpp",
        "features": ["stubs", "qmlplugin"],
    }
    for solution in layers:
        match solution:
            case SolutionLayers.UNREAL:
                unreal["output"] = layers[solution].name
                yaml_dict["layers"].append(unreal)
            case SolutionLayers.CPP:
                cpp14["output"] = layers[solution].name
                yaml_dict["layers"].append(cpp14)
            case SolutionLayers.QT5:
                qt5["output"] = layers[solution].name
                yaml_dict["layers"].append(qt5)
            case SolutionLayers.QT6:
                qt6["output"] = layers[solution].name
                yaml_dict["layers"].append(qt6)

    solution_filename = f"{module_name}.solution.yaml"
    solution_path = directory / solution_filename
    export_yaml(solution_path, yaml_dict)
    log.info(f"Solution file generated at location: {solution_path}")


def export_yaml(file_name, content_dict):
    with open(file_name, "w") as f:
        yaml.dump(
            content_dict,
            f,
            sort_keys=False,
            width=inf,
            indent=2,
            encoding="utf-8",
            allow_unicode=True,
        )


def export_apigear(directory: Path, root: VSSNode, data_type_tree: VSSNode | None,
                   layers: typing.Dict[SolutionLayers, Path]):
    """This method is used to traverse through the root VSS node to build
       -> ApiGear equivalent string buffer and to serialize it accordingly into a file
    """
    module = ApiGearModule()
    module_name = root.name
    module_filename = f"{module_name}.module.yaml"

    log.debug(f"Directory: {directory}")
    log.debug(f"Module name: {module_name}")
    log.debug(f"Module filename: {module_filename}")

    if (not layers):
        layers = {SolutionLayers.CPP: Path("./cppservice")}
        log.warning(f"No layers provided! Defaulting to CPP in {layers[SolutionLayers.CPP]}")

    log.debug(layers)

    export_node(root, module)
    export_data_type_node(data_type_tree, module)
    generate_solution(directory, module_filename, module_name, layers)
    generate_module(directory, module, module_name, module_filename)
    log.info(f"Apigear files generated at location: {directory}")


@click.command()
@clo.vspec_opt
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
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    output_dir: Path,
    apigear_template_unreal_path: Path,
    apigear_template_cpp_path: Path,
    apigear_template_qt5_path: Path,
    apigear_template_qt6_path: Path,
):
    """
    Export to ApiGear.
    """
    tree, data_type_tree = get_trees(
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

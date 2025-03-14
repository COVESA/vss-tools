# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import json
import logging
import re
import sys
import textwrap
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

from vss_tools.model import NodeType
from vss_tools.tree import VSSNode
from vss_tools.utils.misc import getattr_nn
from vss_tools.utils.vhal.property_constants import (
    VehiclePropertyAccess,
    VehiclePropertyChangeMode,
    VhalAreaType,
    VhalPropertyGroup,
    VSSDatatypesToVhal,
)
from vss_tools.utils.vhal.vehicle_mapping import VehicleMappingItem


class VhalMapper:
    """
    VSS to Android VHAL properties mapper.

    :param include_new: Whether new VSS nodes, not previously present in the mapping file, should be added.
    :param group: Android VHAL property group. See
                 https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyGroup.aidl
                 a custom "VSS" group with the number 4 is available for VSS custom namespace.
    :param starting_id: Newly generated VHAL property IDs will start with this number. This applies for the last 2 bytes
                       of the property ID.
    :param override_units: Whether the mapper should override units in the mapping file from the VSS spec.
    :param override_datatype: Whether the mapper should override data types in the mapping file from the VSS spec.
    """

    MAX_VHAL_ID = 65535  # 0xffff, must be in range of 16 bits, defined by Android specs

    def __init__(
        self,
        include_new: bool,
        group: int = 1,
        starting_id: int = 0,
        override_units: bool = False,
        override_datatype: bool = False,
    ):
        self.__group = group
        self.__include_new = include_new
        self.__override_units = override_units
        self.__override_datatype = override_datatype
        self.__property_map: Dict[str, VehicleMappingItem] = {}
        self.__properties_without_source: List[VehicleMappingItem] = []
        self.__properties_with_continuous_change_mode: List[str] = []
        self.__min_vhal_id: int = starting_id
        self.__next_vhal_id: int = starting_id

    def __get_next_vhal_property_id(self, node: VSSNode) -> int:
        """
        Generates static VHAL propertyIds as described here
        https://source.android.com/docs/automotive/vhal/property-configuration

        Android VHAL property ID is composed of unique ID (2bytes), type (1byte), area (1nibble)
        and group (1nibble), e.g.:

            286277632 (0x11104000) = UniqueID (0x00004000) | VehiclePropertyType.STRING (0x00100000) |
                  VehicleArea.GLOBAL (0x01000000) | VehiclePropertyGroup.SYSTEM (0x10000000)

        :param node: VSS node that we want to generate a unique VHAL property ID for.
        :returns: 2 bytes unique ID value for the VSS node.
        """
        node_data = node.get_vss_data()
        datatype = getattr_nn(node_data, "datatype", None)

        if not datatype:
            logging.error(f"Datatype not given for the VSS leaf {node.get_fqn()}")
            sys.exit()

        node_uid = self.__next_vhal_id
        self.__next_vhal_id += 1

        vhal_property_type = VSSDatatypesToVhal.get_property_type_id(datatype)
        vhal_area_type = VhalAreaType.VEHICLE_AREA_TYPE_GLOBAL_AIDL.value
        vhal_property_group = VhalPropertyGroup.get(self.__group).value

        property_id = node_uid | vhal_property_group | vhal_area_type | vhal_property_type

        return property_id

    def __validate_ids(self, mapping: List[VehicleMappingItem]) -> bool:
        """
        Validate IDs against the generator call parameters.

        :param mapping: The generated mapping.
        :returns: True if all IDs are valid, False otherwise.
        """
        total = 0
        valid = 0
        for item in mapping:
            if item.vhalGroup != self.__group:
                logging.error(
                    f"Invalid group {item.vhalGroup} of VSS leaf {item.source}! "
                    f"Group must be in {[self.__group]}! You are probably regenerating a configuration "
                    f"originally generated with a different group."
                )
            if item.vhalId < self.__min_vhal_id or item.vhalId > VhalMapper.MAX_VHAL_ID:
                logging.error(
                    f"Invalid unique ID {item.vhalId} of VSS leaf {item.source}! "
                    f"ID must be in range {[self.__min_vhal_id, VhalMapper.MAX_VHAL_ID]}"
                )
            else:
                valid += 1
            total += 1

        if total != valid:
            logging.error(f"Number of valid IDs {valid} of {total} in total.")
            sys.exit()
        return True

    def load_continuous_list(self, file_path: Path):
        """
        Loads a list of VSS paths which should be considered as continuous change mode.

        :param file_path: Path to the list of VSS paths.
        """
        with open(file_path) as file:
            self.__properties_with_continuous_change_mode = json.load(file)
            logging.info(
                f"Loaded {len(self.__properties_with_continuous_change_mode)} paths to be considered"
                f" as continuous change mode from {file_path}."
            )

    def load(self, file_path: Path, vss_root: VSSNode):
        """
        Loads the mapping file and VSS spec and returns the resulting list of mapping items.

        :param file_path: Path to the mapping file.
        :param vss_root: Root of the VSS tree.
        :returns: List of mapping items.
        """
        if file_path.exists():
            self.load_mapping(file_path)
        self.load_vss_tree(vss_root)
        return self.get()

    def load_mapping(self, file_path: Path) -> Tuple[Dict[str, VehicleMappingItem], List[VehicleMappingItem]]:
        """
        Loads the mapping file and VSS spec and returns the resulting list of mapping items.

        :param file_path: Path to the mapping file.
        :returns: List of mapping items.
        """
        with open(file_path) as file:
            data = [VehicleMappingItem(**item) for item in json.load(file)]
            self.__next_vhal_id = max(list(map(lambda item: item.vhalId + 1, data)) + [self.__next_vhal_id])
            if (
                VhalPropertyGroup.get(self.__group) == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_SYSTEM
                and self.__next_vhal_id < 1000
            ):
                logging.error(
                    f"When generating {VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_SYSTEM} properties starting"
                    f" ID must be greater than 1000 to prevent conflicts with Google defined properties."
                    f" Current start is {self.__min_vhal_id}!"
                )
                sys.exit(1)
            self.__property_map = {item.source: item for item in [item for item in data if item.source != ""]}
            self.__properties_without_source = [item for item in data if item.source == ""]
            for invalid in [item for item in data if item.source == "" and item.formula == ""]:
                logging.warning(f"For standard property {invalid.name} no mapping to VSS was found.")

        return self.__property_map, self.__properties_without_source

    def load_vss_tree(self, node: VSSNode):
        """
        Loads VSS tree into the mapping.
        :param node: Root of the VSS tree.
        """
        if node.is_leaf:
            node_name_flat = node.get_fqn()
            node_data = node.get_vss_data()

            mapping = self.__property_map.get(node_name_flat)
            if mapping or self.__include_new:
                vss_property = VehicleMappingItem(
                    name=mapping.name
                    if mapping
                    else re.sub(
                        r"([a-z])([A-Z])", r"\1_\2", node_name_flat.replace("Vehicle.", "").replace(".", "_")
                    ).upper(),
                    propertyId=mapping.propertyId if mapping else self.__get_next_vhal_property_id(node),
                    areaId=mapping.areaId if mapping else VhalMapper.__get_vhal_vehicle_area_id(node),
                    access=mapping.access if mapping else VhalMapper.__get_vhal_access(node),
                    changeMode=mapping.changeMode if mapping else self.__get_vhal_change_mode(node),
                    unit=mapping.unit
                    if mapping and not self.__override_units
                    else getattr_nn(node_data, "unit", mapping.unit if mapping else ""),
                    source=node_name_flat,
                    formula=mapping.formula if mapping and mapping.formula else None,
                    comment=getattr_nn(node_data, "comment", mapping.comment if mapping and mapping.comment else None),
                    configString=mapping.configString if mapping and mapping.configString else node_data.description,
                    datatype=mapping.datatype
                    if mapping and mapping.datatype and not self.__override_datatype
                    else getattr_nn(node_data, "datatype", None),
                    type=str(node_data.type.value),
                    min=getattr_nn(node_data, "min", None),
                    max=getattr_nn(node_data, "max", None),
                    allowed=mapping.allowed if mapping and mapping.allowed else getattr_nn(node_data, "allowed", None),
                    default=getattr_nn(node_data, "default", None),
                    deprecation=node_data.deprecation,
                )
                self.__property_map[node_name_flat] = vss_property

        for child in node.children:
            self.load_vss_tree(child)

    def get(self) -> List[VehicleMappingItem]:
        """
        Gets the full loaded list of vehicle mapping items properly sorted and validated.
        :returns: List of vehicle mapping items.
        """
        result = sorted(
            [v for v in self.__property_map.values()] + self.__properties_without_source, key=lambda item: item.name
        )
        self.__validate_ids(result)
        return result

    def safe(self, file_path: Path, indent: int = 2):
        """
        Saves the list of mapping items to a mapping json file.

        :param file_path: Path to the mapping json file.
        :param indent: Indentation of the mapping json file.
        """
        result = self.get()
        with open(file_path, "w") as file:
            json.dump(
                [{key: value for key, value in asdict(mapping).items() if value is not None} for mapping in result],
                file,
                indent=indent,
            )

    def generate_java_files(self, output_file_path, permissions_file_path):
        """
        Generates two Java files. First, file with the list of VHAL property IDs and the corresponding constants.
        Second, file with the list of corresponding permissions both read and write.

        :param output_file_path: Output file path.
        :param permissions_file_path: Permissions file path.
        """
        if not output_file_path or not permissions_file_path:
            logging.warning("No Java output file specified. Java properties and permissions are not generated.")
            return

        mapping = self.get()
        java_variables = []

        for item in mapping:
            if item.vhalId > self.__min_vhal_id:
                annotations = []

                if item.access in (VehiclePropertyAccess.READ.value, VehiclePropertyAccess.READ_WRITE.value):
                    annotations.append(
                        f"@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_{item.name}_READ))"
                    )
                if item.access in (VehiclePropertyAccess.WRITE.value, VehiclePropertyAccess.READ_WRITE.value):
                    annotations.append(
                        f"@RequiresPermission.Write(@RequiresPermission(VssPermissions.PERMISSION_VSS_{item.name}_WRITE))"
                    )
                annotations = "\n".join(annotations)

                # JavaDoc
                config_string = item.configString
                lines = textwrap.wrap(config_string, width=120)
                comment_body = (
                    "\n".join(f"\t * {line}" for line in lines)
                    if len(lines) > 1
                    else "".join(f" {line}" for line in lines)
                )
                prefix = "\n" if len(lines) > 1 else ""
                suffix = "\n\t" if len(lines) > 1 else ""
                javadoc = f"\t/**{prefix}{comment_body}{suffix} */\n"

                annotation_line = "\n\t".join(("\t" + annotations).split("\n")) if annotations else ""
                java_variable = (
                    f"{javadoc}{annotation_line}\n\tpublic static final int {item.name} = {item.propertyId};\n"
                )
                java_variables.append(java_variable)

        java_class = "public final class VehiclePropertyIdsVss {\n\n" + "\n".join(java_variables) + "\n}"

        with open(output_file_path, "w") as file:
            file.write(java_class)

        # Permissions
        permissions = []
        for item in mapping:
            if item.vhalId > self.__min_vhal_id:
                if item.access in (VehiclePropertyAccess.READ.value, VehiclePropertyAccess.READ_WRITE.value):
                    permissions.append(
                        f"\tpublic static final String PERMISSION_VSS_{item.name}_READ = "
                        f'"android.car.permission.VSS_{item.name}_READ";'
                    )

                if item.access in (VehiclePropertyAccess.WRITE.value, VehiclePropertyAccess.READ_WRITE.value):
                    permissions.append(
                        f"\tpublic static final String PERMISSION_VSS_{item.name}_WRITE = "
                        f'"android.car.permission.VSS_{item.name}_WRITE";'
                    )

        java_permissions = "\n\n".join(permissions)
        java_permissions_class = f"public final class VssPermissions {{\n\n{java_permissions}\n}}"

        with open(permissions_file_path, "w") as file:
            file.write(java_permissions_class)

    def generate_aidl_file(self, output_filename):
        """
        Generates AIDL file with list of VHAL property IDs.

        :param output_filename: Output file path.
        """
        if not output_filename:
            logging.warning("No AIDL output file specified. AIDL class is not generated.")
            return

        mapping = self.get()
        aidl_variables = []

        for item in mapping:
            if item.vhalId > self.__min_vhal_id:
                vhal_property_group_str = str(VhalPropertyGroup.get(self.__group))
                vhal_area_type_str = str(VhalAreaType.VEHICLE_AREA_TYPE_GLOBAL_AIDL)
                vhal_property_type_str = VSSDatatypesToVhal.get_property_type_repr(item.vhalType << 16)

                aidl_variable = (
                    f"\t{item.name} = "
                    f"{(item.vhalId << 0):#0{6}x} + "
                    f"{(item.vhalGroup << 28):#0{10}x} + "
                    f"{(item.vhalArea << 24):#0{10}x} + \n\t\t\t"
                    f"{(item.vhalType << 16):#0{10}x} "
                    f"// {vhal_property_group_str}, {vhal_area_type_str}, {vhal_property_type_str}"
                )
                aidl_variables.append(aidl_variable)

        aidl_class = "enum VehiclePropertyVss {\n\n" + "\n".join(aidl_variables) + "\n}"

        with open(output_filename, "w") as file:
            file.write(aidl_class)

    @staticmethod
    def __get_vhal_vehicle_area_id(node: VSSNode) -> int:
        """
        Android VHAL area ID is described here:
        https://android.googlesource.com/platform/packages/services/Car/+/refs/heads/main/car-lib/src/android/car/VehicleAreaType.java

        :returns: VHAL Area ID.
        """
        return VhalAreaType.VEHICLE_AREA_TYPE_GLOBAL.value

    @staticmethod
    def __get_vhal_access(node: VSSNode) -> int:
        """
        Get vendor property access mode as defined in Android and VSS specification

        :param node: VSS node (sensor, attribute or actuator).
        :returns: Read for sensor or attribute, read/write for actuator.
        """
        node_data = node.get_vss_data()

        if node_data.type == NodeType.SENSOR or node_data.type == NodeType.ATTRIBUTE:
            access = VehiclePropertyAccess.READ
        elif node_data.type == NodeType.ACTUATOR:
            access = VehiclePropertyAccess.READ_WRITE
        else:
            access = VehiclePropertyAccess.READ
            logging.error(
                f"Node type {node_data.type.value} for node {node.get_fqn()} "
                f"is not one of the types in {[NodeType.ATTRIBUTE.value, NodeType.SENSOR.value, NodeType.ACTUATOR]},"
                f"default access value {access} is set."
            )
        return access

    def __get_vhal_change_mode(self, node: VSSNode) -> int:
        """
        Get vendor property change mode as defined in Android specification. Assumption for VSS sensors: numeric
        datatypes have continuous mode, boolean and string datatypes have on_change mode.

        :param node: sensor, attribute or actuator
        :returns: change mode
        """
        node_data = node.get_vss_data()
        if node_data.type == NodeType.ATTRIBUTE or node_data.type == NodeType.ACTUATOR:
            return VehiclePropertyChangeMode.STATIC.value
        elif node_data.type == NodeType.SENSOR and node.get_fqn() in self.__properties_with_continuous_change_mode:
            return VehiclePropertyChangeMode.CONTINUOUS.value
        elif node_data.type == NodeType.SENSOR:
            return VehiclePropertyChangeMode.ON_CHANGE.value
        else:
            logging.error(
                f"Node type {node_data.type.value} for node {node.get_fqn()} is not one of the types in "
                f"{[NodeType.ATTRIBUTE.value, NodeType.SENSOR.value, NodeType.ACTUATOR]},"
                f"default change mode STATIC is set."
            )
            return VehiclePropertyChangeMode.STATIC.value

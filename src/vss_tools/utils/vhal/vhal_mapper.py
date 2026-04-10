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
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

from pydantic import TypeAdapter

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

        The ID - vspec static UID generator (https://github.com/COVESA/vss-tools/blob/master/docs/id.md) cannot be used
        since it needs 4-bytes.

        :param node: VSS node that we want to generate a unique VHAL property ID for.
        :returns: 2 bytes unique ID value for the VSS node.
        """
        node_data = node.get_vss_data()
        datatype = getattr_nn(node_data, "datatype", None)

        if not datatype:
            raise Exception(f"Datatype not given for the VSS leaf {node.get_fqn()}")

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
            if item.vhal_group != self.__group:
                logging.error(
                    f"Invalid group {item.vhal_group} of VSS leaf {item.source}! "
                    f"Group must be in {[self.__group]}! You are probably regenerating a configuration "
                    f"originally generated with a different group."
                )
            if item.vhal_id < self.__min_vhal_id or item.vhal_id > VhalMapper.MAX_VHAL_ID:
                logging.error(
                    f"Invalid unique ID {item.vhal_id} of VSS leaf {item.source}! "
                    f"ID must be in range {[self.__min_vhal_id, VhalMapper.MAX_VHAL_ID]}"
                )
            else:
                valid += 1
            total += 1

        if total != valid:
            raise Exception(f"Number of valid IDs {valid} of {total} in total.")
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
            data = TypeAdapter(List[VehicleMappingItem]).validate_json(file.read())
            self.__next_vhal_id = max(list(map(lambda item: item.vhal_id + 1, data)) + [self.__next_vhal_id])
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
                if node_data.deprecation:  # ignore deprecated property
                    return

                vss_property = VehicleMappingItem(
                    name=mapping.name
                    if mapping
                    else re.sub(
                        r"([a-z])([A-Z])", r"\1_\2", node_name_flat.replace("Vehicle.", "").replace(".", "_")
                    ).upper(),
                    property_id=mapping.property_id if mapping else self.__get_next_vhal_property_id(node),
                    area_id=mapping.area_id if mapping else self.__get_vhal_vehicle_area_id(node),
                    access=mapping.access if mapping else VhalMapper.__get_vhal_access(node),
                    change_mode=mapping.change_mode if mapping else self.__get_vhal_change_mode(node),
                    unit=mapping.unit
                    if mapping and not self.__override_units
                    else getattr_nn(node_data, "unit", mapping.unit if mapping else ""),
                    source=node_name_flat,
                    formula=mapping.formula if mapping and mapping.formula else None,
                    comment=getattr_nn(node_data, "comment", mapping.comment if mapping and mapping.comment else None),
                    config_string=mapping.config_string if mapping and mapping.config_string else node_data.description,
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
            json_data = TypeAdapter(List[VehicleMappingItem]).dump_json(result, by_alias=True, indent=indent).decode()
            file.write(json_data)

    def generate_java_files(self, output_file_path: Path, permissions_file_path: Path) -> Tuple[str, str]:
        """
        Generates two Java files. First, file with the list of VHAL property IDs and the corresponding constants.
        Second, file with the list of corresponding permissions both read and write.

        :param output_file_path: Output file path.
        :param permissions_file_path: Permissions file path.
        :aconfig_flag_name: Aconfig flag name for custom vendor packages/service/Car module.
        :returns: tuple containing the java code with properties and java code with permissions.
        """
        aconfig_flag_name = "oem_vehicle_property"
        mapping = self.get()
        java_variables = []
        java_head = (
            f"package android.car.oem;\n\n"
            f"import static android.car.feature.Flags.FLAG_{aconfig_flag_name.upper()};\n"
            f"import android.annotation.FlaggedApi;\n"
            f"import android.annotation.RequiresPermission;\n\n"
        )

        for item in mapping:
            if item.vhal_id >= self.__min_vhal_id:
                annotations_list = []

                if item.access in (VehiclePropertyAccess.READ.value, VehiclePropertyAccess.READ_WRITE.value):
                    annotations_list.append(
                        f"@RequiresPermission.Read(@RequiresPermission(OemPermissions.PERMISSION_OEM_{item.name}_READ))"
                    )
                if item.access in (VehiclePropertyAccess.WRITE.value, VehiclePropertyAccess.READ_WRITE.value):
                    annotations_list.append(
                        f"@RequiresPermission.Write(@RequiresPermission(OemPermissions.PERMISSION_OEM_{item.name}_WRITE))"
                    )
                annotations = "\n".join(annotations_list)

                # JavaDoc
                config_string = item.config_string
                lines = textwrap.wrap(config_string, width=120) if config_string else ""
                description = "\n".join(f"\t * {line}" for line in lines)

                access = VehiclePropertyAccess.get_java_doc(item.access)
                area_type = VhalAreaType.get_java_doc(item.area_id)
                change_mode = VehiclePropertyChangeMode.get_java_doc(item.change_mode)
                if item.datatype is not None:
                    type_id = VSSDatatypesToVhal.get_property_type_id(item.datatype)
                    property_type = VSSDatatypesToVhal.get_property_type_repr(type_id).split(".")[1].capitalize()
                else:
                    property_type = "Unknown"

                if item.access in (VehiclePropertyAccess.WRITE.value, VehiclePropertyAccess.READ_WRITE.value):
                    write_permission_str = (
                        f"Dangerous permission "
                        f"{{@link OemPermissions#PERMISSION_OEM_{item.name}_WRITE}} to write property."
                    )
                else:
                    write_permission_str = "Property is not writable"

                comment_body = (
                    f"{description}\n"
                    f"\t * <p>Property Config:\n"
                    f"\t * <ul>\n"
                    f"\t *  <li>{{@link android.car.hardware.CarPropertyConfig#{access}}}\n"
                    f"\t *  <li>{{@link VehicleAreaType#{area_type}}}\n"
                    f"\t *  <li>{{@link android.car.hardware.CarPropertyConfig#{change_mode}}}\n"
                    f"\t *  <li>{{@code {property_type}}} property type\n"
                    f"\t * </ul>\n"
                    f"\t *\n"
                    f"\t * <p>Required Permissions:\n"
                    f"\t * <ul>\n"
                    f"\t *  <li>Dangerous permission "
                    f"{{@link OemPermissions#PERMISSION_OEM_{item.name}_READ}} to read property.\n"
                    f"\t *  <li>{write_permission_str}\n"
                    f"\t * </ul>\n"
                )
                javadoc = f"\t/**\n{comment_body}\t */\n"

                annotation_line = "\n\t".join(("\t" + annotations).split("\n")) if annotations else ""
                java_variable = (
                    f"{javadoc}"
                    f"\t@FlaggedApi(FLAG_{aconfig_flag_name.upper()})\n"
                    f"{annotation_line}\n\tpublic static final int {item.name} = {item.property_id};\n"
                )
                java_variables.append(java_variable)

        java_class = "public final class VehiclePropertyIdsOem {\n\n" + "\n".join(java_variables) + "\n}"
        java_file = java_head + java_class

        with open(output_file_path, "w") as file:
            file.write(java_file)

        # Permissions
        permissions = []

        permissions_head = (
            f"package android.car.oem;\n\n"
            f"import static android.car.feature.Flags.FLAG_{aconfig_flag_name.upper()};\n"
            f"import android.annotation.SuppressLint;\n"
            f"import android.annotation.FlaggedApi;\n\n"
        )

        for item in mapping:
            if item.vhal_id >= self.__min_vhal_id:
                # Suppress false positive errors in AOSP
                false_positive_errors = ["ACTION", "EXTRA"]

                if any(err in item.name for err in false_positive_errors):
                    suppress_errors = (
                        '\t@SuppressLint("IntentName")  '
                        "// Suppress AOSP false positives for names containing ACTION or EXTRA.\n"
                    )
                else:
                    suppress_errors = ""

                if item.access in (VehiclePropertyAccess.READ.value, VehiclePropertyAccess.READ_WRITE.value):
                    permissions.append(
                        f"{suppress_errors}"
                        f"\t@FlaggedApi(FLAG_{aconfig_flag_name.upper()})\n"
                        f"\tpublic static final String PERMISSION_OEM_{item.name}_READ = "
                        f'"android.car.permission.oem.{item.name}_READ";'
                    )

                if item.access in (VehiclePropertyAccess.WRITE.value, VehiclePropertyAccess.READ_WRITE.value):
                    permissions.append(
                        f"{suppress_errors}"
                        f"\t@FlaggedApi(FLAG_{aconfig_flag_name.upper()})\n"
                        f"\tpublic static final String PERMISSION_OEM_{item.name}_WRITE = "
                        f'"android.car.permission.oem.{item.name}_WRITE";'
                    )

        java_permissions = "\n\n".join(permissions)
        java_permissions_class = f"public final class OemPermissions {{\n\n{java_permissions}\n}}"
        java_permissions_file = permissions_head + java_permissions_class

        with open(permissions_file_path, "w") as file:
            file.write(java_permissions_file)

        return java_file, java_permissions_file

    def generate_aidl_file(self, output_filename: Path, property_version: int = 1) -> str:
        """
        Generates AIDL file with list of VHAL property IDs.

        :param output_filename: Output file path.
        :param property_version: Version of the property's AIDL interface.
        :returns: AIDL code.
        """
        mapping = self.get()
        aidl_variables = []

        for item in mapping:
            if item.vhal_id >= self.__min_vhal_id:
                vhal_property_group_str = str(VhalPropertyGroup.get(self.__group))
                vhal_area_type_str = str(VhalAreaType.VEHICLE_AREA_TYPE_GLOBAL)
                vhal_property_type_str = VSSDatatypesToVhal.get_property_type_repr(item.vhal_type << 16)

                # JavaDoc
                description = item.comment
                if description is None:
                    description = item.config_string
                elif not description.endswith("."):
                    description = f"{item.comment}. {item.config_string}"

                lines = textwrap.wrap(description, width=120) if description is not None else []

                comment = "\n".join(f"\t * {line}" for line in lines)
                java_doc = (
                    f"\t/**\n"
                    f"{comment}\n"
                    f"\t *\n"
                    f"\t * @change_mode {str(VehiclePropertyChangeMode(item.change_mode))}\n"
                    f"\t * @access {str(VehiclePropertyAccess(item.access))}\n"
                    f"\t * @version {property_version}\n"
                    f"\t */\n"
                )

                aidl_variable = (
                    f"\t{item.name} = "
                    f"{(item.vhal_id << 0):#0{6}x} + "
                    f"{vhal_property_group_str} + "
                    f"{vhal_area_type_str} + "
                    f"{vhal_property_type_str},\n"
                )

                aidl_variable_with_comment = java_doc + aidl_variable

                aidl_variables.append(aidl_variable_with_comment)

        aidl_head = (
            "package vendor.android.hardware.automotive.vehicle;\n\n"
            "import android.hardware.automotive.vehicle.VehicleArea;\n"
            "import android.hardware.automotive.vehicle.VehiclePropertyType;\n"
            "import android.hardware.automotive.vehicle.VehiclePropertyGroup;\n\n"
        )

        aidl_annotations = "@VintfStability\n" '@Backing(type="int")\n'
        aidl_class = "enum VehiclePropertyOem {\n\n" + "\n".join(aidl_variables) + "\n}"
        aidl_file = aidl_head + aidl_annotations + aidl_class

        with open(output_filename, "w") as file:
            file.write(aidl_file)
        return aidl_file

    def generate_xml_files(self, aosp_workspace_path: Path) -> Tuple[str, str]:
        """
        Generates xml files for car-service. First, file with the new OEM permissions.
        Second, file with the description strings of OEM permissions.

        :param aosp_workspace_path: AOSP workspace directory.
        :returns: A tuple containing an AndroidManifest.xml and strings.xml
        """
        mapping = self.get()
        ANDROID_NS = "http://schemas.android.com/apk/res/android"
        ET.register_namespace("android", ANDROID_NS)
        ET.register_namespace("xliff", "urn:oasis:names:tc:xliff:document:1.2")
        ENCODE_FORMAT = "utf-8"

        # Manifest
        root_manifest = ET.Element("manifest", {"package": "com.android.oem.service", "coreApp": "true"})
        ET.SubElement(root_manifest, "uses-sdk", {f"{{{ANDROID_NS}}}minSdkVersion": "33"})
        ET.SubElement(
            root_manifest,
            "application",
            {
                f"{{{ANDROID_NS}}}label": "@string/app_title",
                f"{{{ANDROID_NS}}}directBootAware": "true",
                f"{{{ANDROID_NS}}}allowBackup": "false",
            },
        )
        tree_manifest = ET.ElementTree(root_manifest)

        # Strings
        root_strings = ET.Element("resources")
        tree_strings = ET.ElementTree(root_strings)
        ET.SubElement(root_strings, "string", {"name": "app_title", "translatable": "false"}).text = "OEM service"

        application_tag = root_manifest.find("application")

        for item in mapping:
            if item.vhal_id >= self.__min_vhal_id:
                access_map = {1: ["read"], 2: ["write"], 3: ["read", "write"]}
                for access in access_map[item.access]:
                    item_name_lower = item.name.lower()
                    # Manifest
                    permission_name = f"android.car.permission.oem.{item.name}_{access.upper()}"
                    permission_desc = f"@string/car_permission_desc_oem_{item_name_lower}_{access}"
                    permission_label = f"@string/car_permission_label_oem_{item_name_lower}_{access}"
                    permission_level = "dangerous"

                    permission_element = ET.Element(
                        "permission",
                        {
                            f"{{{ANDROID_NS}}}name": permission_name,
                            f"{{{ANDROID_NS}}}protectionLevel": permission_level,
                            f"{{{ANDROID_NS}}}label": permission_label,
                            f"{{{ANDROID_NS}}}description": permission_desc,
                        },
                    )

                    if application_tag is None:
                        root_manifest.append(permission_element)
                    else:
                        application_index = list(root_manifest).index(application_tag)
                        root_manifest.insert(application_index, permission_element)

                    # String
                    string_verb = "Read" if access == "read" else "Control"
                    item_name_strings = item_name_lower.split("_is_")
                    item_name_prefix = item_name_strings[0].replace("_", " ")
                    item_name_suffix = f" (is_{item_name_strings[1]})" if len(item_name_strings) > 1 else ""
                    ET.SubElement(
                        root_strings, "string", {"name": f"car_permission_label_oem_{item_name_lower}_{access}"}
                    ).text = f"{string_verb} car\\u2019s state of {item_name_prefix}{item_name_suffix}"
                    ET.SubElement(
                        root_strings, "string", {"name": f"car_permission_desc_oem_{item_name_lower}_{access}"}
                    ).text = f"{string_verb} car\\u2019s state of {item_name_prefix}{item_name_suffix}"

        ET.indent(tree_manifest, space="\n\t")
        manifest_xml_bytes = ET.tostring(root_manifest, encoding=ENCODE_FORMAT, xml_declaration=True)
        manifest_xml_str = manifest_xml_bytes.decode(ENCODE_FORMAT)

        ET.indent(tree_strings, space="\n\t")
        strings_xml_bytes = ET.tostring(root_strings, encoding=ENCODE_FORMAT, xml_declaration=True)
        strings_xml_str = strings_xml_bytes.decode(ENCODE_FORMAT)

        output_manifest_file_path = (
            aosp_workspace_path / "vendor/car/packages/services/Oem/oem-service/AndroidManifest.xml"
        )
        output_strings_file_path = (
            aosp_workspace_path / "vendor/car/packages/services/Oem/oem-service/res/values/strings.xml"
        )
        with open(output_manifest_file_path, "w", encoding=ENCODE_FORMAT) as f:
            f.write(manifest_xml_str + "\n")
        logging.info(f"Written: {output_manifest_file_path}")
        with open(output_strings_file_path, "w", encoding=ENCODE_FORMAT) as f:
            f.write(strings_xml_str + "\n")
        logging.info(f"Written: {output_strings_file_path}")

        return manifest_xml_str, strings_xml_str

    def __get_vhal_vehicle_area_id(self, node: VSSNode) -> int:
        """
        Android VHAL area ID is described here:
        https://android.googlesource.com/platform/packages/services/Car/+/refs/heads/main/car-lib/src/android/car/VehicleAreaType.java
        and
        https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleArea.aidl

        Area type is always generated as GLOBAL. As of now the resulting mapping file needs to be manually edited
        when GLOBAL is not fitting. Consequent runs will keep those edits.

        A detection of area ID based on VSS tree may be implemented in the future.

        Note that for vendor properties the area type VENDOR should be used.

        :returns: VHAL Area ID.
        """
        return (
            VhalAreaType.VEHICLE_AREA_TYPE_VENDOR.value
            if self.__group == 2
            else VhalAreaType.VEHICLE_AREA_TYPE_GLOBAL.value
        )

    @staticmethod
    def __get_vhal_access(node: VSSNode) -> int:
        """
        Get vendor property access mode as defined in Android and VSS specification

        In VSS documentation attributes and sensors have READ access, actuators have READ_WRITE access. Only WRITE
        access was not used in VSS documentation. As a result the properties in mapping will have READ access for VSS
        attributes and sensors, and READ_WRITE for VSS actuators.

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
        Get vendor property change mode as defined in Android specification. VSS attributes and actuators have
        STATIC change mode. Most VSS sensors also to have STATIC change mode except for those sensors, which could be
        mapped to Android properties with CONTINUOUS change mode. What properties should have CONTINUOUS change mode
        must be provided externally.

        :param node: sensor, attribute or actuator
        :returns: change mode
        """
        node_data = node.get_vss_data()
        if node_data.type == NodeType.ATTRIBUTE:
            return VehiclePropertyChangeMode.STATIC.value
        elif (
            node_data.type == NodeType.ACTUATOR or node_data.type == NodeType.SENSOR
        ) and node.get_fqn() in self.__properties_with_continuous_change_mode:
            return VehiclePropertyChangeMode.CONTINUOUS.value
        elif node_data.type == NodeType.ACTUATOR or node_data.type == NodeType.SENSOR:
            return VehiclePropertyChangeMode.ON_CHANGE.value
        else:
            logging.error(
                f"Node type {node_data.type.value} for node {node.get_fqn()} is not one of the types in "
                f"{[NodeType.ATTRIBUTE.value, NodeType.SENSOR.value, NodeType.ACTUATOR]},"
                f"default change mode STATIC is set."
            )
            return VehiclePropertyChangeMode.STATIC.value

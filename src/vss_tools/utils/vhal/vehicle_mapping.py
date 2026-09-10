# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.alias_generators import to_camel

from vss_tools.utils.vhal.property_constants import VhalAreaType, VhalPropertyGroup, VhalPropertyType


class VehicleMappingItem(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    """
    Represents a single vehicle mapping item.

    :param name: Android name of the vehicle property
    :param property_id: Android area ID of the property (https://android.googlesource.com/platform/packages/services/Car/+/refs/heads/main/car-lib/src/android/car/VehicleAreaType.java)
    :param access: See https://source.android.com/docs/automotive/vhal/property-configuration
    :param change_mode: Android change mode for the property (https://developer.android.com/reference/android/car/hardware/CarPropertyConfig#VEHICLE_PROPERTY_CHANGE_MODE_ONCHANGE)
    :param unit: Android property unit
    :param sources: A dictionary mapping a fully-qualified VSS leaf name to its corresponding AOSP Area ID.
                    Example: {"Vehicle.Chassis.Axle.Row1.Wheel.Left.Speed": 1}
    :param formula: For mapping purpose, explains how to map a VSS property to Android property if direct
                    correspondence wasn't found.
    :param comment: Internal comment about current mapping.
    :param config_string: Optional Android string to contain property specific configuration.
    :param type: VSS node type, e.g. actuator, sensor.
    :param min: Minimum allowed value.
    :param max: Maximum allowed value.
    :param allowed:
    :param default: Default value.
    :param deprecation: Whether the VSS node is deprecated or not.
    """

    name: str
    property_id: int
    access: int
    change_mode: int
    unit: str
    sources: Dict[str, int]
    formula: Optional[str] = None
    comment: Optional[str] = None
    config_string: Optional[str] = None

    type: Optional[str] = None
    min: Optional[int] = None
    max: Optional[int] = None
    allowed: Optional[List[str]] = None
    default: Optional[Union[Union[int, str], Union[List[int], List[str]]]] = None
    deprecation: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _derive_sources_from_source_and_area_id(cls, data):
        """
        For backward compatibility: converts obsolete "source" and "areaId" fields into the new "sources" dictionary.
        """
        if not isinstance(data, dict):
            return data

        if "source" in data:
            data["sources"] = {data["source"]: data.get("areaId", 0)}

        return data

    @staticmethod
    def vhal_property_id(
        group: int | VhalPropertyGroup, area_type: int | VhalAreaType, data_type: int | VhalPropertyType, unique_id: int
    ) -> int:
        """
        Construct a VHAL property ID from its components.
        """
        group = VhalPropertyGroup.get(group).value if isinstance(group, int) else group
        area_type = VhalAreaType.get(area_type).value if isinstance(area_type, int) else area_type
        data_type = VhalPropertyType.get(data_type).value if isinstance(data_type, int) else data_type

        return ((group & 0xF) << 28) | ((area_type & 0xF) << 24) | ((data_type & 0xFF) << 16) | (unique_id & 0xFFFF)

    @property
    def vhal_group(self):
        """
        VHAL group component of the property ID.
        - https://source.android.com/docs/automotive/vhal/property-configuration
        - https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleProperty.aidl
        - https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyGroup.aidl
        """
        return (self.property_id & 0xF0000000) >> 28

    @property
    def vhal_area(self):
        """
        VHAL area component of the property ID.
        - https://source.android.com/docs/automotive/vhal/property-configuration
        - https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleProperty.aidl
        - https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleArea.aidl
        - https://cs.android.com/android/platform/superproject/main/+/main:packages/services/Car/car-lib/src/android/car/VehicleAreaType.java?q=vehicleareatype.java&ss=android%2Fplatform%2Fsuperproject%2Fmain
        """
        return (self.property_id & 0x0F000000) >> 24

    @property
    def vhal_type(self):
        """
        VHAL type component of the property ID.
        - https://source.android.com/docs/automotive/vhal/property-configuration
        - https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleProperty.aidl
        """
        return (self.property_id & 0x00FF0000) >> 16

    @property
    def vhal_id(self):
        """
        VHAL unique ID component of the property ID.
        - https://source.android.com/docs/automotive/vhal/property-configuration
        - https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleProperty.aidl
        """
        return self.property_id & 0x0000FFFF

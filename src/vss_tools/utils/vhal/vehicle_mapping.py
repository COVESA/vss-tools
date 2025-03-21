# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass
from typing import List, Optional, Union

from dataclasses_json import LetterCase, dataclass_json


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class VehicleMappingItem:
    """
    Represents a single vehicle mapping item.

    :param name: Android name of the vehicle property
    :param property_id: Android area ID of the property (https://android.googlesource.com/platform/packages/services/Car/+/refs/heads/main/car-lib/src/android/car/VehicleAreaType.java)
    :param area_id: See https://source.android.com/docs/automotive/vhal/property-configuration
    :param access: See https://source.android.com/docs/automotive/vhal/property-configuration
    :param change_mode: Android change mode for the property (https://developer.android.com/reference/android/car/hardware/CarPropertyConfig#VEHICLE_PROPERTY_CHANGE_MODE_ONCHANGE)
    :param unit: Android property unit
    :param source: Corresponding fully-qualified VSS leaf name.
    :param formula: For mapping purpose, explains how to map a VSS property to Android property if direct
                    correspondence wasn't found.
    :param comment: Internal comment about current mapping.
    :param config_string: Optional Android string to contain property specific configuration.
    :param datatype:
    :param type:
    :param min:
    :param max:
    :param allowed:
    :param default:
    :param deprecation:
    """

    name: str
    property_id: int
    area_id: int
    access: int
    change_mode: int
    unit: str
    source: str
    formula: Optional[str] = None
    comment: Optional[str] = None
    config_string: Optional[str] = None

    datatype: Optional[str] = None
    type: Optional[str] = None
    min: Optional[int] = None
    max: Optional[int] = None
    allowed: Optional[List[str]] = None
    default: Optional[Union[Union[int, str], Union[List[int], List[str]]]] = None
    deprecation: Optional[str] = None

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

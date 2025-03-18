# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import logging
import sys
from enum import Enum, IntEnum

from vss_tools.datatypes import Datatypes


class VhalAreaType(Enum):
    """
    Values of vehicle property fields defined in
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleArea.aidl
    https://android.googlesource.com/platform/packages/services/Car/+/refs/heads/main/car-lib/src/android/car/VehicleAreaType.java
    """

    VEHICLE_AREA_TYPE_GLOBAL = 0  # VehicleAreaType.GLOBAL java
    VEHICLE_AREA_TYPE_GLOBAL_AIDL = int(0x01000000)  # VehicleArea.GLOBAL aidl

    VEHICLE_AREA_TYPE_VENDOR = 7  # VehicleAreaType.VENDOR java
    VEHICLE_AREA_TYPE_VENDOR_AIDL = int(0x08000000)  # VehicleArea.VENDOR aidl

    def __str__(self) -> str:
        d = {
            VhalAreaType.VEHICLE_AREA_TYPE_GLOBAL: "VehicleArea.GLOBAL",
            VhalAreaType.VEHICLE_AREA_TYPE_VENDOR: "VehicleArea.VENDOR",
        }
        return d.get(self, f"VehicleAreaType.{self.name}")


class VhalPropertyGroup(Enum):
    """
    Values of vehicle property fields defined in
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyGroup.aidl
    """

    VEHICLE_PROPERTY_GROUP_SYSTEM = int(0x10000000)  # VehiclePropertyGroup.SYSTEM aidl
    VEHICLE_PROPERTY_GROUP_VENDOR = int(0x20000000)  # VehiclePropertyGroup.VENDOR aidl
    VEHICLE_PROPERTY_GROUP_BACKPORTED = int(0x30000000)  # VehiclePropertyGroup.BACKPORTED aidl
    VEHICLE_PROPERTY_GROUP_VSS = int(0x40000000)  # VehiclePropertyGroup.VSS aidl (COVESA)

    @staticmethod
    def get(group: int):
        if group == 1:
            return VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_SYSTEM
        elif group == 2:
            return VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_VENDOR
        elif group == 3:
            return VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_BACKPORTED
        elif group == 4:
            return VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_VSS
        else:
            logging.error(f"Group must be between 1 and 4, was {group}")
            sys.exit(1)

    def __str__(self):
        d = {
            self.VEHICLE_PROPERTY_GROUP_SYSTEM: "VehiclePropertyGroup.SYSTEM",
            self.VEHICLE_PROPERTY_GROUP_VENDOR: "VehiclePropertyGroup.VENDOR",
            self.VEHICLE_PROPERTY_GROUP_BACKPORTED: "VehiclePropertyGroup.BACKPORTED",
            self.VEHICLE_PROPERTY_GROUP_VSS: "VehiclePropertyGroup.VSS",
        }
        return d.get(self, "VehiclePropertyGroup.SYSTEM")


class VSSDatatypesToVhal:
    """
    Mapping of vss datatypes corresponding to standard VHAL property type IDs. For those VSS datatypes, which don't
    correspond to standard VHAL properties, vendor type IDs were defined. See
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyType.aidl
    """

    VSS_TO_VHAL_TYPE_MAP = {
        # VHAL standard type mapping
        Datatypes.STRING[0]: int(0x00100000),  # STRING
        Datatypes.BOOLEAN[0]: int(0x00200000),  # BOOLEAN
        Datatypes.INT32[0]: int(0x00400000),  # INT32
        Datatypes.INT32_ARRAY[0]: int(0x00410000),  # INT32_VEC
        Datatypes.INT64[0]: int(0x00500000),  # INT64
        Datatypes.INT64_ARRAY[0]: int(0x00510000),  # INT64_VEC
        Datatypes.FLOAT[0]: int(0x00600000),  # FLOAT
        Datatypes.FLOAT_ARRAY[0]: int(0x00610000),  # FLOAT_VEC
        # Further VSS types mapped to vendor hex values
        Datatypes.STRING_ARRAY[0]: int(0x00110000),
        Datatypes.BOOLEAN_ARRAY[0]: int(0x00210000),
        Datatypes.INT8[0]: int(0x00300000),
        Datatypes.INT8_ARRAY[0]: int(0x00310000),
        Datatypes.UINT8[0]: int(0x00320000),
        Datatypes.UINT8_ARRAY[0]: int(0x00330000),
        Datatypes.INT16[0]: int(0x00340000),
        Datatypes.INT16_ARRAY[0]: int(0x00350000),
        Datatypes.UINT16[0]: int(0x00360000),
        Datatypes.UINT16_ARRAY[0]: int(0x00370000),
        Datatypes.UINT32[0]: int(0x00420000),
        Datatypes.UINT32_ARRAY[0]: int(0x00430000),
        Datatypes.UINT64[0]: int(0x00520000),
        Datatypes.UINT64_ARRAY[0]: int(0x00530000),
        Datatypes.DOUBLE[0]: int(0x00800000),
        Datatypes.DOUBLE_ARRAY[0]: int(0x00810000),
        Datatypes.NUMERIC[0]: int(0x00820000),
        Datatypes.NUMERIC_ARRAY[0]: int(0x00830000),
    }
    VHAL_TO_VSS_TYPE_MAP = {v: k for k, v in VSS_TO_VHAL_TYPE_MAP.items()}

    @classmethod
    def get_property_type_id(cls, vss_datatype: str) -> int:
        """
        Get a datatype ID of a datatype. For vss datatypes corresponding to a standard VHAL datatype use standard VHAL
        IDs. For those vss datatypes without corresponding standard VHAL IDs, use vendor IDs.

        @param vss_datatype: VSS datatype.
        @return: Integer representation of a datatype ID.
        """
        default_val = cls.VSS_TO_VHAL_TYPE_MAP[Datatypes.STRING[0]]
        return cls.VSS_TO_VHAL_TYPE_MAP.get(vss_datatype, default_val)

    @classmethod
    def get_property_type_repr(cls, datatype_id: int) -> str:
        """
        Get a datatype string representation of a datatype. For vss datatypes corresponding to a standard VHAL datatype
        use standard VHAL IDs. For those vss datatypes without corresponding standard VHAL IDs, use vendor IDs.

        @param datatype_id: datatype Integer representation.
        @return: String representation of a datatype
        """
        datatype_name = VSSDatatypesToVhal.VHAL_TO_VSS_TYPE_MAP.get(datatype_id)
        if not datatype_name:
            raise Exception(f"Invalid property type id {datatype_id}, must be one of IDs listed in VSSDataTypeToVhal")

        return f"VehiclePropertyType.{datatype_name}"


class VehiclePropertyAccess(IntEnum):
    """
    Android VHAL vehicle property access values
    https://developer.android.com/reference/android/car/hardware/CarPropertyConfig#VEHICLE_PROPERTY_ACCESS_READ
    """

    READ = 1
    WRITE = 2
    READ_WRITE = 3


class VehiclePropertyChangeMode(Enum):
    """
    Android VHAL vehicle property change mode values
    https://developer.android.com/reference/android/car/hardware/CarPropertyConfig#VEHICLE_PROPERTY_CHANGE_MODE_STATIC
    """

    STATIC = 0
    ON_CHANGE = 1
    CONTINUOUS = 2

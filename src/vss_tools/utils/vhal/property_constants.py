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

    @staticmethod
    def get_java_doc(area: int) -> str:
        if area == 0:
            return "VEHICLE_AREA_TYPE_GLOBAL"
        elif area == 7:
            return "VEHICLE_AREA_TYPE_VENDOR"
        else:
            logging.error(f"Vehicle property access must be 0 or 7, was {area}")
            sys.exit(1)


class VhalPropertyGroup(Enum):
    """
    Values of vehicle property fields defined in
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyGroup.aidl
    """

    VEHICLE_PROPERTY_GROUP_SYSTEM = int(0x10000000)  # VehiclePropertyGroup.SYSTEM aidl
    VEHICLE_PROPERTY_GROUP_VENDOR = int(0x20000000)  # VehiclePropertyGroup.VENDOR aidl
    VEHICLE_PROPERTY_GROUP_BACKPORTED = int(0x30000000)  # VehiclePropertyGroup.BACKPORTED aidl
    VEHICLE_PROPERTY_GROUP_OEM = int(0x40000000)  # VehiclePropertyGroup.OEM aidl (COVESA)

    @staticmethod
    def get(group: int):
        if group == 1:
            return VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_SYSTEM
        elif group == 2:
            return VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_VENDOR
        elif group == 3:
            return VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_BACKPORTED
        elif group == 4:
            return VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_OEM
        else:
            logging.error(f"Group must be between 1 and 4, was {group}")
            sys.exit(1)

    def __str__(self) -> str:
        d = {
            VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_SYSTEM: "VehiclePropertyGroup.SYSTEM",
            VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_VENDOR: "VehiclePropertyGroup.VENDOR",
            VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_BACKPORTED: "VehiclePropertyGroup.BACKPORTED",
            VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_OEM: "VehiclePropertyGroup.OEM",
        }
        return d.get(self, "VehiclePropertyGroup.SYSTEM")


class VhalPropertyType(Enum):
    VEHICLE_PROPERTY_TYPE_STRING = int(0x00100000)  # VehiclePropertyType.STRING
    VEHICLE_PROPERTY_TYPE_BOOLEAN = int(0x00200000)  # VehiclePropertyType.BOOLEAN
    VEHICLE_PROPERTY_TYPE_INT32 = int(0x00400000)  # VehiclePropertyType.INT32
    VEHICLE_PROPERTY_TYPE_INT32_VEC = int(0x00410000)  # VehiclePropertyType.INT32_VEC
    VEHICLE_PROPERTY_TYPE_INT64 = int(0x00500000)  # VehiclePropertyType.INT64
    VEHICLE_PROPERTY_TYPE_INT64_VEC = int(0x00510000)  # VehiclePropertyType.INT64_VEC
    VEHICLE_PROPERTY_TYPE_FLOAT = int(0x00600000)  # VehiclePropertyType.FLOAT
    VEHICLE_PROPERTY_TYPE_FLOAT_VEC = int(0x00610000)  # VehiclePropertyType.FLOAT_VEC
    VEHICLE_PROPERTY_TYPE_BYTES = int(0x00700000)  # VehiclePropertyType.BYTES
    VEHICLE_PROPERTY_TYPE_MIXED = int(0x00E00000)  # VehiclePropertyType.MIXED

    def __str__(self) -> str:
        d = {
            VhalPropertyType.VEHICLE_PROPERTY_TYPE_STRING: "VehiclePropertyType.STRING",
            VhalPropertyType.VEHICLE_PROPERTY_TYPE_BOOLEAN: "VehiclePropertyType.BOOLEAN",
            VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32: "VehiclePropertyType.INT32",
            VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32_VEC: "VehiclePropertyType.INT32_VEC",
            VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT64: "VehiclePropertyType.INT64",
            VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT64_VEC: "VehiclePropertyType.INT64_VEC",
            VhalPropertyType.VEHICLE_PROPERTY_TYPE_FLOAT: "VehiclePropertyType.FLOAT",
            VhalPropertyType.VEHICLE_PROPERTY_TYPE_FLOAT_VEC: "VehiclePropertyType.FLOAT_VEC",
            VhalPropertyType.VEHICLE_PROPERTY_TYPE_BYTES: "VehiclePropertyType.BYTES",
            VhalPropertyType.VEHICLE_PROPERTY_TYPE_MIXED: "VehiclePropertyType.MIXED",
        }
        return d.get(self, "Unsupported")


class VSSDatatypesToVhal:
    """
    Mapping of vss datatypes corresponding to standard VHAL property type IDs. For those VSS datatypes, which don't
    correspond to standard VHAL properties, vendor type IDs were defined. See
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyType.aidl
    and https://source.android.com/docs/automotive/vhal/property-configuration#property-types
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
        # Further VSS types mapped to hex values of supported types
        Datatypes.STRING_ARRAY[0]: int(0x00100000),  # STRING
        Datatypes.BOOLEAN_ARRAY[0]: int(0x00410000),  # INT32_VEC
        Datatypes.INT8[0]: int(0x00400000),  # INT32
        Datatypes.INT8_ARRAY[0]: int(0x00410000),  # INT32_VEC
        Datatypes.UINT8[0]: int(0x00400000),  # INT32
        Datatypes.UINT8_ARRAY[0]: int(0x00410000),  # INT32_VEC
        Datatypes.INT16[0]: int(0x00400000),  # INT32
        Datatypes.INT16_ARRAY[0]: int(0x00410000),  # INT32_VEC
        Datatypes.UINT16[0]: int(0x00400000),  # INT32
        Datatypes.UINT16_ARRAY[0]: int(0x00410000),  # INT32_VEC
        Datatypes.UINT32[0]: int(0x00400000),  # INT32
        Datatypes.UINT32_ARRAY[0]: int(0x00410000),  # INT32_VEC
        Datatypes.UINT64[0]: int(0x00500000),  # INT64
        Datatypes.UINT64_ARRAY[0]: int(0x00510000),  # INT64_VEC
        Datatypes.DOUBLE[0]: int(0x00600000),  # fallback to FLOAT
        Datatypes.DOUBLE_ARRAY[0]: int(0x00610000),  # fallback to FLOAT_VEC
        Datatypes.NUMERIC[0]: int(0x00600000),  # fallback to FLOAT
        Datatypes.NUMERIC_ARRAY[0]: int(0x00610000),  # fallback to FLOAT_VEC
    }

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
        datatype_name = str(VhalPropertyType(datatype_id))
        if not datatype_name:
            raise Exception(f"Invalid property type id {datatype_id}, must be one of IDs listed in VSSDataTypeToVhal")

        return datatype_name


class VehiclePropertyAccess(IntEnum):
    """
    Android VHAL vehicle property access values
    https://developer.android.com/reference/android/car/hardware/CarPropertyConfig#VEHICLE_PROPERTY_ACCESS_READ
    """

    READ = 1
    WRITE = 2
    READ_WRITE = 3

    def __str__(self):
        d = {
            VehiclePropertyAccess.READ: "VehiclePropertyAccess.READ",
            VehiclePropertyAccess.WRITE: "VehiclePropertyAccess.WRITE",
            VehiclePropertyAccess.READ_WRITE: "VehiclePropertyAccess.READ_WRITE",
        }
        return d.get(self, "VehiclePropertyAccess.READ")

    @staticmethod
    def get_java_doc(access: int) -> str:
        if access == 1:
            return "VEHICLE_PROPERTY_ACCESS_READ"
        elif access == 2:
            return "VEHICLE_PROPERTY_ACCESS_WRITE"
        elif access == 3:
            return "VEHICLE_PROPERTY_ACCESS_READ_WRITE"
        else:
            logging.error(f"Vehicle property access must be between 1 and 3, was {access}")
            sys.exit(1)


class VehiclePropertyChangeMode(Enum):
    """
    Android VHAL vehicle property change mode values
    https://developer.android.com/reference/android/car/hardware/CarPropertyConfig#VEHICLE_PROPERTY_CHANGE_MODE_STATIC
    """

    STATIC = 0
    ON_CHANGE = 1
    CONTINUOUS = 2

    def __str__(self) -> str:
        d = {
            VehiclePropertyChangeMode.STATIC: "VehiclePropertyChangeMode.STATIC",
            VehiclePropertyChangeMode.ON_CHANGE: "VehiclePropertyChangeMode.ON_CHANGE",
            VehiclePropertyChangeMode.CONTINUOUS: "VehiclePropertyChangeMode.CONTINUOUS",
        }
        return d.get(self, "VehiclePropertyChangeMode.STATIC")

    @staticmethod
    def get_java_doc(mode: int) -> str:
        if mode == 0:
            return "VEHICLE_PROPERTY_CHANGE_MODE_STATIC"
        elif mode == 1:
            return "VEHICLE_PROPERTY_CHANGE_MODE_ONCHANGE"
        elif mode == 2:
            return "VEHICLE_PROPERTY_CHANGE_MODE_CONTINUOUS"
        else:
            logging.error(f"Change mode must be between 0 and 2, was {mode}")
            sys.exit(1)

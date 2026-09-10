# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from enum import IntEnum

from vss_tools.datatypes import Datatypes


class VhalEnum(IntEnum):
    @classmethod
    def get(cls, value: int | str):
        value = value.upper() if isinstance(value, str) else value
        options = []
        for item in cls:
            options.append(f"{item} ({item.value})")
            if str(item) == value or item.name == value or item.value == value:
                return item
        raise Exception(f"{cls} can have values: {', '.join(options)}; but was {value}")

    def __str__(self) -> str:
        return self.name


class VhalAreaType(VhalEnum):
    """
    Values of vehicle property fields defined in
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleArea.aidl
    https://android.googlesource.com/platform/packages/services/Car/+/refs/heads/main/car-lib/src/android/car/VehicleAreaType.java
    """

    VEHICLE_AREA_TYPE_GLOBAL = int(0x1)
    VEHICLE_AREA_TYPE_WINDOW = int(0x3)
    VEHICLE_AREA_TYPE_MIRROR = int(0x4)
    VEHICLE_AREA_TYPE_SEAT = int(0x5)
    VEHICLE_AREA_TYPE_DOOR = int(0x6)
    VEHICLE_AREA_TYPE_WHEEL = int(0x7)
    VEHICLE_AREA_TYPE_VENDOR = int(0x8)

    def __str__(self) -> str:
        return self.name.removeprefix("VEHICLE_AREA_TYPE_")


class VhalPropertyGroup(VhalEnum):
    """
    Values of vehicle property fields defined in
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyGroup.aidl
    """

    VEHICLE_PROPERTY_GROUP_SYSTEM = int(0x1)  # VehiclePropertyGroup.SYSTEM
    VEHICLE_PROPERTY_GROUP_VENDOR = int(0x2)  # VehiclePropertyGroup.VENDOR
    VEHICLE_PROPERTY_GROUP_BACKPORTED = int(0x3)  # VehiclePropertyGroup.BACKPORTED
    VEHICLE_PROPERTY_GROUP_OEM = int(0x4)  # VehiclePropertyGroup.OEM (COVESA)

    def __str__(self) -> str:
        return self.name.removeprefix("VEHICLE_PROPERTY_GROUP_")


class VhalPropertyType(VhalEnum):
    VEHICLE_PROPERTY_TYPE_STRING = int(0x10)  # VehiclePropertyType.STRING
    VEHICLE_PROPERTY_TYPE_BOOLEAN = int(0x20)  # VehiclePropertyType.BOOLEAN
    VEHICLE_PROPERTY_TYPE_INT32 = int(0x40)  # VehiclePropertyType.INT32
    VEHICLE_PROPERTY_TYPE_INT32_VEC = int(0x41)  # VehiclePropertyType.INT32_VEC
    VEHICLE_PROPERTY_TYPE_INT64 = int(0x50)  # VehiclePropertyType.INT64
    VEHICLE_PROPERTY_TYPE_INT64_VEC = int(0x51)  # VehiclePropertyType.INT64_VEC
    VEHICLE_PROPERTY_TYPE_FLOAT = int(0x60)  # VehiclePropertyType.FLOAT
    VEHICLE_PROPERTY_TYPE_FLOAT_VEC = int(0x61)  # VehiclePropertyType.FLOAT_VEC
    VEHICLE_PROPERTY_TYPE_BYTES = int(0x70)  # VehiclePropertyType.BYTES
    VEHICLE_PROPERTY_TYPE_MIXED = int(0xE0)  # VehiclePropertyType.MIXED

    def __str__(self) -> str:
        return self.name.removeprefix("VEHICLE_PROPERTY_TYPE_")


class VSSDatatypesToVhal:
    """
    Mapping of vss datatypes corresponding to standard VHAL property type IDs. For those VSS datatypes, which don't
    correspond to standard VHAL properties, vendor type IDs were defined. See
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyType.aidl
    and https://source.android.com/docs/automotive/vhal/property-configuration#property-types
    """

    VSS_TO_VHAL_TYPE_MAP = {
        # VHAL standard type mapping
        Datatypes.STRING[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_STRING,  # STRING
        Datatypes.BOOLEAN[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_BOOLEAN,  # BOOLEAN
        Datatypes.INT32[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32,  # INT32
        Datatypes.INT32_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32_VEC,  # INT32_VEC
        Datatypes.INT64[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT64,  # INT64
        Datatypes.INT64_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT64_VEC,  # INT64_VEC
        Datatypes.FLOAT[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_FLOAT,  # FLOAT
        Datatypes.FLOAT_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_FLOAT_VEC,  # FLOAT_VEC
        # Further VSS types mapped to hex values of supported types
        Datatypes.STRING_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_STRING,  # STRING
        Datatypes.BOOLEAN_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32_VEC,  # INT32_VEC
        Datatypes.INT8[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32,  # INT32
        Datatypes.INT8_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32_VEC,  # INT32_VEC
        Datatypes.UINT8[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32,  # INT32
        Datatypes.UINT8_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32_VEC,  # INT32_VEC
        Datatypes.INT16[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32,  # INT32
        Datatypes.INT16_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32_VEC,  # INT32_VEC
        Datatypes.UINT16[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32,  # INT32
        Datatypes.UINT16_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32_VEC,  # INT32_VEC
        Datatypes.UINT32[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32,  # INT32
        Datatypes.UINT32_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT32_VEC,  # INT32_VEC
        Datatypes.UINT64[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT64,  # INT64
        Datatypes.UINT64_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_INT64_VEC,  # INT64_VEC
        Datatypes.DOUBLE[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_FLOAT,  # fallback to FLOAT
        Datatypes.DOUBLE_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_FLOAT_VEC,  # fallback to FLOAT_VEC
        Datatypes.NUMERIC[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_FLOAT,  # fallback to FLOAT
        Datatypes.NUMERIC_ARRAY[0]: VhalPropertyType.VEHICLE_PROPERTY_TYPE_FLOAT_VEC,  # fallback to FLOAT_VEC
    }

    @classmethod
    def get(cls, vss_datatype: str) -> VhalPropertyType:
        """
        Get a datatype ID of a datatype. For vss datatypes corresponding to a standard VHAL datatype use standard VHAL
        IDs. For those vss datatypes without corresponding standard VHAL IDs, use vendor IDs.

        @param vss_datatype: VSS datatype.
        @return: Integer representation of a datatype ID.
        """
        return cls.VSS_TO_VHAL_TYPE_MAP.get(vss_datatype, cls.VSS_TO_VHAL_TYPE_MAP[Datatypes.STRING[0]])


class VehicleAreaDoor(VhalEnum):
    """
    Android VHAL door area values.
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleAreaDoor.aidl
    """

    ROW_1_LEFT = 0x00000001
    ROW_1_RIGHT = 0x00000004
    ROW_2_LEFT = 0x00000010
    ROW_2_RIGHT = 0x00000040
    ROW_3_LEFT = 0x00000100
    ROW_3_RIGHT = 0x00000400
    HOOD = 0x10000000
    REAR = 0x20000000


class VehicleAreaMirror(VhalEnum):
    """
    Android VHAL mirror area values.
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleAreaMirror.aidl
    """

    DRIVER_LEFT = 0x00000001
    DRIVER_RIGHT = 0x00000002
    DRIVER_CENTER = 0x00000004


class VehicleAreaSeat(VhalEnum):
    """
    Android VHAL seat area values.
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleAreaSeat.aidl
    """

    UNKNOWN = 0x0000
    ROW_1_LEFT = 0x0001
    ROW_1_CENTER = 0x0002
    ROW_1_RIGHT = 0x0004
    ROW_2_LEFT = 0x0010
    ROW_2_CENTER = 0x0020
    ROW_2_RIGHT = 0x0040
    ROW_3_LEFT = 0x0100
    ROW_3_CENTER = 0x0200
    ROW_3_RIGHT = 0x0400


class VehicleAreaWheel(VhalEnum):
    """
    Android VHAL wheel area values.
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleAreaWheel.aidl
    """

    UNKNOWN = 0x00
    LEFT_FRONT = 0x01
    RIGHT_FRONT = 0x02
    LEFT_REAR = 0x04
    RIGHT_REAR = 0x08


class VehicleAreaWindow(VhalEnum):
    """
    Android VHAL window area values.
    https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehicleAreaWindow.aidl
    """

    FRONT_WINDSHIELD = 0x00000001
    REAR_WINDSHIELD = 0x00000002
    ROW_1_LEFT = 0x00000010
    ROW_1_RIGHT = 0x00000040
    ROW_2_LEFT = 0x00000100
    ROW_2_RIGHT = 0x00000400
    ROW_3_LEFT = 0x00001000
    ROW_3_RIGHT = 0x00004000
    ROOF_TOP_1 = 0x00010000
    ROOF_TOP_2 = 0x00020000


class VehiclePropertyAccess(VhalEnum):
    """
    Android VHAL vehicle property access values
    https://developer.android.com/reference/android/car/hardware/CarPropertyConfig#VEHICLE_PROPERTY_ACCESS_READ
    """

    READ = 1
    WRITE = 2
    READ_WRITE = 3


class VehiclePropertyChangeMode(VhalEnum):
    """
    Android VHAL vehicle property change mode values
    https://developer.android.com/reference/android/car/hardware/CarPropertyConfig#VEHICLE_PROPERTY_CHANGE_MODE_STATIC
    """

    STATIC = 0
    ON_CHANGE = 1
    CONTINUOUS = 2

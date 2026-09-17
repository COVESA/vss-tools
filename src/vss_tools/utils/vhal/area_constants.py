# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from typing import Any, Optional, Tuple

from vss_tools.utils.vhal.property_constants import (
    VehicleAreaDoor,
    VehicleAreaMirror,
    VehicleAreaSeat,
    VehicleAreaWheel,
    VehicleAreaWindow,
    VhalAreaType,
)

# All possible VSS positional instance strings
VSS_POSITIONAL_KEYWORDS: frozenset[str] = frozenset(
    [
        "row1",
        "row2",
        "row3",
        "row4",
        "left",
        "right",
        "center",
        "middle",
        "front",
        "rear",
        "frontleft",
        "frontright",
        "rearleft",
        "rearright",
        "driverside",
        "passengerside",
        "driver",
        "passenger",
    ]
)

# Global VSS translation map (normalizing terminology)
VSS_SIDE_TO_COLUMN: dict[str, str] = {
    "driverside": "left",  # ambiguous
    "driver": "left",  # ambiguous
    "middle": "center",
    "passengerside": "right",  # ambiguous
    "passenger": "right",  # ambiguous
}

# Door area: Row[1,2] × [DriverSide,PassengerSide] for Cabin.Door;
# [Front,Rear] for Body.Trunk (HOOD / REAR).
VSS_DOOR_AREA_MAP: dict[tuple[str, ...], VehicleAreaDoor] = {
    ("row1", "left"): VehicleAreaDoor.ROW_1_LEFT,
    ("row1", "right"): VehicleAreaDoor.ROW_1_RIGHT,
    ("row2", "left"): VehicleAreaDoor.ROW_2_LEFT,
    ("row2", "right"): VehicleAreaDoor.ROW_2_RIGHT,
    ("row3", "left"): VehicleAreaDoor.ROW_3_LEFT,
    ("row3", "right"): VehicleAreaDoor.ROW_3_RIGHT,
    ("front",): VehicleAreaDoor.HOOD,
    ("rear",): VehicleAreaDoor.REAR,
}

# Mirror area: [DriverSide,PassengerSide] → left/right mirror.
VSS_MIRROR_AREA_MAP: dict[tuple[str, ...], VehicleAreaMirror] = {
    ("left",): VehicleAreaMirror.DRIVER_LEFT,
    ("center",): VehicleAreaMirror.DRIVER_CENTER,
    ("right",): VehicleAreaMirror.DRIVER_RIGHT,
}

# Seat area: Row[1,3] × [DriverSide/Middle/PassengerSide] and [Driver/Passenger].
# Row 4 is intentionally absent — VehicleAreaSeat has no Row 4.
VSS_SEAT_AREA_MAP: dict[tuple[str, ...], VehicleAreaSeat] = {
    ("row1", "left"): VehicleAreaSeat.ROW_1_LEFT,
    ("row1", "center"): VehicleAreaSeat.ROW_1_CENTER,
    ("row1", "right"): VehicleAreaSeat.ROW_1_RIGHT,
    ("row2", "left"): VehicleAreaSeat.ROW_2_LEFT,
    ("row2", "center"): VehicleAreaSeat.ROW_2_CENTER,
    ("row2", "right"): VehicleAreaSeat.ROW_2_RIGHT,
    ("row3", "left"): VehicleAreaSeat.ROW_3_LEFT,
    ("row3", "center"): VehicleAreaSeat.ROW_3_CENTER,
    ("row3", "right"): VehicleAreaSeat.ROW_3_RIGHT,
}

# Wheel area: Row[1,2] × [Left,Right]
VSS_WHEEL_AREA_MAP: dict[tuple[str, ...], VehicleAreaWheel] = {
    ("row1", "left"): VehicleAreaWheel.LEFT_FRONT,
    ("row1", "right"): VehicleAreaWheel.RIGHT_FRONT,
    ("row2", "left"): VehicleAreaWheel.LEFT_REAR,
    ("row2", "right"): VehicleAreaWheel.RIGHT_REAR,
    ("frontleft",): VehicleAreaWheel.LEFT_FRONT,
    ("frontright",): VehicleAreaWheel.RIGHT_FRONT,
    ("rearleft",): VehicleAreaWheel.LEFT_REAR,
    ("rearright",): VehicleAreaWheel.RIGHT_REAR,
}

# Window area: [Front,Rear] for Body.Windshield.
VSS_WINDOW_AREA_MAP: dict[tuple[str, ...], VehicleAreaWindow] = {
    ("front",): VehicleAreaWindow.FRONT_WINDSHIELD,
    ("rear",): VehicleAreaWindow.REAR_WINDSHIELD,
}

VEHICLE_AREA_TYPE_MAP: dict[VhalAreaType, dict[tuple[str, ...], Any]] = {
    VhalAreaType.VEHICLE_AREA_TYPE_DOOR: VSS_DOOR_AREA_MAP,
    VhalAreaType.VEHICLE_AREA_TYPE_MIRROR: VSS_MIRROR_AREA_MAP,
    VhalAreaType.VEHICLE_AREA_TYPE_SEAT: VSS_SEAT_AREA_MAP,
    VhalAreaType.VEHICLE_AREA_TYPE_WHEEL: VSS_WHEEL_AREA_MAP,
    VhalAreaType.VEHICLE_AREA_TYPE_WINDOW: VSS_WINDOW_AREA_MAP,
}

VEHICLE_AREA_TYPE_TO_ENUM_CLASS: dict[VhalAreaType, Any] = {
    VhalAreaType.VEHICLE_AREA_TYPE_DOOR: VehicleAreaDoor,
    VhalAreaType.VEHICLE_AREA_TYPE_MIRROR: VehicleAreaMirror,
    VhalAreaType.VEHICLE_AREA_TYPE_SEAT: VehicleAreaSeat,
    VhalAreaType.VEHICLE_AREA_TYPE_WHEEL: VehicleAreaWheel,
    VhalAreaType.VEHICLE_AREA_TYPE_WINDOW: VehicleAreaWindow,
}

VEHICLE_AREA_TYPES = {"GLOBAL", "DOOR", "MIRROR", "SEAT", "WHEEL", "WINDOW"}


def get_extracted_instance_parts(vss_path: str) -> Tuple[str, ...]:
    """
    Returns the original positional instance tuple extracted from the VSS path.
    Example: ('row1', 'driverside')
    """
    parts = vss_path.split(".")
    return tuple(p for p in parts if p.lower() in VSS_POSITIONAL_KEYWORDS)


def get_area_id(area_type: VhalAreaType, instance_tuple: Tuple[str, ...]) -> Optional[int]:
    if not instance_tuple:
        return None

    area_map: dict = VEHICLE_AREA_TYPE_MAP.get(area_type, {})
    if not area_map:
        return None

    # Translate side
    key = tuple(VSS_SIDE_TO_COLUMN.get(s.lower(), s.lower()) for s in instance_tuple)

    if key not in area_map:
        return None

    return area_map[key].value


def get_explicit_area_id(area_type: VhalAreaType, area_value: str) -> Optional[int]:
    """
    Checks if a single explicit area value string is valid for the given Area Type,
    and returns its integer bitmask.

    Example: (VEHICLE_AREA_TYPE_DOOR, "HOOD") -> Returns 0x10000000

    @param area_type: The base Area Type (e.g., VEHICLE_AREA_TYPE_DOOR)
    @param area_value: The string value to check (e.g., "HOOD")
    @return: The integer Area ID, or None if invalid.
    """
    enum_class = VEHICLE_AREA_TYPE_TO_ENUM_CLASS.get(area_type)

    if not enum_class:
        return None

    safe_value = area_value.upper()

    # If the member exists, return its integer value!
    if safe_value in enum_class.__members__:
        return enum_class.__members__[safe_value].value

    return None

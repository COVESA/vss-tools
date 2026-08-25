# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

#
# Convert vspec files to various other formats
#

import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

import pytest
from pydantic import ValidationError
from vss_tools.exporters.vhal import VhalMapper
from vss_tools.main import get_trees
from vss_tools.utils.vhal.area_constants import (
    get_area_id,
    get_explicit_area_id,
    get_extracted_instance_parts,
)
from vss_tools.utils.vhal.property_constants import (
    VehicleAreaDoor,
    VehicleAreaMirror,
    VehicleAreaSeat,
    VehicleAreaWheel,
    VehicleAreaWindow,
    VehiclePropertyAccess,
    VehiclePropertyChangeMode,
    VhalAreaType,
    VhalPropertyGroup,
)
from vss_tools.utils.vhal.vehicle_mapping import VehicleMappingItem
from vss_tools.utils.vhal.vhal_area_config import VhalAreaConfigItem, VhalAreaRuleItem

# HELPERS

HERE = Path(__file__).resolve().parent

# FIXTURES


def __validation_properties(group: int, min_id: int = 1, suffix="") -> List[VehicleMappingItem]:
    # read reference vss leaves and corresponding generated property ids
    filename = f"validation_group_{group}_min_{min_id}.json" if min_id > 1 else f"validation_group_{group}{suffix}.json"
    reference_file_path: Path = HERE / "validation_jsons" / filename

    mapper = VhalMapper(
        include_new=True, group=group, starting_id=min_id, override_units=False, override_datatype=False
    )
    mapper.load_mapping(reference_file_path)
    return mapper.get()


@pytest.fixture(scope="session")
def validation_properties_group_1() -> List[VehicleMappingItem]:
    return __validation_properties(group=1, min_id=32768)


@pytest.fixture(scope="session")
def validation_properties_group_2() -> List[VehicleMappingItem]:
    return __validation_properties(group=2)


@pytest.fixture(scope="session")
def validation_properties_group_4() -> List[VehicleMappingItem]:
    return __validation_properties(group=4)


@pytest.fixture(scope="session")
def validation_properties_group_4_update() -> List[VehicleMappingItem]:
    return __validation_properties(group=4, suffix="_update")


@pytest.fixture(scope="session")
def validation_properties_group_4_with_manual_updates() -> List[VehicleMappingItem]:
    return __validation_properties(group=4, suffix="_manual_updates")


def __vhal_mapper(
    group: int, min_id: int = 1, suffix="", mapping: Optional[str] = None, override: bool = False
) -> VhalMapper:
    path_spec = HERE / "vehicle_signal_specification"
    vspec_file = f"vss{suffix}.vspec"

    tree, datatype_tree = get_trees(
        vspec=path_spec / vspec_file,
        include_dirs=(),
        aborts=(),
        strict=False,
        extended_attributes=(),
        quantities=(),
        units=(),
        types=(),
        overlays=(),
        expand=True,
    )

    mapper = VhalMapper(
        include_new=True, group=group, starting_id=min_id, override_units=override, override_datatype=override
    )
    if mapping is not None:
        mapper.load_mapping(HERE / "validation_jsons" / f"{mapping}.json")
    mapper.load_vss_tree(tree)
    return mapper


@pytest.fixture(scope="session")
def vhal_mapper_group_4() -> VhalMapper:
    return __vhal_mapper(group=4)


def __vss_properties(
    group: int, min_id: int = 1, suffix="", mapping: Optional[str] = None, override: bool = False
) -> List[VehicleMappingItem]:
    mapper = __vhal_mapper(group, min_id, suffix, mapping, override)
    return mapper.get()


@pytest.fixture(scope="session")
def vss_properties_group_1() -> List[VehicleMappingItem]:
    return __vss_properties(group=1, min_id=32768)


@pytest.fixture(scope="session")
def vss_properties_group_2() -> List[VehicleMappingItem]:
    return __vss_properties(group=2)


@pytest.fixture(scope="session")
def vss_properties_group_4() -> List[VehicleMappingItem]:
    return __vss_properties(group=4)


@pytest.fixture(scope="session")
def vss_properties_group_4_with_manual_updates() -> List[VehicleMappingItem]:
    return __vss_properties(group=4, mapping="validation_group_4_manual_updates", override=False)


@pytest.fixture(scope="session")
def vss_properties_group_4_with_manual_updates_override() -> List[VehicleMappingItem]:
    return __vss_properties(group=4, mapping="validation_group_4_manual_updates", override=True)


@pytest.fixture(scope="session")
def vss_properties_group_4_update() -> List[VehicleMappingItem]:
    return __vss_properties(group=4, suffix="_update", mapping="validation_group_4", override=True)


@pytest.fixture(scope="session")
def java_property_ids_code() -> str:
    with open(HERE / "validation_jsons" / "VehiclePropertyIdsOem.java", "r") as file:
        return file.read()


@pytest.fixture(scope="session")
def java_permissions_code() -> str:
    with open(HERE / "validation_jsons" / "OemPermissions.java", "r") as file:
        return file.read()


@pytest.fixture(scope="session")
def aidl_code() -> str:
    with open(HERE / "validation_jsons" / "VehiclePropertyOem.aidl", "r") as file:
        return file.read()


@pytest.fixture(scope="session")
def car_service_android_manifest_code() -> str:
    with open(HERE / "validation_jsons" / "AndroidManifest.xml", "r") as file:
        return file.read()


@pytest.fixture(scope="session")
def car_service_strings_code() -> str:
    with open(HERE / "validation_jsons" / "strings.xml", "r") as file:
        return file.read()


# UNIT TESTS


def test_vhal_area_type():
    assert VhalAreaType.get(1) == VhalAreaType.VEHICLE_AREA_TYPE_GLOBAL
    assert VhalAreaType.get(3) == VhalAreaType.VEHICLE_AREA_TYPE_WINDOW
    assert VhalAreaType.get(4) == VhalAreaType.VEHICLE_AREA_TYPE_MIRROR
    assert VhalAreaType.get(5) == VhalAreaType.VEHICLE_AREA_TYPE_SEAT
    assert VhalAreaType.get(6) == VhalAreaType.VEHICLE_AREA_TYPE_DOOR
    assert VhalAreaType.get(7) == VhalAreaType.VEHICLE_AREA_TYPE_WHEEL
    assert VhalAreaType.get(8) == VhalAreaType.VEHICLE_AREA_TYPE_VENDOR

    assert VhalAreaType.get("GLOBAL") == VhalAreaType.VEHICLE_AREA_TYPE_GLOBAL
    assert VhalAreaType.get("WINDOW") == VhalAreaType.VEHICLE_AREA_TYPE_WINDOW
    assert VhalAreaType.get("MIRROR") == VhalAreaType.VEHICLE_AREA_TYPE_MIRROR
    assert VhalAreaType.get("SEAT") == VhalAreaType.VEHICLE_AREA_TYPE_SEAT
    assert VhalAreaType.get("DOOR") == VhalAreaType.VEHICLE_AREA_TYPE_DOOR
    assert VhalAreaType.get("WHEEL") == VhalAreaType.VEHICLE_AREA_TYPE_WHEEL
    assert VhalAreaType.get("VENDOR") == VhalAreaType.VEHICLE_AREA_TYPE_VENDOR
    with pytest.raises(Exception):
        VhalAreaType.get(2)


def test_vhal_property_group():
    assert VhalPropertyGroup.get(1) == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_SYSTEM
    assert VhalPropertyGroup.get(2) == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_VENDOR
    assert VhalPropertyGroup.get(3) == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_BACKPORTED
    assert VhalPropertyGroup.get(4) == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_OEM

    assert VhalPropertyGroup.get("SYSTEM") == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_SYSTEM
    assert VhalPropertyGroup.get("VENDOR") == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_VENDOR
    assert VhalPropertyGroup.get("BACKPORTED") == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_BACKPORTED
    assert VhalPropertyGroup.get("OEM") == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_OEM

    assert str(VhalPropertyGroup.get(1)) == "SYSTEM"
    assert str(VhalPropertyGroup.get(2)) == "VENDOR"
    assert str(VhalPropertyGroup.get(3)) == "BACKPORTED"
    assert str(VhalPropertyGroup.get(4)) == "OEM"

    with pytest.raises(Exception):
        VhalPropertyGroup.get(5)


def test_vhal_vehicle_property_access():
    assert VehiclePropertyAccess.get(1) == VehiclePropertyAccess.READ
    assert VehiclePropertyAccess.get(2) == VehiclePropertyAccess.WRITE
    assert VehiclePropertyAccess.get(3) == VehiclePropertyAccess.READ_WRITE

    assert VehiclePropertyAccess.get("READ") == VehiclePropertyAccess.READ
    assert VehiclePropertyAccess.get("WRITE") == VehiclePropertyAccess.WRITE
    assert VehiclePropertyAccess.get("READ_WRITE") == VehiclePropertyAccess.READ_WRITE

    assert str(VehiclePropertyAccess.get(1)) == "READ"
    assert str(VehiclePropertyAccess.get(2)) == "WRITE"
    assert str(VehiclePropertyAccess.get(3)) == "READ_WRITE"
    with pytest.raises(Exception):
        VehiclePropertyAccess.get(4)


def test_vhal_vehicle_property_change_mode():
    assert VehiclePropertyChangeMode.get(0) == VehiclePropertyChangeMode.STATIC
    assert VehiclePropertyChangeMode.get(1) == VehiclePropertyChangeMode.ON_CHANGE
    assert VehiclePropertyChangeMode.get(2) == VehiclePropertyChangeMode.CONTINUOUS

    assert VehiclePropertyChangeMode.get("STATIC") == VehiclePropertyChangeMode.STATIC
    assert VehiclePropertyChangeMode.get("ON_CHANGE") == VehiclePropertyChangeMode.ON_CHANGE
    assert VehiclePropertyChangeMode.get("CONTINUOUS") == VehiclePropertyChangeMode.CONTINUOUS

    assert str(VehiclePropertyChangeMode.get(0)) == "STATIC"
    assert str(VehiclePropertyChangeMode.get(1)) == "ON_CHANGE"
    assert str(VehiclePropertyChangeMode.get(2)) == "CONTINUOUS"
    with pytest.raises(Exception):
        VehiclePropertyChangeMode.get(3)


def test_vhal_vehicle_area_door():
    assert VehicleAreaDoor.ROW_1_LEFT.value == 0x00000001
    assert VehicleAreaDoor.ROW_1_RIGHT.value == 0x00000004
    assert VehicleAreaDoor.ROW_2_LEFT.value == 0x00000010
    assert VehicleAreaDoor.ROW_2_RIGHT.value == 0x00000040
    assert VehicleAreaDoor.ROW_3_LEFT.value == 0x00000100
    assert VehicleAreaDoor.ROW_3_RIGHT.value == 0x00000400
    assert VehicleAreaDoor.HOOD.value == 0x10000000
    assert VehicleAreaDoor.REAR.value == 0x20000000


def test_vhal_vehicle_area_mirror():
    assert VehicleAreaMirror.DRIVER_LEFT.value == 0x00000001
    assert VehicleAreaMirror.DRIVER_RIGHT.value == 0x00000002
    assert VehicleAreaMirror.DRIVER_CENTER.value == 0x00000004


def test_vhal_vehicle_area_seat():
    assert VehicleAreaSeat.UNKNOWN.value == 0x0000
    assert VehicleAreaSeat.ROW_1_LEFT.value == 0x0001
    assert VehicleAreaSeat.ROW_1_CENTER.value == 0x0002
    assert VehicleAreaSeat.ROW_1_RIGHT.value == 0x0004
    assert VehicleAreaSeat.ROW_2_LEFT.value == 0x0010
    assert VehicleAreaSeat.ROW_2_CENTER.value == 0x0020
    assert VehicleAreaSeat.ROW_2_RIGHT.value == 0x0040
    assert VehicleAreaSeat.ROW_3_LEFT.value == 0x0100
    assert VehicleAreaSeat.ROW_3_CENTER.value == 0x0200
    assert VehicleAreaSeat.ROW_3_RIGHT.value == 0x0400


def test_vhal_vehicle_area_wheel():
    assert VehicleAreaWheel.UNKNOWN.value == 0x00
    assert VehicleAreaWheel.LEFT_FRONT.value == 0x01
    assert VehicleAreaWheel.RIGHT_FRONT.value == 0x02
    assert VehicleAreaWheel.LEFT_REAR.value == 0x04
    assert VehicleAreaWheel.RIGHT_REAR.value == 0x08


def test_vhal_vehicle_area_window():
    assert VehicleAreaWindow.FRONT_WINDSHIELD.value == 0x00000001
    assert VehicleAreaWindow.REAR_WINDSHIELD.value == 0x00000002
    assert VehicleAreaWindow.ROW_1_LEFT.value == 0x00000010
    assert VehicleAreaWindow.ROW_1_RIGHT.value == 0x00000040
    assert VehicleAreaWindow.ROW_2_LEFT.value == 0x00000100
    assert VehicleAreaWindow.ROW_2_RIGHT.value == 0x00000400
    assert VehicleAreaWindow.ROW_3_LEFT.value == 0x00001000
    assert VehicleAreaWindow.ROW_3_RIGHT.value == 0x00004000
    assert VehicleAreaWindow.ROOF_TOP_1.value == 0x00010000
    assert VehicleAreaWindow.ROOF_TOP_2.value == 0x00020000


def test_vhal_area_rule_item_coerce_string():
    item = VhalAreaRuleItem.model_validate("SEAT")
    assert item.area_type == "SEAT"
    assert item.map == {}
    assert item.ignore == []
    assert item.keep == []


def test_vhal_area_rule_item_parse_explicit_map():
    data = {
        "area_type": "DOOR",
        "map": {
            "front": "hood",  # Should strip spaces, lowercase key, uppercase val
            " rear": "REAR",  # Should strip spaces, lowercase key, uppercase val
        },
    }
    item = VhalAreaRuleItem(**data)
    assert item.map == {
        ("front",): "HOOD",
        ("rear",): "REAR",
    }


def test_vhal_area_rule_item_uppercase_area_type():
    item = VhalAreaRuleItem(area_type="SEAT")
    assert item.area_type == "SEAT"

    with pytest.raises(ValidationError):
        VhalAreaRuleItem(area_type="ROOF")


def test_vhal_area_rule_item_lowercase_rule_lists():
    data = {
        "area_type": "WHEEL",
        "ignore": [
            "frontleft",
            ["row1", "left"],
        ],
        "keep": [
            "row2",
        ],
    }
    item = VhalAreaRuleItem(**data)
    assert item.ignore == ["frontleft", ["row1", "left"]]
    assert item.keep == ["row2"]


def test_vhal_are_config_compile_pattern():
    rule = VhalAreaRuleItem.model_validate("DOOR")
    pattern = "Vehicle.Cabin.Door.Row1.DriverSide.IsChildLockActive"
    depth = 6
    item = VhalAreaConfigItem(
        pattern=pattern,
        depth=depth,
        rule=rule,
    )
    assert item.compiled_regex.match(pattern) is not None
    assert item.compiled_regex.match("Vehicle.Cabin.Door") is None


def test_vhal_are_config_from_rule():
    rule = VhalAreaRuleItem.model_validate("MIRROR")
    pattern = "Vehicle.Body.Mirrors.*"
    depth = 4
    item = VhalAreaConfigItem(rule=rule, pattern=pattern, depth=depth)

    assert item.pattern == pattern
    assert item.depth == depth
    assert item.rule is rule


def test_vhal_are_config_resolve_area_type():
    data = {
        "areaType": "WHEEL",
        "map": {"row1, left": "LEFT_FRONT"},
        "ignore": [
            ["row1", "right"],
            "row2",
        ],
        "keep": [
            ["row1", "left"],
        ],
    }
    rule = VhalAreaRuleItem(**data)
    pattern = "Vehicle.MotionManagement.Suspension.Axle.*.Wheel.*"
    depth = 7
    item = VhalAreaConfigItem(rule=rule, pattern=pattern, depth=depth)

    keep_path = "Vehicle.MotionManagement.Suspension.Axle.Row1.Wheel.Left.DampingForce"
    keep_path_area_type = (VhalAreaType.VEHICLE_AREA_TYPE_WHEEL, 1)
    ignore_path1 = "Vehicle.MotionManagement.Suspension.Axle.Row2.Wheel.Left.DampingForce"
    ignore_path2 = "Vehicle.MotionManagement.Suspension.Axle.Row2.Wheel.Right.DampingForce"
    ignore_path_fallback_to_global = (VhalAreaType.VEHICLE_AREA_TYPE_GLOBAL, 0)
    assert item.resolve_area_type(keep_path) == keep_path_area_type
    assert item.resolve_area_type(ignore_path1) == ignore_path_fallback_to_global
    assert item.resolve_area_type(ignore_path2) == ignore_path_fallback_to_global


def test_vhal_area_constants_get_extracted_instance():
    vss_path = "Vehicle.Cabin.Door.Row1.DriverSide.IsChildLockActive"
    assert get_extracted_instance_parts(vss_path) == ("Row1", "DriverSide")
    assert get_extracted_instance_parts("Vehicle.Powertrain.FuelSystem.TankCapacity") == ()

    vss_path_mixed = "Vehicle.MotionManagement.Brake.Axle.Row2.Wheel.Left.Torque"
    assert get_extracted_instance_parts(vss_path_mixed) == ("Row2", "Left")
    assert get_extracted_instance_parts("") == ()


def test_vhal_area_constants_get_area_id():
    seat_area_type = VhalAreaType.VEHICLE_AREA_TYPE_SEAT
    seat_instances = ("Row1", "DriverSide")
    seat_area_value = 1
    assert get_area_id(seat_area_type, seat_instances) == seat_area_value

    # No mapping found for the tuple
    assert get_area_id(seat_area_type, ("Row4", "PassengerSide")) is None


def test_vhal_area_constants_get_explicit_area_id():
    window_area_type = VhalAreaType.VEHICLE_AREA_TYPE_WINDOW
    window_area_value_str = "front_windshield"
    window_area_value = 1
    assert get_explicit_area_id(window_area_type, window_area_value_str) == window_area_value

    # Invalid area value string
    assert get_explicit_area_id(window_area_type, "front") is None


def test_load_continuous_list():
    mapper = VhalMapper(include_new=True, group=1, starting_id=32768, override_units=False, override_datatype=False)
    file = HERE / "continuous.json"
    mapper.load_continuous_list(file)


def test_save():
    mapper = VhalMapper(include_new=True, group=1, starting_id=32768, override_units=False, override_datatype=False)

    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "output.json"
        mapper.safe(file)


# INTEGRATION TESTS


def test_cli():
    with tempfile.TemporaryDirectory() as tmp:
        output_path = Path(tmp)
        (output_path / "vendor/car/packages/services/Oem/oem-service/res/values/").mkdir(parents=True)
        (
            output_path / "vendor/car/hardware/interfaces/automotive/vehicle/aidl_property"
            "/vendor/android/hardware/automotive/vehicle/"
        ).mkdir(parents=True)

        cmd = "vspec export vhal".split() + [
            "--no-extend-new",
            "--vspec",
            HERE / "vehicle_signal_specification/vss.vspec",
            "--vhal-map",
            HERE / "validation_group_1_min_32768.json",
            "--vhal-area-config",
            HERE / "vhal_area_config.json",
            "--aosp-workspace-path",
            output_path,
        ]
        process = subprocess.run(cmd, capture_output=True, text=True)
        assert process.returncode == 0


def test_load_group_1(validation_properties_group_1):
    mapper = VhalMapper(include_new=True, group=1, starting_id=32768, override_units=False, override_datatype=False)

    tree, datatype_tree = get_trees(
        vspec=HERE / "vehicle_signal_specification/vss.vspec",
        include_dirs=(),
        aborts=(),
        strict=False,
        extended_attributes=(),
        quantities=(),
        units=(),
        types=(),
        overlays=(),
        expand=True,
    )

    reference_file_path: Path = HERE / "validation_jsons/validation_group_1_min_32768.json"
    properties = mapper.load(reference_file_path, tree)
    vss_dict = {source: leaf.property_id for leaf in properties for source in leaf.sources}
    validation_dict = {source: leaf.property_id for leaf in validation_properties_group_1 for source in leaf.sources}
    assert vss_dict == validation_dict


def test_uniqueness(vss_properties_group_4: List[VehicleMappingItem]):
    unique_ids = {leaf.property_id for leaf in vss_properties_group_4}
    assert len(vss_properties_group_4) == len(unique_ids)


def test_determinism_for_group_1_invalid():
    with pytest.raises(SystemExit) as e:
        __validation_properties(group=1, min_id=100)
    assert e.value.code == 1


def test_determinism_for_group_1(validation_properties_group_1, vss_properties_group_1: List[VehicleMappingItem]):
    vss_dict = {source: leaf.property_id for leaf in vss_properties_group_1 for source in leaf.sources}
    validation_dict = {source: leaf.property_id for leaf in validation_properties_group_1 for source in leaf.sources}
    assert vss_dict == validation_dict


def test_determinism_for_group_2(validation_properties_group_2, vss_properties_group_2: List[VehicleMappingItem]):
    vss_dict = {source: leaf.property_id for leaf in vss_properties_group_2 for source in leaf.sources}
    validation_dict = {source: leaf.property_id for leaf in validation_properties_group_2 for source in leaf.sources}
    assert vss_dict == validation_dict


def test_determinism_for_group_4(validation_properties_group_4, vss_properties_group_4: List[VehicleMappingItem]):
    vss_dict = {source: leaf.property_id for leaf in vss_properties_group_4 for source in leaf.sources}
    validation_dict = {source: leaf.property_id for leaf in validation_properties_group_4 for source in leaf.sources}
    assert vss_dict == validation_dict


def test_overwrite_manually_updated_mapping(
    validation_properties_group_4_with_manual_updates: List[VehicleMappingItem],
    vss_properties_group_4_with_manual_updates: List[VehicleMappingItem],
):
    vss_dict = {
        source: leaf.property_id for leaf in vss_properties_group_4_with_manual_updates for source in leaf.sources
    }
    validation_dict = {
        source: leaf.property_id
        for leaf in validation_properties_group_4_with_manual_updates
        for source in leaf.sources
    }
    assert vss_dict == validation_dict


def test_overwrite_manually_updated_mapping_override(
    validation_properties_group_4: List[VehicleMappingItem],
    vss_properties_group_4_with_manual_updates_override: List[VehicleMappingItem],
):
    vss_dict = {
        source: leaf.property_id
        for leaf in vss_properties_group_4_with_manual_updates_override
        for source in leaf.sources
    }
    validation_dict = {source: leaf.property_id for leaf in validation_properties_group_4 for source in leaf.sources}
    assert vss_dict == validation_dict


def test_vss_update(
    validation_properties_group_4_update: List[VehicleMappingItem],
    vss_properties_group_4_update: List[VehicleMappingItem],
):
    vss_dict = {source: leaf.property_id for leaf in vss_properties_group_4_update for source in leaf.sources}
    validation_dict = {
        source: leaf.property_id for leaf in validation_properties_group_4_update for source in leaf.sources
    }
    assert vss_dict == validation_dict


def test_java_property_ids_code(java_property_ids_code: str, vhal_mapper_group_4: VhalMapper):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        java_output = path / "VehiclePropertyIdsOem.java"
        actual_code = vhal_mapper_group_4.generate_java_files(java_output)
        assert java_property_ids_code == actual_code


def test_java_permissions_code(java_permissions_code: str, vhal_mapper_group_4: VhalMapper):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        permissions_output = path / "OemPermissions.java"
        actual_code = vhal_mapper_group_4.generate_permission_files(permissions_output)
        assert java_permissions_code == actual_code


def test_aidl_code(aidl_code: str, vhal_mapper_group_4: VhalMapper):
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "VehiclePropertyOem.aidl"
        actual_code = vhal_mapper_group_4.generate_aidl_file(file)
        assert aidl_code == actual_code


def test_car_service_android_manifest(car_service_android_manifest_code: str, vhal_mapper_group_4: VhalMapper):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        (path / "vendor/car/packages/services/Oem/oem-service/res/values/").mkdir(parents=True)
        actual_code, _ = vhal_mapper_group_4.generate_xml_files(path)
        assert car_service_android_manifest_code.rstrip() == actual_code.rstrip()


def test_car_service_strings(car_service_strings_code: str, vhal_mapper_group_4: VhalMapper):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        (path / "vendor/car/packages/services/Oem/oem-service/res/values/").mkdir(parents=True)
        _, actual_code = vhal_mapper_group_4.generate_xml_files(path)
        assert car_service_strings_code.rstrip() == actual_code.rstrip()

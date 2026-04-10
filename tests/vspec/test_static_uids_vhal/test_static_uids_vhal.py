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
from vss_tools.exporters.vhal import VhalMapper
from vss_tools.main import get_trees
from vss_tools.utils.vhal.property_constants import (
    VehiclePropertyAccess,
    VehiclePropertyChangeMode,
    VhalAreaType,
    VhalPropertyGroup,
)
from vss_tools.utils.vhal.vehicle_mapping import VehicleMappingItem

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
    assert VhalAreaType.get_java_doc(0) == "VEHICLE_AREA_TYPE_GLOBAL"
    assert VhalAreaType.get_java_doc(7) == "VEHICLE_AREA_TYPE_VENDOR"
    with pytest.raises(SystemExit) as e:
        VhalAreaType.get_java_doc(2)
    assert e.value.code == 1


def test_vhal_property_group():
    assert VhalPropertyGroup.get(1) == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_SYSTEM
    assert VhalPropertyGroup.get(2) == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_VENDOR
    assert VhalPropertyGroup.get(3) == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_BACKPORTED
    assert VhalPropertyGroup.get(4) == VhalPropertyGroup.VEHICLE_PROPERTY_GROUP_OEM
    with pytest.raises(SystemExit) as e:
        VhalPropertyGroup.get(5)
    assert e.value.code == 1


def test_vhal_vehicle_property_access():
    assert VehiclePropertyAccess.get_java_doc(1) == "VEHICLE_PROPERTY_ACCESS_READ"
    assert VehiclePropertyAccess.get_java_doc(2) == "VEHICLE_PROPERTY_ACCESS_WRITE"
    assert VehiclePropertyAccess.get_java_doc(3) == "VEHICLE_PROPERTY_ACCESS_READ_WRITE"
    with pytest.raises(SystemExit) as e:
        VehiclePropertyAccess.get_java_doc(4)
    assert e.value.code == 1


def test_vhal_vehicle_property_change_mode():
    assert VehiclePropertyChangeMode.get_java_doc(0) == "VEHICLE_PROPERTY_CHANGE_MODE_STATIC"
    assert VehiclePropertyChangeMode.get_java_doc(1) == "VEHICLE_PROPERTY_CHANGE_MODE_ONCHANGE"
    assert VehiclePropertyChangeMode.get_java_doc(2) == "VEHICLE_PROPERTY_CHANGE_MODE_CONTINUOUS"
    with pytest.raises(SystemExit) as e:
        VehiclePropertyChangeMode.get_java_doc(3)
    assert e.value.code == 1


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
    vss_dict = {leaf.source: leaf.property_id for leaf in properties}
    validation_dict = {leaf.source: leaf.property_id for leaf in validation_properties_group_1}
    assert vss_dict == validation_dict


def test_uniqueness(vss_properties_group_4: List[VehicleMappingItem]):
    unique_ids = {leaf.property_id for leaf in vss_properties_group_4}
    assert len(vss_properties_group_4) == len(unique_ids)


def test_determinism_for_group_1_invalid():
    with pytest.raises(SystemExit) as e:
        __validation_properties(group=1, min_id=100)
    assert e.value.code == 1


def test_determinism_for_group_1(validation_properties_group_1, vss_properties_group_1: List[VehicleMappingItem]):
    vss_dict = {leaf.source: leaf.property_id for leaf in vss_properties_group_1}
    validation_dict = {leaf.source: leaf.property_id for leaf in validation_properties_group_1}
    assert vss_dict == validation_dict


def test_determinism_for_group_2(validation_properties_group_2, vss_properties_group_2: List[VehicleMappingItem]):
    vss_dict = {leaf.source: leaf.property_id for leaf in vss_properties_group_2}
    validation_dict = {leaf.source: leaf.property_id for leaf in validation_properties_group_2}
    assert vss_dict == validation_dict


def test_determinism_for_group_4(validation_properties_group_4, vss_properties_group_4: List[VehicleMappingItem]):
    vss_dict = {leaf.source: leaf.property_id for leaf in vss_properties_group_4}
    validation_dict = {leaf.source: leaf.property_id for leaf in validation_properties_group_4}
    assert vss_dict == validation_dict


def test_overwrite_manually_updated_mapping(
    validation_properties_group_4_with_manual_updates: List[VehicleMappingItem],
    vss_properties_group_4_with_manual_updates: List[VehicleMappingItem],
):
    vss_dict = {leaf.source: leaf.property_id for leaf in vss_properties_group_4_with_manual_updates}
    validation_dict = {leaf.source: leaf.property_id for leaf in validation_properties_group_4_with_manual_updates}
    assert vss_dict == validation_dict


def test_overwrite_manually_updated_mapping_override(
    validation_properties_group_4: List[VehicleMappingItem],
    vss_properties_group_4_with_manual_updates_override: List[VehicleMappingItem],
):
    vss_dict = {leaf.source: leaf.property_id for leaf in vss_properties_group_4_with_manual_updates_override}
    validation_dict = {leaf.source: leaf.property_id for leaf in validation_properties_group_4}
    assert vss_dict == validation_dict


def test_vss_update(
    validation_properties_group_4_update: List[VehicleMappingItem],
    vss_properties_group_4_update: List[VehicleMappingItem],
):
    vss_dict = {leaf.source: leaf.property_id for leaf in vss_properties_group_4_update}
    validation_dict = {leaf.source: leaf.property_id for leaf in validation_properties_group_4_update}
    assert vss_dict == validation_dict


def test_java_property_ids_code(java_property_ids_code: str, vhal_mapper_group_4: VhalMapper):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        java_output = path / "VehiclePropertyIdsOem.java"
        permissions_output = path / "OemPermissions.java"
        actual_code, _ = vhal_mapper_group_4.generate_java_files(java_output, permissions_output)
        assert java_property_ids_code == actual_code


def test_java_permissions_code(java_permissions_code: str, vhal_mapper_group_4: VhalMapper):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        java_output = path / "VehiclePropertyIdsOem.java"
        permissions_output = path / "OemPermissions.java"
        _, actual_code = vhal_mapper_group_4.generate_java_files(java_output, permissions_output)
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

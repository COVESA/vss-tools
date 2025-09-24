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

from pathlib import Path
from typing import List, Optional

import pytest
from vss_tools.exporters.vhal import VhalMapper
from vss_tools.main import get_trees
from vss_tools.utils.vhal.vehicle_mapping import VehicleMappingItem

# HELPERS


# FIXTURES


def __validation_properties(group: int, min_id: int = 1, suffix="") -> List[VehicleMappingItem]:
    # read reference vss leaves and corresponding generated property ids
    filename = f"validation_group_{group}_min_{min_id}.json" if min_id > 1 else f"validation_group_{group}{suffix}.json"
    reference_file_path: Path = Path(__file__).resolve().parents[0] / "validation_jsons" / filename

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
    path_spec = Path(__file__).resolve().parents[0] / "vehicle_signal_specification"
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
        mapper.load_mapping(Path(__file__).resolve().parents[0] / "validation_jsons" / f"{mapping}.json")
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
    with open(Path(__file__).resolve().parents[0] / "validation_jsons" / "VehiclePropertyIdsVss.java", "r") as file:
        return file.read()


@pytest.fixture(scope="session")
def java_permissions_code() -> str:
    with open(Path(__file__).resolve().parents[0] / "validation_jsons" / "VssPermissions.java", "r") as file:
        return file.read()


@pytest.fixture(scope="session")
def aidl_code() -> str:
    with open(Path(__file__).resolve().parents[0] / "validation_jsons" / "VehiclePropertyVss.aidl", "r") as file:
        return file.read()


# INTEGRATION TESTS


def test_uniqueness(vss_properties_group_4: List[VehicleMappingItem]):
    unique_ids = {leaf.property_id for leaf in vss_properties_group_4}
    assert len(vss_properties_group_4) == len(unique_ids)


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
    actual_code, _ = vhal_mapper_group_4.generate_java_files()
    assert java_property_ids_code == actual_code


def test_java_permissions_code(java_permissions_code: str, vhal_mapper_group_4: VhalMapper):
    _, actual_code = vhal_mapper_group_4.generate_java_files()
    assert java_permissions_code == actual_code


def test_aidl_code(aidl_code: str, vhal_mapper_group_4: VhalMapper):
    actual_code = vhal_mapper_group_4.generate_aidl_file()
    assert aidl_code == actual_code

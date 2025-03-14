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

import json
from pathlib import Path
from typing import Dict, List

import pytest
from vss_tools.exporters.vhal import VhalMapper
from vss_tools.main import get_trees
from vss_tools.utils.vhal.vehicle_mapping import VehicleMappingItem

# HELPERS


# FIXTURES


@pytest.fixture(scope="session")
def validation_dict() -> Dict[str, int]:
    # read reference vss leaves and corresponding generated property ids
    reference_file_path: str = (Path(__file__).resolve().parents[0] / "validation_jsons" / "validation.json").as_posix()
    validation_dict: Dict[str, int] = {}
    with open(reference_file_path) as reference_file:
        properties = json.load(reference_file)
        for prop in properties:
            validation_dict[prop["source"]] = prop["propertyId"]

    return validation_dict


@pytest.fixture(scope="session")
def vss_properties() -> List[VehicleMappingItem]:
    path_spec = Path(__file__).resolve().parents[4] / "vehicle_signal_specification" / "spec"
    vspec_file = "VehicleSignalSpecification.vspec"

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

    mapper = VhalMapper(include_new=True, group=1, starting_id=32768, override_units=False, override_datatype=False)
    mapper.load_vss_tree(tree)

    return mapper.get()


# INTEGRATION TESTS


@pytest.mark.skip
def test_uniqueness(vss_properties: List[VehicleMappingItem]):
    unique_ids = {leaf.propertyId for leaf in vss_properties}
    assert len(vss_properties) == len(unique_ids)


@pytest.mark.skip
def test_determinism(validation_dict, vss_properties: List[VehicleMappingItem]):
    test_dict = {leaf.source: leaf.propertyId for leaf in vss_properties}
    assert test_dict == validation_dict

# Copyright (c) 2020 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pytest
import os

from vspec.model.constants import VSSType, VSSDataType, VSSUnitCollection, VSSTreeType
from vspec.model.constants import VSSUnit, VSSQuantity


@pytest.mark.parametrize("unit_file",
                         ['explicit_units.yaml',
                          'explicit_units_old_syntax.yaml'])
def test_manually_loaded_units(unit_file):
    """
    Test correct parsing of units
    """
    unit_file = os.path.join(os.path.dirname(__file__), unit_file)
    VSSUnitCollection.load_config_file(unit_file)
    assert VSSUnitCollection.get_unit("puncheon") == "puncheon"
    assert VSSUnitCollection.get_unit("puncheon").definition == \
           "Volume measure in puncheons (1 puncheon = 318 liters)"
    assert VSSUnitCollection.get_unit("puncheon").unit == \
           "Puncheon"
    assert VSSUnitCollection.get_unit("puncheon").quantity == \
           "volume"


def test_invalid_unit():
    assert VSSUnitCollection.get_unit("unknown") is None


@pytest.mark.parametrize("type_enum,type_str",
                         [(VSSType.BRANCH, "branch"),
                          (VSSType.ATTRIBUTE, "attribute"),
                          (VSSType.SENSOR, "sensor"),
                          (VSSType.ACTUATOR, "actuator"),
                          (VSSType.PROPERTY, "property")])
def test_vss_types(type_enum, type_str, ):
    """
    Test correct parsing of VSS Types
    """

    assert type_enum == VSSType.from_str(type_str)


def test_invalid_vss_types():
    with pytest.raises(Exception):
        VSSType.from_str("not_a_valid_case")


@pytest.mark.parametrize("data_type_enum,data_type_str",
                         [(VSSDataType.INT8, "int8"),
                          (VSSDataType.UINT8, "uint8"),
                          (VSSDataType.INT16, "int16"),
                          (VSSDataType.UINT16, "uint16"),
                          (VSSDataType.INT32, "int32"),
                          (VSSDataType.UINT32, "uint32"),
                          (VSSDataType.INT64, "int64"),
                          (VSSDataType.UINT64, "uint64"),
                          (VSSDataType.BOOLEAN, "boolean"),
                          (VSSDataType.FLOAT, "float"),
                          (VSSDataType.DOUBLE, "double"),
                          (VSSDataType.STRING, "string")])
def test_vss_data_types(data_type_enum, data_type_str, ):
    """
    Test correct parsing of VSS Data Types
    """
    assert data_type_enum == VSSDataType.from_str(data_type_str)


def test_invalid_vss_data_types():
    with pytest.raises(Exception):
        VSSDataType.from_str("not_a_valid_case")


@pytest.mark.parametrize("tree_type_enum,tree_type_str, important_types",
                         [(VSSTreeType.SIGNAL_TREE, "signal_tree", ["sensor", "actuator", "attribute", "branch"]),
                          (VSSTreeType.DATA_TYPE_TREE, "data_type_tree", ["struct", "property", "branch"])])
def test_vss_tree_types(tree_type_enum, tree_type_str, important_types):
    """
    Test correct parsing of VSS Tree Types
    """

    assert tree_type_enum == VSSTreeType.from_str(tree_type_str)
    available_types = tree_type_enum.available_types()
    for t in important_types:
        assert t in available_types


def test_invalid_vss_tree_types():
    with pytest.raises(Exception):
        VSSDataType.from_str("not_a_valid_case")


def test_unit():
    """ Test Unit class """
    item = VSSUnit("myid", "myunit", "mydefinition", "myquantity")
    assert item.value == "myid"
    assert item.unit == "myunit"
    assert item.definition == "mydefinition"
    assert item.quantity == "myquantity"
    # String subclass so just comparing shall get "myid"
    assert item == "myid"


def test_quantity():
    """ Test Quantity class """
    item = VSSQuantity("myid", "mydefinition", "myremark", "mycomment")
    assert item.value == "myid"
    assert item.definition == "mydefinition"
    assert item.remark == "myremark"
    assert item.comment == "mycomment"
    # String subclass so just comparing shall get "myid"
    assert item == "myid"

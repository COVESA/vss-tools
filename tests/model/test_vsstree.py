# Copyright (c) 2020 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import unittest
import os
import pytest

from vspec.model.constants import VSSType, VSSDataType, VSSUnitCollection, VSSTreeType
from vspec.model.vsstree import VSSNode
from vspec.model.exceptions import NameStyleValidationException


class TestVSSNode(unittest.TestCase):
    def test_simple_construction(self):
        """
        Test minimal object construction.
        """
        source = {
            "description": "some desc",
            "type": "branch",
            "uuid": "26d6e362-a422-11ea-bb37-0242ac130002",
            "$file_name$": "testfile"}
        node = VSSNode(
            "test",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        self.assertIsNotNone(node)
        self.assertEqual("some desc", node.description)
        self.assertEqual(VSSType.BRANCH, node.type)
        self.assertEqual("26d6e362-a422-11ea-bb37-0242ac130002", node.uuid)
        self.assertFalse(node.has_unit())
        self.assertFalse(node.has_datatype())

    def test_complex_construction(self):
        """
        Test complex object construction.
        """
        source = {"description": "some desc", "type": "sensor", "uuid": "26d6e362-a422-11ea-bb37-0242ac130002",
                  "datatype": "uint8", "unit": "hogshead", "min": 0, "max": 100, "allowed": ["one", "two"],
                  "aggregate": False,
                  "default": "test-default", "$file_name$": "testfile"}
        unit_file = os.path.join(os.path.dirname(__file__), 'explicit_units.yaml')
        VSSUnitCollection.load_config_file(unit_file)
        node = VSSNode(
            "test",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        self.assertIsNotNone(node)
        self.assertEqual("some desc", node.description)
        self.assertEqual(VSSType.SENSOR, node.type)
        self.assertEqual("26d6e362-a422-11ea-bb37-0242ac130002", node.uuid)
        self.assertEqual(VSSDataType.UINT8, node.datatype)
        self.assertEqual(VSSUnitCollection.get_unit("hogshead"), node.unit)
        self.assertEqual(0, node.min)
        self.assertEqual(100, node.max)
        self.assertEqual(["one", "two"], node.allowed)
        self.assertEqual(False, node.aggregate)
        self.assertEqual("test-default", node.default)
        self.assertTrue(node.has_unit())
        self.assertTrue(node.has_datatype())

    def test_merge_nodes(self):
        """
        Tests if merging two nodes works as expected
        """

        target = {
            "description": "some desc",
            "type": "sensor",
            "datatype": "float",
            "uuid": "e36a1d8c-4d06-4c22-ba69-e8b39434a7a3",
            "$file_name$": "testfile"}

        source = {"description": "some desc", "type": "sensor",
                  "uuid": "2cc90035-e1c2-43bf-a394-1a439addc8ad",
                  "datatype": "uint8", "unit": "hogshead", "min": 0, "max": 100, "$file_name$": "testfile"}

        unit_file = os.path.join(os.path.dirname(__file__), 'explicit_units.yaml')
        VSSUnitCollection.reset_units()
        VSSUnitCollection.load_config_file(unit_file)

        node_target = VSSNode(
            "MyNode",
            target,
            VSSTreeType.SIGNAL_TREE.available_types())
        node_source = VSSNode(
            "MyNode2",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        self.assertEqual(
            "e36a1d8c-4d06-4c22-ba69-e8b39434a7a3",
            node_target.uuid)
        self.assertTrue(node_target.has_datatype())
        self.assertEqual(
            "2cc90035-e1c2-43bf-a394-1a439addc8ad",
            node_source.uuid)

        node_target.merge(node_source)
        self.assertEqual(
            "2cc90035-e1c2-43bf-a394-1a439addc8ad",
            node_target.uuid)
        self.assertTrue(node_target.has_datatype())
        self.assertEqual(VSSDataType.UINT8, node_target.datatype)
        self.assertEqual(VSSUnitCollection.get_unit("hogshead"), node_target.unit)
        self.assertEqual(0, node_target.min)
        self.assertEqual(100, node_target.max)

    def test_unit_datatype(self):

        unit_file = os.path.join(os.path.dirname(__file__), 'explicit_units.yaml')
        VSSUnitCollection.reset_units()
        VSSUnitCollection.load_config_file(unit_file)

        # int16 explicitly listed

        source = {"description": "some desc", "type": "sensor",
                  "uuid": "2cc90035-e1c2-43bf-a394-1a439addc8ad",
                  "datatype": "int16", "unit": "puncheon", "min": 0, "max": 100, "$file_name$": "testfile"}

        node_source = VSSNode(
            "MyNode2",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        assert node_source.unit == VSSUnitCollection.get_unit("puncheon")

        # uint16 explicitly listed

        source = {"description": "some desc", "type": "sensor",
                  "uuid": "2cc90035-e1c2-43bf-a394-1a439addc8ad",
                  "datatype": "uint16", "unit": "puncheon", "min": 0, "max": 100, "$file_name$": "testfile"}

        node_source = VSSNode(
            "MyNode2",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        assert node_source.unit == VSSUnitCollection.get_unit("puncheon")

        # uint16[] is ok as uint16 is explicitly listed

        source = {"description": "some desc", "type": "sensor",
                  "uuid": "2cc90035-e1c2-43bf-a394-1a439addc8ad",
                  "datatype": "uint16[]", "unit": "puncheon", "min": 0, "max": 100, "$file_name$": "testfile"}

        node_source = VSSNode(
            "MyNode2",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        assert node_source.unit == VSSUnitCollection.get_unit("puncheon")

        source = {"description": "some desc", "type": "sensor",
                  "uuid": "2cc90035-e1c2-43bf-a394-1a439addc8ad",
                  "datatype": "float", "unit": "puncheon", "min": 0, "max": 100, "$file_name$": "testfile"}

        # float not ok

        with pytest.raises(SystemExit):
            node_source = VSSNode(
                "MyNode2",
                source,
                VSSTreeType.SIGNAL_TREE.available_types())

        # Hogshead defined as "numeric", i.e. all numeric types shall be accepted

        source = {"description": "some desc", "type": "sensor",
                  "uuid": "2cc90035-e1c2-43bf-a394-1a439addc8ad",
                  "datatype": "uint16", "unit": "hogshead", "min": 0, "max": 100, "$file_name$": "testfile"}

        node_source = VSSNode(
            "MyNode2",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        assert node_source.unit == VSSUnitCollection.get_unit("hogshead")

        # Also array of numeric

        source = {"description": "some desc", "type": "sensor",
                  "uuid": "2cc90035-e1c2-43bf-a394-1a439addc8ad",
                  "datatype": "uint16[]", "unit": "hogshead", "min": 0, "max": 100, "$file_name$": "testfile"}

        node_source = VSSNode(
            "MyNode2",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        assert node_source.unit == VSSUnitCollection.get_unit("hogshead")

        # But not string

        source = {"description": "some desc", "type": "sensor",
                  "uuid": "2cc90035-e1c2-43bf-a394-1a439addc8ad",
                  "datatype": "string", "unit": "hogshead", "min": 0, "max": 100, "$file_name$": "testfile"}

        with pytest.raises(SystemExit):
            node_source = VSSNode(
                "MyNode2",
                source,
                VSSTreeType.SIGNAL_TREE.available_types())

    def test_tree_find(self):
        """
        Test if tree can be found within VSS tree
        """
        source_root = {
            "description": "High-level vehicle data.",
            "type": "branch",
            "uuid": "f6750f15-ba2f-4eab-adcc-19a500982293",
            "$file_name$": "testfile"}
        source_drivetrain = {
            "description": "Drivetrain branch.",
            "type": "branch",
            "uuid": "5fb3f710-ed60-426b-a083-015cc7c7bc1b",
            "$file_name$": "testfile"}
        source_drivetrain_element = {
            "description": "Some Drivetrain element.",
            "type": "sensor",
            "datatype": "string",
            "uuid": "9101bbea-aeb6-4b0e-8cec-d8b126e77898",
            "$file_name$": "testfile"}
        node_root = VSSNode(
            "Vehicle",
            source_root,
            VSSTreeType.SIGNAL_TREE.available_types())
        node_drivetrain = VSSNode(
            "Drivetrain",
            source_drivetrain,
            VSSTreeType.SIGNAL_TREE.available_types(),
            node_root)
        # No need to store create node to a variable on next line
        VSSNode(
            "SomeElement",
            source_drivetrain_element,
            VSSTreeType.SIGNAL_TREE.available_types(),
            node_drivetrain)

        self.assertTrue(
            VSSNode.node_exists(
                node_root,
                "/Vehicle/Drivetrain/SomeElement"))

    def test_orphan_detection(self):
        """
        Test if vssnode finds orphan (r)branches.
        """
        source_root = {
            "description": "High-level vehicle data.",
            "type": "branch",
            "uuid": "f6750f15-ba2f-4eab-adcc-19a500982293",
            "$file_name$": "testfile"}
        source_drivetrain = {
            "description": "Drivetrain branch.",
            "type": "branch",
            "uuid": "5fb3f710-ed60-426b-a083-015cc7c7bc1b",
            "$file_name$": "testfile"}
        node_root = VSSNode(
            "Vehicle",
            source_root,
            VSSTreeType.SIGNAL_TREE.available_types())
        node_drivetrain = VSSNode(
            "Drivetrain",
            source_drivetrain,
            VSSTreeType.SIGNAL_TREE.available_types(),
            node_root)

        self.assertTrue(node_drivetrain.is_orphan())

    def test_name_style_string(self):

        source = {
            "description": "Some element.",
            "type": "sensor",
            "datatype": "string",
            "$file_name$": "testfile"}

        node = VSSNode(
            "this_name_is_not_allowed_in_standard_catalog",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        with pytest.raises(NameStyleValidationException):
            node.validate_name_style("dummyfile")

        node = VSSNode(
            "ButThisNameIs",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        # No exception expected
        node.validate_name_style("dummyfile")

    def test_name_style_boolean(self):

        source = {
            "description": "Some element.",
            "type": "sensor",
            "datatype": "boolean",
            "$file_name$": "testfile"}

        node = VSSNode(
            "this_name_is_not_allowed_in_standard_catalog",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        with pytest.raises(NameStyleValidationException):
            node.validate_name_style("dummyfile")

        # Boolean ones must start with "Is"
        node = VSSNode(
            "ThisNameNeither",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        with pytest.raises(NameStyleValidationException):
            node.validate_name_style("dummyfile")

        node = VSSNode(
            "IsThisAllowedYesItIs",
            source,
            VSSTreeType.SIGNAL_TREE.available_types())
        # No exception expected
        node.validate_name_style("dummyfile")


if __name__ == '__main__':
    unittest.main()

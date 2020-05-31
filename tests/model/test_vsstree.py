import unittest

from model.constants import VSSType, VSSDataType, Unit, StringStyle
from model.vsstree import VSSNode


class TestVSSNode(unittest.TestCase):
    def test_simple_construction(self):
        """
        Test minimal object construction.
        """
        source = {"description": "some desc", "type": "sensor", "uuid": "26d6e362-a422-11ea-bb37-0242ac130002"}
        node = VSSNode("test", source)
        self.assertIsNotNone(node)
        self.assertEqual("some desc", node.description)
        self.assertEqual(VSSType.SENSOR, node.type)
        self.assertEqual("26d6e362-a422-11ea-bb37-0242ac130002", node.uuid)
        self.assertFalse(node.has_unit())
        self.assertFalse(node.has_data_type())
        self.assertFalse(node.is_private())

    def test_complex_construction(self):
        """
        Test complex object construction.
        """
        source = {"description": "some desc", "type": "sensor", "uuid": "26d6e362-a422-11ea-bb37-0242ac130002",
                  "datatype": "uint8", "unit": "km", "min": 0, "max": 100, "enum": ["one", "two"], "aggregate": False,
                  "default": "test-default", "value": "test-value", "instances": ["i1", "i2"]}
        node = VSSNode("test", source)
        self.assertIsNotNone(node)
        self.assertEqual("some desc", node.description)
        self.assertEqual(VSSType.SENSOR, node.type)
        self.assertEqual("26d6e362-a422-11ea-bb37-0242ac130002", node.uuid)
        self.assertEqual(VSSDataType.UINT8, node.data_type)
        self.assertEqual(Unit.KILOMETER, node.unit)
        self.assertEqual(0, node.min)
        self.assertEqual(100, node.max)
        self.assertEqual(["one", "two"], node.enum)
        self.assertEqual(False, node.aggregate)
        self.assertEqual("test-default", node.default_value)
        self.assertEqual("test-value", node.value)
        self.assertEqual(["i1", "i2"], node.instances)
        self.assertTrue(node.has_unit())
        self.assertTrue(node.has_data_type())
        self.assertFalse(node.is_private())

    def test_private_attribute(self):
        """
        Test if private attribute construction is correctly working.
        """
        source_root = {"description": "High-level vehicle data.", "type": "branch", "uuid": "f6750f15-ba2f-4eab-adcc-19a500982293"}
        source_private = {"description": "Private vehicle data.", "type": "branch", "uuid": "5fb3f710-ed60-426b-a083-015cc7c7bc1b"}
        source_private_element = {"description": "Private vehicle data.", "type": "sensor", "datatype": "string", "uuid": "9101bbea-aeb6-4b0e-8cec-d8b126e77898"}
        node_root = VSSNode("Vehicle", source_root)
        node_private = VSSNode("Private", source_private, node_root)
        node_private_element = VSSNode("Element", source_private_element, node_private)

        self.assertTrue(node_private_element.is_private())
        self.assertEqual("Vehicle.Private.Element", node_private_element.qualified_name('.', StringStyle.NONE))

    def test_merge_nodes(self):
        """
        Tests if merging two nodes works as expected
        """

        target = {"description": "some desc", "type": "sensor", "uuid": "e36a1d8c-4d06-4c22-ba69-e8b39434a7a3"}

        source = {"description": "some desc", "type": "sensor", "uuid": "2cc90035-e1c2-43bf-a394-1a439addc8ad",
                  "datatype": "uint8", "unit": "km", "min": 0, "max": 100}

        node_target = VSSNode("MyNode", target)
        node_source = VSSNode("Private", source)
        self.assertEqual("e36a1d8c-4d06-4c22-ba69-e8b39434a7a3", node_target.uuid)
        self.assertFalse(node_target.has_data_type())
        self.assertEqual("2cc90035-e1c2-43bf-a394-1a439addc8ad", node_source.uuid)

        node_target.merge(node_source)
        self.assertEqual("2cc90035-e1c2-43bf-a394-1a439addc8ad", node_target.uuid)
        self.assertTrue(node_target.has_data_type())
        self.assertEqual(VSSDataType.UINT8, node_target.data_type)
        self.assertEqual(Unit.KILOMETER, node_target.unit)
        self.assertEqual(0, node_target.min)
        self.assertEqual(100, node_target.max)

    def test_string_tyle(self):
        """
        Tests string style conversion
        """
        source = {"description": "some desc", "type": "sensor", "uuid": "26d6e362-a422-11ea-bb37-0242ac130002"}
        node = VSSNode("test", source)

        self.assertEqual("TEST", node.qualified_name(".", StringStyle.UPPER_CASE))
        self.assertEqual("Test", node.qualified_name(".", StringStyle.CAPITAL_CASE))
        self.assertEqual("test", node.qualified_name(".", StringStyle.LOWER_CASE))

        source = {"description": "some desc", "type": "sensor", "uuid": "26d6e362-a422-11ea-bb37-0242ac130002"}
        node = VSSNode("LongerTestName", source)
        self.assertEqual("LONGERTESTNAME", node.qualified_name(".", StringStyle.UPPER_CASE))
        self.assertEqual("LongerTestName", node.qualified_name(".", StringStyle.CAPITAL_CASE))
        self.assertEqual("longertestname", node.qualified_name(".", StringStyle.LOWER_CASE))
        self.assertEqual("longer_test_name", node.qualified_name(".", StringStyle.SNAKE_CASE))
        self.assertEqual("longerTestName", node.qualified_name(".", StringStyle.CAMEL_BACK))

    def test_tree_find(self):
        """
        Test if tree can be found withing VSS tree
        """
        source_root = {"description": "High-level vehicle data.", "type": "branch", "uuid": "f6750f15-ba2f-4eab-adcc-19a500982293"}
        source_drivetrain = {"description": "Drivetrain branch.", "type": "branch", "uuid": "5fb3f710-ed60-426b-a083-015cc7c7bc1b"}
        source_drivetrain_element = {"description": "Some Drivetrain element.", "type": "sensor", "datatype": "string", "uuid": "9101bbea-aeb6-4b0e-8cec-d8b126e77898"}
        node_root = VSSNode("Vehicle", source_root)
        node_drivetrain = VSSNode("Drivetrain", source_drivetrain, node_root)
        node_drivetrain_element = VSSNode("SomeElement", source_drivetrain_element, node_drivetrain)

        self.assertFalse(node_drivetrain_element.is_private())
        self.assertTrue(VSSNode.node_exists(node_root, "/Vehicle/Drivetrain/SomeElement"))

    def test_orphan_detection(self):
        """
        Test if vssnode finds orphan (r)branches.
        """
        source_root = {"description": "High-level vehicle data.", "type": "branch", "uuid": "f6750f15-ba2f-4eab-adcc-19a500982293"}
        source_drivetrain = {"description": "Drivetrain branch.", "type": "branch", "uuid": "5fb3f710-ed60-426b-a083-015cc7c7bc1b"}
        node_root = VSSNode("Vehicle", source_root)
        node_drivetrain = VSSNode("Drivetrain", source_drivetrain, node_root)

        self.assertTrue(node_drivetrain.is_orphan())

if __name__ == '__main__':
    unittest.main()

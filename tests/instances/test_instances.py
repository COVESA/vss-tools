#!/usr/bin/env python3

#
# Copyright (C) 2022, Bayerische Motoren Werke Aktiengesellschaft (BMW AG)
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

from vspec.model.vsstree import VSSNode
from vspec.model.constants import VSSType, VSSTreeType
import vspec
import os
import sys
import re

myDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(myDir, "../.."))


### TEST SIMPLE INSTANCE STRUCTURE ###
# Goal: Check if simple (=not nested) instantiation works
#
# How: Define three instances in different ways and check,
# if the result matches every time
#
### TEST SIMPLE INSTANCE STRUCTURE ###


# Needed test files
TEST_FILES_SIMPLE = ["resources/instance_simple_range.vspec",
                     "resources/instance_simple_enum.vspec",
                     "resources/instance_simple_range_list.vspec",
                     "resources/instance_simple_enum_list.vspec"]

# test function: read in the files and compare the outcome


def test_simple_structures(request):
    test_path = os.path.dirname(request.fspath)
    for tfs in TEST_FILES_SIMPLE:
        # load the file
        tree = vspec.load_tree(os.path.join(test_path, tfs), [os.path.join(
            test_path, "resources/")], VSSTreeType.SIGNAL_TREE)

        # check if root node has 3 children
        assert len(tree.children) == 3

        list_of_instances = ["Vehicle.Test1",
                             "Vehicle.Test2",
                             "Vehicle.Test3"]

        for child in tree.children:
            assert child.qualified_name() in list_of_instances  # < list qualified names
            assert child.type == VSSType.BRANCH
            assert child.description == "High-level vehicle data."
            # < check that they have exactly one child, which is named...
            assert len(child.children) == 1
            assert child.children[0].name == "SomeThing"  # <... SomeThing
            assert child.children[0].type == VSSType.SENSOR
            assert child.children[0].description == "test"


### TEST COMPLEX INSTANCE STRUCTURE ###
# Goal: Check if a list of instantiations works
#
# How: Define a list of different numbers of instances that
# in different ways and check,
# if the result matches every time
#
### TEST COMPLEX INSTANCE STRUCTURE ###

# Needed test files
TEST_FILES_COMPLEX = ["resources/instance_complex_1.vspec",
                      "resources/instance_complex_2.vspec",
                      "resources/instance_complex_3.vspec",
                      "resources/instance_complex_4.vspec"]

# test function: read in the files and compare the outcome


def test_complex_structures(request):

    test_path = os.path.dirname(request.fspath)
    # helper function to check, if all information are present

    def check_instance_branch(branch: VSSNode, numberOfChildren: int):
        assert branch.type == VSSType.BRANCH
        assert branch.description == "High-level vehicle data."

    for tfs in TEST_FILES_COMPLEX:
        # load the file
        tree = vspec.load_tree(os.path.join(test_path, tfs), [os.path.join(
            test_path, "resources/")], VSSTreeType.SIGNAL_TREE)

        # check if root node has 1 child and check first instances
        assert len(tree.children) == 1
        assert tree.children[0].qualified_name() == "Vehicle.Test1"
        check_instance_branch(tree.children[0], 2)

        # go through the instances and check if expected structure maps
        for child in tree.children[0].children:
            # 2nd level: Test1.Test2 - Test1.Test3
            assert child.qualified_name() in [
                "Vehicle.Test1.Test2", "Vehicle.Test1.Test3"]
            check_instance_branch(child, 3)
            for child_2 in child.children:
                # 2nd level: Test1.Test2.Test4 - Test1.Test3.Test6
                print(child_2.qualified_name())
                assert None is not re.match(
                    "^Vehicle.Test1.Test(2|3).Test(4|5|6)",
                    child_2.qualified_name())
                check_instance_branch(child_2, 4)
                for child_3 in child_2.children:
                    # 3rd level: Test1.Test2.Test4.Test7 -
                    # Test1.Test3.Test6.Test10
                    assert None is not re.match(
                        "^Vehicle.Test1.Test(2|3).Test(4|5|6).Test(7|8|9|10)",
                        child_3.qualified_name())
                    check_instance_branch(child_3, 1)
                    assert 1 == len(child_3.children)
                    child_4 = child_3.children[0]
                    # 4th level: Test1.Test2.Test4.Test7.Test11 -
                    # Test1.Test3.Test6.Test10.Test11
                    assert None is not re.match(
                        "^Vehicle.Test1.Test(2|3).Test(4|5|6).Test(7|8|9|10).Test11",
                        child_4.qualified_name())
                    # All instances are expected to have one child
                    assert 1 == len(child_4.children)
                    assert child_4.children[0].name == "SomeThing"
                    assert child_4.children[0].type == VSSType.SENSOR
                    assert child_4.children[0].description == "test"


### TEST EXCLUSION FROM INSTANCE STRUCTURE ###
# Goal: Check if exclusion of certain nodes during instantiation work
#
# How: Exclude some nodes from instantiation and check if the
# structure is the expected one
#
### TEST EXCLUSION FROM INSTANCE STRUCTURE ###

# Needed test files
TEST_FILES_EXCLUDE = ["resources/instance_exclude_node.vspec"]


def test_exclusion_from_instance(request):
    test_path = os.path.dirname(request.fspath)
    for tfs in TEST_FILES_EXCLUDE:
        # load the file
        tree = vspec.load_tree(os.path.join(test_path, tfs), [os.path.join(
            test_path, "resources/")], VSSTreeType.SIGNAL_TREE)
        assert 6 == len(tree.children)
        name_list = []
        for child in tree.children:
            name_list.append(child.qualified_name())
            if "Vehicle.ExcludeSomeThing" == child.qualified_name():
                assert VSSType.BRANCH == child.type
                assert "ExcludeSomeThing description" == child.description
                assert 1 == len(child.children)
                child_2 = child.children[0]
                assert "Vehicle.ExcludeSomeThing.ExcludeSomethingLeaf" == child_2.qualified_name()
                assert "ExcludeSomethingLeaf description" == child_2.description
                assert VSSType.ACTUATOR == child_2.type

            elif "Vehicle.ExcludeNode" == child.qualified_name():
                assert "Vehicle.ExcludeNode" == child.qualified_name()
                assert "ExcludeNode description" == child.description
                assert VSSType.ATTRIBUTE == child.type

        assert "Vehicle.ExcludeSomeThing" in name_list
        assert "Vehicle.ExcludeNode" in name_list

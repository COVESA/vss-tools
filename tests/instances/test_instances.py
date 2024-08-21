# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import re
from pathlib import Path

import vss_tools.vspec.model as model
from anytree import RenderTree
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.tree import VSSNode

HERE = Path(__file__).resolve().parent
RESOURCES = HERE / "resources"


#  TEST SIMPLE INSTANCE STRUCTURE #
# Goal: Check if simple (=not nested) instantiation works
#
# How: Define three instances in different ways and check,
# if the result matches every time
#
# TEST SIMPLE INSTANCE STRUCTURE #


# Needed test files
TEST_FILES_SIMPLE = [
    "instance_simple_range.vspec",
    "instance_simple_enum.vspec",
    "instance_simple_range_list.vspec",
    "instance_simple_enum_list.vspec",
]


def test_simple_structures(request):
    for tfs in TEST_FILES_SIMPLE:
        # load the file
        print(tfs)
        tree, _ = get_trees(vspec=RESOURCES / tfs, include_dirs=(RESOURCES,))

        print(RenderTree(tree).by_attr())
        # check if root node has 3 children
        assert len(tree.children) == 3

        list_of_instances = ["Vehicle.Test1", "Vehicle.Test2", "Vehicle.Test3"]

        child: VSSNode
        for child in tree.children:
            assert child.get_fqn() in list_of_instances  # < list qualified names
            assert child.data.type == model.NodeType.BRANCH
            assert child.data.description == "High-level vehicle data."
            # < check that they have exactly one child, which is named...
            assert len(child.children) == 1
            assert child.children[0].name == "SomeThing"  # <... SomeThing
            assert child.children[0].data.type == model.NodeType.SENSOR
            assert child.children[0].data.description == "test"


# TEST COMPLEX INSTANCE STRUCTURE #
# Goal: Check if a list of instantiations works
#
# How: Define a list of different numbers of instances that
# in different ways and check,
# if the result matches every time
#
# TEST COMPLEX INSTANCE STRUCTURE #

# Needed test files
TEST_FILES_COMPLEX = [
    "instance_complex_1.vspec",
    "instance_complex_2.vspec",
    "instance_complex_3.vspec",
    "instance_complex_4.vspec",
]

# test function: read in the files and compare the outcome


def test_complex_structures():
    # helper function to check, if all information are present

    def check_instance_branch(branch: VSSNode, numberOfChildren: int):
        assert branch.data.type == model.NodeType.BRANCH
        assert branch.data.description == "High-level vehicle data."

    for tfs in TEST_FILES_COMPLEX:
        print(tfs)
        # load the file
        tree, _ = get_trees(vspec=RESOURCES / tfs, include_dirs=(RESOURCES,))

        # check if root node has 1 child and check first instances
        assert len(tree.children) == 1
        assert tree.children[0].get_fqn() == "Vehicle.Test1"
        check_instance_branch(tree.children[0], 2)

        # go through the instances and check if expected structure maps
        child: VSSNode
        for child in tree.children[0].children:
            # 2nd level: Test1.Test2 - Test1.Test3
            assert child.get_fqn() in [
                "Vehicle.Test1.Test2",
                "Vehicle.Test1.Test3",
            ]
            check_instance_branch(child, 3)
            child_2: VSSNode
            for child_2 in child.children:
                # 2nd level: Test1.Test2.Test4 - Test1.Test3.Test6
                print(child_2.get_fqn())
                assert None is not re.match("^Vehicle.Test1.Test(2|3).Test(4|5|6)", child_2.get_fqn())
                check_instance_branch(child_2, 4)
                child_3: VSSNode
                for child_3 in child_2.children:
                    # 3rd level: Test1.Test2.Test4.Test7 -
                    # Test1.Test3.Test6.Test10
                    assert None is not re.match(
                        "^Vehicle.Test1.Test(2|3).Test(4|5|6).Test(7|8|9|10)",
                        child_3.get_fqn(),
                    )
                    check_instance_branch(child_3, 1)
                    assert 1 == len(child_3.children)
                    child_4 = child_3.children[0]
                    # 4th level: Test1.Test2.Test4.Test7.Test11 -
                    # Test1.Test3.Test6.Test10.Test11
                    assert None is not re.match(
                        "^Vehicle.Test1.Test(2|3).Test(4|5|6).Test(7|8|9|10).Test11",
                        child_4.get_fqn(),
                    )
                    # All instances are expected to have one child
                    assert 1 == len(child_4.children)
                    assert child_4.children[0].name == "SomeThing"
                    assert child_4.children[0].data.type == model.NodeType.SENSOR
                    assert child_4.children[0].data.description == "test"


# TEST EXCLUSION FROM INSTANCE STRUCTURE #
# Goal: Check if exclusion of certain nodes during instantiation work
#
# How: Exclude some nodes from instantiation and check if the
# structure is the expected one
#
# TEST EXCLUSION FROM INSTANCE STRUCTURE #

# Needed test files
TEST_FILES_EXCLUDE = ["instance_exclude_node.vspec"]


def test_exclusion_from_instance():
    for tfs in TEST_FILES_EXCLUDE:
        # load the file
        print(tfs)
        tree, _ = get_trees(vspec=RESOURCES / tfs, include_dirs=(RESOURCES,))
        assert 6 == len(tree.children)
        name_list = []
        child: VSSNode
        for child in tree.children:
            name_list.append(child.get_fqn())
            if "Vehicle.ExcludeSomeThing" == child.get_fqn():
                assert model.NodeType.BRANCH == child.data.type
                assert "ExcludeSomeThing description" == child.data.description
                assert 1 == len(child.children)
                child_2 = child.children[0]
                assert "Vehicle.ExcludeSomeThing.ExcludeSomethingLeaf" == child_2.get_fqn()
                assert "ExcludeSomethingLeaf description" == child_2.data.description
                assert model.NodeType.ACTUATOR == child_2.data.type

            elif "Vehicle.ExcludeNode" == child.get_fqn():
                assert "Vehicle.ExcludeNode" == child.get_fqn()
                assert "ExcludeNode description" == child.data.description
                assert model.NodeType.ATTRIBUTE == child.data.type

        assert "Vehicle.ExcludeSomeThing" in name_list
        assert "Vehicle.ExcludeNode" in name_list


def test_extended_attribute():
    tree, _ = get_trees(vspec=RESOURCES / "instance_extended_attribute.vspec", include_dirs=(RESOURCES,))

    # check if root node has 3 children
    assert len(tree.children) == 3

    # Programmatically change value of dbc/signal for instance in Test2

    child: VSSNode
    for child in tree.children:
        if child.get_fqn() == "Vehicle.Test2":
            assert len(child.children) == 1
            assert child.children[0].name == "SomeThing"  # <... SomeThing
            assert len(child.children[0].data.get_extra_attributes()) == 1
            assert isinstance(getattr(child.children[0].data, "dbc"), dict)
            assert getattr(child.children[0].data, "dbc")["signal"] == "bababa"
            child.children[0].data.dbc["signal"] = "lalala"

    child: VSSNode
    for child in tree.children:
        if child.get_fqn() == "Vehicle.Test2":
            assert child.children[0].data.dbc["signal"] == "lalala"
        else:
            # Make sure that all other instances keeps same name
            assert child.children[0].data.dbc["signal"] == "bababa"

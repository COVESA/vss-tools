#!/usr/bin/env python3
# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pytest
import os


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


def check_expected_for_tool(signal_name: str, grep_str: str, tool_path: str):

    test_str = "printf '%s\n' 'm' " + signal_name + "  '1' 'q' | " + tool_path + " test.binary > out.txt"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0
    test_str = "grep '" + grep_str + "' out.txt > /dev/null"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


def check_expected(signal_name: str, grep_str: str):
    check_expected_for_tool(signal_name, grep_str, "./ctestparser")
    check_expected_for_tool(signal_name, grep_str, "../../binary/go_parser/gotestparser")


def test_binary(change_test_dir):
    """
    Tests binary tools by generating binary file and using test parsers to interpret them and request
    some basic information.
    """
    test_str = "gcc -shared -o ../../binary/binarytool.so -fPIC ../../binary/binarytool.c"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = "../../vspec2binary.py -u ../vspec/test_units.yaml test.vspec test.binary"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = "cc ../../binary/c_parser/testparser.c ../../binary/c_parser/cparserlib.c -o ctestparser"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    # Needs to be built from where the go parser is
    result = os.system("cd ../../binary/go_parser; go build -o gotestparser testparser.go > out.txt 2>&1")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0
    os.system("cd -")

    check_expected('A.String', 'Node type=SENSOR')
    check_expected('A.Int', 'Node type=ACTUATOR')

    os.system("rm -f test.binary ctestparser out.txt")
    os.system("rm -f ../../binary/go_parser/gotestparser  ../../binary/go_parser/out.txt")

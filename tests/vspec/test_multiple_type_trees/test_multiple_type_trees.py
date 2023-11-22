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


def test_error(change_test_dir):
    """
    Verify that you cannot have multiple type trees, ie. both TypesA and TypesB, there must be a single root
    """
    test_str = "../../../vspec2csv.py -vt struct1.vspec -vt struct2.vspec -u ../test_units.yaml " \
               "test.vspec out.csv 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    # failure expected
    assert os.WEXITSTATUS(result) != 0
    test_str = 'grep \"unknown root node\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.csv out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

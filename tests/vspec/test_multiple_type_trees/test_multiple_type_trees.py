#!/usr/bin/env python3

#
# (C) 2023 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

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
    test_str = "../../../vspec2x.py --format csv -vt struct1.vspec -vt struct2.vspec -u ../test_units.yaml " \
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

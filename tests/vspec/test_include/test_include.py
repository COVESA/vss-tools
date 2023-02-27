#!/usr/bin/env python3

#
# (C) 2022 Robert Bosch GmbH
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


def test_include(change_test_dir):
    test_str = "../../../vspec2json.py -u ../test_units.yaml --no-uuid  --json-pretty test.vspec out.json" + \
               " 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    # No real need to test more than one exporter
    result = os.system("diff out.json expected.json")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    os.system("rm -f out.json out.txt")


def test_error(change_test_dir):
    test_str = "../../../vspec2json.py -u ../test_units.yaml --no-uuid  --json-pretty test_error.vspec out.json " + \
               "1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    # failure expected
    assert os.WEXITSTATUS(result) != 0

    # Test on faulty include
    test_str = 'grep \"WARNING  No branch matching\" out.txt > /dev/null'
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    # Test on missing include, is fatal error
    test_str = 'grep \"Exception: Invalid VSS model\" out.txt > /dev/null'
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    os.system("rm -f out.json out.txt")

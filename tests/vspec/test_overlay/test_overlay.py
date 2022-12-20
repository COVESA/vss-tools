#!/usr/bin/env python3

#
# (C) 2022 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

import pathlib
import runpy
import pytest
import os

@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)

# Only running json exporter, overlay-fucntionality should be independent of selected exporter
def run_overlay(overlay_file, expected_file):
    test_str = "../../../vspec2json.py --json-pretty -e dbc --no-uuid test.vspec -o " + overlay_file + " out.json > out.txt"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = "diff out.json " + expected_file
    result =  os.system(test_str)
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0
    
    

def test_explicit_overlay(change_test_dir):
    run_overlay("overlay_explicit_branches.vspec", "expected.json")
    
def test_implicit_overlay(change_test_dir):
    run_overlay("overlay_implicit_branches.vspec", "expected.json")

def test_overlay_error(change_test_dir):
    test_str = "../../../vspec2json.py --json-pretty --no-uuid test.vspec -o overlay_error.vspec out.json > out.txt"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    # failure expected
    assert os.WEXITSTATUS(result) != 0

    test_str = 'grep \"Merging impossible\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

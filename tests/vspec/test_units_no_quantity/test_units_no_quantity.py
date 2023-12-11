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
from typing import Optional


# #################### Helper methods #############################

@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


def run_unit(vspec_file, unit_argument, expected_file, quantity_argument="",
             grep_present: bool = True, grep_string: Optional[str] = None):
    test_str = "../../../vspec2json.py --json-pretty " + \
        vspec_file + " " + unit_argument + " " + quantity_argument + " out.json > out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = "diff out.json " + expected_file
    result = os.system(test_str)
    os.system("rm -f out.json")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    # Verify expected quntity

    if grep_string is not None:
        test_str = 'grep \"' + grep_string + '\" out.txt > /dev/null'
        result = os.system(test_str)
        assert os.WIFEXITED(result)
        if grep_present:
            assert os.WEXITSTATUS(result) == 0
        else:
            assert os.WEXITSTATUS(result) == 1

    os.system("rm -f out.txt")


# #################### Tests #############################

def test_default_unit_no_quantity_warning(change_test_dir):
    """
    If no quantity file is found it shall only inform about that
    """
    run_unit("test.vspec", "-u ../test_units.yaml", "expected.json", "", True,
             "No quantities defined")
    run_unit("test.vspec", "-u ../test_units.yaml", "expected.json", "", False,
             "Quantity length used by unit km has not been defined")
    run_unit("test.vspec", "-u ../test_units.yaml", "expected.json", "", False,
             "Quantity temperature used by unit celsius has not been defined")


def test_default_unit_quantities_missing(change_test_dir):
    """
    If quantity file found it shall inform about missing quantities (once for each)
    """
    run_unit("test.vspec", "-u ../test_units.yaml", "expected.json", "-q test_quantities.yaml", False,
             "No quantities defined")
    run_unit("test.vspec", "-u ../test_units.yaml", "expected.json", "-q test_quantities.yaml", True,
             "Quantity length used by unit km has not been defined")
    run_unit("test.vspec", "-u ../test_units.yaml", "expected.json", "-q test_quantities.yaml", True,
             "Quantity temperature used by unit celsius has not been defined")


def test_default_unit_quantities_ok(change_test_dir):
    run_unit("test.vspec", "-u ../test_units.yaml", "expected.json", "-q ../test_quantities.yaml", False,
             "No quantities defined")
    run_unit("test.vspec", "-u ../test_units.yaml", "expected.json", "-q ../test_quantities.yaml", False,
             "Quantity length used by unit km has not been defined")
    run_unit("test.vspec", "-u ../test_units.yaml", "expected.json", "-q ../test_quantities.yaml", False,
             "Quantity temperature used by unit celsius has not been defined")

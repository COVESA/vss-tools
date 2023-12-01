#!/usr/bin/env python3

# Copyright (c) 2022 Contributors to COVESA
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
    test_str = "../../../vspec2json.py --json-pretty --no-uuid " + \
        vspec_file + " " + unit_argument + " " + quantity_argument + " out.json > out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = "diff out.json " + expected_file
    result = os.system(test_str)
    os.system("rm -f out.json")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    # Verify expected quantity

    if grep_string is not None:
        test_str = 'grep \"' + grep_string + '\" out.txt > /dev/null'
        result = os.system(test_str)
        assert os.WIFEXITED(result)
        if grep_present:
            assert os.WEXITSTATUS(result) == 0
        else:
            assert os.WEXITSTATUS(result) == 1

    os.system("rm -f out.txt")


def run_unit_error(vspec_file, unit_argument, grep_error):
    test_str = "../../../vspec2json.py --json-pretty --no-uuid " + \
        vspec_file + " " + unit_argument + " out.json > out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    # failure expected
    assert os.WEXITSTATUS(result) != 0

    test_str = 'grep \"' + grep_error + '\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

# #################### Tests #############################

# Short form


def test_single_u(change_test_dir):
    run_unit("signals_with_special_units.vspec", "-u units_all.yaml", "expected_special.json")


# Short form multiple files
def test_multiple_u(change_test_dir):
    run_unit(
        "signals_with_special_units.vspec",
        "-u units_hogshead.yaml -u units_puncheon.yaml",
        "expected_special.json")


# Short form duplication should not matter
def test_multiple_duplication(change_test_dir):
    run_unit("signals_with_special_units.vspec", "-u units_all.yaml -u units_all.yaml", "expected_special.json")

# Long form


def test_single_unit_files(change_test_dir):
    run_unit("signals_with_special_units.vspec", "--unit-file units_all.yaml", "expected_special.json")

# Long form multiple files


def test_multiple_unit_files(change_test_dir):
    run_unit(
        "signals_with_special_units.vspec",
        "--unit-file units_hogshead.yaml --unit-file units_puncheon.yaml",
        "expected_special.json")

# Special units not defined


def test_unit_error_no_unit_file(change_test_dir):
    run_unit_error("signals_with_special_units.vspec", "", "No units defined")

# Not all units defined


def test_unit_error_unit_file_incomplete(change_test_dir):
    run_unit_error("signals_with_special_units.vspec", "-u units_hogshead.yaml", "Unknown unit")

# File not found


def test_unit_error_missing_file(change_test_dir):
    run_unit_error("signals_with_special_units.vspec", "-u file_that_does_not_exist.yaml", "FileNotFoundError")


def test_unit_on_branch(change_test_dir):
    run_unit_error("unit_on_branch.vspec", "-u units_all.yaml", "cannot have unit")


# Quantity tests
def test_implicit_quantity(change_test_dir):
    run_unit(
        "signals_with_special_units.vspec",
        "--unit-file units_all.yaml",
        "expected_special.json",
        "", False, "has not been defined")


def test_explicit_quantity(change_test_dir):
    run_unit(
        "signals_with_special_units.vspec",
        "--unit-file units_all.yaml",
        "expected_special.json",
        "-q quantities.yaml", False, "has not been defined")


def test_explicit_quantity_2(change_test_dir):
    run_unit(
        "signals_with_special_units.vspec",
        "--unit-file units_all.yaml",
        "expected_special.json",
        "--quantity-file quantities.yaml", False, "has not been defined")


def test_explicit_quantity_warning(change_test_dir):
    """
    We should get two warnings as the quantity file contain "volym", not "volume"
    """
    run_unit(
        "signals_with_special_units.vspec",
        "--unit-file units_all.yaml",
        "expected_special.json",
        "-q quantity_volym.yaml", True, "Quantity volume used by unit puncheon has not been defined")


def test_quantity_redefinition(change_test_dir):
    run_unit(
        "signals_with_special_units.vspec",
        "--unit-file units_all.yaml",
        "expected_special.json",
        "-q quantity_volym.yaml -q quantity_volym.yaml", True, "Redefinition of quantity volym")

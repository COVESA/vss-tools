#!/usr/bin/env python3

#
# (C) 2022 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

import pytest
import os


# #################### Helper methods #############################

@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


def run_unit(vspec_file, unit_argument, expected_file):
    test_str = "../../../vspec2json.py --json-pretty --no-uuid " + \
        vspec_file + " " + unit_argument + " out.json > out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = "diff out.json " + expected_file
    result = os.system(test_str)
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


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

# FIle not found


def test_unit_error_missing_file(change_test_dir):
    run_unit_error("signals_with_special_units.vspec", "-u file_that_does_not_exist.yaml", "FileNotFoundError")

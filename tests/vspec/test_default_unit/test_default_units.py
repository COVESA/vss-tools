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


# #################### Helper methods #############################

@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


def run_unit(vspec_file, unit_argument, expected_file):
    test_str = "vspec2json --json-pretty " + \
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
    test_str = "vspec2json --json-pretty " + \
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

# #################### Tests related to default units (config.yaml) #############################


# Test with no unit specified - shall pass as file "units.yaml" with wanted type exists in same folder
def test_default_ok(change_test_dir):
    run_unit("signals_with_default_units.vspec", "", "expected_default.json")


# Explicitly stating same file shall also be ok
def test_default_explicit(change_test_dir):
    run_unit("signals_with_default_units.vspec", "", "expected_default.json")

# If specifying another unit file an error is expected


def test_default_error(change_test_dir):
    run_unit_error("signals_with_default_units.vspec", "-u ../test_units.yaml", "Unknown unit")

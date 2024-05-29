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


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)

# Only running json exporter, overlay-functionality should be independent
# of selected exporter


def run_overlay(overlay_prefix):
    test_str = "../../../vspec2json.py --json-pretty -u ../test_units.yaml -e dbc test.vspec -o overlay_" + \
        overlay_prefix + ".vspec out.json > out.txt"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = "diff out.json expected_" + overlay_prefix + ".json"
    result = os.system(test_str)
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


def test_explicit_overlay(change_test_dir):
    run_overlay("explicit_branches")


def test_implicit_overlay(change_test_dir):
    run_overlay("implicit_branches")


def test_no_datatype(change_test_dir):
    run_overlay("no_datatype")


def test_no_type(change_test_dir):
    run_overlay("no_type")


def test_overlay_error(change_test_dir):

    test_str = "../../../vspec2json.py --json-pretty -u ../test_units.yaml -o overlay_error.vspec " + \
               "test.vspec out.json 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    # failure expected
    assert os.WEXITSTATUS(result) != 0

    test_str = 'grep \"need to have a datatype\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


def test_overlay_branch_error(change_test_dir):
    test_str = "../../../vspec2json.py -e dbc --json-pretty -u ../test_units.yaml test.vspec " + \
               "-o overlay_implicit_branch_no_description.vspec out.json 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    # failure expected
    assert os.WEXITSTATUS(result) != 0

    test_str = 'grep \"Invalid VSS element AB, must have description\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

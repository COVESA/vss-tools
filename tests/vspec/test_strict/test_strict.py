#!/usr/bin/env python3

# Copyright (c) 2024 Contributors to COVESA
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


@pytest.mark.parametrize("vspec_file", [
    "correct.vspec",
    "correct_boolean.vspec",
    "faulty_case.vspec",
    "faulty_name_boolean.vspec"
    ])
def test_not_strict(vspec_file: str, change_test_dir):
    test_str = "../../../vspec2json.py --json-pretty -u ../test_units.yaml " + vspec_file + \
               " out.json > out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = 'grep \"You asked for strict checking. Terminating\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0


@pytest.mark.parametrize("vspec_file", [
    "correct.vspec",
    "correct_boolean.vspec"
    ])
def test_strict_ok(vspec_file: str, change_test_dir):
    test_str = "../../../vspec2json.py --json-pretty -s -u ../test_units.yaml " + vspec_file + \
               " out.json > out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = 'grep \"You asked for strict checking. Terminating\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0


@pytest.mark.parametrize("vspec_file", [
    "faulty_case.vspec",
    "faulty_name_boolean.vspec"
    ])
def test_strict_error(vspec_file: str, change_test_dir):
    test_str = "../../../vspec2json.py --json-pretty -s -u ../test_units.yaml " + vspec_file + \
               " out.json > out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    test_str = 'grep \"You asked for strict checking. Terminating.\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

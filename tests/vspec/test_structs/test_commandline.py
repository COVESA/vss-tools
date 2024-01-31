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


def test_error_when_data_types_file_is_missing(change_test_dir):
    # test that program fails due to parser error
    cmdline = '../../../vspec2json.py  -u ../test_units.yaml -ot output_types_file.json test.vspec output_file.json'
    test_str = cmdline + " 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    # test that the expected error is outputted
    test_str = 'grep \"error: An output file for data types was provided. Please also provide the input ' + \
               'vspec file for data types\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


@pytest.mark.parametrize("format", ["binary", "franca", "graphql"])
def test_error_with_non_compatible_formats(format, change_test_dir):
    # test that program fails due to parser error
    cmdline = ('../../../vspec2' + format + '.py -u ../test_units.yaml -vt VehicleDataTypes.vspec '
               '-ot output_types_file.json'
               'test.vspec output_file.json')
    test_str = cmdline + " 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    # test that the expected error is outputted
    test_str = 'grep \"error: unrecognized arguments: -vt\" ' + \
        'out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt output_types_file.json output_file.json")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

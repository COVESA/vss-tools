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


def test_error_when_data_types_file_is_missing(change_test_dir):
    # test that program fails due to parser error
    cmdline = '../../../vspec2x.py  -u ../test_units.yaml -ot output_types_file.json test.vspec output_file.json'
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


@pytest.mark.parametrize("format", ["binary", "franca", "idl", "graphql"])
def test_error_with_non_compatible_formats(format, change_test_dir):
    # test that program fails due to parser error
    cmdline = ('../../../vspec2x.py -u ../test_units.yaml -vt VehicleDataTypes.vspec -ot output_types_file.json'
               f' --format {format} test.vspec output_file.json')
    test_str = cmdline + " 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    # test that the expected error is outputted
    test_str = f'grep \"error: {format} format is not yet supported in vspec struct/data type support feature\" ' + \
               'out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt output_types_file.json output_file.json")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

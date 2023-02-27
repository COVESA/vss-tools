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


def test_error_when_output_file_is_missing(change_test_dir):
    # test that program fails due to parser error
    cmdline = '../../../vspec2x.py  -u ../test_units.yaml -vt data_types_file.spec vspec_file.spec output_file.json'
    test_str = cmdline + " 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    # test that the expected error is outputted
    test_str = 'grep \"error: Please provide the vspec data types file and the output file\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


def test_error_when_data_types_file_is_missing(change_test_dir):
    # test that program fails due to parser error
    cmdline = '../../../vspec2x.py  -u ../test_units.yaml -ot output_types_file.json vspec_file.spec output_file.json'
    test_str = cmdline + " 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    # test that the expected error is outputted
    test_str = 'grep \"error: Please provide the vspec data types file and the output file\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


def test_error_incompatibility_with_overlays(change_test_dir):
    # test that program fails due to parser error
    cmdline = '../../../vspec2x.py  -u ../test_units.yaml -vt data_types_file.spec -ot output_types_file.json ' + \
              '-o overlays_file.json vspec_file.spec output_file.json'
    test_str = cmdline + " 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    # test that the expected error is outputted
    test_str = 'grep \"error: Overlays are not yet supported in vspec struct/data type support feature\" out.txt ' + \
               '> /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


@pytest.mark.parametrize("format", ["csv", "yaml", "binary", "franca", "idl", "graphql"])
def test_error_incompatibility_with_non_json_formats(format, change_test_dir):
    # test that program fails due to parser error
    cmdline = '../../../vspec2x.py  -u ../test_units.yaml -vt data_types_file.spec -ot output_types_file ' + \
              f'--format {format} vspec_file.spec output_file.json'
    test_str = cmdline + " 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) != 0

    # test that the expected error is outputted
    test_str = f'grep \"error: {format} format is not yet supported in vspec struct/data type support feature\" ' + \
               'out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

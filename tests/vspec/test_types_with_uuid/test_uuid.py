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


def run_exporter(exporter, argument, compare_suffix):
    test_str = "../../../vspec2" + exporter + ".py " + argument + \
        " -u ../test_units.yaml test.vspec out." + exporter + " 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0
    test_str = "diff out." + exporter + " expected_" + compare_suffix + "." + exporter
    result = os.system(test_str)
    os.system("rm -f out." + exporter + " out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


def test_uuid(change_test_dir):

    # Run all "supported" exporters, i.e. not those in contrib
    # Exception is "binary", as it is assumed output may vary depending on
    # target
    exporters = ["json", "ddsidl", "csv", "yaml", "franca", "graphql"]
    for exporter in exporters:
        run_exporter(exporter, "--uuid", "uuid")
        # Same behavior expected if no argument
        run_exporter(exporter, "", "no_uuid")


def run_obsolete_arg_test(argument, obsolete_arg_expected: bool):
    test_str = "../../../vspec2json.py " + argument + " -u ../test_units.yaml test.vspec out.json 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    if obsolete_arg_expected:
        assert os.WEXITSTATUS(result) != 0
    else:
        assert os.WEXITSTATUS(result) == 0
    test_str = 'grep \"error: unrecognized arguments\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    if obsolete_arg_expected:
        assert os.WEXITSTATUS(result) == 0
    else:
        assert os.WEXITSTATUS(result) != 0


def test_obsolete_arg(change_test_dir):
    run_obsolete_arg_test("", False)
    run_obsolete_arg_test("--uuid", False)
    run_obsolete_arg_test("--no-uuid", True)

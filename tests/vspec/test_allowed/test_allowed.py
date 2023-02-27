#!/usr/bin/env python3

#
# (C) 2023 Robert Bosch GmbH
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


def run_exporter(exporter, argument):
    test_str = "../../../vspec2" + exporter + ".py " + argument + " test.vspec out." + exporter + " > out.txt"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0
    test_str = "diff out." + exporter + " expected." + exporter
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    # Check if warning given
    # ddsidl can not handle float and integer
    # Some other tools ignore "allowed" all together
    if exporter in ["ddsidl"]:
        expected_grep_result = 0
    else:
        expected_grep_result = 1

    test_str = 'grep \"can only handle allowed values for string type\" out.txt > /dev/null'
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == expected_grep_result
    os.system("rm -f out." + exporter + " out.txt")


def test_uuid(change_test_dir):

    # Run all "supported" exporters, i.e. not those in contrib
    # Exception is "binary", as it is assumed output may vary depending on target
    exporters = ["json", "ddsidl", "csv", "yaml", "franca", "graphql"]
    for exporter in exporters:
        run_exporter(exporter, "--no-uuid -u ../test_units.yaml")

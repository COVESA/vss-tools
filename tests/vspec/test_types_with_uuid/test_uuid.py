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

    # Run all "supported" exporters that supports uuid, i.e. not those in contrib
    # Exception is "binary", as it is assumed output may vary depending on
    # target
    exporters = ["json", "ddsidl", "csv", "yaml", "franca"]
    for exporter in exporters:
        run_exporter(exporter, "--uuid", "uuid")
        run_exporter(exporter, "", "no_uuid")


def run_error_test(tool, argument, arg_error_expected: bool):
    test_str = "../../../" + tool + " " + argument + " -u ../test_units.yaml test.vspec out.json 1> out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    if arg_error_expected:
        assert os.WEXITSTATUS(result) != 0
    else:
        assert os.WEXITSTATUS(result) == 0
    test_str = 'grep \"error: unrecognized arguments\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    if arg_error_expected:
        assert os.WEXITSTATUS(result) == 0
    else:
        assert os.WEXITSTATUS(result) != 0


def test_obsolete_arg(change_test_dir):
    """
    Check that obsolete argument --no-uuid results in error
    """
    run_error_test("vspec2json.py", "", False)
    run_error_test("vspec2json.py", "--uuid", False)
    run_error_test("vspec2json.py", "--no-uuid", True)


def test_uuid_unsupported(change_test_dir):
    """
    Test that we get an error if using --uuid for tools not supporting it
    """
    run_error_test("vspec2graphql.py", "--uuid", True)

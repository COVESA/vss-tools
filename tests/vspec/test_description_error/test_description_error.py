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


def run_description_error(vspec_file: str):
    test_str = "../../../vspec2json.py --json-pretty --no-uuid " + vspec_file + " out.json > out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    # failure expected
    assert os.WEXITSTATUS(result) != 0

    test_str = 'grep \"Exception: Invalid VSS element\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


def test_no_description_branch(change_test_dir):
    run_description_error("no_description_branch.vspec")


def test_no_description_signal(change_test_dir):
    run_description_error("no_description_signal.vspec")

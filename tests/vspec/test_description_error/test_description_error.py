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


@pytest.mark.parametrize("vspec_file, type_str", [
    ("no_description_branch.vspec", ""),
    ("no_description_signal.vspec", ""),
    ("correct.vspec", "-vt no_description_type_branch.vspec -ot ot.json"),
    ("correct.vspec", "-vt no_description_type_struct.vspec -ot ot.json"),
    ("correct.vspec", "-vt no_description_type_property.vspec -ot ot.json")
    ])
def test_description_error(vspec_file: str, type_str: str, change_test_dir):
    test_str = "../../../vspec2json.py --json-pretty -u ../test_units.yaml " + type_str + " " + vspec_file + \
               " out.json > out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    # failure expected
    assert os.WEXITSTATUS(result) != 0

    test_str = 'grep \"Invalid VSS element\" out.txt > /dev/null'
    result = os.system(test_str)
    os.system("cat out.txt")
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

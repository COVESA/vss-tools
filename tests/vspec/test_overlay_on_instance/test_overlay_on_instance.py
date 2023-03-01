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

# Only running json exporter, overlay-functionality should be independent of selected exporter


def test_expanded_overlay(change_test_dir):
    test_str = "../../../vspec2json.py  -e my_id --json-pretty --no-uuid -u ../test_units.yaml test.vspec " + \
               "-o overlay_1.vspec -o overlay_2.vspec out.json > out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = "diff out.json expected.json"
    result = os.system(test_str)
    os.system("rm -f out.json out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

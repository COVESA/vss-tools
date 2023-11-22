# Copyright (c) 2023 Contributors to COVESA
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


def test_generator(change_test_dir):

    test_str = "./example_generator.py -k \"VSS Contributor\" -u ../vspec/test_units.yaml test.vspec > out.txt 2>&1"
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = 'grep \"I found 2 comments with vss contributor\" out.txt > /dev/null'
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0
    os.system("rm -f  out.txt")

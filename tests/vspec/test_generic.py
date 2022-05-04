#!/usr/bin/env python3

#
# (C) 2022 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

import pathlib
import runpy
import pytest
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

def default_directories() -> list:
    directories = []
    for path in pathlib.Path(dir_path).iterdir():
      if path.is_dir():
        if list(path.rglob("*.vspec")):
# Exclude directories with custom made python file
          if not list(path.rglob("*.py")):
            directories.append(path)
    return directories

# Use directory name as test name
def idfn(directory: pathlib.PosixPath):
    return directory.name

@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)

@pytest.mark.parametrize('directory', default_directories(), ids=idfn)
def test_script_execution(directory, change_test_dir):
    os.chdir(directory.name)
    test_str = "../../../vspec2json.py --no-uuid test.vspec out.json > out.txt"
    result = os.system(test_str)
    os.chdir("..")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0
    os.chdir(directory.name)
    test_str = "diff out.json expected.json"
    result =  os.system(test_str)
    os.system("rm -f out.json out.txt")
    os.chdir("..")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

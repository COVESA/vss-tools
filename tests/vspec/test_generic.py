#!/usr/bin/env python3

#
# (C) 2022 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

import pathlib
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


def run_exporter(directory, exporter):
    os.chdir(directory.name)
    test_str = "../../../vspec2" + exporter + ".py -u ../test_units.yaml test.vspec out." + exporter + \
               " > out.txt"
    result = os.system(test_str)
    os.chdir("..")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0
    os.chdir(directory.name)
    test_str = "diff out." + exporter + " expected." + exporter
    result = os.system(test_str)
    os.system("rm -f out." + exporter + " out.txt")
    os.chdir("..")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0


@pytest.mark.parametrize('directory', default_directories(), ids=idfn)
def test_exporters(directory, change_test_dir):
    # Run all "supported" exporters, i.e. not those in contrib
    # Exception is "binary", as it is assumed output may vary depending on target
    exporters = ["json", "ddsidl", "csv", "yaml", "franca", "graphql"]
    for exporter in exporters:
        run_exporter(directory, exporter)

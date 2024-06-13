#!/usr/bin/env python3

# Copyright (c) 2024 Contributors to COVESA
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


@pytest.fixture(scope="function", autouse=True)
def delete_files(change_test_dir):
    yield None
    os.system("rm -rf out.json out.txt vehicle_signal_specification")

# Test all VSS versions we support
#
# Intended workflow:
#
# ---------- After a new VSS release -----------------
#
# * Add the new tag to this test case
# * Update compatibility section in README
#
# ----------- If this test case fails -----------------
#
# * Check if we can add backward compatibility with limited effort
# * If not add limitation to compatibility section in README and remove '
#   unsupported versions from the test case
#


@pytest.mark.parametrize("tag",
                         [
                          'v4',
                          'v4.0',
                          'v4.1',
                          'v4.2'])
def test_compatibility(tag, change_test_dir):
    """
    Test that we still can analyze wanted versions without error
    """

    os.system("git clone --depth 1 --branch " + tag +
              " https://github.com/COVESA/vehicle_signal_specification")

    result = os.system("../../vspec2json.py --json-pretty "
                       "vehicle_signal_specification/spec/VehicleSignalSpecification.vspec "
                       "out.json 1>out.txt 2>&1")
    os.system("cat out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

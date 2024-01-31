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


# First test case on all supported exportes

@pytest.mark.parametrize("format,signals_out, expected_signal", [
    ('json', 'out.json', 'expected.json'),
    ('yaml', 'out.yaml', 'expected.yaml'),
    ('csv', 'out.csv', 'expected.csv'),
    ('protobuf', 'out.proto', 'expected.proto')])
def test_overlay_struct(format, signals_out, expected_signal, change_test_dir):
    """
    Test that data types provided in vspec format are converted correctly
    """
    args = ["../../../vspec2" + format + ".py"]
    if format == 'json':
        args.append('--json-pretty')
    args.extend(["-vt", "struct1.vspec", "-vt", "struct2.vspec", "-u", "../test_units.yaml",
                 "test.vspec", "-o", "overlay.vspec", signals_out, "1>", "out.txt", "2>&1"])
    test_str = " ".join(args)

    result = os.system(test_str)
    os.system("cat out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = f"diff {signals_out} {expected_signal}"
    result = os.system(test_str)
    os.system("rm -f out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    os.system(f"rm -f {signals_out}")

    if format == 'protobuf':
        test_str = "diff Types/Types.proto expected_types.proto"
        result = os.system(test_str)
        os.system("rm -f out.txt")
        assert os.WIFEXITED(result)
        assert os.WEXITSTATUS(result) == 0
        os.system("rm -rf Types")


@pytest.mark.parametrize("format,signals_out, expected_signal", [
    ('json', 'out.json', 'expected_struct_using_struct.json')])
def test_overlay_struct_using_struct(format, signals_out, expected_signal, change_test_dir):
    """
    Test that data types provided in vspec format are converted correctly
    """
    args = ["../../../vspec2" + format + ".py"]
    if format == 'json':
        args.append('--json-pretty')
    args.extend(["-vt", "struct1.vspec", "-vt", "struct2_using_struct1.vspec", "-u", "../test_units.yaml",
                 "test.vspec", "-o", "overlay.vspec", signals_out, "1>", "out.txt", "2>&1"])
    test_str = " ".join(args)

    result = os.system(test_str)
    os.system("cat out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = f"diff {signals_out} {expected_signal}"
    result = os.system(test_str)
    os.system("rm -f out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    os.system(f"rm -f {signals_out}")

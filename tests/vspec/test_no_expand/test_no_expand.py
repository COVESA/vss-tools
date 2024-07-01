#!/usr/bin/env python3

# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pytest
import os


# #################### Helper methods #############################

@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


@pytest.mark.parametrize("format, output_file, comparison_file, is_error_expected", [
    ('json', 'out.json', 'expected.json', False),
    ('yaml', 'out.yaml', 'expected.yaml', False),
    ('csv', 'out.csv', 'expected.csv', False),
    ('protobuf', 'out.proto', 'expected.proto', True),
    ('ddsidl', 'out.idl', 'expected.idl', True),
    ('franca', 'out.fidl', 'expected.fidl', True),
    ('graphql', 'out.graphql', 'expected.graphql', True)])
def test_no_expand(format, output_file, comparison_file, is_error_expected: bool, change_test_dir):

    args = ["vspec2" + format, "--no-expand"]
    if format == 'json':
        args.append('--json-pretty')
    args.extend(["-u", "../test_units.yaml",
                 "test.vspec", output_file, "1>", "out.txt", "2>&1"])
    test_str = " ".join(args)

    result = os.system(test_str)
    os.system("cat out.txt")
    assert os.WIFEXITED(result)
    if is_error_expected:
        assert os.WEXITSTATUS(result) != 0
    else:
        assert os.WEXITSTATUS(result) == 0

    # For exporters not supporting "no-expand" an error shall be given
    test_str = 'grep \"error: unrecognized arguments: --no-expand\" out.txt > /dev/null'
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    if is_error_expected:
        assert os.WEXITSTATUS(result) == 0
    else:
        assert os.WEXITSTATUS(result) == 1
        test_str = f"diff {output_file} {comparison_file}"
        result = os.system(test_str)
        os.system("rm -f out.txt")
        assert os.WIFEXITED(result)
        assert os.WEXITSTATUS(result) == 0

    os.system(f"rm -f {output_file}")

# Overlay tests, just showing for JSON


@pytest.mark.parametrize("no_expand, comparison_file", [
    (False, 'expected_overlay_expand.json'),
    (True, 'expected_overlay_no_expand.json')])
def test_json_overlay(no_expand, comparison_file, change_test_dir):
    """Test with overlay and expansion (for reference/comparison)"""
    args = ["vspec2json"]

    if no_expand:
        args.append('--no-expand')

    args.extend(["--json-pretty", "-u", "../test_units.yaml",
                 "test.vspec", "-o", "overlay.vspec", "out.json", "1>", "out.txt", "2>&1"])
    test_str = " ".join(args)

    result = os.system(test_str)
    os.system("cat out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    test_str = f"diff out.json {comparison_file}"
    result = os.system(test_str)
    os.system("rm -f out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    os.system("rm -f out.json")

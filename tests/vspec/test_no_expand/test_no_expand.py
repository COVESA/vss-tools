#!/usr/bin/env python3

#
# (C) 2023 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

import pytest
import os


# #################### Helper methods #############################

@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


@pytest.mark.parametrize("format, output_file, comparison_file, is_warning_expected", [
    ('json', 'out.json', 'expected.json', False),
    ('yaml', 'out.yaml', 'expected.yaml', False),
    ('csv', 'out.csv', 'expected.csv', False),
    ('protobuf', 'out.proto', 'expected.proto', True),
    ('idl', 'out.idl', 'expected.idl', True),
    ('franca', 'out.fidl', 'expected.fidl', True),
    ('graphql', 'out.graphql', 'expected.graphql', True)])
def test_no_expand(format, output_file, comparison_file, is_warning_expected: bool, change_test_dir):

    args = ["../../../vspec2x.py", "--no-expand", "--format", format]
    if format == 'json':
        args.append('--json-pretty')
    args.extend(["-u", "../test_units.yaml",
                 "test.vspec", output_file, "1>", "out.txt", "2>&1"])
    test_str = " ".join(args)

    result = os.system(test_str)
    os.system("cat out.txt")
    assert os.WIFEXITED(result)
    assert os.WEXITSTATUS(result) == 0

    # For exporters not supporting "no-expand" a warning shall be given
    test_str = 'grep \"no_expand not supported by exporter\" out.txt > /dev/null'
    result = os.system(test_str)
    assert os.WIFEXITED(result)
    if is_warning_expected:
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
    args = ["../../../vspec2x.py"]

    if no_expand:
        args.append('--no-expand')

    args.extend(["--format", "json", "--json-pretty", "-u", "../test_units.yaml",
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

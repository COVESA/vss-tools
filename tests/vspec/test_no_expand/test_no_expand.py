# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pytest

from pathlib import Path
import subprocess
import filecmp

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


@pytest.mark.parametrize(
    "format, output_file, comparison_file, is_error_expected",
    [
        ("json", "out.json", "expected.json", False),
        ("yaml", "out.yaml", "expected.yaml", False),
        ("csv", "out.csv", "expected.csv", False),
        ("protobuf", "out.proto", "expected.proto", True),
        ("ddsidl", "out.idl", "expected.idl", True),
        ("franca", "out.fidl", "expected.fidl", True),
        ("graphql", "out.graphql", "expected.graphql", True),
    ],
)
def test_no_expand(
    format, output_file, comparison_file, is_error_expected: bool, tmp_path
):
    spec = HERE / "test.vspec"
    output = tmp_path / output_file
    cmd = f"vspec2x {format} --no-expand"
    if format == "json":
        cmd += " --pretty"
    cmd += f" -u {TEST_UNITS} --vspec {spec} --output {output}"

    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    if is_error_expected:
        assert process.returncode != 0
    else:
        assert process.returncode == 0

    # For exporters not supporting "no-expand" an error shall be given
    expected = HERE / comparison_file
    if is_error_expected:
        assert "No such option: --no-expand" in process.stderr
    else:
        assert filecmp.cmp(output, expected)


# Overlay tests, just showing for JSON
@pytest.mark.parametrize(
    "no_expand, comparison_file",
    [
        (False, "expected_overlay_expand.json"),
        (True, "expected_overlay_no_expand.json"),
    ],
)
def test_json_overlay(no_expand, comparison_file, tmp_path):
    """Test with overlay and expansion (for reference/comparison)"""

    overlay = HERE / "overlay.vspec"
    spec = HERE / "test.vspec"
    output = tmp_path / "out.json"

    cmd = "vspec2x json"
    if no_expand:
        cmd += " --no-expand"
    cmd += f" --pretty -u {TEST_UNITS} --vspec {spec} -l {overlay} --output {output}"

    subprocess.run(cmd.split(), check=True, capture_output=True, text=True)
    expected = HERE / comparison_file
    assert filecmp.cmp(output, expected)

# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import filecmp
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


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

    cmd = "vspec export json"
    if no_expand:
        cmd += " --no-expand"
    cmd += f" --pretty -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} -l {overlay} --output {output}"

    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode == 0
    expected = HERE / comparison_file
    assert filecmp.cmp(output, expected)

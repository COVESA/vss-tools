#!/usr/bin/env python3

# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
import subprocess
import filecmp

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


# Only running json exporter, overlay-functionality should be independent of selected exporter
def test_expanded_overlay(tmp_path):
    spec = HERE / "test.vspec"
    overlay1 = HERE / "overlay_1.vspec"
    overlay2 = HERE / "overlay_2.vspec"
    output = tmp_path / "out.json"
    cmd = f"vspec2json -e my_id --json-pretty -u {TEST_UNITS} {spec} -o {overlay1} -o {overlay2} {output}"
    process = subprocess.run(cmd.split())
    assert process.returncode == 0

    expected = HERE / "expected.json"
    assert filecmp.cmp(output, expected)


def test_expanded_overlay_no_type_datatype(tmp_path):
    """
    This test shows current limitation on type/datatype lookup.
    We cannot do lookup on expanded names containing instances.
    That would require quite some more advanced lookup considering instance declarations.
    Not impossible, but more complex.
    """
    spec = HERE / "test.vspec"
    overlay = HERE / "overlay_no_type_datatype.vspec"
    output = tmp_path / "out.json"
    cmd = f"vspec2json -e my_id --json-pretty -u {TEST_UNITS} {spec} -o {overlay} {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert "No type specified for A.B.Row1.Left.C" in process.stdout

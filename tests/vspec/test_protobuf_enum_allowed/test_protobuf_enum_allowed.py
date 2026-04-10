# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""
Test that the protobuf exporter generates nested enum types for
`datatype: string` signals that have an `allowed` attribute, instead
of emitting a plain `string` field.

Related issue: https://github.com/COVESA/vss-tools/issues/493
"""

import filecmp
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


def test_protobuf_enum_for_allowed_string(tmp_path):
    """
    A `string` field with `allowed` values must produce a nested enum and
    use the enum type as the field type, not plain `string`.

    A `string[]` field with `allowed` must produce `repeated <EnumType>`.

    A numeric field without `allowed` must remain unchanged (regression check).
    """
    vspec = HERE / "test.vspec"
    output = tmp_path / "out.proto"
    cmd = f"vspec export protobuf -u {TEST_UNITS} -q {TEST_QUANT} --vspec {vspec} --output {output}"
    subprocess.run(cmd.split(), check=True)
    expected = HERE / "expected.proto"
    assert filecmp.cmp(output, expected), (
        f"Output differs from expected.\nGot:\n{output.read_text()}\nExpected:\n{expected.read_text()}"
    )

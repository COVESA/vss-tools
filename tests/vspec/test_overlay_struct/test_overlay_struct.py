# Copyright (c) 2022 Contributors to COVESA
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


# First test case on all supported exportes
@pytest.mark.parametrize(
    "format,signals_out, expected_signal",
    [
        ("json", "out.json", "expected.json"),
        ("yaml", "out.yaml", "expected.yaml"),
        ("csv", "out.csv", "expected.csv"),
        ("protobuf", "out.proto", "expected.proto"),
    ],
)
def test_overlay_struct(format, signals_out, expected_signal, tmp_path):
    """
    Test that data types provided in vspec format are converted correctly
    """
    spec = HERE / "test.vspec"
    struct1 = HERE / "struct1.vspec"
    struct2 = HERE / "struct2.vspec"
    overlay = HERE / "overlay.vspec"
    output = tmp_path / signals_out

    cmd = f"vspec2{format}"
    if format == "json":
        cmd += " --json-pretty"
    cmd += f" -vt {struct1} -vt {struct2} -u {TEST_UNITS} -o {overlay} {spec} {output}"

    subprocess.run(cmd.split(), cwd=tmp_path, check=True)
    expected = HERE / expected_signal
    assert filecmp.cmp(output, expected)

    if format == "protobuf":
        types_proto = tmp_path / "Types" / "Types.proto"
        expected = HERE / "expected_types.proto"
        assert filecmp.cmp(types_proto, expected)


@pytest.mark.parametrize(
    "format,signals_out, expected_signal",
    [("json", "out.json", "expected_struct_using_struct.json")],
)
def test_overlay_struct_using_struct(format, signals_out, expected_signal, tmp_path):
    """
    Test that data types provided in vspec format are converted correctly
    """

    struct1 = HERE / "struct1.vspec"
    struct2 = HERE / "struct2_using_struct1.vspec"
    overlay = HERE / "overlay.vspec"
    spec = HERE / "test.vspec"
    output = tmp_path / signals_out
    cmd = f"vspec2{format} --json-pretty -vt {struct1} -vt {struct2} -u {TEST_UNITS} {spec} -o {overlay} {output}"
    subprocess.run(cmd.split(), check=True)
    expected = HERE / expected_signal
    assert filecmp.cmp(output, expected)

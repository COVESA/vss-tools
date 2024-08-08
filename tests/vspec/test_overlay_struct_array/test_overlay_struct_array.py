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
def test_overlay_struct_array(format, signals_out, expected_signal, tmp_path):
    """
    Test that data types provided in vspec format are converted correctly
    """
    struct = HERE / "struct1.vspec"
    spec = HERE / "test.vspec"
    overlay = HERE / "overlay.vspec"
    output = tmp_path / signals_out
    cmd = f"vspec export {format}"
    if format == "json":
        cmd += " --pretty"
    cmd += f" --types {struct} -u {TEST_UNITS} --vspec {spec} -l {overlay} --output {output}"
    subprocess.run(cmd.split(), cwd=tmp_path, check=True)

    expected = HERE / expected_signal
    assert filecmp.cmp(output, expected)

    if format == "protobuf":
        types_proto = tmp_path / "Types" / "Types.proto"
        expected = HERE / "expected_types.proto"
        assert filecmp.cmp(types_proto, expected)

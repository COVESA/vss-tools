# Copyright (c) 2026 Contributors to COVESA
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


@pytest.mark.parametrize(
    "include_comments, expected_file",
    [
        (False, "expected_no_comments.proto"),
        (True, "expected_with_comments.proto"),
    ],
)
def test_protobuf_comments(include_comments, expected_file, tmp_path):
    """
    Test that --include-comments adds description and metadata
    as comments to the protobuf output, and that without the flag
    no comments are present.
    """
    vspec = HERE / "test.vspec"
    output = tmp_path / "out.proto"
    cmd = f"vspec export protobuf -u {TEST_UNITS} -q {TEST_QUANT} --vspec {vspec} --output {output}"
    if include_comments:
        cmd += " --include-comments"
    subprocess.run(cmd.split(), check=True)
    expected = HERE / expected_file
    assert filecmp.cmp(output, expected), (
        f"Output differs from expected.\n" f"Got:\n{output.read_text()}\n" f"Expected:\n{expected.read_text()}"
    )

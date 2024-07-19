# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "vspec" / "test_units.yaml"


def test_ddsldl(tmp_path):
    """
    Tests that generated ddsidl is accepted by idlc
    """

    cmd = f"vspec export ddsidl -u {TEST_UNITS} -s {HERE / 'test.vspec'} -o test.idl"
    subprocess.run(cmd.split(), check=True)
    cmd = "idlc -l py test.idl"
    subprocess.run(cmd.split(), check=True)

    # Basic sanity check that output is as expected
    cmd = "grep -i A.String A/_test.py"
    subprocess.run(cmd.split(), check=True)

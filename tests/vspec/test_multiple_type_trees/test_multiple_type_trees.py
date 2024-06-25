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

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


def test_error(tmp_path):
    """
    Verify that you cannot have multiple type trees,
    ie. both TypesA and TypesB, there must be a single root
    """
    output = tmp_path / "out.csv"
    vt1 = HERE / "struct1.vspec"
    vt2 = HERE / "struct2.vspec"
    spec = HERE / "test.vspec"
    cmd = f"vspec2csv -vt {vt1} -vt {vt2} -u {TEST_UNITS} {spec} {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert "unknown root node" in process.stderr

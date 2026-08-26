# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import filecmp
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def test_include(tmp_path):
    spec = HERE / "A.vspec"
    output = tmp_path / "out.yaml"
    expected = HERE / "expected.yaml"
    cmd = f"vspec export yaml --vspec {spec} --output {output}"
    subprocess.run(cmd.split(), check=True)
    assert filecmp.cmp(output, expected)


def test_error(tmp_path):
    spec = HERE / "test_error.vspec"
    output = tmp_path / "out.yaml"
    cmd = f"vspec export yaml --vspec {spec} --output {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0

    assert "MultipleRootsException" in process.stderr

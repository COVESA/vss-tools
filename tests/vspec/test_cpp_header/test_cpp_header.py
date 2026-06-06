# Copyright (c) 2024 Contributors to COVESA
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
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


def test_cpp_header(tmp_path: Path):
    spec = HERE / "test.vspec"
    output = tmp_path / "out.hpp"
    log = tmp_path / "log.txt"
    cmd = f"vspec --log-file {log} export cpp-header -s {spec} -u {TEST_UNITS} -q {TEST_QUANT} -o {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    assert filecmp.cmp(output, HERE / "expected.hpp")

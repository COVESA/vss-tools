# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import os


from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


def test_error_when_data_types_file_is_missing(tmp_path):
    otypes = HERE / "output_types_file.json"
    spec = HERE / "test.vspec"
    output = tmp_path / "output.json"
    cmd = f"vspec export json -u {TEST_UNITS} --types-output {otypes} --vspec {spec} --output {output}"
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, env=env)
    assert process.returncode != 0
    assert (
        "raise ArgumentException"
        in process.stderr
    )

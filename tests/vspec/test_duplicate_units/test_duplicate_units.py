# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def test_duplicate_unit_descriptions(tmp_path):
    """Test that duplicate unit descriptions are detected and reported."""
    spec = HERE / "test.vspec"
    out = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    units = HERE / "test_units_duplicate.yaml"
    quantities = HERE / "test_quantities.yaml"

    cmd = f"vspec --log-file {log} export json --pretty --vspec {spec}"
    cmd += f" -u {units} -q {quantities} --output {out}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=HERE)

    assert process.returncode != 0
    log_content = log.read_text()
    # Check for the expected error message format
    expected_error = "Duplicated unit: 'grams per second'"
    assert expected_error in log_content or expected_error in process.stderr


def test_valid_unique_unit_descriptions(tmp_path):
    """Test that unique unit descriptions pass validation."""
    spec = HERE / "test.vspec"
    out = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    units = HERE / "test_units_valid.yaml"
    quantities = HERE / "test_quantities.yaml"

    cmd = f"vspec --log-file {log} export json --pretty --vspec {spec}"
    cmd += f" -u {units} -q {quantities} --output {out}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=HERE)

    assert process.returncode == 0
    assert out.exists()

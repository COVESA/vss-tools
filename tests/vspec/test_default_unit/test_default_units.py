# Copyright (c) 2023 Contributors to COVESA
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


def run_unit(vspec_file, unit_argument, expected_file, tmp_path):
    output = tmp_path / "out.json"
    cmd = f"vspec export json --pretty --vspec {vspec_file} {unit_argument} --output {output}"
    subprocess.run(cmd.split(), check=True)
    assert filecmp.cmp(expected_file, output)


def run_unit_error(vspec_file, unit_argument, check_message, tmp_path):
    output = tmp_path / "out.json"
    cmd = f"vspec export json --pretty --vspec {vspec_file} {unit_argument} --output {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert check_message in process.stdout


def test_default_ok(tmp_path):
    run_unit(
        HERE / "signals_with_default_units.vspec",
        f"-q {TEST_QUANT}",
        HERE / "expected_default.json",
        tmp_path,
    )


# Explicitly stating same file shall also be ok
def test_default_explicit(tmp_path):
    units = HERE / "units.yaml"
    run_unit(
        HERE / "signals_with_default_units.vspec",
        f"-u {units} -q {TEST_QUANT}",
        HERE / "expected_default.json",
        tmp_path,
    )


# If specifying another unit file an error is expected
def test_default_error(tmp_path):
    run_unit_error(
        HERE / "signals_with_default_units.vspec",
        f"-u {TEST_UNITS} -q {TEST_QUANT}",
        "not a valid unit",
        tmp_path,
    )

# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


@pytest.mark.parametrize(
    "vspec_file",
    [
        "correct.vspec",
        "correct_boolean.vspec",
        "faulty_case.vspec",
        "faulty_name_boolean.vspec",
    ],
)
def test_not_strict(vspec_file: str, tmp_path):
    spec = HERE / vspec_file
    output = tmp_path / "out.json"
    cmd = f"vspec export json --pretty -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} --output {output}"
    process = subprocess.run(cmd.split())
    assert process.returncode == 0


@pytest.mark.parametrize("vspec_file", ["correct.vspec", "correct_boolean.vspec"])
def test_strict_ok(vspec_file: str, tmp_path):
    spec = HERE / vspec_file
    output = tmp_path / "out.json"
    cmd = f"vspec export json --pretty --strict -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} --output {output}"
    process = subprocess.run(cmd.split())
    assert process.returncode == 0


@pytest.mark.parametrize("vspec_file", ["faulty_case.vspec", "faulty_name_boolean.vspec"])
def test_strict_error(vspec_file: str, tmp_path):
    spec = HERE / vspec_file
    output = tmp_path / "out.json"
    cmd = f"vspec export json --pretty --strict -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} --output {output}"
    process = subprocess.run(cmd.split())
    assert process.returncode != 0


@pytest.mark.parametrize("vspec_file", ["faulty_case.vspec", "faulty_name_boolean.vspec"])
def test_strict_exceptions(vspec_file: str, tmp_path):
    spec = HERE / vspec_file
    output = tmp_path / "out.json"
    cmd = f"vspec export json --pretty --strict --strict-exceptions {HERE / 'exceptions.yaml'}"
    cmd += f" -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} --output {output}"
    process = subprocess.run(cmd.split())
    assert process.returncode == 0

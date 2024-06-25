#!/usr/bin/env python3

# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pytest
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


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
    cmd = f"vspec2json --json-pretty -u {TEST_UNITS} {spec} {output}"
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, env=env)
    assert process.returncode == 0
    print(process.stdout)
    assert "You asked for strict checking. Terminating" not in process.stdout


@pytest.mark.parametrize("vspec_file", ["correct.vspec", "correct_boolean.vspec"])
def test_strict_ok(vspec_file: str, tmp_path):
    spec = HERE / vspec_file
    output = tmp_path / "out.json"
    cmd = f"vspec2json --json-pretty -s -u {TEST_UNITS} {spec} {output}"
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, env=env)
    assert process.returncode == 0
    assert "You asked for strict checking. Terminating" not in process.stdout


@pytest.mark.parametrize(
    "vspec_file", ["faulty_case.vspec", "faulty_name_boolean.vspec"]
)
def test_strict_error(vspec_file: str, tmp_path):
    spec = HERE / vspec_file
    output = tmp_path / "out.json"
    cmd = f"vspec2json --json-pretty -s -u {TEST_UNITS} {spec} {output}"
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, env=env)
    assert process.returncode != 0
    assert "You asked for strict checking. Terminating" in process.stdout

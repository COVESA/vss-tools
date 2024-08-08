# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
import os
from typing import Optional
from pathlib import Path
import subprocess
import filecmp

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


def run_unit(
    tmp_path,
    vspec_file,
    unit_argument,
    expected_file,
    quantity_argument="",
    grep_present: bool = True,
    grep_string: Optional[str] = None,
):
    out = tmp_path / "out.json"
    cmd = f"vspec export json --pretty --vspec {vspec_file} {unit_argument} {quantity_argument} --output {out}"
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, cwd=HERE, env=env, check=True)
    assert filecmp.cmp(out, HERE / expected_file)

    if grep_string and grep_present:
        assert grep_string in process.stdout or grep_string in process.stderr


def test_default_unit_no_quantity_warning(tmp_path):
    """
    If no quantity file is found it shall only inform about that
    """
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        "expected.json",
        "",
        True,
        "No quantities defined",
    )
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        "expected.json",
        "",
        False,
        "Quantity length used by unit km has not been defined",
    )
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        "expected.json",
        "",
        False,
        "Quantity temperature used by unit celsius has not been defined",
    )


def test_default_unit_quantities_missing(tmp_path):
    """
    If quantity file found it shall inform about missing quantities (once for each)
    """
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        "expected.json",
        "-q test_quantities.yaml",
        False,
        "No quantities defined",
    )
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        "expected.json",
        "-q test_quantities.yaml",
        True,
        "Quantity length used by unit km has not been defined",
    )
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        "expected.json",
        "-q test_quantities.yaml",
        True,
        "Quantity temperature used by unit celsius has not been defined",
    )


def test_default_unit_quantities_ok(tmp_path):
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        "expected.json",
        "-q ../test_quantities.yaml",
        False,
        "No quantities defined",
    )
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        "expected.json",
        "-q ../test_quantities.yaml",
        False,
        "Quantity length used by unit km has not been defined",
    )
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        "expected.json",
        "-q ../test_quantities.yaml",
        False,
        "Quantity temperature used by unit celsius has not been defined",
    )

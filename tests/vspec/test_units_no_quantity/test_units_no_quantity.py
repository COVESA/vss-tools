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
from typing import Optional

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
    fails: bool = False,
):
    out = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    cmd = f"vspec --log-file {log} export json --pretty --vspec {vspec_file}"
    cmd += f" {unit_argument} {quantity_argument} --output {out}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=HERE)
    print(process.stdout)
    if fails:
        assert process.returncode != 0
    else:
        assert process.returncode == 0
        assert filecmp.cmp(out, HERE / expected_file)

    if grep_string and grep_present:
        assert grep_string in log.read_text() or grep_string in process.stderr


def test_default_unit_no_quantity_warning(tmp_path):
    """
    If no quantity file is found it shall only inform about that
    """
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        None,
        "",
        True,
        "No 'quantity' files defined.",
        True,
    )
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        None,
        "",
        False,
        "Invalid quantity: 'length'",
        True,
    )


def test_default_unit_quantities_missing(tmp_path):
    """
    If quantity file found it shall inform about missing quantities (once for each)
    """
    run_unit(
        tmp_path,
        "test.vspec",
        "-u ../test_units.yaml",
        None,
        "-q test_quantities.yaml",
        False,
        "Invalid quantity: 'length'",
        True,
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

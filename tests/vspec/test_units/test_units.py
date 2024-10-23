# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
import filecmp
import os
import subprocess
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


def run_unit(
    tmp_path,
    vspec_file,
    units,
    expected_file,
    quantities=None,
    grep_present: bool = True,
    grep_string: Optional[str] = None,
    fails: bool = False,
):
    if not quantities:
        quantities = []
    if not units:
        units = []
    spec = HERE / vspec_file
    out = tmp_path / "out.json"
    unit_argument = " ".join([f"-u {HERE / unit}" for unit in units])
    quantity_argument = " ".join([f"-q {HERE / quantity}" for quantity in quantities])
    cmd = f"vspec export json --pretty --vspec {spec}"
    cmd += f" {unit_argument} {quantity_argument} --output {out}"
    env = os.environ.copy()
    # Long line needed as file name printed in some error messages
    env["COLUMNS"] = "200"
    process = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=HERE, env=env)

    if fails:
        assert process.returncode != 0
    else:
        assert process.returncode == 0
        assert filecmp.cmp(HERE / expected_file, out)

    if grep_present and grep_string:
        assert grep_string in process.stdout or grep_string in process.stderr


def run_unit_error(tmp_path, vspec_file, units, grep_error, quantities=None):
    if not quantities:
        quantities = []
    if not units:
        units = []
    out = tmp_path / "out.json"
    unit_argument = " ".join([f"-u {HERE / unit}" for unit in units])
    quantity_argument = " ".join([f"-q {HERE / quantity}" for quantity in quantities])
    cmd = f"vspec export json --pretty --vspec {vspec_file}"
    cmd += f" {unit_argument} {quantity_argument} --output {out}"
    env = os.environ.copy()
    # Long line needed as file name printed in some error messages
    env["COLUMNS"] = "300"
    process = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=HERE, env=env)
    assert process.returncode != 0
    if grep_error:
        assert grep_error in process.stdout or grep_error in process.stderr


def test_single_u(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_all.yaml"],
        "expected_special.json",
    )


# Short form multiple files
def test_multiple_u(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_hogshead.yaml", "units_puncheon.yaml"],
        "expected_special.json",
    )


# Short form duplication should not matter
def test_multiple_duplication(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_all.yaml", "units_all.yaml"],
        "expected_special.json",
        None,
        True,
        "redefinition of 'puncheon'",
        True,
    )


# Long form


def test_single_unit_files(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_all.yaml"],
        "expected_special.json",
    )


# Long form multiple files


def test_multiple_unit_files(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_hogshead.yaml", "units_puncheon.yaml"],
        "expected_special.json",
    )


# Special units not defined


def test_unit_error_no_unit_file(tmp_path):
    run_unit_error(tmp_path, "signals_with_special_units.vspec", None, "No 'unit' files defined")


# Not all units defined


def test_unit_error_unit_file_incomplete(tmp_path):
    run_unit_error(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_hogshead.yaml"],
        "'puncheon' is not a valid unit",
    )


# File not found


def test_unit_error_missing_file(tmp_path):
    run_unit_error(
        tmp_path,
        "signals_with_special_units.vspec",
        ["file_that_does_not_exist.yaml"],
        "does not exist",
    )


# Quantity tests


def test_implicit_quantity(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_all.yaml"],
        "expected_special.json",
        "",
        False,
        "has not been defined",
    )


def test_explicit_quantity(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_all.yaml"],
        "expected_special.json",
        ["quantities.yaml"],
        False,
        "has not been defined",
    )


def test_explicit_quantity_2(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_all.yaml"],
        "expected_special.json",
        ["quantities.yaml"],
        False,
        "has not been defined",
    )


def test_explicit_quantity_warning(tmp_path):
    """
    We should get two warnings as the quantity file contain "volym", not "volume"
    """
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_all.yaml"],
        "expected_special.json",
        ["quantity_volym.yaml"],
        True,
        "Invalid quantity: 'volume'",
        True,
    )


def test_quantity_redefinition(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_all.yaml"],
        "expected_special.json",
        ["quantity_volym.yaml", "quantity_volym.yaml"],
        True,
        "redefinition of 'volym'",
        True,
    )


def test_quantity_err_no_def(tmp_path):
    """
    Test scenario when definition is not given
    """
    run_unit_error(
        tmp_path,
        "signals_with_special_units.vspec",
        ["units_all.yaml"],
        "'volume' is 'None'",
        ["quantities_no_def.yaml"],
    )

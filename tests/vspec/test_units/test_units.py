#!/usr/bin/env python3

# Copyright (c) 2022 Contributors to COVESA
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
    cmd = f"vspec2json --json-pretty {vspec_file} {unit_argument} {quantity_argument} {out}"
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, cwd=HERE, env=env
    )
    assert process.returncode == 0
    assert filecmp.cmp(HERE / expected_file, out)

    if grep_present and grep_string:
        assert grep_string in process.stdout


def run_unit_error(
    tmp_path, vspec_file, unit_argument, grep_error, quantity_argument=""
):
    out = tmp_path / "out.json"
    cmd = f"vspec2json --json-pretty {vspec_file} {unit_argument} {quantity_argument} {out}"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, cwd=HERE)
    assert process.returncode != 0
    if grep_error:
        assert grep_error in process.stdout or grep_error in process.stderr


def test_single_u(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        "-u units_all.yaml",
        "expected_special.json",
    )


# Short form multiple files
def test_multiple_u(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        "-u units_hogshead.yaml -u units_puncheon.yaml",
        "expected_special.json",
    )


# Short form duplication should not matter
def test_multiple_duplication(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        "-u units_all.yaml -u units_all.yaml",
        "expected_special.json",
    )


# Long form


def test_single_unit_files(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        "--unit-file units_all.yaml",
        "expected_special.json",
    )


# Long form multiple files


def test_multiple_unit_files(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        "--unit-file units_hogshead.yaml --unit-file units_puncheon.yaml",
        "expected_special.json",
    )


# Special units not defined


def test_unit_error_no_unit_file(tmp_path):
    run_unit_error(tmp_path, "signals_with_special_units.vspec",
                   "", "No units defined")


# Not all units defined


def test_unit_error_unit_file_incomplete(tmp_path):
    run_unit_error(
        tmp_path,
        "signals_with_special_units.vspec",
        "-u units_hogshead.yaml",
        "Unknown unit",
    )


# File not found


def test_unit_error_missing_file(tmp_path):
    run_unit_error(
        tmp_path,
        "signals_with_special_units.vspec",
        "-u file_that_does_not_exist.yaml",
        "FileNotFoundError",
    )


def test_unit_on_branch(tmp_path):
    run_unit_error(
        tmp_path, "unit_on_branch.vspec", "-u units_all.yaml", "cannot have unit"
    )


# Quantity tests


def test_implicit_quantity(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        "--unit-file units_all.yaml",
        "expected_special.json",
        "",
        False,
        "has not been defined",
    )


def test_explicit_quantity(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        "--unit-file units_all.yaml",
        "expected_special.json",
        "-q quantities.yaml",
        False,
        "has not been defined",
    )


def test_explicit_quantity_2(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        "--unit-file units_all.yaml",
        "expected_special.json",
        "--quantity-file quantities.yaml",
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
        "--unit-file units_all.yaml",
        "expected_special.json",
        "-q quantity_volym.yaml",
        True,
        "Quantity volume used by unit puncheon has not been defined",
    )


def test_quantity_redefinition(tmp_path):
    run_unit(
        tmp_path,
        "signals_with_special_units.vspec",
        "--unit-file units_all.yaml",
        "expected_special.json",
        "-q quantity_volym.yaml -q quantity_volym.yaml",
        True,
        "Redefinition of quantity volym",
    )


def test_quantity_err_no_def(tmp_path):
    """
    Test scenario when definition is not given
    """
    run_unit_error(
        tmp_path,
        "signals_with_special_units.vspec",
        "-u units_all.yaml",
        "No definition found for quantity volume",
        "-q quantities_no_def.yaml",
    )

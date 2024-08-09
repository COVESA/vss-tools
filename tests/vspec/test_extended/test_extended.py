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
TEST_QUANT = HERE / ".." / "test_quantities.yaml"
TEST_FILE = HERE / "test.vspec"
KNOWN_PREFIX = "User defined extra attributes: "
WARNING_PREFIX = "Unknown extra attribute:"


@pytest.mark.parametrize(
    "extended_args, known_extended, extended_warning",
    [
        ("", None, "e1, e2, e3"),
        ("-e e1", "('e1',)", "e2, e3"),
        # Duplicated items presented as is
        ("-e e1 -e e1", "('e1', 'e1')", "e2, e3"),
        ("-e e1 -e e2", "('e1', 'e2')", "e3"),
        ("-e e1 -e e2 -e e3", "('e1', 'e2', 'e3')", None),
        ("-e e1 -e e2 -e e3 -e e2", "('e1', 'e2', 'e3', 'e2')", None),
        (
            "-e e1 -e e2 -e e3 -e e4",
            "('e1', 'e2', 'e3', 'e4')",
            None,
        ),  # also ones that are not used (e4) are presented
        # Some cases like above but using full name
        ("--extended-attributes e1 --extended-attributes e2", "('e1', 'e2')", "e3"),
        ("--extended-attributes e1 -e e2", "('e1', 'e2')", "e3"),
        ("-e e1 --extended-attributes e2", "('e1', 'e2')", "e3"),
    ],
)
def test_extended_ok(
    extended_args: str,
    known_extended: str | None,
    extended_warning: str | None,
    tmp_path,
):
    output = tmp_path / "out.json"
    cmd = f"vspec export json --pretty -u {TEST_UNITS}"
    cmd += f" -q {TEST_QUANT} {extended_args} -s {TEST_FILE} -o {output}"

    # Make sure there is no line break that affects compare
    os.environ["COLUMNS"] = "120"

    process = subprocess.run(cmd.split(), capture_output=True, check=True, text=True)

    if known_extended is not None:
        print(process.stdout)
        check_str = KNOWN_PREFIX + known_extended + " "
        assert check_str in process.stdout
    else:
        assert KNOWN_PREFIX not in process.stdout

    if extended_warning:
        for i in extended_warning.split(","):
            assert (WARNING_PREFIX + f" 'A.SignalA':'{i.strip()}'") in process.stdout


@pytest.mark.parametrize(
    "extended_args",
    [
        ("-e e1,e2"),
        ("-e e1,e2,e3"),
        ("-e e1,e2 -e e3"),
        # Some cases like above but using full name
        ("--extended-attributes e1,e2"),
    ],
)
def test_extended_error(extended_args: str, tmp_path):
    output = tmp_path / "out.json"
    cmd = f"vspec export json --pretty -u {TEST_UNITS}"
    cmd += f" -q {TEST_QUANT} {extended_args} -s {TEST_FILE} -o {output}"

    # Make sure there is no line break that affects compare
    os.environ["COLUMNS"] = "120"

    process = subprocess.run(
        cmd.split(), stdout=subprocess.PIPE, text=True, stderr=subprocess.STDOUT
    )
    assert process.returncode != 0
    assert "not allowed" in process.stdout

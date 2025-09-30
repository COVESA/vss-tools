# Copyright (c) 2022 Contributors to COVESA
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


def run_error_test(tool, exporter, argument, arg_error_expected: bool, tmp_path):
    vspec = HERE / "test.vspec"
    out = tmp_path / "out.json"
    cmd = f"{tool} {exporter} {argument} -u {TEST_UNITS} -q {TEST_QUANT} --vspec {vspec} --output {out}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    if arg_error_expected:
        assert process.returncode != 0
        assert "No such option:" in process.stderr
    else:
        assert process.returncode == 0


@pytest.mark.parametrize(
    "exporter",
    ["binary", "csv", "ddsidl", "franca", "graphql", "id", "json", "jsonschema", "protobuf", "tree", "yaml"],
)
def test_obsolete_arg(exporter, tmp_path):
    """
    Check that you get errors for all
    """
    run_error_test("vspec export ", exporter, "", False, tmp_path)
    run_error_test("vspec export ", exporter, "--uuid", True, tmp_path)
    run_error_test("vspec export ", exporter, "--no-uuid", True, tmp_path)

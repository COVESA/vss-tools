# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
import subprocess
import filecmp

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


def run_exporter(exporter, argument, tmp_path):
    spec = HERE / "test.vspec"
    output = tmp_path / f"out.{exporter}"
    cmd = f"vspec2x {exporter}{argument} --vspec {spec} --output {output}"

    process = subprocess.run(cmd.split(), check=True, capture_output=True, text=True)
    expected = HERE / f"expected.{exporter}"
    assert filecmp.cmp(output, expected)

    # Check if warning given
    # ddsidl can not handle float and integer
    # Some other tools ignore "allowed" all together
    if exporter in ["ddsidl"]:
        assert "can only handle allowed values for string type" in process.stdout


def test_allowed(tmp_path):
    # Run all "supported" exporters, i.e. not those in contrib
    # Exception is "binary", as it is assumed output may vary depending on target
    exporters = ["json", "ddsidl", "csv", "yaml", "franca", "graphql"]
    for exporter in exporters:
        run_exporter(exporter, f" -u {TEST_UNITS}", tmp_path)

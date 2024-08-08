# Copyright (c) 2022 Contributors to COVESA
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


def run_exporter(exporter, argument, compare_suffix, tmp_path):
    vspec = HERE / "test.vspec"
    out = tmp_path / f"out.{exporter}"
    cmd = f"vspec export {exporter}{argument} -u {TEST_UNITS} --vspec {vspec} --output {out}"
    subprocess.run(cmd.split(), check=True)
    expected = HERE / f"expected_{compare_suffix}.{exporter}"
    assert filecmp.cmp(out, expected)


def test_uuid(tmp_path):
    # Run all "supported" exporters that supports uuid, i.e. not those in contrib
    # Exception is "binary", as it is assumed output may vary depending on
    # target
    exporters = ["json", "ddsidl", "csv", "yaml", "franca"]
    for exporter in exporters:
        run_exporter(exporter, " --uuid", "uuid", tmp_path)
        run_exporter(exporter, "", "no_uuid", tmp_path)


def run_error_test(tool, argument, arg_error_expected: bool, tmp_path):
    vspec = HERE / "test.vspec"
    out = tmp_path / "out.json"
    cmd = f"{tool} {argument} -u {TEST_UNITS} --vspec {vspec} --output {out}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    if arg_error_expected:
        assert process.returncode != 0
        assert "No such option:" in process.stderr
    else:
        assert process.returncode == 0


def test_obsolete_arg(tmp_path):
    """
    Check that obsolete argument --no-uuid results in error
    """
    run_error_test("vspec export json", "", False, tmp_path)
    run_error_test("vspec export json", "--uuid", False, tmp_path)
    run_error_test("vspec export json", "--no-uuid", False, tmp_path)


def test_uuid_unsupported(tmp_path):
    """
    Test that we get an error if using --uuid for tools not supporting it
    """
    run_error_test("vspec export graphql", "--uuid", True, tmp_path)

# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import filecmp
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


def test_cpp_header(tmp_path: Path):
    spec = HERE / "test.vspec"
    output = tmp_path / "out.hpp"
    log = tmp_path / "log.txt"
    cmd = f"vspec --log-file {log} export cpp-header -s {spec} -u {TEST_UNITS} -q {TEST_QUANT} -o {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    assert filecmp.cmp(output, HERE / "expected.hpp")


def test_cpp_header_signal_filter_exact(tmp_path: Path):
    spec = HERE / "test.vspec"
    output = tmp_path / "out.hpp"
    log = tmp_path / "log.txt"
    cmd = (
        f"vspec --log-file {log} export cpp-header -s {spec} -u {TEST_UNITS} -q {TEST_QUANT} "
        f"--signal A.Speed -o {output}"
    )
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    content = output.read_text()
    assert "constexpr Signal A_Speed = {" in content
    assert "A_GearMode" not in content
    assert "A_Count" not in content


def test_cpp_header_signal_filter_glob(tmp_path: Path):
    spec = HERE / "test.vspec"
    output = tmp_path / "out.hpp"
    log = tmp_path / "log.txt"
    cmd = (
        f"vspec --log-file {log} export cpp-header -s {spec} -u {TEST_UNITS} -q {TEST_QUANT} "
        f"--signal 'A.Gear*' -o {output}"
    )
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    content = output.read_text()
    assert "constexpr Signal A_GearMode = {" in content
    assert "A_Speed" not in content
    assert "A_Count" not in content


def test_cpp_header_signal_filter_no_match_warns(tmp_path: Path):
    spec = HERE / "test.vspec"
    output = tmp_path / "out.hpp"
    log = tmp_path / "log.txt"
    cmd = (
        f"vspec --log-file {log} export cpp-header -s {spec} -u {TEST_UNITS} -q {TEST_QUANT} "
        f"--signal A.DoesNotExist -o {output}"
    )
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    assert "No signals matched" in log.read_text()
    content = output.read_text()
    assert "constexpr Signal kSignals[] = {\n};" in content


def test_cpp_header_signal_filter_include_branches(tmp_path: Path):
    spec = HERE / "test_nested_signal.vspec"
    output = tmp_path / "out.hpp"
    log = tmp_path / "log.txt"
    cmd = (
        f"vspec --log-file {log} export cpp-header -s {spec} -u {TEST_UNITS} -q {TEST_QUANT} "
        f"--signal Vehicle.Body.Lights.IsOn --include-branches -o {output}"
    )
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    content = output.read_text()
    # The matched signal and its ancestor branches are included...
    assert "constexpr Signal Vehicle_Body_Lights_IsOn = {" in content
    assert "constexpr Signal Vehicle_Body_Lights = {" in content
    assert "constexpr Signal Vehicle_Body = {" in content
    # ...but the sibling branch and its signal are not.
    assert "Vehicle_Cabin" not in content

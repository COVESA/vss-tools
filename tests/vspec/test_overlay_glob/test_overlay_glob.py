# Copyright (c) 2024 Contributors to COVESA
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


def _run(overlay: Path, tmp_path: Path, log_path: Path) -> subprocess.CompletedProcess:
    spec = HERE / "test.vspec"
    output = tmp_path / "out.json"
    cmd = (
        f"vspec --log-file {log_path} export json --pretty"
        f" -s {spec} -u {TEST_UNITS} -q {TEST_QUANT}"
        f" -l {overlay} --output {output}"
    )
    return subprocess.run(cmd.split(), capture_output=True, text=True)


def test_glob_overlay_expands_to_all_matching_signals(tmp_path: Path):
    log = tmp_path / "log.txt"
    result = _run(HERE / "overlay_glob.vspec", tmp_path, log)
    assert result.returncode == 0, result.stderr
    assert filecmp.cmp(tmp_path / "out.json", HERE / "expected.json")


def test_glob_overlay_no_match_warns(tmp_path: Path):
    log = tmp_path / "log.txt"
    result = _run(HERE / "overlay_no_match.vspec", tmp_path, log)
    assert result.returncode == 0, result.stderr
    assert "matched no keys" in log.read_text()

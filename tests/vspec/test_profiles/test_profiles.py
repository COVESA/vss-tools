# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""
Tests for the '--profile' CLI option, which selects which HIM
(Hierarchical Information Model,
https://github.com/COVESA/hierarchical_information_model) profile is
used to validate node 'type' values and parent/child nesting rules.
"""

import filecmp
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


def run(tmp_path, profile: str | None, vspec_file: str, expect_ok: bool):
    spec = HERE / vspec_file
    out = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    cmd = "vspec"
    if profile:
        cmd += f" --profile {profile}"
    cmd += f" --log-file {log} export json --pretty --vspec {spec}"
    cmd += f" -u {TEST_UNITS} -q {TEST_QUANT} --output {out}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    if expect_ok:
        assert process.returncode == 0, process.stderr
    else:
        assert process.returncode != 0
    return process, log, out


def test_default_profile_is_vehicle_data(tmp_path):
    """No '--profile' given should behave exactly like '--profile vehicle-data'."""
    _, _, out = run(tmp_path, None, "vehicle_data.vspec", expect_ok=True)
    assert filecmp.cmp(HERE / "expected_vehicle_data.json", out)


def test_vehicle_data_profile_explicit(tmp_path):
    _, _, out = run(tmp_path, "vehicle-data", "vehicle_data.vspec", expect_ok=True)
    assert filecmp.cmp(HERE / "expected_vehicle_data.json", out)


def test_data_profile_ok(tmp_path):
    _, _, out = run(tmp_path, "data", "data_profile.vspec", expect_ok=True)
    assert filecmp.cmp(HERE / "expected_data_profile.json", out)


def test_service_profile_ok(tmp_path):
    _, _, out = run(tmp_path, "service", "service_profile.vspec", expect_ok=True)
    assert filecmp.cmp(HERE / "expected_service_profile.json", out)


def test_sensor_actuator_rejected_under_data_profile(tmp_path):
    """'sensor'/'actuator' are 'vehicle-data' profile types, not valid under 'data'."""
    _, log, _ = run(tmp_path, "data", "vehicle_data.vspec", expect_ok=False)
    log_content = log.read_text()
    assert "not a valid 'type' for the 'data' profile" in log_content


def test_ro_rw_rejected_under_vehicle_data_profile(tmp_path):
    """'ro'/'rw' are 'data' profile types, not valid under the default 'vehicle-data' profile."""
    _, log, _ = run(tmp_path, "vehicle-data", "data_profile.vspec", expect_ok=False)
    log_content = log.read_text()
    assert "not a valid 'type' for the 'vehicle-data' profile" in log_content


def test_procedure_rejected_under_vehicle_data_profile(tmp_path):
    """'procedure'/'iostruct'/'symlink' are 'service' profile types."""
    _, log, _ = run(tmp_path, "vehicle-data", "service_profile.vspec", expect_ok=False)
    log_content = log.read_text()
    assert "not a valid 'type' for the 'vehicle-data' profile" in log_content


def test_wrong_type_for_active_profile(tmp_path):
    _, log, _ = run(tmp_path, "data", "wrong_type_for_data_profile.vspec", expect_ok=False)
    log_content = log.read_text()
    assert "not a valid 'type' for the 'data' profile" in log_content


def test_service_iostruct_must_be_named_input_or_output(tmp_path):
    _, log, _ = run(tmp_path, "service", "service_bad_iostruct_name.vspec", expect_ok=False)
    log_content = log.read_text()
    assert "'iostruct' node must be named 'Input' or 'Output'" in log_content


def test_service_symlink_needs_iostruct_parent(tmp_path):
    _, log, _ = run(tmp_path, "service", "service_symlink_bad_parent.vspec", expect_ok=False)
    log_content = log.read_text()
    assert "Invalid nodes=1" in log_content
    assert "VehicleService.GetPosition.BadLink" in log_content
    assert "invalid parent: 'VSSDataProcedure'" in log_content


@pytest.mark.parametrize("profile", ["vehicle-data", "data", "service", "invalid-profile"])
def test_profile_choice_validation(tmp_path, profile):
    """Only the three defined profile names are accepted by the CLI."""
    # A lone 'branch' root is valid under any profile, so this only
    # exercises whether '--profile' accepts/rejects the given choice.
    spec = HERE / "root_branch_only.vspec"
    out = tmp_path / "out.json"
    cmd = f"vspec --profile {profile} export json --pretty --vspec {spec}"
    cmd += f" -u {TEST_UNITS} -q {TEST_QUANT} --output {out}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    if profile == "invalid-profile":
        assert process.returncode != 0
        assert "Invalid value for '--profile'" in process.stderr
    else:
        assert process.returncode == 0, process.stdout + process.stderr

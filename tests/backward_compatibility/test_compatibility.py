# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pytest
import subprocess

# Test all VSS versions we support
#
# Intended workflow:
#
# ---------- After a new VSS release -----------------
#
# * Add the new tag to this test case
# * Update compatibility section in README
#
# ----------- If this test case fails -----------------
#
# * Check if we can add backward compatibility with limited effort
# * If not add limitation to compatibility section in README and remove '
#   unsupported versions from the test case
#


@pytest.mark.parametrize("tag",
                         [
                          'v4',
                          'v4.0',
                          'v4.1',
                          'v4.2'])
def test_compatibility(tag, tmp_path):
    """
    Test that we still can analyze wanted versions without error
    """
    url = "https://github.com/COVESA/vehicle_signal_specification"
    vss_dir = tmp_path / "vss"
    clone_cmd = f"git clone --depth 1 --branch {tag} {url} {vss_dir}"

    subprocess.run(clone_cmd.split(), check=True)

    vspec = vss_dir / "spec" / "VehicleSignalSpecification.vspec"
    output = tmp_path / "out.json"

    cmd = f"vspec export json --pretty --vspec {vspec} --output {output}"
    subprocess.run(cmd.split(), check=True)

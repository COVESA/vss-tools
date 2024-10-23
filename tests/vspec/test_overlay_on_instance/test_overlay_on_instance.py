# Copyright (c) 2023 Contributors to COVESA
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


# Only running json exporter, overlay-functionality should be independent of selected exporter
def test_expanded_overlay(tmp_path):
    spec = HERE / "test.vspec"
    overlay1 = HERE / "overlay_1.vspec"
    overlay2 = HERE / "overlay_2.vspec"
    output = tmp_path / "out.json"
    cmd = f"vspec export json -e my_id --pretty -u {TEST_UNITS} -q {TEST_QUANT}"
    cmd += f" --vspec {spec} -l {overlay1} -l {overlay2} --output {output}"
    subprocess.run(cmd.split(), check=True)
    expected = HERE / "expected.json"
    assert filecmp.cmp(output, expected)

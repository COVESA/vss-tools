# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
import pytest
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


@pytest.mark.parametrize(
    "spec_id, quantity_id, unit_id, expected_out",
    [
        (1, 1, 1, "Invalid datatype: 'numerics'"),
        (1, 1, 2, "Invalid quantity: 'workie'"),
        (1, 1, 3, "Field required"),
        (2, 1, 4, "'arraysize' set on a non array datatype"),
        (3, 1, 4, "'foo' is not of type 'uint8[]'"),
        (4, 1, 4, "'min/max' and 'allowed' cannot be used together"),
        (5, 1, 4, "default value '4' is not in 'allowed' list"),
        (6, 1, 4, "'string' is not allowed for unit 'kWh'"),
        (7, 1, 4, "Forbidden extra attribute (core attribute): 'Vehicle':'datatype'"),
        (8, 1, 4, "'default' array size does not match 'arraysize'"),
    ],
)
def test_consistency(
    spec_id: int, quantity_id: int, unit_id: int, expected_out: str, tmp_path: Path
):
    spec = DATA / f"s_{spec_id}.yaml"
    quantity = DATA / f"q_{quantity_id}.yaml"
    unit = DATA / f"u_{unit_id}.yaml"
    log = tmp_path / "log.txt"
    cmd = f"vspec --log-file {log} export tree -s {spec} -u {unit} -q {quantity}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert expected_out in log.read_text()

# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import subprocess
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


def test_id_exporter_includes_struct_nodes(tmp_path: Path):
    output = tmp_path / "out.yaml"
    cmd = (
        f"vspec export id -s {HERE / 'test.vspec'}"
        f" -u {TEST_UNITS} -q {TEST_QUANT}"
        f" --types {HERE / 'types.vspec'}"
        f" -o {output}"
    )
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr

    ids = yaml.safe_load(output.read_text())
    assert ids is not None

    # Struct and property nodes must appear in the output
    assert "Types.Reading" in ids, "struct node missing from id output"
    assert "Types.Reading.Value" in ids, "property node missing from id output"
    assert "Types.Reading.Quality" in ids, "property node missing from id output"

    # Each entry must have a staticUID
    for key in ("Types.Reading", "Types.Reading.Value", "Types.Reading.Quality"):
        assert "staticUID" in ids[key], f"{key} is missing staticUID"
        assert ids[key]["staticUID"].startswith("0x"), f"{key} staticUID not hex"

    # Regular signal nodes still present
    assert "A.Signal" in ids

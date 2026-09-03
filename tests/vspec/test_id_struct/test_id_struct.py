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


def test_id_exporter_writes_struct_nodes_to_types_output(tmp_path: Path):
    output = tmp_path / "out.yaml"
    types_output = tmp_path / "out_types.yaml"
    cmd = (
        f"vspec export id -s {HERE / 'test.vspec'}"
        f" -u {TEST_UNITS} -q {TEST_QUANT}"
        f" --types {HERE / 'types.vspec'}"
        f" -o {output} --types-output {types_output}"
    )
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr

    ids = yaml.safe_load(output.read_text())
    assert ids is not None
    types_ids = yaml.safe_load(types_output.read_text())
    assert types_ids is not None

    # Struct and property nodes must appear in the types output, not the main one
    assert "Types.Reading" in types_ids, "struct node missing from types output"
    assert "Types.Reading.Value" in types_ids, "property node missing from types output"
    assert "Types.Reading.Quality" in types_ids, "property node missing from types output"
    assert "Types.Reading" not in ids
    assert "Types.Reading.Value" not in ids
    assert "Types.Reading.Quality" not in ids

    # Each entry must have a staticUID
    for key in ("Types.Reading", "Types.Reading.Value", "Types.Reading.Quality"):
        assert "staticUID" in types_ids[key], f"{key} is missing staticUID"
        assert types_ids[key]["staticUID"].startswith("0x"), f"{key} staticUID not hex"

    # Regular signal nodes still present in the main output
    assert "A.Signal" in ids


def test_id_exporter_defaults_types_output_name_when_not_given(tmp_path: Path):
    output = tmp_path / "out.yaml"
    default_types_output = tmp_path / "structs_out.yaml"
    cmd = (
        f"vspec export id -s {HERE / 'test.vspec'}"
        f" -u {TEST_UNITS} -q {TEST_QUANT}"
        f" --types {HERE / 'types.vspec'}"
        f" -o {output}"
    )
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    assert default_types_output.exists(), "default types-output file was not created"

    ids = yaml.safe_load(output.read_text())
    assert ids is not None
    types_ids = yaml.safe_load(default_types_output.read_text())
    assert types_ids is not None

    assert "Types.Reading" in types_ids
    assert "Types.Reading" not in ids
    assert "A.Signal" in ids

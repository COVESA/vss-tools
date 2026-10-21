# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import json
import os
import subprocess
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"

# Wide console so that rich does not wrap log messages
ENV = {**os.environ, "COLUMNS": "1000"}

SPEC = HERE / "test.vspec"
SPEC_NESTED = HERE / "test_nested.vspec"
TYPES_BASE = HERE / "types_base.vspec"
OVERLAY_ADD = HERE / "overlay_add.vspec"
OVERLAY_MODIFY = HERE / "overlay_modify.vspec"
OVERLAY_NESTED_STRUCT = HERE / "overlay_nested_struct.vspec"
OVERLAY_NESTED_HEADER = HERE / "overlay_nested_header.vspec"
OVERLAY_OTHER_ROOT = HERE / "overlay_other_root.vspec"


def run_json_export(tmp_path: Path, spec: Path, types: list[Path], overlays: list[Path]):
    output = tmp_path / "out.json"
    types_output = tmp_path / "types.json"
    cmd = f"vspec export json -u {TEST_UNITS} -q {TEST_QUANT} -s {spec} --types-output {types_output} -o {output}"
    for t in types:
        cmd += f" -t {t}"
    for o in overlays:
        cmd += f" --types-overlays {o}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True, env=ENV)
    return process, types_output


def test_overlay_adds_to_existing_header(tmp_path):
    process, types_output = run_json_export(tmp_path, SPEC, [TYPES_BASE], [OVERLAY_ADD])
    assert process.returncode == 0, process.stdout
    assert "Types overlay modifies" not in process.stdout
    children = json.loads(types_output.read_text())["Types"]["children"]
    assert set(children) == {"Struct1", "Struct3"}
    assert set(children["Struct1"]["children"]) == {"x", "y"}
    assert set(children["Struct3"]["children"]) == {"a"}


def test_overlay_modifies_and_logs(tmp_path):
    process, types_output = run_json_export(tmp_path, SPEC, [TYPES_BASE], [OVERLAY_ADD, OVERLAY_MODIFY])
    assert process.returncode == 0, process.stdout
    assert "Types overlay modifies" in process.stdout
    assert "Types.Struct1.x" in process.stdout
    assert "'double' -> 'float'" in process.stdout
    struct1 = json.loads(types_output.read_text())["Types"]["children"]["Struct1"]
    assert struct1["description"] == "Modified struct description."
    assert struct1["children"]["x"]["datatype"] == "float"


def test_header_in_another_overlay(tmp_path):
    process, types_output = run_json_export(
        tmp_path, SPEC_NESTED, [TYPES_BASE], [OVERLAY_NESTED_STRUCT, OVERLAY_NESTED_HEADER]
    )
    assert process.returncode == 0, process.stderr
    sub = json.loads(types_output.read_text())["Types"]["children"]["Sub"]
    assert "Struct4" in sub["children"]


def test_header_missing_everywhere(tmp_path):
    process, _ = run_json_export(tmp_path, SPEC_NESTED, [TYPES_BASE], [OVERLAY_NESTED_STRUCT])
    assert process.returncode != 0
    assert "Types overlay has orphans" in process.stdout
    assert "Types.Sub.Struct4" in process.stdout


def test_overlay_without_types(tmp_path):
    process, _ = run_json_export(tmp_path, SPEC, [], [OVERLAY_ADD])
    assert process.returncode != 0
    assert "requires at least one '--types' file" in process.stdout


def test_overlay_with_different_root(tmp_path):
    process, _ = run_json_export(tmp_path, SPEC, [TYPES_BASE], [OVERLAY_OTHER_ROOT])
    assert process.returncode != 0
    assert "is not below the types root" in process.stdout


def test_without_overlays_unchanged(tmp_path):
    """Without overlays the base types must be self-contained, signals using overlay types fail"""
    process, _ = run_json_export(tmp_path, SPEC, [TYPES_BASE], [])
    assert process.returncode != 0


def test_compose_snapshot_contains_overlays(tmp_path):
    out_dir = tmp_path / "composed"
    cmd = f"vspec compose -u {TEST_UNITS} -q {TEST_QUANT} -s {SPEC} -t {TYPES_BASE}"
    cmd += f" --types-overlays {OVERLAY_ADD} --types-overlays {OVERLAY_MODIFY} -o {out_dir}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True, env=ENV)
    assert process.returncode == 0, process.stdout
    structs = yaml.safe_load((out_dir / "structs.vspec").read_text())
    assert "Types.Struct3" in structs
    assert "Types.Struct1.y" in structs
    assert structs["Types.Struct1"]["description"] == "Modified struct description."
    assert structs["Types.Struct1.x"]["datatype"] == "float"


def test_option_registration():
    """'--types-overlays' is available for exporters with '--types', but not for 'id'"""
    json_help = subprocess.run("vspec export json --help".split(), capture_output=True, text=True)
    assert "--types-overlays" in json_help.stdout
    id_help = subprocess.run("vspec export id --help".split(), capture_output=True, text=True)
    assert "--types-overlays" not in id_help.stdout

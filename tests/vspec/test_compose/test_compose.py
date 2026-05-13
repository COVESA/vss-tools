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
EXPECTED = HERE / "expected"


def _compose(tmp_path: Path, vspec: Path, types: Path | None = None) -> tuple[Path, subprocess.CompletedProcess]:
    out = tmp_path / "out"
    cmd = [
        "vspec",
        "compose",
        "-u",
        str(TEST_UNITS),
        "-q",
        str(TEST_QUANT),
        "-s",
        str(vspec),
        "-o",
        str(out),
    ]
    if types:
        cmd += ["--types", str(types)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return out, result


def test_compose_with_structs(tmp_path):
    """Both output files are written and match expected fixtures."""
    out, result = _compose(tmp_path, HERE / "test.vspec", HERE / "types.vspec")
    assert result.returncode == 0, result.stderr

    assert filecmp.cmp(out / "model_snapshot.vspec", EXPECTED / "model_snapshot.vspec")
    assert filecmp.cmp(out / "structs_snapshot.vspec", EXPECTED / "structs_snapshot.vspec")


def test_compose_no_types(tmp_path):
    """Without --types only model_snapshot.vspec is written; structs file absent."""
    out, result = _compose(tmp_path, HERE / "test_no_types.vspec")
    assert result.returncode == 0, result.stderr

    assert filecmp.cmp(out / "model_snapshot.vspec", EXPECTED / "model_snapshot_no_types.vspec")
    assert not (out / "structs_snapshot.vspec").exists()


def test_compose_round_trip(tmp_path):
    """Compose output can be fed back into vspec export yaml without errors."""
    out, result = _compose(tmp_path, HERE / "test.vspec", HERE / "types.vspec")
    assert result.returncode == 0, result.stderr

    yaml_out = tmp_path / "round_trip.yaml"
    rt = subprocess.run(
        [
            "vspec",
            "export",
            "yaml",
            "-u",
            str(TEST_UNITS),
            "-q",
            str(TEST_QUANT),
            "-s",
            str(out / "model_snapshot.vspec"),
            "--types",
            str(out / "structs_snapshot.vspec"),
            "--output",
            str(yaml_out),
        ],
        capture_output=True,
        text=True,
    )
    assert rt.returncode == 0, rt.stderr
    assert yaml_out.exists()


def test_compose_existing_dir_is_reused(tmp_path):
    """Pre-existing output directory is reused and stale files are overwritten."""
    out = tmp_path / "out"
    out.mkdir()
    stale = out / "model_snapshot.vspec"
    stale.write_text("stale content", encoding="utf-8")

    _, result = _compose(tmp_path, HERE / "test_no_types.vspec")
    assert result.returncode == 0, result.stderr

    assert stale.read_text(encoding="utf-8") != "stale content"

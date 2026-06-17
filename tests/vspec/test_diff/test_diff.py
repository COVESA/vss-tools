# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Tests for vss_tools.diff (pure logic) and `vspec diff` CLI."""

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from vss_tools.diff import ADDED, MODIFIED, REMOVED, diff_folders, load_flat_yaml
from vss_tools.diff_cmd import cli

FIXTURES = Path(__file__).parent / "fixtures"
PREVIOUS = FIXTURES / "previous_snapshot"
CURRENT = FIXTURES / "current_snapshot"
NO_CHANGES = FIXTURES / "no_changes_snapshot"
EMPTY = FIXTURES / "empty_previous"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def changes_by_path(result: dict[str, Any]) -> dict[str, Any]:
    """Index the changes list by 'path' for easy lookup in assertions."""
    return {c["path"]: c for c in result["changes"]}


# ---------------------------------------------------------------------------
# load_flat_yaml
# ---------------------------------------------------------------------------


class TestLoadFlatYaml:
    def test_loads_valid_yaml(self, tmp_path: Path):
        f = tmp_path / "snap.vspec"
        f.write_text("A:\n  type: branch\n  description: x\n")
        result = load_flat_yaml(f)
        assert result == {"A": {"type": "branch", "description": "x"}}

    def test_returns_empty_dict_for_missing_file(self, tmp_path: Path):
        assert load_flat_yaml(tmp_path / "nonexistent.yaml") == {}

    def test_returns_empty_dict_for_non_mapping(self, tmp_path: Path):
        f = tmp_path / "bad.yaml"
        f.write_text("- item1\n- item2\n")
        assert load_flat_yaml(f) == {}


# ---------------------------------------------------------------------------
# diff_folders — model changes
# ---------------------------------------------------------------------------


class TestSignalChanges:
    """Covers the main model diff between previous_snapshot and current_snapshot."""

    @pytest.fixture(scope="class")
    def result(self):
        return diff_folders(PREVIOUS, CURRENT)

    def test_metadata(self, result: dict[str, Any]):
        assert str(PREVIOUS) in result["previous"]
        assert str(CURRENT) in result["current"]

    def test_rename_detected(self, result: dict[str, Any]):
        by_path = changes_by_path(result)
        rename = by_path.get("A.Portal")
        assert rename is not None, "A.Portal rename not detected"
        assert rename["type"] == MODIFIED
        assert rename["source"] == "model"
        assert rename["previous_path"] == "A.Door"
        assert rename["cascade"] is False

    def test_cascade_rename_detected(self, result: dict[str, Any]):
        by_path = changes_by_path(result)
        cascade = by_path.get("A.Portal.IsOpen")
        assert cascade is not None, "A.Portal.IsOpen cascade not detected"
        assert cascade["type"] == MODIFIED
        assert cascade["previous_path"] == "A.Door.IsOpen"
        assert cascade["cascade"] is True

    def test_cascade_rename_includes_attribute_change(self, result: dict[str, Any]):
        by_path = changes_by_path(result)
        cascade = by_path["A.Portal.IsOpen"]
        # datatype changed from boolean → string
        attr_change = next((c for c in cascade["attribute_changes"] if c["attribute"] == "datatype"), None)
        assert attr_change is not None
        assert attr_change["previous"] == "boolean"
        assert attr_change["current"] == "string"

    def test_removed_signal(self, result: dict[str, Any]):
        by_path = changes_by_path(result)
        removed = by_path.get("A.Door.LockState")
        assert removed is not None, "A.Door.LockState should be removed (not cascade-matched)"
        assert removed["type"] == REMOVED

    def test_added_signal(self, result: dict[str, Any]):
        by_path = changes_by_path(result)
        added = by_path.get("A.Humidity")
        assert added is not None
        assert added["type"] == ADDED
        assert added["source"] == "model"

    def test_modified_attribute(self, result: dict[str, Any]):
        by_path = changes_by_path(result)
        modified = by_path.get("A.Speed")
        assert modified is not None, "A.Speed unit change not detected"
        assert modified["type"] == MODIFIED
        attr_change = next((c for c in modified["attribute_changes"] if c["attribute"] == "unit"), None)
        assert attr_change is not None
        assert attr_change["previous"] == "km/h"
        assert attr_change["current"] == "m/s"

    def test_summary_counts(self, result: dict[str, Any]):
        summary = result["summary"]
        assert summary[ADDED] >= 1
        assert summary[REMOVED] >= 1
        assert summary[MODIFIED] >= 1

    def test_message_field_present_on_all_changes(self, result: dict[str, Any]):
        for c in result["changes"]:
            assert "message" in c, f"Missing 'message' on change: {c}"
            assert isinstance(c["message"], str) and c["message"]


# ---------------------------------------------------------------------------
# diff_folders — units changes
# ---------------------------------------------------------------------------


class TestUnitChanges:
    @pytest.fixture(scope="class")
    def result(self):
        return diff_folders(PREVIOUS, CURRENT)

    def test_unit_removed(self, result: dict[str, Any]):
        by_path = changes_by_path(result)
        removed = by_path.get("km/h")
        assert removed is not None
        assert removed["type"] == REMOVED
        assert removed["source"] == "units"

    def test_unit_added(self, result: dict[str, Any]):
        by_path = changes_by_path(result)
        added = by_path.get("percent")
        assert added is not None
        assert added["type"] == ADDED
        assert added["source"] == "units"


# ---------------------------------------------------------------------------
# diff_folders — no changes
# ---------------------------------------------------------------------------


class TestNoChanges:
    def test_empty_changes_when_identical(self):
        result = diff_folders(NO_CHANGES, NO_CHANGES)
        assert result["changes"] == []
        assert result["summary"][ADDED] == 0
        assert result["summary"][REMOVED] == 0
        assert result["summary"][MODIFIED] == 0


# ---------------------------------------------------------------------------
# diff_folders — missing files are tolerated
# ---------------------------------------------------------------------------


class TestMissingFiles:
    def test_empty_previous_dir_treated_as_all_added(self, tmp_path: Path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = diff_folders(empty_dir, PREVIOUS)
        types = {c["type"] for c in result["changes"]}
        # Everything in PREVIOUS is new from the perspective of an empty baseline
        assert types == {ADDED}

    def test_missing_structs_file_is_skipped(self):
        # PREVIOUS has no structs_snapshot.vspec — should not error
        result = diff_folders(PREVIOUS, CURRENT)
        structs_changes = [c for c in result["changes"] if c["source"] == "structs"]
        # No structs file in either → 0 structs changes
        assert structs_changes == []


# ---------------------------------------------------------------------------
# diff_folders — fka type mismatch ignored
# ---------------------------------------------------------------------------


class TestFkaTypeMismatch:
    def test_fka_with_different_node_type_not_treated_as_rename(self, tmp_path: Path):
        prev_dir = tmp_path / "prev"
        curr_dir = tmp_path / "curr"
        prev_dir.mkdir()
        curr_dir.mkdir()

        (prev_dir / "model_snapshot.vspec").write_text(
            "A.OldSignal:\n  datatype: float\n  description: x\n  type: sensor\n"
        )
        (curr_dir / "model_snapshot.vspec").write_text(
            "A.NewBranch:\n  description: x\n  fka: A.OldSignal\n  type: branch\n"
        )

        result = diff_folders(prev_dir, curr_dir)
        by_path = changes_by_path(result)
        # Type mismatch → no rename; both reported independently
        assert by_path["A.OldSignal"]["type"] == REMOVED
        assert by_path["A.NewBranch"]["type"] == ADDED


# ---------------------------------------------------------------------------
# CLI — vspec diff
# ---------------------------------------------------------------------------


class TestDiffCli:
    def test_cli_outputs_json_to_stdout(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["-p", str(PREVIOUS), "-c", str(CURRENT)])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "changes" in data
        assert "summary" in data

    def test_cli_writes_to_file(self, tmp_path: Path):
        out = tmp_path / "diff.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["-p", str(PREVIOUS), "-c", str(CURRENT), "-o", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()
        data = json.loads(out.read_text())
        assert "changes" in data

    def test_cli_no_changes(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["-p", str(NO_CHANGES), "-c", str(NO_CHANGES)])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["changes"] == []

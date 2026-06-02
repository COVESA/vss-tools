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
from vss_tools.diff import (
    ADDED,
    ENTITY,
    ENUM_VALUE,
    MODIFIED,
    PROPERTY,
    REMOVED,
    diff_folders,
    load_flat_yaml,
)
from vss_tools.diff_cmd import cli

FIXTURES = Path(__file__).parent / "fixtures"
PREVIOUS = FIXTURES / "previous_snapshot"
CURRENT = FIXTURES / "current_snapshot"
NO_CHANGES = FIXTURES / "no_changes_snapshot"
EMPTY = FIXTURES / "empty_previous"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def changes_by_label(result: dict[str, Any]) -> dict[str, Any]:
    """Index the changes list by 'label' for easy lookup in assertions."""
    return {c["label"]: c for c in result["changes"]}


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
        by_label = changes_by_label(result)
        rename = by_label.get("A.Portal")
        assert rename is not None, "A.Portal rename not detected"
        assert rename["change_type"] == MODIFIED
        assert rename["kind"] == ENTITY
        assert rename["renamed_from"] == "A.Door"

    def test_cascade_rename_detected(self, result: dict[str, Any]):
        by_label = changes_by_label(result)
        cascade = by_label.get("A.Portal.IsOpen")
        assert cascade is not None, "A.Portal.IsOpen cascade not detected"
        assert cascade["change_type"] == MODIFIED
        assert cascade["kind"] == PROPERTY
        assert cascade["renamed_from"] == "A.Door.IsOpen"
        assert cascade["parent_label"] == "A.Portal"

    def test_cascade_rename_includes_aspect_change(self, result: dict[str, Any]):
        by_label = changes_by_label(result)
        cascade = by_label["A.Portal.IsOpen"]
        # datatype changed from boolean → string, mapped to output_type
        assert cascade["aspects"].get("output_type") == "string"

    def test_removed_signal(self, result: dict[str, Any]):
        by_label = changes_by_label(result)
        removed = by_label.get("A.Door.LockState")
        assert removed is not None, "A.Door.LockState should be removed"
        assert removed["change_type"] == REMOVED
        assert removed["kind"] == PROPERTY

    def test_added_signal(self, result: dict[str, Any]):
        by_label = changes_by_label(result)
        added = by_label.get("A.Humidity")
        assert added is not None
        assert added["change_type"] == ADDED
        assert added["kind"] == PROPERTY
        assert added["parent_label"] == "A"
        assert added["aspects"]["output_type"] == "float"
        assert added["aspects"]["is_list"] is False
        assert added["aspects"]["is_required"] is False

    def test_modified_attribute(self, result: dict[str, Any]):
        by_label = changes_by_label(result)
        modified = by_label.get("A.Speed")
        assert modified is not None, "A.Speed unit change not detected"
        assert modified["change_type"] == MODIFIED
        assert modified["aspects"].get("unit") == "m/s"

    def test_no_summary_field(self, result: dict[str, Any]):
        assert "summary" not in result

    def test_no_message_field_on_any_change(self, result: dict[str, Any]):
        for c in result["changes"]:
            assert "message" not in c, f"Unexpected 'message' on change: {c}"

    def test_no_cascade_field_on_any_change(self, result: dict[str, Any]):
        for c in result["changes"]:
            assert "cascade" not in c, f"Unexpected 'cascade' on change: {c}"


# ---------------------------------------------------------------------------
# diff_folders — units changes
# ---------------------------------------------------------------------------


class TestUnitChanges:
    @pytest.fixture(scope="class")
    def result(self):
        return diff_folders(PREVIOUS, CURRENT)

    def test_unit_removed(self, result: dict[str, Any]):
        by_label = changes_by_label(result)
        removed = by_label.get("km/h")
        assert removed is not None
        assert removed["change_type"] == REMOVED
        assert removed["kind"] == ENUM_VALUE
        assert removed["parent_label"] == "speed"

    def test_unit_added(self, result: dict[str, Any]):
        by_label = changes_by_label(result)
        added = by_label.get("percent")
        assert added is not None
        assert added["change_type"] == ADDED
        assert added["kind"] == ENUM_VALUE
        assert added["parent_label"] == "relation"
        # 'unit' renamed to 'symbol' in aspects
        assert "symbol" in added["aspects"]
        assert "unit" not in added["aspects"]

    def test_unit_has_no_output_type(self, result: dict[str, Any]):
        by_label = changes_by_label(result)
        added = by_label.get("percent")
        assert added is not None
        assert "output_type" not in added["aspects"]


# ---------------------------------------------------------------------------
# diff_folders — entity content injection
# ---------------------------------------------------------------------------


class TestEntityContent:
    @pytest.fixture(scope="class")
    def result(self):
        return diff_folders(PREVIOUS, CURRENT)

    def test_parent_entity_has_content_for_added_child(self, result: dict[str, Any]):
        # A.Humidity was added under A — A should appear as ENTITY MODIFIED with content
        by_label = changes_by_label(result)
        entity_a = by_label.get("A")
        assert entity_a is not None, "Synthetic ENTITY MODIFIED for 'A' not found"
        assert entity_a["kind"] == ENTITY
        assert entity_a["change_type"] == MODIFIED
        content_labels = [item["label"] for item in entity_a.get("content", [])]
        assert "A.Humidity" in content_labels

    def test_parent_entity_has_content_for_removed_child(self, result: dict[str, Any]):
        # A.Door.LockState was removed — its parent A.Door (now A.Portal) should have content
        # A.Portal is already MODIFIED (rename) so content is injected into it
        by_label = changes_by_label(result)
        portal = by_label.get("A.Portal")
        assert portal is not None
        content_labels = [item["label"] for item in portal.get("content", [])]
        assert "A.Portal.IsOpen" in content_labels


# ---------------------------------------------------------------------------
# diff_folders — no changes
# ---------------------------------------------------------------------------


class TestNoChanges:
    def test_empty_changes_when_identical(self):
        result = diff_folders(NO_CHANGES, NO_CHANGES)
        assert result["changes"] == []


# ---------------------------------------------------------------------------
# diff_folders — missing files are tolerated
# ---------------------------------------------------------------------------


class TestMissingFiles:
    def test_empty_previous_dir_treated_as_all_added(self, tmp_path: Path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = diff_folders(empty_dir, PREVIOUS)
        # All leaf events must be ADDED; ENTITY MODIFIED may be injected as parent summaries
        non_entity_types = {c["change_type"] for c in result["changes"] if c["kind"] not in (ENTITY, "ENUMERATION_SET")}
        assert non_entity_types == {ADDED}

    def test_first_run_mode_all_added(self):
        result = diff_folders(None, CURRENT)
        # All leaf events must be ADDED; ENTITY MODIFIED may be injected as parent summaries
        non_entity_types = {c["change_type"] for c in result["changes"] if c["kind"] not in (ENTITY, "ENUMERATION_SET")}
        assert non_entity_types == {ADDED}
        assert result["previous"] is None

    def test_missing_structs_file_is_skipped(self):
        result = diff_folders(PREVIOUS, CURRENT)
        # No structs file in either snapshot → no ENUMERATION_SET or struct ENTITY events
        struct_changes = [c for c in result["changes"] if c.get("kind") == "ENUMERATION_SET"]
        assert struct_changes == []


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
        by_label = changes_by_label(result)
        # Type mismatch → no rename; both reported independently
        assert by_label["A.OldSignal"]["change_type"] == REMOVED
        assert by_label["A.NewBranch"]["change_type"] == ADDED


# ---------------------------------------------------------------------------
# diff_folders — datatype array mapping
# ---------------------------------------------------------------------------


class TestDatatypeMapping:
    def test_array_datatype_sets_is_list(self, tmp_path: Path):
        prev_dir = tmp_path / "prev"
        curr_dir = tmp_path / "curr"
        prev_dir.mkdir()
        curr_dir.mkdir()

        (prev_dir / "model_snapshot.vspec").write_text(
            "A.Vals:\n  datatype: float[]\n  description: x\n  type: sensor\n"
        )
        (curr_dir / "model_snapshot.vspec").write_text(
            "A.Vals:\n  datatype: float[]\n  description: x\n  type: sensor\n"
        )

        result = diff_folders(prev_dir, curr_dir)
        # No changes between identical snapshots
        assert result["changes"] == []

    def test_added_array_signal_has_is_list_true(self, tmp_path: Path):
        prev_dir = tmp_path / "prev"
        curr_dir = tmp_path / "curr"
        prev_dir.mkdir()
        curr_dir.mkdir()

        (prev_dir / "model_snapshot.vspec").write_text("")
        (curr_dir / "model_snapshot.vspec").write_text(
            "A.Tags:\n  datatype: string[]\n  description: list of tags\n  type: sensor\n"
        )

        result = diff_folders(prev_dir, curr_dir)
        by_label = changes_by_label(result)
        signal = by_label.get("A.Tags")
        assert signal is not None
        assert signal["aspects"]["output_type"] == "string"
        assert signal["aspects"]["is_list"] is True


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

    def test_cli_first_run_mode_no_previous(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["-c", str(CURRENT)])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["previous"] is None
        # All leaf events must be ADDED; ENTITY MODIFIED may be injected as parent summaries
        non_entity_types = {c["change_type"] for c in data["changes"] if c["kind"] not in (ENTITY, "ENUMERATION_SET")}
        assert non_entity_types == {ADDED}


# ---------------------------------------------------------------------------
# _expand_instances — Cartesian product
# ---------------------------------------------------------------------------


class TestExpandInstances:
    """Unit tests for the _expand_instances helper."""

    def _expand(self, value: Any) -> list[str]:
        from vss_tools.diff import _expand_instances

        return _expand_instances(value)

    def test_single_plain_string(self):
        assert self._expand("Row[1,3]") == ["Row1", "Row2", "Row3"]

    def test_plain_list_is_single_dimension(self):
        assert self._expand(["Left", "Right"]) == ["Left", "Right"]

    def test_range_string_in_list_is_single_dimension(self):
        assert self._expand(["Row[1,2]"]) == ["Row1", "Row2"]

    def test_multidimensional_cartesian_product(self):
        # ["Row[1,4]", ["DriverSide","PassengerSide"]] → 8 combinations
        value = ["Row[1,4]", ["DriverSide", "PassengerSide"]]
        result = self._expand(value)
        expected = [
            "Row1.DriverSide",
            "Row1.PassengerSide",
            "Row2.DriverSide",
            "Row2.PassengerSide",
            "Row3.DriverSide",
            "Row3.PassengerSide",
            "Row4.DriverSide",
            "Row4.PassengerSide",
        ]
        assert result == expected

    def test_two_range_dimensions(self):
        value = ["Row[1,2]", "Pos[1,2]"]
        result = self._expand(value)
        assert result == ["Row1.Pos1", "Row1.Pos2", "Row2.Pos1", "Row2.Pos2"]

    def test_none_returns_empty(self):
        assert self._expand(None) == []

    def test_multidimensional_in_diff_output(self, tmp_path: Path):
        """Cartesian product instances appear correctly in diff_folders output."""
        from vss_tools.diff import diff_folders

        prev_dir = tmp_path / "prev"
        curr_dir = tmp_path / "curr"
        prev_dir.mkdir()
        curr_dir.mkdir()

        (prev_dir / "model_snapshot.vspec").write_text(
            "Vehicle.Seat:\n"
            "  type: branch\n"
            "  description: seat\n"
            "  instances:\n"
            "    - Row[1,2]\n"
            "    - - DriverSide\n"
            "      - PassengerSide\n"
        )
        (curr_dir / "model_snapshot.vspec").write_text(
            "Vehicle.Seat:\n"
            "  type: branch\n"
            "  description: seat\n"
            "  instances:\n"
            "    - Row[1,2]\n"
            "    - - DriverSide\n"
            "      - PassengerSide\n"
        )

        result = diff_folders(prev_dir, curr_dir)
        assert result["changes"] == []

    def test_instances_added_with_cartesian_product(self, tmp_path: Path):
        """An ADDED ENTITY node with multi-dimensional instances has Cartesian product in aspects."""
        from vss_tools.diff import ADDED, ENTITY, diff_folders

        prev_dir = tmp_path / "prev"
        curr_dir = tmp_path / "curr"
        prev_dir.mkdir()
        curr_dir.mkdir()

        (prev_dir / "model_snapshot.vspec").write_text("")
        (curr_dir / "model_snapshot.vspec").write_text(
            "Vehicle.Seat:\n"
            "  type: branch\n"
            "  description: seat\n"
            "  instances:\n"
            "    - Row[1,2]\n"
            "    - - DriverSide\n"
            "      - PassengerSide\n"
        )

        result = diff_folders(prev_dir, curr_dir)
        by_label = {c["label"]: c for c in result["changes"]}
        seat = by_label.get("Vehicle.Seat")
        assert seat is not None
        assert seat["change_type"] == ADDED
        assert seat["kind"] == ENTITY
        assert seat["aspects"]["instances"] == [
            "Row1.DriverSide",
            "Row1.PassengerSide",
            "Row2.DriverSide",
            "Row2.PassengerSide",
        ]

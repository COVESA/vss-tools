# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Tests for the top-level `property_paths` list required by modl >=0.8.0."""

from pathlib import Path
from typing import Any

import yaml
from modl.ir import DiffReport

from vss_tools.diff import diff_folders


def snapshot(
    root: Path,
    name: str,
    model: dict[str, Any] | None = None,
    structs: dict[str, Any] | None = None,
) -> Path:
    folder = root / name
    folder.mkdir()
    (folder / "model.vspec").write_text(yaml.safe_dump(model or {}), encoding="utf-8")
    if structs is not None:
        (folder / "structs.vspec").write_text(yaml.safe_dump(structs), encoding="utf-8")
    return folder


def paths_for(result: dict[str, Any], label: str) -> dict[str, Any]:
    matches = [p for p in result["property_paths"] if p["label"] == label]
    assert len(matches) == 1, f"expected exactly one property_paths entry for {label}, got {len(matches)}"
    return matches[0]


def path_strings(entry: dict[str, Any]) -> set[str]:
    return {p["path"] for p in entry["paths"]}


def change_for_path(entry: dict[str, Any], path: str) -> str:
    matches = [p["change"] for p in entry["paths"] if p["path"] == path]
    assert len(matches) == 1
    return matches[0]


class TestSingletonAndSingleDimension:
    def test_singleton_property_has_single_path_entry(self, tmp_path: Path):
        prev = snapshot(tmp_path, "prev", {"Vehicle": {"type": "branch", "description": "root"}})
        curr = snapshot(
            tmp_path,
            "curr",
            {
                "Vehicle": {"type": "branch", "description": "root"},
                "Vehicle.Speed": {"type": "sensor", "datatype": "float", "description": "speed"},
            },
        )
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        entry = paths_for(result, "Vehicle.Speed")
        assert entry["parent_label"] == "Vehicle"
        assert entry["paths"] == [{"tags": {}, "path": "Vehicle.Speed", "change": "added"}]

    def test_single_dimension_instanced_ancestor_fans_out(self, tmp_path: Path):
        model = {
            "Vehicle": {"type": "branch", "description": "root"},
            "Vehicle.Door": {"type": "branch", "description": "door", "instances": ["Left", "Right"]},
            "Vehicle.Door.IsOpen": {"type": "sensor", "datatype": "boolean", "description": "open"},
        }
        prev = snapshot(tmp_path, "prev", {"Vehicle": {"type": "branch", "description": "root"}})
        curr = snapshot(tmp_path, "curr", model)
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        entry = paths_for(result, "Vehicle.Door.IsOpen")
        assert path_strings(entry) == {"Vehicle.Door.Left.IsOpen", "Vehicle.Door.Right.IsOpen"}
        for p in entry["paths"]:
            assert p["change"] == "added"
            assert set(p["tags"]) == {"Vehicle.Door"}
            assert set(p["tags"]["Vehicle.Door"]) == {"dimension1"}


class TestMultiDimensionAndNestedAncestors:
    def test_multi_dimension_ancestor_cartesian_product(self, tmp_path: Path):
        model = {
            "Vehicle": {"type": "branch", "description": "root"},
            "Vehicle.Seat": {
                "type": "branch",
                "description": "seat",
                "instances": ["Row[1,2]", ["Left", "Right"]],
            },
            "Vehicle.Seat.Position": {"type": "sensor", "datatype": "float", "description": "pos"},
        }
        prev = snapshot(tmp_path, "prev", {"Vehicle": {"type": "branch", "description": "root"}})
        curr = snapshot(tmp_path, "curr", model)
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        entry = paths_for(result, "Vehicle.Seat.Position")
        assert path_strings(entry) == {
            "Vehicle.Seat.Row1.Left.Position",
            "Vehicle.Seat.Row1.Right.Position",
            "Vehicle.Seat.Row2.Left.Position",
            "Vehicle.Seat.Row2.Right.Position",
        }

    def test_nested_multi_ancestor_axle_wheel(self, tmp_path: Path):
        """Each contributing ancestor's hop is inserted right after its own segment."""
        model = {
            "Vehicle": {"type": "branch", "description": "root"},
            "Vehicle.Axle": {"type": "branch", "description": "axle", "instances": "Axle[1,2]"},
            "Vehicle.Axle.Wheel": {"type": "branch", "description": "wheel", "instances": ["Left", "Right"]},
            "Vehicle.Axle.Wheel.Speed": {"type": "sensor", "datatype": "float", "description": "speed"},
        }
        prev = snapshot(tmp_path, "prev", {"Vehicle": {"type": "branch", "description": "root"}})
        curr = snapshot(tmp_path, "curr", model)
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        entry = paths_for(result, "Vehicle.Axle.Wheel.Speed")
        assert path_strings(entry) == {
            "Vehicle.Axle.Axle1.Wheel.Left.Speed",
            "Vehicle.Axle.Axle1.Wheel.Right.Speed",
            "Vehicle.Axle.Axle2.Wheel.Left.Speed",
            "Vehicle.Axle.Axle2.Wheel.Right.Speed",
        }
        axle1_left = next(p for p in entry["paths"] if p["path"] == "Vehicle.Axle.Axle1.Wheel.Left.Speed")
        assert axle1_left["tags"] == {
            "Vehicle.Axle": {"dimension1": "Axle1"},
            "Vehicle.Axle.Wheel": {"dimension1": "Left"},
        }


class TestInstantiateFalsePinning:
    def test_instantiate_false_skips_immediate_parent_instances(self, tmp_path: Path):
        model = {
            "Vehicle": {"type": "branch", "description": "root"},
            "Vehicle.Zone": {"type": "branch", "description": "zone", "instances": ["Left", "Right", "Center"]},
            "Vehicle.Zone.Label": {
                "type": "sensor",
                "datatype": "string",
                "description": "label",
                "instantiate": False,
            },
        }
        prev = snapshot(tmp_path, "prev", {"Vehicle": {"type": "branch", "description": "root"}})
        curr = snapshot(tmp_path, "curr", model)
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        entry = paths_for(result, "Vehicle.Zone.Label")
        # Only one occurrence — the immediate parent's instances are not fanned out.
        assert entry["paths"] == [{"tags": {}, "path": "Vehicle.Zone.Label", "change": "added"}]


class TestAncestorRenameClassification:
    def test_ancestor_rename_refreshes_path_without_add_remove(self, tmp_path: Path):
        prev_model = {
            "Vehicle": {"type": "branch", "description": "root"},
            "Vehicle.Door": {"type": "branch", "description": "door", "instances": ["Left", "Right"]},
            "Vehicle.Door.IsOpen": {"type": "sensor", "datatype": "boolean", "description": "open"},
        }
        curr_model = {
            "Vehicle": {"type": "branch", "description": "root"},
            "Vehicle.Portal": {
                "type": "branch",
                "description": "door",
                "fka": "Vehicle.Door",
                "instances": ["Left", "Right"],
            },
            "Vehicle.Portal.IsOpen": {"type": "sensor", "datatype": "boolean", "description": "open"},
        }
        prev = snapshot(tmp_path, "prev", prev_model)
        curr = snapshot(tmp_path, "curr", curr_model)
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        entry = paths_for(result, "Vehicle.Portal.IsOpen")
        assert path_strings(entry) == {"Vehicle.Portal.Left.IsOpen", "Vehicle.Portal.Right.IsOpen"}
        for p in entry["paths"]:
            assert p["change"] == "unchanged"
            assert p["tags"] == {"Vehicle.Portal": {"dimension1": p["path"].split(".")[2]}}


class TestEntityInstanceDeltaCascade:
    def test_entity_gaining_instance_recascades_untouched_property(self, tmp_path: Path):
        prev_model = {
            "Vehicle": {"type": "branch", "description": "root"},
            "Vehicle.Door": {"type": "branch", "description": "door", "instances": ["Left", "Right"]},
            "Vehicle.Door.IsOpen": {"type": "sensor", "datatype": "boolean", "description": "open"},
        }
        curr_model = {
            "Vehicle": {"type": "branch", "description": "root"},
            "Vehicle.Door": {
                "type": "branch",
                "description": "door",
                "instances": ["Left", "Right", "Center"],
            },
            "Vehicle.Door.IsOpen": {"type": "sensor", "datatype": "boolean", "description": "open"},
        }
        prev = snapshot(tmp_path, "prev", prev_model)
        curr = snapshot(tmp_path, "curr", curr_model)
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        # Vehicle.Door.IsOpen itself has no own ADDED/REMOVED/MODIFIED event (its attributes
        # didn't change), yet it must still be re-reported with a fresh "added" path entry
        # for the new Center instance.
        entry = paths_for(result, "Vehicle.Door.IsOpen")
        assert path_strings(entry) == {
            "Vehicle.Door.Left.IsOpen",
            "Vehicle.Door.Right.IsOpen",
            "Vehicle.Door.Center.IsOpen",
        }
        assert change_for_path(entry, "Vehicle.Door.Left.IsOpen") == "unchanged"
        assert change_for_path(entry, "Vehicle.Door.Right.IsOpen") == "unchanged"
        assert change_for_path(entry, "Vehicle.Door.Center.IsOpen") == "added"


class TestStructMembersExcluded:
    """Struct fields never get their own property_paths entry — only the referencing
    property (binding-eligible via `binding_eligible`) does."""

    def test_struct_field_not_reported_single_usage_site(self, tmp_path: Path):
        structs = {
            "Types.Position": {"type": "struct", "description": "position"},
            "Types.Position.x": {"type": "property", "datatype": "float", "description": "x"},
        }
        prev = snapshot(tmp_path, "prev", {"Vehicle": {"type": "branch", "description": "root"}}, structs=structs)
        curr = snapshot(
            tmp_path,
            "curr",
            {
                "Vehicle": {"type": "branch", "description": "root"},
                "Vehicle.Position": {"type": "sensor", "datatype": "Types.Position", "description": "pos"},
            },
            structs=structs,
        )
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        assert [p for p in result["property_paths"] if p["label"] == "Types.Position.x"] == []
        entry = paths_for(result, "Vehicle.Position")
        assert entry["paths"] == [{"tags": {}, "path": "Vehicle.Position", "change": "added"}]

    def test_struct_field_not_reported_with_multiple_usage_sites(self, tmp_path: Path):
        structs = {
            "Types.Position": {"type": "struct", "description": "position"},
            "Types.Position.x": {"type": "property", "datatype": "float", "description": "x"},
        }
        model = {
            "Vehicle": {"type": "branch", "description": "root"},
            "Vehicle.Front": {"type": "sensor", "datatype": "Types.Position", "description": "front pos"},
            "Vehicle.Rear": {"type": "sensor", "datatype": "Types.Position", "description": "rear pos"},
        }
        prev = snapshot(tmp_path, "prev", {"Vehicle": {"type": "branch", "description": "root"}}, structs=structs)
        curr = snapshot(tmp_path, "curr", model, structs=structs)
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        assert [p for p in result["property_paths"] if p["label"] == "Types.Position.x"] == []
        assert path_strings(paths_for(result, "Vehicle.Front")) == {"Vehicle.Front"}
        assert path_strings(paths_for(result, "Vehicle.Rear")) == {"Vehicle.Rear"}

    def test_nested_struct_of_struct_members_not_reported(self, tmp_path: Path):
        structs = {
            "Types.Inner": {"type": "struct", "description": "inner"},
            "Types.Inner.value": {"type": "property", "datatype": "float", "description": "value"},
            "Types.Outer": {"type": "struct", "description": "outer"},
            "Types.Outer.inner": {"type": "property", "datatype": "Types.Inner", "description": "inner field"},
        }
        prev = snapshot(tmp_path, "prev", {"Vehicle": {"type": "branch", "description": "root"}}, structs=structs)
        curr = snapshot(
            tmp_path,
            "curr",
            {
                "Vehicle": {"type": "branch", "description": "root"},
                "Vehicle.Outer": {"type": "sensor", "datatype": "Types.Outer", "description": "outer sensor"},
            },
            structs=structs,
        )
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        assert [p for p in result["property_paths"] if p["label"] == "Types.Inner.value"] == []
        assert [p for p in result["property_paths"] if p["label"] == "Types.Outer.inner"] == []
        entry = paths_for(result, "Vehicle.Outer")
        assert entry["paths"] == [{"tags": {}, "path": "Vehicle.Outer", "change": "added"}]


class TestStructMemberIsLeafFalse:
    """
    Struct fields are never independently addressable — they have no property_paths entry
    (see TestStructMembersExcluded), so they must never be reported as binding-eligible in
    `changes` either, regardless of their own datatype: is_leaf=False and binding_eligible
    omitted (effectively False), even when the field's own datatype is a primitive.
    """

    def test_primitive_struct_field_is_leaf_false(self, tmp_path: Path):
        structs = {
            "Types.Position": {"type": "struct", "description": "position"},
            "Types.Position.x": {"type": "property", "datatype": "float", "description": "x"},
        }
        prev = snapshot(tmp_path, "prev", {"Vehicle": {"type": "branch", "description": "root"}})
        curr = snapshot(
            tmp_path,
            "curr",
            {
                "Vehicle": {"type": "branch", "description": "root"},
                "Vehicle.Position": {"type": "sensor", "datatype": "Types.Position", "description": "pos"},
            },
            structs=structs,
        )
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        field_event = next(c for c in result["changes"] if c["label"] == "Types.Position.x")
        assert field_event["is_leaf"] is False
        assert "binding_eligible" not in field_event

        # The referencing property itself is still binding-eligible.
        ref_event = next(c for c in result["changes"] if c["label"] == "Vehicle.Position" and c["kind"] == "PROPERTY")
        assert ref_event["is_leaf"] is False
        assert ref_event["binding_eligible"] is True

    def test_struct_of_struct_field_is_leaf_false_and_references_preserved(self, tmp_path: Path):
        structs = {
            "Types.Inner": {"type": "struct", "description": "inner"},
            "Types.Inner.value": {"type": "property", "datatype": "float", "description": "value"},
            "Types.Outer": {"type": "struct", "description": "outer"},
            "Types.Outer.inner": {"type": "property", "datatype": "Types.Inner", "description": "inner field"},
        }
        prev = snapshot(tmp_path, "prev", {"Vehicle": {"type": "branch", "description": "root"}})
        curr = snapshot(
            tmp_path,
            "curr",
            {
                "Vehicle": {"type": "branch", "description": "root"},
                "Vehicle.Outer": {"type": "sensor", "datatype": "Types.Outer", "description": "outer sensor"},
            },
            structs=structs,
        )
        result = diff_folders(prev, curr)
        DiffReport.model_validate(result)

        # The struct-of-struct field is non-leaf by its own datatype too, and must not be
        # binding-eligible either way.
        inner_field_event = next(c for c in result["changes"] if c["label"] == "Types.Outer.inner")
        assert inner_field_event["is_leaf"] is False
        assert "binding_eligible" not in inner_field_event
        # references is still derived from the real datatype, for contract cascading purposes.
        assert inner_field_event["references"] == {"output_type": "Types.Inner"}

        value_field_event = next(c for c in result["changes"] if c["label"] == "Types.Inner.value")
        assert value_field_event["is_leaf"] is False
        assert "binding_eligible" not in value_field_event

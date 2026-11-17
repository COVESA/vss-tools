# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""
Consistency rules between the change events and the runtime `property_paths` of a diff report.

The runtime paths come from the vss-tools tree, so they must equal what `vspec export` produces
for the same model. `assert_report_consistent` enforces the rules for every scenario below.
"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from modl.ir import DiffReport

from vss_tools.diff import _expand_instances, diff_folders

VSPEC_DIR = Path(__file__).resolve().parents[1]
LEAF_TYPES = {"sensor", "actuator", "attribute"}

Model = dict[str, dict[str, Any]]


def branch(**extra: Any) -> dict[str, Any]:
    return {"type": "branch", "description": "b", **extra}


def sensor(**extra: Any) -> dict[str, Any]:
    return {"type": "sensor", "datatype": "uint32", "description": "s", **extra}


def write_snapshot(root: Path, name: str, model: Model) -> Path:
    folder = root / name
    folder.mkdir()
    (folder / "model.vspec").write_text(yaml.safe_dump(model), encoding="utf-8")
    return folder


def export_nodes(tmp_path: Path, name: str, model: Model) -> dict[str, dict[str, Any]]:
    """Expand a model with the real `vspec export yaml` and return the flat result."""
    spec = tmp_path / f"{name}_export.vspec"
    out = tmp_path / f"{name}_export.yaml"
    spec.write_text(yaml.safe_dump(model), encoding="utf-8")
    vspec = shutil.which("vspec") or str(Path(sys.executable).parent / "vspec")
    subprocess.run(
        [
            vspec,
            "export",
            "yaml",
            "-s",
            str(spec),
            "-u",
            str(VSPEC_DIR / "test_units.yaml"),
            "-q",
            str(VSPEC_DIR / "test_quantities.yaml"),
            "-o",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return yaml.safe_load(out.read_text(encoding="utf-8"))


def leaf_paths(nodes: dict[str, dict[str, Any]]) -> set[str]:
    return {fqn for fqn, attrs in nodes.items() if attrs.get("type") in LEAF_TYPES}


def canonicalize(path: str, rename_map: dict[str, str]) -> str:
    for old, new in sorted(rename_map.items(), key=lambda kv: -len(kv[0])):
        if path == old or path.startswith(old + "."):
            return new + path[len(old) :]
    return path


def effective_instantiate(attrs: dict[str, Any]) -> bool:
    return attrs.get("instantiate") is not False


def assert_report_consistent(report: dict[str, Any], prev_model: Model, curr_model: Model, tmp_path: Path) -> None:
    """Enforce the consistency rules between `changes` and `property_paths` of one report."""
    DiffReport.model_validate(report)
    changes = report["changes"]
    entries = report["property_paths"]

    prev_nodes = export_nodes(tmp_path, "prev", prev_model)
    curr_nodes = export_nodes(tmp_path, "curr", curr_model)
    prev_leaves, curr_leaves = leaf_paths(prev_nodes), leaf_paths(curr_nodes)

    rename_map = {
        ev["renamed_from"]: ev["label"]
        for ev in changes
        if ev["kind"] == "ENTITY" and ev["change_type"] == "MODIFIED" and ev.get("renamed_from")
    }
    keys = [(e["label"], e["parent_label"]) for e in entries]
    assert len(keys) == len(set(keys)), "duplicate property_paths entries"

    changed_entities = {
        ev["label"]
        for ev in changes
        if ev["kind"] == "ENTITY"
        and ev["change_type"] == "MODIFIED"
        and (ev["aspects"].get("instances_added") or ev["aspects"].get("instances_removed"))
    }
    property_events = {
        (ev["label"], ev["parent_label"]): ev
        for ev in changes
        if ev["kind"] == "PROPERTY" and (ev.get("is_leaf") or ev.get("binding_eligible"))
    }

    # Completeness: every binding-eligible property event has exactly one entry, and vice versa
    # (an entry without an event must be justified by an instance change of a tagged entity).
    for key, ev in property_events.items():
        assert key in keys, f"binding-eligible property event {key} has no property_paths entry"
        entry = next(e for e in entries if (e["label"], e["parent_label"]) == key)
        paths = {p["path"]: p["change"] for p in entry["paths"]}
        if ev["change_type"] == "ADDED":
            assert set(paths.values()) <= {"added"}, f"{key}: ADDED event with non-added paths"
        elif ev["change_type"] == "REMOVED":
            assert set(paths.values()) <= {"removed"}, f"{key}: REMOVED event with non-removed paths"

    seen_paths: set[str] = set()
    for entry in entries:
        key = (entry["label"], entry["parent_label"])
        label_in_both = entry["label"] in prev_model and entry["label"] in curr_model
        flipped = label_in_both and effective_instantiate(prev_model[entry["label"]]) != effective_instantiate(
            curr_model[entry["label"]]
        )
        if key not in property_events:
            assert any(tag in changed_entities for p in entry["paths"] for tag in p["tags"]), (
                f"{key}: entry without own event is not justified by an entity instance change"
            )

        for p in entry["paths"]:
            path, change, tags = p["path"], p["change"], p["tags"]
            assert path not in seen_paths, f"path {path} reported twice"
            seen_paths.add(path)

            # Path integrity against the real exporter, on the side(s) the change says.
            in_curr = path in curr_leaves
            in_prev = path in {canonicalize(x, rename_map) for x in prev_leaves}
            assert (change in ("added", "unchanged")) == in_curr, f"{path}: '{change}' disagrees with current tree"
            assert (change in ("removed", "unchanged")) == in_prev, f"{path}: '{change}' disagrees with previous tree"

            # Tag validity: keys are instanced entities, values are among their instances.
            model = prev_model if change == "removed" else curr_model
            for entity, dims in tags.items():
                source = {v: k for k, v in rename_map.items()}.get(entity, entity) if change == "removed" else entity
                declared = _expand_instances(model[source]["instances"])
                for dim, value in dims.items():
                    assert value in declared[dim], f"{path}: tag {entity}.{dim}={value} is not an instance"

            # Path-to-cause: a path appearing/disappearing on a label present on both sides needs a cause.
            if label_in_both and not flipped and change in ("added", "removed"):
                assert any(tag in changed_entities for tag in tags), f"{path}: '{change}' without an instance change"

    # Entity integrity: events are only reported for authored labels (instance branches such as
    # `Vehicle.Axle.Axle1.Wheel.Left` are an aspect of their entity, never entities themselves).
    # `modl sync` rejects a MODIFIED entity the ledger has no concept for, so every MODIFIED entity
    # must already exist in the previous snapshot, and every parent must be an entity of the report
    # or already authored.
    entity_labels = {ev["label"] for ev in changes if ev["kind"] == "ENTITY"}
    for ev in changes:
        if ev["kind"] in ("ENTITY", "PROPERTY"):
            assert ev["label"] in curr_model or ev["label"] in prev_model, f"non-authored label {ev['label']}"
            parent = ev.get("parent_label")
            assert parent is None or parent in entity_labels or parent in prev_model, (
                f"{ev['label']}: parent {parent} is neither an entity event nor already authored"
            )
        if ev["kind"] == "ENTITY" and ev["change_type"] == "MODIFIED":
            assert ev.get("renamed_from", ev["label"]) in prev_model, f"MODIFIED {ev['label']} has no prior concept"


def run(tmp_path: Path, prev_model: Model, curr_model: Model) -> dict[str, Any]:
    prev = write_snapshot(tmp_path, "prev", prev_model)
    curr = write_snapshot(tmp_path, "curr", curr_model)
    report = diff_folders(prev, curr)
    assert_report_consistent(report, prev_model, curr_model, tmp_path)
    return report


def entry_for(report: dict[str, Any], label: str) -> dict[str, Any]:
    matches = [e for e in report["property_paths"] if e["label"] == label]
    assert len(matches) == 1, f"expected one entry for {label}, got {len(matches)}"
    return matches[0]


def paths_of(entry: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    return {p["path"]: (p["change"], p["tags"]) for p in entry["paths"]}


ROOT: Model = {"Vehicle": branch()}


class TestImplicitBranchForm:
    """`Vehicle.Foo.Red.Extra` declares a leaf below an instance of `Vehicle.Foo` directly."""

    MODEL: Model = {
        "Vehicle": branch(),
        "Vehicle.Foo": branch(instances=["Red", "Green", "Blue"]),
        "Vehicle.Foo.Item": sensor(),
        "Vehicle.Foo.Total": sensor(instantiate=False),
        "Vehicle.Foo.Red.Extra": sensor(instantiate=False),
    }

    def test_extra_has_exactly_one_path_and_no_phantoms(self, tmp_path: Path):
        report = run(tmp_path, ROOT, self.MODEL)

        extra = paths_of(entry_for(report, "Vehicle.Foo.Red.Extra"))
        assert extra == {"Vehicle.Foo.Red.Extra": ("added", {"Vehicle.Foo": {"dimension1": "Red"}})}
        assert paths_of(entry_for(report, "Vehicle.Foo.Total")) == {"Vehicle.Foo.Total": ("added", {})}
        assert set(paths_of(entry_for(report, "Vehicle.Foo.Item"))) == {
            "Vehicle.Foo.Red.Item",
            "Vehicle.Foo.Green.Item",
            "Vehicle.Foo.Blue.Item",
        }
        all_paths = {p["path"] for e in report["property_paths"] for p in e["paths"]}
        assert "Vehicle.Foo.Green.Extra" not in all_paths
        assert "Vehicle.Foo.Blue.Extra" not in all_paths

    def test_removing_an_instance_removes_its_paths(self, tmp_path: Path):
        curr = {**self.MODEL, "Vehicle.Foo": branch(instances=["Green", "Blue"])}
        report = run(tmp_path, self.MODEL, curr)

        item = paths_of(entry_for(report, "Vehicle.Foo.Item"))
        assert item["Vehicle.Foo.Red.Item"][0] == "removed"
        assert item["Vehicle.Foo.Green.Item"][0] == "unchanged"


class TestInstanceChanges:
    def test_multi_dimension_gaining_value(self, tmp_path: Path):
        prev = {**ROOT, "Vehicle.Seat": branch(instances=["Row[1,2]", ["Left", "Right"]]), "Vehicle.Seat.Pos": sensor()}
        curr = {**prev, "Vehicle.Seat": branch(instances=["Row[1,3]", ["Left", "Right"]])}
        report = run(tmp_path, prev, curr)

        pos = paths_of(entry_for(report, "Vehicle.Seat.Pos"))
        assert pos["Vehicle.Seat.Row3.Left.Pos"] == (
            "added",
            {"Vehicle.Seat": {"dimension1": "Row3", "dimension2": "Left"}},
        )
        assert pos["Vehicle.Seat.Row1.Left.Pos"][0] == "unchanged"

    def test_nested_entities(self, tmp_path: Path):
        curr = {
            **ROOT,
            "Vehicle.Axle": branch(instances="Axle[1,2]"),
            "Vehicle.Axle.Wheel": branch(instances=["Left", "Right"]),
            "Vehicle.Axle.Wheel.Speed": sensor(),
        }
        report = run(tmp_path, ROOT, curr)

        speed = paths_of(entry_for(report, "Vehicle.Axle.Wheel.Speed"))
        assert speed["Vehicle.Axle.Axle2.Wheel.Right.Speed"] == (
            "added",
            {"Vehicle.Axle": {"dimension1": "Axle2"}, "Vehicle.Axle.Wheel": {"dimension1": "Right"}},
        )
        entity_labels = {c["label"] for c in report["changes"] if c["kind"] == "ENTITY" and c["change_type"] == "ADDED"}
        assert entity_labels == {"Vehicle.Axle", "Vehicle.Axle.Wheel"}

    def test_instantiate_flip(self, tmp_path: Path):
        prev = {**ROOT, "Vehicle.Zone": branch(instances=["Left", "Right"]), "Vehicle.Zone.Label": sensor()}
        curr = {**prev, "Vehicle.Zone.Label": sensor(instantiate=False)}
        report = run(tmp_path, prev, curr)

        label = paths_of(entry_for(report, "Vehicle.Zone.Label"))
        assert label["Vehicle.Zone.Label"] == ("added", {})
        assert label["Vehicle.Zone.Left.Label"][0] == "removed"
        assert label["Vehicle.Zone.Right.Label"][0] == "removed"

    def test_pure_ancestor_rename_is_unchanged(self, tmp_path: Path):
        prev = {**ROOT, "Vehicle.Door": branch(instances=["Left", "Right"]), "Vehicle.Door.IsOpen": sensor()}
        curr = {
            **ROOT,
            "Vehicle.Portal": branch(instances=["Left", "Right"], fka=["Vehicle.Door"]),
            "Vehicle.Portal.IsOpen": sensor(),
        }
        report = run(tmp_path, prev, curr)

        entry = paths_of(entry_for(report, "Vehicle.Portal.IsOpen"))
        assert entry == {
            "Vehicle.Portal.Left.IsOpen": ("unchanged", {"Vehicle.Portal": {"dimension1": "Left"}}),
            "Vehicle.Portal.Right.IsOpen": ("unchanged", {"Vehicle.Portal": {"dimension1": "Right"}}),
        }


class TestSiblingRelation:
    def test_sibling_instances_follow_the_tree(self, tmp_path: Path):
        curr = {
            **ROOT,
            "Vehicle.Door": branch(instances=["Left", "Right"], instances_relation="sibling"),
            "Vehicle.Door.IsOpen": sensor(),
        }
        report = run(tmp_path, ROOT, curr)

        entry = paths_of(entry_for(report, "Vehicle.Door.IsOpen"))
        assert len(entry) == 2
        for change, tags in entry.values():
            assert change == "added"
            assert set(tags) == {"Vehicle.Door"}


@pytest.mark.parametrize("instances", [["Left", "Right"], "Row[1,3]", ["Row[1,2]", ["A", "B"]]])
def test_first_run_paths_match_exporter(tmp_path: Path, instances: Any):
    model = {**ROOT, "Vehicle.X": branch(instances=instances), "Vehicle.X.Y": sensor()}
    curr = write_snapshot(tmp_path, "curr", model)
    report = diff_folders(None, curr)
    DiffReport.model_validate(report)

    reported = {p["path"] for e in report["property_paths"] for p in e["paths"]}
    assert reported == leaf_paths(export_nodes(tmp_path, "curr", model))
    assert all(p["change"] == "added" for e in report["property_paths"] for p in e["paths"])


class TestInstanceBranchesAreNotEvents:
    """Instance branches are an aspect of their entity: no event, parent or MODIFIED is fabricated for them."""

    BMW_SHAPE: Model = {
        **ROOT,
        "Vehicle.Config": branch(instances=["DefaultSettings", "DirectStartSettings"]),
        "Vehicle.Config.Seat": branch(instances=["Row[1,3]", ["DriverSide", "PassengerSide"]]),
        "Vehicle.Config.Seat.Heating": sensor(),
        "Vehicle.Axle": branch(instances="Axle[1,2]"),
        "Vehicle.Axle.Wheel": branch(instances=["Left", "Right", "Center"]),
        "Vehicle.Axle.Wheel.Speed": sensor(),
        "Vehicle.Axle.Weight": sensor(),
        "Vehicle.Foo": branch(instances=["Red", "Green"]),
        "Vehicle.Foo.Item": sensor(),
        "Vehicle.Foo.Red.Extra": sensor(instantiate=False),
    }

    def test_first_run_reports_only_authored_entities(self, tmp_path: Path):
        report = diff_folders(None, write_snapshot(tmp_path, "curr", self.BMW_SHAPE))
        DiffReport.model_validate(report)

        changes = report["changes"]
        assert not [c for c in changes if c["change_type"] == "MODIFIED"]
        entities = {c["label"] for c in changes if c["kind"] == "ENTITY"}
        assert entities == {
            "Vehicle",
            "Vehicle.Config",
            "Vehicle.Config.Seat",
            "Vehicle.Axle",
            "Vehicle.Axle.Wheel",
            "Vehicle.Foo",
        }
        for c in changes:
            if c["kind"] in ("ENTITY", "PROPERTY"):
                assert c["label"] in self.BMW_SHAPE
                assert c.get("parent_label") in entities | {None}

        extra = next(c for c in changes if c["label"] == "Vehicle.Foo.Red.Extra" and c["kind"] == "PROPERTY")
        assert extra["parent_label"] == "Vehicle.Foo"

    def test_later_run_has_only_previously_known_modified_entities(self, tmp_path: Path):
        curr = {**self.BMW_SHAPE, "Vehicle.Config.Seat.Cooling": sensor()}
        report = run(tmp_path, self.BMW_SHAPE, curr)

        assert [c for c in report["changes"] if c["change_type"] == "MODIFIED"] == [
            c for c in report["changes"] if c["kind"] == "ENTITY" and c["change_type"] == "MODIFIED"
        ]
        added = next(c for c in report["changes"] if c["label"] == "Vehicle.Config.Seat.Cooling")
        assert added["parent_label"] == "Vehicle.Config.Seat"

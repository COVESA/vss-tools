# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""`instantiate` must be a top-level PROPERTY field of the diff report, never an aspect."""

import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from vss_tools.diff import ADDED, ENUM_VALUE, MODIFIED, PROPERTY, REMOVED, diff_folders

BASE: dict[str, Any] = {
    "Cabin": {"type": "branch", "description": "Cabin."},
    "Cabin.Zone": {"type": "branch", "description": "Zone.", "instances": ["Left", "Right", "Center"]},
    "Cabin.Zone.Temperature": {"type": "sensor", "datatype": "float", "description": "Temp."},
    "Cabin.Zone.Label": {"type": "sensor", "datatype": "string", "description": "Label.", "instantiate": False},
}


def snapshot(root: Path, name: str, model: dict[str, Any], units: dict[str, Any] | None = None) -> Path:
    folder = root / name
    folder.mkdir()
    (folder / "model.vspec").write_text(yaml.safe_dump(model), encoding="utf-8")
    if units is not None:
        (folder / "units.yaml").write_text(yaml.safe_dump(units), encoding="utf-8")
    return folder


def with_label(**overrides: Any) -> dict[str, Any]:
    """BASE with `Cabin.Zone.Label` attributes overridden; a value of None drops the key."""
    model = {k: dict(v) for k, v in BASE.items()}
    for key, value in overrides.items():
        if value is None:
            model["Cabin.Zone.Label"].pop(key, None)
        else:
            model["Cabin.Zone.Label"][key] = value
    return model


def prop(result: dict[str, Any], label: str) -> dict[str, Any]:
    matches = [c for c in result["changes"] if c["kind"] == PROPERTY and c["label"] == label]
    assert len(matches) == 1, f"expected exactly one PROPERTY event for {label}, got {len(matches)}"
    return matches[0]


def contract_violations(report: dict[str, Any]) -> list[str]:
    """Minimal local mirror of modl's PropertyChanged rules for `instantiate`."""
    problems = []
    for c in report["changes"]:
        for key in ("aspects", "previous_aspects"):
            if "instantiate" in c.get(key, {}):
                problems.append(f"{c['label']}: 'instantiate' found in {key}")
        if c["kind"] != PROPERTY and c.get("instantiate") is not None:
            problems.append(f"{c['label']}: 'instantiate' on {c['kind']}")
        if c.get("instantiate") is not None and not isinstance(c["instantiate"], bool):
            problems.append(f"{c['label']}: 'instantiate' is not a boolean")
    return problems


class TestFreshDiff:
    @pytest.fixture(scope="class")
    def result(self, tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
        root = tmp_path_factory.mktemp("fresh")
        return diff_folders(None, snapshot(root, "cur", BASE))

    def test_label_is_top_level_false_and_not_an_aspect(self, result: dict[str, Any]):
        label = prop(result, "Cabin.Zone.Label")
        assert label["change_type"] == ADDED
        assert label["instantiate"] is False
        assert "instantiate" not in label["aspects"]

    def test_label_is_a_sibling_of_structural_fields(self, result: dict[str, Any]):
        label = prop(result, "Cabin.Zone.Label")
        assert {"label", "parent_label", "kind", "is_leaf", "instantiate"} <= set(label)
        # the uninstantiated path, parented on the instanced branch itself
        assert label["label"] == "Cabin.Zone.Label"
        assert label["parent_label"] == "Cabin.Zone"

    def test_instantiated_sibling_has_no_instantiate(self, result: dict[str, Any]):
        assert prop(result, "Cabin.Zone.Temperature").get("instantiate") is None

    def test_mixed_siblings_in_one_report(self, result: dict[str, Any]):
        labels = {c["label"] for c in result["changes"] if c["kind"] == PROPERTY}
        assert {"Cabin.Zone.Label", "Cabin.Zone.Temperature"} <= labels

    def test_no_instance_qualified_leaves(self, result: dict[str, Any]):
        labels = {c["label"] for c in result["changes"]}
        assert not any(label.startswith(("Cabin.Zone.Left.", "Cabin.Zone.Right.")) for label in labels)

    def test_contract(self, result: dict[str, Any]):
        assert contract_violations(result) == []


class TestFlip:
    def test_true_to_false(self, tmp_path: Path):
        prev = snapshot(tmp_path, "prev", with_label(instantiate=None))
        cur = snapshot(tmp_path, "cur", with_label(instantiate=False))
        result = diff_folders(prev, cur)
        label = prop(result, "Cabin.Zone.Label")
        assert label["change_type"] == MODIFIED
        assert label["instantiate"] is False
        assert label["aspects"] == {}
        assert contract_violations(result) == []

    def test_false_to_true(self, tmp_path: Path):
        prev = snapshot(tmp_path, "prev", with_label(instantiate=False))
        cur = snapshot(tmp_path, "cur", with_label(instantiate=None))
        label = prop(diff_folders(prev, cur), "Cabin.Zone.Label")
        assert label["change_type"] == MODIFIED
        assert label["instantiate"] is True
        assert label["aspects"] == {}

    def test_absent_to_explicit_true_is_not_a_change(self, tmp_path: Path):
        prev = snapshot(tmp_path, "prev", with_label(instantiate=None))
        cur = snapshot(tmp_path, "cur", with_label(instantiate=True))
        result = diff_folders(prev, cur)
        assert not [c for c in result["changes"] if c["kind"] == PROPERTY]

    def test_flip_with_other_change_keeps_both(self, tmp_path: Path):
        prev = snapshot(tmp_path, "prev", with_label(instantiate=None))
        cur = snapshot(tmp_path, "cur", with_label(instantiate=False, description="New."))
        label = prop(diff_folders(prev, cur), "Cabin.Zone.Label")
        assert label["instantiate"] is False
        assert set(label["aspects"]) == {"description"}


class TestModifiedAlwaysCarriesCurrentValue:
    def test_unrelated_change_on_non_instantiated_leaf(self, tmp_path: Path):
        prev = snapshot(tmp_path, "prev", with_label())
        cur = snapshot(tmp_path, "cur", with_label(description="Changed."))
        label = prop(diff_folders(prev, cur), "Cabin.Zone.Label")
        assert label["change_type"] == MODIFIED
        assert label["instantiate"] is False
        assert set(label["aspects"]) == {"description"}

    def test_unrelated_change_on_instantiated_leaf(self, tmp_path: Path):
        model = {k: dict(v) for k, v in BASE.items()}
        model["Cabin.Zone.Temperature"]["description"] = "Changed."
        prev = snapshot(tmp_path, "prev", BASE)
        cur = snapshot(tmp_path, "cur", model)
        result = diff_folders(prev, cur)
        temperature = prop(result, "Cabin.Zone.Temperature")
        assert temperature["change_type"] == MODIFIED
        assert temperature["instantiate"] is True
        assert contract_violations(result) == []

    def test_rename_carries_current_value(self, tmp_path: Path):
        renamed = {k: dict(v) for k, v in BASE.items() if k != "Cabin.Zone.Label"}
        renamed["Cabin.Zone.Tag"] = {**BASE["Cabin.Zone.Label"], "fka": ["Cabin.Zone.Label"]}
        prev = snapshot(tmp_path, "prev", BASE)
        cur = snapshot(tmp_path, "cur", renamed)
        tag = prop(diff_folders(prev, cur), "Cabin.Zone.Tag")
        assert tag["renamed_from"] == "Cabin.Zone.Label"
        assert tag["instantiate"] is False
        assert "instantiate" not in tag["aspects"]


class TestRemoved:
    def test_removed_label(self, tmp_path: Path):
        model = {k: dict(v) for k, v in BASE.items() if k != "Cabin.Zone.Label"}
        prev = snapshot(tmp_path, "prev", BASE)
        cur = snapshot(tmp_path, "cur", model)
        result = diff_folders(prev, cur)
        label = prop(result, "Cabin.Zone.Label")
        assert label["change_type"] == REMOVED
        assert label["instantiate"] is False
        assert "instantiate" not in label["previous_aspects"]
        assert label["previous_aspects"]  # still a non-empty snapshot
        assert contract_violations(result) == []


class TestEnumValue:
    def test_enum_value_never_carries_instantiate(self, tmp_path: Path):
        units = {"kg": {"definition": "mass", "quantity": "mass", "unit": "kg"}}
        quantities = {"mass": {"definition": "mass"}}
        cur = snapshot(tmp_path, "cur", BASE, units)
        (cur / "quantities.yaml").write_text(yaml.safe_dump(quantities), encoding="utf-8")
        result = diff_folders(None, cur)
        enum_values = [c for c in result["changes"] if c["kind"] == ENUM_VALUE]
        assert enum_values
        assert all("instantiate" not in c for c in enum_values)
        assert contract_violations(result) == []


class TestNestedCase:
    """
    vspec only honours `instantiate: false` on DIRECT children of the instanced branch
    (tree.expand_instances); two levels down it is a no-op and the leaf is instantiated.
    The producer reports it faithfully and does not work around it.
    """

    NESTED: dict[str, Any] = {
        **BASE,
        "Cabin.Zone.Sub": {"type": "branch", "description": "Sub."},
        "Cabin.Zone.Sub.Nested": {"type": "sensor", "datatype": "string", "description": "N.", "instantiate": False},
    }

    def test_nested_leaf_is_reported_as_authored(self, tmp_path: Path):
        result = diff_folders(None, snapshot(tmp_path, "cur", self.NESTED))
        nested = prop(result, "Cabin.Zone.Sub.Nested")
        assert nested["instantiate"] is False
        assert nested["parent_label"] == "Cabin.Zone.Sub"

    def test_intermediate_branch_has_no_instances_of_its_own(self, tmp_path: Path):
        # Documents the gap: modl resolves instances from the direct parent only, and
        # `Cabin.Zone.Sub` declares none, so modl cannot see the Zone instances from here.
        result = diff_folders(None, snapshot(tmp_path, "cur", self.NESTED))
        sub = next(c for c in result["changes"] if c["kind"] == "ENTITY" and c["label"] == "Cabin.Zone.Sub")
        assert "instances" not in sub["aspects"]


class TestModlSchema:
    """Validate against modl's own DiffReport model when its source is available."""

    @pytest.fixture(scope="class")
    def diff_report(self):
        pytest.importorskip("pydantic")
        modl_src = Path(__file__).resolve().parents[4] / "cloned-modl" / "src"
        if modl_src.exists() and str(modl_src) not in sys.path:
            sys.path.append(str(modl_src))
        ir = pytest.importorskip("modl.ir")
        return ir.DiffReport

    def test_report_validates(self, diff_report: Any, tmp_path: Path):
        prev = snapshot(tmp_path, "prev", with_label(instantiate=None))
        cur = snapshot(tmp_path, "cur", with_label(instantiate=False))
        for report in (diff_folders(None, cur), diff_folders(prev, cur)):
            parsed = diff_report.model_validate_json(json.dumps(report))
            flagged = [c for c in parsed.changes if c.label == "Cabin.Zone.Label" and c.kind == PROPERTY]
            assert flagged and all(c.instantiate is False for c in flagged)

    def test_aspects_instantiate_is_detected(self):
        bad = {"changes": [{"label": "A.X", "parent_label": "A", "kind": PROPERTY, "change_type": ADDED,
                            "is_leaf": True, "aspects": {"instantiate": False}}]}  # fmt: skip
        assert contract_violations(bad) == ["A.X: 'instantiate' found in aspects"]

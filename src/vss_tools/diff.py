# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""
Pure diff logic for vspec compose snapshot folders.

Compares two snapshot folders produced by `vspec compose` and returns a
structured list of ADDED, REMOVED, and MODIFIED change events covering:
  - model      (model_snapshot.vspec)
  - structs    (structs_snapshot.vspec)
  - units      (units_snapshot.yaml)
  - quantities (quantities_snapshot.yaml)

No vss-tools tree parsing is performed — snapshots are already flat dicts.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

import yaml

from vss_tools import log
from vss_tools.compose import (
    MODEL_SNAPSHOT_FILENAME,
    QUANTITIES_SNAPSHOT_FILENAME,
    STRUCTS_SNAPSHOT_FILENAME,
    UNITS_SNAPSHOT_FILENAME,
)
from vss_tools.tree import expand_string

# ---------------------------------------------------------------------------
# Change type constants
# ---------------------------------------------------------------------------
ADDED = "ADDED"
REMOVED = "REMOVED"
MODIFIED = "MODIFIED"

# ---------------------------------------------------------------------------
# modl IR kind constants
# ---------------------------------------------------------------------------
ENTITY = "ENTITY"
PROPERTY = "PROPERTY"
ENUMERATION_SET = "ENUMERATION_SET"
ENUM_VALUE = "ENUM_VALUE"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_flat_yaml(path: Path) -> dict[str, Any]:
    """Load a flat snapshot YAML file. Returns empty dict when file is absent."""
    if not path.exists():
        return {}
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    return content if isinstance(content, dict) else {}


def _node_type(attrs: dict[str, Any]) -> str:
    """Extract the VSS node type label from an attribute dict."""
    return str(attrs.get("type", "unknown"))


def _field_diff(prev_attrs: dict[str, Any], curr_attrs: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return a list of per-attribute change dicts for fields that differ.
    Includes fields that appeared or disappeared (previous/current = None).
    """
    all_keys = set(prev_attrs) | set(curr_attrs)
    changes = []
    for k in sorted(all_keys):
        pv = prev_attrs.get(k)
        cv = curr_attrs.get(k)
        if pv != cv:
            changes.append({"attribute": k, "previous": pv, "current": cv})
    return changes


# ---------------------------------------------------------------------------
# modl IR translation helpers
# ---------------------------------------------------------------------------


def _vss_kind(node_type: str, source: str) -> str:
    """Map a VSS node type + source to a modl IR element kind."""
    if source == "quantities":
        return ENUMERATION_SET
    if source == "units":
        return ENUM_VALUE
    # model or structs
    if node_type in ("branch", "struct"):
        return ENTITY
    return PROPERTY


def _extract_datatype(value: str | None) -> tuple[str | None, bool]:
    """Split a VSS datatype string into base type and is_list flag."""
    if value is None:
        return None, False
    if value.endswith("[]"):
        return value[:-2], True
    return value, False


def _expand_instances(value: Any) -> list[str]:
    """
    Expand a VSS instances value into fully-qualified instance path labels.

    Each top-level list item is one dimension; the result is the Cartesian
    product of all dimensions joined with '.'.  Examples:

      "Row[1,4]"                                    → ["Row1","Row2","Row3","Row4"]
      ["Left", "Right"]                             → ["Left", "Right"]
      ["Row[1,2]", ["DriverSide","PassengerSide"]]  → ["Row1.DriverSide",
                                                         "Row1.PassengerSide",
                                                         "Row2.DriverSide",
                                                         "Row2.PassengerSide"]
    """
    if value is None:
        return []
    if isinstance(value, str):
        return expand_string(value)
    if not isinstance(value, list):
        return [str(value)]

    # If every item is a plain string with no range syntax the whole list is
    # a single dimension (e.g. ["Left", "Right"]).
    if all(isinstance(item, str) and "[" not in item for item in value):
        return [str(item) for item in value]

    # Otherwise each item is its own dimension; compute Cartesian product.
    dimensions: list[list[str]] = []
    for item in value:
        if isinstance(item, list):
            dimensions.append([str(x) for x in item])
        elif isinstance(item, str) and "[" in item:
            dimensions.append(expand_string(item))
        else:
            dimensions.append([str(item)])

    if not dimensions:
        return []
    return [".".join(combo) for combo in itertools.product(*dimensions)]


def _map_aspects_added(attrs: dict[str, Any], source: str, node_type: str) -> dict[str, Any]:
    """Build the full aspects snapshot for an ADDED event."""
    aspects = {k: v for k, v in attrs.items() if k not in ("fka", "quantity")}
    kind = _vss_kind(node_type, source)
    if kind == PROPERTY:
        raw_dt = aspects.pop("datatype", None)
        output_type, is_list = _extract_datatype(raw_dt)
        if output_type is not None:
            aspects["output_type"] = output_type
            aspects["is_list"] = is_list
        aspects.setdefault("is_required", False)
    elif kind == ENTITY:
        if "instances" in aspects:
            aspects["instances"] = _expand_instances(aspects["instances"])
    elif kind == ENUM_VALUE:
        # rename the 'unit' display-name key to 'symbol'
        if "unit" in aspects:
            aspects["symbol"] = aspects.pop("unit")
    return aspects


def _map_aspects_delta(attribute_changes: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the changed-keys-only aspects dict for a MODIFIED event."""
    delta: dict[str, Any] = {}
    for ac in attribute_changes:
        attr, current = ac["attribute"], ac["current"]
        if attr == "fka":
            continue
        if attr == "datatype":
            output_type, is_list = _extract_datatype(current)
            if output_type is not None:
                delta["output_type"] = output_type
                delta["is_list"] = is_list
        elif attr == "instances":
            delta["instances"] = _expand_instances(current)
        else:
            delta[attr] = current
    return delta


def _parent_label(path: str, source: str, attrs: dict[str, Any]) -> str | None:
    """Derive the modl parent_label for an event."""
    if source == "quantities":
        return None
    if source == "units":
        qty = attrs.get("quantity")
        if not qty:
            log.warning(f"Unit '{path}' has no quantity — skipping parent_label assignment")
            return None
        return str(qty)
    # model or structs: parent is the FQN prefix
    if "." in path:
        return path.rsplit(".", 1)[0]
    return None


def _to_modl_events(raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Translate internal diff events to the modl adapter IR format."""
    result = []
    for ev in raw_events:
        source = ev["source"]
        node_type = ev["node_type"]
        path = ev["path"]
        change_type = ev["type"]
        attrs = ev.get("attributes") or {}

        kind = _vss_kind(node_type, source)
        parent = _parent_label(path, source, attrs)

        event: dict[str, Any] = {
            "label": path,
            "kind": kind,
            "change_type": change_type,
        }
        if parent is not None:
            event["parent_label"] = parent

        if change_type == ADDED:
            event["aspects"] = _map_aspects_added(attrs, source, node_type)
        elif change_type == REMOVED:
            pass  # modl: REMOVED must carry no aspects
        else:  # MODIFIED
            if ev.get("previous_path"):
                event["renamed_from"] = ev["previous_path"]
            event["aspects"] = _map_aspects_delta(ev.get("attribute_changes") or [])

        result.append(event)
    return result


def _inject_entity_content(modl_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Ensure every ENTITY/ENUMERATION_SET has a MODIFIED event with a content list
    summarising which children changed, when those children are ADDED/REMOVED/MODIFIED
    but the parent itself was not independently changed.
    """
    entity_kinds = {ENTITY, ENUMERATION_SET}
    child_kinds = {PROPERTY, ENUM_VALUE}

    # Track which entity labels were fully ADDED or REMOVED (no content injection needed)
    entity_added_removed: set[str] = set()
    # Map entity label → index in the working list for already-present MODIFIED entities
    entity_modified: dict[str, int] = {}

    events = list(modl_events)

    for i, ev in enumerate(events):
        if ev["kind"] in entity_kinds:
            if ev["change_type"] in (ADDED, REMOVED):
                entity_added_removed.add(ev["label"])
            elif ev["change_type"] == MODIFIED:
                entity_modified[ev["label"]] = i

    for ev in modl_events:
        if ev["kind"] not in child_kinds:
            continue
        parent = ev.get("parent_label")
        if parent is None or parent in entity_added_removed:
            continue

        content_item = {"label": ev["label"], "change_type": ev["change_type"]}

        if parent in entity_modified:
            events[entity_modified[parent]].setdefault("content", []).append(content_item)
        else:
            new_entity_event: dict[str, Any] = {
                "label": parent,
                "kind": ENTITY,
                "change_type": MODIFIED,
                "aspects": {},
                "content": [content_item],
            }
            entity_modified[parent] = len(events)
            events.append(new_entity_event)

    return events


# ---------------------------------------------------------------------------
# Core diff
# ---------------------------------------------------------------------------


def _diff_dicts(
    previous: dict[str, Any],
    current: dict[str, Any],
    source: str,
    detect_renames: bool = True,
) -> list[dict[str, Any]]:
    """
    Compute the full diff between two flat dicts.

    When detect_renames=True (model/structs) rename detection runs:
      1. Explicit: added node has fka entry matching a removed path AND node_type matches.
      2. Cascade:  confirmed parent renames propagate to children by FQN prefix substitution;
                   each cascaded child is independently checked for attribute changes too.
    """
    prev_keys = set(previous)
    curr_keys = set(current)

    raw_added = {k: current[k] for k in curr_keys - prev_keys}
    raw_removed = {k: previous[k] for k in prev_keys - curr_keys}

    events: list[dict[str, Any]] = []

    # --- rename detection ---
    consumed_added: set[str] = set()
    consumed_removed: set[str] = set()
    confirmed_renames: list[tuple[str, str]] = []  # (old_prefix, new_prefix)

    if detect_renames:
        # Pass 1 — explicit fka
        for new_path, new_attrs in raw_added.items():
            fka: list[str] = new_attrs.get("fka") or []
            if isinstance(fka, str):
                fka = [fka]
            new_nt = _node_type(new_attrs)
            for old_path in fka:
                if old_path in raw_removed and old_path not in consumed_removed:
                    old_attrs = raw_removed[old_path]
                    # node_type must match to confirm rename (not just any fka hit)
                    if _node_type(old_attrs) != new_nt:
                        continue
                    attr_changes = _field_diff(old_attrs, new_attrs)
                    # Remove fka from attribute_changes — it's expected to differ
                    attr_changes = [c for c in attr_changes if c["attribute"] != "fka"]
                    events.append(
                        {
                            "type": MODIFIED,
                            "source": source,
                            "path": new_path,
                            "previous_path": old_path,
                            "node_type": new_nt,
                            "cascade": False,
                            "attribute_changes": attr_changes,
                        }
                    )
                    consumed_added.add(new_path)
                    consumed_removed.add(old_path)
                    confirmed_renames.append((old_path, new_path))
                    break

        # Pass 2 — cascade: children whose FQN prefix changed due to a confirmed parent rename
        for old_prefix, new_prefix in confirmed_renames:
            old_child_prefix = old_prefix + "."
            new_child_prefix = new_prefix + "."

            for new_path, new_attrs in raw_added.items():
                if new_path in consumed_added:
                    continue
                if not new_path.startswith(new_child_prefix):
                    continue
                # Reconstruct the expected old path
                old_path = old_child_prefix + new_path[len(new_child_prefix) :]
                if old_path not in raw_removed or old_path in consumed_removed:
                    continue
                old_attrs = raw_removed[old_path]
                if _node_type(old_attrs) != _node_type(new_attrs):
                    continue
                attr_changes = _field_diff(old_attrs, new_attrs)
                new_nt = _node_type(new_attrs)
                events.append(
                    {
                        "type": MODIFIED,
                        "source": source,
                        "path": new_path,
                        "previous_path": old_path,
                        "node_type": new_nt,
                        "cascade": True,
                        "attribute_changes": attr_changes,
                    }
                )
                consumed_added.add(new_path)
                consumed_removed.add(old_path)

    # --- plain ADDED ---
    for path, attrs in sorted(raw_added.items()):
        if path in consumed_added:
            continue
        nt = _node_type(attrs)
        events.append(
            {
                "type": ADDED,
                "source": source,
                "path": path,
                "node_type": nt,
                "attributes": attrs,
            }
        )

    # --- plain REMOVED ---
    for path, attrs in sorted(raw_removed.items()):
        if path in consumed_removed:
            continue
        nt = _node_type(attrs)
        events.append(
            {
                "type": REMOVED,
                "source": source,
                "path": path,
                "node_type": nt,
                "attributes": attrs,
            }
        )

    # --- MODIFIED (attribute changes on nodes present in both) ---
    for path in sorted(prev_keys & curr_keys):
        attr_changes = _field_diff(previous[path], current[path])
        if not attr_changes:
            continue
        nt = _node_type(current[path])
        events.append(
            {
                "type": MODIFIED,
                "source": source,
                "path": path,
                "node_type": nt,
                "attribute_changes": attr_changes,
            }
        )

    return events


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def diff_folders(previous_dir: Path | None, current_dir: Path) -> dict[str, Any]:
    """
    Diff two compose snapshot folders and return a modl-compatible diff report.

    Returns a dict with:
      previous, current  — folder paths as strings
      changes            — ordered list of modl IR change events

    When previous_dir is None (first-run mode), every element in current_dir
    is treated as ADDED and emitted with its complete aspects snapshot.
    """
    raw_changes: list[dict[str, Any]] = []

    sources = [
        (MODEL_SNAPSHOT_FILENAME, "model", True),
        (STRUCTS_SNAPSHOT_FILENAME, "structs", True),
        (UNITS_SNAPSHOT_FILENAME, "units", False),
        (QUANTITIES_SNAPSHOT_FILENAME, "quantities", False),
    ]

    for filename, source_label, detect_renames in sources:
        prev = load_flat_yaml(previous_dir / filename) if previous_dir else {}
        curr = load_flat_yaml(current_dir / filename)
        if not prev and not curr:
            continue
        raw_changes.extend(_diff_dicts(prev, curr, source_label, detect_renames=detect_renames))

    modl_events = _to_modl_events(raw_changes)
    modl_events = _inject_entity_content(modl_events)

    _KIND_ORDER = {ENTITY: 0, ENUMERATION_SET: 1, PROPERTY: 2, ENUM_VALUE: 3}
    modl_events.sort(key=lambda e: _KIND_ORDER.get(e["kind"], 99))

    return {
        "previous": str(previous_dir) if previous_dir else None,
        "current": str(current_dir),
        "changes": modl_events,
    }

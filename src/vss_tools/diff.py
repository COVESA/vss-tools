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
from vss_tools.datatypes import Datatypes
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


def load_snapshot_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file. Returns an empty dict when the file is absent."""
    if not path.exists():
        return {}
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    return content if isinstance(content, dict) else {}


def _node_type(attrs: dict[str, Any]) -> str:
    """Extract the VSS node type label from an attribute dict."""
    return str(attrs.get("type", "unknown"))


def _effective_instantiate(attrs: dict[str, Any]) -> bool:
    """Indicates whether the property is expanded per parent instance (anything but an explicit `false`)."""
    return attrs.get("instantiate") is not False


def _field_diff(prev_attrs: dict[str, Any], curr_attrs: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return a list of per-attribute change dicts for fields that differ.
    Includes fields that appeared or disappeared (previous/current = None).

    `instantiate` is compared by its effective outcome, so an absent value and an explicit
    `true` are not a change.
    """
    all_keys = set(prev_attrs) | set(curr_attrs)
    changes = []
    for k in sorted(all_keys):
        pv = prev_attrs.get(k)
        cv = curr_attrs.get(k)
        if k == "instantiate":
            if _effective_instantiate(prev_attrs) != _effective_instantiate(curr_attrs):
                changes.append({"attribute": k, "previous": pv, "current": cv})
            continue
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


def _instance_dimensions(instances_value: Any) -> list[list[str]]:
    """
    Split a VSS `instances` value into its individual dimensions, each a list of
    concrete instance values — without computing their Cartesian product.

      "Row[1,4]"                                    → [["Row1","Row2","Row3","Row4"]]
      ["Left", "Right"]                             → [["Left", "Right"]]
      ["Row[1,2]", ["DriverSide","PassengerSide"]]  → [["Row1","Row2"],
                                                         ["DriverSide","PassengerSide"]]
    """
    if not instances_value:
        return []
    if isinstance(instances_value, str):
        return [expand_string(instances_value)]
    if not isinstance(instances_value, list):
        return [[str(instances_value)]]

    # If every item is a plain string with no range syntax the whole list is
    # a single dimension (e.g. ["Left", "Right"]).
    if all(isinstance(item, str) and "[" not in item for item in instances_value):
        return [[str(item) for item in instances_value]]

    # Otherwise each item is its own dimension.
    dimensions: list[list[str]] = []
    for item in instances_value:
        if isinstance(item, list):
            dimensions.append([str(x) for x in item])
        elif isinstance(item, str) and "[" in item:
            dimensions.append(expand_string(item))
        else:
            dimensions.append([str(item)])
    return dimensions


def _expand_instances(value: Any) -> dict[str, list[str]]:
    """
    Expand a VSS `instances` value into modl's dimension-map form: one entry per
    dimension, positionally named `dimension1`, `dimension2`, ... (no Cartesian join).

      "Row[1,4]"                                    → {"dimension1": ["Row1","Row2","Row3","Row4"]}
      ["Left", "Right"]                             → {"dimension1": ["Left", "Right"]}
      ["Row[1,2]", ["DriverSide","PassengerSide"]]  → {"dimension1": ["Row1","Row2"],
                                                         "dimension2": ["DriverSide","PassengerSide"]}
    """
    dimensions = _instance_dimensions(value)
    return {f"dimension{i + 1}": values for i, values in enumerate(dimensions)}


def _expand_instance_fqns(base_fqn: str, instances_value: Any) -> list[str]:
    """
    Expand a branch's instances into all branch FQN paths produced by expansion,
    mirroring expand_instance() in tree.py — including every intermediate dimension hop.

    Each top-level entry in instances_value is one dimension, iterated exactly as
    expand_instances() iterates ``for instance in node.data.instances``.
    Roots advance (next dimension attaches to generated nodes) when the dimension
    entry is a list or expands to more than one name — matching the tree.py rule:
      ``len(names) > 1 or isinstance(instance, list) → return nodes, nodes``.
    """
    if not instances_value:
        return []

    # Normalise: if instances_value itself is not a list, wrap it so we can
    # iterate uniformly (mirrors tree.py where data.instances is always iterable).
    raw_dimensions: list[Any] = instances_value if isinstance(instances_value, list) else [instances_value]

    roots: list[str] = [base_fqn]
    all_created: list[str] = []

    for dimension in raw_dimensions:
        if isinstance(dimension, list):
            # Inner list: each element is an explicit name (possibly range syntax)
            names: list[str] = []
            for item in dimension:
                s = str(item)
                names.extend(expand_string(s) if "[" in s else [s])
            advance = True  # isinstance(instance, list) → return nodes, nodes
        elif isinstance(dimension, str) and "[" in dimension:
            names = expand_string(dimension)
            advance = len(names) > 1  # range expansion → return nodes, nodes
        else:
            names = [str(dimension)]
            advance = False  # single plain string → return roots, nodes

        new_nodes: list[str] = []
        for root in roots:
            for name in names:
                fqn = f"{root}.{name}"
                all_created.append(fqn)
                new_nodes.append(fqn)

        if advance:
            roots = new_nodes

    return all_created


def _inject_instance_expansions(raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    For every ENTITY ADDED or REMOVED event that carries an ``instances`` attribute,
    inject ADDED or REMOVED events for all branch FQNs produced by instance expansion.

    This mirrors the YAML exporter's behaviour: instances expand into concrete branch
    hops (one per dimension level), so those branches must appear in the diff just as
    they would appear in any expanded output.  Without these synthetic events,
    ``_inject_entity_content`` has no parent to anchor children to and creates phantom
    ENTITY MODIFIED events instead.
    """
    result: list[dict[str, Any]] = []
    for ev in raw_events:
        result.append(ev)
        if ev["type"] not in (ADDED, REMOVED):
            continue
        if _vss_kind(ev["node_type"], ev["source"]) != ENTITY:
            continue
        attrs = ev.get("attributes") or {}
        instances_value = attrs.get("instances")
        if not instances_value:
            continue

        description = attrs.get("description", "")
        for fqn in _expand_instance_fqns(ev["path"], instances_value):
            result.append(
                {
                    "type": ev["type"],
                    "source": ev["source"],
                    "path": fqn,
                    "node_type": "branch",
                    "attributes": {
                        "type": "branch",
                        "description": description,
                    },
                }
            )
    return result


def _map_full_aspects(attrs: dict[str, Any], source: str, node_type: str) -> dict[str, Any]:
    """
    Build a full aspects snapshot.

    Used both for an ADDED event's `aspects` and a REMOVED event's `previous_aspects`
    (the modl IR requires the latter to carry the full prior-state snapshot).

    `instantiate` is excluded: it has no representation at all in modl's IR — it only
    gates how vss-tools resolves literal runtime paths internally (see
    `_effective_instantiate`/`_direct_path_occurrences`).
    """
    aspects = {k: v for k, v in attrs.items() if k not in ("fka", "quantity", "name", "instantiate")}
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


def _datatype_is_leaf(raw_datatype: str | None) -> bool:
    """
    Whether a raw VSS `datatype` string resolves to a primitive/scalar (a leaf,
    binding-eligible) rather than another entity (a struct reference).

    Missing/None datatype defensively defaults to True (shouldn't occur for valid VSS
    signals). Array datatypes (`"Foo[]"`) are checked on their base type.
    """
    base_type, _ = _extract_datatype(raw_datatype)
    if base_type is None:
        return True
    return Datatypes.get_type(base_type) is not None


def _is_leaf(attrs: dict[str, Any]) -> bool:
    """Whether a PROPERTY event's `datatype` attribute resolves to a primitive/scalar."""
    return _datatype_is_leaf(attrs.get("datatype"))


def _references_delta(attribute_changes: list[dict[str, Any]], current_is_leaf: bool) -> dict[str, Any] | None:
    """
    Compute the `references` field for a MODIFIED PROPERTY event's `output_type` role.

    Returns `None` when `datatype` didn't change — omit the field entirely, keeping modl's
    stored edge. Returns `{}` when the property dropped a struct reference in favour of a
    primitive. Returns the full `{"output_type": <label>}` map when the property now points
    at a struct — whether newly (added) or retargeted (a different struct than before).
    """
    datatype_change = next((c for c in attribute_changes if c["attribute"] == "datatype"), None)
    if datatype_change is None:
        return None
    if not current_is_leaf:
        current_base, _ = _extract_datatype(datatype_change["current"])
        return {"output_type": current_base}
    if not _datatype_is_leaf(datatype_change["previous"]):
        return {}
    return None


def _wrap_op(previous: Any, current: Any) -> dict[str, Any]:
    """
    Wrap a single changed aspect value with its modl `_op` annotation.

    `_op` is "added" when there was no previous value, "removed" when there is no
    current value, and "modified" otherwise — each variant carries only the fields
    the modl IR requires for that operation.
    """
    if previous is None and current is not None:
        return {"_op": "added", "_value": current}
    if previous is not None and current is None:
        return {"_op": "removed", "_previous": previous}
    return {"_op": "modified", "_value": current, "_previous": previous}


def _map_aspects_delta(attribute_changes: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Build the changed-keys-only aspects dict for a MODIFIED event.

    Every key is wrapped with its `_op` annotation via `_wrap_op`, except the
    directional instance dimension-map keys `instances_added`/`instances_removed`, which
    the modl IR requires to stay as plain, unwrapped dimension maps.
    """
    delta: dict[str, Any] = {}
    for ac in attribute_changes:
        attr, previous, current = ac["attribute"], ac["previous"], ac["current"]
        if attr in ("fka", "name", "instantiate"):
            continue
        if attr == "datatype":
            prev_type, prev_is_list = _extract_datatype(previous)
            curr_type, curr_is_list = _extract_datatype(current)
            if prev_type != curr_type:
                delta["output_type"] = _wrap_op(prev_type, curr_type)
            if prev_is_list != curr_is_list:
                delta["is_list"] = _wrap_op(prev_is_list, curr_is_list)
        elif attr == "instances":
            added, removed = _instances_dimension_delta(previous, current)
            if added:
                delta["instances_added"] = added
            if removed:
                delta["instances_removed"] = removed
        else:
            delta[attr] = _wrap_op(previous, current)
    return delta


def _instances_dimension_delta(previous: Any, current: Any) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """
    Diff two VSS `instances` values per-dimension (by positional dimension name),
    returning `(added, removed)` dimension maps suitable for modl's
    `instances_added`/`instances_removed` aspects.

    A dimension that only exists on one side reports all of its values as added or
    removed; a dimension present on both sides reports only the values that changed.
    """
    prev_map = _expand_instances(previous)
    curr_map = _expand_instances(current)
    added: dict[str, list[str]] = {}
    removed: dict[str, list[str]] = {}
    for dim in sorted(set(prev_map) | set(curr_map)):
        pv = prev_map.get(dim, [])
        cv = curr_map.get(dim, [])
        add_vals = [v for v in cv if v not in pv]
        rem_vals = [v for v in pv if v not in cv]
        if add_vals:
            added[dim] = add_vals
        if rem_vals:
            removed[dim] = rem_vals
    return added, removed


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


def _build_primary_event(ev: dict[str, Any]) -> dict[str, Any]:
    """Build the primary modl event for a raw diff event (ENTITY/PROPERTY/vocabulary as mapped by `_vss_kind`)."""
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
    if kind == PROPERTY:
        is_leaf = _is_leaf(attrs)
        event["is_leaf"] = is_leaf
        # A non-leaf PROPERTY's datatype always resolves to a struct (vspec datatypes
        # are either primitives or struct FQNs — never branches), so the struct value
        # itself is read/written as one atomic unit and is eligible for its own binding,
        # on top of the bindings already minted for each of its child properties.
        if not is_leaf:
            event["binding_eligible"] = True

    if change_type == ADDED:
        event["aspects"] = _map_full_aspects(attrs, source, node_type)
        if kind == PROPERTY and not is_leaf:
            output_type = event["aspects"].get("output_type")
            if output_type is not None:
                event["references"] = {"output_type": output_type}
    elif change_type == REMOVED:
        event["aspects"] = {}
        event["previous_aspects"] = _map_full_aspects(attrs, source, node_type)
    else:  # MODIFIED
        if ev.get("previous_path"):
            event["renamed_from"] = ev["previous_path"]
        attribute_changes = ev.get("attribute_changes") or []
        event["aspects"] = _map_aspects_delta(attribute_changes)
        if kind == PROPERTY:
            references = _references_delta(attribute_changes, is_leaf)
            if references is not None:
                event["references"] = references

    return event


def _build_property_pointer_event(ev: dict[str, Any], parent: str) -> dict[str, Any]:
    """
    Build the synthetic PROPERTY-side event for a branch/struct that is itself a child
    of another branch/struct.

    Mirrors how a GraphQL field like `cabin: Cabin` is reported as both a PROPERTY on
    its parent type and a standalone ENTITY: every branch/struct with a parent is
    dual-reported as PROPERTY (this event) + ENTITY (the primary event). Root-level
    containers (no parent) are ENTITY only — see `_to_modl_events`.

    Kept intentionally minimal — no `output_type`, since vspec branches have no
    standalone type layer to point to. Only `is_list` (true when the branch defines
    instances) and `is_required` are reported.
    """
    path = ev["path"]
    change_type = ev["type"]
    attrs = ev.get("attributes") or {}

    event: dict[str, Any] = {
        "label": path,
        "parent_label": parent,
        "kind": PROPERTY,
        "change_type": change_type,
        # A branch/struct pointer always references another entity, never a leaf.
        "is_leaf": False,
    }

    if change_type == ADDED:
        event["aspects"] = {"is_list": bool(attrs.get("instances")), "is_required": False}
    elif change_type == REMOVED:
        event["aspects"] = {}
        event["previous_aspects"] = {"is_list": bool(attrs.get("instances")), "is_required": False}
    else:  # MODIFIED — always emitted alongside the ENTITY-side MODIFIED event
        if ev.get("previous_path"):
            event["renamed_from"] = ev["previous_path"]
        event["aspects"] = _property_pointer_delta(ev.get("attribute_changes") or [])

    return event


def _property_pointer_delta(attribute_changes: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the `is_list` delta (if any) for a branch/struct's PROPERTY-side MODIFIED event."""
    delta: dict[str, Any] = {}
    for ac in attribute_changes:
        if ac["attribute"] != "instances":
            continue
        prev_has = bool(ac["previous"])
        curr_has = bool(ac["current"])
        if prev_has != curr_has:
            delta["is_list"] = _wrap_op(prev_has, curr_has)
    return delta


def _to_modl_events(raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Translate internal diff events to the modl adapter IR format.

    A branch/struct that is itself a child of another branch is dual-reported: once
    as an ENTITY (the primary event) and once as a PROPERTY (the synthetic pointer
    event from `_build_property_pointer_event`) — mirroring GraphQL's `cabin: Cabin`
    field. Root-level containers (no parent) are reported as ENTITY only.
    """
    result: list[dict[str, Any]] = []
    for ev in raw_events:
        primary = _build_primary_event(ev)
        result.append(primary)
        if primary["kind"] == ENTITY and "parent_label" in primary:
            result.append(_build_property_pointer_event(ev, primary["parent_label"]))
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
# property_paths resolution
# ---------------------------------------------------------------------------


def _direct_path_occurrences(
    fqn: str,
    prop_attrs: dict[str, Any],
    attrs_by_path: dict[str, dict[str, Any]],
) -> list[tuple[str, dict[str, dict[str, str]]]]:
    """
    Resolve every literal runtime-path occurrence of a model/structs property by walking
    its ancestor branch chain and fanning out over every instanced ancestor's dimensions.

    Each instanced ancestor contributes one chosen combination of its dimension values,
    inserted as an extra dotted path segment immediately after the ancestor's own name
    (e.g. `Vehicle.Door.Left.IsOpen`, not `Vehicle.DoorLeft.IsOpen`). The immediate parent's
    instances are skipped when `prop_attrs` declares `instantiate: false`. Returns a list of
    `(path, tags)` pairs, where `tags` maps each contributing ancestor's FQN label to its
    chosen `{dimension1: value, ...}` selection.

    Known limitation: branches using `instances_relation: sibling` are not supported here —
    same limitation as the existing `_expand_instance_fqns` branch-hop injection.
    """
    parts = fqn.split(".")
    if len(parts) == 1:
        return [(fqn, {})]
    prop_name = parts[-1]
    ancestor_segments = parts[:-1]
    immediate_parent = ".".join(ancestor_segments)

    contributions: list[tuple[str, list[list[str]]]] = []
    running = ""
    for seg in ancestor_segments:
        running = seg if not running else f"{running}.{seg}"
        if running == immediate_parent and not _effective_instantiate(prop_attrs):
            continue
        anc_attrs = attrs_by_path.get(running) or {}
        dims = _instance_dimensions(anc_attrs.get("instances"))
        if dims:
            contributions.append((running, dims))

    if not contributions:
        return [(fqn, {})]

    choice_lists: list[list[tuple[str, tuple[str, ...]]]] = [
        [(ancestor_label, combo) for combo in itertools.product(*dims)] for ancestor_label, dims in contributions
    ]

    occurrences: list[tuple[str, dict[str, dict[str, str]]]] = []
    for selection in itertools.product(*choice_lists):
        tags: dict[str, dict[str, str]] = {}
        hops: dict[str, str] = {}
        for ancestor_label, combo in selection:
            tags[ancestor_label] = {f"dimension{i + 1}": v for i, v in enumerate(combo)}
            hops[ancestor_label] = ".".join(combo)

        path_parts: list[str] = []
        running = ""
        for seg in ancestor_segments:
            running = seg if not running else f"{running}.{seg}"
            path_parts.append(seg)
            if running in hops:
                path_parts.append(hops[running])
        path_parts.append(prop_name)
        occurrences.append((".".join(path_parts), tags))

    return occurrences


def _struct_reverse_refs(attrs_by_path: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    """
    Build a struct-label → referencing-FQNs reverse map from a combined model+structs
    attrs snapshot, used to flatten struct fields onto every property that uses them.

    Known limitation: a relative (non fully-qualified) struct reference is matched
    verbatim against the referencing node's own `datatype` string — vss-tools does not
    build a real tree here, so short struct names are not resolved against their
    declaring branch, mirroring the existing `references`/`output_type` behaviour
    elsewhere in this module.
    """
    reverse: dict[str, list[str]] = {}
    for fqn, attrs in attrs_by_path.items():
        if _node_type(attrs) in ("branch", "struct"):
            continue
        base_type, _ = _extract_datatype(attrs.get("datatype"))
        if base_type is None:
            continue
        reverse.setdefault(base_type, []).append(fqn)
    return reverse


def _struct_field_occurrences(
    fqn: str,
    attrs_by_path: dict[str, dict[str, Any]],
    reverse_refs: dict[str, list[str]],
    _visiting: frozenset[str] = frozenset(),
) -> list[tuple[str, dict[str, dict[str, str]]]]:
    """
    Resolve every literal runtime-path occurrence of a struct field by flattening it onto
    every property (anywhere in the model, or another struct) whose datatype names the
    field's own struct, recursing through struct-of-struct nesting.

    Returns `[]` when the struct has no referencing property anywhere (an orphan struct) —
    callers report an empty `paths: []` entry and log a warning in that case.
    """
    parent_label, _, field_name = fqn.rpartition(".")
    if not parent_label or parent_label in _visiting:
        if parent_label in _visiting:
            log.warning(f"Circular struct reference detected while resolving '{fqn}' — skipping")
        return []
    visiting = _visiting | {parent_label}

    occurrences: list[tuple[str, dict[str, dict[str, str]]]] = []
    for usage_fqn in reverse_refs.get(parent_label, []):
        usage_attrs = attrs_by_path.get(usage_fqn)
        if usage_attrs is None:
            continue
        if _node_type(usage_attrs) == "property":
            base_occurrences = _struct_field_occurrences(usage_fqn, attrs_by_path, reverse_refs, visiting)
        else:
            base_occurrences = _direct_path_occurrences(usage_fqn, usage_attrs, attrs_by_path)
        for base_path, tags in base_occurrences:
            occurrences.append((f"{base_path}.{field_name}", tags))
    return occurrences


def _merge_occurrences_into_bucket(
    bucket: dict[str, tuple[dict[str, dict[str, str]], str]],
    curr_occurrences: list[tuple[str, dict[str, dict[str, str]]]],
    prev_occurrences: list[tuple[str, dict[str, dict[str, str]]]],
) -> None:
    """
    Classify a property's current/previous runtime-path occurrences by their literal path
    string and merge the result into `bucket`, keyed by path.

    Callers must pre-canonicalize previous-side occurrence paths/tags through any ancestor
    rename map (see `_canonicalize_path`/`_canonicalize_tags`) before calling this, so that an
    ancestor rename only refreshes `tags` without manufacturing a spurious add+remove pair.
    """
    curr_by_path = dict(curr_occurrences)
    prev_by_path = dict(prev_occurrences)
    for path, tags in curr_by_path.items():
        change = "unchanged" if path in prev_by_path else "added"
        bucket[path] = (tags, change)
    for path, tags in prev_by_path.items():
        if path not in curr_by_path:
            bucket[path] = (tags, "removed")


def _build_rename_map(modl_events: list[dict[str, Any]]) -> dict[str, str]:
    """
    Build a previous-label \u2192 current-label map from every renamed ENTITY event in this diff
    (including cascaded descendant renames, each of which gets its own ENTITY MODIFIED event).

    Used to canonicalize an ancestor's tag key before classifying a property's path occurrences,
    so an ancestor rename doesn't defeat tags-based unchanged/added/removed classification.
    """
    rename_map: dict[str, str] = {}
    for ev in modl_events:
        if ev["kind"] == ENTITY and ev["change_type"] == MODIFIED and ev.get("renamed_from"):
            rename_map[ev["renamed_from"]] = ev["label"]
    return rename_map


def _canonicalize_tags(tags: dict[str, dict[str, str]], rename_map: dict[str, str]) -> dict[str, dict[str, str]]:
    """Remap each ancestor FQN key in `tags` through `rename_map` to its current-label equivalent."""
    if not rename_map:
        return tags
    return {rename_map.get(label, label): dims for label, dims in tags.items()}


def _canonicalize_path(path: str, rename_map: dict[str, str]) -> str:
    """
    Rewrite the longest renamed-ancestor prefix of a previous-snapshot runtime path to its
    current-label equivalent, so a pure ancestor rename resolves to the same literal path as
    the current occurrence (classified as `unchanged` instead of a spurious add+remove pair).
    """
    if not rename_map:
        return path
    best_old: str | None = None
    for old in rename_map:
        if path == old or path.startswith(old + "."):
            if best_old is None or len(old) > len(best_old):
                best_old = old
    if best_old is None:
        return path
    return rename_map[best_old] + path[len(best_old) :]


def _all_struct_field_fqns(
    struct_label: str,
    attrs_by_path: dict[str, dict[str, Any]],
    _visiting: frozenset[str] = frozenset(),
) -> set[str]:
    """
    Recursively collect every property FQN that is a direct or nested field of `struct_label`
    (nested through struct-of-struct fields), within a single snapshot's attrs map.
    """
    if struct_label in _visiting:
        return set()
    visiting = _visiting | {struct_label}
    prefix = struct_label + "."
    result: set[str] = set()
    for fqn, attrs in attrs_by_path.items():
        if not fqn.startswith(prefix) or "." in fqn[len(prefix) :]:
            continue
        if _node_type(attrs) in ("branch", "struct"):
            continue
        result.add(fqn)
        base_type, _ = _extract_datatype(attrs.get("datatype"))
        if base_type is not None and not _datatype_is_leaf(attrs.get("datatype")):
            result |= _all_struct_field_fqns(base_type, attrs_by_path, visiting)
    return result


def _struct_reference(attrs: dict[str, Any] | None) -> str | None:
    """Return the struct label a property's `datatype` points at, or `None` for a leaf/branch/struct."""
    if attrs is None or _node_type(attrs) in ("branch", "struct"):
        return None
    base_type, _ = _extract_datatype(attrs.get("datatype"))
    if base_type is None or _datatype_is_leaf(attrs.get("datatype")):
        return None
    return base_type


def _build_property_paths(
    modl_events: list[dict[str, Any]],
    current_attrs_by_path: dict[str, dict[str, Any]],
    previous_attrs_by_path: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build the top-level `property_paths` list required by modl >=0.8.0.

    For every ADDED/MODIFIED/REMOVED PROPERTY event that is binding-eligible
    (`is_leaf` or `binding_eligible`), resolves every literal runtime-path occurrence in
    the current and/or previous snapshot. Also re-reports every binding-eligible property
    tagged with an entity whose `instances` changed in this diff (the entity instance-delta
    cascade), and every field of a struct whose set of referencing properties changed in this
    diff (the struct usage-site cascade) — in both cases even when the property itself has no
    standalone event of its own.
    """
    current_reverse_refs = _struct_reverse_refs(current_attrs_by_path)
    previous_reverse_refs = _struct_reverse_refs(previous_attrs_by_path)
    rename_map = _build_rename_map(modl_events)

    def resolve(
        fqn: str | None, attrs_by_path: dict[str, dict[str, Any]], reverse_refs: dict[str, list[str]]
    ) -> list[tuple[str, dict[str, dict[str, str]]]]:
        if fqn is None:
            return []
        attrs = attrs_by_path.get(fqn)
        if attrs is None:
            return []
        if _node_type(attrs) == "property":
            return _struct_field_occurrences(fqn, attrs_by_path, reverse_refs)
        return _direct_path_occurrences(fqn, attrs, attrs_by_path)

    def resolve_previous(fqn: str | None) -> list[tuple[str, dict[str, dict[str, str]]]]:
        occ = resolve(fqn, previous_attrs_by_path, previous_reverse_refs)
        return [(_canonicalize_path(path, rename_map), _canonicalize_tags(tags, rename_map)) for path, tags in occ]

    entries: dict[tuple[str, str], dict[str, tuple[dict[str, dict[str, str]], str]]] = {}

    def merge_fqns(label: str, parent_label: str, curr_fqn: str | None, prev_fqn: str | None) -> None:
        curr_occ = resolve(curr_fqn, current_attrs_by_path, current_reverse_refs)
        prev_occ = resolve_previous(prev_fqn)
        bucket = entries.setdefault((label, parent_label), {})
        _merge_occurrences_into_bucket(bucket, curr_occ, prev_occ)

    def merge(label: str, parent_label: str, curr_fqn: str | None, prev_fqn: str | None, warn_if_orphan: bool) -> None:
        curr_occ = resolve(curr_fqn, current_attrs_by_path, current_reverse_refs)
        prev_occ = resolve_previous(prev_fqn)
        if warn_if_orphan and not curr_occ and not prev_occ:
            log.warning(
                f"No runtime path could be resolved for binding-eligible property '{label}' "
                "— likely an orphan struct type with no referencing property; reporting empty paths."
            )
        bucket = entries.setdefault((label, parent_label), {})
        _merge_occurrences_into_bucket(bucket, curr_occ, prev_occ)

    # ADDED/MODIFIED/REMOVED binding-eligible PROPERTY events.
    changed_entities: set[str] = set()
    for ev in modl_events:
        if ev["kind"] == ENTITY and ev["change_type"] == MODIFIED:
            if ev["aspects"].get("instances_added") or ev["aspects"].get("instances_removed"):
                changed_entities.add(ev["label"])

    for ev in modl_events:
        if ev["kind"] != PROPERTY:
            continue
        if not (ev.get("is_leaf") or ev.get("binding_eligible", False)):
            continue
        label = ev["label"]
        parent_label = ev.get("parent_label")
        if parent_label is None:
            continue
        change_type = ev["change_type"]
        if change_type == ADDED:
            merge(label, parent_label, label, None, warn_if_orphan=True)
        elif change_type == REMOVED:
            merge(label, parent_label, None, label, warn_if_orphan=False)
        else:
            prev_label = ev.get("renamed_from") or label
            merge(label, parent_label, label, prev_label, warn_if_orphan=False)

    # Entity instance-delta cascade: re-report every binding-eligible property tagged
    # with a changed entity, even without its own event.
    if changed_entities:
        all_fqns = set(current_attrs_by_path) | set(previous_attrs_by_path)
        for fqn in sorted(all_fqns):
            curr_attrs = current_attrs_by_path.get(fqn)
            prev_attrs = previous_attrs_by_path.get(fqn)
            rep_attrs = curr_attrs if curr_attrs is not None else prev_attrs
            if rep_attrs is None or _node_type(rep_attrs) in ("branch", "struct"):
                continue
            parent_label = fqn.rsplit(".", 1)[0] if "." in fqn else None
            if parent_label is None or (fqn, parent_label) in entries:
                continue
            curr_occ = resolve(fqn if curr_attrs is not None else None, current_attrs_by_path, current_reverse_refs)
            prev_occ = resolve_previous(fqn if prev_attrs is not None else None)
            touches_changed_entity = any(
                entity_label in tags for _, tags in (*curr_occ, *prev_occ) for entity_label in changed_entities
            )
            if not touches_changed_entity:
                continue
            bucket = entries.setdefault((fqn, parent_label), {})
            _merge_occurrences_into_bucket(bucket, curr_occ, prev_occ)

    # Struct usage-site cascade: whenever a property's struct reference is gained, lost, or
    # retargeted, re-report every field of every struct involved, even when the fields
    # themselves are unchanged (only their set of usage sites changed).
    changed_structs: set[str] = set()
    for fqn in set(current_attrs_by_path) | set(previous_attrs_by_path):
        curr_struct = _struct_reference(current_attrs_by_path.get(fqn))
        prev_struct = _struct_reference(previous_attrs_by_path.get(fqn))
        if curr_struct != prev_struct:
            if curr_struct is not None:
                changed_structs.add(curr_struct)
            if prev_struct is not None:
                changed_structs.add(prev_struct)

    if changed_structs:
        candidate_fqns: set[str] = set()
        for struct_label in changed_structs:
            candidate_fqns |= _all_struct_field_fqns(struct_label, current_attrs_by_path)
            candidate_fqns |= _all_struct_field_fqns(struct_label, previous_attrs_by_path)
        for fqn in sorted(candidate_fqns):
            curr_attrs = current_attrs_by_path.get(fqn)
            prev_attrs = previous_attrs_by_path.get(fqn)
            parent_label = fqn.rsplit(".", 1)[0] if "." in fqn else None
            if parent_label is None or (fqn, parent_label) in entries:
                continue
            merge_fqns(
                fqn,
                parent_label,
                fqn if curr_attrs is not None else None,
                fqn if prev_attrs is not None else None,
            )

    property_paths: list[dict[str, Any]] = []
    for label, parent_label in sorted(entries):
        bucket = entries[(label, parent_label)]
        paths = [
            {"tags": tags, "path": path, "change": change}
            for path, (tags, change) in sorted(bucket.items(), key=lambda kv: kv[0])
        ]
        property_paths.append({"label": label, "parent_label": parent_label, "paths": paths})
    return property_paths


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
                            "attributes": new_attrs,
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
                        "attributes": new_attrs,
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
                "attributes": current[path],
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
      changes             — ordered list of modl IR change events
      property_paths      — modl IR PropertyPaths entries (literal runtime-path occurrences)

    When previous_dir is None (first-run mode), every element in current_dir
    is treated as ADDED and emitted with its complete aspects snapshot.
    """
    raw_changes: list[dict[str, Any]] = []
    current_attrs_by_path: dict[str, dict[str, Any]] = {}
    previous_attrs_by_path: dict[str, dict[str, Any]] = {}

    sources = [
        (MODEL_SNAPSHOT_FILENAME, "model", True),
        (STRUCTS_SNAPSHOT_FILENAME, "structs", True),
        (UNITS_SNAPSHOT_FILENAME, "units", False),
        (QUANTITIES_SNAPSHOT_FILENAME, "quantities", False),
    ]

    for filename, source_label, detect_renames in sources:
        prev = load_snapshot_yaml(previous_dir / filename) if previous_dir else {}
        curr = load_snapshot_yaml(current_dir / filename)
        if source_label in ("model", "structs"):
            current_attrs_by_path.update(curr)
            previous_attrs_by_path.update(prev)
        if not prev and not curr:
            continue
        raw_changes.extend(_diff_dicts(prev, curr, source_label, detect_renames=detect_renames))

    raw_changes = _inject_instance_expansions(raw_changes)
    modl_events = _to_modl_events(raw_changes)
    modl_events = _inject_entity_content(modl_events)

    property_paths = _build_property_paths(modl_events, current_attrs_by_path, previous_attrs_by_path)

    _KIND_ORDER = {ENTITY: 0, ENUMERATION_SET: 1, PROPERTY: 2, ENUM_VALUE: 3}
    modl_events.sort(key=lambda e: _KIND_ORDER.get(e["kind"], 99))

    return {
        "previous": str(previous_dir) if previous_dir else None,
        "current": str(current_dir),
        "changes": modl_events,
        "property_paths": property_paths,
    }

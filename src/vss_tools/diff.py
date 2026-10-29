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
  - model      (model.vspec)
  - structs    (structs.vspec)
  - units      (units.yaml)
  - quantities (quantities.yaml)

Change events are computed on the authored flat dicts of the snapshots. The runtime
paths reported in `property_paths` are computed separately: each snapshot's model is
parsed and instance-expanded with the vss-tools tree (the same code `vspec export` uses),
and the resulting leaf paths of the previous and current snapshot are compared.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from anytree import PreOrderIter

from vss_tools import log
from vss_tools.compose import (
    MODEL_SNAPSHOT_FILENAME,
    QUANTITIES_SNAPSHOT_FILENAME,
    STRUCTS_SNAPSHOT_FILENAME,
    UNITS_SNAPSHOT_FILENAME,
)
from vss_tools.datatypes import Datatypes
from vss_tools.model import VSSData, VSSRaw
from vss_tools.tree import (
    InvalidExpansionEntryException,
    InvalidInstanceNodeException,
    MultipleRootsException,
    NoRootsException,
    VSSNode,
    build_tree,
    expand_string,
)

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


def _map_full_aspects(attrs: dict[str, Any], source: str, node_type: str) -> dict[str, Any]:
    """
    Build a full aspects snapshot.

    Used both for an ADDED event's `aspects` and a REMOVED event's `previous_aspects`
    (the modl IR requires the latter to carry the full prior-state snapshot).

    `instantiate` is excluded: it has no representation at all in modl's IR — it only
    gates how vss-tools expands runtime paths (see `_expand_model`).
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

    # datatype_leaf reflects the raw datatype (primitive vs. struct reference) and always
    # drives `references`. A struct field (source == "structs") is never independently
    # addressable — it has no property_paths entry of its own (see _is_struct_member in
    # _build_property_paths) — so it is always reported as non-binding-eligible
    # (is_leaf=False, binding_eligible omitted/False) regardless of its own datatype.
    datatype_leaf = True
    is_struct_field = source == "structs"
    if kind == PROPERTY:
        datatype_leaf = _is_leaf(attrs)
        is_leaf = False if is_struct_field else datatype_leaf
        event["is_leaf"] = is_leaf
        # A non-leaf PROPERTY's datatype always resolves to a struct (vspec datatypes
        # are either primitives or struct FQNs — never branches), so the struct value
        # itself is read/written as one atomic unit and is eligible for its own binding,
        # on top of the bindings already minted for each of its child properties. This
        # doesn't apply to a struct's own fields, which are never independently addressable.
        if not datatype_leaf and not is_struct_field:
            event["binding_eligible"] = True

    if change_type == ADDED:
        event["aspects"] = _map_full_aspects(attrs, source, node_type)
        if kind == PROPERTY and not datatype_leaf:
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
            references = _references_delta(attribute_changes, datatype_leaf)
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


def _reparent_events(
    modl_events: list[dict[str, Any]],
    previous_reparent: dict[str, str],
    current_reparent: dict[str, str],
) -> None:
    """
    Re-point events whose `parent_label` names no authored entity at the authored ancestor the
    vss-tools tree resolves it to (see `_ExpandedModel.reparent`), in place.

    Without this, a leaf authored below an instance (`Vehicle.Foo.Red.Extra`) would anchor to
    `Vehicle.Foo.Red`, a label that is never reported as an entity, and `_inject_entity_content`
    would fabricate an ENTITY MODIFIED for it that references no existing concept. `REMOVED`
    events resolve against the previous snapshot, all others against the current one.
    """
    for ev in modl_events:
        parent = ev.get("parent_label")
        if parent is None:
            continue
        mapping = previous_reparent if ev["change_type"] == REMOVED else current_reparent
        if parent in mapping:
            ev["parent_label"] = mapping[parent]


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


class DiffTreeException(Exception):
    """A snapshot model could not be parsed and expanded by the vss-tools tree."""


PathOccurrence = tuple[str, dict[str, dict[str, str]]]

# Marker attributes stamped onto the authored nodes before the tree expands them. Extra attributes
# survive the tree's copy/merge operations, which lets the expanded nodes be traced back to the
# authored (flat-diff) labels that change events are reported under.
_DECLARED_KEY = "diff_declared"
_INSTANCE_OF_KEY = "diff_instance_of"

_LEAF_TYPES = frozenset({"sensor", "actuator", "attribute"})
_STRUCTURAL_ATTRIBUTES = ("type", "instances", "instances_relation", "instantiate")


@dataclass
class _ExpandedModel:
    """
    Runtime view of one snapshot's model after vss-tools instance expansion.

    `paths` maps each authored leaf label to every runtime path it expands to, with the
    instance `tags` selecting that path. `reparent` maps a parent label that is not authored
    in the model (e.g. the implicit instance branch `Vehicle.Foo.Red` of an authored
    `Vehicle.Foo.Red.Extra`) to the nearest authored ancestor the tree resolves it to
    (`Vehicle.Foo`). Instance branches are never reported as entities of their own: instances
    are an aspect of the authored entity, and the expanded paths live in `property_paths`.
    """

    paths: dict[str, list[PathOccurrence]] = field(default_factory=dict)
    reparent: dict[str, str] = field(default_factory=dict)


def _node_type_value(node: VSSNode) -> str:
    node_type = getattr(node.data, "type", None)
    return str(getattr(node_type, "value", node_type))


def _hop_entity(node: VSSNode) -> str | None:
    """
    Return the label of the instanced entity this node is an instance hop of, else `None`.

    Hop nodes are copies of the authored entity node, so they carry its instance marker; the
    entity node itself (and copies of it nested below other hops) is told apart by its name.
    `is_instance` is deliberately not used: the tree resets it when a hop is merged with an
    authored node of the same name (e.g. `Vehicle.Foo.Red.Extra`).
    """
    entity = getattr(node.data, _INSTANCE_OF_KEY, None)
    if entity is None or node.name == entity.rsplit(".", 1)[-1]:
        return None
    return str(entity)


def _leaf_tags(leaf: VSSNode) -> dict[str, dict[str, str]]:
    """Derive an expanded leaf's instance tags from the hop branches along its path."""
    tags: dict[str, dict[str, str]] = {}
    previous_entity: str | None = None
    position = 0
    for node in leaf.path[:-1]:
        entity = _hop_entity(node)
        if entity is None:
            previous_entity = None
            continue
        # Consecutive hops of the same entity are its successive dimensions.
        position = position + 1 if entity == previous_entity else 1
        previous_entity = entity
        tags.setdefault(entity, {})[f"dimension{position}"] = node.name
    return tags


def _authored_ancestor(node: VSSNode, own_label: str) -> str | None:
    """
    Return the label of the nearest authored entity above `node` in the expanded tree.

    An instance hop resolves to the instanced entity it was generated for; any other node
    carrying a declared marker resolves to that label. Auto-created implicit nodes carry no
    marker and are skipped.
    """
    for ancestor in reversed(node.path[:-1]):
        entity = _hop_entity(ancestor)
        if entity is not None:
            return entity
        declared = getattr(ancestor.data, _DECLARED_KEY, None)
        if declared is not None and declared != own_label:
            return str(declared)
    return None


def _expand_model(model: dict[str, Any]) -> _ExpandedModel:
    """
    Parse a snapshot's model with the vss-tools tree and expand its instances exactly as
    `vspec export` does, then collect the runtime leaf paths (sensor, actuator, attribute)
    and how parents that are not authored resolve to authored entities.

    Struct types are not part of this tree: a struct never has runtime paths of its own, only
    the leaf that references it does.
    """
    expanded = _ExpandedModel()
    if not model:
        return expanded

    # Only the attributes that shape the expanded tree are handed to it, so unrelated
    # attributes can never make a node fail validation.
    marked: dict[str, Any] = {}
    for fqn, attrs in model.items():
        attrs = attrs or {}
        entry = {k: attrs[k] for k in _STRUCTURAL_ATTRIBUTES if k in attrs}
        entry[_DECLARED_KEY] = fqn
        if entry.get("instances"):
            entry[_INSTANCE_OF_KEY] = fqn
        marked[fqn] = entry

    # The tree needs a root node. Snapshots composed from a full model always declare one;
    # a bare root stub keeps partial models (only descendants declared) expandable.
    for root_name in {fqn.split(".", 1)[0] for fqn in marked}:
        marked.setdefault(root_name, {"type": "branch"})

    try:
        root, _ = build_tree(marked, connect_orphans=True)
        for node in PreOrderIter(root):
            if isinstance(node.data, VSSRaw) and not isinstance(node.data, VSSData):
                if _node_type_value(node) == "branch" and getattr(node.data, "instances", None):
                    raise DiffTreeException(
                        f"'{node.get_fqn()}' declares instances but is not a valid branch, cannot expand it"
                    )
        root.expand_instances()
    except (
        NoRootsException,
        MultipleRootsException,
        InvalidExpansionEntryException,
        InvalidInstanceNodeException,
    ) as e:
        raise DiffTreeException(f"Could not expand the snapshot model with vss-tools: {type(e).__name__} {e}") from e

    for node in PreOrderIter(root):
        declared = getattr(node.data, _DECLARED_KEY, None)
        # Hop nodes carry their entity's markers but are not authored nodes themselves.
        if declared is not None and "." in declared and _hop_entity(node) is None:
            parent_label = declared.rsplit(".", 1)[0]
            if parent_label not in model and parent_label not in expanded.reparent:
                ancestor = _authored_ancestor(node, declared)
                if ancestor is not None:
                    expanded.reparent[parent_label] = ancestor
        if node.is_leaf and _node_type_value(node) in _LEAF_TYPES:
            label = str(declared or node.get_fqn())
            expanded.paths.setdefault(label, []).append((node.get_fqn(), _leaf_tags(node)))
    return expanded


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


def _is_struct_member(
    parent_label: str,
    current_attrs_by_path: dict[str, dict[str, Any]],
    previous_attrs_by_path: dict[str, dict[str, Any]],
) -> bool:
    """Whether `parent_label` is a struct, i.e. the property is a struct field rather than a model signal."""
    parent_attrs = current_attrs_by_path.get(parent_label) or previous_attrs_by_path.get(parent_label)
    return parent_attrs is not None and _node_type(parent_attrs) == "struct"


def _build_property_paths(
    modl_events: list[dict[str, Any]],
    current_attrs_by_path: dict[str, dict[str, Any]],
    previous_attrs_by_path: dict[str, dict[str, Any]],
    current_model: _ExpandedModel,
    previous_model: _ExpandedModel,
) -> list[dict[str, Any]]:
    """
    Build the top-level `property_paths` list required by modl >=0.8.0.

    For every ADDED/MODIFIED/REMOVED model/structs PROPERTY event that is binding-eligible
    (`is_leaf` or `binding_eligible`), looks up its runtime-path occurrences in the
    expanded current and/or previous model (`_expand_model`) and classifies each path as
    added, removed or unchanged. Also re-reports every leaf tagged with an entity whose
    `instances` changed in this diff (the entity instance-delta cascade), even when the
    property itself has no standalone event of its own.

    Struct fields (properties whose parent is a struct, not a branch) never get their own
    entry — a struct has no standalone runtime address of its own; only the property that
    references the struct (itself binding-eligible via `binding_eligible`) is reported.
    """
    rename_map = _build_rename_map(modl_events)

    def current_occurrences(label: str | None) -> list[PathOccurrence]:
        return list(current_model.paths.get(label, [])) if label is not None else []

    def previous_occurrences(label: str | None) -> list[PathOccurrence]:
        occ = previous_model.paths.get(label, []) if label is not None else []
        return [(_canonicalize_path(path, rename_map), _canonicalize_tags(tags, rename_map)) for path, tags in occ]

    entries: dict[tuple[str, str], dict[str, tuple[dict[str, dict[str, str]], str]]] = {}

    def merge(label: str, parent_label: str, curr_fqn: str | None, prev_fqn: str | None, warn_if_orphan: bool) -> None:
        curr_occ = current_occurrences(curr_fqn)
        prev_occ = previous_occurrences(prev_fqn)
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
        if _is_struct_member(parent_label, current_attrs_by_path, previous_attrs_by_path):
            continue
        change_type = ev["change_type"]
        if change_type == ADDED:
            merge(label, parent_label, label, None, warn_if_orphan=True)
        elif change_type == REMOVED:
            merge(label, parent_label, None, label, warn_if_orphan=False)
        else:
            prev_label = ev.get("renamed_from") or label
            merge(label, parent_label, label, prev_label, warn_if_orphan=False)

    # Entity instance-delta cascade: re-report every leaf tagged with a changed entity,
    # even without its own event.
    if changed_entities:
        for fqn in sorted(set(current_model.paths) | set(previous_model.paths)):
            parent_label = fqn.rsplit(".", 1)[0] if "." in fqn else None
            if parent_label is None or (fqn, parent_label) in entries:
                continue
            curr_occ = current_occurrences(fqn)
            prev_occ = previous_occurrences(fqn)
            touches_changed_entity = any(
                entity_label in tags for _, tags in (*curr_occ, *prev_occ) for entity_label in changed_entities
            )
            if not touches_changed_entity:
                continue
            bucket = entries.setdefault((fqn, parent_label), {})
            _merge_occurrences_into_bucket(bucket, curr_occ, prev_occ)

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
    current_model_flat: dict[str, Any] = {}
    previous_model_flat: dict[str, Any] = {}

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
        if source_label == "model":
            current_model_flat, previous_model_flat = curr, prev
        if not prev and not curr:
            continue
        raw_changes.extend(_diff_dicts(prev, curr, source_label, detect_renames=detect_renames))

    previous_model = _expand_model(previous_model_flat)
    current_model = _expand_model(current_model_flat)

    modl_events = _to_modl_events(raw_changes)
    _reparent_events(modl_events, previous_model.reparent, current_model.reparent)
    modl_events = _inject_entity_content(modl_events)

    property_paths = _build_property_paths(
        modl_events, current_attrs_by_path, previous_attrs_by_path, current_model, previous_model
    )

    _KIND_ORDER = {ENTITY: 0, ENUMERATION_SET: 1, PROPERTY: 2, ENUM_VALUE: 3}
    modl_events.sort(key=lambda e: _KIND_ORDER.get(e["kind"], 99))

    return {
        "previous": str(previous_dir) if previous_dir else None,
        "current": str(current_dir),
        "changes": modl_events,
        "property_paths": property_paths,
    }

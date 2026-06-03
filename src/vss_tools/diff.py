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

from pathlib import Path
from typing import Any

import yaml

from vss_tools.compose import (
    MODEL_SNAPSHOT_FILENAME,
    QUANTITIES_SNAPSHOT_FILENAME,
    STRUCTS_SNAPSHOT_FILENAME,
    UNITS_SNAPSHOT_FILENAME,
)

# ---------------------------------------------------------------------------
# Change type constants
# ---------------------------------------------------------------------------
ADDED = "ADDED"
REMOVED = "REMOVED"
MODIFIED = "MODIFIED"


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


def _build_message(
    change_type: str,
    source: str,
    path: str,
    node_type: str,
    attribute_changes: list[dict[str, Any]] | None = None,
    previous_path: str | None = None,
    cascade: bool = False,
) -> str:
    """Build a human-readable sentence describing the change."""
    label = f"{node_type.capitalize()} '{path}'"

    if change_type == ADDED:
        return f"{label} was added to {source}."

    if change_type == REMOVED:
        return f"{label} was removed from {source}."

    # MODIFIED
    parts = []
    if previous_path:
        suffix = " (cascaded from parent rename)" if cascade else ""
        parts.append(f"{node_type.capitalize()} '{previous_path}' was renamed to '{path}'{suffix}.")
    if attribute_changes:
        for ac in attribute_changes:
            attr, pv, cv = ac["attribute"], ac["previous"], ac["current"]
            if pv is None:
                parts.append(f"Attribute '{attr}' was added with value '{cv}'.")
            elif cv is None:
                parts.append(f"Attribute '{attr}' was removed (was '{pv}').")
            else:
                parts.append(f"Attribute '{attr}' changed from '{pv}' to '{cv}'.")
    if not parts:
        parts.append(f"{label} was modified in {source}.")
    return " ".join(parts)


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
                            "message": _build_message(
                                MODIFIED,
                                source,
                                new_path,
                                new_nt,
                                attribute_changes=attr_changes,
                                previous_path=old_path,
                                cascade=False,
                            ),
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
                        "message": _build_message(
                            MODIFIED,
                            source,
                            new_path,
                            new_nt,
                            attribute_changes=attr_changes,
                            previous_path=old_path,
                            cascade=True,
                        ),
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
                "message": _build_message(ADDED, source, path, nt),
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
                "message": _build_message(REMOVED, source, path, nt),
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
                "message": _build_message(MODIFIED, source, path, nt, attribute_changes=attr_changes),
            }
        )

    return events


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def diff_folders(previous_dir: Path, current_dir: Path) -> dict[str, Any]:
    """
    Diff two compose snapshot folders.

    Returns a dict with:
      previous, current  — folder paths as strings
      summary            — counts per change type
      changes            — flat list of change objects
    """
    changes: list[dict[str, Any]] = []

    sources = [
        (MODEL_SNAPSHOT_FILENAME, "model", True),
        (STRUCTS_SNAPSHOT_FILENAME, "structs", True),
        (UNITS_SNAPSHOT_FILENAME, "units", False),
        (QUANTITIES_SNAPSHOT_FILENAME, "quantities", False),
    ]

    for filename, source_label, detect_renames in sources:
        prev = load_flat_yaml(previous_dir / filename)
        curr = load_flat_yaml(current_dir / filename)
        if not prev and not curr:
            continue
        changes.extend(_diff_dicts(prev, curr, source_label, detect_renames=detect_renames))

    summary = {
        ADDED: sum(1 for c in changes if c["type"] == ADDED),
        REMOVED: sum(1 for c in changes if c["type"] == REMOVED),
        MODIFIED: sum(1 for c in changes if c["type"] == MODIFIED),
    }

    return {
        "previous": str(previous_dir),
        "current": str(current_dir),
        "summary": summary,
        "changes": changes,
    }

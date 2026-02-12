"""
Pandas utilities for VSS tree processing.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from anytree import PreOrderIter

from vss_tools import log
from vss_tools.tree import VSSNode, get_expected_parent
from vss_tools.utils.misc import getattr_nn


def get_metadata_df(root: VSSNode, extended_attributes: tuple[str, ...] = ()) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Traverses the VSS tree and returns DataFrames with metadata for branches and leaves.

    Args:
        root: The root VSSNode of the VSS tree
        extended_attributes: Tuple of extended attribute names to include as additional columns.
                           These should match the attributes whitelisted via CLI flags
                           (-e/--extended-attributes or --extend-all-attributes)

    Returns:
        tuple: (branches_df, leaves_df)
               branches_df: DataFrame containing metadata for branch nodes
               leaves_df: DataFrame containing metadata for leaf nodes (attributes, sensors, actuators)
    """
    # Standard VSS columns that are always included
    core_headers = ["fqn", "parent", "name", "type", "description", "comment", "deprecation"]
    leaf_specific_headers = ["datatype", "unit", "min", "max", "allowed", "default", "instantiate"]
    branch_specific_headers = ["instances"]

    # Standard headers
    standard_headers = core_headers + leaf_specific_headers + branch_specific_headers

    # Extended attributes from CLI flags
    extended_headers = list(extended_attributes) if extended_attributes else []

    all_headers = standard_headers + extended_headers

    df = pd.DataFrame(columns=all_headers)

    # Track which extended attributes were actually found in the data
    found_extended_attrs = set()

    for node in PreOrderIter(root):
        data = node.get_vss_data()
        fqn = node.get_fqn()
        parent = get_expected_parent(fqn)
        name = node.name
        vss_type = data.type.value

        metadata = {
            "fqn": fqn,
            "parent": parent,
            "name": name,
            "type": vss_type,
        }

        # Add all standard metadata fields
        for header in standard_headers[4:]:
            metadata[header] = getattr_nn(data, header, "")

        # Add extended attributes if requested
        if extended_headers:
            for header in extended_headers:
                value = getattr_nn(data, header, None)
                if value is not None:
                    found_extended_attrs.add(header)
                metadata[header] = value

        df = pd.concat([df, pd.DataFrame([metadata])], ignore_index=True)

    # Split into branches and leaves
    branch_headers = core_headers + branch_specific_headers + extended_headers
    # Include both "branch" and "struct" as branch-like types
    branches_df = df[df["type"].isin(["branch", "struct"])]
    branches_df = branches_df[branch_headers].set_index("fqn").sort_index()

    leaf_headers = core_headers + leaf_specific_headers + extended_headers
    # Include "property" along with attribute, sensor, actuator as leaf-like types
    leaves_df = df[df["type"].isin(["attribute", "sensor", "actuator", "property"])]
    leaves_df = leaves_df[leaf_headers].set_index("fqn").sort_index()

    # Log DataFrame structure information
    if extended_headers and found_extended_attrs:
        log.debug("DataFrame content:")
        log.debug(f"  VSS branches have columns: {', '.join(branch_headers)}")
        log.debug(f"  VSS leaves have columns: {', '.join(leaf_headers)}")
        log.debug(f"  Extended attributes found: {', '.join(sorted(found_extended_attrs))}")

    return branches_df, leaves_df


def detect_and_resolve_short_name_collisions(
    branches_df: pd.DataFrame,
) -> tuple[dict[str, str], list[dict[str, Any]], dict[str, int]]:
    """
    Detect name collisions in branch names and resolve using progressive parent qualification.

    Uses a progressive qualification strategy:
    1. Try short name (e.g., "Window")
    2. If collision, try parent.name (e.g., "Door_Window")
    3. If still collision, try grandparent.parent.name, etc.
    4. As last resort, use full FQN with underscores

    Args:
        branches_df: DataFrame with branch metadata (must have 'name' and 'parent' columns, FQN as index)

    Returns:
        tuple: (fqn_to_short_name_mapping, collision_warnings, statistics)
               - fqn_to_short_name_mapping: Dict mapping FQN to assigned GraphQL type name
               - collision_warnings: List of collision details for reporting
               - statistics: Dict with counts for each resolution strategy

    Example:
        >>> df = pd.DataFrame({
        ...     'name': ['Window', 'Window', 'Seat'],
        ...     'parent': ['Vehicle.Cabin.Door', 'Vehicle.Body.Windshield', 'Vehicle.Cabin']
        ... }, index=['Vehicle.Cabin.Door.Window', 'Vehicle.Body.Windshield.Window', 'Vehicle.Cabin.Seat'])
        >>> mapping, warnings, stats = detect_and_resolve_short_name_collisions(df)
        >>> mapping
        {'Vehicle.Cabin.Door.Window': 'Door_Window', 'Vehicle.Body.Windshield.Window': 'Windshield_Window', ...}
    """
    from collections import defaultdict

    # Sort by FQN for deterministic processing
    sorted_df = branches_df.sort_index()

    # Track assigned names to detect collisions
    assigned_names: dict[str, str] = {}  # short_name -> fqn (currently using this name)
    fqn_to_short_name: dict[str, str] = {}  # fqn -> assigned short name
    collision_groups: dict[str, list[str]] = defaultdict(list)  # short_name -> list of colliding FQNs

    # First pass: detect collisions at the short name level
    short_name_groups = sorted_df.groupby("name")
    for short_name, group in short_name_groups:
        fqns = list(group.index)
        if len(fqns) > 1:
            collision_groups[short_name] = fqns

    # Track statistics
    stats = {
        "no_collision": 0,  # Clean short names
        "parent_qualified": 0,  # Needed parent.name
        "multi_parent_qualified": 0,  # Needed grandparent.parent.name or deeper
        "full_fqn": 0,  # Had to use full FQN
    }

    # Second pass: assign names using progressive qualification
    # For branches with collisions, process by depth (shallowest first) to prioritize root-level branches
    # For branches without collisions, process alphabetically

    # Separate colliding and non-colliding branches
    colliding_fqns = set()
    for fqns in collision_groups.values():
        colliding_fqns.update(fqns)

    non_colliding_df = sorted_df[~sorted_df.index.isin(colliding_fqns)]
    colliding_df = sorted_df[sorted_df.index.isin(colliding_fqns)].copy()

    # Add depth column for colliding branches (count dots in FQN)
    colliding_df["depth"] = colliding_df.index.str.count(r"\.")

    # Sort colliding branches by depth first (shallowest gets priority), then alphabetically
    colliding_df = colliding_df.sort_values(["depth", colliding_df.index.name or "fqn"])

    # Process non-colliding branches first (they get clean short names)
    for fqn in non_colliding_df.index:
        short_name = non_colliding_df.loc[fqn, "name"]
        fqn_to_short_name[fqn] = short_name
        assigned_names[short_name] = fqn
        stats["no_collision"] += 1

    # Then process colliding branches (depth priority means shallowest gets short name first)
    for fqn in colliding_df.index:
        short_name = colliding_df.loc[fqn, "name"]

        # Try progressive qualification
        assigned_name = _resolve_collision_with_qualification(
            fqn, short_name, colliding_df.loc[fqn, "parent"], assigned_names, stats
        )
        fqn_to_short_name[fqn] = assigned_name
        assigned_names[assigned_name] = fqn

    # Build collision warnings for reporting
    collision_warnings = []
    for short_name, fqns in collision_groups.items():
        warning = {
            "short_name": short_name,
            "collision_count": len(fqns),
            "fqns": fqns,
            "assigned_names": {fqn: fqn_to_short_name[fqn] for fqn in fqns},
        }
        collision_warnings.append(warning)

    # Log statistics
    len(sorted_df)
    log.info("Short name collision resolution:")
    log.info(f"  ✓ {stats['no_collision']} types use short names (no collisions)")
    if stats["parent_qualified"] > 0:
        log.info(f"  ⚠ {stats['parent_qualified']} types qualified with parent (e.g., Parent_Name)")
    if stats["multi_parent_qualified"] > 0:
        log.info(f"  ⚠ {stats['multi_parent_qualified']} types qualified with multiple nested parents")
    if stats["full_fqn"] > 0:
        log.warning(f"  ⚠ {stats['full_fqn']} types use full FQN due to deep collisions")

    if collision_warnings:
        log.info(f"  → See vspec_reference/short_name_collisions.yaml for {len(collision_warnings)} collision groups")

    # Return mapping, warnings, and statistics for detailed reporting
    return fqn_to_short_name, collision_warnings, stats


def _resolve_collision_with_qualification(
    fqn: str, short_name: str, parent_fqn: str, assigned_names: dict[str, str], stats: dict[str, int]
) -> str:
    """
    Resolve a name collision by progressively adding parent qualifiers.

    Tries: parent.name, grandparent.parent.name, ..., full FQN

    Args:
        fqn: The fully qualified name to resolve
        short_name: The base short name (last segment of FQN)
        parent_fqn: The parent's FQN
        assigned_names: Dict of already assigned names (to detect further collisions)
        stats: Statistics dict to update

    Returns:
        The assigned qualified name
    """
    # Build list of parent segments for progressive qualification
    fqn_parts = fqn.split(".")
    if len(fqn_parts) == 1:
        # Root node, no qualification possible - use as-is (shouldn't happen in collision scenario)
        stats["no_collision"] += 1
        return short_name

    # Try progressive qualification: parent.name, grandparent.parent.name, etc.
    for depth in range(1, len(fqn_parts)):
        # Take last 'depth + 1' segments (depth parents + name)
        qualified_parts = fqn_parts[-(depth + 1) :]
        candidate_name = "_".join(qualified_parts)

        # Check if this qualified name is available
        if candidate_name not in assigned_names:
            if depth == 1:
                stats["parent_qualified"] += 1
            else:
                stats["multi_parent_qualified"] += 1
            return candidate_name

    # All qualified names taken - use full FQN as last resort
    full_fqn_name = "_".join(fqn_parts)
    stats["full_fqn"] += 1
    return full_fqn_name

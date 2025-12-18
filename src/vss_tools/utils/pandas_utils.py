"""
Pandas utilities for VSS tree processing.
"""

from __future__ import annotations

import pandas as pd
from anytree import PreOrderIter

from vss_tools import log
from vss_tools.tree import VSSNode, get_expected_parent
from vss_tools.utils.misc import getattr_nn


def get_metadata_df(
    root: VSSNode, extended_attributes: tuple[str, ...] = ()
) -> tuple[pd.DataFrame, pd.DataFrame]:
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

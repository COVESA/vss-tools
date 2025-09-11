"""
Pandas utilities for VSS tree processing.
"""

from __future__ import annotations

import pandas as pd
from anytree import PreOrderIter

from vss_tools.tree import VSSNode, get_expected_parent
from vss_tools.utils.misc import getattr_nn


def get_metadata_df(root: VSSNode) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Traverses the VSS tree and returns DataFrames with metadata for branches and leaves.

    Args:
        root: The root VSSNode of the VSS tree

    Returns:
        tuple: (branches_df, leaves_df)
               branches_df: DataFrame containing metadata for branch nodes
               leaves_df: DataFrame containing metadata for leaf nodes (attributes, sensors, actuators)
    """
    core_headers = ["fqn", "parent", "name", "type", "description", "comment", "deprecation"]
    leaf_specific_headers = ["datatype", "unit", "min", "max", "allowed", "default"]
    branch_specific_headers = ["instances"]
    headers = core_headers + leaf_specific_headers + branch_specific_headers

    df = pd.DataFrame(columns=headers)

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

        # Add all other metadata fields
        for header in headers[4:]:
            metadata[header] = getattr_nn(data, header, "")

        df = pd.concat([df, pd.DataFrame([metadata])], ignore_index=True)

    # Split into branches and leaves
    branch_headers = core_headers + branch_specific_headers
    branches_df = df[df["type"] == "branch"]
    branches_df = branches_df[branch_headers].set_index("fqn").sort_index()

    leaf_headers = core_headers + leaf_specific_headers
    leaves_df = df[df["type"].isin(["attribute", "sensor", "actuator"])]
    leaves_df = leaves_df[leaf_headers].set_index("fqn").sort_index()

    return branches_df, leaves_df

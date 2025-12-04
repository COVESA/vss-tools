# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Utility functions for generating statistics from VSS data

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from vss_tools import log


def process_sankey_stats(data_metadata: pd.DataFrame, output: Path) -> None:
    """Process data for Sankey diagram statistics."""

    data_metadata = data_metadata[~data_metadata.isin(["branch"]).any(axis=1)]

    data_metadata["Property"] = data_metadata["Type"].apply(
        lambda x: "dynamic" if x in ["sensor", "actuator"] else "static"
    )

    if "Dummy" not in data_metadata.columns:
        data_metadata["Dummy"] = 0

    columns_order = ["Property", "Type", "DataType", "Dummy"]
    data_metadata = data_metadata.loc[:, columns_order]

    data_metadata.to_csv(output, index=False)
    log.info(f"Sankey stats CSV saved: {output}")


def process_piechart_stats(data_metadata: pd.DataFrame, output: Path, old_chart: Path) -> None:
    """Process data for pie chart statistics."""

    latest = pd.read_csv(old_chart)

    data_metadata["Default"] = pd.to_numeric(data_metadata["Default"], errors="coerce")

    major_version = None
    for index, row in data_metadata.iterrows():
        if "Vehicle.VersionVSS.Major" in row["Signal"] and row["Default"] > 5:
            major_version = int(row["Default"])
            break

    if major_version is not None:
        type_counts = Counter(data_metadata["Type"])
        counts = {
            "Branches": type_counts.get("branch", 0),
            "Sensors": type_counts.get("sensor", 0),
            "Actuators": type_counts.get("actuator", 0),
            "Attributes": type_counts.get("attribute", 0),
        }

        column_name = f"V{major_version}"
        if column_name not in latest.columns:
            latest[column_name] = pd.Series(
                [counts["Attributes"], counts["Branches"], counts["Sensors"], counts["Actuators"]]
            )

        version_cols = [col for col in latest.columns if col.startswith("V")]
        for i in range(len(version_cols) - 1):
            v1 = int(version_cols[i][1])
            v2 = int(version_cols[i + 1][1])
            if v2 != v1 + 1:
                log.warning(f"MISSING VERSION: V{v1+1}")
    else:
        raise ValueError("No valid major version found. The operation cannot proceed.")

    latest.to_csv(output, index=False)
    log.info(f"Pie chart stats CSV saved: {output}")


def process_radial_stats(signals_data: dict[str, Any], output: Path) -> None:
    """Process data for radial tree statistics."""

    root_key: str | None
    root_key = next(iter(signals_data))
    if root_key is None:
        raise KeyError("No root node with children found in signals data")

    children = []
    stack = [{"key": key, "value": value, "parent": None} for key, value in signals_data[root_key]["children"].items()]

    while stack:
        current = stack.pop()
        key, value, parent = current["key"], current["value"], current["parent"]

        item = {"name": key}
        if "children" in value:
            item["children"] = []
            stack.extend(
                {"key": child_key, "value": child_value, "parent": item["children"]}
                for child_key, child_value in value["children"].items()
            )
        else:
            for prop, prop_value in value.items():
                if prop != "children":
                    item[prop] = prop_value

        if parent is not None:
            parent.append(item)
        else:
            children.append(item)

    stack = [{"children": children}]
    while stack:
        current = stack.pop()
        if "children" in current:
            current["children"].sort(key=lambda x: ("children" not in x, x.get("type", ""), x.get("name", "")))
            stack.extend(child for child in current["children"] if "children" in child)

    radial_tree_data = {
        "name": root_key,
        "type": root_key,
        "children": children,
    }

    with open(output, "w") as f:
        json.dump(radial_tree_data, f, indent=2)
    log.info(f"Radial tree stats JSON saved: {output}")

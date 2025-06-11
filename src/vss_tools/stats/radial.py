# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Export JSON Data for Radial Tree.

import os
import json
import subprocess
from pathlib import Path

import rich_click as click

import vss_tools.cli_options as clo
from vss_tools import log


@click.command()
@clo.vspec_opt
@clo.output_required_opt
def cli(
    vspec: Path,
    output: Path,
):
    """
    Export JSON Data for Radial Tree.
    """

    interim_file = output.parent / "interim_vss_data.json"
    subprocess.run(
        [
            "vspec",
            "export",
            "json",
            "-s", str(vspec),
            "-o", str(interim_file),
        ],
        check=True
    )
    log.info(f"Interim JSON file generated: {interim_file}")

    with open(interim_file, "r") as f:
        signals_data = json.load(f)

    children = []
    stack = [{"key": key, "value": value, "parent": None} for key, value in signals_data["Vehicle"]["children"].items()]

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
            current["children"].sort(key=lambda x: (x.get("type", ""), x.get("name", "")))
            stack.extend(child for child in current["children"] if "children" in child)

    radial_tree_data = {
        "name": "Vehicle",
        "type": "Vehicle",
        "children": children,
    }

    with open(output, "w") as f:
        json.dump(radial_tree_data, f, indent=2)
    log.info(f"Final JSON file saved: {output}")

    try:
        os.remove(interim_file)
        log.info(f"Interim file removed: {interim_file}")
    except OSError as e:
        log.error(f"Error removing interim file: {e}")
# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Export CSV Statistics for Pie Chart.

import os
from collections import Counter
from pathlib import Path
from click.testing import CliRunner
import pandas as pd
import rich_click as click

import vss_tools.cli_options as clo
from vss_tools import log
import subprocess

@click.command()
@clo.vspec_opt
@clo.output_required_opt
@clo.old_chart_opt

def cli(
    vspec: Path,
    output: Path,
    old_chart: Path,
):
    """
    Export CSV Statistics for Pie Chart.
    """

    interim_file = output.parent / "interim_vss_data.csv"
    subprocess.run(
        [
            "vspec",
            "export",
            "csv",
            "-s", str(vspec),
            "-o", str(interim_file),
            "--no-expand"
        ],
        check=True
    )
    log.info(f"Interim CSV file generated: {interim_file}")

    data_metadata = pd.read_csv(interim_file)

    latest = pd.read_csv(old_chart)

    metadata = data_metadata  # Use the imported CSV content

    metadata["Default"] = pd.to_numeric(metadata["Default"], errors="coerce")

    major_version = None
    for index, row in metadata.iterrows():
        if "Vehicle.VersionVSS.Major" in row["Signal"] and row["Default"] > 5:
            major_version = int(row["Default"])
            break

    if major_version is not None:
        type_counts = Counter(metadata["Type"])
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
    log.info(f"Final CSV file saved: {output}")

    try:
        os.remove(interim_file)
        log.info(f"Interim file removed: {interim_file}")
    except OSError as e:
        log.error(f"Error removing interim file: {e}")

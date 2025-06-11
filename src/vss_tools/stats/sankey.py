# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Export CSV Stats for Sankey Diagram.

import os
import subprocess
from pathlib import Path

import pandas as pd
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
    Export CSV Stats for Sankey Diagram.
    """
    interim_file = output.parent / "interim_vss_data.csv"
    subprocess.run(
        [
            "vspec",
            "export",
            "csv",
            "-s",
            str(vspec),
            "-o",
            str(interim_file),
            "--no-expand",
        ],
        check=True,
    )
    log.info(f"Interim CSV file generated: {interim_file}")

    data_metadata = pd.read_csv(interim_file)

    data_metadata = data_metadata[~data_metadata.isin(["branch"]).any(axis=1)]

    data_metadata["Property"] = data_metadata["Type"].apply(
        lambda x: "dynamic" if x in ["sensor", "actuator"] else "static"
    )

    if "Dummy" not in data_metadata.columns:
        data_metadata["Dummy"] = 0

    columns_order = ["Property", "Type", "DataType", "Dummy"]
    data_metadata = data_metadata.loc[:, columns_order]

    data_metadata.to_csv(output, index=False)
    log.info(f"Final CSV file saved: {output}")

    try:
        os.remove(interim_file)
        log.info(f"Interim file removed: {interim_file}")
    except OSError as e:
        log.error(f"Error removing interim file: {e}")


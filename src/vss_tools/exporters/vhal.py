# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import rich_click as click

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.main import get_trees
from vss_tools.utils.vhal.vhal_mapper import VhalMapper


@click.command()
@clo.vspec_opt
@clo.vhal_map_opt
@clo.continuous_change_mode_opt
@clo.output_dir_opt
@clo.extend_new_opt
@clo.property_group_opt
@clo.min_property_id_opt
@clo.override_vhal_units_opt
@clo.override_vhal_datatype_opt
def cli(
    vspec: Path,
    vhal_map: Path,
    continuous_change_mode: Path | None,
    output_dir: Path,
    extend_new: bool,
    property_group: int,
    min_property_id: int,
    override_vhal_units: bool,
    override_vhal_datatype: bool,
):
    """
    Export as VSS as VHAL mapping file, Java and AIDL sources.
    """
    tree, datatype_tree = get_trees(
        vspec=vspec,
        include_dirs=(),
        aborts=(),
        strict=False,
        extended_attributes=(),
        quantities=(),
        units=(),
        types=(),
        overlays=(),
        expand=True,
    )

    log.info("Generating JSON output for VHAL Mapper...")
    mapper = VhalMapper(
        group=property_group,
        include_new=extend_new,
        starting_id=min_property_id,
        override_units=override_vhal_units,
        override_datatype=override_vhal_datatype,
    )

    if continuous_change_mode is not None:
        mapper.load_continuous_list(continuous_change_mode)
    mapper.load(vhal_map, tree)
    mapper.safe(vhal_map)

    java_output = output_dir / "VehiclePropertyIdsVss.java"
    permissions_output = output_dir / "VssPermissions.java"
    mapper.generate_java_files(java_output, permissions_output)

    aidl_output = output_dir / "VehiclePropertyVss.aidl"
    mapper.generate_aidl_file(aidl_output)

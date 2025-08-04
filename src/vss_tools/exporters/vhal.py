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
@click.option(
    "--vhal-map",
    type=click.Path(dir_okay=False, readable=True, path_type=Path, exists=False),
    required=True,
    help="""
        Read a json file with mapping of VSS property names to Android vehicle property ids.
        The file containing json list of all VSS properties (leaves) mappings by vss_tools generated VHAL IDs.
    """,
)
@click.option(
    "--continuous-change-mode",
    type=click.Path(dir_okay=False, readable=True, path_type=Path, exists=True),
    required=False,
    help="Read a json file list of VSS paths which should be considered as continuous change mode.",
)
@click.option(
    "--output-dir",
    type=click.Path(dir_okay=True, readable=True, path_type=Path, exists=True),
    required=True,
    help="Output directory, where vhal specific generated files are saved into.",
)
@click.option(
    "--property-group",
    type=int,
    required=False,
    default=1,
    show_default=True,
    help="""
        Group of generated VHAL properties: 1 = SYSTEM, 2 = VENDOR, 3 = BACKPORTED, 4 = VSS.
        See https://cs.android.com/android/platform/superproject/main/+/main:hardware/interfaces/automotive/vehicle/aidl_property/android/hardware/automotive/vehicle/VehiclePropertyGroup.aidl
    """,
)
@click.option(
    "--min-property-id",
    type=int,
    required=False,
    default=1,
    show_default=True,
    help="Stating ID for newly generated properties. This considers only the last 2 bytes of the VHAL property ID.",
)
@click.option(
    "--extend-new/--no-extend-new",
    help="""
        Whether to extend the map with new VSS nodes from the spec not present in the map file or only update
        existing VHAL properties and ignores all new VSS nodes.
    """,
    default=True,
    show_default=True,
)
@click.option(
    "--override-vhal-units/--no-override-vhal-units",
    help="Overrides previously generated VHAL units.",
    default=False,
    show_default=True,
)
@click.option(
    "--override-vhal-datatype/--no-override-vhal-datatype",
    help="Overrides previously generated VHAL datatypes.",
    default=False,
    show_default=True,
)
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

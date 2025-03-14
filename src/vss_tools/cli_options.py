# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import rich_click as click
from rich_click import option

from vss_tools.model import get_all_model_fields


def validate_attribute(value):
    """
    Checks that a user given attribute is valid.
    Should not contain ',' and should not be a core attribute
    """
    if "," in value:
        raise click.BadParameter("Comma (',') not allowed")
    if value in get_all_model_fields():
        raise click.BadParameter(f"'{value}' is a core attribute")
    return value


log_level_opt = click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    default="INFO",
    help="Log level.",
    show_default=True,
)

log_file_opt = click.option(
    "--log-file",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Log file.",
)

include_dirs_opt = option(
    "--include-dirs",
    "-I",
    multiple=True,
    type=click.Path(file_okay=False, readable=True, path_type=Path, exists=True),
    help="Add include directory to search for included vspec files.",
)

extended_attributes_opt = option(
    "--extended-attributes",
    "-e",
    multiple=True,
    type=validate_attribute,
    help="Whitelisted extended attributes",
)

strict_opt = option(
    "--strict/--no-strict",
    help="Whether to enable strict. Enables all '--abort/-a' values.",
    default=False,
    show_default=True,
)

aborts_opt = option(
    "--aborts",
    "-a",
    multiple=True,
    type=click.Choice(["unknown-attribute", "name-style"]),
    help="Abort on selected option. The '--strict' option enables all of them.",
    show_choices=True,
)

expand_opt = option(
    "--expand/--no-expand",
    default=True,
    show_default=True,
    help="Whether to expand 'instances'.",
)

overlays_opt = option(
    "--overlays",
    "-l",
    multiple=True,
    type=click.Path(dir_okay=False, readable=True, path_type=Path, exists=True),
    help="Overlay files to apply on top of the vspec.",
)

quantities_opt = option(
    "--quantities",
    "-q",
    multiple=True,
    type=click.Path(dir_okay=False, readable=True, path_type=Path, exists=True),
    help="Quantity files. [default: VSPEC/quantities.yaml]",
)

units_opt = option(
    "--units",
    "-u",
    type=click.Path(dir_okay=False, readable=True, path_type=Path, exists=True),
    help="Unit files. [default: VSPEC/units.yaml]",
    multiple=True,
)

vspec_opt = option(
    "--vspec",
    "-s",
    type=click.Path(dir_okay=False, readable=True, path_type=Path, exists=True),
    required=True,
    help="The vspec file.",
)

output_required_opt = option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output file.",
    required=True,
)

output_opt = option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output file.",
)

types_opt = option(
    "--types",
    "-t",
    multiple=True,
    type=click.Path(dir_okay=False, readable=True, path_type=Path, exists=True),
    help="Data types files.",
)


types_output_opt = option(
    "--types-output",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="""
        Output file for writing data types from vspec file.
        If not specified, a single file is used where applicable.
        In case of JSON and YAML, the data is exported under a
        special key: "ComplexDataTypes",
    """,
)


extend_all_attributes_opt = option(
    "--extend-all-attributes/--no-extend-all-attributes",
    help="""
        Generates all extended attributes,
        not only the ones given via '-e/--extended-attributes'
    """,
    default=False,
    show_default=True,
)

pretty_print_opt = option("--pretty/--no-pretty", help="Pretty print.", default=False, show_default=True)

vhal_map_opt = option(
    "--vhal-map",
    type=click.Path(dir_okay=False, readable=True, path_type=Path, exists=False),
    required=True,
    help="""
        Read a json file with mapping of VSS property names to Android vehicle property ids.
        The file containing json list of all VSS properties (leaves) mappings by vss_tools generated VHAL IDs.
    """,
)

continuous_change_mode_opt = option(
    "--continuous-change-mode",
    type=click.Path(dir_okay=False, readable=True, path_type=Path, exists=True),
    required=False,
    help="Read a json file list of VSS paths which should be considered as continuous change mode.",
)

output_dir_opt = option(
    "--output-dir",
    type=click.Path(dir_okay=True, readable=True, path_type=Path, exists=True),
    required=True,
    help="Output directory, where vhal specific generated files are saved into.",
)

property_group_opt = option(
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

min_property_id_opt = option(
    "--min-property-id",
    type=int,
    required=False,
    default=1,
    show_default=True,
    help="Stating ID for newly generated properties. This considers only the last 2 bytes of the VHAL property ID.",
)

extend_new_opt = option(
    "--extend-new/--no-extend-new",
    help="""
        Whether to extend the map with new VSS nodes from the spec not present in the map file or only update
        existing VHAL properties and ignores all new VSS nodes.
    """,
    default=True,
    show_default=True,
)

override_vhal_units_opt = option(
    "--override-vhal-units/--no-override-vhal-units",
    help="Overrides previously generated VHAL units.",
    default=False,
    show_default=True,
)

override_vhal_datatype_opt = option(
    "--override-vhal-datatype/--no-override-vhal-datatype",
    help="Overrides previously generated VHAL datatypes.",
    default=False,
    show_default=True,
)

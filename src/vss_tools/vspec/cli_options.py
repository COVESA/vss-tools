# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import rich_click as click
from rich_click import option
from pathlib import Path

log_level_opt = click.option(
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
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
    help="Whitelisted extended attributes, comma separated.",
)

strict_opt = option(
    "--strict/--no-strict",
    help="Whether to enable strict. Enables all '--abort/-a' values.",
    default=False,
    show_default=True)

aborts_opt = option(
    "--aborts",
    "-a",
    multiple=True,
    type=click.Choice(["unknown-attribute", "name-style"]),
    help="Abort on selected option. The '--strict' option enables all of them.",
    show_choices=True,
)

uuid_opt = option("--uuid/--no-uuid", help="Whether to add UUIDs.", show_default=True, default=False)

expand_opt = option(
    "--expand/--no-expand", default=True, show_default=True, help="Whether to expand the tree."
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
    help="The vspec file."
)

output_required_opt = option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output file.",
    required=True
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
    show_default=True
)

pretty_print_opt = option("--pretty/--no-pretty", help="Pretty print.", default=False, show_default=True)

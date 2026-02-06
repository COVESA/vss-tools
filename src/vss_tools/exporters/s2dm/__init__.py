# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""S2DM GraphQL Schema Exporter for VSS.

This exporter converts VSS specifications into S2DM-compliant GraphQL schemas.
The modular architecture organizes code into focused, maintainable modules.
"""

from __future__ import annotations

import sys
from pathlib import Path

import rich_click as click

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.main import get_trees
from vss_tools.utils.pandas_utils import get_metadata_df

from .constants import S2DM_CONVERSIONS, S2DMExporterException
from .reference_generator import generate_vspec_reference
from .schema_generator import (
    generate_s2dm_schema,
    print_schema_with_vspec_directives,
    write_modular_schema,
)


@click.command()
@clo.vspec_opt
@clo.output_file_or_dir_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@clo.modular_opt
@clo.flat_domains_opt
@clo.strict_exceptions_opt
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path, ...],
    extended_attributes: tuple[str, ...],
    strict: bool,
    aborts: tuple[str, ...],
    overlays: tuple[Path, ...],
    quantities: tuple[Path, ...],
    units: tuple[Path, ...],
    types: tuple[Path, ...],
    modular: bool,
    flat_domains: bool,
    strict_exceptions: Path | None,
) -> None:
    """
    Export a VSS specification to S2DM GraphQL schema.

    Output must be a directory. Creates vspec_reference/ subdirectory with
    VSS lookup spec and input files (units/quantities) for traceability.

    Output structure:
    - Default: outputDir/outputDir.graphql + vspec_reference/
    - Modular: outputDir/{domain,instances,other}/ + vspec_reference/
    """
    try:
        # Validate that output path doesn't have a file extension (enforce directory name only)
        if output.suffix:
            log.error(f"Output path appears to be a file (has extension '{output.suffix}'): {output}")
            log.error("Please provide a directory path (without file extension) for the S2DM export output.")
            sys.exit(1)

        # Validate that output is not an existing file
        if output.exists() and output.is_file():
            log.error(f"Output path must be a directory, not a file: {output}")
            log.error("Please provide a directory path for the S2DM export output.")
            sys.exit(1)

        # Create output directory if it doesn't exist
        if not output.exists():
            output.mkdir(parents=True, exist_ok=True)
            log.info(f"Created output directory: {output}")

        output_dir = output

        tree, data_type_tree = get_trees(
            vspec=vspec,
            include_dirs=include_dirs,
            aborts=aborts,
            strict=strict,
            extended_attributes=extended_attributes,
            quantities=quantities,
            units=units,
            types=types,
            overlays=overlays,
            expand=False,
            strict_exceptions_file=strict_exceptions,
        )

        log.info("Generating S2DM GraphQL schema...")

        # Generate the schema
        schema, unit_enums_metadata, allowed_enums_metadata, mapping_metadata = generate_s2dm_schema(
            tree, data_type_tree, extended_attributes=extended_attributes
        )

        if modular:
            # Write modular files
            write_modular_schema(
                schema, unit_enums_metadata, allowed_enums_metadata, mapping_metadata, output_dir, flat_domains
            )
            log.info(f"Modular GraphQL schema written to {output_dir}/")
        else:
            # Single file export: write to outputDir/outputDir.graphql
            graphql_file = output_dir / f"{output_dir.name}.graphql"
            full_schema_str = print_schema_with_vspec_directives(
                schema, unit_enums_metadata, allowed_enums_metadata, mapping_metadata
            )
            with open(graphql_file, "w") as outfile:
                outfile.write(full_schema_str)

            log.info(f"GraphQL schema written to {graphql_file}")

        # Generate VSS reference files (will check for implicit files)
        generate_vspec_reference(
            tree, data_type_tree, output_dir, extended_attributes, vspec, units, quantities, mapping_metadata
        )

    except S2DMExporterException as e:
        log.error(e)
        sys.exit(1)


__all__ = [
    "cli",
    "generate_s2dm_schema",
    "print_schema_with_vspec_directives",
    "write_modular_schema",
    "generate_vspec_reference",
    "get_metadata_df",
    "S2DM_CONVERSIONS",
]

# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

#
# Composes a vspec model (potentially spread across many files and overlays)
# into a stand-alone output folder containing:
#   - model_snapshot.vspec  — the flat, non-expanded signal tree
#   - structs_snapshot.vspec — the flat types tree (only written when --types is given)
#
# Both files are plain YAML and can be fed back into any vspec exporter as:
#   vspec export <format> -s <dir>/model_snapshot.vspec \
#                         --types <dir>/structs_snapshot.vspec ...
#

from pathlib import Path

import rich_click as click

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.exporters.yaml import export_yaml
from vss_tools.main import get_trees

# Fields to drop during compose serialization.
# Keeps instantiate/aggregate/arraysize (unlike the normal export) so the
# output remains a valid, re-parseable vspec.
SNAPSHOT_EXCLUDE_FIELDS = ["delete", "fqn", "is_instance"]

MODEL_SNAPSHOT_FILENAME = "model_snapshot.vspec"
STRUCTS_SNAPSHOT_FILENAME = "structs_snapshot.vspec"


@click.command()
@clo.vspec_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@clo.extend_all_attributes_opt
@clo.strict_exceptions_opt
@click.option(
    "--output-dir",
    "-o",
    required=True,
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    help="Output directory. Created if it does not exist.",
)
def cli(
    vspec: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    extend_all_attributes: bool,
    strict_exceptions: Path | None,
    output_dir: Path,
) -> None:
    """
    Compose a vspec model into a stand-alone, re-parseable folder snapshot.

    Merges all input files and overlays, then writes a flat FQN-keyed YAML
    snapshot with expansion disabled — so authored fields such as `instances`,
    `instantiate`, `aggregate`, and `arraysize` are preserved verbatim.

    The output folder contains:
      model_snapshot.vspec   — signal tree (always written)
      structs_snapshot.vspec — custom struct types (written only when --types is given)

    Both files can be used directly as -s / --types inputs for any subsequent
    vspec export invocation.
    """
    if output_dir.exists():
        log.info(f"Output directory already exists, writing into it: {output_dir}")
    else:
        output_dir.mkdir(parents=True)

    tree, datatype_tree = get_trees(
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
    )

    log.info(f"Composing vspec model into {output_dir}...")

    tree_data = tree.as_flat_dict(
        extend_all_attributes, extended_attributes, exclude_fields=SNAPSHOT_EXCLUDE_FIELDS, exclude_defaults=True
    )
    model_out = output_dir / MODEL_SNAPSHOT_FILENAME
    if model_out.exists():
        log.info(f"Overwriting existing file: {model_out}")
    export_yaml(model_out, tree_data)
    log.info(f"Signal tree written to {model_out}")

    if datatype_tree:
        structs_data = datatype_tree.as_flat_dict(
            extend_all_attributes, extended_attributes, exclude_fields=SNAPSHOT_EXCLUDE_FIELDS, exclude_defaults=True
        )
        structs_out = output_dir / STRUCTS_SNAPSHOT_FILENAME
        if structs_out.exists():
            log.info(f"Overwriting existing file: {structs_out}")
        export_yaml(structs_out, structs_data)
        log.info(f"Struct types written to {structs_out}")

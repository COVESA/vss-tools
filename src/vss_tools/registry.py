# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Registry CLI commands: sync and validate."""

from pathlib import Path

import rich_click as click
from anytree import PreOrderIter  # type: ignore[import]

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.main import get_trees
from vss_tools.utils.registry_utils import (
    RegistryConfigException,
    RegistryIntegrityException,
    empty_registry,
    load_namespaces,
    load_registry,
    sync_registry,
    to_jsonld,
    validate_immutability,
    write_jsonld,
)

_namespaces_opt = click.option(
    "--namespaces",
    "-n",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    help="YAML file declaring namespace prefixes and URIs.",
)

_registry_opt = click.option(
    "--registry",
    "-r",
    required=True,
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Registry CSV file (created on first run if absent).",
)


@click.command()
@clo.vspec_opt
@_namespaces_opt
@_registry_opt
@click.option(
    "--export-jsonld",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    default=None,
    help="Optional path to write a JSON-LD sidecar of the full registry.",
)
@clo.include_dirs_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@clo.overlays_opt
@clo.aborts_opt
@clo.strict_opt
@clo.strict_exceptions_opt
def sync_cli(
    vspec: Path,
    namespaces: Path,
    registry: Path,
    export_jsonld: Path | None,
    include_dirs: tuple[Path, ...],
    quantities: tuple[Path, ...],
    units: tuple[Path, ...],
    types: tuple[Path, ...],
    overlays: tuple[Path, ...],
    aborts: tuple[str, ...],
    strict: bool,
    strict_exceptions: Path | None,
) -> None:
    """
    Synchronize the identifier registry with the current VSS spec.

    Mints stable IDs for any FQNs not yet in the registry under the prefix
    declared in the namespaces file. Safe to run repeatedly — existing IDs
    are never changed or removed.
    """
    try:
        ns_config = load_namespaces(namespaces)
    except RegistryConfigException as e:
        raise click.ClickException(str(e))

    prefix = ns_config.namespace.prefix

    if registry.exists():
        try:
            existing_df = load_registry(registry)
        except RegistryIntegrityException as e:
            raise click.ClickException(f"Registry integrity check failed: {e}")
    else:
        log.info(f"No registry found at {registry} — starting fresh.")
        existing_df = empty_registry()

    tree, datatype_tree = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=(),
        quantities=quantities,
        units=units,
        types=types,
        overlays=overlays,
    )

    fqns: list[str] = sorted(node.get_fqn() for node in PreOrderIter(tree))
    if datatype_tree:
        fqns = sorted(fqns + [node.get_fqn() for node in PreOrderIter(datatype_tree)])

    updated_df, minted = sync_registry(existing_df, fqns, prefix)

    try:
        validate_immutability(existing_df, updated_df)
    except RegistryIntegrityException as e:
        raise click.ClickException(f"Immutability violation: {e}")

    updated_df.to_csv(registry, index=False)
    log.info(f"Registry written to {registry} ({minted} new IDs minted under '{prefix}:').")

    if export_jsonld:
        write_jsonld(to_jsonld(updated_df, ns_config), export_jsonld)
        log.info(f"JSON-LD sidecar written to {export_jsonld}.")


@click.command()
@_namespaces_opt
@_registry_opt
def validate_cli(namespaces: Path, registry: Path) -> None:
    """
    Validate the integrity of the registry and namespaces files.

    Checks schema validity and per-row hash integrity without writing anything.
    Exits with a non-zero status code if any check fails.
    """
    try:
        ns_config = load_namespaces(namespaces)
        owned = ns_config.namespace
        imports = ns_config.imports
        log.info(f"Namespaces OK — owned: '{owned.prefix}' ({owned.uri})")
        if imports:
            log.info(f"  Imports: {', '.join(sorted(imports))}")
    except RegistryConfigException as e:
        raise click.ClickException(str(e))

    try:
        df = load_registry(registry)
        log.info(
            f"Registry OK — {len(df)} row(s) across {df['composed_id'].str.split(':').str[0].nunique()} prefix(es)."
        )
    except RegistryIntegrityException as e:
        raise click.ClickException(f"Registry integrity check failed: {e}")

# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import logging
from pathlib import Path

import rich_click as click

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.lazy_group import LazyGroup


@click.group(context_settings={"auto_envvar_prefix": "vss_tools"}, invoke_without_command=True)
@clo.log_level_opt
@clo.log_file_opt
@click.version_option()
@click.pass_context
def cli(ctx: click.Context, log_level: str, log_file: Path):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
        log.addHandler(file_handler)

    log.setLevel(log_level)


@cli.group(
    cls=LazyGroup,
    lazy_subcommands={
        "apigear": "vss_tools.exporters.apigear:cli",
        "binary": "vss_tools.exporters.binary:cli",
        "csv": "vss_tools.exporters.csv:cli",
        "ddsidl": "vss_tools.exporters.ddsidl:cli",
        "franca": "vss_tools.exporters.franca:cli",
        "plantuml": "vss_tools.exporters.plantuml:cli",
        "id": "vss_tools.exporters.id:cli",
        "json": "vss_tools.exporters.json:cli",
        "jsonschema": "vss_tools.exporters.jsonschema:cli",
        "protobuf": "vss_tools.exporters.protobuf:cli",
        "yaml": "vss_tools.exporters.yaml:cli",
        "tree": "vss_tools.exporters.tree:cli",
        "samm": "vss_tools.exporters.samm:cli",
        "go": "vss_tools.exporters.go:cli",
        "ros2interface": "vss_tools.exporters.ros2interface:cli",
        "s2dm": "vss_tools.exporters.s2dm:cli",
    },
)
@click.pass_context
def export(ctx: click.Context):
    """
    Export a vspec to a chosen format
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

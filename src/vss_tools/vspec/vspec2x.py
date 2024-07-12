import logging
import rich_click as click
from vss_tools.vspec.lazy_group import LazyGroup
import vss_tools.vspec.cli_options as clo
from vss_tools import log
from pathlib import Path


@click.group(
    cls=LazyGroup,
    lazy_subcommands={
        "binary": "vss_tools.vspec.vssexporters.vss2binary:cli",
        "csv": "vss_tools.vspec.vssexporters.vss2csv:cli",
        "ddsidl": "vss_tools.vspec.vssexporters.vss2ddsidl:cli",
        "franca": "vss_tools.vspec.vssexporters.vss2franca:cli",
        "graphql": "vss_tools.vspec.vssexporters.vss2graphql:cli",
        "id": "vss_tools.vspec.vssexporters.vss2id:cli",
        "json": "vss_tools.vspec.vssexporters.vss2json:cli",
        "jsonschema": "vss_tools.vspec.vssexporters.vss2jsonschema:cli",
        "protobuf": "vss_tools.vspec.vssexporters.vss2protobuf:cli",
        "yaml": "vss_tools.vspec.vssexporters.vss2yaml:cli",
    },
    context_settings={"auto_envvar_prefix": "vss_tools"},
    invoke_without_command=True,
)
@clo.log_level_opt
@clo.log_file_opt
@click.pass_context
def cli(ctx: click.Context, log_level: str, log_file: Path):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        exit(1)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
        )
        log.addHandler(file_handler)

    log.setLevel(log_level)

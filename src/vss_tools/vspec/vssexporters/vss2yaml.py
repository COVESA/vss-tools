# Copyright (c) 2016 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

#
# Convert all vspec input files to a single flat YAML file.
#


from pathlib import Path

import rich_click as click
import yaml

import vss_tools.vspec.cli_options as clo
from vss_tools import log
from vss_tools.vspec.main import get_trees


def export_yaml(file_name, content_dict):
    with open(file_name, "w") as f:
        yaml.dump(
            content_dict,
            f,
            default_flow_style=False,
            Dumper=NoAliasDumper,
            sort_keys=True,
            width=1024,
            indent=2,
            encoding="utf-8",
            allow_unicode=True,
        )


# create dumper to remove aliases from output and to add nice new line after each object for a better readability
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()


@click.command()
@clo.vspec_opt
@clo.output_required_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.uuid_opt
@clo.expand_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@clo.types_output_opt
@clo.extend_all_attributes_opt
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    uuid: bool,
    expand: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    types_output: Path | None,
    extend_all_attributes: bool,
):
    """
    Export as YAML.
    """
    tree, datatype_tree = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        uuid=uuid,
        quantities=quantities,
        units=units,
        types=types,
        overlays=overlays,
        expand=expand,
    )
    log.info("Generating YAML output...")
    tree_data = tree.as_flat_dict(extend_all_attributes, extended_attributes)

    if datatype_tree:
        datatype_tree_data = datatype_tree.as_flat_dict(extend_all_attributes, extended_attributes)
        if not types_output:
            log.info("Adding custom data types to signal dictionary")
            tree_data["ComplexDataTypes"] = datatype_tree_data
        else:
            export_yaml(types_output, datatype_tree_data)

    export_yaml(output, tree_data)

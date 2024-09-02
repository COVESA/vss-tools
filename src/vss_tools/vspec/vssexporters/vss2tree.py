# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import rich_click as click
from anytree import RenderTree

import vss_tools.vspec.cli_options as clo
from vss_tools import log
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.tree import VSSNode


def get_rendered_tree(tree: VSSNode, attributes: tuple[str]) -> str:
    tree_content_lines = []
    for pre, fill, node in RenderTree(tree):
        tree_content_lines.append("%s%s" % (pre, node.name))
        for attribute in attributes:
            content = getattr(node.data, attribute, None)
            if content is None:
                continue
            if isinstance(content, str):
                tree_content_lines.append("%s%s='%s'" % (fill, attribute, content))
            else:
                tree_content_lines.append("%s%s=%s" % (fill, attribute, content))
    return "\n".join(tree_content_lines)


@click.command()
@clo.vspec_opt
@clo.output_opt
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
@click.option("--attr", help="Show VSSData attribute", multiple=True)
def cli(
    vspec: Path,
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
    output: Path | None,
    attr: tuple[str],
):
    """
    Export as Tree.
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

    rendered_tree = get_rendered_tree(tree, attr)
    if datatype_tree:
        rendered_tree += "\n" + get_rendered_tree(datatype_tree, attr)

    if output:
        log.info(f"Writing tree to: {output.absolute()}")
        with open(output, "w") as f:
            f.write(rendered_tree)
    else:
        log.info(rendered_tree)

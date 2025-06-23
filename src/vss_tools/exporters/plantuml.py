# Copyright (c) 2025 Contributors to COVESA, CEA LIST
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import rich_click as click
from anytree import RenderTree
from anytree import AbstractStyle
from anytree import AsciiStyle

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.main import get_trees
from vss_tools.tree import VSSNode

fqns: set[str] = {} 


# make first character lowercase
def lc_first(s):
    if len(s) == 0:
        return s
    else:
        return s[0].lower() + s[1:]

# variant of get_fqn that skips instance nodes (and the top-level one)
def get_fqn2(node: VSSNode) -> str:
    fqn = node.name
    while node.parent:
        data = node.get_vss_data()
        if node.is_leaf or (not data.is_instance):
            # generated classes are in a package carrying their own name, but enumerations are not
            if not getattr(data, "allowed", None):
                fqn = "P" + node.name + "." + fqn 
        node = node.parent
    return fqn

def get_name(node: VSSNode, qualify: bool) -> str:
    if qualify:
        return get_fqn2(node)
    else:
        return node.name

# get the class name of a node that is not an instance going up.
# adds postfix IS
def get_classname(node: VSSNode, qualify: bool) -> str:
    data = node.get_vss_data()
    if node.is_leaf:
        return get_name(node, qualify)
    elif not data.is_instance:
        if has_nested_instance_child(node):
            return get_name(node, qualify) + "IS0"
        elif has_instance_child(node):
            return get_name(node, qualify) + "IS"
        else:
            return get_name(node, qualify)
    else:
        parent = node.parent
        if parent.get_vss_data().is_instance:
            parent = parent.parent
        if has_instance_child(node):
            # node is already instance, implies nested one 
            return get_name(parent, qualify) + "_IS1"
        else:
            return get_name(parent, qualify)

# convenience function wrapping count_instance_children_depth
def has_instance_child(node: VSSNode) -> bool:
    return node.count_instance_children_depth() > 0

# convenience function wrapping count_instance_children_depth
def has_nested_instance_child(node: VSSNode) -> bool:
    return node.count_instance_children_depth() > 1

def get_enums(tree: VSSNode, fill: str, attributes: tuple[str]) -> str:
    tree_content_lines = []
    for node in tree.children:
        data = node.get_vss_data()
        if node.is_leaf:
            allowed = getattr(data, "allowed", None)
            fqn = get_fqn2(node)
            if allowed and (fqn not in fqns):
                # use enumeration instead of datatype, use 2nd level package name
                fqns[fqn] = True
                # create Enumeration
                tree_content_lines.append("")
                tree_content_lines.append("%s' %s" % (fill, data.description))
                tree_content_lines.append("%senum %s {" % (fill, node.name))
                for a in allowed:
                    tree_content_lines.append("%s\t%s," % (fill, a))
                tree_content_lines.append("%s}" % (fill))
        else:
            if not node.parent:
                # top level package, recurse only
                result =  get_enums(node, fill + "\t", attributes)
                tree_content_lines.append(result)
            elif data.is_instance:
                # instance node, recurse only (no package, no indent)
                result =  get_enums(node, fill, attributes)
                if result:
                    tree_content_lines.append(result)
            else:
                result =  get_enums(node, fill + "\t", attributes)
                # only add package, if it contains an enumeration
                if result:
                    tree_content_lines.append("")
                    tree_content_lines.append("%spackage P%s {" % (fill, node.name))
                    tree_content_lines.append(result)
                    tree_content_lines.append("%s}" % (fill))
                    
    return "\n".join(tree_content_lines)

def get_rendered_class(tree: VSSNode, fill, attributes: tuple[str]) -> str:
    tree_content_lines = []
    for node in tree.children:
        data = node.get_vss_data()
        if node.is_leaf:
            # add an entry to the data type
            tree_content_lines.append("")
            tree_content_lines.append("%s' %s: %s" % (fill, data.type.value, data.description))
            datatype = getattr(data, "datatype", None)
            unit = getattr(data, "unit", None)
            if unit:
                tree_content_lines.append("%s' unit: %s" % (fill, unit))
            min = getattr(data, "min", None)
            max = getattr(data, "max", None)
            if (min is not None) and (max is not None):
                tree_content_lines.append("%s' interval [%s..%s]" % (fill, min, max))
            elif min is not None:
                tree_content_lines.append("%s' interval [%s..)" % (fill, min))
            elif max is not None:
                tree_content_lines.append("%s' interval (..%s]" % (fill, max))
            if getattr(data, "allowed", None):
                # use qualified name of enumeration as datatype
                datatype = get_fqn2(node)
            tree_content_lines.append("%s%s : %s" % (fill, lc_first(node.name), datatype))
        else:
            tree_content_lines.append("%s%s : %s" % (fill, lc_first(node.name), get_classname(node, True)))

    return "\n".join(tree_content_lines)

def get_rendered_tree(node: VSSNode, fill, attributes: tuple[str]) -> str:
    tree_content_lines = []
    data = node.get_vss_data()
    needPkg = node.parent and (node.is_leaf or (not data.is_instance))
    if needPkg:
        tree_content_lines.append("%s' %s" % (fill, data.description))
        tree_content_lines.append("%spackage P%s {" % (fill, node.name))
        nFill = fill + "\t"
    else:
        nFill = fill
    tree_content_lines.append("%sclass %s {" % (nFill, get_classname(node, False)))
    # if the node has child instances, enter into first one (skip current child node)
    result = get_rendered_class(node, nFill + "\t", attributes)
    tree_content_lines.append(result)
    tree_content_lines.append("%s}" % (nFill))
    for node in node.children:
        data = node.get_vss_data()
        if node.is_leaf:
            pass
        else:
            result = get_rendered_tree(node, nFill, attributes)
            tree_content_lines.append(result)
            if data.is_instance:
                break

    if needPkg:
        tree_content_lines.append("%s}" % (fill))

    return "\n".join(tree_content_lines)

@click.command()
@clo.vspec_opt
@clo.output_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
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
    expand: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    output: Path | None,
    attr: tuple[str],
):
    """
    Export as PlantUML.
    """
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
        expand=expand,
    )

    rendered_tree = get_enums(tree, "", attr)
    rendered_tree += "\n' --- end of enums\n\n" + get_rendered_tree(tree, "", attr)
    if datatype_tree:
        rendered_tree += "\n'datatype tree:\n" + get_rendered_tree(datatype_tree, "", attr)

    if output:
        log.info(f"Writing tree to: {output.absolute()}")
        with open(output, "w") as f:
            f.write(rendered_tree)
    else:
        log.info(rendered_tree)

#!/usr/bin/env python3

# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec file to proto
#

import os
import sys
import rich_click as click
import vss_tools.vspec.cli_options as clo
from vss_tools.vspec.vssexporters.utils import get_trees
from pathlib import Path
from typing import Set

from anytree import PreOrderIter  # type: ignore[import]
from vss_tools import log
from vss_tools.vspec.model.vsstree import VSSNode

# Add path to main py vspec  parser
myDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(myDir, ".."))

PATH_DELIMITER = "."
DIR_DELIMITER = "/"

mapped = {
    "uint16": "uint32",
    "uint8": "uint32",
    "int8": "int32",
    "int16": "int32",
    "boolean": "bool",
}


class ProtoExporter(object):
    def __init__(self, out_dir: Path):
        self.out_files: Set[Path] = set()
        self.out_dir = out_dir

    def setup_file(self, fp: Path, package_name: str):
        with open(fp, "w") as proto_file:
            log.info(f"Initializing {fp}, package {package_name}")
            proto_file.write('syntax = "proto3";\n\n')
            # set up the proto's package
            proto_file.write(f"package {package_name};\n\n")
            self.out_files.add(fp)

    def traverse_data_type_tree(self, tree: VSSNode, static_uid, add_optional):
        """
        All structs in a branch are written to a single .proto file.
        The file's base name is same as the branch's name
        The fully qualified path of the type becomes the package.

        Example A.B.C.MyType becomes:
        "package A.B.C;
        message MyType{}"

        The files are organized by package.
        With the above example, the file generated is
        A/B/C/C.proto
        """

        tree_node: VSSNode

        for tree_node in filter(lambda n: n.is_struct(), PreOrderIter(tree)):
            type_qn = tree_node.qualified_name(PATH_DELIMITER).split(PATH_DELIMITER)
            curr_branch_qn = type_qn[:-1]
            # create dir if necessary
            dp = self.out_dir / Path(DIR_DELIMITER.join(curr_branch_qn))
            dp.mkdir(parents=True, exist_ok=True)

            curr_branch = type_qn[-2]
            fp = dp / Path(f"{curr_branch}.proto")
            is_first_write = fp not in self.out_files
            if is_first_write:
                self.setup_file(fp, ".".join(curr_branch_qn))
            with open(fp, "a") as proto_file:
                # import of other proto types in other branches
                imports = []
                for c_node in filter(
                    lambda c: c.is_property() and not c.has_datatype(),
                    tree_node.children,
                ):
                    child_branch_path = c_node.get_datatype().split(PATH_DELIMITER)[:-1]
                    child_branch_path_str = DIR_DELIMITER.join(child_branch_path)
                    if child_branch_path_str != DIR_DELIMITER.join(curr_branch_qn):
                        child_basename = child_branch_path[-1]
                        imports.append(
                            f"{child_branch_path_str}/{child_basename}.proto"
                        )

                # unique sorted list
                imports = list(set(imports))
                imports.sort()
                for importstmt in imports:
                    proto_file.write(f'import "{importstmt}";\n')
                proto_file.write("\n")

                proto_file.write(f"message {type_qn[-1]} {{" + "\n")
                print_message_body(
                    tree_node.children, proto_file, static_uid, add_optional
                )
                proto_file.write("}\n\n")
                log.info(f"Wrote {type_qn[-1]} to {fp}")


def traverse_signal_tree(tree: VSSNode, proto_file, static_uid, add_optional):
    proto_file.write('syntax = "proto3";\n\n')
    tree_node: VSSNode

    # get all the import statements for dependent types (structs)
    imports = []
    for c_node in filter(
        lambda c: c.is_signal() and not c.has_datatype(), PreOrderIter(tree)
    ):
        child_path = c_node.get_datatype().split(PATH_DELIMITER)[:-1]
        child_basename = child_path[-1]
        imports.append(f"{DIR_DELIMITER.join(child_path)}/{child_basename}.proto")

    # unique sorted list
    imports = list(set(imports))
    imports.sort()
    # write import statements to file
    for importstmt in imports:
        proto_file.write(f'import "{importstmt}";\n')
    proto_file.write("\n")

    # write proto messages to file
    for tree_node in filter(lambda n: n.is_branch(), PreOrderIter(tree)):
        proto_file.write(f"message {tree_node.qualified_name('')} {{" + "\n")
        print_message_body(tree_node.children, proto_file, static_uid, add_optional)
        proto_file.write("}\n\n")


def print_message_body(nodes, proto_file, static_uid, add_optional):
    usedKeys = {}
    for i, node in enumerate(nodes, 1):
        if not (node.is_branch() or node.is_struct()):
            dt_val = node.get_datatype()
            data_type = mapped.get(dt_val.strip("[]"), dt_val.strip("[]"))
            if dt_val.endswith("[]"):
                data_type = "repeated " + data_type
            elif add_optional:
                data_type = "optional " + data_type
        else:
            data_type = node.qualified_name("")
            if add_optional:
                data_type = "optional " + data_type
        if static_uid:
            if "staticUID" not in node.extended_attributes:
                log.fatal(
                    (
                        f"Aborting because {node.qualified_name('.')} does not have the staticUID attribute. "
                        f"When using the option --static-uid each node must have the attribute staticUID."
                    )
                )
                sys.exit(-1)
            fieldNumber = int(int(node.extended_attributes["staticUID"], 0) / 8)
            if fieldNumber < 20000 and fieldNumber >= 19000:
                log.fatal("""Aborting because field number {fieldNumber} for signal {node.name} is in
                reservered range between 19000 and 20000. Consider changing the signal to alter the staticUID.""")
                sys.exit(-1)
            if fieldNumber in usedKeys:
                log.fatal(
                    (
                        f"Aborting, due to collision for fieldNumber {fieldNumber}. "
                        f"It is used by {node.qualified_name('.')} and {usedKeys[fieldNumber]}. "
                        "Consider changing the signals to alter the staticUID."
                    )
                )
                proto_file.truncate(0)
                sys.exit(-1)
            else:
                usedKeys[fieldNumber] = node.qualified_name(".")
        else:
            fieldNumber = i
        proto_file.write(f"  {data_type} {node.name} = {fieldNumber};" + "\n")


@click.command()
@clo.vspec_opt
@clo.output_required_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@click.option(
    "--types-out-dir",
    help="Output directory for generated protos.",
    type=click.Path(file_okay=False, writable=True),
)
@click.option(
    "--static-uid",
    is_flag=True,
    help="Expect staticUID attribute in the vspec input and use it as field number",
)
@click.option("--add-optional", is_flag=True, help="Set each field to 'optional'")
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    types_out_dir: Path,
    static_uid: bool,
    add_optional: bool,
):
    """
    Export as protobuf.
    """
    log.info("Generating protobuf output...")
    tree, datatype_tree = get_trees(
        include_dirs,
        aborts,
        strict,
        extended_attributes,
        False,
        quantities,
        vspec,
        units,
        types,
        None,
        overlays,
        True,
    )
    if datatype_tree is not None:
        if types_out_dir:
            exporter_path = types_out_dir
        else:
            exporter_path = Path.cwd()
        log.debug(f"Will use {exporter_path} for type exports")
        exporter = ProtoExporter(exporter_path)
        exporter.traverse_data_type_tree(datatype_tree, static_uid, add_optional)

    with open(output, "w") as f:
        log.info(f"Writing to: {output}")
        traverse_signal_tree(tree, f, static_uid, add_optional)

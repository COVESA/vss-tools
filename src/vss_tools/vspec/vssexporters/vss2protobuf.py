# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec file to proto
#

import sys
from io import TextIOWrapper
from pathlib import Path

import rich_click as click
from anytree import findall

import vss_tools.vspec.cli_options as clo
from vss_tools import log
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.model import (
    VSSDataBranch,
    VSSDataDatatype,
    VSSDataStruct,
)
from vss_tools.vspec.tree import VSSNode

PATH_DELIMITER = "."
DIR_DELIMITER = "/"

mapped = {
    "uint16": "uint32",
    "uint8": "uint32",
    "int8": "int32",
    "int16": "int32",
    "boolean": "bool",
}


def init_package_file(path: Path, package_name: str):
    with open(path, "w") as f:
        log.info(f"Initializing {path}, package {package_name}")
        f.write('syntax = "proto3";\n\n')
        f.write(f"package {package_name};\n\n")


def traverse_data_type_tree(tree: VSSNode, static_uid: bool, add_optional: bool, out_dir: Path):
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

    node: VSSNode
    for node in findall(tree, filter_=lambda n: isinstance(n.data, VSSDataStruct)):
        # A/B/C/MyType
        struct_path = Path(node.get_fqn("/"))

        # <out-dir>/A/B/C
        package_path = out_dir / struct_path.parent
        package_path.mkdir(parents=True, exist_ok=True)

        # <out-dir>/A/B/C/C.proto
        out_file = package_path / f"{package_path.name}.proto"
        if not out_file.exists():
            init_package_file(out_file, ".".join(struct_path.parent.parts))

        with open(out_file, "a") as fd:
            imports = []
            for c_node in findall(node, filter_=lambda n: isinstance(n.data, VSSDataDatatype)):
                datatype = c_node.data.datatype
                if "." not in datatype:
                    continue
                c_struct_path = Path(datatype.replace(".", "/"))
                if c_struct_path.parent != struct_path.parent:
                    imports.append(f"{c_struct_path.parent}/{c_struct_path.parent.name}.proto")

            write_imports(fd, imports)

            fd.write(f"message {struct_path.name} {{" + "\n")
            print_messages(node.children, fd, static_uid, add_optional)
            fd.write("}\n\n")
            log.info(f"Wrote {struct_path.name} to {out_file}")


def traverse_signal_tree(tree: VSSNode, fd: TextIOWrapper, static_uid: bool, add_optional: bool):
    fd.write('syntax = "proto3";\n\n')

    imports = []
    for node in findall(tree, filter_=lambda n: isinstance(n.data, VSSDataDatatype)):
        datatype = node.data.datatype
        if "." not in datatype:
            continue
        struct_path = Path(node.data.datatype.replace(".", "/"))  # type: ignore
        imports.append(f"{struct_path.parent}/{struct_path.parent.name}.proto")
    write_imports(fd, imports)

    # write proto messages to file
    for node in findall(tree, filter_=lambda node: isinstance(node.data, VSSDataBranch)):
        fd.write(f"message {node.get_fqn('')} {{" + "\n")
        print_messages(node.children, fd, static_uid, add_optional)
        fd.write("}\n\n")


def write_imports(fd: TextIOWrapper, imports: list[str]):
    imports = list(set(imports))
    imports.sort()
    for stmt in imports:
        fd.write(f'import "{stmt}";\n')
    fd.write("\n")


def print_messages(nodes: tuple[VSSNode], fd: TextIOWrapper, static_uid: bool, add_optional: bool):
    usedKeys: dict[int, str] = {}
    for i, node in enumerate(nodes, 1):
        if isinstance(node.data, VSSDataDatatype):
            dt_val = node.data.datatype
            data_type = mapped.get(dt_val.strip("[]"), dt_val.strip("[]"))
            if dt_val.endswith("[]"):
                data_type = "repeated " + data_type
            elif add_optional:
                data_type = "optional " + data_type
        else:
            data_type = node.get_fqn("")
            if add_optional:
                data_type = "optional " + data_type
        if static_uid:
            if "staticUID" not in node.data.get_extra_attributes():
                log.fatal(
                    (
                        f"Aborting because {node.get_fqn()} does not have the staticUID attribute. "
                        f"When using the option --static-uid each node must have the attribute staticUID."
                    )
                )
                sys.exit(-1)
            fieldNumber = int(int(getattr(node.data, "staticUID"), 0) / 8)
            if fieldNumber < 20000 and fieldNumber >= 19000:
                log.fatal("""Aborting because field number {fieldNumber} for signal {node.name} is in
                reservered range between 19000 and 20000. Consider changing the signal to alter the staticUID.""")
                sys.exit(-1)
            if fieldNumber in usedKeys:
                log.fatal(
                    (
                        f"Aborting, due to collision for fieldNumber {fieldNumber}. "
                        f"It is used by {node.get_fqn()} and {usedKeys[fieldNumber]}. "
                        "Consider changing the signals to alter the staticUID."
                    )
                )
                fd.truncate(0)
                sys.exit(-1)
            else:
                usedKeys[fieldNumber] = node.get_fqn()
        else:
            fieldNumber = i
        fd.write(f"  {data_type} {node.name} = {fieldNumber};" + "\n")


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
    types_out_dir: Path | None,
    static_uid: bool,
    add_optional: bool,
):
    """
    Export as protobuf.
    """
    log.info("Generating protobuf output...")
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
    )
    if datatype_tree:
        if not types_out_dir:
            types_out_dir = Path.cwd()
            log.warning(f"No output directory given. Writing to: {types_out_dir.absolute()}")
        traverse_data_type_tree(datatype_tree, static_uid, add_optional, types_out_dir)

    with open(output, "w") as f:
        log.info(f"Writing to: {output}")
        traverse_signal_tree(tree, f, static_uid, add_optional)

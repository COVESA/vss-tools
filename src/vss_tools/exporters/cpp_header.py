# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Export VSS tree as a C++ header-only file suitable for embedding in
# binaries with no filesystem dependency (e.g. microcontrollers).

import re
from pathlib import Path

import rich_click as click
from anytree import PreOrderIter

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.main import get_trees
from vss_tools.model import VSSDataBranch
from vss_tools.tree import VSSNode

_CPP_TYPE_MAP: dict[str, str] = {
    "uint8": "uint8_t",
    "uint16": "uint16_t",
    "uint32": "uint32_t",
    "uint64": "uint64_t",
    "int8": "int8_t",
    "int16": "int16_t",
    "int32": "int32_t",
    "int64": "int64_t",
    "float": "float",
    "double": "double",
    "boolean": "bool",
    "string": "const char*",
    "uint8[]": "const uint8_t*",
    "uint16[]": "const uint16_t*",
    "uint32[]": "const uint32_t*",
    "uint64[]": "const uint64_t*",
    "int8[]": "const int8_t*",
    "int16[]": "const int16_t*",
    "int32[]": "const int32_t*",
    "int64[]": "const int64_t*",
    "float[]": "const float*",
    "double[]": "const double*",
    "boolean[]": "const bool*",
    "string[]": "const char* const*",
    "numeric": "double",
    "numeric[]": "const double*",
    "int": "int64_t",
}


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _str_literal(v: object | None) -> str:
    if v is None:
        return "nullptr"
    return f'"{_escape(str(v))}"'


def _identifier(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "_", path)


def _emit_signal(node: VSSNode) -> list[str]:
    data = node.get_vss_data()
    fqn = node.get_fqn()
    ident = _identifier(fqn)
    datatype = str(getattr(data, "datatype", "")) or ""
    cpp_type = _CPP_TYPE_MAP.get(datatype, "const char*")
    unit = getattr(data, "unit", None)
    min_val = getattr(data, "min", None)
    max_val = getattr(data, "max", None)
    allowed = getattr(data, "allowed", None)
    default = getattr(data, "default", None)

    lines: list[str] = []

    if allowed:
        lines.append(f"constexpr const char* {ident}_kAllowed[] = {{")
        for v in allowed:
            lines.append(f'    "{_escape(str(v))}",')
        lines.append("    nullptr,")
        lines.append("};")
        allowed_ref = f"{ident}_kAllowed"
    else:
        allowed_ref = "nullptr"

    lines.append(f"constexpr VssSignal {ident} = {{")
    lines.append(f"    {_str_literal(fqn)},")
    lines.append(f"    {_str_literal(data.type.value)},")
    lines.append(f"    {_str_literal(datatype if datatype else None)},")
    lines.append(f'    "{cpp_type}",')
    lines.append(f"    {_str_literal(unit)},")
    lines.append(f"    {_str_literal(data.description)},")
    lines.append(f"    {_str_literal(min_val)},")
    lines.append(f"    {_str_literal(max_val)},")
    lines.append(f"    {allowed_ref},")
    lines.append(f"    {_str_literal(default)},")
    lines.append("};")
    return lines


def generate(root: VSSNode, namespace: str, include_branches: bool) -> str:
    leaf_nodes = [
        n
        for n in PreOrderIter(root)
        if n.parent is not None and (include_branches or not isinstance(n.data, VSSDataBranch))
    ]

    signal_idents = [_identifier(n.get_fqn()) for n in leaf_nodes]

    out: list[str] = []
    out.append("// SPDX-FileCopyrightText: Copyright (c) 2024 Contributors to COVESA")
    out.append("// SPDX-License-Identifier: MPL-2.0")
    out.append("")
    out.append("// Auto-generated from the Vehicle Signal Specification.")
    out.append("// Do not edit manually.")
    out.append("")
    out.append("#pragma once")
    out.append("")
    out.append("#include <cstddef>")
    out.append("#include <cstdint>")
    out.append("")
    out.append(f"namespace {namespace} {{")
    out.append("")
    out.append("struct VssSignal {")
    out.append("    const char* const path;")
    out.append("    const char* const type;")
    out.append("    const char* const datatype;")
    out.append("    const char* const cpp_type;")
    out.append("    const char* const unit;")
    out.append("    const char* const description;")
    out.append("    const char* const min_value;")
    out.append("    const char* const max_value;")
    out.append("    const char* const* const allowed_values;  // null-terminated, or nullptr")
    out.append("    const char* const default_value;")
    out.append("};")
    out.append("")

    for node in leaf_nodes:
        for line in _emit_signal(node):
            out.append(line)
        out.append("")

    out.append(f"constexpr VssSignal kSignals[] = {{")
    for ident in signal_idents:
        out.append(f"    {ident},")
    out.append("};")
    out.append("")
    out.append("constexpr std::size_t kSignalCount = sizeof(kSignals) / sizeof(kSignals[0]);")
    out.append("")
    out.append(f"}}  // namespace {namespace}")
    out.append("")

    return "\n".join(out)


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
@clo.strict_exceptions_opt
@click.option("--namespace", default="vss", show_default=True, help="C++ namespace name.")
@click.option(
    "--include-branches/--no-include-branches",
    default=False,
    show_default=True,
    help="Include branch nodes in addition to leaf signals.",
)
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
    namespace: str,
    include_branches: bool,
    strict_exceptions: Path | None,
):
    """
    Export as a C++ header-only file for embedding VSS in compiled binaries.
    """
    log.info("Generating C++ header output...")
    tree, _ = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        quantities=quantities,
        units=units,
        types=types,
        overlays=overlays,
        strict_exceptions_file=strict_exceptions,
    )
    content = generate(tree, namespace, include_branches)
    output.write_text(content, encoding="utf-8")
    log.info(f"C++ header written to {output}")

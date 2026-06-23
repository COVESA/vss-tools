# Copyright (c) 2026 Contributors to COVESA
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

_NODE_TYPE_ENUM: dict[str, str] = {
    "sensor": "VssNodeType::kSensor",
    "actuator": "VssNodeType::kActuator",
    "attribute": "VssNodeType::kAttribute",
    "branch": "VssNodeType::kBranch",
}

_DATATYPE_ENUM: dict[str, str] = {
    "uint8": "VssDataType::kUint8",
    "int8": "VssDataType::kInt8",
    "uint16": "VssDataType::kUint16",
    "int16": "VssDataType::kInt16",
    "uint32": "VssDataType::kUint32",
    "int32": "VssDataType::kInt32",
    "uint64": "VssDataType::kUint64",
    "int64": "VssDataType::kInt64",
    "float": "VssDataType::kFloat",
    "double": "VssDataType::kDouble",
    "boolean": "VssDataType::kBoolean",
    "string": "VssDataType::kString",
    "uint8[]": "VssDataType::kUint8Array",
    "int8[]": "VssDataType::kInt8Array",
    "uint16[]": "VssDataType::kUint16Array",
    "int16[]": "VssDataType::kInt16Array",
    "uint32[]": "VssDataType::kUint32Array",
    "int32[]": "VssDataType::kInt32Array",
    "uint64[]": "VssDataType::kUint64Array",
    "int64[]": "VssDataType::kInt64Array",
    "float[]": "VssDataType::kFloatArray",
    "double[]": "VssDataType::kDoubleArray",
    "boolean[]": "VssDataType::kBooleanArray",
    "string[]": "VssDataType::kStringArray",
    "numeric": "VssDataType::kNumeric",
    "numeric[]": "VssDataType::kNumericArray",
    "int": "VssDataType::kInt64",
}

_CPP_TYPE_ENUM: dict[str, str] = {
    "uint8_t": "VssCppType::kUint8T",
    "int8_t": "VssCppType::kInt8T",
    "uint16_t": "VssCppType::kUint16T",
    "int16_t": "VssCppType::kInt16T",
    "uint32_t": "VssCppType::kUint32T",
    "int32_t": "VssCppType::kInt32T",
    "uint64_t": "VssCppType::kUint64T",
    "int64_t": "VssCppType::kInt64T",
    "float": "VssCppType::kFloat",
    "double": "VssCppType::kDouble",
    "bool": "VssCppType::kBool",
    "const char*": "VssCppType::kConstCharPtr",
    "const uint8_t*": "VssCppType::kConstUint8TPtr",
    "const int8_t*": "VssCppType::kConstInt8TPtr",
    "const uint16_t*": "VssCppType::kConstUint16TPtr",
    "const int16_t*": "VssCppType::kConstInt16TPtr",
    "const uint32_t*": "VssCppType::kConstUint32TPtr",
    "const int32_t*": "VssCppType::kConstInt32TPtr",
    "const uint64_t*": "VssCppType::kConstUint64TPtr",
    "const int64_t*": "VssCppType::kConstInt64TPtr",
    "const float*": "VssCppType::kConstFloatPtr",
    "const double*": "VssCppType::kConstDoublePtr",
    "const bool*": "VssCppType::kConstBoolPtr",
    "const char* const*": "VssCppType::kConstCharConstPtr",
}


def _unit_enum_member(unit: str) -> str:
    """Convert a VSS unit string to a C++ enum member name prefixed with k."""
    s = unit
    s = s.replace("/", "_Per_")
    s = s.replace("^", "_Pow_")
    s = s.replace("°", "Deg")
    s = s.replace("%", "Pct")
    s = s.replace("-", "_Minus_")
    s = s.replace("·", "_Mul_")
    s = s.replace("*", "_Mul_")
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if s and s[0].isdigit():
        s = "n" + s
    parts = [p for p in s.split("_") if p]
    name = "".join(p[0].upper() + p[1:] for p in parts)
    return "k" + name


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _str_literal(v: object | None) -> str:
    if v is None:
        return "nullptr"
    return f'"{_escape(str(v))}"'


def _double_literal(v: object) -> str:
    try:
        return repr(float(str(v)))
    except (ValueError, TypeError):
        return "kNoValue"


def _identifier(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "_", path)


def _emit_signal(node: VSSNode, unit_map: dict[str, str]) -> list[str]:
    data = node.get_vss_data()
    fqn = node.get_fqn()
    ident = _identifier(fqn)
    datatype = str(getattr(data, "datatype", "")) or ""
    cpp_type_str = _CPP_TYPE_MAP.get(datatype, "const char*")
    unit = getattr(data, "unit", None)
    min_val = getattr(data, "min", None)
    max_val = getattr(data, "max", None)
    allowed = getattr(data, "allowed", None)
    default = getattr(data, "default", None)

    type_enum = _NODE_TYPE_ENUM.get(data.type.value, "VssNodeType::kSensor")
    datatype_enum = _DATATYPE_ENUM.get(datatype, "VssDataType::kString") if datatype else "VssDataType::kString"
    cpp_type_enum = _CPP_TYPE_ENUM.get(cpp_type_str, "VssCppType::kConstCharPtr")
    unit_enum_val = unit_map.get(unit, "VssUnit::kNone") if unit else "VssUnit::kNone"

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
    lines.append(f"    {type_enum},")
    lines.append(f"    {datatype_enum},")
    lines.append(f"    {cpp_type_enum},")
    lines.append(f"    {unit_enum_val},")
    lines.append(f"    {_str_literal(data.description)},")
    lines.append(f"    {_double_literal(min_val) if min_val is not None else 'kNoValue'},")
    lines.append(f"    {_double_literal(max_val) if max_val is not None else 'kNoValue'},")
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

    # Collect ordered unique units from the signal set
    seen_units: dict[str, str] = {}  # unit_str → enum member name
    for node in leaf_nodes:
        u = getattr(node.get_vss_data(), "unit", None)
        if u and u not in seen_units:
            seen_units[u] = _unit_enum_member(u)

    unit_map = {u: f"VssUnit::{m}" for u, m in seen_units.items()}

    out: list[str] = []
    out.append("// SPDX-FileCopyrightText: Copyright (c) 2026 Contributors to COVESA")
    out.append("// SPDX-License-Identifier: MPL-2.0")
    out.append("")
    out.append("// Auto-generated from the Vehicle Signal Specification.")
    out.append("// Do not edit manually.")
    out.append("")
    out.append("#pragma once")
    out.append("")
    out.append("#include <cstddef>")
    out.append("#include <cstdint>")
    out.append("#include <limits>")
    out.append("")
    out.append(f"namespace {namespace} {{")
    out.append("")
    out.append("constexpr double kNoValue = std::numeric_limits<double>::quiet_NaN();")
    out.append("")
    out.append("enum class VssNodeType : uint8_t {")
    out.append("    kSensor = 0,")
    out.append("    kActuator,")
    out.append("    kAttribute,")
    out.append("    kBranch,")
    out.append("};")
    out.append("")
    out.append("enum class VssDataType : uint8_t {")
    out.append("    kUnknown = 0,")
    out.append("    kUint8,")
    out.append("    kInt8,")
    out.append("    kUint16,")
    out.append("    kInt16,")
    out.append("    kUint32,")
    out.append("    kInt32,")
    out.append("    kUint64,")
    out.append("    kInt64,")
    out.append("    kFloat,")
    out.append("    kDouble,")
    out.append("    kBoolean,")
    out.append("    kString,")
    out.append("    kUint8Array,")
    out.append("    kInt8Array,")
    out.append("    kUint16Array,")
    out.append("    kInt16Array,")
    out.append("    kUint32Array,")
    out.append("    kInt32Array,")
    out.append("    kUint64Array,")
    out.append("    kInt64Array,")
    out.append("    kFloatArray,")
    out.append("    kDoubleArray,")
    out.append("    kBooleanArray,")
    out.append("    kStringArray,")
    out.append("    kNumeric,")
    out.append("    kNumericArray,")
    out.append("};")
    out.append("")
    out.append("enum class VssCppType : uint8_t {")
    out.append("    kUnknown = 0,")
    out.append("    kUint8T,")
    out.append("    kInt8T,")
    out.append("    kUint16T,")
    out.append("    kInt16T,")
    out.append("    kUint32T,")
    out.append("    kInt32T,")
    out.append("    kUint64T,")
    out.append("    kInt64T,")
    out.append("    kFloat,")
    out.append("    kDouble,")
    out.append("    kBool,")
    out.append("    kConstCharPtr,")
    out.append("    kConstUint8TPtr,")
    out.append("    kConstInt8TPtr,")
    out.append("    kConstUint16TPtr,")
    out.append("    kConstInt16TPtr,")
    out.append("    kConstUint32TPtr,")
    out.append("    kConstInt32TPtr,")
    out.append("    kConstUint64TPtr,")
    out.append("    kConstInt64TPtr,")
    out.append("    kConstFloatPtr,")
    out.append("    kConstDoublePtr,")
    out.append("    kConstBoolPtr,")
    out.append("    kConstCharConstPtr,")
    out.append("};")
    out.append("")
    out.append("enum class VssUnit : uint8_t {")
    out.append("    kNone = 0,")
    for member in seen_units.values():
        out.append(f"    {member},")
    out.append("};")
    out.append("")
    out.append("struct VssSignal {")
    out.append("    const char* const path;")
    out.append("    VssNodeType type;")
    out.append("    VssDataType datatype;")
    out.append("    VssCppType cpp_type;")
    out.append("    VssUnit unit;")
    out.append("    const char* const description;")
    out.append("    double min_value;   // kNoValue if unset")
    out.append("    double max_value;   // kNoValue if unset")
    out.append("    const char* const* const allowed_values;  // null-terminated, or nullptr")
    out.append("    const char* const default_value;")
    out.append("};")
    out.append("")

    for node in leaf_nodes:
        for line in _emit_signal(node, unit_map):
            out.append(line)
        out.append("")

    out.append("constexpr VssSignal kSignals[] = {")
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

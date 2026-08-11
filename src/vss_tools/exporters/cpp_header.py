# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Export VSS tree as a C++ header-only file suitable for embedding in
# binaries with no filesystem dependency (e.g. microcontrollers).

import fnmatch
import re
from pathlib import Path

import rich_click as click
from anytree import PreOrderIter
from jinja2 import Environment, FileSystemLoader

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.datatypes import Datatypes, is_array
from vss_tools.main import get_trees
from vss_tools.model import VSSDataBranch
from vss_tools.tree import VSSNode

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)

# Base (non-array) VSS datatype -> C++ type. Derived from the datatype names
# themselves; vss_tools.datatypes.Datatypes is the single source of truth for
# which datatypes exist, so adding one there is enough to cover it here too.
_BASE_CPP_TYPE: dict[str, str] = {
    "uint8": "uint8_t",
    "int8": "int8_t",
    "uint16": "uint16_t",
    "int16": "int16_t",
    "uint32": "uint32_t",
    "int32": "int32_t",
    "uint64": "uint64_t",
    "int64": "int64_t",
    "float": "float",
    "double": "double",
    "boolean": "bool",
    "string": "const char*",
    "numeric": "double",
    "int": "int64_t",
}


def _cpp_type_for(datatype: str) -> str:
    if is_array(datatype):
        base = _BASE_CPP_TYPE[datatype.removesuffix("[]")]
        # "const char*" arrays are "const char* const*", not "const const char**"
        return "const char* const*" if base == "const char*" else f"const {base}*"
    return _BASE_CPP_TYPE[datatype]


_CPP_TYPE_MAP: dict[str, str] = {t[0]: _cpp_type_for(t[0]) for t in Datatypes.types}

_NODE_TYPE_ENUM: dict[str, str] = {
    "sensor": "kSensor",
    "actuator": "kActuator",
    "attribute": "kAttribute",
    "branch": "kBranch",
}

_DATATYPE_ENUM: dict[str, str] = {
    "uint8": "kUint8",
    "int8": "kInt8",
    "uint16": "kUint16",
    "int16": "kInt16",
    "uint32": "kUint32",
    "int32": "kInt32",
    "uint64": "kUint64",
    "int64": "kInt64",
    "float": "kFloat",
    "double": "kDouble",
    "boolean": "kBoolean",
    "string": "kString",
    "uint8[]": "kUint8Array",
    "int8[]": "kInt8Array",
    "uint16[]": "kUint16Array",
    "int16[]": "kInt16Array",
    "uint32[]": "kUint32Array",
    "int32[]": "kInt32Array",
    "uint64[]": "kUint64Array",
    "int64[]": "kInt64Array",
    "float[]": "kFloatArray",
    "double[]": "kDoubleArray",
    "boolean[]": "kBooleanArray",
    "string[]": "kStringArray",
    "numeric": "kNumeric",
    "numeric[]": "kNumericArray",
    "int": "kInt64",
}

_CPP_TYPE_ENUM: dict[str, str] = {
    "uint8_t": "kUint8T",
    "int8_t": "kInt8T",
    "uint16_t": "kUint16T",
    "int16_t": "kInt16T",
    "uint32_t": "kUint32T",
    "int32_t": "kInt32T",
    "uint64_t": "kUint64T",
    "int64_t": "kInt64T",
    "float": "kFloat",
    "double": "kDouble",
    "bool": "kBool",
    "const char*": "kConstCharPtr",
    "const uint8_t*": "kConstUint8TPtr",
    "const int8_t*": "kConstInt8TPtr",
    "const uint16_t*": "kConstUint16TPtr",
    "const int16_t*": "kConstInt16TPtr",
    "const uint32_t*": "kConstUint32TPtr",
    "const int32_t*": "kConstInt32TPtr",
    "const uint64_t*": "kConstUint64TPtr",
    "const int64_t*": "kConstInt64TPtr",
    "const float*": "kConstFloatPtr",
    "const double*": "kConstDoublePtr",
    "const bool*": "kConstBoolPtr",
    "const char* const*": "kConstCharConstPtr",
}


def _unit_enum_member(unit: str) -> str:
    """
    Convert a VSS unit string to a C++ enum member name prefixed with k.

    Only handles characters that actually occur in spec/units.yaml today:
    '/' (cm/s^2), '^' (m/s^2), '-' (mpg-uk). No VSS unit uses '°', '%',
    '·' or '*' (those are spelled out, e.g. "percent", "degrees").
    """
    s = unit
    s = s.replace("/", "_Per_")
    s = s.replace("^", "_Pow_")
    s = s.replace("-", "_Minus_")
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


def _signal_context(node: VSSNode, unit_map: dict[str, str]) -> dict[str, object]:
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

    return {
        "ident": ident,
        "fqn": _str_literal(fqn),
        "type_enum": _NODE_TYPE_ENUM.get(data.type.value, "kSensor"),
        "datatype_enum": _DATATYPE_ENUM.get(datatype, "kString") if datatype else "kString",
        "cpp_type_enum": _CPP_TYPE_ENUM.get(cpp_type_str, "kConstCharPtr"),
        "unit_enum": unit_map.get(unit, "kNone") if unit else "kNone",
        "description": _str_literal(data.description),
        "min_value": _double_literal(min_val) if min_val is not None else "kNoValue",
        "max_value": _double_literal(max_val) if max_val is not None else "kNoValue",
        "allowed": [f'"{_escape(str(v))}"' for v in allowed] if allowed else None,
        "allowed_ref": f"{ident}_kAllowed" if allowed else "nullptr",
        "default_value": _str_literal(default),
    }


def generate(
    root: VSSNode,
    namespace: str,
    include_branches: bool,
    signal_patterns: tuple[str, ...] = (),
) -> str:
    all_nodes = [n for n in PreOrderIter(root) if n.parent is not None]

    if signal_patterns:
        leaf_nodes = [
            n
            for n in all_nodes
            if not isinstance(n.data, VSSDataBranch)
            and any(fnmatch.fnmatch(n.get_fqn(), pattern) for pattern in signal_patterns)
        ]
        if not leaf_nodes:
            log.warning(f"No signals matched --signal filter(s): {', '.join(signal_patterns)}")
        emitted_nodes = leaf_nodes
        if include_branches:
            # Only pull in branches that are actual ancestors of a matched
            # signal, not every branch in the tree - that would defeat the
            # point of filtering for embedded/MCU memory footprint.
            wanted_branches: set[VSSNode] = set()
            for n in leaf_nodes:
                parent = n.parent
                while parent is not None and parent.parent is not None:
                    wanted_branches.add(parent)
                    parent = parent.parent
            emitted_set = set(leaf_nodes) | wanted_branches
            emitted_nodes = [n for n in all_nodes if n in emitted_set]
    else:
        emitted_nodes = [n for n in all_nodes if include_branches or not isinstance(n.data, VSSDataBranch)]

    # Collect ordered unique units from the emitted signal set
    seen_units: dict[str, str] = {}  # unit_str -> enum member name
    for node in emitted_nodes:
        u = getattr(node.get_vss_data(), "unit", None)
        if u and u not in seen_units:
            seen_units[u] = _unit_enum_member(u)

    signals = [_signal_context(node, seen_units) for node in emitted_nodes]

    template = _ENV.get_template("cpp_header.hpp.j2")
    return template.render(
        namespace=namespace,
        units=list(seen_units.values()),
        signals=signals,
    )


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
@click.option(
    "--signal",
    "signals",
    multiple=True,
    default=(),
    help=(
        "Restrict output to specific signal paths (dotted, glob '*' supported, e.g. "
        "'Vehicle.ADAS.*'). Repeatable. If --include-branches is set, only the "
        "ancestor branches of matched signals are included. Omit to export every signal."
    ),
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
    signals: tuple[str],
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
    content = generate(tree, namespace, include_branches, signals)
    output.write_text(content, encoding="utf-8")
    log.info(f"C++ header written to {output}")

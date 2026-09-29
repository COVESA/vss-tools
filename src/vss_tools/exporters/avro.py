# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""AVRO IDL (.avdl) exporter for VSS struct definitions.

Each top-level struct in the provided ``--types`` files is written to its own
``.avdl`` file inside the output directory.  The file contains:

1. Enum declarations (one per property with ``allowed`` values).
2. Record declarations for every struct the top-level struct depends on,
   either because it is nested as a tree child or because a property's
   ``datatype`` references it directly (e.g. ``datatype: Types.Address`` or
   ``datatype: Types.Address[]``), declared bottom-up so each type is
   declared before use.
3. The main record.
4. An optional array-container record (``--include-array-record``).
"""

from __future__ import annotations

from pathlib import Path

import caseconverter
import inflect
import rich_click as click
from anytree import findall

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.main import get_trees
from vss_tools.model import VSSDataProperty, VSSDataStruct
from vss_tools.tree import VSSNode

# ---------------------------------------------------------------------------
# VSS → Avro primitive type mapping
# ---------------------------------------------------------------------------

_VSS_TO_AVRO: dict[str, str] = {
    "uint8": "int",
    "int8": "int",
    "uint16": "int",
    "int16": "int",
    "int32": "int",
    "uint32": "long",
    "int64": "long",
    "uint64": "long",
    "float": "float",
    "double": "double",
    "boolean": "boolean",
    "string": "string",
}


def vss_type_to_avro(datatype: str) -> str:
    """Map a VSS primitive datatype to its Avro type name.

    Any array type (``T[]``) maps to ``bytes``.
    Raises ``ValueError`` for unknown types.
    """
    if datatype.endswith("[]"):
        return "bytes"
    mapped = _VSS_TO_AVRO.get(datatype)
    if mapped is None:
        raise ValueError(f"Unsupported VSS datatype for AVRO mapping: '{datatype}'")
    return mapped


# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------


def to_avro_field_name(name: str) -> str:
    """Convert a PascalCase VSS name to lowerCamelCase for Avro field names."""
    return caseconverter.camelcase(name)


def build_enum_name(path_segments: list[str], field_name: str) -> str:
    """Build the Avro enum type name from the struct path and the field name.

    Pattern: ``{Segment1}{Segment2}...{FieldName}Value``

    Example::

        path_segments=["Departure", "ElectricBattery"],
        field_name="PreconditioningMaxPerformance"
        → "DepartureElectricBatteryPreconditioningMaxPerformanceValue"
    """
    return "".join(path_segments) + field_name + "Value"


def ensure_unknown_first(values: list[str]) -> list[str]:
    """Return *values* with ``"UNKNOWN"`` guaranteed at index 0, without duplicates."""
    without_unknown = [v for v in values if v != "UNKNOWN"]
    return ["UNKNOWN"] + without_unknown


# ---------------------------------------------------------------------------
# Tree traversal helpers
# ---------------------------------------------------------------------------


def get_top_level_structs(data_type_tree: VSSNode) -> list[VSSNode]:
    """Return all top-level struct nodes (structs whose direct parent is not a struct)."""
    return list(
        findall(
            data_type_tree,
            filter_=lambda n: isinstance(n.data, VSSDataStruct) and not isinstance(n.parent.data, VSSDataStruct),
        )
    )


def collect_enums(struct_node: VSSNode) -> list[tuple[str, list[str]]]:
    """Collect all ``(enum_name, values)`` pairs for *struct_node*, depth-first.

    The enum name follows the pattern ``{Path...}{FieldName}Value`` so that every
    field gets a unique, unambiguous enum even when multiple fields share the same
    allowed values.
    """
    result: list[tuple[str, list[str]]] = []
    _collect_enums_recursive(struct_node, [struct_node.name], result)
    return result


def _collect_enums_recursive(
    node: VSSNode,
    path_segments: list[str],
    result: list[tuple[str, list[str]]],
) -> None:
    for child in node.children:
        if isinstance(child.data, VSSDataProperty):
            if child.data.allowed:
                enum_name = build_enum_name(path_segments, child.name)
                values = [str(v) for v in child.data.allowed]
                result.append((enum_name, ensure_unknown_first(values)))
        elif isinstance(child.data, VSSDataStruct):
            _collect_enums_recursive(child, path_segments + [child.name], result)


def collect_nested_structs_ordered(struct_node: VSSNode) -> list[VSSNode]:
    """Return nested struct nodes in post-order (leaves first).

    Post-order ensures each nested record is declared before it is referenced
    by its parent record.
    """
    result: list[VSSNode] = []
    _collect_nested_postorder(struct_node, result)
    return result


def _collect_nested_postorder(node: VSSNode, result: list[VSSNode]) -> None:
    for child in node.children:
        if isinstance(child.data, VSSDataStruct):
            _collect_nested_postorder(child, result)
            result.append(child)


def _path_from_toplevel(node: VSSNode) -> list[str]:
    """Return path segments from the nearest top-level struct ancestor down to *node*.

    A top-level struct (whose parent is not itself a struct) returns
    ``[node.name]``. A struct nested inside another struct returns the full
    chain of struct names down to *node*, e.g. ``["Schedule", "Window"]``.
    Works for any struct node regardless of where it lives in the data type
    tree, which is required because a struct referenced via a property's
    ``datatype`` (see below) is not necessarily an ancestor/descendant of the
    struct that references it.
    """
    segments: list[str] = [node.name]
    current = node
    while current.parent is not None and isinstance(current.parent.data, VSSDataStruct):
        current = current.parent
        segments.append(current.name)
    return list(reversed(segments))


# ---------------------------------------------------------------------------
# Struct-reference resolution
# ---------------------------------------------------------------------------
#
# A struct property's ``datatype`` may reference another struct instead of a
# primitive, e.g. ``datatype: Types.Address`` or ``datatype: Types.Address[]``.
# vss-tools' core model already validates and loads such references (self- and
# circular references are rejected upstream by vss-tools itself), but this
# exporter previously only inlined structs that were *nested* as direct tree
# children, so it crashed on this pattern with a "not a valid AVRO datatype"
# style error. The helpers below resolve these references and ensure the
# referenced struct (and anything it transitively depends on) is declared in
# the same protocol before it is used.


def _node_fqn(node: VSSNode) -> str:
    """Return the dotted fully-qualified name of *node* (root included)."""
    segments: list[str] = []
    current: VSSNode | None = node
    while current is not None:
        segments.append(current.name)
        current = current.parent
    return ".".join(reversed(segments))


def build_struct_index(data_type_tree: VSSNode) -> tuple[dict[str, VSSNode], dict[str, VSSNode]]:
    """Index every struct node under *data_type_tree* by FQN and by short name.

    Used to resolve a property's ``datatype`` when it references another
    struct (e.g. ``datatype: Types.Address``) instead of a primitive.
    """
    by_fqn: dict[str, VSSNode] = {}
    by_short: dict[str, VSSNode] = {}
    for node in findall(data_type_tree, filter_=lambda n: isinstance(n.data, VSSDataStruct)):
        by_fqn[_node_fqn(node)] = node
        # First writer wins for short names; ambiguous short names across
        # distinct structs are rare in practice and are unambiguous when
        # referenced by their fully-qualified name instead.
        by_short.setdefault(node.name, node)
    return by_fqn, by_short


def resolve_struct_datatype(
    datatype: str,
    by_fqn: dict[str, VSSNode],
    by_short: dict[str, VSSNode],
) -> tuple[VSSNode | None, bool]:
    """Resolve *datatype* to a struct node if it references one.

    Returns ``(struct_node, is_array)`` when *datatype* (optionally suffixed
    with ``[]`` for an array of structs) matches a known struct by
    fully-qualified or short name. Returns ``(None, is_array)`` when
    *datatype* is a primitive (or an array of a primitive), in which case the
    caller should fall back to :func:`vss_type_to_avro`.
    """
    is_array = datatype.endswith("[]")
    base = datatype[:-2] if is_array else datatype
    node = by_fqn.get(base) or by_short.get(base)
    return node, is_array


def _struct_dependencies(
    node: VSSNode,
    by_fqn: dict[str, VSSNode],
    by_short: dict[str, VSSNode],
) -> list[VSSNode]:
    """Direct struct dependencies of *node*.

    Includes both structs nested as tree children and structs referenced by a
    property's ``datatype`` (single struct or array-of-struct reference).
    """
    deps: list[VSSNode] = []
    for child in node.children:
        if isinstance(child.data, VSSDataStruct):
            deps.append(child)
        elif isinstance(child.data, VSSDataProperty) and not child.data.allowed:
            ref, _ = resolve_struct_datatype(child.data.datatype, by_fqn, by_short)
            if ref is not None:
                deps.append(ref)
    return deps


def collect_records_ordered(
    top: VSSNode,
    by_fqn: dict[str, VSSNode],
    by_short: dict[str, VSSNode],
) -> list[VSSNode]:
    """Return every struct node that must be declared for *top*, dependencies first.

    Combines nested tree children and structs referenced via ``datatype`` into
    a single dependency-ordered (post-order), de-duplicated list: each
    record is declared only after every record it depends on. *top* itself is
    always the last element.

    Cycle-safe: a struct that (directly or transitively) depends on itself is
    only visited once. In practice vss-tools' own model validation already
    rejects self-referential and circular struct definitions before this
    exporter runs, so this guard mainly protects against future model changes
    rather than a case reachable via a valid vspec file today.
    """
    order: list[VSSNode] = []
    done: set[str] = set()
    stack: set[str] = set()

    def visit(node: VSSNode) -> None:
        key = _node_fqn(node)
        if key in done or key in stack:
            return
        stack.add(key)
        for dep in _struct_dependencies(node, by_fqn, by_short):
            visit(dep)
        stack.discard(key)
        done.add(key)
        order.append(node)

    visit(top)
    return order


def _direct_enums(node: VSSNode, path_segments: list[str]) -> list[tuple[str, list[str]]]:
    """Return ``(enum_name, values)`` pairs for the direct ``allowed`` properties of *node*.

    Unlike :func:`collect_enums`, this does not recurse into nested structs.
    It is meant to be called once per record while assembling a protocol so
    that every record's own enums are collected exactly once, regardless of
    whether that record is the main struct, a nested struct, or a struct
    reached through a ``datatype`` reference.
    """
    result: list[tuple[str, list[str]]] = []
    for child in node.children:
        if isinstance(child.data, VSSDataProperty) and child.data.allowed:
            enum_name = build_enum_name(path_segments, child.name)
            values = [str(v) for v in child.data.allowed]
            result.append((enum_name, ensure_unknown_first(values)))
    return result


# ---------------------------------------------------------------------------
# AVDL rendering helpers
# ---------------------------------------------------------------------------


def _generate_record_fields(
    struct_node: VSSNode,
    path_segments: list[str],
    by_fqn: dict[str, VSSNode],
    by_short: dict[str, VSSNode],
) -> list[str]:
    """Generate ``union { null, T } fieldName;`` lines for each direct child of *struct_node*.

    *path_segments* is the list of struct names from the top-level struct down
    to *struct_node* (inclusive) and is used to build enum type names.
    *by_fqn* / *by_short* (see :func:`build_struct_index`) are used to resolve
    a property's ``datatype`` when it references another struct rather than a
    primitive.
    """
    fields: list[str] = []
    for child in struct_node.children:
        field_name = to_avro_field_name(child.name)
        if isinstance(child.data, VSSDataStruct):
            avro_type = child.name  # reference nested record by its short name
        elif isinstance(child.data, VSSDataProperty):
            data = child.data
            if data.allowed:
                avro_type = build_enum_name(path_segments, child.name)
            else:
                ref, is_array = resolve_struct_datatype(data.datatype, by_fqn, by_short)
                if ref is not None:
                    avro_type = f"array<{ref.name}>" if is_array else ref.name
                else:
                    avro_type = vss_type_to_avro(data.datatype)
        else:
            continue
        fields.append(f"union {{ null, {avro_type} }} {field_name};")
    return fields


def _render_record_lines(record_name: str, field_lines: list[str]) -> list[str]:
    lines = [f"    record {record_name} {{"]
    for line in field_lines:
        lines.append(f"        {line}")
    lines.append("    }")
    return lines


# ---------------------------------------------------------------------------
# Protocol generator
# ---------------------------------------------------------------------------


def generate_protocol(
    struct_node: VSSNode,
    namespace: str,
    include_array: bool,
    plural_engine: inflect.engine,
    by_fqn: dict[str, VSSNode] | None = None,
    by_short: dict[str, VSSNode] | None = None,
) -> str:
    """Generate the complete ``.avdl`` text for a single top-level struct.

    Declaration order (per AVDL best practices):

    1. Enums (one per record with ``allowed`` fields, dependency order)
    2. Dependency records: nested structs and structs referenced via a
       property's ``datatype`` (post-order so each is declared before use)
    3. Main record
    4. Array container record (only when *include_array* is ``True``)

    *by_fqn* / *by_short* are the struct index built by
    :func:`build_struct_index`, used to resolve struct-typed ``datatype``
    references anywhere in the wider data type tree. When omitted, an index
    scoped to *struct_node*'s own subtree is built instead, which only
    resolves nested (tree-child) structs; a struct referenced via ``datatype``
    from outside that subtree still raises ``ValueError``, exactly like
    before this feature was added. The CLI always builds and passes the full
    index so this limitation is never hit in practice.
    """
    if by_fqn is None or by_short is None:
        by_fqn, by_short = build_struct_index(struct_node)

    struct_name = struct_node.name
    ns_full = f"{namespace}.{struct_name.lower()}"

    records = collect_records_ordered(struct_node, by_fqn, by_short)

    lines: list[str] = []
    lines.append(f'@namespace("{ns_full}")')
    lines.append(f"protocol {struct_name} {{")
    lines.append("")

    # 1. Enums (declared once per record, in dependency order)
    seen_enums: set[str] = set()
    for record in records:
        path_segments = _path_from_toplevel(record)
        for enum_name, values in _direct_enums(record, path_segments):
            if enum_name in seen_enums:
                continue
            seen_enums.add(enum_name)
            lines.append(f"    enum {enum_name} {{")
            for i, v in enumerate(values):
                suffix = "," if i < len(values) - 1 else ""
                lines.append(f"        {v}{suffix}")
            lines.append("    } = UNKNOWN;")
            lines.append("")

    # 2. Dependency records (post-order: leaves/references first)
    for record in records[:-1]:
        path_segs = _path_from_toplevel(record)
        fields = _generate_record_fields(record, path_segs, by_fqn, by_short)
        lines.extend(_render_record_lines(record.name, fields))
        lines.append("")

    # 3. Main record
    main_fields = _generate_record_fields(struct_node, [struct_node.name], by_fqn, by_short)
    lines.extend(_render_record_lines(struct_name, main_fields))

    # 4. Array container record (optional)
    if include_array:
        lines.append("")
        array_name = f"{struct_name}Array"
        field_singular = to_avro_field_name(struct_name)
        field_plural = plural_engine.plural(field_singular)
        lines.append(f"    record {array_name} {{")
        lines.append(f"        array<{struct_name}> {field_plural};")
        lines.append("    }")

    lines.append("}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command()
@clo.vspec_opt
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    required=True,
    help="Output directory for generated .avdl files.",
)
@click.option(
    "--namespace",
    required=True,
    help="AVRO namespace prefix (e.g. com.example.vss.struct).",
)
@click.option(
    "--file-prefix",
    default="",
    show_default=True,
    help="Prefix for each output filename (e.g. 'struct' → structLocation.avdl).",
)
@click.option(
    "--include-array-record/--no-include-array-record",
    default=False,
    show_default=True,
    help="Generate an array container record for each struct.",
)
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@clo.strict_exceptions_opt
@click.pass_context
def cli(
    ctx: click.Context,
    vspec: Path,
    output: Path,
    namespace: str,
    file_prefix: str,
    include_array_record: bool,
    include_dirs: tuple[Path, ...],
    extended_attributes: tuple[str, ...],
    strict: bool,
    aborts: tuple[str, ...],
    overlays: tuple[Path, ...],
    quantities: tuple[Path, ...],
    units: tuple[Path, ...],
    types: tuple[Path, ...],
    strict_exceptions: Path | None,
) -> None:
    """Export VSS struct definitions to AVRO IDL (.avdl) files."""
    if not types:
        raise click.ClickException("At least one --types / -t file must be provided for AVRO export.")

    _, data_type_tree = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        quantities=quantities,
        units=units,
        types=types,
        overlays=overlays,
        expand=False,
        strict_exceptions_file=strict_exceptions,
    )

    if data_type_tree is None:
        raise click.ClickException("No data type tree was loaded. Check your --types files.")

    output.mkdir(parents=True, exist_ok=True)
    plural_engine = inflect.engine()
    by_fqn, by_short = build_struct_index(data_type_tree)
    structs = get_top_level_structs(data_type_tree)

    if not structs:
        log.warning("No top-level structs found in the provided --types files.")
        return

    log.info(f"Generating AVRO IDL for {len(structs)} struct(s) into '{output}'...")
    for struct_node in structs:
        content = generate_protocol(struct_node, namespace, include_array_record, plural_engine, by_fqn, by_short)
        filename = f"{file_prefix}{struct_node.name}.avdl"
        out_path = output / filename
        out_path.write_text(content, encoding="utf-8")
        log.debug(f"  Written: {out_path}")

    log.info("AVRO IDL export complete.")

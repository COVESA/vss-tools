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
2. Nested record declarations (bottom-up so each type is declared before use).
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


def _get_path_segments(node: VSSNode, top_level: VSSNode) -> list[str]:
    """Return path segment names from *top_level* down to *node* (both inclusive)."""
    segments: list[str] = []
    current: VSSNode = node
    while current is not top_level:
        segments.append(current.name)
        current = current.parent  # type: ignore[assignment]
    segments.append(top_level.name)
    return list(reversed(segments))


# ---------------------------------------------------------------------------
# AVDL rendering helpers
# ---------------------------------------------------------------------------


def _generate_record_fields(struct_node: VSSNode, path_segments: list[str]) -> list[str]:
    """Generate ``union { null, T } fieldName;`` lines for each direct child of *struct_node*.

    *path_segments* is the list of struct names from the top-level struct down
    to *struct_node* (inclusive) and is used to build enum type names.
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
) -> str:
    """Generate the complete ``.avdl`` text for a single top-level struct.

    Declaration order (per AVDL best practices):

    1. Enums (depth-first, one per field with ``allowed`` values)
    2. Nested records (post-order so leaves are declared before parents)
    3. Main record
    4. Array container record (only when *include_array* is ``True``)
    """
    struct_name = struct_node.name
    ns_full = f"{namespace}.{struct_name.lower()}"

    lines: list[str] = []
    lines.append(f'@namespace("{ns_full}")')
    lines.append(f"protocol {struct_name} {{")
    lines.append("")

    # 1. Enums
    for enum_name, values in collect_enums(struct_node):
        lines.append(f"    enum {enum_name} {{")
        for i, v in enumerate(values):
            suffix = "," if i < len(values) - 1 else ""
            lines.append(f"        {v}{suffix}")
        lines.append("    } = UNKNOWN;")
        lines.append("")

    # 2. Nested records (post-order: leaves first)
    for nested in collect_nested_structs_ordered(struct_node):
        path_segs = _get_path_segments(nested, struct_node)
        fields = _generate_record_fields(nested, path_segs)
        lines.extend(_render_record_lines(nested.name, fields))
        lines.append("")

    # 3. Main record
    main_fields = _generate_record_fields(struct_node, [struct_node.name])
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
    structs = get_top_level_structs(data_type_tree)

    if not structs:
        log.warning("No top-level structs found in the provided --types files.")
        return

    log.info(f"Generating AVRO IDL for {len(structs)} struct(s) into '{output}'...")
    for struct_node in structs:
        content = generate_protocol(struct_node, namespace, include_array_record, plural_engine)
        filename = f"{file_prefix}{struct_node.name}.avdl"
        out_path = output / filename
        out_path.write_text(content, encoding="utf-8")
        log.debug(f"  Written: {out_path}")

    log.info("AVRO IDL export complete.")

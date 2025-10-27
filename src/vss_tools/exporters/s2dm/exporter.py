# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict

import pandas as pd
import rich_click as click
from caseconverter import DELIMITERS, pascalcase
from graphql import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLID,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.datatypes import dynamic_units
from vss_tools.main import get_trees
from vss_tools.tree import VSSNode
from vss_tools.utils.graphql_directive_processor import GraphQLDirectiveProcessor
from vss_tools.utils.graphql_scalars import VSS_DATATYPE_MAP, get_vss_scalar_types
from vss_tools.utils.graphql_utils import (
    DEFAULT_CONVERSIONS,
    GraphQLElementType,
    convert_name_for_graphql_schema,
    load_predefined_schema_elements,
)
from vss_tools.utils.modular_export_utils import (
    analyze_schema_for_flat_domains,
    analyze_schema_for_nested_domains,
    write_common_files,
    write_domain_files,
)
from vss_tools.utils.pandas_utils import get_metadata_df
from vss_tools.utils.string_conversion_utils import handle_fqn_conversion

# S2DM-specific conversions that override defaults for FQN handling
# For type-like elements, we use standard delimiters (without dots) so FQNs are handled correctly
# For other elements, we inherit the DEFAULT behavior (includes dot delimiter support)


def get_s2dm_conversions() -> Dict[GraphQLElementType, Callable[[str], str]]:
    """Get S2DM conversions with proper enum instances."""
    s2dm_conversions = DEFAULT_CONVERSIONS.copy()
    s2dm_conversions.update(
        {
            # Override type-like elements to handle FQNs (Vehicle.Body -> Vehicle_Body)
            # Use standard delimiters (space, dash, underscore) but NOT dots for FQN names
            GraphQLElementType.TYPE: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.INTERFACE: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.UNION: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.INPUT: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.ENUM: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
        }
    )
    return s2dm_conversions


# Create the conversions dictionary
S2DM_CONVERSIONS = get_s2dm_conversions()


class S2DMExporterException(Exception):
    """Exception raised for errors in the S2DM export process."""

    pass


# Load predefined schema elements from directory
BASE_SCHEMA, CUSTOM_DIRECTIVES = load_predefined_schema_elements(Path(__file__).parent / "predefined_elements")

# Custom directives loaded from SDL
VSpecDirective = CUSTOM_DIRECTIVES["vspec"]
RangeDirective = CUSTOM_DIRECTIVES["range"]
InstanceTagDirective = CUSTOM_DIRECTIVES["instanceTag"]

# Initialize directive processor
directive_processor = GraphQLDirectiveProcessor()


@click.command()
@clo.vspec_opt
@clo.output_file_or_dir_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.modular_opt
@clo.flat_domains_opt
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path, ...],
    extended_attributes: tuple[str, ...],
    strict: bool,
    aborts: tuple[str, ...],
    overlays: tuple[Path, ...],
    quantities: tuple[Path, ...],
    units: tuple[Path, ...],
    modular: bool,
    flat_domains: bool,
) -> None:
    """Export a VSS specification to S2DM GraphQL schema."""
    try:
        tree, _ = get_trees(
            vspec=vspec,
            include_dirs=include_dirs,
            aborts=aborts,
            strict=strict,
            extended_attributes=extended_attributes,
            quantities=quantities,
            units=units,
            overlays=overlays,
            expand=False,
        )

        log.info("Generating S2DM GraphQL schema...")

        # Generate the schema
        schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments = generate_s2dm_schema(tree)

        if modular:
            # Handle directory or file path for modular output
            if output.is_dir():
                output_dir = output
            else:
                output_dir = output.parent / output.stem if output.suffix else output
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create modular_spec directory and write modular files
            modular_spec_dir = output_dir
            write_modular_schema(
                schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments, modular_spec_dir, flat_domains
            )
            log.info(f"Modular files written to {modular_spec_dir}")
        else:
            # Single file export (default behavior)
            full_schema_str = print_schema_with_vspec_directives(
                schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments
            )
            # Ensure output is treated as a file
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w") as outfile:
                outfile.write(full_schema_str)

            log.info(f"S2DM GraphQL schema written to {output}")

    except S2DMExporterException as e:
        log.error(e)
        sys.exit(1)


def generate_s2dm_schema(
    tree: VSSNode,
) -> tuple[
    GraphQLSchema,
    dict[str, dict[str, dict[str, str]]],
    dict[str, dict[str, dict[str, str]]],
    dict[str, dict[str, Any]],
]:
    """Generate S2DM GraphQL schema from VSS tree."""
    branches_df, leaves_df = get_metadata_df(tree)
    vspec_comments = _init_vspec_comments()

    # Create all types in logical order
    unit_enums, unit_metadata = _create_unit_enums()
    instance_types = _create_instance_types(branches_df, vspec_comments)
    allowed_enums, allowed_metadata = _create_allowed_enums(leaves_df)

    # Combine all types
    types_registry = {**instance_types, **allowed_enums}

    # Create object types
    for fqn in branches_df.index:
        if fqn not in types_registry:
            types_registry[fqn] = _create_object_type(
                fqn, branches_df, leaves_df, types_registry, unit_enums, vspec_comments
            )

    # Assemble schema
    vehicle_type = types_registry.get("Vehicle", GraphQLString)
    query = GraphQLObjectType("Query", {"vehicle": GraphQLField(vehicle_type)})
    schema = GraphQLSchema(
        query=query,
        types=get_vss_scalar_types() + list(types_registry.values()) + list(unit_enums.values()),
        directives=[VSpecDirective, RangeDirective, InstanceTagDirective],
    )

    return schema, unit_metadata, allowed_metadata, vspec_comments


def _init_vspec_comments() -> dict[str, dict[str, Any]]:
    """
    Initialize data structure for storing VSS metadata to be rendered as GraphQL directives.

    Creates a dictionary with predefined keys for tracking comments, ranges, deprecations,
    instance tags, and VSS type information that will later be converted to @vspec directives.

    Returns:
        Dictionary with empty sub-dictionaries for each metadata category
    """
    return {
        "field_comments": {},
        "type_comments": {},
        "field_ranges": {},
        "field_deprecated": {},
        "instance_tags": {},
        "instance_tag_types": {},
        "vss_types": {},
        "field_vss_types": {},
    }


def _create_unit_enums() -> tuple[dict[str, GraphQLEnumType], dict[str, dict[str, dict[str, str]]]]:
    """
    Create GraphQL enum types for VSS units grouped by quantity kind.

    Processes the VSS dynamic units registry to generate GraphQL enums where each enum
    represents all valid units for a specific quantity (e.g., LengthUnitEnum for length).

    Returns:
        A tuple containing:
        - Dictionary mapping quantity names to their corresponding GraphQL enum types
        - Nested dictionary with unit metadata (quantity -> unit_key -> {name, key})
    """
    unit_enums = {}
    unit_metadata = {}

    for quantity, units in _get_quantity_units().items():
        enum_name = f"{convert_name_for_graphql_schema(quantity, GraphQLElementType.ENUM, S2DM_CONVERSIONS)}UnitEnum"
        values = {
            convert_name_for_graphql_schema(
                info["name"], GraphQLElementType.ENUM_VALUE, S2DM_CONVERSIONS
            ): GraphQLEnumValue(key)
            for key, info in units.items()
        }
        unit_enums[quantity] = GraphQLEnumType(enum_name, values, description=f'Units for "{quantity}"')
        unit_metadata[quantity] = units

    return unit_enums, unit_metadata


def _get_quantity_units() -> dict[str, dict[str, dict[str, str]]]:
    """
    Extract and organize units from VSS dynamic units registry by quantity kind.

    Leverages the VSSUnit.key field to directly access the unit key without
    needing to deduplicate or search through the registry.

    Returns:
        Nested dictionary: quantity -> unit_key -> {name: display_name, key: unit_key}
    """
    quantity_units: dict[str, dict[str, dict[str, str]]] = {}
    processed_units = set()

    for unit_key, unit_data in dynamic_units.items():
        # Skip if we've already processed this VSSUnit object
        unit_id = id(unit_data)
        if unit_id in processed_units:
            continue

        quantity = unit_data.quantity
        unit_display_name = unit_data.unit
        actual_unit_key = unit_data.key or unit_key  # Use the key field if available

        if quantity and unit_display_name:
            if quantity not in quantity_units:
                quantity_units[quantity] = {}

            quantity_units[quantity][actual_unit_key] = {"name": unit_display_name, "key": actual_unit_key}
            processed_units.add(unit_id)

    return quantity_units


def _create_allowed_enums(
    leaves_df: pd.DataFrame,
) -> tuple[dict[str, GraphQLEnumType], dict[str, dict[str, dict[str, str]]]]:
    """
    Create GraphQL enum types for VSS signals with allowed value constraints.

    Scans leaf nodes to identify those with 'allowed' values defined and generates
    corresponding GraphQL enum types to enforce these constraints in the schema.

    Args:
        leaves_df: DataFrame containing VSS leaf node metadata

    Returns:
        A tuple containing:
        - Dictionary mapping enum type names to GraphQL enum types
        - Nested dictionary with enum metadata (enum_name -> {fqn, allowed_values})
    """
    enums, metadata = {}, {}

    for fqn, row in leaves_df[leaves_df["allowed"].notna()].iterrows():
        if allowed := row.get("allowed"):
            enum_name = f"{convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)}_Enum"
            values = {_clean_enum_name(str(v)): GraphQLEnumValue(v) for v in allowed}
            enums[enum_name] = GraphQLEnumType(enum_name, values, description=f"Allowed values for {fqn}.")
            metadata[enum_name] = {"fqn": fqn, "allowed_values": {_clean_enum_name(str(v)): str(v) for v in allowed}}

    return enums, metadata


def _clean_enum_name(value: str) -> str:
    """
    Sanitize enum value names to comply with GraphQL naming rules.

    GraphQL enum values must start with a letter and cannot contain dots or hyphens.
    This function prefixes numeric values and replaces invalid characters.

    Args:
        value: Original enum value string

    Returns:
        GraphQL-compliant enum value name
    """
    if value[0].isdigit():
        value = f"_{value}"
    return value.replace(".", "_DOT_").replace("-", "_DASH_")


def _create_instance_types(
    branches_df: pd.DataFrame, vspec_comments: dict[str, dict[str, Any]]
) -> dict[str, GraphQLEnumType | GraphQLObjectType]:
    """
    Create GraphQL types for VSS instance-based branches.

    For branches with instance declarations (e.g., Row[1,2], ["Left", "Right"]),
    generates instance tag enums and object types to represent the dimensional
    structure of instances in the GraphQL schema.

    Args:
        branches_df: DataFrame containing VSS branch node metadata
        vspec_comments: Dictionary to store instance tag metadata

    Returns:
        Dictionary mapping type names to GraphQL enum or object types
    """
    types: dict[str, GraphQLEnumType | GraphQLObjectType] = {}
    for fqn, row in branches_df[branches_df["instances"].notna()].iterrows():
        if instances := row.get("instances"):
            base_name = convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)
            tag_name = f"{base_name}_InstanceTag"

            dimensions = _parse_instances_simple(instances)
            fields = {}
            for i, values in enumerate(dimensions, 1):
                enum_name = f"{tag_name}_Dimension{i}"
                types[enum_name] = GraphQLEnumType(
                    enum_name,
                    {v: GraphQLEnumValue(v) for v in values},
                    description=f"Dimensional enum for VSS instance dimension {i}.",
                )
                fields[f"dimension{i}"] = GraphQLField(types[enum_name])

            types[tag_name] = GraphQLObjectType(tag_name, fields)
            vspec_comments["instance_tags"][tag_name] = True
            vspec_comments.setdefault("instance_tag_types", {})[base_name] = tag_name

    return types


def _parse_instances_simple(instances: list[Any]) -> list[list[str]]:
    """
    Parse VSS instance declarations into dimensional arrays.

    Converts VSS instance notation (e.g., "Row[1,4]", ["Left", "Right"]) into
    a list of dimensions where each dimension contains the expanded instance values.

    Args:
        instances: List of VSS instance declarations (ranges or literal lists)

    Returns:
        List of dimensions, where each dimension is a list of instance values
    """
    if all(isinstance(item, str) and "[" not in item for item in instances):
        return [instances]  # Single dimension

    dimensions = []
    for item in instances:
        if isinstance(item, str) and "[" in item:
            base = item.split("[")[0]
            range_part = item.split("[")[1].split("]")[0]
            start, end = map(int, range_part.split(","))
            dimensions.append([f"{base}{i}" for i in range(start, end + 1)])
        elif isinstance(item, list):
            dimensions.append(item)

    return dimensions


def _create_object_type(
    fqn: str,
    branches_df: pd.DataFrame,
    leaves_df: pd.DataFrame,
    types_registry: dict[str, Any],
    unit_enums: dict[str, GraphQLEnumType],
    vspec_comments: dict[str, dict[str, Any]],
) -> GraphQLObjectType:
    """Create GraphQL object type with inline field processing."""
    branch_row = branches_df.loc[fqn]
    type_name = convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)

    # Store type metadata
    vspec_comments["vss_types"][type_name] = {"fqn": fqn, "vspec_type": "BRANCH"}
    if comment := branch_row.get("comment"):
        vspec_comments["type_comments"][type_name] = comment

    def get_fields() -> dict[str, GraphQLField]:
        fields = {}

        # System fields
        if type_name == "Vehicle" or branch_row.get("instances"):
            fields["id"] = GraphQLField(GraphQLNonNull(GraphQLID))
        if instance_tag_type := vspec_comments.get("instance_tag_types", {}).get(type_name):
            if instance_tag_type in types_registry:
                fields["instanceTag"] = GraphQLField(types_registry[instance_tag_type])

        # Leaf fields with inline metadata
        for child_fqn, leaf_row in leaves_df[leaves_df["parent"] == fqn].iterrows():
            field_name = convert_name_for_graphql_schema(leaf_row["name"], GraphQLElementType.FIELD, S2DM_CONVERSIONS)
            field_path = f"{type_name}.{field_name}"

            # Store metadata inline
            if leaf_type := leaf_row.get("type", "").upper():
                if leaf_type in ["SENSOR", "ACTUATOR", "ATTRIBUTE"]:
                    vspec_comments["field_vss_types"][field_path] = {"fqn": child_fqn, "vspec_type": leaf_type}
            if comment := leaf_row.get("comment"):
                vspec_comments["field_comments"][field_path] = comment

            # Handle range constraints
            min_val = leaf_row.get("min")
            max_val = leaf_row.get("max")
            if min_val is not None or max_val is not None:
                range_data = {k: v for k, v in {"min": min_val, "max": max_val}.items() if v is not None}
                vspec_comments["field_ranges"][field_path] = range_data

            if deprecation := leaf_row.get("deprecation"):
                vspec_comments["field_deprecated"][field_path] = deprecation

            field_type = get_graphql_type_for_leaf(leaf_row, types_registry)
            unit_args = _get_unit_args(leaf_row, unit_enums)
            fields[field_name] = GraphQLField(field_type, args=unit_args, description=leaf_row.get("description", ""))

        # Branch fields
        for child_fqn, child_row in branches_df[branches_df["parent"] == fqn].iterrows():
            field_name = convert_name_for_graphql_schema(child_row["name"], GraphQLElementType.FIELD, S2DM_CONVERSIONS)
            child_type = types_registry.get(child_fqn) or _create_object_type(
                child_fqn, branches_df, leaves_df, types_registry, unit_enums, vspec_comments
            )
            types_registry[child_fqn] = child_type

            if child_row.get("instances"):
                fields[f"{field_name}_s"] = GraphQLField(GraphQLList(child_type))
            else:
                fields[field_name] = GraphQLField(child_type)

        return fields

    return GraphQLObjectType(name=type_name, fields=get_fields, description=branch_row.get("description", ""))


def _get_unit_args(leaf_row: pd.Series, unit_enums: dict[str, GraphQLEnumType]) -> dict[str, GraphQLArgument]:
    """
    Generate GraphQL field arguments for unit selection.

    If a VSS leaf has a unit defined, creates a 'unit' argument with the appropriate
    enum type and default value, allowing clients to request values in different units.

    Args:
        leaf_row: Pandas Series containing leaf node metadata
        unit_enums: Dictionary of GraphQL enum types for units by quantity

    Returns:
        Dictionary with 'unit' argument if applicable, empty dict otherwise
    """
    unit = leaf_row.get("unit", "")
    if not unit or unit not in dynamic_units:
        return {}

    unit_data = dynamic_units[unit]
    if not unit_data.quantity:
        return {}

    unit_enum = unit_enums.get(unit_data.quantity)
    if not unit_enum:
        return {}

    return {"unit": GraphQLArgument(type_=unit_enum, default_value=unit)}


def print_schema_with_vspec_directives(
    schema: GraphQLSchema,
    unit_enums_metadata: dict[str, Any],
    allowed_enums_metadata: dict[str, Any],
    vspec_comments: dict[str, Any],
) -> str:
    """
    Custom schema printer that includes @vspec directives.

    Args:
        schema: The GraphQL schema to print
        unit_enums_metadata: Metadata for unit enums to add @vspec directives
        vspec_comments: Comments data for fields and types

    Returns:
        SDL string with @vspec directives
    """
    # Use directive processor instead of manual string manipulation
    return directive_processor.process_schema(schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments)


def get_graphql_type_for_leaf(leaf_row: pd.Series, types_registry: dict[str, Any] | None = None) -> Any:
    """
    Get the appropriate GraphQL type for a VSS leaf node.

    Args:
        leaf_row: Pandas Series containing leaf metadata
        types_registry: Registry of custom GraphQL types (for enums)

    Returns:
        GraphQL type for the leaf
    """
    # Check for allowed values first - these override the base type
    if types_registry:
        try:
            allowed_values = leaf_row.get("allowed")
            if allowed_values is not None and isinstance(allowed_values, list) and len(allowed_values) > 0:
                # Create enum type name based on the leaf's fully qualified path
                # Use the index as the FQN since qualified_name might not be available
                fqn = leaf_row.name if hasattr(leaf_row, "name") else leaf_row.get("qualified_name", "unknown")
                enum_type_name = (
                    f"{convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)}_Enum"
                )

                # Return the enum type if it exists in registry
                if enum_type_name in types_registry:
                    return types_registry[enum_type_name]
        except (ValueError, TypeError, KeyError):
            # Handle pandas array issues gracefully
            pass

    datatype = leaf_row.get("datatype", "string")

    # Map VSS datatypes to GraphQL types
    return VSS_DATATYPE_MAP.get(datatype, GraphQLString)


def write_modular_schema(
    schema: GraphQLSchema,
    unit_enums_metadata: dict[str, Any],
    allowed_enums_metadata: dict[str, Any],
    vspec_comments: dict[str, Any],
    output_dir: Path,
    flat_domains: bool = True,
) -> None:
    """
    Write the GraphQL schema as modular files.

    Args:
        schema: The GraphQL schema to split
        unit_enums_metadata: Metadata for unit enums
        allowed_enums_metadata: Metadata for allowed value enums
        vspec_comments: Comments data for fields and types
        output_dir: Directory to write modular files to
        flat_domains: If True, create flat structure; if False, create nested structure
    """
    write_common_files(schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments, output_dir)

    if flat_domains:
        domain_structure = analyze_schema_for_flat_domains(schema)
    else:
        domain_structure = analyze_schema_for_nested_domains(schema)

    write_domain_files(domain_structure, schema, output_dir, vspec_comments, directive_processor)

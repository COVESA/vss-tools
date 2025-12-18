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
from vss_tools.tree import VSSNode, expand_string
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
    """
    Configure GraphQL naming conversions for S2DM schema generation.

    Overrides default conversions for type-like elements to handle fully qualified names
    (e.g., Vehicle.Body -> Vehicle_Body) by excluding dots from delimiters.
    """
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

# VSS leaf types to track in field metadata (corresponds to VspecElement enum in directives.graphql)
# Note: BRANCH is excluded as it's handled separately for object types
VSS_LEAF_TYPES = ["SENSOR", "ACTUATOR", "ATTRIBUTE"]


class S2DMExporterException(Exception):
    """Exception raised for errors in the S2DM export process."""

    pass


# Load custom directives from predefined GraphQL schema files
_, CUSTOM_DIRECTIVES = load_predefined_schema_elements(Path(__file__).parent / "predefined_elements")

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
@clo.types_opt
@clo.modular_opt
@clo.flat_domains_opt
@clo.strict_exceptions_opt
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
    types: tuple[Path, ...],
    modular: bool,
    flat_domains: bool,
    strict_exceptions: Path | None,
) -> None:
    """Export a VSS specification to S2DM GraphQL schema."""
    try:
        tree, data_type_tree = get_trees(
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

        log.info("Generating S2DM GraphQL schema...")

        # Generate the schema
        schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments = generate_s2dm_schema(
            tree, data_type_tree, extended_attributes=extended_attributes
        )

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
    data_type_tree: VSSNode | None = None,
    extended_attributes: tuple[str, ...] = (),
) -> tuple[
    GraphQLSchema,
    dict[str, dict[str, dict[str, str]]],
    dict[str, dict[str, dict[str, str]]],
    dict[str, dict[str, Any]],
]:
    """
    Generate complete S2DM GraphQL schema from VSS tree.

    Creates unit enums, instance types, allowed value enums, struct types, and object types for all branches,
    then assembles them into a GraphQL schema with custom directives.

    Args:
        tree: The main VSS tree containing vehicle signals
        data_type_tree: Optional tree containing user-defined struct types
        extended_attributes: Tuple of extended attribute names requested via CLI flags.
    """
    branches_df, leaves_df = get_metadata_df(tree, extended_attributes=extended_attributes)
    vspec_comments = _init_vspec_comments()

    # Create all types in logical order
    unit_enums, unit_metadata = _create_unit_enums()
    instance_types = _create_instance_types(branches_df, vspec_comments)
    allowed_enums, allowed_metadata = _create_allowed_enums(leaves_df)

    # Create struct types from data type tree
    struct_types = _create_struct_types(data_type_tree, vspec_comments, extended_attributes=extended_attributes)

    # Combine all types
    types_registry = {**instance_types, **allowed_enums, **struct_types}

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
    Initialize dictionary for storing VSS metadata for directives.

    - vss_types/field_vss_types: Used for @vspec directive (element + fqn only)
    - field_ranges: Used for @range directive (min/max values)
    - field_deprecated: Used for @deprecated directive (deprecation reasons)
    """
    return {
        "instance_tags": {},
        "instance_tag_types": {},
        # type_name -> {"element": "BRANCH"|"STRUCT", "fqn": "..."}
        "vss_types": {},
        # field_path -> {"element": "ATTRIBUTE"|"SENSOR"|"ACTUATOR"|"STRUCT_PROPERTY", "fqn": "..."}
        "field_vss_types": {},
        # field_path -> {"min": value, "max": value} for @range directive
        "field_ranges": {},
        # field_path -> "deprecation reason" for @deprecated directive
        "field_deprecated": {},
    }


def _create_unit_enums() -> tuple[dict[str, GraphQLEnumType], dict[str, dict[str, dict[str, str]]]]:
    """
    Create GraphQL enum types for VSS units grouped by quantity.

    Generates enums like LengthUnitEnum containing all length units (km, m, cm, etc.).
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
    """Extract and organize units from VSS registry by quantity (e.g., length -> {km, m, cm})."""
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

    Args:
        leaves_df: DataFrame containing VSS leaf node metadata

    Returns:
        Tuple of (enums dictionary, metadata dictionary with fqn, vss_type, and allowed_values)
    """
    enums, metadata = {}, {}

    for fqn, row in leaves_df[leaves_df["allowed"].notna()].iterrows():
        if allowed := row.get("allowed"):
            enum_name = f"{convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)}_Enum"
            values = {_clean_enum_name(str(v)): GraphQLEnumValue(v) for v in allowed}
            enums[enum_name] = GraphQLEnumType(enum_name, values, description=f"Allowed values for {fqn}.")

            # Get VSS type (ATTRIBUTE, SENSOR, or ACTUATOR)
            vss_type = row.get("type", "").upper()
            if vss_type not in VSS_LEAF_TYPES:
                vss_type = "ATTRIBUTE"  # Default fallback

            metadata[enum_name] = {
                "fqn": fqn,
                "vss_type": vss_type,
                "allowed_values": {_clean_enum_name(str(v)): str(v) for v in allowed},
            }

    return enums, metadata


def _clean_enum_name(value: str) -> str:
    """Sanitize enum value names for GraphQL (prefix numbers, replace dots/hyphens)."""
    if value[0].isdigit():
        value = f"_{value}"
    return value.replace(".", "_DOT_").replace("-", "_DASH_")


def _resolve_datatype_to_graphql(datatype: str, types_registry: dict[str, Any]) -> Any:
    """
    Resolve a VSS datatype string to its corresponding GraphQL type.

    Handles primitive types, struct references, and arrays.

    Args:
        datatype: VSS datatype string (e.g., "uint8", "MyStruct", "MyStruct[]")
        types_registry: Dictionary of custom types (structs, enums)

    Returns:
        Corresponding GraphQL type
    """
    # Handle array types
    if datatype.endswith("[]"):
        base_datatype = datatype[:-2]
        struct_type_name = convert_name_for_graphql_schema(base_datatype, GraphQLElementType.TYPE, S2DM_CONVERSIONS)

        if struct_type_name in types_registry:
            return GraphQLList(GraphQLNonNull(types_registry[struct_type_name]))

        # Primitive array type
        base_type = VSS_DATATYPE_MAP.get(base_datatype, GraphQLString)
        return GraphQLList(GraphQLNonNull(base_type))

    # Check for custom types (structs)
    struct_type_name = convert_name_for_graphql_schema(datatype, GraphQLElementType.TYPE, S2DM_CONVERSIONS)
    if struct_type_name in types_registry:
        return types_registry[struct_type_name]

    # Fall back to primitive type
    return VSS_DATATYPE_MAP.get(datatype, GraphQLString)


def _create_struct_types(
    data_type_tree: VSSNode | None,
    vspec_comments: dict[str, dict[str, Any]],
    extended_attributes: tuple[str, ...] = (),
) -> dict[str, GraphQLObjectType]:
    """
    Convert VSS struct definitions to GraphQL object types.

    Each struct becomes a GraphQL object type with all properties as non-null fields.
    Supports nested structs and struct arrays.

    Args:
        data_type_tree: VSS tree containing user-defined struct types
        vspec_comments: Dictionary to store struct metadata for @vspec directives
        extended_attributes: Tuple of extended attribute names requested via CLI flags

    Returns:
        Dictionary mapping struct type names to GraphQL object types
    """
    if not data_type_tree:
        return {}

    struct_types: dict[str, GraphQLObjectType] = {}

    # Get metadata for the data type tree
    branches_df, leaves_df = get_metadata_df(data_type_tree, extended_attributes=extended_attributes)

    # Filter for struct nodes (type == "struct")
    struct_nodes = branches_df[branches_df["type"] == "struct"]

    for fqn, struct_row in struct_nodes.iterrows():
        type_name = convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)

        # Get struct properties (children of the struct node - type == "property")
        properties = leaves_df[leaves_df["parent"] == fqn]

        fields = {}
        for prop_fqn, prop_row in properties.iterrows():
            field_name = convert_name_for_graphql_schema(prop_row["name"], GraphQLElementType.FIELD, S2DM_CONVERSIONS)

            # Get base GraphQL type for the property
            base_type = _get_graphql_type_for_property(prop_row, struct_types)

            # All struct properties are non-null (!)
            fields[field_name] = GraphQLField(GraphQLNonNull(base_type), description=prop_row.get("description", ""))

            # Store property metadata for @vspec directives (element and fqn only)
            field_path = f"{type_name}.{field_name}"
            vspec_comments["field_vss_types"][field_path] = {"element": "STRUCT_PROPERTY", "fqn": prop_fqn}

            # Track ranges for @range directive
            if pd.notna(prop_row.get("min")) or pd.notna(prop_row.get("max")):
                vspec_comments["field_ranges"][field_path] = {
                    "min": prop_row.get("min") if pd.notna(prop_row.get("min")) else None,
                    "max": prop_row.get("max") if pd.notna(prop_row.get("max")) else None,
                }

            # Track deprecation for @deprecated directive
            if pd.notna(prop_row.get("deprecation")) and prop_row.get("deprecation").strip():
                vspec_comments["field_deprecated"][field_path] = prop_row["deprecation"]

        struct_types[type_name] = GraphQLObjectType(
            name=type_name, fields=fields, description=struct_row.get("description", "")
        )

        # Track struct metadata for @vspec directives (element and fqn only)
        vspec_comments["vss_types"][type_name] = {"element": "STRUCT", "fqn": fqn}

    return struct_types


def _get_graphql_type_for_property(prop_row: pd.Series, struct_types: dict[str, GraphQLObjectType]) -> Any:
    """
    Map VSS property datatype to GraphQL type.

    Args:
        prop_row: DataFrame row containing property metadata
        struct_types: Dictionary of already-created struct types

    Returns:
        GraphQL type for the property
    """
    datatype = prop_row.get("datatype", "string")
    return _resolve_datatype_to_graphql(datatype, struct_types)


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
            # Store instance tag metadata for @vspec directive with instances information
            vspec_comments["instance_tags"][tag_name] = {
                "element": "BRANCH",
                "fqn": fqn,
                "instances": str(instances),  # Store original instances specification
            }
            vspec_comments.setdefault("instance_tag_types", {})[base_name] = tag_name

    return types


def _parse_instances_simple(instances: list[Any]) -> list[list[str]]:
    """
    Parse VSS instance declarations into dimensional arrays.

    Example: ["Row[1,2]", ["Left", "Right"]] -> [["Row1", "Row2"], ["Left", "Right"]]
    """
    if all(isinstance(item, str) and "[" not in item for item in instances):
        return [instances]  # Single dimension

    dimensions = []
    for item in instances:
        if isinstance(item, str) and "[" in item:
            dimensions.append(expand_string(item))
        elif isinstance(item, list):
            dimensions.append(item)

    return dimensions


def _get_hoisted_fields(
    child_branch_fqn: str,
    child_branch_row: pd.Series,
    leaves_df: pd.DataFrame,
    types_registry: dict[str, Any],
    unit_enums: dict[str, GraphQLEnumType],
    vspec_comments: dict[str, dict[str, Any]],
) -> dict[str, GraphQLField]:
    """
    Get fields that should be hoisted from an instantiated child branch to its parent.

    When a branch has instances but some of its properties have instantiate=false,
    those properties should be hoisted to the parent type with the naming pattern
    {branchName}{PropertyName} (e.g., Door.SomeSignal -> doorSomeSignal).

    Args:
        child_branch_fqn: FQN of the child branch (e.g., "Vehicle.Cabin.Door")
        child_branch_row: DataFrame row for the child branch
        leaves_df: DataFrame of all leaf nodes
        types_registry: Registry of GraphQL types
        unit_enums: Dictionary of unit enums
        vspec_comments: Dictionary for VSS metadata

    Returns:
        Dictionary of hoisted fields to add to parent type
    """
    hoisted: dict[str, GraphQLField] = {}

    # Only process branches with instances
    if not child_branch_row.get("instances"):
        return hoisted

    # Get the branch name for generating hoisted field names
    child_branch_row["name"]

    # Find leaves that are direct children of this branch
    child_leaves = leaves_df[leaves_df["parent"] == child_branch_fqn]

    for leaf_fqn, leaf_row in child_leaves.iterrows():
        # OPTIMIZED: Check instantiate directly from DataFrame instead of tree lookup
        instantiate = leaf_row.get("instantiate")
        # Default to True if not present (standard VSS behavior)
        if instantiate is False:  # Explicitly check for False, not just falsy
            # This property should be hoisted to parent
            leaf_name = leaf_row["name"]

            # Get the parent type name to construct the field path
            parent_fqn = child_branch_row["parent"]

            # Check if there's a valid parent to hoist to
            if parent_fqn is None or parent_fqn == "" or pd.isna(parent_fqn):
                log.warning(
                    f"Property '{leaf_fqn}' is defined for branch '{child_branch_fqn}' with instantiate=false, "
                    f"but cannot be hoisted because '{child_branch_fqn}' has no parent branch. "
                    f"The property will be omitted from the GraphQL schema."
                )
                continue

            # Generate hoisted field name: {branchName}{PropertyName} in camelCase
            hoisted_field_name = convert_name_for_graphql_schema(
                f"{leaf_name}", GraphQLElementType.FIELD, S2DM_CONVERSIONS
            )

            parent_type_name = convert_name_for_graphql_schema(parent_fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)
            field_path = f"{parent_type_name}.{hoisted_field_name}"

            # Store metadata for hoisted field (element, fqn, and instantiate=false indicator)
            if leaf_type := leaf_row.get("type", "").upper():
                if leaf_type in VSS_LEAF_TYPES:
                    vspec_comments["field_vss_types"][field_path] = {
                        "element": leaf_type,
                        "fqn": leaf_fqn,
                        "instantiate": False,  # Mark this as a hoisted non-instantiated field
                    }

            # Track ranges for @range directive
            if pd.notna(leaf_row.get("min")) or pd.notna(leaf_row.get("max")):
                vspec_comments["field_ranges"][field_path] = {
                    "min": leaf_row.get("min") if pd.notna(leaf_row.get("min")) else None,
                    "max": leaf_row.get("max") if pd.notna(leaf_row.get("max")) else None,
                }

            # Track deprecation for @deprecated directive
            if pd.notna(leaf_row.get("deprecation")) and leaf_row.get("deprecation").strip():
                vspec_comments["field_deprecated"][field_path] = leaf_row["deprecation"]

            # Create the GraphQL field
            field_type = get_graphql_type_for_leaf(leaf_row, types_registry)
            unit_args = _get_unit_args(leaf_row, unit_enums)
            hoisted[hoisted_field_name] = GraphQLField(
                field_type, args=unit_args, description=leaf_row.get("description", "")
            )

    return hoisted


def _create_object_type(
    fqn: str,
    branches_df: pd.DataFrame,
    leaves_df: pd.DataFrame,
    types_registry: dict[str, Any],
    unit_enums: dict[str, GraphQLEnumType],
    vspec_comments: dict[str, dict[str, Any]],
) -> GraphQLObjectType:
    """
    Create GraphQL object type for a VSS branch.

    Recursively builds the type hierarchy with system fields (id, instanceTag),
    leaf fields (sensors/actuators/attributes), and nested branches.

    Handles hoisting of non-instantiated properties from child branches with instances
    to the parent type with the naming pattern {branchName}{PropertyName}.
    """
    branch_row = branches_df.loc[fqn]
    type_name = convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)

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
            # Skip non-instantiated leaves if this branch has instances
            # (they will be hoisted to parent by _get_hoisted_fields)
            if branch_row.get("instances"):
                # OPTIMIZED: Check instantiate directly from DataFrame
                instantiate = leaf_row.get("instantiate")
                if instantiate is False:  # Explicitly check for False
                    # Check if this branch has a parent to hoist to
                    parent_fqn = branch_row.get("parent")
                    if parent_fqn is None or parent_fqn == "" or pd.isna(parent_fqn):
                        # No parent to hoist to - log warning
                        log.warning(
                            f"Property '{child_fqn}' is defined for branch '{fqn}' with instantiate=false, "
                            f"but cannot be hoisted because '{fqn}' has no parent branch. "
                            f"The property will be omitted from the GraphQL schema."
                        )
                    continue  # Skip this leaf - it will be hoisted to parent (or omitted if no parent)

            field_name = convert_name_for_graphql_schema(leaf_row["name"], GraphQLElementType.FIELD, S2DM_CONVERSIONS)
            field_path = f"{type_name}.{field_name}"

            # Store VSS type metadata (element and fqn only)
            if leaf_type := leaf_row.get("type", "").upper():
                if leaf_type in VSS_LEAF_TYPES:
                    vspec_comments["field_vss_types"][field_path] = {"element": leaf_type, "fqn": child_fqn}

            # Track ranges for @range directive
            if pd.notna(leaf_row.get("min")) or pd.notna(leaf_row.get("max")):
                vspec_comments["field_ranges"][field_path] = {
                    "min": leaf_row.get("min") if pd.notna(leaf_row.get("min")) else None,
                    "max": leaf_row.get("max") if pd.notna(leaf_row.get("max")) else None,
                }

            # Track deprecation for @deprecated directive
            if pd.notna(leaf_row.get("deprecation")) and leaf_row.get("deprecation").strip():
                vspec_comments["field_deprecated"][field_path] = leaf_row["deprecation"]

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

            # Check if child branch has non-instantiated properties that need to be hoisted
            hoisted_fields = _get_hoisted_fields(
                child_fqn, child_row, leaves_df, types_registry, unit_enums, vspec_comments
            )
            fields.update(hoisted_fields)

            if child_row.get("instances"):
                fields[f"{field_name}_s"] = GraphQLField(GraphQLList(child_type))
            else:
                fields[field_name] = GraphQLField(child_type)

        return fields

    # Track branch metadata for @vspec directive (element and fqn only)
    vspec_comments["vss_types"][type_name] = {"element": "BRANCH", "fqn": fqn}

    return GraphQLObjectType(name=type_name, fields=get_fields, description=branch_row.get("description", ""))


def _get_unit_args(leaf_row: pd.Series, unit_enums: dict[str, GraphQLEnumType]) -> dict[str, GraphQLArgument]:
    """Generate 'unit' argument for fields with units, enabling unit conversion in queries."""
    unit = leaf_row.get("unit", "")
    if not unit:
        return {}

    # Unit validity is guaranteed by tree parsing validation
    unit_data = dynamic_units[unit]
    if not unit_data.quantity:
        return {}

    unit_enum = unit_enums.get(unit_data.quantity)
    if not unit_enum:
        log.warning(
            f"Unit '{unit}' with quantity '{unit_data.quantity}' has no corresponding GraphQL enum. "
            "Unit argument will not be generated."
        )
        return {}

    return {"unit": GraphQLArgument(type_=unit_enum, default_value=unit)}


def print_schema_with_vspec_directives(
    schema: GraphQLSchema,
    unit_enums_metadata: dict[str, Any],
    allowed_enums_metadata: dict[str, Any],
    vspec_comments: dict[str, Any],
) -> str:
    """Serialize GraphQL schema to SDL with @vspec directives."""
    # Use directive processor instead of manual string manipulation
    return directive_processor.process_schema(schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments)


def get_graphql_type_for_leaf(leaf_row: pd.Series, types_registry: dict[str, Any] | None = None) -> Any:
    """Map VSS leaf to GraphQL type, using custom enum if allowed values are defined or struct types."""
    # Check for allowed values first - these override the base type
    if types_registry:
        try:
            allowed_values = leaf_row.get("allowed")
            if allowed_values is not None and isinstance(allowed_values, list) and len(allowed_values) > 0:
                fqn = leaf_row.name if hasattr(leaf_row, "name") else leaf_row.get("qualified_name", "unknown")
                enum_type_name = (
                    f"{convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)}_Enum"
                )
                if enum_type_name in types_registry:
                    return types_registry[enum_type_name]
        except (ValueError, TypeError, KeyError):
            pass

    datatype = leaf_row.get("datatype", "string")

    # Use unified resolver for struct/array/primitive types
    if types_registry:
        return _resolve_datatype_to_graphql(datatype, types_registry)

    # No types registry - just handle primitive types
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

    write_domain_files(
        domain_structure, schema, output_dir, vspec_comments, directive_processor, allowed_enums_metadata
    )

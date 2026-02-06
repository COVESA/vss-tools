# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""GraphQL type builders for VSS elements.

This module contains all type creation logic for S2DM schema generation:
- Unit enums (grouped by quantity)
- Instance types (for multi-dimensional instantiation)
- Struct types (user-defined data types)
- Branch types (VSS signal hierarchy)
- Allowed value enums
"""

from __future__ import annotations

import re
from typing import Any

import caseconverter
import inflect
import pandas as pd
from graphql import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLID,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLString,
)

from vss_tools import log
from vss_tools.datatypes import dynamic_units
from vss_tools.tree import VSSNode, expand_string
from vss_tools.utils.graphql_scalars import VSS_DATATYPE_MAP
from vss_tools.utils.graphql_utils import GraphQLElementType, convert_name_for_graphql_schema
from vss_tools.utils.pandas_utils import get_metadata_df

from .constants import S2DM_CONVERSIONS, VSS_LEAF_TYPES
from .metadata_tracker import build_field_path


def _extract_extended_attributes(row: pd.Series, extended_attributes: tuple[str, ...]) -> dict[str, Any]:
    """
    Extract extended attributes from a DataFrame row.

    Args:
        row: pandas Series (DataFrame row) containing VSS node data
        extended_attributes: Tuple of extended attribute names to extract

    Returns:
        Dictionary containing only the extended attributes that exist and are not NA
    """
    extracted = {}
    for ext_attr in extended_attributes:
        if ext_attr in row.index and pd.notna(row.get(ext_attr)):
            extracted[ext_attr] = row[ext_attr]
    return extracted


# Initialize inflect engine for pluralization (singleton)
_inflect_engine = inflect.engine()


def _check_and_collect_plural_type_name(
    converted_type_name: str, fqn: str, original_name: str, plural_name_warnings: dict[str, dict[str, Any]]
) -> None:
    """
    Check if a name appears to be plural and collect for reporting.

    Uses inflect library to detect potential plural forms. Reports all cases where
    a singular form is detected, without filtering. This allows downstream tools
    to decide which cases are true issues vs. acceptable exceptions.

    Args:
        converted_type_name: The converted type name (for schema)
        fqn: The fully qualified VSS name for context
        original_name: The original VSS branch/struct name (before conversion)
        plural_name_warnings: Dictionary to store metadata (adds to "plural_type_warnings" key)
    """
    # Check if inflect detects a singular form
    # Returns False if already singular, or the singular form if plural
    singular = _inflect_engine.singular_noun(original_name)

    if singular:
        plural_name_warnings.setdefault("plural_type_warnings", []).append(
            {"type_name": converted_type_name, "fqn": fqn, "plural_word": original_name, "suggested_singular": singular}
        )

        # Also log to console for immediate visibility
        log.warning(
            f"Type '{converted_type_name}' uses potential plural name '{original_name}'. "
            f"Suggested singular: '{singular}' (VSS FQN: {fqn})"
        )


def create_unit_enums() -> tuple[dict[str, GraphQLEnumType], dict[str, dict[str, dict[str, str]]]]:
    """
    Create GraphQL enum types for VSS units grouped by quantity.

    Generates enums like LengthUnitEnum containing all length units (km, m, cm, etc.).

    Returns:
        Tuple of (unit_enums, unit_metadata)
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
    """Extract and organize units from VSS registry by quantity."""
    quantity_units: dict[str, dict[str, dict[str, str]]] = {}
    processed_units = set()

    for unit_key, unit_data in dynamic_units.items():
        unit_id = id(unit_data)
        if unit_id in processed_units:
            continue

        quantity = unit_data.quantity
        unit_display_name = unit_data.unit
        actual_unit_key = unit_data.key or unit_key

        if quantity and unit_display_name:
            if quantity not in quantity_units:
                quantity_units[quantity] = {}

            quantity_units[quantity][actual_unit_key] = {"name": unit_display_name, "key": actual_unit_key}
            processed_units.add(unit_id)

    return quantity_units


def create_instance_types(
    branches_df: pd.DataFrame, vspec_comments: dict[str, dict[str, Any]]
) -> dict[str, GraphQLEnumType | GraphQLObjectType]:
    """
    Create GraphQL types for VSS instance-based branches.

    Args:
        branches_df: VSS branch node metadata
        vspec_comments: Dictionary to store instance tag metadata

    Returns:
        Mapping of type names to GraphQL enum or object types
    """
    types: dict[str, GraphQLEnumType | GraphQLObjectType] = {}
    vspec_comments.setdefault("instance_dimension_enums", {})

    for fqn, row in branches_df[branches_df["instances"].notna()].iterrows():
        if instances := row.get("instances"):
            base_name = convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)
            tag_name = f"{base_name}_InstanceTag"

            dimensions = _parse_instances_simple(instances)
            fields = {}
            for i, values in enumerate(dimensions, 1):
                enum_name = f"{tag_name}_Dimension{i}"

                # Sanitize enum values and track modifications
                enum_values = {}
                modified_values = {}

                for v in values:
                    sanitized, was_modified = _sanitize_enum_value_for_graphql(str(v))
                    enum_values[sanitized] = GraphQLEnumValue(v)

                    if was_modified:
                        modified_values[sanitized] = str(v)

                types[enum_name] = GraphQLEnumType(
                    enum_name,
                    enum_values,
                    description=f"Dimensional enum for VSS instance dimension {i}.",
                )

                # Store metadata for directive processor
                if modified_values:
                    vspec_comments["instance_dimension_enums"][enum_name] = {"modified_values": modified_values}

                fields[f"dimension{i}"] = GraphQLField(types[enum_name])

            types[tag_name] = GraphQLObjectType(tag_name, fields)
            vspec_comments["instance_tags"][tag_name] = {
                "element": "BRANCH",
                "fqn": fqn,
                "instances": str(instances),
            }
            vspec_comments.setdefault("instance_tag_types", {})[base_name] = tag_name

    return types


def _parse_instances_simple(instances: list[Any]) -> list[list[str]]:
    """
    Parse VSS instance declarations into dimensional arrays.

    Example: ["Row[1,2]", ["Left", "Right"]] -> [["Row1", "Row2"], ["Left", "Right"]]
    """
    if all(isinstance(item, str) and "[" not in item for item in instances):
        return [instances]

    dimensions = []
    for item in instances:
        if isinstance(item, str) and "[" in item:
            dimensions.append(expand_string(item))
        elif isinstance(item, list):
            dimensions.append(item)

    return dimensions


def create_allowed_enums(
    leaves_df: pd.DataFrame,
) -> tuple[dict[str, GraphQLEnumType], dict[str, dict[str, dict[str, str]]]]:
    """
    Create GraphQL enum types for VSS signals with allowed value constraints.

    Args:
        leaves_df: DataFrame containing VSS leaf node metadata

    Returns:
        Tuple of (enums dictionary, metadata dictionary)
    """
    enums, metadata = {}, {}

    for fqn, row in leaves_df[leaves_df["allowed"].notna()].iterrows():
        if allowed := row.get("allowed"):
            enum_name = f"{convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)}_Enum"

            # Track values and their modifications
            values = {}
            modified_values = {}

            for v in allowed:
                sanitized, was_modified = _sanitize_enum_value_for_graphql(str(v))
                values[sanitized] = GraphQLEnumValue(v)

                # Track if value was modified for metadata annotation
                if was_modified:
                    modified_values[sanitized] = str(v)

            enums[enum_name] = GraphQLEnumType(enum_name, values, description=f"Allowed values for {fqn}.")

            vss_type = row.get("type", "").upper()
            if vss_type not in VSS_LEAF_TYPES:
                vss_type = "ATTRIBUTE"

            allowed_values_graphql = {
                _sanitize_enum_value_for_graphql(str(v))[0]: str(v).replace('"', "'") for v in allowed
            }

            metadata[enum_name] = {
                "fqn": fqn,
                "vss_type": vss_type,
                "allowed_values": allowed_values_graphql,
                "modified_values": modified_values,  # Store modified values for directive annotations
            }

    return enums, metadata


def _sanitize_enum_value_for_graphql(original_value: str) -> tuple[str, bool]:
    """
    Sanitize enum value for GraphQL schema compliance.

    Converts values with spaces, camelCase, or other invalid characters to valid GraphQL enum values.
    Uses caseconverter to properly handle camelCase word boundaries.

    Examples:
        "some value" -> "SOME_VALUE"
        "SOME VALUE" -> "SOME_VALUE"
        "PbCa" -> "PB_CA"
        "HTTPSConnection" -> "HTTPS_CONNECTION"
        "value-with-dash" -> "VALUE_WITH_DASH"

    Args:
        original_value: The original enum value from VSS

    Returns:
        Tuple of (sanitized_value, was_modified)
        - sanitized_value: Valid GraphQL enum value name
        - was_modified: True if the value was changed, False otherwise
    """

    # Handle empty or whitespace-only strings
    if not original_value or not original_value.strip():
        raise ValueError(f"Cannot create GraphQL enum value from empty or whitespace-only string: {original_value!r}")

    # Replace with underscore all the special characters that are not allowed in GraphQL enum names
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", original_value)

    # Convert to caseconverter MACRO_CASE (i.e., SCREAMING_SNAKE_CASE)
    if re.search(r"[A-Z]{2,}", sanitized) and re.search(r"[a-z]", sanitized):
        words: list[str] = []
        for segment in sanitized.split("_"):
            words.extend(re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+", segment))
        sanitized = "_".join(caseconverter.macrocase(word, strip_punctuation=False) for word in words if word)
    else:
        sanitized = caseconverter.macrocase(sanitized, strip_punctuation=False)

    # Handle enum values starting with digits
    sanitized = f"_{sanitized}" if sanitized[0].isdigit() else sanitized

    # Check if modification occurred
    was_modified = sanitized != original_value

    return sanitized, was_modified


def create_struct_types(
    data_type_tree: VSSNode | None,
    vspec_comments: dict[str, dict[str, Any]],
    extended_attributes: tuple[str, ...] = (),
) -> dict[str, GraphQLObjectType]:
    """
    Convert VSS struct definitions to GraphQL object types.

    Args:
        data_type_tree: VSS tree containing user-defined struct types
        vspec_comments: Dictionary to store struct metadata
        extended_attributes: Extended attribute names from CLI

    Returns:
        Dictionary mapping struct type names to GraphQL object types
    """
    if not data_type_tree:
        return {}

    struct_types: dict[str, GraphQLObjectType] = {}
    branches_df, leaves_df = get_metadata_df(data_type_tree, extended_attributes=extended_attributes)
    struct_nodes = branches_df[branches_df["type"] == "struct"]

    for fqn, struct_row in struct_nodes.iterrows():
        type_name = convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)
        properties = leaves_df[leaves_df["parent"] == fqn]

        fields = {}
        for prop_fqn, prop_row in properties.iterrows():
            field_name = convert_name_for_graphql_schema(prop_row["name"], GraphQLElementType.FIELD, S2DM_CONVERSIONS)
            base_type = _get_graphql_type_for_property(prop_row, struct_types)
            fields[field_name] = GraphQLField(GraphQLNonNull(base_type), description=prop_row.get("description", ""))

            field_path = build_field_path(type_name, field_name)
            field_metadata = {"element": "STRUCT_PROPERTY", "fqn": prop_fqn}

            # Capture extended attributes if present
            field_metadata.update(_extract_extended_attributes(prop_row, extended_attributes))

            vspec_comments["field_vss_types"][field_path] = field_metadata

            if pd.notna(prop_row.get("min")) or pd.notna(prop_row.get("max")):
                vspec_comments["field_ranges"][field_path] = {
                    "min": prop_row.get("min") if pd.notna(prop_row.get("min")) else None,
                    "max": prop_row.get("max") if pd.notna(prop_row.get("max")) else None,
                }

            if pd.notna(prop_row.get("deprecation")) and prop_row.get("deprecation").strip():
                vspec_comments["field_deprecated"][field_path] = prop_row["deprecation"]

        struct_types[type_name] = GraphQLObjectType(
            name=type_name, fields=fields, description=struct_row.get("description", "")
        )

        # Store type-level metadata including extended attributes
        type_metadata = {"element": "STRUCT", "fqn": fqn}
        type_metadata.update(_extract_extended_attributes(struct_row, extended_attributes))
        vspec_comments["vss_types"][type_name] = type_metadata

    return struct_types


def _get_graphql_type_for_property(prop_row: pd.Series, struct_types: dict[str, GraphQLObjectType]) -> Any:
    """Map VSS property datatype to GraphQL type."""
    datatype = prop_row.get("datatype", "string")
    return resolve_datatype_to_graphql(datatype, struct_types)


def resolve_datatype_to_graphql(datatype: str, types_registry: dict[str, Any]) -> Any:
    """
    Resolve a VSS datatype string to its corresponding GraphQL type.

    Args:
        datatype: VSS datatype string (e.g., "uint8", "MyStruct", "MyStruct[]")
        types_registry: Dictionary of custom types

    Returns:
        Corresponding GraphQL type
    """
    if datatype.endswith("[]"):
        base_datatype = datatype[:-2]
        struct_type_name = convert_name_for_graphql_schema(base_datatype, GraphQLElementType.TYPE, S2DM_CONVERSIONS)

        if struct_type_name in types_registry:
            return GraphQLList(GraphQLNonNull(types_registry[struct_type_name]))

        base_type = VSS_DATATYPE_MAP.get(base_datatype, GraphQLString)
        return GraphQLList(GraphQLNonNull(base_type))

    struct_type_name = convert_name_for_graphql_schema(datatype, GraphQLElementType.TYPE, S2DM_CONVERSIONS)
    if struct_type_name in types_registry:
        return types_registry[struct_type_name]

    return VSS_DATATYPE_MAP.get(datatype, GraphQLString)


def create_object_type(
    fqn: str,
    branches_df: pd.DataFrame,
    leaves_df: pd.DataFrame,
    types_registry: dict[str, Any],
    unit_enums: dict[str, GraphQLEnumType],
    vspec_comments: dict[str, dict[str, Any]],
    extended_attributes: tuple[str, ...] = (),
) -> GraphQLObjectType:
    """
    Create GraphQL object type for a VSS branch.

    Builds type hierarchy with system fields, leaf fields, and nested branches.
    Hoists non-instantiated properties from instance-based child branches.

    Args:
        fqn: Fully qualified name of the branch
        branches_df: DataFrame of branch nodes
        leaves_df: DataFrame of leaf nodes
        types_registry: Registry of already-created types
        unit_enums: Unit enum types
        vspec_comments: Metadata tracking dictionary
        extended_attributes: Extended attribute names from CLI

    Returns:
        GraphQL object type for the branch
    """
    branch_row = branches_df.loc[fqn]
    original_name = branch_row["name"]
    type_name = convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)

    # Check if branch name is plural and collect for reporting
    # Pass original VSS branch name (before any conversion)
    _check_and_collect_plural_type_name(type_name, fqn, original_name, vspec_comments)

    def get_fields() -> dict[str, GraphQLField]:
        fields = {}

        # System fields
        if type_name == "Vehicle" or branch_row.get("instances"):
            fields["id"] = GraphQLField(GraphQLNonNull(GraphQLID))
        if instance_tag_type := vspec_comments.get("instance_tag_types", {}).get(type_name):
            if instance_tag_type in types_registry:
                fields["instanceTag"] = GraphQLField(types_registry[instance_tag_type])

        # Leaf fields
        for child_fqn, leaf_row in leaves_df[leaves_df["parent"] == fqn].iterrows():
            if branch_row.get("instances"):
                instantiate = leaf_row.get("instantiate")
                if instantiate is False:
                    parent_fqn = branch_row.get("parent")
                    if parent_fqn is None or parent_fqn == "" or pd.isna(parent_fqn):
                        log.warning(
                            f"Property '{child_fqn}' has instantiate=false but '{fqn}' has no parent. "
                            f"Property will be omitted from schema."
                        )
                    continue

            field_name = convert_name_for_graphql_schema(leaf_row["name"], GraphQLElementType.FIELD, S2DM_CONVERSIONS)
            field_path = build_field_path(type_name, field_name)

            if leaf_type := _get_vss_type_if_valid(leaf_row):
                field_metadata = {"element": leaf_type, "fqn": child_fqn}

                # Capture extended attributes if present
                field_metadata.update(_extract_extended_attributes(leaf_row, extended_attributes))

                vspec_comments["field_vss_types"][field_path] = field_metadata

            if pd.notna(leaf_row.get("min")) or pd.notna(leaf_row.get("max")):
                vspec_comments["field_ranges"][field_path] = {
                    "min": leaf_row.get("min") if pd.notna(leaf_row.get("min")) else None,
                    "max": leaf_row.get("max") if pd.notna(leaf_row.get("max")) else None,
                }

            if pd.notna(leaf_row.get("deprecation")) and leaf_row.get("deprecation").strip():
                vspec_comments["field_deprecated"][field_path] = leaf_row["deprecation"]

            field_type = get_graphql_type_for_leaf(leaf_row, types_registry)
            unit_args = _get_unit_args(leaf_row, unit_enums)
            fields[field_name] = GraphQLField(field_type, args=unit_args, description=leaf_row.get("description", ""))

        # Branch fields
        for child_fqn, child_row in branches_df[branches_df["parent"] == fqn].iterrows():
            field_name = convert_name_for_graphql_schema(child_row["name"], GraphQLElementType.FIELD, S2DM_CONVERSIONS)
            child_type = types_registry.get(child_fqn) or create_object_type(
                child_fqn, branches_df, leaves_df, types_registry, unit_enums, vspec_comments, extended_attributes
            )
            types_registry[child_fqn] = child_type

            hoisted_fields = get_hoisted_fields(
                child_fqn, child_row, leaves_df, types_registry, unit_enums, vspec_comments, extended_attributes
            )
            fields.update(hoisted_fields)

            if child_row.get("instances"):
                # Use natural plural form for list fields (using inflect directly)
                plural_field_name = _inflect_engine.plural(field_name)
                fields[plural_field_name] = GraphQLField(GraphQLList(child_type))

                # Collect pluralized field name for reporting
                field_path = build_field_path(type_name, plural_field_name)
                vspec_comments.setdefault("pluralized_field_names", []).append(
                    {"fqn": child_fqn, "plural_field_name": plural_field_name, "path_in_graphql_model": field_path}
                )
            else:
                fields[field_name] = GraphQLField(child_type)

        return fields

    # Store type-level metadata including extended attributes
    type_metadata = {"element": "BRANCH", "fqn": fqn}
    type_metadata.update(_extract_extended_attributes(branch_row, extended_attributes))
    vspec_comments["vss_types"][type_name] = type_metadata

    return GraphQLObjectType(name=type_name, fields=get_fields, description=branch_row.get("description", ""))


def get_hoisted_fields(
    child_branch_fqn: str,
    child_branch_row: pd.Series,
    leaves_df: pd.DataFrame,
    types_registry: dict[str, Any],
    unit_enums: dict[str, GraphQLEnumType],
    vspec_comments: dict[str, dict[str, Any]],
    extended_attributes: tuple[str, ...] = (),
) -> dict[str, GraphQLField]:
    """Get fields to hoist from instantiated child branch to parent."""
    hoisted: dict[str, GraphQLField] = {}

    if not child_branch_row.get("instances"):
        return hoisted

    child_leaves = leaves_df[leaves_df["parent"] == child_branch_fqn]

    for leaf_fqn, leaf_row in child_leaves.iterrows():
        instantiate = leaf_row.get("instantiate")
        if instantiate is False:
            leaf_name = leaf_row["name"]
            parent_fqn = child_branch_row["parent"]

            if parent_fqn is None or parent_fqn == "" or pd.isna(parent_fqn):
                log.warning(
                    f"Property '{leaf_fqn}' has instantiate=false but '{child_branch_fqn}' has no parent. "
                    f"Property will be omitted."
                )
                continue

            hoisted_field_name = convert_name_for_graphql_schema(
                f"{leaf_name}", GraphQLElementType.FIELD, S2DM_CONVERSIONS
            )

            parent_type_name = convert_name_for_graphql_schema(parent_fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)
            field_path = build_field_path(parent_type_name, hoisted_field_name)

            if leaf_type := _get_vss_type_if_valid(leaf_row):
                field_metadata = {
                    "element": leaf_type,
                    "fqn": leaf_fqn,
                    "instantiate": False,
                }

                # Capture extended attributes if present
                field_metadata.update(_extract_extended_attributes(leaf_row, extended_attributes))

                vspec_comments["field_vss_types"][field_path] = field_metadata

            if pd.notna(leaf_row.get("min")) or pd.notna(leaf_row.get("max")):
                vspec_comments["field_ranges"][field_path] = {
                    "min": leaf_row.get("min") if pd.notna(leaf_row.get("min")) else None,
                    "max": leaf_row.get("max") if pd.notna(leaf_row.get("max")) else None,
                }

            if pd.notna(leaf_row.get("deprecation")) and leaf_row.get("deprecation").strip():
                vspec_comments["field_deprecated"][field_path] = leaf_row["deprecation"]

            field_type = get_graphql_type_for_leaf(leaf_row, types_registry)
            unit_args = _get_unit_args(leaf_row, unit_enums)
            hoisted[hoisted_field_name] = GraphQLField(
                field_type, args=unit_args, description=leaf_row.get("description", "")
            )

    return hoisted


def _get_vss_type_if_valid(row: pd.Series) -> str | None:
    """Get VSS type if valid, else None."""
    if vss_type := row.get("type", "").upper():
        if vss_type in VSS_LEAF_TYPES:
            return vss_type
    return None


def _get_unit_args(leaf_row: pd.Series, unit_enums: dict[str, GraphQLEnumType]) -> dict[str, GraphQLArgument]:
    """Generate unit argument for fields with units."""
    unit = leaf_row.get("unit", "")
    if not unit:
        return {}

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


def get_graphql_type_for_leaf(leaf_row: pd.Series, types_registry: dict[str, Any] | None = None) -> Any:
    """Map VSS leaf to GraphQL type."""
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

    if types_registry:
        return resolve_datatype_to_graphql(datatype, types_registry)

    return VSS_DATATYPE_MAP.get(datatype, GraphQLString)

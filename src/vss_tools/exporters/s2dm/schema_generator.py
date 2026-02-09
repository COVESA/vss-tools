# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Core S2DM GraphQL schema generation and serialization.

This module orchestrates the schema generation process:
- Assembles all types into a complete GraphQL schema
- Serializes schema to SDL format with VSS directives
- Writes modular schema files (flat or nested structure)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from graphql import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString

from vss_tools.tree import VSSNode
from vss_tools.utils.pandas_utils import get_metadata_df

from .constants import CUSTOM_DIRECTIVES, S2DMExporterException
from .graphql_directive_processor import GraphQLDirectiveProcessor
from .graphql_scalars import get_vss_scalar_types
from .metadata_tracker import init_vspec_comments
from .modular_export_utils import (
    analyze_schema_for_flat_domains,
    analyze_schema_for_nested_domains,
    write_common_files,
    write_domain_files,
)
from .type_builders import (
    create_allowed_enums,
    create_instance_types,
    create_object_type,
    create_struct_types,
    create_unit_enums,
)

# Extract directive definitions
VSpecDirective = CUSTOM_DIRECTIVES["vspec"]
RangeDirective = CUSTOM_DIRECTIVES["range"]
InstanceTagDirective = CUSTOM_DIRECTIVES["instanceTag"]

# Initialize directive processor
directive_processor = GraphQLDirectiveProcessor()


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
    Generate S2DM GraphQL schema from VSS tree.

    Orchestrates the complete schema generation process:
    1. Extract metadata from VSS tree
    2. Create unit enums, instance types, allowed value enums, struct types
    3. Create object types for all branches
    4. Assemble complete GraphQL schema

    Args:
        tree: Main VSS tree with vehicle signals
        data_type_tree: Optional user-defined struct types
        extended_attributes: Extended attribute names from CLI flags

    Returns:
        Tuple of (schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments)

    Raises:
        S2DMExporterException: If schema generation fails
    """
    try:
        branches_df, leaves_df = get_metadata_df(tree, extended_attributes=extended_attributes)
        vspec_comments = init_vspec_comments()

        # Create all types in logical order
        unit_enums, unit_metadata = create_unit_enums()
        instance_types = create_instance_types(branches_df, vspec_comments)
        allowed_enums, allowed_metadata = create_allowed_enums(leaves_df)

        # Create struct types from data type tree
        struct_types = create_struct_types(data_type_tree, vspec_comments, extended_attributes=extended_attributes)

        # Combine all types
        types_registry = {**instance_types, **allowed_enums, **struct_types}

        # Create object types for all branches
        for fqn in branches_df.index:
            if fqn not in types_registry:
                types_registry[fqn] = create_object_type(
                    fqn, branches_df, leaves_df, types_registry, unit_enums, vspec_comments, extended_attributes
                )

        # Assemble complete schema
        vehicle_type = types_registry.get("Vehicle", GraphQLString)
        query = GraphQLObjectType("Query", {"vehicle": GraphQLField(vehicle_type)})
        schema = GraphQLSchema(
            query=query,
            types=get_vss_scalar_types() + list(types_registry.values()) + list(unit_enums.values()),
            directives=[VSpecDirective, RangeDirective, InstanceTagDirective],
        )

        return schema, unit_metadata, allowed_metadata, vspec_comments

    except Exception as e:
        raise S2DMExporterException(f"Failed to generate S2DM schema: {e}") from e


def print_schema_with_vspec_directives(
    schema: GraphQLSchema,
    unit_enums_metadata: dict[str, Any],
    allowed_enums_metadata: dict[str, Any],
    vspec_comments: dict[str, Any],
) -> str:
    """
    Serialize GraphQL schema to SDL format with VSS directives.

    Uses directive processor to inject @vspec, @range, @deprecated directives
    based on VSS metadata.

    Args:
        schema: GraphQL schema to serialize
        unit_enums_metadata: Metadata for unit enum definitions
        allowed_enums_metadata: Metadata for allowed value enum definitions
        vspec_comments: VSS metadata for directives

    Returns:
        Schema Definition Language (SDL) string with directives
    """
    return directive_processor.process_schema(schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments)


def write_modular_schema(
    schema: GraphQLSchema,
    unit_enums_metadata: dict[str, Any],
    allowed_enums_metadata: dict[str, Any],
    vspec_comments: dict[str, Any],
    output_dir: Path,
    flat_domains: bool = True,
) -> None:
    """
    Write GraphQL schema as modular files organized by domain.

    Creates a structured directory layout with common files and domain-specific files.

    Structure (flat_domains=True):
    ```
    schema/
        common.graphql        # Shared types, enums, directives
        domain_cabin.graphql  # Cabin-related types
        domain_body.graphql   # Body-related types
        ...
    ```

    Structure (flat_domains=False):
    ```
    schema/
        common.graphql
        cabin/
            cabin.graphql
            door.graphql
            ...
    ```

    Args:
        schema: The GraphQL schema to split
        unit_enums_metadata: Metadata for unit enums
        allowed_enums_metadata: Metadata for allowed value enums
        vspec_comments: Comments data for fields and types
        output_dir: Directory to write modular files to
        flat_domains: If True, flat structure; if False, nested structure

    Raises:
        S2DMExporterException: If writing modular files fails
    """
    try:
        # Write common files (directives, scalars, enums, query root)
        write_common_files(schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments, output_dir)

        # Analyze schema structure
        if flat_domains:
            domain_structure = analyze_schema_for_flat_domains(schema)
        else:
            domain_structure = analyze_schema_for_nested_domains(schema)

        # Write domain-specific files
        write_domain_files(
            domain_structure, schema, output_dir, vspec_comments, directive_processor, allowed_enums_metadata
        )

    except Exception as e:
        raise S2DMExporterException(f"Failed to write modular schema files: {e}") from e

# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Utilities for modular GraphQL schema export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from graphql import GraphQLEnumType, GraphQLSchema, is_enum_type, is_object_type, print_type


def analyze_schema_for_flat_domains(schema: GraphQLSchema) -> dict[str, list[str]]:
    """
    Analyze GraphQL schema and create flat domain file structure.

    Each object type gets its own file, named exactly after the type (no transformation).
    Files are organized in domain/ directory with flat structure.
    Instance tags get their own files in instances/ directory.

    Returns:
        Dict mapping file paths to list of type names to include
    """
    domain_files: dict[str, list[str]] = {}

    # Process all object types - put each in its own file with exact type name
    for type_name, graphql_type in schema.type_map.items():
        # Skip built-in types and Query type
        if type_name.startswith("__") or type_name == "Query":
            continue

        if is_object_type(graphql_type):
            # Instance tag types get their own file in instances/
            if "InstanceTag" in type_name:
                instance_file = f"instances/{type_name}.graphql"
                if instance_file not in domain_files:
                    domain_files[instance_file] = []
                domain_files[instance_file].append(type_name)
            else:
                # Regular object types get their own file in domain/
                file_name = f"domain/{type_name}.graphql"
                domain_files[file_name] = [type_name]
        elif is_enum_type(graphql_type):
            # Group enums by category
            if "UnitEnum" in type_name:
                # Unit enums go to other/units.graphql
                enum_file = "other/units.graphql"
                if enum_file not in domain_files:
                    domain_files[enum_file] = []
                domain_files[enum_file].append(type_name)
            elif "InstanceTag" in type_name:
                # Instance tag dimensional enums go with their parent InstanceTag type
                # Extract the base instance tag name (remove _Dimension1, _Dimension2, etc.)
                base_name = type_name
                if "_Dimension" in type_name:
                    base_name = type_name.split("_Dimension")[0]

                instance_file = f"instances/{base_name}.graphql"
                if instance_file not in domain_files:
                    domain_files[instance_file] = []
                domain_files[instance_file].append(type_name)
            elif type_name in ["VspecElementKind", "VspecType"]:
                # Schema meta enums go to directives file (they belong together)
                enum_file = "other/directives.graphql"
                if enum_file not in domain_files:
                    domain_files[enum_file] = []
                domain_files[enum_file].append(type_name)
            else:
                # Domain-specific enums - create their own files in domain/
                enum_file = f"domain/{type_name}.graphql"
                domain_files[enum_file] = [type_name]

    return domain_files


def analyze_schema_for_nested_domains(schema: GraphQLSchema) -> dict[str, list[str]]:
    """
    Analyze GraphQL schema and create nested domain structure based on type relationships.

    Groups related types into domain directories following the hierarchy.
    Instance tags get their own files in instances/ directory.

    Returns:
        Dict mapping file paths to list of type names to include
    """
    # Start from Vehicle type and build hierarchy
    vehicle_type = schema.type_map.get("Vehicle")
    if not vehicle_type or not is_object_type(vehicle_type):
        # Fallback to flat structure if no Vehicle type
        return analyze_schema_for_flat_domains(schema)

    # Group types by their name prefixes (Vehicle_Body -> domain/Vehicle/Body.graphql)
    type_groups: dict[str, list[str]] = {}

    for type_name, graphql_type in schema.type_map.items():
        if type_name.startswith("__") or type_name == "Query":
            continue

        if is_object_type(graphql_type):
            # Instance tag types get their own file in instances/
            if "InstanceTag" in type_name:
                instance_file = f"instances/{type_name}.graphql"
                if instance_file not in type_groups:
                    type_groups[instance_file] = []
                type_groups[instance_file].append(type_name)
            else:
                # Extract domain hierarchy from type name
                if "_" in type_name:
                    # Vehicle_Body_Lights -> domain/Vehicle/Body/Lights.graphql
                    parts = type_name.split("_")
                    if len(parts) >= 2:
                        # Build nested path: domain/Vehicle/Body/Lights.graphql
                        domain_path = "domain/" + "/".join(parts[:-1]) + f"/{parts[-1]}.graphql"
                    else:
                        domain_path = f"domain/{parts[0]}.graphql"
                else:
                    domain_path = f"domain/{type_name}.graphql"

                if domain_path not in type_groups:
                    type_groups[domain_path] = []
                type_groups[domain_path].append(type_name)
        elif is_enum_type(graphql_type):
            # Group enums by category
            if "UnitEnum" in type_name:
                # Unit enums go to other/units.graphql
                enum_file = "other/units.graphql"
                if enum_file not in type_groups:
                    type_groups[enum_file] = []
                type_groups[enum_file].append(type_name)
            elif "InstanceTag" in type_name:
                # Instance tag dimensional enums go with their parent InstanceTag type
                # Extract the base instance tag name (remove _Dimension1, _Dimension2, etc.)
                base_name = type_name
                if "_Dimension" in type_name:
                    base_name = type_name.split("_Dimension")[0]

                instance_file = f"instances/{base_name}.graphql"
                if instance_file not in type_groups:
                    type_groups[instance_file] = []
                type_groups[instance_file].append(type_name)
            elif type_name in ["VspecElementKind", "VspecType"]:
                # Schema meta enums go to directives file (they belong together)
                enum_file = "other/directives.graphql"
                if enum_file not in type_groups:
                    type_groups[enum_file] = []
                type_groups[enum_file].append(type_name)
            else:
                # Domain-specific enums - place in nested domain structure
                if "_" in type_name:
                    # Vehicle_Cabin_DriverPosition_Enum -> domain/vehicle/cabin/DriverPosition_Enum.graphql
                    parts = type_name.split("_")
                    if len(parts) >= 2:
                        # Build nested path
                        enum_path = "domain/" + "/".join(parts[:-1]) + f"/{parts[-1]}.graphql"
                    else:
                        enum_path = f"domain/{parts[0]}.graphql"
                else:
                    enum_path = f"domain/{type_name}.graphql"

                if enum_path not in type_groups:
                    type_groups[enum_path] = []
                type_groups[enum_path].append(type_name)

    return type_groups


def write_domain_files(
    domain_structure: dict[str, list[str]],
    schema: GraphQLSchema,
    output_dir: Path,
    vspec_comments: dict[str, Any],
    directive_processor: Any,
) -> None:
    """
    Write domain-specific GraphQL files.

    Args:
        domain_structure: Mapping of file paths to type names
        schema: GraphQL schema containing the types
        output_dir: Output directory
        vspec_comments: VSS comments for directive processing
        directive_processor: Processor for adding @vspec directives
    """
    for file_path, type_names in domain_structure.items():
        if not type_names:
            continue

        # Create domain file
        domain_file = output_dir / file_path
        domain_file.parent.mkdir(parents=True, exist_ok=True)

        # Special handling for directives file with schema enums
        if file_path == "other/directives.graphql":
            # This file will be handled by write_common_files with schema enums included
            # Skip processing it here to avoid duplication
            continue
        # Special handling for instance files
        if file_path.startswith("instances/"):
            content_parts = ["# Instance tag type and dimensional enums\n"]

            # Separate instance tag types from dimensional enums
            instance_tag_types = []
            dimensional_enums = []

            for type_name in type_names:
                if type_name in schema.type_map:
                    graphql_type = schema.type_map[type_name]
                    if is_object_type(graphql_type) and "InstanceTag" in type_name:
                        instance_tag_types.append(type_name)
                    elif is_enum_type(graphql_type) and "InstanceTag" in type_name:
                        dimensional_enums.append(type_name)

            # Write instance tag types first
            for type_name in instance_tag_types:
                if type_name in schema.type_map:
                    graphql_type = schema.type_map[type_name]
                    type_sdl = print_type(graphql_type)

                    # Add @instanceTag directive to instance tag types
                    if "InstanceTag" in type_name:
                        type_sdl = type_sdl.replace(f"type {type_name}", f"type {type_name} @instanceTag")

                    content_parts.append(type_sdl)

            # Write dimensional enums after instance tag types
            for type_name in dimensional_enums:
                if type_name in schema.type_map:
                    graphql_type = schema.type_map[type_name]
                    type_sdl = print_type(graphql_type)
                    content_parts.append(type_sdl)
        else:
            # Regular domain files
            content_parts = ["# Domain-specific GraphQL types\n"]

            for type_name in type_names:
                if type_name in schema.type_map:
                    graphql_type = schema.type_map[type_name]
                    type_sdl = print_type(graphql_type)

                    # Apply vspec directives if available
                    if directive_processor and hasattr(directive_processor, "add_directives_to_type"):
                        try:
                            enhanced_sdl = directive_processor.add_directives_to_type(
                                type_sdl, type_name, vspec_comments
                            )
                            content_parts.append(enhanced_sdl)
                        except (AttributeError, TypeError):
                            # Fallback to plain SDL if directive processing fails
                            content_parts.append(type_sdl)
                    else:
                        content_parts.append(type_sdl)

        # Write the file
        with open(domain_file, "w") as f:
            f.write("\n\n".join(content_parts))


def write_common_files(
    schema: GraphQLSchema,
    unit_enums_metadata: dict[str, Any],
    allowed_enums_metadata: dict[str, Any],
    vspec_comments: dict[str, Any],
    output_dir: Path,
) -> None:
    """
    Write common GraphQL files (directives, scalars, queries) using GraphQL introspection.

    Args:
        schema: GraphQL schema to extract components from
        unit_enums_metadata: Metadata for unit enums
        allowed_enums_metadata: Metadata for allowed value enums
        vspec_comments: VSS comments for directive processing
        output_dir: Output directory
    """
    from graphql import is_scalar_type, print_type

    from vss_tools.utils.graphql_utils import extract_custom_directives_from_schema

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create other directory for common files
    other_dir = output_dir / "other"
    other_dir.mkdir(parents=True, exist_ok=True)

    # Extract and write directives using GraphQL introspection
    custom_directives = extract_custom_directives_from_schema(schema)

    if custom_directives:
        directives_content = ["# GraphQL directive definitions\n"]

        # For each custom directive, use GraphQL's print function or reconstruct the SDL
        for directive_name, directive_obj in custom_directives.items():
            # Build directive definition string
            args_parts = []
            for arg_name, arg in directive_obj.args.items():
                arg_type_str = str(arg.type)
                if arg.default_value is not None:
                    args_parts.append(f"  {arg_name}: {arg_type_str} = {arg.default_value}")
                else:
                    args_parts.append(f"  {arg_name}: {arg_type_str}")

                # Add description if available
                if arg.description:
                    args_parts[-1] = f'  """{arg.description}"""\n  {args_parts[-1].strip()}'

            # Build locations string
            locations = " | ".join([loc.name for loc in directive_obj.locations])

            # Construct the directive
            directive_def = f"directive @{directive_name}"
            if args_parts:
                directive_def += f"(\n{chr(10).join(args_parts)}\n)"
            directive_def += f" on {locations}"

            directives_content.append(directive_def)

        # Add schema enums that belong with directives (VspecElementKind, VspecType, etc.)
        schema_enums = []
        for type_name, type_def in schema.type_map.items():
            if isinstance(type_def, GraphQLEnumType) and type_name in ["VspecElementKind", "VspecType"]:
                schema_enums.append(print_type(type_def))

        if schema_enums:
            directives_content.extend(schema_enums)

        with open(other_dir / "directives.graphql", "w") as f:
            f.write("\n\n".join(directives_content))

    # Extract custom scalars using GraphQL introspection
    custom_scalars = []
    for type_name, type_def in schema.type_map.items():
        if (
            is_scalar_type(type_def)
            and not type_name.startswith("__")
            and type_name not in ["String", "Int", "Float", "Boolean", "ID"]
        ):
            custom_scalars.append(print_type(type_def))

    if custom_scalars:
        with open(other_dir / "scalars.graphql", "w") as f:
            f.write("# GraphQL scalar type definitions\n\n")
            f.write("\n\n".join(custom_scalars))

    # Extract Query type and schema definition
    query_parts = []
    if "Query" in schema.type_map:
        query_parts.append(print_type(schema.type_map["Query"]))

    # Add schema definition if needed
    if schema.query_type or schema.mutation_type or schema.subscription_type:
        schema_def_parts = ["schema {"]
        if schema.query_type:
            schema_def_parts.append(f"  query: {schema.query_type.name}")
        if schema.mutation_type:
            schema_def_parts.append(f"  mutation: {schema.mutation_type.name}")
        if schema.subscription_type:
            schema_def_parts.append(f"  subscription: {schema.subscription_type.name}")
        schema_def_parts.append("}")
        query_parts.append("\n".join(schema_def_parts))

    if query_parts:
        with open(other_dir / "queries.graphql", "w") as f:
            f.write("# GraphQL query and schema definitions\n\n")
            f.write("\n\n".join(query_parts))

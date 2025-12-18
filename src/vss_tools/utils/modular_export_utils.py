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
from typing import Any, cast

from graphql import GraphQLEnumType, GraphQLObjectType, GraphQLSchema, is_enum_type, is_object_type, print_type


def analyze_schema_for_flat_domains(schema: GraphQLSchema) -> dict[str, list[str]]:
    """
    Analyze GraphQL schema and create flat domain file structure.

    Each object type gets its own file, named exactly after the type (no transformation).
    Files are organized in domain/ directory with flat structure.
    Instance tags get their own files in instances/ directory.
    Struct types get their own files in structs/ directory.

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
            # Check if this is a struct type by examining the schema's vspec_comments
            # Structs are identified by having type metadata with vspec_type="STRUCT"
            # Note: We'll need to check this via metadata passed separately
            # For now, use naming convention - types from VehicleDataTypes tree
            elif type_name.startswith("VehicleDataTypes"):
                # Struct types go to structs/ directory
                struct_file = f"structs/{type_name}.graphql"
                domain_files[struct_file] = [type_name]
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
            elif type_name in ["VspecElement"]:
                # Schema meta enums go to directives file (they belong together)
                enum_file = "other/directives.graphql"
                if enum_file not in domain_files:
                    domain_files[enum_file] = []
                domain_files[enum_file].append(type_name)
            # Note: Domain-specific allowed value enums are NOT added to separate files
            # They will be embedded in the type files that use them
            # This is handled in write_domain_files()

    return domain_files


def analyze_schema_for_nested_domains(schema: GraphQLSchema) -> dict[str, list[str]]:
    """
    Analyze GraphQL schema and create nested domain structure with _ prefix for root types.

    Groups related types into domain directories following the hierarchy.
    Filenames use only the immediate type name (no parent prefix) since folder path provides context.
    Root types in each folder use _ prefix to sort first.

    Example:
        Vehicle type -> domain/Vehicle/_Vehicle.graphql
        Vehicle_Body type -> domain/Vehicle/Body.graphql
        Vehicle_Cabin type -> domain/Vehicle/Cabin/_Cabin.graphql
        Vehicle_Cabin_Door type -> domain/Vehicle/Cabin/Door.graphql
        Vehicle_Cabin_Seat type -> domain/Vehicle/Cabin/Seat/_Seat.graphql
        Vehicle_Cabin_Seat_Airbag type -> domain/Vehicle/Cabin/Seat/Airbag.graphql

    Returns:
        Dict mapping file paths to list of type names to include
    """
    # Start from Vehicle type and build hierarchy
    vehicle_type = schema.type_map.get("Vehicle")
    if not vehicle_type or not is_object_type(vehicle_type):
        # Fallback to flat structure if no Vehicle type
        return analyze_schema_for_flat_domains(schema)

    # Group types by their name prefixes
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
            # Struct types go to structs/
            elif type_name.startswith("VehicleDataTypes"):
                struct_file = f"structs/{type_name}.graphql"
                type_groups[struct_file] = [type_name]
            else:
                # Extract domain hierarchy from type name
                if "_" in type_name:
                    # Vehicle_Cabin_Seat_Airbag -> domain/Vehicle/Cabin/Seat/Airbag.graphql
                    parts = type_name.split("_")
                    if len(parts) >= 2:
                        # Check if this is a "root" for its nesting level or a leaf
                        # A type is a root if it has children (i.e., there's a type with this as prefix)
                        # We determine this by checking if any type starts with this type's name + "_"
                        type_prefix = type_name + "_"
                        has_children = any(
                            t.startswith(type_prefix) and is_object_type(schema.type_map[t])
                            for t in schema.type_map.keys()
                            if not t.startswith("__") and t != "Query"
                        )

                        if has_children:
                            # This is a root for its folder level - create folder for it with _ prefix
                            # e.g., Vehicle_Cabin -> domain/Vehicle/Cabin/_Cabin.graphql
                            folder_path = "/".join(parts)
                            filename = f"_{parts[-1]}.graphql"
                        else:
                            # This is a leaf - goes in parent folder without prefix
                            # e.g., Vehicle_Cabin_Door -> domain/Vehicle/Cabin/Door.graphql
                            folder_path = "/".join(parts[:-1])
                            filename = f"{parts[-1]}.graphql"

                        domain_path = f"domain/{folder_path}/{filename}"
                    else:
                        # Single part type -> domain/TypeName/_TypeName.graphql
                        domain_path = f"domain/{parts[0]}/_{parts[0]}.graphql"
                else:
                    # No underscore -> domain/TypeName/_TypeName.graphql
                    domain_path = f"domain/{type_name}/_{type_name}.graphql"

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
            elif type_name in ["VspecElement"]:
                # Schema meta enums go to directives file (they belong together)
                enum_file = "other/directives.graphql"
                if enum_file not in type_groups:
                    type_groups[enum_file] = []
                type_groups[enum_file].append(type_name)
            # Note: Domain-specific allowed value enums are NOT added to separate files
            # They will be embedded in the type files that use them
            # This is handled in write_domain_files()

    return type_groups


def write_domain_files(
    domain_structure: dict[str, list[str]],
    schema: GraphQLSchema,
    output_dir: Path,
    vspec_comments: dict[str, Any],
    directive_processor: Any,
    allowed_enums_metadata: dict[str, Any],
) -> None:
    """
    Write domain-specific GraphQL files.

    Args:
        domain_structure: Mapping of file paths to type names
        schema: GraphQL schema containing the types
        output_dir: Output directory
        vspec_comments: VSS comments for directive processing
        directive_processor: Processor for adding @vspec directives
        allowed_enums_metadata: Metadata for allowed value enums
    """
    for file_path, type_names in domain_structure.items():
        if not type_names:
            continue

        domain_file = output_dir / file_path
        domain_file.parent.mkdir(parents=True, exist_ok=True)

        # Special handling for directives file with schema enums
        if file_path == "other/directives.graphql":
            continue
        # Special handling for instance files
        if file_path.startswith("instances/"):
            content_parts = ["# Instance tag type and dimensional enums\n"]
            instance_tag_types = []
            dimensional_enums = []
            for type_name in type_names:
                if type_name in schema.type_map:
                    graphql_type = schema.type_map[type_name]
                    if is_object_type(graphql_type) and "InstanceTag" in type_name:
                        instance_tag_types.append(type_name)
                    elif is_enum_type(graphql_type) and "InstanceTag" in type_name:
                        dimensional_enums.append(type_name)
            for type_name in instance_tag_types:
                if type_name in schema.type_map:
                    graphql_type = schema.type_map[type_name]
                    type_sdl = print_type(graphql_type)
                    content_parts.append(type_sdl)
            for type_name in dimensional_enums:
                if type_name in schema.type_map:
                    graphql_type = schema.type_map[type_name]
                    type_sdl = print_type(graphql_type)
                    content_parts.append(type_sdl)

            # Join all content parts and apply directives
            file_content = "\n\n".join(content_parts)

            # Apply vspec directives to instance tag files
            if directive_processor and hasattr(directive_processor, "process_schema"):
                lines = file_content.split("\n")
                lines = directive_processor._process_type_directives(lines, vspec_comments)
                file_content = "\n".join(lines)

            with open(domain_file, "w") as f:
                f.write(file_content)
            continue
        else:
            # Regular domain files
            content_parts = ["# Domain-specific GraphQL types\n"]
            for type_name in type_names:
                if type_name in schema.type_map:
                    graphql_type = schema.type_map[type_name]
                    type_sdl = print_type(graphql_type)

                    # Find allowed value enums used by this type
                    allowed_enums_sdl = []
                    if is_object_type(graphql_type):
                        # Type guard ensures graphql_type is GraphQLObjectType here
                        object_type = cast(GraphQLObjectType, graphql_type)
                        for field in object_type.fields.values():
                            field_type = field.type
                            # Unwrap NonNull and List
                            while hasattr(field_type, "of_type"):
                                field_type = field_type.of_type
                            if is_enum_type(field_type):
                                enum_type = field_type
                                # Only include enums that are not built-in (i.e., allowed value enums)
                                is_allowed_enum = enum_type.name in schema.type_map and enum_type.name not in [
                                    "VspecElement",
                                ]
                                if is_allowed_enum:
                                    enum_sdl = print_type(enum_type)
                                    # Only add if not already present in this file
                                    if enum_sdl not in allowed_enums_sdl:
                                        allowed_enums_sdl.append(enum_sdl)

                    # Place type definition first, then enums at the bottom
                    content_parts.append(type_sdl)
                    content_parts.extend(allowed_enums_sdl)

        # Join all content parts
        file_content = "\n\n".join(content_parts)

        # Apply vspec directives to the entire file content if directive processor is available
        if directive_processor and hasattr(directive_processor, "process_schema"):
            # Process the SDL string to add directives
            # We need to split into lines and process
            lines = file_content.split("\n")
            lines = directive_processor._process_allowed_enum_directives(lines, allowed_enums_metadata, set())
            lines = directive_processor._process_field_directives(lines, vspec_comments)
            lines = directive_processor._process_deprecated_directives(
                lines, vspec_comments.get("field_deprecated", {})
            )
            lines = directive_processor._process_range_directives(lines, vspec_comments.get("field_ranges", {}))
            lines = directive_processor._process_type_directives(lines, vspec_comments)
            file_content = "\n".join(lines)

        with open(domain_file, "w") as f:
            f.write(file_content)


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

        # Add schema enums that belong with directives (VspecElement, etc.)
        schema_enums = []
        for type_name, type_def in schema.type_map.items():
            if isinstance(type_def, GraphQLEnumType) and type_name in ["VspecElement"]:
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

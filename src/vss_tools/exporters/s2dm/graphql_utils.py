# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""
GraphQL utilities that extend graphql-core functionality.

This module provides utilities for working with GraphQL schemas that are not
available out-of-the-box in graphql-core, such as loading and merging multiple
SDL files from a directory, and GraphQL naming conventions.

Key features:
- Unified GraphQL element type enumeration covering all SDL language elements
- Consistent case conversion functions for all GraphQL element types
- Utilities for handling fully qualified names (FQNs) from VSS specifications
- Name validation and sanitization functions for GraphQL compliance
- Schema loading utilities for predefined SDL elements

This module promotes consistency across different GraphQL exporters by providing
a single source of truth for GraphQL naming conventions and schema utilities.
"""

from __future__ import annotations

import keyword
from enum import Enum
from pathlib import Path
from typing import Callable, Dict

from caseconverter import DELIMITERS, camelcase, macrocase, pascalcase
from graphql import GraphQLDirective, GraphQLSchema, build_schema


class GraphQLElementType(Enum):
    """Enumeration of GraphQL schema element types with their naming conventions."""

    TYPE = "type"
    FIELD = "field"
    ARGUMENT = "argument"
    ENUM = "enum"
    ENUM_VALUE = "enum_value"
    DIRECTIVE = "directive"
    INTERFACE = "interface"
    UNION = "union"
    INPUT = "input"
    SCALAR = "scalar"


# GraphQL standard naming conventions using caseconverter functions with dot support
# The delimiters parameter includes dots to handle names like "with.dots" properly
GRAPHQL_DELIMITERS = DELIMITERS + "."

DEFAULT_CONVERSIONS: Dict[GraphQLElementType, Callable[[str], str]] = {
    # GraphQL types: PascalCase
    GraphQLElementType.TYPE: lambda s: pascalcase(s, delimiters=GRAPHQL_DELIMITERS),
    # GraphQL fields: camelCase
    GraphQLElementType.FIELD: lambda s: camelcase(s, delimiters=GRAPHQL_DELIMITERS),
    # GraphQL arguments: camelCase
    GraphQLElementType.ARGUMENT: lambda s: camelcase(s, delimiters=GRAPHQL_DELIMITERS),
    # GraphQL enums: PascalCase
    GraphQLElementType.ENUM: lambda s: pascalcase(s, delimiters=GRAPHQL_DELIMITERS),
    # GraphQL enum values: SCREAMING_SNAKE_CASE
    GraphQLElementType.ENUM_VALUE: lambda s: macrocase(s, delimiters=GRAPHQL_DELIMITERS),
    # GraphQL directives: camelCase
    GraphQLElementType.DIRECTIVE: lambda s: camelcase(s, delimiters=GRAPHQL_DELIMITERS),
    # GraphQL interfaces: PascalCase
    GraphQLElementType.INTERFACE: lambda s: pascalcase(s, delimiters=GRAPHQL_DELIMITERS),
    # GraphQL unions: PascalCase
    GraphQLElementType.UNION: lambda s: pascalcase(s, delimiters=GRAPHQL_DELIMITERS),
    # GraphQL input types: PascalCase
    GraphQLElementType.INPUT: lambda s: pascalcase(s, delimiters=GRAPHQL_DELIMITERS),
    # GraphQL scalars: PascalCase
    GraphQLElementType.SCALAR: lambda s: pascalcase(s, delimiters=GRAPHQL_DELIMITERS),
}


def convert_name_for_graphql_schema(
    name: str,
    element_type: GraphQLElementType,
    conversions: Dict[GraphQLElementType, Callable[[str], str]] = DEFAULT_CONVERSIONS,
) -> str:
    """
    Convert name for GraphQL schema using specified conversion rules.

    This function provides a unified approach to case conversion for GraphQL elements,
    ensuring consistency across different exporters. Default conversions follow
    GraphQL best practices and use caseconverter functions with dot delimiter support.

    Args:
        name: The name to convert
        element_type: The type of GraphQL element
        conversions: Conversion rules (defaults to DEFAULT_CONVERSIONS for GraphQL best practices)

    Returns:
        The name converted to the appropriate case convention

    Examples:
        >>> convert_name_for_graphql_schema("user_name", GraphQLElementType.FIELD)
        'userName'
        >>> convert_name_for_graphql_schema("with.dots", GraphQLElementType.FIELD)
        'withDots'
        >>> convert_name_for_graphql_schema("user_type", GraphQLElementType.TYPE)
        'UserType'
        >>> convert_name_for_graphql_schema("status_active", GraphQLElementType.ENUM_VALUE)
        'STATUS_ACTIVE'
    """
    converter = conversions.get(element_type)

    # If not found, try lookup by enum value (handles different enum instances)
    if not converter:
        for key, value in conversions.items():
            if hasattr(key, "value") and hasattr(element_type, "value") and key.value == element_type.value:
                converter = value
                break

    if not converter:
        raise ValueError(f"No converter for {element_type}")

    result = converter(name)

    # Handle enum values that start with digits (GraphQL spec requirement)
    if hasattr(element_type, "value") and element_type.value == "enum_value" and result and result[0].isdigit():
        result = f"_{result}"
    elif element_type == GraphQLElementType.ENUM_VALUE and result and result[0].isdigit():
        result = f"_{result}"

    # Handle Python keywords
    if keyword.iskeyword(result):
        result += "_"

    return result


def convert_fqn_to_graphql_type_name(fqn: str, separator: str = "_") -> str:
    """
    Convert a fully qualified name (FQN) to a GraphQL type name.

    This is a specialized version for type names that handles dotted paths
    like "Vehicle.Body.Lights" and converts them to valid GraphQL type names.

    Args:
        fqn: Fully qualified name with dots as separators
        separator: Character to use between path components (default: "_")

    Returns:
        GraphQL-compatible type name

    Examples:
        >>> convert_fqn_to_graphql_type_name("Vehicle.Body.Lights")
        'Vehicle_Body_Lights'
        >>> convert_fqn_to_graphql_type_name("Vehicle.Body.Lights", "")
        'VehicleBodyLights'
    """
    parts = fqn.split(".")
    converted_parts = [convert_name_for_graphql_schema(part, GraphQLElementType.TYPE) for part in parts if part]
    return separator.join(converted_parts)


def is_valid_graphql_name(name: str) -> bool:
    """
    Check if a name is valid for GraphQL according to the specification.

    GraphQL names must match the pattern: [_A-Za-z][_0-9A-Za-z]*

    Args:
        name: The name to validate

    Returns:
        True if the name is valid, False otherwise
    """
    import re

    return bool(re.match(r"^[_A-Za-z][_0-9A-Za-z]*$", name))


def sanitize_graphql_name(name: str, element_type: GraphQLElementType) -> str:
    """
    Sanitize a name to make it valid for GraphQL.

    This function removes or replaces invalid characters and ensures
    the name follows GraphQL naming rules.

    Args:
        name: The name to sanitize
        element_type: The type of GraphQL element

    Returns:
        A valid GraphQL name
    """
    # Remove special characters and replace with underscore
    import re

    sanitized = re.sub(r"[^_A-Za-z0-9]", "_", name)

    # Track if we need to preserve a leading underscore for names starting with digits
    needs_leading_underscore = sanitized and sanitized[0].isdigit()

    # Ensure it starts with a letter or underscore
    if needs_leading_underscore:
        sanitized = f"_{sanitized}"

    # Apply appropriate case conversion
    if sanitized:
        converted = convert_name_for_graphql_schema(sanitized, element_type)
        # If we needed a leading underscore and it got removed, add it back
        if needs_leading_underscore and not converted.startswith("_") and converted[0].isdigit():
            converted = f"_{converted}"
        return converted
    else:
        return "UnknownName"


class GraphQLUtilsException(Exception):
    """Exception raised for errors in GraphQL utilities."""

    pass


def load_graphql_schema_from_path(path: Path) -> GraphQLSchema:
    """
    Load and build GraphQL schema from SDL file or directory.

    This function can handle either:
    - A single .graphql file containing SDL
    - A directory containing multiple .graphql files (which will be merged)

    Args:
        path: Path to either a .graphql file or directory containing .graphql files

    Returns:
        GraphQLSchema: Complete schema with all types, directives, etc.

    Raises:
        GraphQLUtilsException: If path doesn't exist, no .graphql files found,
                              or schema building fails

    Examples:
        >>> # Load from a single file
        >>> schema_file = Path("./schema.graphql")
        >>> schema = load_graphql_schema_from_path(schema_file)

        >>> # Load from a directory
        >>> schema_dir = Path("./schema_definitions")
        >>> schema = load_graphql_schema_from_path(schema_dir)
        >>> print(f"Schema has {len(schema.type_map)} types")
    """
    if not path.exists():
        raise GraphQLUtilsException(f"Path not found: {path}")

    # Collect SDL files based on whether it's a file or directory
    if path.is_file():
        # Single file case
        if not path.suffix == ".graphql":
            raise GraphQLUtilsException(f"File must have .graphql extension: {path}")
        sdl_files = [path]
    elif path.is_dir():
        # Directory case - collect all .graphql files
        sdl_files = list(path.glob("*.graphql"))
        if not sdl_files:
            raise GraphQLUtilsException(f"No .graphql files found in directory: {path}")
    else:
        raise GraphQLUtilsException(f"Path must be a file or directory: {path}")

    # Read and concatenate all SDL content
    combined_sdl = []

    for sdl_file in sorted(sdl_files):  # Sort for consistent ordering
        try:
            content = sdl_file.read_text(encoding="utf-8")
            # Add file comment for debugging (only for multiple files)
            if len(sdl_files) > 1:
                combined_sdl.append(f"# From {sdl_file.name}\n{content}")
            else:
                combined_sdl.append(content)
        except Exception as e:
            raise GraphQLUtilsException(f"Failed to read SDL file {sdl_file}: {e}")

    # Combine all SDL content
    full_sdl = "\n\n".join(combined_sdl)

    # Add a minimal Query type if none exists (GraphQL requires it)
    if "type Query" not in full_sdl:
        full_sdl += "\n\ntype Query { _empty: String }"

    # Build the complete schema
    try:
        return build_schema(full_sdl)
    except Exception as e:
        raise GraphQLUtilsException(f"Failed to build schema from SDL files at {path}: {e}")


def extract_custom_directives_from_schema(schema: GraphQLSchema) -> Dict[str, GraphQLDirective]:
    """
    Extract custom directives from a GraphQL schema, excluding built-in directives.

    GraphQL has built-in directives (@skip, @include, @deprecated, @specifiedBy)
    that are automatically included in every schema. This function filters those
    out and returns only custom directives defined in the schema.

    Args:
        schema: GraphQL schema to extract directives from

    Returns:
        Dictionary mapping directive names to GraphQLDirective objects

    Example:
        >>> schema = build_schema('''
        ...     directive @vspec(comment: String) on FIELD_DEFINITION
        ...     type Query { field: String }
        ... ''')
        >>> custom_directives = extract_custom_directives_from_schema(schema)
        >>> print(list(custom_directives.keys()))  # ['vspec']
    """
    # Built-in GraphQL directives that should be excluded
    builtin_directives = {"skip", "include", "deprecated", "specifiedBy"}

    custom_directives = {}

    for directive in schema.directives:
        if directive.name not in builtin_directives:
            custom_directives[directive.name] = directive

    return custom_directives


def load_predefined_schema_elements(path: Path) -> tuple[GraphQLSchema, Dict[str, GraphQLDirective]]:
    """
    Load predefined GraphQL schema elements from SDL file or directory and extract custom directives.

    This is a convenience function that combines loading a schema from SDL file(s)
    and extracting custom directives in one call.

    Args:
        path: Path to either a .graphql file or directory containing .graphql files

    Returns:
        tuple: (base_schema, custom_directives)
               - base_schema: Complete GraphQL schema from SDL file(s)
               - custom_directives: Dictionary of custom directives (excluding built-ins)

    Raises:
        GraphQLUtilsException: If path loading or schema building fails

    Examples:
        >>> # Load from a single file
        >>> schema_file = Path("./schema.graphql")
        >>> base_schema, directives = load_predefined_schema_elements(schema_file)

        >>> # Load from a directory
        >>> predefined_dir = Path("./schema_definitions")
        >>> base_schema, directives = load_predefined_schema_elements(predefined_dir)
        >>> vspec_directive = directives["vspec"]
        >>> print(f"Loaded {len(directives)} custom directives")
    """
    # Load the complete base schema from SDL file(s)
    base_schema = load_graphql_schema_from_path(path)

    # Extract custom directives for later use
    custom_directives = extract_custom_directives_from_schema(base_schema)

    return base_schema, custom_directives

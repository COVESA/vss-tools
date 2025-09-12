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
SDL files from a directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from graphql import GraphQLDirective, GraphQLSchema, build_schema


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
        if not path.suffix == '.graphql':
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
            content = sdl_file.read_text(encoding='utf-8')
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

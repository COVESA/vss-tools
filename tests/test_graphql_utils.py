# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import tempfile
from pathlib import Path

import pytest
from graphql import build_schema

from vss_tools.utils.graphql_utils import (
    GraphQLUtilsException,
    extract_custom_directives_from_schema,
    load_graphql_schema_from_path,
    load_predefined_schema_elements,
)


class TestGraphQLUtils:
    """Test cases for GraphQL utilities."""

    def test_load_graphql_schema_from_path_success(self):
        """Test successful loading of schema from directory with multiple SDL files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            # Create test SDL files
            (schema_dir / "directives.graphql").write_text("""
                directive @vspec(comment: String) on FIELD_DEFINITION
                directive @range(min: Float, max: Float) on FIELD_DEFINITION
            """)
            
            (schema_dir / "scalars.graphql").write_text("""
                scalar Int8
                scalar UInt8
            """)
            
            (schema_dir / "types.graphql").write_text("""
                type Vehicle {
                    id: ID!
                    speed: Float @vspec(comment: "Vehicle speed")
                }
            """)
            
            # Load schema using the new function
            schema = load_graphql_schema_from_path(schema_dir)
            
            # Verify schema was built correctly
            assert schema is not None
            assert "Vehicle" in schema.type_map
            assert "Int8" in schema.type_map
            assert "UInt8" in schema.type_map
            
            # Verify directives are present
            directive_names = {directive.name for directive in schema.directives}
            assert "vspec" in directive_names
            assert "range" in directive_names

    def test_load_graphql_schema_from_path_single_file(self):
        """Test successful loading of schema from a single SDL file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_file = Path(temp_dir) / "schema.graphql"
            
            # Create single test SDL file
            schema_file.write_text("""
                directive @vspec(comment: String) on FIELD_DEFINITION
                scalar Int8
                scalar UInt8
                
                type Vehicle {
                    id: ID!
                    speed: Float @vspec(comment: "Vehicle speed")
                }
                
                type Query {
                    vehicle: Vehicle
                }
            """)
            
            # Load schema
            schema = load_graphql_schema_from_path(schema_file)
            
            # Verify schema was built correctly
            assert schema is not None
            assert "Vehicle" in schema.type_map
            assert "Int8" in schema.type_map
            assert "UInt8" in schema.type_map
            
            # Verify directives are present
            directive_names = {directive.name for directive in schema.directives}
            assert "vspec" in directive_names
            
            # Verify Query type exists
            query_type = schema.query_type
            assert query_type is not None
            assert query_type.name == "Query"

    def test_load_graphql_schema_from_path_file_not_found(self):
        """Test error when file doesn't exist."""
        non_existent_file = Path("/non/existent/file.graphql")
        
        with pytest.raises(GraphQLUtilsException, match="Path not found"):
            load_graphql_schema_from_path(non_existent_file)

    def test_load_graphql_schema_from_path_invalid_file_extension(self):
        """Test error when file doesn't have .graphql extension."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as temp_file:
            file_path = Path(temp_file.name)
            
            with pytest.raises(GraphQLUtilsException, match="File must have .graphql extension"):
                load_graphql_schema_from_path(file_path)

    def test_load_graphql_schema_from_path_directory_no_files(self):
        """Test error when directory has no .graphql files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            # Create non-.graphql file
            (schema_dir / "readme.txt").write_text("No GraphQL files here")
            
            with pytest.raises(GraphQLUtilsException, match="No .graphql files found in directory"):
                load_graphql_schema_from_path(schema_dir)

    def test_load_graphql_schema_from_path_backward_compatibility(self):
        """Test that the old function still works for backward compatibility."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            # Create test SDL file
            (schema_dir / "schema.graphql").write_text("""
                type Vehicle {
                    id: ID!
                }
            """)
            
            # Test old function
            schema = load_graphql_schema_from_path(schema_dir)
            
            # Verify schema was built correctly
            assert schema is not None
            assert "Vehicle" in schema.type_map

    def test_load_graphql_schema_from_path_success_old_function(self):
        """Test successful loading of schema from directory with multiple SDL files (old function)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            # Create test SDL files
            (schema_dir / "directives.graphql").write_text("""
                directive @vspec(comment: String) on FIELD_DEFINITION
                directive @range(min: Float, max: Float) on FIELD_DEFINITION
            """)
            
            (schema_dir / "scalars.graphql").write_text("""
                scalar Int8
                scalar UInt8
            """)
            
            (schema_dir / "types.graphql").write_text("""
                type Vehicle {
                    id: ID!
                    speed: Float @vspec(comment: "Vehicle speed")
                }
            """)
            
            # Load schema using old function for backward compatibility
            schema = load_graphql_schema_from_path(schema_dir)
            
            # Verify schema was built correctly
            assert schema is not None
            assert "Vehicle" in schema.type_map
            assert "Int8" in schema.type_map
            assert "UInt8" in schema.type_map
            
            # Verify directives are present
            directive_names = {directive.name for directive in schema.directives}
            assert "vspec" in directive_names
            assert "range" in directive_names
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            # Create test SDL files
            (schema_dir / "directives.graphql").write_text("""
                directive @vspec(comment: String) on FIELD_DEFINITION
                directive @range(min: Float, max: Float) on FIELD_DEFINITION
            """)
            
            (schema_dir / "scalars.graphql").write_text("""
                scalar Int8
                scalar UInt8
            """)
            
            (schema_dir / "types.graphql").write_text("""
                type Vehicle {
                    id: ID!
                    speed: Float @vspec(comment: "Vehicle speed")
                }
            """)
            
            # Load schema
            schema = load_graphql_schema_from_path(schema_dir)
            
            # Verify schema was built correctly
            assert schema is not None
            assert "Vehicle" in schema.type_map
            assert "Int8" in schema.type_map
            assert "UInt8" in schema.type_map
            
            # Verify directives are present
            directive_names = {directive.name for directive in schema.directives}
            assert "vspec" in directive_names
            assert "range" in directive_names

    def test_load_graphql_schema_from_path_with_query_type(self):
        """Test loading schema that already has a Query type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            (schema_dir / "schema.graphql").write_text("""
                type Query {
                    vehicle: Vehicle
                }
                
                type Vehicle {
                    id: ID!
                }
            """)
            
            schema = load_graphql_schema_from_path(schema_dir)
            
            # Verify Query type exists and has the right field
            query_type = schema.query_type
            assert query_type is not None
            assert query_type.name == "Query"
            assert "vehicle" in query_type.fields

    def test_load_graphql_schema_from_path_directory_not_found(self):
        """Test error when directory doesn't exist."""
        non_existent_dir = Path("/non/existent/directory")
        
        with pytest.raises(GraphQLUtilsException, match="Path not found"):
            load_graphql_schema_from_path(non_existent_dir)

    def test_load_graphql_schema_from_path_not_a_directory(self):
        """Test error when path is not a directory."""
        with tempfile.NamedTemporaryFile() as temp_file:
            file_path = Path(temp_file.name)
            
            with pytest.raises(GraphQLUtilsException, match="File must have .graphql extension"):
                load_graphql_schema_from_path(file_path)

    def test_load_graphql_schema_from_path_no_graphql_files(self):
        """Test error when no .graphql files found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            # Create non-.graphql file
            (schema_dir / "readme.txt").write_text("No GraphQL files here")
            
            with pytest.raises(GraphQLUtilsException, match="No .graphql files found"):
                load_graphql_schema_from_path(schema_dir)

    def test_load_graphql_schema_from_path_invalid_sdl(self):
        """Test error when SDL content is invalid."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            (schema_dir / "invalid.graphql").write_text("""
                invalid graphql syntax here !!!
            """)
            
            with pytest.raises(GraphQLUtilsException, match="Failed to build schema"):
                load_graphql_schema_from_path(schema_dir)

    def test_load_graphql_schema_from_path_file_read_error(self):
        """Test error when SDL file cannot be read."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            # Create a file with invalid encoding
            invalid_file = schema_dir / "invalid.graphql"
            invalid_file.write_bytes(b'\xff\xfe\x00\x00invalid_utf8')
            
            with pytest.raises(GraphQLUtilsException, match="Failed to read SDL file"):
                load_graphql_schema_from_path(schema_dir)

    def test_extract_custom_directives_from_schema(self):
        """Test extraction of custom directives from schema."""
        schema = build_schema("""
            directive @vspec(comment: String) on FIELD_DEFINITION
            directive @range(min: Float, max: Float) on FIELD_DEFINITION
            directive @instanceTag on OBJECT
            
            type Query {
                field: String @vspec(comment: "test")
            }
        """)
        
        custom_directives = extract_custom_directives_from_schema(schema)
        
        # Should contain custom directives but not built-in ones
        assert "vspec" in custom_directives
        assert "range" in custom_directives
        assert "instanceTag" in custom_directives
        
        # Should not contain built-in directives
        assert "skip" not in custom_directives
        assert "include" not in custom_directives
        assert "deprecated" not in custom_directives
        assert "specifiedBy" not in custom_directives

    def test_extract_custom_directives_empty_schema(self):
        """Test extraction from schema with no custom directives."""
        schema = build_schema("""
            type Query {
                field: String
            }
        """)
        
        custom_directives = extract_custom_directives_from_schema(schema)
        
        # Should be empty since no custom directives defined
        assert len(custom_directives) == 0

    def test_load_predefined_schema_elements(self):
        """Test loading predefined schema elements (combined function)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            (schema_dir / "directives.graphql").write_text("""
                directive @vspec(comment: String) on FIELD_DEFINITION
                directive @range(min: Float, max: Float) on FIELD_DEFINITION
            """)
            
            (schema_dir / "types.graphql").write_text("""
                type Vehicle {
                    id: ID!
                    speed: Float @vspec(comment: "Vehicle speed")
                }
            """)
            
            # Load both schema and directives
            base_schema, custom_directives = load_predefined_schema_elements(schema_dir)
            
            # Verify schema
            assert base_schema is not None
            assert "Vehicle" in base_schema.type_map
            
            # Verify custom directives were extracted
            assert "vspec" in custom_directives
            assert "range" in custom_directives
            
            # Verify built-in directives are not included
            assert "skip" not in custom_directives
            assert "deprecated" not in custom_directives

    def test_file_ordering_consistency(self):
        """Test that files are processed in consistent order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schema_dir = Path(temp_dir)
            
            # Create files in specific order to test sorting
            (schema_dir / "z_last.graphql").write_text('scalar ZLast')
            (schema_dir / "a_first.graphql").write_text('scalar AFirst')
            (schema_dir / "m_middle.graphql").write_text('scalar MMiddle')
            
            schema = load_graphql_schema_from_path(schema_dir)
            
            # All scalars should be present regardless of file order
            assert "ZLast" in schema.type_map
            assert "AFirst" in schema.type_map
            assert "MMiddle" in schema.type_map

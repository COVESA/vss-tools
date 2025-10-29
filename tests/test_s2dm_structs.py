# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""Tests for S2DM exporter struct support."""

from pathlib import Path

import pytest
from graphql import GraphQLList, GraphQLNonNull, GraphQLObjectType, is_object_type
from vss_tools.exporters.s2dm import generate_s2dm_schema
from vss_tools.exporters.s2dm.exporter import S2DM_CONVERSIONS
from vss_tools.main import get_trees
from vss_tools.utils.graphql_scalars import VSS_DATATYPE_MAP
from vss_tools.utils.graphql_utils import GraphQLElementType, convert_name_for_graphql_schema


class TestS2DMStructs:
    """Test class for S2DM GraphQL exporter struct support."""

    @pytest.fixture
    def struct_trees(self):
        """Load VSS trees with struct types."""
        tree, data_type_tree = get_trees(
            vspec=Path("tests/vspec/test_structs/test_s2dm_structs.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(),
            units=(),
            types=(Path("tests/vspec/test_structs/VehicleDataTypes.vspec"),),
            overlays=(),
            expand=False,
        )
        return tree, data_type_tree

    def test_data_type_tree_is_captured(self, struct_trees):
        """Test that data_type_tree is properly captured from get_trees."""
        tree, data_type_tree = struct_trees
        assert tree is not None
        assert data_type_tree is not None
        assert data_type_tree.name == "VehicleDataTypes"

    def test_struct_types_are_created(self, struct_trees):
        """Test that struct types are converted to GraphQL object types."""
        tree, data_type_tree = struct_trees
        schema, _, _, vspec_comments = generate_s2dm_schema(tree, data_type_tree)

        # Check that struct types exist in the schema
        nested_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.NestedStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )
        parent_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.ParentStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )

        assert nested_struct_name in schema.type_map
        assert parent_struct_name in schema.type_map

        # Check that they are object types
        assert is_object_type(schema.type_map[nested_struct_name])
        assert is_object_type(schema.type_map[parent_struct_name])

        # Check metadata
        assert nested_struct_name in vspec_comments["vss_types"]
        assert vspec_comments["vss_types"][nested_struct_name]["vspec_type"] == "STRUCT"

    def test_struct_properties_are_non_null(self, struct_trees):
        """Test that all struct properties are non-null fields."""
        tree, data_type_tree = struct_trees
        schema, _, _, _ = generate_s2dm_schema(tree, data_type_tree)

        # Get NestedStruct type
        nested_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.NestedStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )
        nested_struct_type = schema.type_map[nested_struct_name]

        # Check that all fields are non-null
        assert isinstance(nested_struct_type, GraphQLObjectType)
        for field_name, field in nested_struct_type.fields.items():
            assert isinstance(field.type, GraphQLNonNull), f"Field {field_name} should be non-null"

    def test_struct_properties_have_correct_types(self, struct_trees):
        """Test that struct properties map to correct GraphQL types."""
        tree, data_type_tree = struct_trees
        schema, _, _, _ = generate_s2dm_schema(tree, data_type_tree)

        # Get NestedStruct type
        nested_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.NestedStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )
        nested_struct_type = schema.type_map[nested_struct_name]

        # Check field types
        assert isinstance(nested_struct_type, GraphQLObjectType)
        fields = nested_struct_type.fields

        # x, y, z properties should all be double (Float in GraphQL)
        assert "x" in fields
        assert "y" in fields
        assert "z" in fields

        # Check that the unwrapped type is Float
        for field_name in ["x", "y", "z"]:
            field_type = fields[field_name].type
            assert isinstance(field_type, GraphQLNonNull)
            # The wrapped type should be Float (double maps to Float)
            assert field_type.of_type == VSS_DATATYPE_MAP["double"]

    def test_nested_struct_references(self, struct_trees):
        """Test that structs can reference other structs."""
        tree, data_type_tree = struct_trees
        schema, _, _, _ = generate_s2dm_schema(tree, data_type_tree)

        # Get ParentStruct type
        parent_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.ParentStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )
        parent_struct_type = schema.type_map[parent_struct_name]

        # Get NestedStruct type
        nested_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.NestedStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )

        # Check that x_property and y_property reference NestedStruct
        assert isinstance(parent_struct_type, GraphQLObjectType)
        fields = parent_struct_type.fields

        # x_property should reference NestedStruct
        assert "xProperty" in fields  # camelCase conversion
        x_property_type = fields["xProperty"].type
        assert isinstance(x_property_type, GraphQLNonNull)
        assert x_property_type.of_type == schema.type_map[nested_struct_name]

        # y_property should also reference NestedStruct (using FQN)
        assert "yProperty" in fields
        y_property_type = fields["yProperty"].type
        assert isinstance(y_property_type, GraphQLNonNull)
        assert y_property_type.of_type == schema.type_map[nested_struct_name]

    def test_struct_array_properties(self, struct_trees):
        """Test that struct array properties are correctly handled."""
        tree, data_type_tree = struct_trees
        schema, _, _, _ = generate_s2dm_schema(tree, data_type_tree)

        # Get ParentStruct type
        parent_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.ParentStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )
        parent_struct_type = schema.type_map[parent_struct_name]

        # Get NestedStruct type
        nested_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.NestedStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )

        # Check array properties
        assert isinstance(parent_struct_type, GraphQLObjectType)
        fields = parent_struct_type.fields

        # x_properties should be an array of NestedStruct
        assert "xProperties" in fields
        x_properties_type = fields["xProperties"].type
        assert isinstance(x_properties_type, GraphQLNonNull)
        assert isinstance(x_properties_type.of_type, GraphQLList)
        assert isinstance(x_properties_type.of_type.of_type, GraphQLNonNull)
        assert x_properties_type.of_type.of_type.of_type == schema.type_map[nested_struct_name]

        # y_properties should also be an array of NestedStruct
        assert "yProperties" in fields
        y_properties_type = fields["yProperties"].type
        assert isinstance(y_properties_type, GraphQLNonNull)
        assert isinstance(y_properties_type.of_type, GraphQLList)

    def test_signal_with_struct_datatype(self, struct_trees):
        """Test that signals can use struct datatypes."""
        tree, data_type_tree = struct_trees
        schema, _, _, _ = generate_s2dm_schema(tree, data_type_tree)

        # Get the TestRoot type
        root_type_name = convert_name_for_graphql_schema("TestRoot", GraphQLElementType.TYPE, S2DM_CONVERSIONS)
        root_type = schema.type_map[root_type_name]

        # Get struct type names
        parent_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.ParentStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )
        nested_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.NestedStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )

        # Check fields
        assert isinstance(root_type, GraphQLObjectType)
        fields = root_type.fields

        # ParentStructSensor should reference ParentStruct
        assert "parentStructSensor" in fields
        parent_sensor_type = fields["parentStructSensor"].type
        assert parent_sensor_type == schema.type_map[parent_struct_name]

        # NestedStructSensor should reference NestedStruct
        assert "nestedStructSensor" in fields
        nested_sensor_type = fields["nestedStructSensor"].type
        assert nested_sensor_type == schema.type_map[nested_struct_name]

    def test_struct_metadata_and_comments(self, struct_trees):
        """Test that struct metadata and comments are preserved."""
        tree, data_type_tree = struct_trees
        schema, _, _, vspec_comments = generate_s2dm_schema(tree, data_type_tree)

        # Get struct type name
        nested_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.NestedStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )

        # Check description
        nested_struct_type = schema.type_map[nested_struct_name]
        assert isinstance(nested_struct_type, GraphQLObjectType)
        assert "struct" in nested_struct_type.description.lower()

        # Check that vspec metadata is stored
        assert nested_struct_name in vspec_comments["vss_types"]
        assert vspec_comments["vss_types"][nested_struct_name]["vspec_type"] == "STRUCT"

    def test_struct_property_range_constraints(self, struct_trees):
        """Test that range constraints on struct properties are preserved."""
        tree, data_type_tree = struct_trees
        schema, _, _, vspec_comments = generate_s2dm_schema(tree, data_type_tree)

        # Get struct type name
        nested_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.NestedStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )

        # Check that range metadata is captured
        # x has min: -10
        x_field_path = f"{nested_struct_name}.x"
        assert x_field_path in vspec_comments["field_ranges"]
        assert vspec_comments["field_ranges"][x_field_path]["min"] == -10

        # y has max: 10
        y_field_path = f"{nested_struct_name}.y"
        assert y_field_path in vspec_comments["field_ranges"]
        assert vspec_comments["field_ranges"][y_field_path]["max"] == 10

    def test_primitive_property_in_struct(self, struct_trees):
        """Test that primitive (non-struct) properties work correctly."""
        tree, data_type_tree = struct_trees
        schema, _, _, _ = generate_s2dm_schema(tree, data_type_tree)

        # Get ParentStruct type
        parent_struct_name = convert_name_for_graphql_schema(
            "VehicleDataTypes.TestBranch1.ParentStruct", GraphQLElementType.TYPE, S2DM_CONVERSIONS
        )
        parent_struct_type = schema.type_map[parent_struct_name]

        # Check z_property (primitive double)
        assert isinstance(parent_struct_type, GraphQLObjectType)
        fields = parent_struct_type.fields

        assert "zProperty" in fields
        z_property_type = fields["zProperty"].type
        assert isinstance(z_property_type, GraphQLNonNull)
        assert z_property_type.of_type == VSS_DATATYPE_MAP["double"]


class TestS2DMStructsModular:
    """Test class for modular output with struct support."""

    def test_modular_output_structs_in_separate_folder(self, tmp_path):
        """Test that struct types are placed in structs/ folder for modular output."""
        from vss_tools.exporters.s2dm.exporter import write_modular_schema

        # Load trees with structs
        tree, data_type_tree = get_trees(
            vspec=Path("tests/vspec/test_structs/test_s2dm_structs.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(),
            units=(),
            types=(Path("tests/vspec/test_structs/VehicleDataTypes.vspec"),),
            overlays=(),
            expand=False,
        )

        # Generate schema
        schema, unit_metadata, allowed_metadata, vspec_comments = generate_s2dm_schema(tree, data_type_tree)

        # Write modular output
        output_dir = tmp_path / "modular_output"
        write_modular_schema(schema, unit_metadata, allowed_metadata, vspec_comments, output_dir, flat_domains=True)

        # Check that structs directory exists
        structs_dir = output_dir / "structs"
        assert structs_dir.exists()
        assert structs_dir.is_dir()

        # Check that struct type files exist in structs/
        nested_struct_file = structs_dir / "VehicleDataTypes_TestBranch1_NestedStruct.graphql"
        parent_struct_file = structs_dir / "VehicleDataTypes_TestBranch1_ParentStruct.graphql"

        assert nested_struct_file.exists(), f"Expected {nested_struct_file} to exist"
        assert parent_struct_file.exists(), f"Expected {parent_struct_file} to exist"

        # Verify content
        nested_content = nested_struct_file.read_text()
        assert "type VehicleDataTypes_TestBranch1_NestedStruct" in nested_content
        assert "x: Float!" in nested_content
        assert "y: Float!" in nested_content
        assert "z: Float!" in nested_content

        parent_content = parent_struct_file.read_text()
        assert "type VehicleDataTypes_TestBranch1_ParentStruct" in parent_content
        assert "xProperty: VehicleDataTypes_TestBranch1_NestedStruct!" in parent_content

    def test_modular_output_regular_types_not_in_structs_folder(self, tmp_path):
        """Test that regular object types are NOT placed in structs/ folder."""
        from vss_tools.exporters.s2dm.exporter import write_modular_schema

        # Load trees with structs
        tree, data_type_tree = get_trees(
            vspec=Path("tests/vspec/test_structs/test_s2dm_structs.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(),
            units=(),
            types=(Path("tests/vspec/test_structs/VehicleDataTypes.vspec"),),
            overlays=(),
            expand=False,
        )

        # Generate schema
        schema, unit_metadata, allowed_metadata, vspec_comments = generate_s2dm_schema(tree, data_type_tree)

        # Write modular output
        output_dir = tmp_path / "modular_output"
        write_modular_schema(schema, unit_metadata, allowed_metadata, vspec_comments, output_dir, flat_domains=True)

        # Check that domain directory exists
        domain_dir = output_dir / "domain"
        assert domain_dir.exists()
        assert domain_dir.is_dir()

        # Check that regular type (TestRoot) is in domain/ not structs/
        test_root_file = domain_dir / "TestRoot.graphql"
        assert test_root_file.exists(), f"Expected {test_root_file} to exist in domain/"

        # Verify it's NOT in structs/
        structs_dir = output_dir / "structs"
        test_root_in_structs = structs_dir / "TestRoot.graphql"
        assert not test_root_in_structs.exists(), "TestRoot should not be in structs/ folder"


class TestS2DMStructsCLI:
    """Test class for CLI integration with struct support."""

    def test_cli_with_types_option(self, tmp_path):
        """Test that CLI works with --types option."""
        import subprocess

        output_file = tmp_path / "cli_test_output.graphql"

        result = subprocess.run(
            [
                "uv",
                "run",
                "vspec",
                "export",
                "s2dm",
                "--vspec",
                "tests/vspec/test_structs/test_s2dm_structs.vspec",
                "--types",
                "tests/vspec/test_structs/VehicleDataTypes.vspec",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output_file.exists(), "Output file was not created"

        # Verify struct types are in the output
        content = output_file.read_text()
        assert "type VehicleDataTypes_TestBranch1_NestedStruct" in content
        assert "type VehicleDataTypes_TestBranch1_ParentStruct" in content
        assert "x: Float!" in content  # Non-null field from struct

    def test_cli_modular_output_with_structs(self, tmp_path):
        """Test that CLI creates modular output with structs in separate folder."""
        import subprocess

        output_dir = tmp_path / "cli_modular_test"

        result = subprocess.run(
            [
                "uv",
                "run",
                "vspec",
                "export",
                "s2dm",
                "--vspec",
                "tests/vspec/test_structs/test_s2dm_structs.vspec",
                "--types",
                "tests/vspec/test_structs/VehicleDataTypes.vspec",
                "--output",
                str(output_dir),
                "--modular",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output_dir.exists(), "Output directory was not created"

        # Verify struct directory exists
        structs_dir = output_dir / "structs"
        assert structs_dir.exists(), "structs/ directory was not created"

        # Verify struct files exist
        nested_struct_file = structs_dir / "VehicleDataTypes_TestBranch1_NestedStruct.graphql"
        assert nested_struct_file.exists(), "NestedStruct file not found in structs/"

        # Verify content
        content = nested_struct_file.read_text()
        assert "type VehicleDataTypes_TestBranch1_NestedStruct" in content

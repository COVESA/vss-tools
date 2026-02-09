# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import pytest
from graphql import build_schema, print_schema
from vss_tools.exporters.s2dm import (
    S2DM_CONVERSIONS,
    generate_s2dm_schema,
    get_metadata_df,
    print_schema_with_vspec_directives,
)
from vss_tools.exporters.s2dm.graphql_utils import GraphQLElementType, convert_name_for_graphql_schema
from vss_tools.exporters.s2dm.type_builders import _sanitize_enum_value_for_graphql
from vss_tools.main import get_trees


class TestS2DMExporter:
    """Test class for S2DM GraphQL exporter."""

    def test_convert_for_graphql_type_names(self):
        """Test conversion to GraphQL type names using unified function."""
        assert (
            convert_name_for_graphql_schema("Vehicle.Cabin.Seat", GraphQLElementType.TYPE, S2DM_CONVERSIONS)
            == "Vehicle_Cabin_Seat"
        )
        assert convert_name_for_graphql_schema("simple", GraphQLElementType.TYPE, S2DM_CONVERSIONS) == "Simple"
        assert convert_name_for_graphql_schema("with-dash", GraphQLElementType.TYPE, S2DM_CONVERSIONS) == "WithDash"

    def test_convert_for_graphql_field_names(self):
        """Test conversion to GraphQL field names using unified function."""
        assert convert_name_for_graphql_schema("SomeName", GraphQLElementType.FIELD, S2DM_CONVERSIONS) == "someName"
        assert convert_name_for_graphql_schema("simple", GraphQLElementType.FIELD, S2DM_CONVERSIONS) == "simple"
        assert convert_name_for_graphql_schema("with.dots", GraphQLElementType.FIELD, S2DM_CONVERSIONS) == "withDots"

    def test_get_metadata_df_with_seat_example(self):
        """Test metadata extraction from seat example."""
        # Load the example seat vspec
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        branches_df, leaves_df = get_metadata_df(tree)

        # Check that we have expected branches
        assert "Vehicle" in branches_df.index
        assert "Vehicle.Cabin" in branches_df.index
        assert "Vehicle.Cabin.Seat" in branches_df.index

        # Check that we have expected leaves
        assert "Vehicle.Cabin.DriverPosition" in leaves_df.index
        assert "Vehicle.Cabin.Seat.HeatingCooling" in leaves_df.index

        # Check instance information
        seat_row = branches_df.loc["Vehicle.Cabin.Seat"]
        assert seat_row["instances"] is not None and seat_row["instances"] != ""

    def test_generate_s2dm_schema_basic_structure(self):
        """Test that basic schema generation works."""
        # Load the example seat vspec
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, _, _, _ = generate_s2dm_schema(tree)

        # Check that schema is valid
        assert schema is not None

        # Check that Query type exists
        query_type = schema.type_map["Query"]
        assert query_type is not None

        # Check that Vehicle type exists
        vehicle_type = schema.type_map["Vehicle"]
        assert vehicle_type is not None

        # Check that custom scalars exist
        assert "Int8" in schema.type_map
        assert "UInt8" in schema.type_map
        assert "UInt16" in schema.type_map

        # Check that custom directives exist
        directive_names = [d.name for d in schema.directives]
        assert "vspec" in directive_names
        assert "range" in directive_names
        assert "instanceTag" in directive_names

    def test_schema_can_be_printed(self):
        """Test that the schema can be serialized to GraphQL SDL."""
        # Load the example seat vspec
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, _, _, _ = generate_s2dm_schema(tree)
        schema_str = print_schema(schema)

        # Check that output contains expected elements
        assert "type Query" in schema_str
        assert "type Vehicle" in schema_str
        assert "scalar Int8" in schema_str
        assert "directive @vspec" in schema_str

        # Check that it can be parsed back
        parsed_schema = build_schema(schema_str)
        assert parsed_schema is not None

    def test_unit_enums_generation(self):
        """Test that unit enums are generated correctly."""
        # Load the example seat vspec
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, _, _, _ = generate_s2dm_schema(tree)
        schema_str = print_schema(schema)

        # Check that unit enums are generated
        assert "enum LengthUnitEnum" in schema_str
        assert "enum AngleUnitEnum" in schema_str
        assert "enum RelationUnitEnum" in schema_str

        # Check that enum values use uppercase unit names
        assert "MILLIMETER" in schema_str
        assert "DEGREE" in schema_str
        assert "PERCENT" in schema_str

        # Check that unit arguments are added to fields with proper defaults
        assert "unit: LengthUnitEnum = MILLIMETER" in schema_str
        assert "unit: AngleUnitEnum = DEGREE" in schema_str
        assert "unit: RelationUnitEnum = PERCENT" in schema_str

    def test_vspec_comment_directives(self):
        """Test that @vspec comment directives are generated correctly."""
        # Load the example seat vspec
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments = generate_s2dm_schema(tree)
        schema_str = print_schema_with_vspec_directives(
            schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments
        )

        # Check that VSS types are tracked (element + fqn only, no comments)
        assert len(vspec_comments["field_vss_types"]) > 0
        assert len(vspec_comments["vss_types"]) > 0

        # Check that @vspec directive uses simplified format (element + fqn only)
        # Comments should NOT be in the @vspec directive
        assert "@vspec(element:" in schema_str
        assert "fqn:" in schema_str

        # Check that comments are NOT included in @vspec directives
        assert 'comment: "Affects the property' not in schema_str

        # Verify specific VSS type tracking
        assert any("BRANCH" in str(v.get("element", "")) for v in vspec_comments["vss_types"].values())
        assert any(
            "ATTRIBUTE" in str(v.get("element", "")) or "SENSOR" in str(v.get("element", ""))
            for v in vspec_comments["field_vss_types"].values()
        )

    def test_range_and_deprecation_directives(self):
        """Test that @range and @deprecated directives are correctly generated for VSS constraints"""
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments = generate_s2dm_schema(tree)
        sdl = print_schema_with_vspec_directives(schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments)

        # Test @deprecated directive for massage field
        assert '@deprecated(reason: "v5.0 - refactored to Seat.MassageLevel")' in sdl

        # Test @range directives for fields with constraints
        assert "@range(min: -100, max: 100)" in sdl  # heatingCooling
        assert "@range(min: 0, max: 100)" in sdl  # massage, massageLevel, lumbarSupport, sideBolsterSupport

        # Test @range directives with only min constraint (e.g., height: min 0)
        assert "@range(min: 0)" in sdl

        # Ensure no empty @range directives are present
        assert "@range(min: , max: )" not in sdl
        assert "@range(min: , max:" not in sdl
        assert "@range(min:, max:" not in sdl

        # Check specific field combinations
        # massage field should have @vspec with element, @deprecated and @range
        import re

        massage_field_pattern = (
            r"massage\([^)]*\):[^@]*@vspec\(element: ACTUATOR[^)]*\)" r"[^@]*@deprecated[^@]*@range\(min: 0, max: 100\)"
        )
        assert re.search(massage_field_pattern, sdl) is not None

        # massageLevel should have @range but not @deprecated
        massageLevel_context = sdl[sdl.find("massageLevel") : sdl.find("massageLevel") + 200]
        assert "@range(min: 0, max: 100)" in massageLevel_context
        assert "@deprecated" not in massageLevel_context

    def test_instance_tag_support(self):
        """Test that @instanceTag directive and dimensional enums are correctly generated for VSS instances"""
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments = generate_s2dm_schema(tree)
        sdl = print_schema_with_vspec_directives(schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments)

        # Test that instance tag type is created
        assert "type Vehicle_Cabin_Seat_InstanceTag @instanceTag" in sdl

        # Test that dimensional enums are created with correct names and values
        assert "enum Vehicle_Cabin_Seat_InstanceTag_Dimension1" in sdl
        assert "enum Vehicle_Cabin_Seat_InstanceTag_Dimension2" in sdl

        # Test enum values match expected format from VSS instances
        assert "Row1" in sdl
        assert "Row2" in sdl
        assert "DriverSide" in sdl
        assert "PassengerSide" in sdl

        # Test that main type has instanceTag field
        assert "instanceTag: Vehicle_Cabin_Seat_InstanceTag" in sdl

        # Test that instance tag type has dimension fields
        assert "dimension1: Vehicle_Cabin_Seat_InstanceTag_Dimension1" in sdl
        assert "dimension2: Vehicle_Cabin_Seat_InstanceTag_Dimension2" in sdl

        # Test that main type does NOT have @instanceTag directive (only instance tag type has it)
        # Look specifically for the main type, not sub-types like Vehicle_Cabin_Seat_Airbag
        main_type_pattern = "type Vehicle_Cabin_Seat "
        main_type_lines = [
            line
            for line in sdl.split("\n")
            if main_type_pattern in line
            and "{" in line
            and "@instanceTag" not in line
            and "Vehicle_Cabin_Seat_" not in line.replace(main_type_pattern, "")
        ]
        assert len(main_type_lines) == 1
        assert "@instanceTag" not in main_type_lines[0]

        # Test that types with instances get ID field
        assert "id: ID!" in sdl

        # Verify the complete structure matches the reference pattern
        # The seat should be a list field (seats) with natural plural because it has instances
        assert "seats: [Vehicle_Cabin_Seat]" in sdl

    def test_allowed_value_enums_generation(self):
        """Test that allowed value enums are generated correctly."""
        # Use S2DM-specific test file with allowed values
        test_vspec_path = Path(__file__).parent / "vspec" / "test_s2dm" / "test_allowed_values.vspec"

        # Get tree from file
        tree, _ = get_trees(
            vspec=test_vspec_path,
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(),
            units=(),
            overlays=(),
        )

        # Generate schema
        schema, _, _, _ = generate_s2dm_schema(tree)
        schema_sdl = print_schema(schema)

        # Check that allowed value enums were generated
        # Check for the string field with allowed values ["PARK", "REVERSE", "NEUTRAL", "DRIVE"]
        assert "Vehicle_Transmission_GearMode_Enum" in schema_sdl
        assert "PARK" in schema_sdl
        assert "REVERSE" in schema_sdl
        assert "NEUTRAL" in schema_sdl
        assert "DRIVE" in schema_sdl

        # Check for numeric field with allowed values [1, 2, 3, 4, 5]
        assert "Vehicle_Performance_Level_Enum" in schema_sdl
        assert "_1" in schema_sdl  # Numeric values should have underscore prefix
        assert "_2" in schema_sdl
        assert "_5" in schema_sdl

        # Check for float field with allowed values [1.0, 2.5, 4.0, 5.0]
        assert "Vehicle_Performance_Rating_Enum" in schema_sdl
        assert "_1_0" in schema_sdl  # 1.0 becomes _1_0
        assert "_2_5" in schema_sdl  # 2.5 becomes _2_5
        assert "_4" in schema_sdl
        assert "_5" in schema_sdl

        # Check that fields use the enum types instead of base types
        assert "gearMode: Vehicle_Transmission_GearMode_Enum" in schema_sdl
        assert "level: Vehicle_Performance_Level_Enum" in schema_sdl
        assert "rating: Vehicle_Performance_Rating_Enum" in schema_sdl

        # Check enum descriptions
        assert "Allowed values for Vehicle.Transmission.GearMode" in schema_sdl

    def test_modular_export_flat_domains(self, tmp_path):
        """Test modular export with flat domain structure."""
        from vss_tools.exporters.s2dm import write_modular_schema

        # Load the example seat vspec
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        # Generate schema
        schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments = generate_s2dm_schema(tree)

        # Test modular export with flat domains (default)
        output_dir = tmp_path / "modular_flat"
        write_modular_schema(
            schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments, output_dir, flat_domains=True
        )

        # Check that common files were created in other/ directory
        assert (output_dir / "other" / "directives.graphql").exists()
        assert (output_dir / "other" / "scalars.graphql").exists()
        assert (output_dir / "other" / "queries.graphql").exists()

        # Check that domain files were created in domain/ directory (flat structure)
        assert (output_dir / "domain" / "Vehicle.graphql").exists()
        assert (output_dir / "domain" / "Vehicle_Cabin.graphql").exists()
        assert (output_dir / "domain" / "Vehicle_Cabin_Seat.graphql").exists()

        # Check that unit enum files were created in other/ directory
        assert (output_dir / "other" / "units.graphql").exists()

        # Check that instance files were created in instances/ directory
        assert (output_dir / "instances" / "Vehicle_Cabin_Seat_InstanceTag.graphql").exists()

        # Verify content of a domain file
        vehicle_content = (output_dir / "domain" / "Vehicle.graphql").read_text()
        assert "type Vehicle" in vehicle_content
        assert "Domain-specific GraphQL types" in vehicle_content

    def test_modular_export_nested_domains(self, tmp_path):
        """Test modular export with nested domain structure."""
        from vss_tools.exporters.s2dm import write_modular_schema

        # Load the example seat vspec
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        # Generate schema
        schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments = generate_s2dm_schema(tree)

        # Test modular export with nested domains
        output_dir = tmp_path / "modular_nested"
        write_modular_schema(
            schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments, output_dir, flat_domains=False
        )

        # Check that common files were created in other/ directory
        assert (output_dir / "other" / "directives.graphql").exists()
        assert (output_dir / "other" / "queries.graphql").exists()

        # Check that nested structure was created with _ prefix for root types
        assert (output_dir / "domain" / "Vehicle" / "_Vehicle.graphql").exists()
        assert (output_dir / "domain" / "Vehicle" / "Cabin" / "_Cabin.graphql").exists()
        assert (output_dir / "domain" / "Vehicle" / "Cabin" / "Seat" / "_Seat.graphql").exists()

        # Check that leaf types don't have _ prefix
        assert (output_dir / "domain" / "Vehicle" / "VehicleIdentification.graphql").exists()
        assert (output_dir / "domain" / "Vehicle" / "Cabin" / "Seat" / "Airbag.graphql").exists()

        # Check that enum directory structure was created in other/ directory
        assert (output_dir / "other" / "units.graphql").exists()

        # Check that instance files were created in instances/ directory
        assert (output_dir / "instances" / "Vehicle_Cabin_Seat_InstanceTag.graphql").exists()

        # Verify nested directory content
        seat_content = (output_dir / "domain" / "Vehicle" / "Cabin" / "Seat" / "_Seat.graphql").read_text()
        assert "Vehicle_Cabin_Seat" in seat_content

    def test_modular_export_instance_enum_directives(self, tmp_path):
        """Test that instance dimension enums get @vspec directives in modular export."""
        from vss_tools.exporters.s2dm import write_modular_schema

        # Load test vspec with instances that need sanitization
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/test_instance_sanitization.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        # Generate schema
        schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments = generate_s2dm_schema(tree)

        # Test modular export with flat domains
        output_dir = tmp_path / "modular_instance_test"
        write_modular_schema(
            schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments, output_dir, flat_domains=True
        )

        # Check that instance files were created
        instance_file = output_dir / "instances" / "Vehicle_Cabin_Seat_InstanceTag.graphql"
        assert instance_file.exists()

        # Verify that instance dimension enums have @vspec directives with originalName
        instance_content = instance_file.read_text()

        # Check for sanitized enum values with @vspec directives
        assert 'DRIVER_SIDE @vspec(metadata: [{key: "originalName", value: "DriverSide"}])' in instance_content
        assert 'PASSENGER_SIDE @vspec(metadata: [{key: "originalName", value: "PassengerSide"}])' in instance_content

    def test_non_instantiated_property_hoisting(self, tmp_path: Path):
        """Test that properties with instantiate=false are hoisted to parent type."""
        # Load the test vspec with non-instantiated properties
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_non_instantiated_props/test.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(),
            units=(),
            types=(),
            overlays=(),
            expand=False,  # S2DM exporter uses non-expanded mode
        )

        # Generate schema
        schema, unit_metadata, allowed_metadata, vspec_comments = generate_s2dm_schema(tree)
        schema_str = print_schema_with_vspec_directives(schema, unit_metadata, allowed_metadata, vspec_comments)

        # Verify that Vehicle_Cabin_Door type doesn't have someSignal
        assert "type Vehicle_Cabin_Door @vspec" in schema_str
        door_type_start = schema_str.find("type Vehicle_Cabin_Door @vspec")
        door_type_end = schema_str.find("\n}", door_type_start) + 2  # Include closing brace
        door_type_content = schema_str[door_type_start:door_type_end]

        # someSignal should NOT be on Door type
        assert "someSignal" not in door_type_content
        # But isOpen and isLocked should be
        assert "isOpen" in door_type_content
        assert "isLocked" in door_type_content

        # Verify that Vehicle_Cabin type has doorSomeSignal (hoisted)
        assert "type Vehicle_Cabin @vspec" in schema_str
        cabin_type_start = schema_str.find("type Vehicle_Cabin @vspec")
        cabin_type_end = schema_str.find("\n}", cabin_type_start) + 2  # Include closing brace
        cabin_type_content = schema_str[cabin_type_start:cabin_type_end]

        # someSignal should be on Cabin type (hoisted without branch prefix)
        assert "someSignal" in cabin_type_content
        # Verify it has the instantiate=false metadata
        assert 'metadata: [{key: "instantiate", value: "false"}]' in cabin_type_content
        # And doors array field should also be there (natural plural)
        assert "doors" in cabin_type_content

    def test_enum_value_sanitization_with_spaces(self):
        """Test that enum values with spaces are sanitized correctly."""
        # Test the sanitization function
        assert _sanitize_enum_value_for_graphql("some value") == ("SOME_VALUE", True)
        assert _sanitize_enum_value_for_graphql("SOME VALUE") == ("SOME_VALUE", True)
        assert _sanitize_enum_value_for_graphql("another-value") == ("ANOTHER_VALUE", True)
        assert _sanitize_enum_value_for_graphql("YET_ANOTHER") == ("YET_ANOTHER", False)
        assert _sanitize_enum_value_for_graphql("front left") == ("FRONT_LEFT", True)
        assert _sanitize_enum_value_for_graphql("1value") == ("_1VALUE", True)

    def test_enum_sanitization_in_schema_generation(self):
        """Test that enum values with spaces generate proper schema with metadata."""
        # Load the test vspec with spaces in enum values
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/test_enum_sanitization.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, _, allowed_metadata, _ = generate_s2dm_schema(tree)

        # Check that schema is valid
        assert schema is not None

        # Check that enum type for LightMode exists
        light_mode_enum_name = "Vehicle_Cabin_LightMode_Enum"
        assert light_mode_enum_name in schema.type_map

        # Check metadata includes modified values
        assert light_mode_enum_name in allowed_metadata
        metadata = allowed_metadata[light_mode_enum_name]
        assert "modified_values" in metadata

        # Verify specific modifications
        modified = metadata["modified_values"]
        assert "SOME_VALUE" in modified
        assert modified["SOME_VALUE"] in ["some value", "SOME VALUE"]  # One of them
        assert "ANOTHER_VALUE" in modified
        assert modified["ANOTHER_VALUE"] == "another-value"

        # YET_ANOTHER should not be in modified (no modification needed)
        assert "YET_ANOTHER" not in modified

    def test_enum_sanitization_schema_output_with_directives(self):
        """Test that the schema output includes proper @vspec directives for modified enum values."""
        # Load the test vspec with spaces in enum values
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/test_enum_sanitization.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, unit_metadata, allowed_metadata, vspec_comments = generate_s2dm_schema(tree)
        schema_str = print_schema_with_vspec_directives(schema, unit_metadata, allowed_metadata, vspec_comments)

        # Check that enum type has @vspec directive with element
        assert "enum Vehicle_Cabin_LightMode_Enum @vspec" in schema_str

        # Check that modified enum values have @vspec directives with originalName metadata
        # "some value" -> SOME_VALUE
        assert (
            'SOME_VALUE @vspec(metadata: [{key: "originalName", value: "some value"}])' in schema_str
            or 'SOME_VALUE @vspec(metadata: [{key: "originalName", value: "SOME VALUE"}])' in schema_str
        )

        # "another-value" -> ANOTHER_VALUE
        assert 'ANOTHER_VALUE @vspec(metadata: [{key: "originalName", value: "another-value"}])' in schema_str

        # YET_ANOTHER should not have originalName metadata (wasn't modified)
        assert 'YET_ANOTHER @vspec(metadata: [{key: "originalName"' not in schema_str

        # Check SeatPosition enum
        assert "enum Vehicle_Cabin_SeatPosition_Enum @vspec" in schema_str
        assert 'FRONT_LEFT @vspec(metadata: [{key: "originalName", value: "front left"}])' in schema_str
        assert 'FRONT_RIGHT @vspec(metadata: [{key: "originalName", value: "front right"}])' in schema_str

    def test_enum_camelcase_sanitization(self):
        """Test that camelCase enum values are properly converted using caseconverter."""
        from vss_tools.exporters.s2dm.type_builders import _sanitize_enum_value_for_graphql

        # Test camelCase word boundary detection
        test_cases = [
            ("PbCa", "PB_CA", True),  # Mixed case acronyms
            ("HTTPSConnection", "HTTPS_CONNECTION", True),  # Acronym + word
            ("someAPIKey", "SOME_API_KEY", True),  # word + acronym + word
            ("XMLParser", "XML_PARSER", True),  # Acronym + word
            ("myValue", "MY_VALUE", True),  # Simple camelCase
            ("IOError", "IO_ERROR", True),  # Two-letter acronym
            ("AGM", "AGM", False),  # Already uppercase, no change
            ("EFB", "EFB", False),  # Already uppercase, no change
            ("already_snake", "ALREADY_SNAKE", True),  # snake_case to SCREAMING_SNAKE_CASE
            ("ALREADY_SCREAMING", "ALREADY_SCREAMING", False),  # No change needed
            ("mixed-Case", "MIXED_CASE", True),  # Mixed with hyphen
            ("some value", "SOME_VALUE", True),  # Spaces
            ("value.with.dots", "VALUE_WITH_DOTS", True),  # Dots
            ("123value", "_123VALUE", True),  # Starts with number
        ]

        error_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
        ]

        for input_val, expected_output, expected_modified in test_cases:
            result, was_modified = _sanitize_enum_value_for_graphql(input_val)
            assert result == expected_output, f"Failed for '{input_val}': expected '{expected_output}', got '{result}'"
            assert was_modified == expected_modified, f"Failed modification flag for '{input_val}'"

        for input_val in error_cases:
            with pytest.raises(ValueError):
                _sanitize_enum_value_for_graphql(input_val)

    def test_camelcase_enums_schema_generation(self):
        """Test that camelCase enum values in vspec generate proper schema with directives."""
        # Load the test vspec with camelCase enum values
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/test_camelcase_enums.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, unit_metadata, allowed_metadata, vspec_comments = generate_s2dm_schema(tree)
        schema_str = print_schema_with_vspec_directives(schema, unit_metadata, allowed_metadata, vspec_comments)

        # Check Component.Type enum with AbCd
        assert "enum Vehicle_Component_Type_Enum @vspec" in schema_str

        # AbCd should be converted to AB_CD with originalName annotation
        assert 'AB_CD @vspec(metadata: [{key: "originalName", value: "AbCd"}])' in schema_str

        # AAA, BBB, CCC, DDD should not have originalName (no change needed)
        assert 'AAA @vspec(metadata: [{key: "originalName"' not in schema_str
        assert 'BBB @vspec(metadata: [{key: "originalName"' not in schema_str

        # Check Connection.Protocol enum
        assert "enum Vehicle_Connection_Protocol_Enum @vspec" in schema_str
        assert 'HTTPS_PROTOCOL @vspec(metadata: [{key: "originalName", value: "HTTPSProtocol"}])' in schema_str
        assert 'TCP_PROTOCOL @vspec(metadata: [{key: "originalName", value: "TCPProtocol"}])' in schema_str
        assert 'UDP_PROTOCOL @vspec(metadata: [{key: "originalName", value: "UDPProtocol"}])' in schema_str

        # Check Status.Code enum
        assert "enum Vehicle_Status_Code_Enum @vspec" in schema_str
        assert 'IO_ERROR @vspec(metadata: [{key: "originalName", value: "IOError"}])' in schema_str
        assert 'XML_PARSER @vspec(metadata: [{key: "originalName", value: "XMLParser"}])' in schema_str
        assert 'SOME_API_KEY @vspec(metadata: [{key: "originalName", value: "someAPIKey"}])' in schema_str

    def test_instance_dimension_enum_sanitization(self):
        """Test that instance dimension enum values are properly sanitized and annotated."""
        # Load the test vspec with instances that need sanitization
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/test_instance_sanitization.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, unit_metadata, allowed_metadata, vspec_comments = generate_s2dm_schema(tree)
        schema_str = print_schema_with_vspec_directives(schema, unit_metadata, allowed_metadata, vspec_comments)

        # Check that Row instance enum is created and values are sanitized
        assert "enum Vehicle_Cabin_InstanceTag_Dimension1" in schema_str
        assert 'ROW1 @vspec(metadata: [{key: "originalName", value: "Row1"}])' in schema_str
        assert 'ROW2 @vspec(metadata: [{key: "originalName", value: "Row2"}])' in schema_str

        # Check that DriverSide/PassengerSide instance enum is created and values are sanitized
        assert "enum Vehicle_Cabin_Seat_InstanceTag_Dimension1" in schema_str
        assert 'DRIVER_SIDE @vspec(metadata: [{key: "originalName", value: "DriverSide"}])' in schema_str
        assert 'PASSENGER_SIDE @vspec(metadata: [{key: "originalName", value: "PassengerSide"}])' in schema_str

        # Check that FrontLeft/FrontRight/RearLeft/RearRight instance enum is created and values are sanitized
        assert "enum Vehicle_Cabin_Seat_Position_InstanceTag_Dimension1" in schema_str
        assert 'FRONT_LEFT @vspec(metadata: [{key: "originalName", value: "FrontLeft"}])' in schema_str
        assert 'FRONT_RIGHT @vspec(metadata: [{key: "originalName", value: "FrontRight"}])' in schema_str
        assert 'REAR_LEFT @vspec(metadata: [{key: "originalName", value: "RearLeft"}])' in schema_str
        assert 'REAR_RIGHT @vspec(metadata: [{key: "originalName", value: "RearRight"}])' in schema_str

    def test_extended_attributes_in_metadata(self):
        """Test that extended attributes are captured and added to @vspec metadata."""
        # Load the test vspec with extended attributes
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_s2dm/test_extended_attributes.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=("source", "quality", "calibration", "customMetadata", "anotherAttribute"),
            quantities=(Path("tests/vspec/test_s2dm/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_s2dm/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, unit_metadata, allowed_metadata, vspec_comments = generate_s2dm_schema(
            tree, extended_attributes=("source", "quality", "calibration", "customMetadata", "anotherAttribute")
        )
        schema_str = print_schema_with_vspec_directives(schema, unit_metadata, allowed_metadata, vspec_comments)

        # Check Vehicle.Speed has source and quality in metadata
        assert "speed(unit: RelationUnitEnum = PERCENT): Float" in schema_str
        assert '@vspec(element: SENSOR, fqn: "Vehicle.Speed"' in schema_str
        assert '{key: "source", value: "ecu0xAA"}' in schema_str
        assert '{key: "quality", value: "100"}' in schema_str

        # Check Vehicle.Temperature has source, quality, and calibration
        assert "temperature(unit: AngleUnitEnum = DEGREE): Int16" in schema_str
        assert '@vspec(element: SENSOR, fqn: "Vehicle.Temperature"' in schema_str
        assert '{key: "source", value: "ecu0xBB"}' in schema_str
        assert '{key: "quality", value: "95"}' in schema_str
        assert '{key: "calibration", value: "factory"}' in schema_str

        # Check Vehicle.Info.Model has customMetadata and anotherAttribute
        assert "model: String" in schema_str
        assert '@vspec(element: ATTRIBUTE, fqn: "Vehicle.Info.Model"' in schema_str
        assert '{key: "customMetadata", value: "test_value"}' in schema_str
        assert '{key: "anotherAttribute", value: "42"}' in schema_str

# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from graphql import build_schema, print_schema
from vss_tools.exporters.s2dm import (
    generate_s2dm_schema,
    get_metadata_df,
    print_schema_with_vspec_directives,
)
from vss_tools.exporters.s2dm.exporter import S2DM_CONVERSIONS
from vss_tools.main import get_trees
from vss_tools.utils.graphql_utils import GraphQLElementType, convert_name_for_graphql_schema


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

        # Check that field comments are captured
        assert len(vspec_comments["field_comments"]) > 0

        # Check that type comments are captured
        assert len(vspec_comments["type_comments"]) > 0

        # Check that @vspec comment directives appear in the output with new consolidated format
        assert 'comment: "Affects the property (SingleSeat.Position)."' in schema_str

        # Check for specific field comment directive
        assert "Affects the property (SingleSeat.Position)" in schema_str

        # Check for type comment directive
        assert "Seating is here considered as the part of the seat that supports the thighs" in schema_str

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
        # massage field should have @vspec with VSS type, @deprecated and @range
        import re

        massage_field_pattern = (
            r"massage\([^)]*\):[^@]*@vspec\([^)]*vspecType: ACTUATOR[^)]*\)"
            r"[^@]*@deprecated[^@]*@range\(min: 0, max: 100\)"
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
        # The seat should be a list field (seat_s) because it has instances
        assert "seat_s: [Vehicle_Cabin_Seat]" in sdl

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
        assert "_1" in schema_sdl  # 1.0 becomes _1
        assert "_2_DOT_5" in schema_sdl  # 2.5 should use _DOT_
        assert "_4" in schema_sdl
        assert "_5" in schema_sdl

        # Check that fields use the enum types instead of base types
        assert "gearMode: Vehicle_Transmission_GearMode_Enum" in schema_sdl
        assert "level: Vehicle_Performance_Level_Enum" in schema_sdl
        assert "rating: Vehicle_Performance_Rating_Enum" in schema_sdl

        # Check enum descriptions
        assert "Allowed values for Vehicle.Transmission.GearMode" in schema_sdl

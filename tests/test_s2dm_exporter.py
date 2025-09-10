"""
Tests for the S2DM GraphQL exporter.
"""

from pathlib import Path

from graphql import build_schema, print_schema

from vss_tools.exporters.s2dm import (
    convert_to_graphql_field_name,
    convert_to_graphql_type_name,
    generate_s2dm_schema,
    get_metadata_df,
    print_schema_with_vspec_directives,
)
from vss_tools.main import get_trees


class TestS2DMExporter:
    """Test class for S2DM GraphQL exporter."""

    def test_convert_name_to_pascal_case(self):
        """Test conversion to PascalCase using our GraphQL type name converter."""
        # Updated expected values to match our new GraphQL type naming strategy
        assert convert_to_graphql_type_name("Vehicle.Cabin.Seat") == "Vehicle_Cabin_Seat"
        assert convert_to_graphql_type_name("angular-speed") == "AngularSpeed"  
        assert convert_to_graphql_type_name("mass-per-distance") == "MassPerDistance"
        assert convert_to_graphql_type_name("simple") == "Simple"
        assert convert_to_graphql_type_name("with-dash") == "WithDash"

    def test_convert_name_to_camel_case(self):
        """Test conversion to camelCase using our GraphQL field name converter."""
        # Updated expected values to match our new GraphQL field naming strategy
        assert convert_to_graphql_field_name("SomeName") == "someName"
        assert convert_to_graphql_field_name("simple") == "simple"
        assert convert_to_graphql_field_name("with.dots") == "withdots"

    def test_get_metadata_df_with_seat_example(self):
        """Test metadata extraction from seat example."""
        # Load the example seat vspec
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_graphql_exporter/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_graphql_exporter/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_graphql_exporter/test_units.yaml"),),
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
            vspec=Path("tests/vspec/test_graphql_exporter/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_graphql_exporter/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_graphql_exporter/test_units.yaml"),),
            overlays=(),
            expand=False,
        )
        
        schema, _, _ = generate_s2dm_schema(tree)
        
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
            vspec=Path("tests/vspec/test_graphql_exporter/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_graphql_exporter/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_graphql_exporter/test_units.yaml"),),
            overlays=(),
            expand=False,
        )
        
        schema, _, _ = generate_s2dm_schema(tree)
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
            vspec=Path("tests/vspec/test_graphql_exporter/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_graphql_exporter/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_graphql_exporter/test_units.yaml"),),
            overlays=(),
            expand=False,
        )
        
        schema, _, _ = generate_s2dm_schema(tree)
        schema_str = print_schema(schema)
        
        # Check that unit enums are generated (updated for case-converter naming)
        assert "enum LengthUnitEnum" in schema_str
        assert "enum AngleUnitEnum" in schema_str
        assert "enum RelationUnitEnum" in schema_str
        
        # Check that enum values use uppercase unit names
        assert "MILLIMETER" in schema_str
        assert "DEGREE" in schema_str
        assert "PERCENT" in schema_str
        
        # Check that unit arguments are added to fields with proper defaults (updated for case-converter naming)
        assert "unit: LengthUnitEnum = MILLIMETER" in schema_str
        
        # Check that metadata has proper structure for each quantity
        assert 'Set of units for the quantity kind "length"' in schema_str
        assert 'Set of units for the quantity kind "angle"' in schema_str
        assert 'Set of units for the quantity kind "relation"' in schema_str

    def test_vspec_comment_directives(self):
        """Test that @vspec comment directives are generated correctly."""
        # Load the example seat vspec
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_graphql_exporter/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_graphql_exporter/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_graphql_exporter/test_units.yaml"),),
            overlays=(),
            expand=False,
        )
        
        schema, unit_enums_metadata, vspec_comments = generate_s2dm_schema(tree)
        schema_str = print_schema_with_vspec_directives(schema, unit_enums_metadata, vspec_comments)
        
        # Check that field comments are captured
        assert len(vspec_comments['field_comments']) > 0
        
        # Check that type comments are captured
        assert len(vspec_comments['type_comments']) > 0
        
        # Check that @vspec comment directives appear in the output
        assert '@vspec(comment:' in schema_str
        
        # Check for specific field comment directive
        assert 'Affects the property (SingleSeat.Position)' in schema_str
        
        # Check for type comment directive
        assert 'Seating is here considered as the part of the seat that supports the thighs' in schema_str

    def test_range_and_deprecation_directives(self):
        """Test that @range and @deprecated directives are correctly generated for VSS constraints"""
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_graphql_exporter/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_graphql_exporter/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_graphql_exporter/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, unit_enums_metadata, vspec_comments = generate_s2dm_schema(tree)
        sdl = print_schema_with_vspec_directives(schema, unit_enums_metadata, vspec_comments)
        
        # Test @deprecated directive for massage field
        assert '@deprecated(reason: "v5.0 - refactored to Seat.MassageLevel")' in sdl
        
        # Test @range directives for fields with constraints
        assert '@range(min: -100, max: 100)' in sdl  # heatingCooling
        assert '@range(min: 0, max: 100)' in sdl     # massage, massageLevel, lumbarSupport, sideBolsterSupport
        
        # Test @range directives with only min constraint (e.g., height: min 0)
        assert '@range(min: 0)' in sdl
        
        # Ensure no empty @range directives are present
        assert '@range(min: , max: )' not in sdl
        assert '@range(min: , max:' not in sdl
        assert '@range(min:, max:' not in sdl
        
        # Check specific field combinations
        # massage field should have both @deprecated and @range
        import re
        massage_field_pattern = r'massage\([^)]*\):[^@]*@deprecated[^@]*@range\(min: 0, max: 100\)'
        assert re.search(massage_field_pattern, sdl) is not None
        
        # massageLevel should have @range but not @deprecated  
        massageLevel_context = sdl[sdl.find('massageLevel'):sdl.find('massageLevel') + 200]
        assert '@range(min: 0, max: 100)' in massageLevel_context
        assert '@deprecated' not in massageLevel_context

    def test_instance_tag_support(self):
        """Test that @instanceTag directive and dimensional enums are correctly generated for VSS instances"""
        tree, _ = get_trees(
            vspec=Path("tests/vspec/test_graphql_exporter/example_seat.vspec"),
            include_dirs=(),
            aborts=(),
            strict=False,
            extended_attributes=(),
            quantities=(Path("tests/vspec/test_graphql_exporter/test_quantities.yaml"),),
            units=(Path("tests/vspec/test_graphql_exporter/test_units.yaml"),),
            overlays=(),
            expand=False,
        )

        schema, unit_enums_metadata, vspec_comments = generate_s2dm_schema(tree)
        sdl = print_schema_with_vspec_directives(schema, unit_enums_metadata, vspec_comments)
        
        # Test that instance tag type is created (updated for new naming approach)
        assert 'type Vehicle_Cabin_Seat_InstanceTag @instanceTag' in sdl
        
        # Test that dimensional enums are created with correct names and values (updated for new naming approach)
        assert 'enum Vehicle_Cabin_Seat_InstanceTag_Dimension1' in sdl
        assert 'enum Vehicle_Cabin_Seat_InstanceTag_Dimension2' in sdl
        
        # Test enum values match expected format from VSS instances
        assert 'Row1' in sdl
        assert 'Row2' in sdl
        assert 'DriverSide' in sdl
        assert 'PassengerSide' in sdl
        
        # Test that main type has instanceTag field (updated for new naming approach)
        assert 'instanceTag: Vehicle_Cabin_Seat_InstanceTag' in sdl
        
        # Test that instance tag type has dimension fields
        assert 'dimension1: Vehicle_Cabin_Seat_InstanceTag_Dimension1' in sdl
        assert 'dimension2: Vehicle_Cabin_Seat_InstanceTag_Dimension2' in sdl
        
        # Test that main type does NOT have @instanceTag directive (only instance tag type has it)
        # Check that the main type line doesn't contain @instanceTag (updated for new naming approach)
        main_type_lines = [line for line in sdl.split('\n') if 'type Vehicle_Cabin_Seat {' in line]
        assert len(main_type_lines) == 1
        assert '@instanceTag' not in main_type_lines[0]
        
        # Test that types with instances get ID field
        assert 'id: ID!' in sdl
        
        # Verify the complete structure matches the reference pattern
        # The seat should be a list field (seat_s) because it has instances
        assert 'seat_s: [Vehicle_Cabin_Seat]' in sdl

    def test_allowed_value_enums_generation(self):
        """Test that allowed value enums are generated correctly."""
        # Use test file with allowed values
        test_vspec_path = Path(__file__).parent / "vspec" / "test_allowed" / "test.vspec"
        
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
        schema, _, _ = generate_s2dm_schema(tree)
        schema_sdl = print_schema(schema)
        
        # Check that allowed value enums were generated (test.vspec has multiple fields with allowed values)
        # Check for the string field with allowed values ["January", "February"] (updated for new naming approach)
        assert "A_String_Enum" in schema_sdl
        assert "JANUARY" in schema_sdl  # String values converted to SCREAMING_CASE
        assert "FEBRUARY" in schema_sdl
        
        # Check for numeric field with allowed values [1, 2, 3] (updated for new naming approach)
        assert "A_Int_Enum" in schema_sdl
        assert "_1" in schema_sdl  # Numeric values should have underscore prefix
        assert "_2" in schema_sdl
        assert "_3" in schema_sdl
        
        # Check for float field with allowed values [1.1, 2.54, 3] (updated for new naming approach)
        assert "A_Float_Enum" in schema_sdl
        assert "_11" in schema_sdl   # Float values are also converted to valid enum names
        assert "_254" in schema_sdl
        assert "_3" in schema_sdl
        
        # Check that fields use the enum types instead of base types (updated for new naming approach)
        assert "string: A_String_Enum" in schema_sdl
        assert "int: A_Int_Enum" in schema_sdl
        assert "float: A_Float_Enum" in schema_sdl
        
        # Check enum descriptions
        assert "Allowed values for A.String" in schema_sdl

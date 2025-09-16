from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict

import pandas as pd
import rich_click as click
from caseconverter import DELIMITERS, pascalcase
from graphql import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLID,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.datatypes import dynamic_units
from vss_tools.main import get_trees
from vss_tools.tree import VSSNode
from vss_tools.utils.graphql_directive_processor import GraphQLDirectiveProcessor
from vss_tools.utils.graphql_scalars import VSS_DATATYPE_MAP, get_vss_scalar_types
from vss_tools.utils.graphql_utils import (
    DEFAULT_CONVERSIONS,
    GraphQLElementType,
    convert_name_for_graphql_schema,
    load_predefined_schema_elements,
)
from vss_tools.utils.pandas_utils import get_metadata_df
from vss_tools.utils.string_conversion_utils import handle_fqn_conversion

# S2DM-specific conversions that override defaults for FQN handling
# For type-like elements, we use standard delimiters (without dots) so FQNs are handled correctly
# For other elements, we inherit the DEFAULT behavior (includes dot delimiter support)


def get_s2dm_conversions() -> Dict[GraphQLElementType, Callable[[str], str]]:
    """Get S2DM conversions with proper enum instances."""
    s2dm_conversions = DEFAULT_CONVERSIONS.copy()
    s2dm_conversions.update(
        {
            # Override type-like elements to handle FQNs (Vehicle.Body -> Vehicle_Body)
            # Use standard delimiters (space, dash, underscore) but NOT dots for FQN names
            GraphQLElementType.TYPE: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.INTERFACE: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.UNION: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.INPUT: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
            GraphQLElementType.ENUM: lambda name: handle_fqn_conversion(name, pascalcase, DELIMITERS),
        }
    )
    return s2dm_conversions


# Create the conversions dictionary
S2DM_CONVERSIONS = get_s2dm_conversions()


class S2DMExporterException(Exception):
    """Exception raised for errors in the S2DM export process."""

    pass


# Load predefined schema elements from directory
BASE_SCHEMA, CUSTOM_DIRECTIVES = load_predefined_schema_elements(Path(__file__).parent / "predefined_elements")

# Custom directives loaded from SDL
VSpecDirective = CUSTOM_DIRECTIVES["vspec"]
RangeDirective = CUSTOM_DIRECTIVES["range"]
InstanceTagDirective = CUSTOM_DIRECTIVES["instanceTag"]

# Initialize directive processor
directive_processor = GraphQLDirectiveProcessor()


@click.command()
@clo.vspec_opt
@clo.output_required_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path, ...],
    extended_attributes: tuple[str, ...],
    strict: bool,
    aborts: tuple[str, ...],
    overlays: tuple[Path, ...],
    quantities: tuple[Path, ...],
    units: tuple[Path, ...],
):
    """Export a VSS specification to S2DM GraphQL schema."""
    try:
        tree, _ = get_trees(
            vspec=vspec,
            include_dirs=include_dirs,
            aborts=aborts,
            strict=strict,
            extended_attributes=extended_attributes,
            quantities=quantities,
            units=units,
            overlays=overlays,
            expand=False,
        )

        log.info("Generating S2DM GraphQL schema...")

        # Generate the schema
        schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments = generate_s2dm_schema(tree)

        # Write to output file with custom @vspec directives
        with open(output, "w") as outfile:
            outfile.write(
                print_schema_with_vspec_directives(schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments)
            )

        log.info(f"S2DM GraphQL schema written to {output}")

    except S2DMExporterException as e:
        log.error(e)
        sys.exit(1)


def generate_s2dm_schema(
    tree: VSSNode,
) -> tuple[
    GraphQLSchema,
    dict[str, dict[str, dict[str, str]]],
    dict[str, dict[str, dict[str, str]]],
    dict[str, dict[str, Any]],
]:
    """
    Generate a GraphQL schema from a VSS tree.

    Args:
        tree: The root VSSNode of the VSS tree

    Returns:
        tuple: (GraphQLSchema, unit_enums_metadata, allowed_enums_metadata, vspec_comments)
               The generated GraphQL schema, unit enum metadata, allowed enums metadata, and vspec comments
    """
    # Use the structured schema builder
    schema_builder = S2DMSchemaBuilder(tree)
    return schema_builder.build_schema()


class S2DMSchemaBuilder:
    """Builds GraphQL schema in structured phases for S2DM exporter."""

    def __init__(self, tree: VSSNode):
        """Initialize the schema builder with VSS tree."""
        self.tree = tree
        self.branches_df, self.leaves_df = get_metadata_df(tree)
        self.types_registry: dict[str, Any] = {}
        self.vspec_comments = self._init_vspec_comments()

    def _init_vspec_comments(self) -> dict[str, dict[str, Any]]:
        """Initialize the vspec comments dictionary structure."""
        return {
            "field_comments": {},  # field_path -> comment
            "type_comments": {},  # type_name -> comment
            "field_ranges": {},  # field_path -> {'min': value, 'max': value}
            "field_deprecated": {},  # field_path -> reason
            "instance_tags": {},  # type_name -> True (for types with instances)
            "instance_tag_types": {},  # type_name -> instance_tag_type_name
            "vss_types": {},  # type_name -> {'fqn': fqn, 'vspec_type': type}
            "field_vss_types": {},  # field_path -> {'fqn': fqn, 'vspec_type': type}
        }

    def build_schema(
        self,
    ) -> tuple[
        GraphQLSchema,
        dict[str, dict[str, dict[str, str]]],
        dict[str, dict[str, dict[str, str]]],
        dict[str, dict[str, Any]],
    ]:
        """Build schema in phases."""
        # Phase 1: Prepare base data
        unit_enums, unit_enums_metadata = self._create_unit_data()

        # Phase 2: Generate supporting types
        self._generate_instance_types()
        allowed_enums_metadata = self._generate_allowed_value_enums()

        # Phase 3: Generate main object types
        self._generate_object_types(unit_enums)

        # Phase 4: Assemble final schema
        schema = self._assemble_schema(unit_enums)

        return schema, unit_enums_metadata, allowed_enums_metadata, self.vspec_comments

    def _create_unit_data(self) -> tuple[dict[str, GraphQLEnumType], dict[str, dict[str, dict[str, str]]]]:
        """Phase 1: Create unit enums and metadata."""
        unit_enums = create_unit_enums()
        unit_enums_metadata = get_quantity_kinds_and_units()
        return unit_enums, unit_enums_metadata

    def _generate_instance_types(self) -> None:
        """Phase 2a: Generate instance types and enums."""
        instance_types = generate_instance_types_and_enums(self.branches_df, self.vspec_comments)
        self.types_registry.update(instance_types)

    def _generate_allowed_value_enums(self) -> dict[str, dict[str, dict[str, str]]]:
        """Phase 2b: Generate allowed value enums."""
        allowed_enums, allowed_enums_metadata = generate_allowed_value_enums(self.leaves_df)

        # Only add actual GraphQL types (filter out mapping keys)
        actual_allowed_enums = {k: v for k, v in allowed_enums.items() if not k.startswith("_fqn_to_enum_")}
        self.types_registry.update(actual_allowed_enums)

        return allowed_enums_metadata

    def _generate_object_types(self, unit_enums: dict[str, GraphQLEnumType]) -> None:
        """Phase 3: Generate main GraphQL object types."""
        # Create GraphQL types for each branch in topological order
        for fqn in self.branches_df.index:
            if fqn not in self.types_registry:
                gql_type = create_object_type(
                    fqn, self.branches_df, self.leaves_df, self.types_registry, unit_enums, self.vspec_comments
                )
                self.types_registry[fqn] = gql_type

    def _assemble_schema(self, unit_enums: dict[str, GraphQLEnumType]) -> GraphQLSchema:
        """Phase 4: Assemble the final GraphQL schema."""
        # Create the Query type
        vehicle_type = self.types_registry.get("Vehicle")
        query_type = GraphQLObjectType(
            name="Query",
            fields={"vehicle": GraphQLField(vehicle_type) if vehicle_type else GraphQLField(GraphQLString)},
        )

        # Create the schema with custom scalar types and directives
        vss_scalars = get_vss_scalar_types()
        all_types = vss_scalars + list(self.types_registry.values()) + list(unit_enums.values())
        schema = GraphQLSchema(
            query=query_type,
            types=all_types,
            directives=[VSpecDirective, RangeDirective, InstanceTagDirective],
        )

        return schema


class VSpecMetadataProcessor:
    """Processes VSS metadata for GraphQL directive generation."""

    @staticmethod
    def extract_field_metadata(field_path: str, child_fqn: str, leaf_row: pd.Series) -> dict[str, Any]:
        """Extract all metadata for a field in one pass."""
        metadata = {}

        # VSS type info
        leaf_type = leaf_row.get("type", "").upper()
        if leaf_type in ["SENSOR", "ACTUATOR", "ATTRIBUTE"]:
            metadata["vss_type"] = {"fqn": child_fqn, "vspec_type": leaf_type}

        # Comments
        vss_comment = leaf_row.get("comment", "")
        if vss_comment:
            metadata["comment"] = vss_comment

        # Range constraints
        min_val = leaf_row.get("min", None)
        max_val = leaf_row.get("max", None)
        if min_val is not None or max_val is not None:
            range_data = {}
            if min_val is not None:
                range_data["min"] = min_val
            if max_val is not None:
                range_data["max"] = max_val
            metadata["range"] = range_data

        # Deprecation
        deprecation = leaf_row.get("deprecation", "")
        if deprecation:
            metadata["deprecation"] = deprecation

        return metadata

    @staticmethod
    def store_field_metadata(vspec_comments: dict, field_path: str, metadata: dict[str, Any]) -> None:
        """Store field metadata in the appropriate vspec_comments sections."""
        if "vss_type" in metadata:
            vspec_comments["field_vss_types"][field_path] = metadata["vss_type"]

        if "comment" in metadata:
            vspec_comments["field_comments"][field_path] = metadata["comment"]

        if "range" in metadata:
            vspec_comments["field_ranges"][field_path] = metadata["range"]

        if "deprecation" in metadata:
            vspec_comments["field_deprecated"][field_path] = metadata["deprecation"]

    @staticmethod
    def extract_type_metadata(branch_row: pd.Series) -> dict[str, Any]:
        """Extract metadata for a type."""
        metadata = {}

        # Type-level comment
        vss_comment = branch_row.get("comment", "")
        if vss_comment:
            metadata["comment"] = vss_comment

        return metadata

    @staticmethod
    def store_type_metadata(vspec_comments: dict, type_name: str, fqn: str, metadata: dict[str, Any]) -> None:
        """Store type metadata in vspec_comments."""
        # Always store VSS type information
        vspec_comments["vss_types"][type_name] = {
            "fqn": fqn,
            "vspec_type": "BRANCH",  # All types created here are branches
        }

        # Store type-level comment if available
        if "comment" in metadata:
            vspec_comments["type_comments"][type_name] = metadata["comment"]


class FieldProcessor:
    """Handles processing of different GraphQL field types for S2DM exporter."""

    def __init__(self, vspec_comments: dict, types_registry: dict, unit_enums: dict):
        """
        Initialize the field processor.

        Args:
            vspec_comments: Dictionary to store @vspec comments and directives
            types_registry: Registry of already created GraphQL types
            unit_enums: Dictionary of unit enums by quantity
        """
        self.vspec_comments = vspec_comments
        self.types_registry = types_registry
        self.unit_enums = unit_enums

    def add_system_fields(self, fields: dict, type_name: str, branch_row: pd.Series) -> None:
        """Add system fields like ID and instanceTag."""
        # Add ID field for Vehicle and types with instances
        if type_name == "Vehicle" or branch_row.get("instances"):
            fields["id"] = GraphQLField(GraphQLNonNull(GraphQLID))

        # Add instanceTag field for types with instances
        if type_name in self.vspec_comments.get("instance_tag_types", {}):
            instance_tag_type_name = self.vspec_comments["instance_tag_types"][type_name]
            if instance_tag_type_name in self.types_registry:
                instance_tag_type = self.types_registry[instance_tag_type_name]
                fields["instanceTag"] = GraphQLField(instance_tag_type)

    def process_leaf_fields(self, fields: dict, type_name: str, fqn: str, leaves_df: pd.DataFrame) -> None:
        """Process leaf fields (attributes, sensors, actuators)."""
        child_leaves = leaves_df[leaves_df["parent"] == fqn]
        for child_fqn, leaf_row in child_leaves.iterrows():
            field_name = convert_name_for_graphql_schema(leaf_row["name"], GraphQLElementType.FIELD, S2DM_CONVERSIONS)
            field_type = get_graphql_type_for_leaf(leaf_row, self.types_registry)
            field_description = leaf_row.get("description", "")
            field_path = f"{type_name}.{field_name}"

            # Extract and store metadata using the metadata processor
            metadata = VSpecMetadataProcessor.extract_field_metadata(field_path, child_fqn, leaf_row)
            VSpecMetadataProcessor.store_field_metadata(self.vspec_comments, field_path, metadata)

            # Process unit arguments
            field_args = self._process_unit_arguments(leaf_row)

            fields[field_name] = GraphQLField(
                field_type, args=field_args if field_args else None, description=field_description
            )

    def process_branch_fields(self, fields: dict, fqn: str, branches_df: pd.DataFrame, leaves_df: pd.DataFrame) -> None:
        """Process branch fields (child branches)."""
        child_branches = branches_df[branches_df["parent"] == fqn]
        for child_fqn, child_branch_row in child_branches.iterrows():
            field_name = convert_name_for_graphql_schema(
                child_branch_row["name"], GraphQLElementType.FIELD, S2DM_CONVERSIONS
            )

            # Get or create the child type
            child_type = self._get_or_create_child_type(child_fqn, branches_df, leaves_df)

            # Handle instances (make it a list)
            if child_branch_row.get("instances"):
                field_name += "_s"  # Following the pattern from desired output
                fields[field_name] = GraphQLField(GraphQLList(child_type))
            else:
                fields[field_name] = GraphQLField(child_type)

    def _process_unit_arguments(self, leaf_row: pd.Series) -> dict:
        """Process unit arguments for a leaf field."""
        unit = leaf_row.get("unit", "")
        field_args = {}

        if unit and unit in dynamic_units:
            unit_data = dynamic_units[unit]
            quantity = unit_data.quantity
            if quantity:
                unit_enum = get_unit_enum_for_quantity(quantity, self.unit_enums)
                if unit_enum:
                    field_args["unit"] = GraphQLArgument(
                        type_=unit_enum,
                        default_value=unit,  # Use the unit key directly (e.g., 'mm', 'km')
                    )

        return field_args

    def _get_or_create_child_type(
        self, child_fqn: str, branches_df: pd.DataFrame, leaves_df: pd.DataFrame
    ) -> GraphQLObjectType:
        """Get or create a child type from the types registry."""
        if child_fqn not in self.types_registry:
            child_type = create_object_type(
                child_fqn, branches_df, leaves_df, self.types_registry, self.unit_enums, self.vspec_comments
            )
            self.types_registry[child_fqn] = child_type
        else:
            child_type = self.types_registry[child_fqn]
        return child_type


def create_object_type(
    fqn: str,
    branches_df: pd.DataFrame,
    leaves_df: pd.DataFrame,
    types_registry: dict,
    unit_enums: dict,
    vspec_comments: dict,
) -> GraphQLObjectType:
    """
    Create a GraphQL object type for a given VSS branch.

    Args:
        fqn: Fully qualified name of the branch
        branches_df: DataFrame containing branch metadata
        leaves_df: DataFrame containing leaf metadata
        types_registry: Registry of already created types
        unit_enums: Dictionary of unit enums by quantity
        vspec_comments: Dictionary to store @vspec comments

    Returns:
        GraphQLObjectType: The created GraphQL object type
    """
    branch_row = branches_df.loc[fqn]
    type_name = convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)
    description = branch_row.get("description", "")

    # Extract and store type metadata using the metadata processor
    type_metadata = VSpecMetadataProcessor.extract_type_metadata(branch_row)
    VSpecMetadataProcessor.store_type_metadata(vspec_comments, type_name, fqn, type_metadata)

    # Mark types with instances for @instanceTag directive
    # Note: Only the InstanceTag type gets the directive, not the main type
    # if branch_row.get("instances"):
    #     vspec_comments['instance_tags'][type_name] = True

    # Use a lambda to create fields lazily to avoid circular dependencies
    def get_fields():
        fields = {}

        # Create field processor to handle different field types
        field_processor = FieldProcessor(vspec_comments, types_registry, unit_enums)

        # Add system fields (ID, instanceTag)
        field_processor.add_system_fields(fields, type_name, branch_row)

        # Add fields for child leaves (attributes, sensors, actuators)
        field_processor.process_leaf_fields(fields, type_name, fqn, leaves_df)

        # Add fields for child branches
        field_processor.process_branch_fields(fields, fqn, branches_df, leaves_df)

        return fields

    return GraphQLObjectType(name=type_name, fields=get_fields, description=description)


def get_quantity_kinds_and_units() -> dict[str, dict[str, dict[str, str]]]:
    """Get the quantity kinds and their units from the VSS dynamic units."""
    quantity_units: dict[str, dict[str, dict[str, str]]] = {}

    # Process each unit only once to avoid duplicates
    # The dynamic_units dict contains both unit keys and unit display names pointing to the same VSSUnit
    # We want to process only the actual unit keys, not the display names
    processed_units = set()

    for unit_key, unit_data in dynamic_units.items():
        # Skip if we've already processed this VSSUnit object via its display name
        unit_id = id(unit_data)
        if unit_id in processed_units:
            continue

        quantity = unit_data.quantity
        unit_display_name = unit_data.unit  # This is the display name like "millimeter", "degree"

        if quantity and unit_display_name:
            if quantity not in quantity_units:
                quantity_units[quantity] = {}

            # Use the key that's NOT the display name
            # If unit_key equals the display name, find the actual key
            actual_unit_key = unit_key
            if unit_key == unit_display_name:
                # Find the actual key by looking for the other entry with same VSSUnit
                for other_key, other_data in dynamic_units.items():
                    if id(other_data) == unit_id and other_key != unit_display_name:
                        actual_unit_key = other_key
                        break

            quantity_units[quantity][actual_unit_key] = {"name": unit_display_name, "key": actual_unit_key}

            processed_units.add(unit_id)

    return quantity_units


def create_unit_enums() -> dict[str, GraphQLEnumType]:
    """Create GraphQL enums for VSS units grouped by quantity."""
    quantity_units = get_quantity_kinds_and_units()
    unit_enums = {}

    for quantity, units_data in quantity_units.items():
        # Create enum name: length -> LengthUnitEnum, angular-speed -> AngularSpeedUnitEnum
        enum_name = f"{convert_name_for_graphql_schema(quantity, GraphQLElementType.ENUM, S2DM_CONVERSIONS)}UnitEnum"

        # Create enum values
        enum_values = {}
        for unit_key, unit_info in units_data.items():
            # Use the unit name for enum value name (kilometer -> KILOMETER)
            unit_name = unit_info["name"]  # Use the display name from VSS unit data
            enum_value_name = convert_name_for_graphql_schema(
                unit_name, GraphQLElementType.ENUM_VALUE, S2DM_CONVERSIONS
            )

            # The GraphQL enum value should represent the original unit key
            # This is what will be used in schema serialization
            enum_values[enum_value_name] = GraphQLEnumValue(
                value=unit_key  # Use the unit key (e.g., 'km', 'km/h')
            )

        # Create the enum with description
        unit_enums[quantity] = GraphQLEnumType(
            name=enum_name,
            values=enum_values,
            description=f'Set of units for the quantity kind "{quantity}". NOTE: Taken from VSS specification.',
        )

    return unit_enums


def get_unit_enum_for_quantity(quantity: str, unit_enums: dict[str, GraphQLEnumType]) -> GraphQLEnumType | None:
    """Get the unit enum for a given quantity."""
    return unit_enums.get(quantity)


def print_schema_with_vspec_directives(
    schema: GraphQLSchema, unit_enums_metadata: dict, allowed_enums_metadata: dict, vspec_comments: dict
) -> str:
    """
    Custom schema printer that includes @vspec directives.

    Args:
        schema: The GraphQL schema to print
        unit_enums_metadata: Metadata for unit enums to add @vspec directives
        vspec_comments: Comments data for fields and types

    Returns:
        SDL string with @vspec directives
    """
    # Use directive processor instead of manual string manipulation
    return directive_processor.process_schema(schema, unit_enums_metadata, allowed_enums_metadata, vspec_comments)


def get_graphql_type_for_leaf(leaf_row: pd.Series, types_registry=None):
    """
    Get the appropriate GraphQL type for a VSS leaf node.

    Args:
        leaf_row: Pandas Series containing leaf metadata
        types_registry: Registry of custom GraphQL types (for enums)

    Returns:
        GraphQL type for the leaf
    """
    # Check for allowed values first - these override the base type
    if types_registry:
        try:
            allowed_values = leaf_row.get("allowed")
            if allowed_values is not None and isinstance(allowed_values, list) and len(allowed_values) > 0:
                # Create enum type name based on the leaf's fully qualified path
                # Use the index as the FQN since qualified_name might not be available
                fqn = leaf_row.name if hasattr(leaf_row, "name") else leaf_row.get("qualified_name", "unknown")
                enum_type_name = (
                    f"{convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)}_Enum"
                )

                # Return the enum type if it exists in registry
                if enum_type_name in types_registry:
                    return types_registry[enum_type_name]
        except (ValueError, TypeError, KeyError):
            # Handle pandas array issues gracefully
            pass

    datatype = leaf_row.get("datatype", "string")

    # Map VSS datatypes to GraphQL types
    return VSS_DATATYPE_MAP.get(datatype, GraphQLString)


def parse_instance_dimensions(instances_list):
    """
    Parse VSS instances list to extract dimensional data.

    Args:
        instances_list: List of instance definitions like:
        - ['Row[1,2]', ['DriverSide', 'PassengerSide']] (multi-dimensional)
        - ['Low', 'High'] (single dimension flat list)
        - [['Low', 'High']] (single dimension nested list)

    Returns:
        list: List of dimensional enum definitions like [
            {
                'dimension_name': 'dimension1',
                'enum_name': 'TypeName_InstanceTag_Dimension1',
                'values': ['Row1', 'Row2']
            },
            {
                'dimension_name': 'dimension2',
                'enum_name': 'TypeName_InstanceTag_Dimension2',
                'values': ['DriverSide', 'PassengerSide']
            }
        ]
    """
    dimensions = []

    # Special case: if all items are simple strings (not containing '[' or being lists),
    # treat the entire list as a single dimension
    if isinstance(instances_list, list) and all(isinstance(item, str) and "[" not in item for item in instances_list):
        # This is a flat list like ["Low", "High"] - treat as single dimension
        dimensions.append({"dimension_name": "dimension1", "dimension_num": 1, "values": instances_list})
        return dimensions

    # Handle multi-dimensional cases
    for idx, instance_def in enumerate(instances_list):
        dimension_num = idx + 1
        dimension_name = f"dimension{dimension_num}"

        if isinstance(instance_def, str):
            # Handle range format like "Row[1,2]"
            if "[" in instance_def and "]" in instance_def:
                # Extract base name and range
                base_name = instance_def.split("[")[0]
                range_part = instance_def.split("[")[1].split("]")[0]

                # Parse range (e.g., "1,2" -> [1, 2])
                range_values = [int(x.strip()) for x in range_part.split(",")]
                start, end = range_values[0], range_values[1]

                # Generate enum values (e.g., Row1, Row2)
                enum_values = [f"{base_name}{i}" for i in range(start, end + 1)]

                dimensions.append(
                    {"dimension_name": dimension_name, "dimension_num": dimension_num, "values": enum_values}
                )
        elif isinstance(instance_def, list):
            # Handle explicit list format like ['DriverSide', 'PassengerSide']
            if len(instance_def) > 0:
                # Use the actual values as enum values
                enum_values = instance_def

                dimensions.append(
                    {"dimension_name": dimension_name, "dimension_num": dimension_num, "values": enum_values}
                )

    return dimensions


def generate_instance_types_and_enums(branches_df, vspec_comments):
    """
    Generate instance tag types and dimensional enums for VSS instances.

    Returns:
        dict: Dictionary mapping enum/type names to GraphQL types
    """
    instance_types = {}

    # Find all branches with instances
    branches_with_instances = branches_df[branches_df["instances"].notna()]

    for fqn, branch_row in branches_with_instances.iterrows():
        instances = branch_row["instances"]
        if instances:
            base_type_name = convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)
            instance_tag_type_name = f"{base_type_name}_InstanceTag"

            dimensions = parse_instance_dimensions(instances)

            # Create dimensional enums
            instance_tag_fields = {}

            for dimension in dimensions:
                dimension_num = dimension["dimension_num"]
                enum_name = f"{base_type_name}_InstanceTag_Dimension{dimension_num}"
                enum_values = dimension["values"]

                # Create GraphQL enum values
                graphql_values = {}
                for value in enum_values:
                    graphql_values[value] = GraphQLEnumValue(value)

                # Create the GraphQL enum type
                dimensional_enum = GraphQLEnumType(
                    name=enum_name,
                    values=graphql_values,
                    description=f"Dimensional enum for VSS instance dimension {dimension_num}.",
                )

                instance_types[enum_name] = dimensional_enum

                # Add field to instance tag type
                instance_tag_fields[dimension["dimension_name"]] = GraphQLField(dimensional_enum)

            # Create the instance tag type
            instance_tag_type = GraphQLObjectType(
                name=instance_tag_type_name,
                fields=instance_tag_fields,
                description=f"Instance tag for {base_type_name} with dimensional information.",
            )

            instance_types[instance_tag_type_name] = instance_tag_type

            # Mark the instance tag type for @instanceTag directive
            vspec_comments["instance_tags"][instance_tag_type_name] = True

            # Store reference for adding instanceTag field to main type
            vspec_comments["instance_tag_types"] = vspec_comments.get("instance_tag_types", {})
            vspec_comments["instance_tag_types"][base_type_name] = instance_tag_type_name

    return instance_types


def generate_allowed_value_enums(leaves_df):
    """
    Generate GraphQL enums for VSS fields with allowed values.

    Returns:
        tuple: (allowed_enums dict, allowed_enums_metadata dict)
               allowed_enums: Dictionary mapping enum names to GraphQL enum types
               allowed_enums_metadata: Dictionary mapping enum names to their VSS metadata
    """
    allowed_enums = {}
    allowed_enums_metadata = {}

    # Find all leaves with allowed values
    leaves_with_allowed = leaves_df[leaves_df["allowed"].notna()]

    for fqn, leaf_row in leaves_with_allowed.iterrows():
        allowed_values = leaf_row["allowed"]
        if allowed_values and isinstance(allowed_values, list):
            # Generate enum name from FQN
            enum_name = f"{convert_name_for_graphql_schema(fqn, GraphQLElementType.TYPE, S2DM_CONVERSIONS)}_Enum"

            # Store metadata for @vspec directive generation
            allowed_enums_metadata[enum_name] = {"fqn": fqn, "allowed_values": {}}

            # Create GraphQL enum values
            graphql_values = {}
            for value in allowed_values:
                # Convert all values to strings and ensure they're valid GraphQL enum names
                value_str = str(value)
                original_value = value_str  # Store original for @vspec directive

                # GraphQL enum values must start with a letter or underscore
                if value_str[0].isdigit():
                    value_str = f"_{value_str}"
                # Replace any invalid characters
                value_str = value_str.replace(".", "_DOT_").replace("-", "_DASH_")

                graphql_values[value_str] = GraphQLEnumValue(value)

                # Store mapping for @vspec directive: GraphQL name -> original VSS value
                allowed_enums_metadata[enum_name]["allowed_values"][value_str] = original_value

            # Create the GraphQL enum type
            allowed_enums[enum_name] = GraphQLEnumType(
                name=enum_name, values=graphql_values, description=f"Allowed values for {fqn}."
            )

            # Also store a mapping from FQN to enum name for easy lookup
            allowed_enums[f"_fqn_to_enum_{fqn}"] = enum_name

    return allowed_enums, allowed_enums_metadata

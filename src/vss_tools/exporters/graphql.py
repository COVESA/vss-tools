# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0


from __future__ import annotations

import json
import re
import sys
from itertools import product
from pathlib import Path
from typing import Any, Dict

import graphene
import pandas as pd
import rich_click as click
from graphene import Field, Scalar

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.datatypes import Datatypes, dynamic_units, is_array
from vss_tools.main import get_trees
from vss_tools.tree import VSSNode, expand_string
from vss_tools.utils.graphql_utils import GraphQLElementType, convert_name_for_graphql_schema
from vss_tools.utils.pandas_utils import get_metadata_df


class GraphQLExporterException(Exception):
    """Exception raised for errors in the GraphQL export process."""

    pass


# ========= Custom GraphQL scalar types =========
class Int8(Scalar):
    pass


class UInt8(Scalar):
    pass


class Int16(Scalar):
    pass


class UInt16(Scalar):
    pass


class UInt32(Scalar):
    pass


class Int64(Scalar):
    pass


class UInt64(Scalar):
    pass


# ========= Mapping aids =========
# Use the unified GraphQL element type enum from utils
GQLElementType = GraphQLElementType


datatype_map = {
    Datatypes.INT8[0]: Int8,
    Datatypes.INT8_ARRAY[0]: graphene.List(Int8),
    Datatypes.UINT8[0]: UInt8,
    Datatypes.UINT8_ARRAY[0]: graphene.List(UInt8),
    Datatypes.INT16[0]: Int16,
    Datatypes.INT16_ARRAY[0]: graphene.List(Int16),
    Datatypes.UINT16[0]: UInt16,
    Datatypes.UINT16_ARRAY[0]: graphene.List(UInt16),
    Datatypes.INT32[0]: graphene.Int,
    Datatypes.INT32_ARRAY[0]: graphene.List(graphene.Int),
    Datatypes.UINT32[0]: UInt32,
    Datatypes.UINT32_ARRAY[0]: graphene.List(UInt32),
    Datatypes.INT64[0]: Int64,
    Datatypes.INT64_ARRAY[0]: graphene.List(Int64),
    Datatypes.UINT64[0]: UInt64,
    Datatypes.UINT64_ARRAY[0]: graphene.List(UInt64),
    Datatypes.FLOAT[0]: graphene.Float,
    Datatypes.FLOAT_ARRAY[0]: graphene.List(graphene.Float),
    Datatypes.DOUBLE[0]: graphene.Float,
    Datatypes.DOUBLE_ARRAY[0]: graphene.List(graphene.Float),
    Datatypes.BOOLEAN[0]: graphene.Boolean,
    Datatypes.BOOLEAN_ARRAY[0]: graphene.List(graphene.Boolean),
    Datatypes.STRING[0]: graphene.String,
    Datatypes.STRING_ARRAY[0]: graphene.List(graphene.String),
}

# ========= Global variables =========
vss_branches_df = pd.DataFrame()
vss_leaves_df = pd.DataFrame()
gql_allowed_enums: Dict[str, graphene.Enum] = {}
gql_instance_enums: Dict[str, graphene.Enum] = {}
gql_unit_enums: Dict[str, graphene.Enum] = {}

mapping_quantity_kinds_df = pd.DataFrame(columns=["vspec_quantity_kind", "gql_unit_enum", "units"]).set_index(
    "vspec_quantity_kind"
)
mapping_branches_df = pd.DataFrame(columns=["vspec_fqn", "gql_type", "gql_instance_enum", "instance_labels"]).set_index(
    "vspec_fqn"
)
mapping_leaves_df = pd.DataFrame(
    columns=["vspec_fqn", "gql_field", "in_gql_type", "gql_allowed_enum", "allowed_values"]
).set_index("vspec_fqn")


def get_gql_name(text: str, gql_type: GQLElementType) -> str:
    """
    Converts a given text to a GraphQL compatible name based on the given GQLElementType.

    This function wraps the unified convert_name_for_graphql_schema utility to maintain
    backward compatibility with existing code.

    For example:
    - type, enum, and scalars must be PascalCase.
    - fields and arguments must be camelCase.
    - enum values must be SCREAMING_SNAKE_CASE.
    """
    return convert_name_for_graphql_schema(text, gql_type)


def get_unit_enum_name(quantity_kind: str) -> str:
    """Get the name for the GraphQL unit enum"""
    text = f"{quantity_kind}_Unit"
    return get_gql_name(text, GQLElementType.ENUM)


def get_gql_unit_enums() -> Dict[str, graphene.Enum]:
    """Get GraphQL enums for VSS units and quantity kinds."""
    global mapping_quantity_kinds_df

    spec_quantity_kinds = get_quantity_kinds_and_units()
    unit_enums: Dict[str, graphene.Enum] = {}

    # Create a graphene enum for each key in the spec_quantity_kinds
    for quantity_kind, units in spec_quantity_kinds.items():
        enum_name = get_unit_enum_name(quantity_kind)
        enum_values = {}
        unit_mappings = {}
        for unit in units:
            unit_name = get_gql_name(unit, GQLElementType.ENUM_VALUE)
            unit_mappings[unit] = unit_name
            enum_values[unit_name] = unit_name

        unit_enums[enum_name] = type(enum_name, (graphene.Enum,), sort_dict_by_key(enum_values))  # type: ignore
        mapping_quantity_kinds_df.loc[quantity_kind] = [enum_name, sort_dict_by_key(unit_mappings)]

    return unit_enums


def get_quantity_kinds_and_units() -> dict[str, set[str]]:
    """Get the quantity kinds and their units as specified in VSS."""
    spec_quantity_kinds: Dict[str, set[str]] = {}
    for unit_data in dynamic_units.values():
        quantity_kind_name = unit_data.quantity
        if unit_data.unit:
            unit_name = unit_data.unit
            if quantity_kind_name not in spec_quantity_kinds:
                spec_quantity_kinds[quantity_kind_name] = set()
            spec_quantity_kinds[quantity_kind_name].add(unit_name)

    return dict(sorted(spec_quantity_kinds.items()))


def get_branches_with_specified_instances() -> pd.DataFrame:
    """Get the branches that have instances specified."""
    return vss_branches_df[vss_branches_df["instances"].astype(str) != "[]"]


def get_instances_enums() -> Dict[str, graphene.Enum]:
    """Create a GraphQL enum for each branch that has instances specified."""
    enums: Dict[str, graphene.Enum] = {}
    branches_with_instances = get_branches_with_specified_instances()

    for fqn, row in branches_with_instances.iterrows():
        spec_instances = row["instances"]
        instance_labels = expand_instance_labels(spec_instances)
        mapping_instance_labels = {}
        enum_description = (
            "Specified reference instance names (informative only) for the type "
            f"{get_gql_name(f'{fqn}', GQLElementType.TYPE)}."
        )
        enum_name = get_gql_name(f"{fqn}.Instance", GQLElementType.ENUM)  # TODO: Todo pass a shorter name!
        enum_values = {}

        for label in instance_labels:
            value = get_gql_name(label, GQLElementType.ENUM_VALUE)
            enum_values[value] = value
            mapping_instance_labels[label] = value

        enums[fqn] = type(enum_name, (graphene.Enum,), enum_values, description=enum_description)  # type: ignore

        global mapping_branches_df
        mapping_branches_df.loc[fqn, ["gql_instance_enum", "instance_labels"]] = [enum_name, mapping_instance_labels]  # type: ignore

    return enums


def expand_instance_labels(instances: list[str]) -> list[str]:
    """
    Expands the instance expressions into a unidimensional list of combined labels.

    Example 1:
        - input:  ['Row[1,2]', ['DriverSide', 'PassengerSide']]
        - result: ['Row1.DriverSide', 'Row1.PassengerSide', 'Row2.DriverSide', 'Row2.PassengerSide']

    Example 2:
        - input:    ['Rear', 'Front']
        - result:   ['Rear', 'Front']
    """

    pattern = r".*\[\d+,\d+\].*"
    if not is_list_inside(instances) and not any(re.match(pattern, i) for i in instances):
        return instances  # If the instance is not a list and does not contain a range, return it as is.
    else:
        instance_levels = []
        for instance_expression in instances:
            if isinstance(instance_expression, str) and re.match(pattern, instance_expression):
                instance_levels.append(expand_string(instance_expression))
            elif isinstance(instance_expression, list):
                instance_levels.append(instance_expression)
            else:
                log.warning(f"Special case not considered: {instance_expression}")

        if is_list_inside(instance_levels):
            return [".".join(item) for item in product(*instance_levels)]
        else:
            return [item for sublist in instance_levels for item in sublist]  # Flatten the list before returning


def is_list_inside(some_list: list) -> bool:
    """Check if a list contains another list."""
    return any(isinstance(element, list) for element in some_list)


def get_allowed_enums() -> Dict[str, graphene.Enum]:
    """Create a GraphQL enum for each leaf that has allowed values specified."""
    gql_allowed_enums: Dict[str, graphene.Enum] = {}

    leaves_with_allowed = vss_leaves_df[vss_leaves_df["allowed"].astype(str) != ""]

    for fqn, row in leaves_with_allowed.iterrows():
        allowed_list = eval(row["allowed"]) if isinstance(row["allowed"], str) else row["allowed"]
        enum_values = {}
        mapping_allowed_values = {}
        for allowed_value in allowed_list:
            enum_name = get_gql_name(str(fqn), GQLElementType.ENUM)
            value = get_gql_name(str(allowed_value), GQLElementType.ENUM_VALUE)
            enum_values[value] = value
            mapping_allowed_values[allowed_value] = value

        gql_allowed_enums[fqn] = type(enum_name, (graphene.Enum,), enum_values)  # type: ignore
        global mapping_leaves_df
        mapping_leaves_df.loc[fqn, ["gql_allowed_enum", "allowed_values"]] = [enum_name, mapping_allowed_values]  # type: ignore

    return gql_allowed_enums


def get_gql_object_types() -> Dict[str, graphene.ObjectType]:
    """Create a GraphQL object type for each branch in the VSS."""
    gql_object_types: Dict[str, graphene.ObjectType] = {}

    for fqn, _ in vss_branches_df.iterrows():
        gql_object_types[str(fqn)] = create_gql_object_type(str(fqn))

    return gql_object_types


def get_description(fqn: str) -> str:
    description = ""
    if fqn in vss_branches_df.index or fqn in vss_leaves_df.index:
        df = vss_branches_df if fqn in vss_branches_df.index else vss_leaves_df
        description = str(df.loc[fqn, "description"])
        comment = str(df.loc[fqn, "comment"])
        description += f"\n@comment: {comment}" if comment else ""

        if fqn in vss_leaves_df.index:
            for attr in ["min", "max", "default"]:
                value = df.loc[fqn, attr]
                if value:
                    description += f"\n@{attr}: {str(value)}"

    return description


def create_gql_object_type(fqn: str) -> graphene.ObjectType:
    """Create a GraphQL object type for a given Fully Qualified Name (fqn) in the VSS."""
    gql_fields: Dict[str, graphene.Field] = {}
    gql_type_name = get_gql_name(fqn, GQLElementType.TYPE)

    if gql_type_name == "Vehicle":
        gql_fields["id"] = Field(name="id", type_=graphene.NonNull(graphene.ID))

    gql_type_description = get_description(fqn)
    branch_deprecation = vss_branches_df.loc[fqn, "deprecation"]

    if branch_deprecation:
        gql_type_description += f'\n@deprecated(reason: "{branch_deprecation}")'

    if fqn in get_branches_with_specified_instances().index:
        gql_fields["id"] = Field(name="id", type_=graphene.NonNull(graphene.ID))
        gql_fields["instanceLabel"] = Field(name="instanceLabel", type_=graphene.String)

    add_leaf_fields(fqn, gql_fields)
    add_branch_fields(fqn, gql_fields)

    global mapping_branches_df
    mapping_branches_df.loc[fqn, "gql_type"] = gql_type_name
    return type(gql_type_name, (graphene.ObjectType,), gql_fields, description=gql_type_description)  # type: ignore


def add_leaf_fields(fqn: str, gql_fields: Dict[str, graphene.Field]) -> None:
    """Add GraphQL fields for each leaf that belongs to the current branch."""
    child_leaves = vss_leaves_df[vss_leaves_df["parent"] == fqn]

    for child_fqn, child_leaf_metadata_row in child_leaves.iterrows():
        field_name = get_gql_name(child_leaf_metadata_row["name"], GQLElementType.FIELD)
        unit = child_leaf_metadata_row["unit"]
        allowed = child_leaf_metadata_row["allowed"]
        deprecation = child_leaf_metadata_row["deprecation"]

        field_args: Dict[str, Any] = {
            "name": field_name,
            "description": get_description(str(child_fqn)),
            "type_": None,
            "args": {},
        }

        if deprecation:
            field_args["deprecation_reason"] = deprecation

        if allowed == "":
            field_args["type_"] = datatype_map[child_leaf_metadata_row["datatype"]]
        else:
            allowed_enum = gql_allowed_enums[str(child_fqn)]
            datatype = child_leaf_metadata_row["datatype"]
            if datatype and is_array(datatype):
                field_args["type_"] = graphene.List(allowed_enum)
            else:
                field_args["type_"] = allowed_enum

        if unit:
            add_unit_argument(field_args, unit)

        gql_fields[field_name] = Field(**field_args)

        global mapping_leaves_df
        mapping_leaves_df.loc[child_fqn, ["gql_field", "in_gql_type"]] = [  # type: ignore
            field_name,
            get_gql_name(fqn, GQLElementType.TYPE),
        ]


def add_unit_argument(field_args: Dict[str, Any], unit: str) -> None:
    """Add unit argument to the field arguments."""
    try:
        quantity_kind = dynamic_units[unit].quantity
        enum_name = get_unit_enum_name(quantity_kind)
        unit_enum = gql_unit_enums[enum_name]
        unit_value = dynamic_units[unit].unit

        if unit_value is not None:
            unit_enum_value = get_gql_name(unit_value, GQLElementType.ENUM_VALUE)
        else:
            raise GraphQLExporterException(f"Unit value for '{unit}' is None")

        if unit_enum_value not in unit_enum._meta.enum.__members__:
            raise GraphQLExporterException(f"Unit enum value '{unit_enum_value}' not found in enum '{unit_enum}'")
        else:
            field_args["args"]["unit"] = graphene.Argument(type_=unit_enum, default_value=unit_enum_value)  # type: ignore

    except GraphQLExporterException:
        raise


def add_branch_fields(fqn: str, gql_fields: Dict[str, graphene.Field]) -> None:
    """Add GraphQL fields for each sub-branch and call the creation of the GraphQL type recursively."""
    child_branches = vss_branches_df[vss_branches_df["parent"] == fqn]
    branches_with_instances = get_branches_with_specified_instances()

    for child_fqn, child_branch_metadata_row in child_branches.iterrows():
        field_name = get_gql_name(child_branch_metadata_row["name"], GQLElementType.FIELD)
        field_type = create_gql_object_type(str(child_fqn))
        if child_fqn in branches_with_instances.index:
            field_name += "_s"
            field_type = graphene.List(field_type)
        gql_fields[field_name] = Field(name=field_name, type_=field_type)


def get_graphql_schema(tree: VSSNode) -> graphene.Schema:
    """Create a GraphQL schema from the VSS tree."""
    global vss_branches_df, vss_leaves_df, gql_unit_enums, gql_allowed_enums, gql_instance_enums

    # Get pandas DataFrame for all the metadata in the vspec
    vss_branches_df, vss_leaves_df = get_metadata_df(tree)

    # Include the custom scalar types even if they are not used by any type in the schema
    custom_scalars = [Int8, UInt8, Int16, UInt16, UInt32, Int64, UInt64]

    # Create enums for the instances specified
    gql_instance_enums = get_instances_enums()

    # Get GraphQL enums for the units and quantities
    gql_unit_enums = get_gql_unit_enums()

    # In the leaves DataFrame, get the entries that have allowed values and create enums for them
    gql_allowed_enums = get_allowed_enums()

    # In branches DataFrame, create a GraphQL type for each pure branch (not for instance branches)
    gql_branch_types = get_gql_object_types()

    class Query(graphene.ObjectType):
        vehicle = graphene.Field(gql_branch_types[get_gql_name(tree.name, gql_type=GQLElementType.TYPE)])

    # Order the schema as desired
    ordered_types = (
        [Query]
        + custom_scalars
        + list(gql_branch_types.values())
        + list(gql_allowed_enums.values())
        + list(gql_unit_enums.values())
        + list(gql_instance_enums.values())
    )
    return graphene.Schema(types=ordered_types, auto_camelcase=False)


def export_mappings() -> Dict[str, Dict[str, Any]]:
    """Export the mappings of the VSS to the GraphQL schema."""
    mappings = {
        "quantity_kinds_and_units": {
            "info": "Mappings of vspec quantity kind and their units to the corresponding names in GraphQL.",
            "mappings": sort_dict_by_key(mapping_quantity_kinds_df.to_dict(orient="index")),
        },
        "vspec_branches": {
            "info": "Mappings of vspec branches to the corresponding names in GraphQL.",
            "mappings": sort_dict_by_key(mapping_branches_df.fillna("").to_dict(orient="index")),
        },
        "vspec_leaves": {
            "info": "Mappings of vspec leaves to the corresponding names in GraphQL.",
            "mappings": sort_dict_by_key(mapping_leaves_df.fillna("").to_dict(orient="index")),
        },
    }
    return mappings


def sort_dict_by_key(dictionary: dict) -> dict:
    """Sorts a dictionary by its keys in a case-insensitive manner but preserves the original key."""
    return dict(sorted(dictionary.items(), key=lambda item: item[0].lower()))


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
@clo.strict_exceptions_opt
@click.option(
    "--legacy-mapping-output",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output json file of the legacy units and quantities",
)
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    legacy_mapping_output: Path | None,
    strict_exceptions: Path | None,
):
    """
    Export a VSS specification to a GraphQL schema.
    """
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
            strict_exceptions_file=strict_exceptions,
        )

        log.info("Generating GraphQL output...")

        gql_schema = get_graphql_schema(tree)
        mappings = export_mappings()

        with open(output, "w") as outfile:
            outfile.write(f"{str(gql_schema)}\n")

        if legacy_mapping_output:
            with open(legacy_mapping_output, "w") as mapping_outfile:
                mapping_outfile.write(json.dumps(mappings, indent=4))
    except GraphQLExporterException as e:
        log.error(e)
        sys.exit(1)

# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
from typing import Dict

import rich_click as click
from graphql import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLField,
    GraphQLFloat,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    print_schema,
)

import vss_tools.vspec.cli_options as clo
from vss_tools import log
from vss_tools.vspec.datatypes import Datatypes
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.model import VSSDataDatatype
from vss_tools.vspec.tree import VSSNode
from vss_tools.vspec.utils.misc import camel_back

GRAPHQL_TYPE_MAPPING = {
    Datatypes.INT8[0]: GraphQLInt,
    Datatypes.INT8_ARRAY[0]: GraphQLList(GraphQLInt),
    Datatypes.UINT8[0]: GraphQLInt,
    Datatypes.UINT8_ARRAY[0]: GraphQLList(GraphQLInt),
    Datatypes.INT16[0]: GraphQLInt,
    Datatypes.INT16_ARRAY[0]: GraphQLList(GraphQLInt),
    Datatypes.UINT16[0]: GraphQLInt,
    Datatypes.UINT16_ARRAY[0]: GraphQLList(GraphQLInt),
    Datatypes.INT32[0]: GraphQLInt,
    Datatypes.INT32_ARRAY[0]: GraphQLList(GraphQLInt),
    Datatypes.UINT32[0]: GraphQLFloat,
    Datatypes.UINT32_ARRAY[0]: GraphQLList(GraphQLFloat),
    Datatypes.INT64[0]: GraphQLFloat,
    Datatypes.INT64_ARRAY[0]: GraphQLList(GraphQLFloat),
    Datatypes.UINT64[0]: GraphQLFloat,
    Datatypes.UINT64_ARRAY[0]: GraphQLList(GraphQLFloat),
    Datatypes.FLOAT[0]: GraphQLFloat,
    Datatypes.FLOAT_ARRAY[0]: GraphQLList(GraphQLFloat),
    Datatypes.DOUBLE[0]: GraphQLFloat,
    Datatypes.DOUBLE_ARRAY[0]: GraphQLList(GraphQLFloat),
    Datatypes.BOOLEAN[0]: GraphQLBoolean,
    Datatypes.BOOLEAN_ARRAY[0]: GraphQLList(GraphQLBoolean),
    Datatypes.STRING[0]: GraphQLString,
    Datatypes.STRING_ARRAY[0]: GraphQLList(GraphQLString),
}


class GraphQLFieldException(Exception):
    pass


def get_schema_from_tree(root: VSSNode, additional_leaf_fields: list) -> str:
    """Takes a VSSNode and additional fields for the leafs. Returns a graphql schema as string."""
    args = dict(
        id=GraphQLArgument(
            GraphQLNonNull(GraphQLString),
            description="VIN of the vehicle that you want to request data for.",
        ),
        after=GraphQLArgument(
            GraphQLString,
            description=(
                "Filter data to only provide information that was sent " "from the vehicle after that timestamp."
            ),
        ),
    )

    root_query = GraphQLObjectType(
        "Query",
        lambda: {"vehicle": GraphQLField(to_gql_type(root, additional_leaf_fields), args)},
    )
    return print_schema(GraphQLSchema(root_query))


def to_gql_type(node: VSSNode, additional_leaf_fields: list) -> GraphQLObjectType:
    if isinstance(node.data, VSSDataDatatype):
        fields = leaf_fields(node, additional_leaf_fields)
    else:
        fields = branch_fields(node, additional_leaf_fields)
    return GraphQLObjectType(
        name=node.get_fqn("_"),
        fields=fields,
        description=node.get_vss_data().description,
    )


def leaf_fields(node: VSSNode, additional_leaf_fields: list) -> Dict[str, GraphQLField]:
    field_dict = {}
    datatype = getattr(node.data, "datatype", None)
    if datatype is not None:
        field_dict["value"] = field(node, "Value: ", GRAPHQL_TYPE_MAPPING[datatype])
    field_dict["timestamp"] = field(node, "Timestamp: ")
    if additional_leaf_fields:
        for additional_field in additional_leaf_fields:
            if len(additional_field) == 2:
                field_dict[additional_field[0]] = field(node, f" {str(additional_field[1])}: ")
            else:
                raise GraphQLFieldException("", "", "Incorrect format of graphql field specification")
    unit = getattr(node.data, "unit", None)
    if unit:
        field_dict["unit"] = field(node, "Unit of ")
    return field_dict


def branch_fields(node: VSSNode, additional_leaf_fields: list) -> Dict[str, GraphQLField]:
    # we only consider nodes that either have children or are datatype leafs
    valid = (c for c in node.children if len(c.children) or hasattr(c.data, "datatype"))
    return {camel_back(c.name): field(c, type=to_gql_type(c, additional_leaf_fields)) for c in valid}


def field(node: VSSNode, description_prefix="", type=GraphQLString) -> GraphQLField:
    data = node.get_vss_data()
    return GraphQLField(
        type,
        deprecation_reason=data.deprecation,
        description=f"{description_prefix}{data.description}",
    )


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
@click.option(
    "--gql-fields",
    "-g",
    multiple=True,
    help="""
        Add additional fields to the nodes in the graphql schema.
        Usage: '<field_name>,<description>'",
    """,
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
    gql_fields: list[str],
):
    """
    Export as GraphQL.
    """
    tree, _ = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        quantities=quantities,
        units=units,
        overlays=overlays,
    )
    log.info("Generating graphql output...")
    outfile = open(output, "w")
    gqlfields: list[list[str]] = []
    for field in gql_fields:
        gqlfields.append(field.split(","))
    outfile.write(get_schema_from_tree(tree, gqlfields))
    outfile.write("\n")
    outfile.close()

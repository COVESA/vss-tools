#!/usr/bin/env python3

#
# Copyright (C) 2022, Bayerische Motoren Werke Aktiengesellschaft (BMW AG)
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

import argparse
from vspec.model.vsstree import VSSNode
from vspec.utils.stringstyle import camel_back
from vspec.model.constants import VSSDataType
from vspec import VSpecError
from typing import Dict

from graphql import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLArgument,
    GraphQLNonNull,
    GraphQLString,
    GraphQLList,
    print_schema,
    GraphQLInt,
    GraphQLFloat,
    GraphQLBoolean,
)

GRAPHQL_TYPE_MAPPING = {
    VSSDataType.INT8: GraphQLInt,
    VSSDataType.INT8_ARRAY: GraphQLList(GraphQLInt),
    VSSDataType.UINT8: GraphQLInt,
    VSSDataType.UINT8_ARRAY: GraphQLList(GraphQLInt),
    VSSDataType.INT16: GraphQLInt,
    VSSDataType.INT16_ARRAY: GraphQLList(GraphQLInt),
    VSSDataType.UINT16: GraphQLInt,
    VSSDataType.UINT16_ARRAY: GraphQLList(GraphQLInt),
    VSSDataType.INT32: GraphQLInt,
    VSSDataType.INT32_ARRAY: GraphQLList(GraphQLInt),
    VSSDataType.UINT32: GraphQLFloat,
    VSSDataType.UINT32_ARRAY: GraphQLList(GraphQLFloat),
    VSSDataType.INT64: GraphQLFloat,
    VSSDataType.INT64_ARRAY: GraphQLList(GraphQLFloat),
    VSSDataType.UINT64: GraphQLFloat,
    VSSDataType.UINT64_ARRAY: GraphQLList(GraphQLFloat),
    VSSDataType.FLOAT: GraphQLFloat,
    VSSDataType.FLOAT_ARRAY: GraphQLList(GraphQLFloat),
    VSSDataType.DOUBLE: GraphQLFloat,
    VSSDataType.DOUBLE_ARRAY: GraphQLList(GraphQLFloat),
    VSSDataType.BOOLEAN: GraphQLBoolean,
    VSSDataType.BOOLEAN_ARRAY: GraphQLList(GraphQLBoolean),
    VSSDataType.STRING: GraphQLString,
    VSSDataType.STRING_ARRAY: GraphQLList(GraphQLString),
}


def add_arguments(parser: argparse.ArgumentParser):
    # no additional output for graphql at this moment
    parser.description = "The graphql exporter never generates uuid, i.e. the --uuid option has no effect."
    parser.add_argument('--gqlfield', action='append', nargs=2,
                        help=" Add additional fields to the nodes in the graphql schema. "
                             "use: <field_name> <description>")


def get_schema_from_tree(root_node: VSSNode, additional_leaf_fields: list) -> str:
    """Takes a VSSNode and additional fields for the leafs. Returns a graphql schema as string."""
    args = dict(
        id=GraphQLArgument(
            GraphQLNonNull(GraphQLString),
            description="VIN of the vehicle that you want to request data for.",
        ),
        after=GraphQLArgument(
            GraphQLString,
            description=(
                "Filter data to only provide information that was sent "
                "from the vehicle after that timestamp."
            ),
        ),
    )

    root_query = GraphQLObjectType(
        "Query",
        lambda: {"vehicle": GraphQLField(to_gql_type(root_node, additional_leaf_fields), args)},
    )
    return print_schema(GraphQLSchema(root_query))


def to_gql_type(node: VSSNode, additional_leaf_fields: list) -> GraphQLObjectType:
    return GraphQLObjectType(
        name=node.qualified_name("_"),
        fields=leaf_fields(node, additional_leaf_fields) if hasattr(
            node, "datatype") else branch_fields(node, additional_leaf_fields),
        description=node.description,
    )


def leaf_fields(node: VSSNode, additional_leaf_fields: list) -> Dict[str, GraphQLField]:
    field_dict = {}
    if node.datatype is not None:
        field_dict["value"] = field(node, "Value: ", GRAPHQL_TYPE_MAPPING[node.datatype])
    field_dict["timestamp"] = field(node, "Timestamp: ")
    if additional_leaf_fields:
        for additional_field in additional_leaf_fields:
            if len(additional_field) == 2:
                field_dict[additional_field[0]] = field(node, f" {str(additional_field[1])}: ")
            else:
                raise VSpecError("", "", "Incorrect format of graphql field specification")
    if node.has_unit():
        field_dict["unit"] = field(node, "Unit of ")
    return field_dict


def branch_fields(node: VSSNode, additional_leaf_fields: list) -> Dict[str, GraphQLField]:
    # we only consider nodes that either have children or are leave with a datatype
    valid = (c for c in node.children if len(c.children) or hasattr(c, "datatype"))
    return {camel_back(c.name): field(c, type=to_gql_type(c, additional_leaf_fields)) for c in valid}


def field(node: VSSNode, description_prefix="", type=GraphQLString) -> GraphQLField:
    return GraphQLField(
        type,
        deprecation_reason=node.deprecation or None,
        description=f"{description_prefix}{node.description}",
    )


def export(config: argparse.Namespace, root: VSSNode, print_uuid):
    print("Generating graphql output...")
    outfile = open(config.output_file, 'w')
    outfile.write(get_schema_from_tree(root, config.gqlfield))
    outfile.write("\n")
    outfile.close()

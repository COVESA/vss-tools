#
# Copyright (C) 2022, Bayerische Motoren Werke Aktiengesellschaft (BMW AG)
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

import re
from anytree import RenderTree, PreOrderIter
from model.vsstree import VSSNode, camel_back
from model.constants import GRAPHQL_TYPE_MAPPING
from anytree import PostOrderIter
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
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLString,
)


def get_schema_from_tree(root_node: VSSNode) -> str:
    """Takes a VSSNode. Returns a graphql schema as string."""
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
        lambda: {"vehicle": GraphQLField(to_gql_type(root_node), args)},
    )
    return print_schema(GraphQLSchema(root_query))


def to_gql_type(node: VSSNode) -> GraphQLObjectType:
    return GraphQLObjectType(
        name=node.qualified_name("_"),
        fields=leaf_fields(node) if hasattr(node, "data_type") else branch_fields(node),
        description=node.description,
    )


def leaf_fields(node: VSSNode) -> Dict[str, GraphQLField]:
    field_dict = {
        "value": field(node, "Value: ", GRAPHQL_TYPE_MAPPING[node.data_type]),
        "source": field(node, "Source system: "),
        "channel": field(node, "Collecting channel: "),
        "timestamp": field(node, "Timestamp: "),
    }
    if hasattr(node, "unit"):
        field_dict["unit"] = field(node, "Unit of ")
    return field_dict


def branch_fields(node: VSSNode) -> Dict[str, GraphQLField]:
    # we only consider nodes that either have children or are leave with a data_type
    valid = (c for c in node.children if len(c.children) or hasattr(c, "data_type"))
    return {camel_back(c.name): field(c, type=to_gql_type(c)) for c in valid}


def field(node: VSSNode, description_prefix="", type=GraphQLString) -> GraphQLField:
    return GraphQLField(
        type,
        deprecation_reason=node.deprecation or None,
        description=f"{description_prefix}{node.description}",
    )

# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from vss_tools import log
from vss_tools.vspec.model import VSSDataBranch
from vss_tools.vspec.tree import VSSNode

from ..config import config as cfg
from . import ttl_builder_helper as ttl_builder
from . import vss_helper as vss_helper
from .file_helper import write_graph_to_file
from .namespaces import get_node_name_from_vspec_uri, samm_output_namespace
from .samm_concepts import SammConcepts, VSSConcepts
from .string_helper import str_to_uc_first_camel_case


# Parse provided VSSNode to an RDF Graph and write it to a TTL file
def parse_vss_tree(path_to_ttl: Path, vss_node: VSSNode, split_vss: bool):
    # Process provided vss_node so to get all of its unique VSSNode names, check if there is any duplicates etc.
    # This will be further used to make sure that we don't get any duplicate nodes in the generated TTL graph(s)
    vss_helper.count_vss_tree_unique_node_names(vss_node)

    log.debug(
        "Parse VSS node: '%s' to TTL file\n  -- as aspect%s\n", vss_node.name, "\n  -- split" if split_vss else ""
    )

    # Skip parsing of VSSNode is branches, which have only deprecated children
    # NOTE: this is a special case for the OBD branch, which children are marked as deprecated from VSS 5.0,
    #       but the branch itself is not marked as deprecated.
    deprecated_children = list(filter(lambda n: n.data.deprecation, vss_node.children))

    if len(deprecated_children) == len(vss_node.children):
        log.warning(
            "All child nodes of VSSNode: '%s' are deprecated.\n" "Skip the parsing of VSSNode: '%s'.\n",
            vss_node.name,
            vss_node.name,
        )

        return "DEPRECATED"

    # Initialize RDF Graph for current node
    graph = ttl_builder.setup_graph()

    # Build VSS graph tree node.
    # NOTE: ESMF-AME requires standalone aspect models to have an aspect node.
    node_uri = handle_vss_node(path_to_ttl, graph, vss_node, True, split_vss)

    if node_uri != "DEPRECATED":
        # Print graph for current vss_node to a TTL file
        # NOTE: make sure that TTL file name will reflect this graph's Aspect model name, i.e. uc first camel case
        vss_node_ttl_file = write_graph_to_file(path_to_ttl, str_to_uc_first_camel_case(vss_node.ttl_name), graph)

        log.debug("TTL file for parsed VSS node: '%s' is:\n'%s'\n", vss_node.name, vss_node_ttl_file)

    return node_uri


def handle_vss_node(path_to_ttl: Path, graph: Graph, vss_node: VSSNode, is_aspect: bool, split_vss: bool):
    log.debug(
        "Handle VSSNode: '%s'\n  -- node VSS path: '%s'\n  -- is_aspect: '%s'\n",
        vss_node.name,
        vss_node.get_fqn(),
        is_aspect,
    )

    # Check if node is deprecated and return DEPRECATED so it will be skipped for further conversion to TTL
    if (
        hasattr(vss_node.data, "deprecation")
        and vss_node.data.deprecation
        and len(vss_node.data.deprecation.strip()) > 0
    ):
        log.warning(
            "Skipping VSSNode: '%s' since it is deprecated.\nDeprecation: '%s'\n",
            vss_node.name,
            vss_node.data.deprecation,
        )

        return "DEPRECATED"

    # Build the general graph node for current vss_node
    node_uri = ttl_builder.add_graph_node(graph, vss_node, is_aspect)

    if isinstance(vss_node.data, VSSDataBranch):
        node_char_uri = ttl_builder.add_node_branch_characteristic(graph, vss_node, node_uri)

        if vss_node.data.instances:
            # Build instance(s) node(s) for the current vss_node ONLY when node is NOT EXPANDED.
            # Otherwise, the expanded child nodes will cause conflicts with generated instance nodes
            # and mess up the generated aspect model.
            #
            # NOTE: in this case the node's characteristic (node_char_uri),
            #       will become a characteristic of each of this vss_node's instance(s)
            node_name = get_node_name_from_vspec_uri(node_uri)

            instances_dict_tree = vss_helper.get_instances_dict_tree(vss_node.data.instances, node_name)  # type: ignore

            node_instance_uri = ttl_builder.add_node_instances(graph, instances_dict_tree, node_char_uri)

            # Link current vss_node to its instance uri, as if the instance uri is characteristic of this vss_node
            graph.add((node_uri, SammConcepts.CHARACTERISTIC_RELATION.uri, node_instance_uri))

        else:
            # Link the characteristic uri to current vss_node's node_uri as usual
            graph.add((node_uri, SammConcepts.CHARACTERISTIC_RELATION.uri, node_char_uri))

        handle_branch_node(path_to_ttl, graph, vss_node, split_vss, node_uri, node_char_uri)

    if vss_node.is_leaf:
        ttl_builder.add_node_leaf(graph, node_uri, vss_node)

    return node_uri


def handle_branch_node(
    path_to_ttl: Path, graph: Graph, vss_node: VSSNode, split_vss: bool, node_uri: URIRef, node_char_uri: URIRef
):
    log.debug("Handle branch node for VSSNode: '%s'", vss_node.name)

    # Create node Entity to this vss_node branch
    # NOTE: this will be like a Class representation of the current vss_node
    #       In order to keep consistent the naming of semantic nodes,
    #       we should append 'Entity' to the node's name, taken from its node_uri.
    node_name = get_node_name_from_vspec_uri(node_uri)

    # Node Entity name should be in camel case format with its first character in UPPER CASE
    node_entity_name = str_to_uc_first_camel_case(node_name + "Entity")
    node_entity_uri = URIRef(VSSConcepts.EMPTY.uri_string + node_entity_name)

    # Add the node entity to the graph
    graph.add((node_entity_uri, RDF.type, SammConcepts.ENTITY.uri))

    # Add the node entity to its characteristic as data type
    graph.add((node_char_uri, SammConcepts.DATA_TYPE.uri, node_entity_uri))

    # Populate Entity properties if the current vss_node holds any child node
    properties_uris = []

    for child_node in vss_node.children:
        child_node_uri = None

        if split_vss and child_node.depth <= cfg.SPLIT_DEPTH and isinstance(child_node.data, VSSDataBranch):
            # Build VSS node into separate Aspect model
            # when --split option is provided
            # and depth of current VSSNode is within specified config SPLIT_DEPT level,
            # Default SPLIT_DEPT is 1, i.e. just 1st level branches like Vehicle.Cabin etc.
            child_node_uri = parse_vss_tree(path_to_ttl, child_node, True)

        else:
            # Each child should be a leaf node of its parent - i.e. NO ASPECTS and no split for child nodes
            child_node_uri = handle_vss_node(path_to_ttl, graph, child_node, False, False)

        if child_node_uri and child_node_uri != "DEPRECATED" and str(child_node_uri) != samm_output_namespace:
            # Each property should have payloadName = property name,
            # so to avoid the prefixed ttl_name when generating APIs and JSON payloads
            properties_uris.append((child_node_uri, ("payloadName", child_node.name)))

        elif child_node_uri != "DEPRECATED":
            log.warning(
                "Child node: '%s' does not have a valid URI: '%s' and is not added to '%s' node.\n",
                child_node.name,
                str(child_node_uri),
                vss_node.name,
            )

    # Add properties to current node_entity_uri
    if len(properties_uris) > 0:
        ttl_builder.add_node_properties(properties_uris, graph, node_entity_uri)

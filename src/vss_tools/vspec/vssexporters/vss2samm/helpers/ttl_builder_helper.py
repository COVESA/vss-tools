# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from typing import Sequence

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD
from vss_tools import log
from vss_tools.vspec.tree import VSSNode

from . import vss_helper as vss_helper
from .data_types_and_units import DataTypes
from .namespaces import Namespaces, get_node_name_from_vspec_uri, get_vspec_uri
from .samm_concepts import SammCConcepts, SammConcepts, VSSConcepts
from .string_helper import str_camel_case_split, str_to_lc_first_camel_case, str_to_uc_first_camel_case

#
# Builder helper, which provides a set of functions, to set up a TTL Graph,
# build various graph nodes like property, characteristic, entity etc. and add them to this graph,
# which then can be stored in an ESMF Aspect Model Editor loadable TTL file.
#


def __add_node_tuple(graph: Graph, subject_uri: URIRef, predicate_uri: URIRef, object_data: Literal | URIRef) -> bool:
    """
    Helper function to add a Node tuple to specified graph.<br>
    Will validate if the node is present and skip it to avoid duplicates or add is as usual.

    Args:
        graph (Graph): Graph to which node will be added
        subject_uri (URIRef): Subject - URIRef for the node to be created.
        predicate_uri (URIRef): Predicate RDF type for the node to create.
        object_data (Literal | URIRef): Object - contents of the node to create.

    Returns:
        bool: TRUE when node is added to graph and FALSE otherwise.
    """

    # Initialize the node - tuple
    # NOTE: a Tuple elements are: (Subject, Predicate, Object)
    node_tuple = (subject_uri, predicate_uri, object_data)

    # 2: validate if is present
    if graph.__contains__(node_tuple):
        log.debug(
            "A node with below properties already exists."
            "\n  -- subject uri: %s\n  -- predicate: %s\n  -- object data: %s\n",
            subject_uri,
            predicate_uri,
            object_data,
        )

        return False

    # 3: add the tuple to the graph
    else:
        graph.add(node_tuple)

        return True


# Initialize an empty RDF Graph with related bindings and ESMF - AME namespaces
def setup_graph():
    # Create a Graph
    graph = Graph()

    # Bind the namespaces to a prefix for more readable output
    graph.bind(VSSConcepts.EMPTY.value, VSSConcepts.EMPTY.uri)
    graph.bind("xsd", XSD)

    for nsKey in Namespaces:
        graph.bind(nsKey, URIRef(Namespaces[nsKey]))

    return graph


# Build an RDF Tree Node as property for the provided vss_node and add it to the specified graph.
def add_graph_node(graph: Graph, vss_node: VSSNode, is_aspect: bool) -> URIRef:
    node_property_name = vss_helper.get_node_property_name(vss_node)
    node_uri = get_vspec_uri(node_property_name)

    # Initialize the Property node - tuple
    if __add_node_tuple(graph, node_uri, RDF.type, SammConcepts.PROPERTY.uri) is False:
        # Node was already created, just return its URI
        return node_uri

    if is_aspect:
        add_node_aspect(graph, vss_node, node_uri)
    # ELSE: just build a simple property node as usual

    # Preferred name should be white space in front of each upper case letter
    # i.e. more human friendly / readable name
    # EXAMPLE:
    #     node.name     : IsStrongCrossWindDetected
    #     should be like: Is Strong Cross Wind Detected
    __add_node_tuple(
        graph, node_uri, SammConcepts.PREFERRED_NAME.uri, Literal(str_camel_case_split(vss_node.ttl_name), "en")
    )

    log.debug("Created graph node with URI: '%s'.\n", node_uri)

    return node_uri


def add_node_aspect(graph: Graph, vss_node: VSSNode, node_uri: URIRef):
    # Initialize Aspect for current Graph.
    log.debug("Add aspect node for node uri:\t  -- '%s'.", node_uri)

    # NOTE: there can be only 1 Aspect per graph. For Aspect nodes, vss_node.ttl_name is same as vss_node.name
    # Aspect Name must be UC FIRST CAMEL CASE
    aspect_node_uri = get_vspec_uri(str_to_uc_first_camel_case(vss_node.ttl_name))

    if __add_node_tuple(graph, aspect_node_uri, RDF.type, SammConcepts.ASPECT.uri) is True:
        # Aspect added => complete its creation
        __add_node_tuple(
            graph, aspect_node_uri, SammConcepts.PREFERRED_NAME.uri, Literal(str_camel_case_split(vss_node.name), "en")
        )

        # Add the property instance of this Tree node to its Aspect
        __add_node_tuple(
            graph,
            aspect_node_uri,
            SammConcepts.PROPERTIES.uri,
            Literal(f"( {get_property_uri_from_node_uri(node_uri)} )"),
        )

        # Add placeholders for Aspect operations and events
        __add_node_tuple(graph, aspect_node_uri, SammConcepts.OPERATIONS.uri, Literal("()"))
        __add_node_tuple(graph, aspect_node_uri, SammConcepts.EVENTS.uri, Literal("()"))

    # ELSE: do nothing since aspect node has already been created


def add_node_branch_characteristic(graph: Graph, vss_node: VSSNode, node_uri: URIRef):
    # NOTE: constraints are usually on a leaf node
    #       and will result in Node having a Trait with BaseCharacteristic and Constraint nodes.
    node_char_name = get_node_characteristic_name(node_uri, vss_helper.has_constraints(vss_node))
    node_char_uri = get_vspec_uri(node_char_name)

    log.debug("Add branch characteristic: '%s' for VSSNode: '%s'.", node_char_name, vss_node.name)

    if __add_node_tuple(graph, node_char_uri, RDF.type, SammConcepts.CHARACTERISTIC.uri) is False:
        # Characteristic was already added => just return its URI
        return node_char_uri

    # ELSE: complete creation of node characteristic

    __add_node_tuple(graph, node_char_uri, SammConcepts.NAME.uri, Literal(node_char_name))

    # Add description to this node's characteristic
    # NOTE: Keep description under this vss_node's branch - node_char_uri,
    #       because if there is any instances,
    #       each of its instance(s) will point to node_char_uri
    __add_node_tuple(
        graph, node_char_uri, SammConcepts.DESCRIPTION.uri, Literal(vss_helper.get_node_description(vss_node), "en")
    )

    return node_char_uri


def add_node_leaf(graph: Graph, node_uri: URIRef, vss_node: VSSNode):
    log.debug(
        "Add node for VSS Node: '%s'\n  -- of type: '%s'\n  -- with path: '%s'",
        vss_node.name,
        vss_node.data.type,  # type: ignore
        vss_node.get_fqn(),
    )

    has_limits = vss_helper.has_constraints(vss_node)

    node_char_name = get_node_characteristic_name(node_uri, has_limits)
    node_char_uri = get_vspec_uri(node_char_name)

    # Bind current vss_node to its characteristic
    if __add_node_tuple(graph, node_uri, SammConcepts.CHARACTERISTIC_RELATION.uri, node_char_uri) is True:
        # Complete creation of leaf node
        if has_limits:
            node_char_uri = add_node_leaf_constraint(graph, node_char_name, node_char_uri, vss_node)

        # Add description to this node's characteristic
        # NOTE: this could be the general characteristic or trait, in case if vss_node has limits
        __add_node_tuple(
            graph, node_char_uri, SammConcepts.DESCRIPTION.uri, Literal(vss_helper.get_node_description(vss_node), "en")
        )

        # Get RDF and Data types for specified node_characteristic_uri from its related vss_node
        rdf_type = vss_helper.get_node_rdf_type(vss_node)
        data_type = vss_helper.get_data_type(vss_node)

        match rdf_type:
            case SammCConcepts.ENUM | SammCConcepts.STATE:
                # Handle ENUM type nodes
                log.debug("  -- set node ENUM values")

                if vss_node.data.default:  # type: ignore
                    __add_node_tuple(
                        graph,
                        node_char_uri,
                        SammCConcepts.DEFAULT_VALUE.uri,
                        Literal(vss_node.data.default, datatype=data_type),  # type: ignore
                    )

                # Read values for this vss_node's characteristic
                enum_values = None
                if hasattr(vss_node.data, "allowed") and vss_node.data.allowed and type(vss_node.data.allowed) is list:
                    # Add allowed values to this node characteristic
                    enum_values = get_enum_values(vss_node.data.allowed)
                elif hasattr(vss_node.data, "enum") and vss_node.data.enum:
                    # NOTE: From VSS 3.0 the 'enum' attribute has been renamed to `allowed`
                    #       However, we will keep this for backwards compatibility.

                    # Add ENUM values, as usual, to this node characteristic
                    enum_values = get_enum_values(vss_node.data.enum)  # type: ignore

                if enum_values is not None:
                    __add_node_tuple(graph, node_char_uri, SammCConcepts.VALUES.uri, enum_values)

            case SammCConcepts.LIST:
                # Handle LIST type nodes
                log.debug("  -- set node List values")

                # TODO: do we need to add values here?

            case SammCConcepts.MEASUREMENT:
                # Handle MEASUREMENT (unit) type nodes
                log.debug("  -- set node Measurement values")

                if hasattr(vss_node.data, "unit") and vss_node.data.unit:
                    __add_node_tuple(
                        graph, node_char_uri, SammCConcepts.UNIT.uri, vss_helper.get_data_unit_uri(vss_node.data.unit)
                    )

                else:
                    log.warning(
                        "Unit is not set for vss node: '%s' with type: '%s'\n"
                        "Setting node 'RDF.type' from MEASUREMENT to default: CHARACTERISTIC\n",
                        vss_node.name,
                        vss_node.data.datatype,  # type: ignore
                    )

                    rdf_type = SammConcepts.CHARACTERISTIC

                if hasattr(vss_node.data, "default") and vss_node.data.default:
                    __add_node_tuple(
                        graph,
                        node_uri,
                        SammConcepts.EXAMPLE_VALUE.uri,
                        Literal(vss_node.data.default, datatype=data_type),
                    )

            case SammConcepts.CHARACTERISTIC:
                # Handle CHARACTERISTIC type nodes
                log.debug(" -- set regular node values")

                if hasattr(vss_node.data, "default") and vss_node.data.default:
                    if (
                        hasattr(vss_node.data, "unit")
                        and vss_node.data.unit
                        and vss_node.data.unit == "iso8601"
                        and data_type == DataTypes[vss_node.data.unit]
                    ):
                        # Handle date-time based nodes
                        log.debug(" -- set node DATE-TIME values")

                        # NOTE: Some examples are provided in the form: 0000-01-01T00:00Z
                        #       which FAILS ON THE ESMF AME VALIDATION because of the 0000 year.
                        #       Correct format in ESMF AME is:
                        #           yyyy-mm-ddThh:mmZ
                        #       OR
                        #           yyyy-mm-ddThh:mm:ss.milliseconds+hh:mm, where +hh:mm is the timezone
                        #
                        #       Example: '2000-01-01T14:23:00',
                        #                '0001-01-01T00:00:00.00000+00:00',
                        #                '2023-11-27T16:26:05.671Z'
                        if not vss_node.data.default.startswith("0000"):
                            # Add property node exampleValue date time - TIMESTAMP, if is provided and valid
                            __add_node_tuple(
                                graph,
                                node_uri,
                                SammConcepts.EXAMPLE_VALUE.uri,
                                Literal(vss_node.data.default, datatype=data_type),
                            )
                        else:
                            log.warning(
                                "Skipping incorrect date time default value: '%s' for VSS Node: '%s'\n"
                                "CORRECT format + timezone is:\n"
                                "    yyyy-mm-ddThh:mmZ\n"
                                "or\n"
                                "    yyyy-mm-ddThh:mm:ss.milliseconds+hh:mm\n"
                                "where yyyy cannot be just 0000, i.e. 0001 is valid year, but 0000 is not valid.\n",
                                vss_node.data.default,
                                vss_node.name,
                            )

                    else:
                        # Add default ONLY for other than date-time nodes.
                        # DateTime nodes default is handled above.
                        __add_node_tuple(
                            graph,
                            node_uri,
                            SammConcepts.EXAMPLE_VALUE.uri,
                            Literal(vss_node.data.default, datatype=data_type),  # type: ignore
                        )

            case _:
                # DEFAULT
                log.warning(
                    "Could not match Characteristic type: '%s' for vss_node: '%s'\n",
                    rdf_type,
                    vss_node.get_fqn(),
                )

        # Set RDF.type for current leaf node characteristic
        __add_node_tuple(graph, node_char_uri, RDF.type, rdf_type.uri)

        # Set data_type for current vss_node's characteristic
        __add_node_tuple(graph, node_char_uri, SammConcepts.DATA_TYPE.uri, data_type)

    # ELSE: do nothing since leaf node has already been created


def add_node_leaf_constraint(graph: Graph, node_char_name: str, node_char_uri: URIRef, vss_node: VSSNode):
    log.debug("Add leaf-node constraint")

    constraint_name = str_to_uc_first_camel_case(vss_node.ttl_name + "Constraint")
    constraint_node_uri = get_vspec_uri(constraint_name)

    __add_node_tuple(graph, constraint_node_uri, RDF.type, SammCConcepts.RANGE_CONSTRAINT.uri)
    __add_node_tuple(graph, constraint_node_uri, SammConcepts.NAME.uri, Literal(constraint_name))

    # Workaround since doubles are serialized as scientific numbers
    data_type = vss_helper.get_data_type(vss_node)
    if data_type == XSD.double:
        data_type = XSD.anyURI

    if vss_node.data.max is not None:  # type: ignore
        __add_node_tuple(
            graph,
            constraint_node_uri,
            SammCConcepts.MAX_VALUE.uri,
            Literal(vss_node.data.max, datatype=data_type),  # type: ignore
        )

    if vss_node.data.min is not None:  # type: ignore
        __add_node_tuple(
            graph,
            constraint_node_uri,
            SammCConcepts.MIN_VALUE.uri,
            Literal(vss_node.data.min, datatype=data_type),  # type: ignore
        )

    base_c_name = str_to_uc_first_camel_case(vss_node.ttl_name + "BaseCharacteristic")
    base_c_uri = get_vspec_uri(base_c_name)

    __add_node_tuple(graph, node_char_uri, SammCConcepts.BASE_CHARACTERISTICS.uri, base_c_uri)
    __add_node_tuple(graph, node_char_uri, RDF.type, SammCConcepts.TRAIT.uri)
    __add_node_tuple(graph, node_char_uri, SammConcepts.NAME.uri, Literal(node_char_name))
    __add_node_tuple(graph, node_char_uri, SammCConcepts.CONSTRAINT.uri, constraint_node_uri)

    return base_c_uri


# Accepts list of:
#  URIRef(s) - URIRef of the property node to be added to specified vss_node_uri
#
# or tuples in the form:
#       ( URIRef, ( "optional", True ), ( "payloadName", "givenName" ) )
# where:
#   - URIRef - is the URIRef of the property node to be added to specified vss_node_uri
#   - other, OPTIONAL, tuples are for property attributes: optional and payloadName
def add_node_properties(vss_nodes_uris: Sequence[URIRef | tuple], graph: Graph, vss_node_uri: URIRef):
    log.debug("Prepare properties from vss nodes URIs:\n%s\n", vss_nodes_uris)

    node_props = ""

    for node_uri in vss_nodes_uris:
        if node_uri:
            property_prefix = " " if node_props else ""

            if type(node_uri) is tuple:
                # Handle node_uri with some additional parameters
                # EXAMPLE tuple:
                #   ( NodeURI, ( "optional", True ), ( "payloadName", "givenName" ) )
                # will result in:
                #   [ samm:property :prop1; samm:optional true; samm:payloadName "givenName"; ]
                property_name = ""
                is_optional = False  # type: ignore
                payload_name = ""

                for entry in node_uri:
                    if type(entry) is URIRef:
                        property_name = get_property_uri_from_node_uri(entry)

                    elif type(entry) is tuple:
                        if entry[0] == "optional":
                            is_optional = entry[1] is True

                        elif entry[0] == "payloadName":
                            # Make sure that payload name starts with lower case
                            payload_name = str_to_lc_first_camel_case(entry[1])

                        else:
                            log.warning(
                                "Node uri tuple: '%s'\n is not in correct format: (attrName, attrValue) "
                                "or is not supported for a property attribute.\n",
                                entry,
                            )

                    else:
                        log.warning(
                            "Node uri tuple: '%s'\n is not in correct format: URIRef OR tuple(attrName, attrValue)\n",
                            entry,
                        )

                if property_name:
                    property_name = f"{SammConcepts.PROPERTY.samm_name} {property_name}"
                    is_optional = f"; {SammConcepts.OPTIONAL.samm_name} true" if is_optional else ""  # type: ignore

                    if payload_name:
                        payload_name = f'; {SammConcepts.PAYLOAD_NAME.samm_name} "{payload_name}"'
                    else:
                        payload_name = ""

                    if is_optional or payload_name:
                        property = f"[ {property_name}{is_optional}{payload_name} ]"
                    else:
                        property = property_name

                    node_props += property_prefix + property

            elif type(node_uri) is URIRef:
                node_props += property_prefix + get_property_uri_from_node_uri(node_uri)

            else:
                log.warning("Not supported type: '%s' for Node URI: '%s'.", type(node_uri), node_uri)

    # Remove trailing white space and set node_props in the form: ( ... )
    node_props = "( {} )".format(node_props.strip())

    log.debug("Add properties URIs to vss node URI: '%s'\n  -- properties:\n%s\n", vss_node_uri, node_props)

    # Add properties to the specified vss_node_uri
    __add_node_tuple(graph, vss_node_uri, SammConcepts.PROPERTIES.uri, Literal(node_props))


def get_property_uri_from_node_uri(vss_node_uri: URIRef):
    return f":{str_to_lc_first_camel_case(vss_node_uri.replace(VSSConcepts.EMPTY.uri, ''))}"


def get_node_characteristic_name(node_uri: URIRef, has_limits: bool):
    # Node characteristic name is based on the node property URI, and should be in the form:
    # NodePropertyNameCharacteristic or NodePropertyNameTrait, in case if the node has some constraints
    node_name = get_node_name_from_vspec_uri(node_uri)
    characteristic_name_suffix = "Trait" if has_limits else "Characteristic"

    return str_to_uc_first_camel_case(node_name + characteristic_name_suffix)


# Helper function to convert a list of strings into TTL formatted ENUM VALUES list
# in the form: ( "value1" "value2" ... "value#" )
# TODO-NOTE: the collection_to_process is provided from VSSNode.allowed, which is currently defined as str.
#            However, ALL allowed definitions in VSS are set as list of strings.
#            For example check VSS::FuelSystem::SupportedFuelTypes::allowed field.
#
#            We might need to further refactor the VssNote.allowed field so it has the correct type: list[str]
#
#            For the moment, we define the collection_to_process as: list[str] | str, so to pass the mypy check.
def get_enum_values(collection_to_process: list[str] | str):
    enum_values = ""

    for value in collection_to_process:
        if type(value) is str:
            enum_values += '"' + value + '" '
        else:
            enum_values += value + " "

    return Literal(f"( {enum_values.strip()} )")


def add_node_instances(graph: Graph, instances_dict_tree: dict, node_char_uri: URIRef):
    instance_char_uri = None

    if instances_dict_tree:
        log.debug("Build nodes from instances dict tree: '%s'", instances_dict_tree["name"])

        # Build Node Instance as characteristic which then will be added to the corresponding node_uri
        node_instance_name = str_to_uc_first_camel_case(instances_dict_tree["name"] + "Instance")
        instance_char_uri, instance_entity_uri = add_node_instance_characteristic_with_entity(graph, node_instance_name)

        instance_entity_properties = []
        skip_siblings_child_nodes = False

        # Populate the node_instance tree graph
        for instance in instances_dict_tree["children"]:
            log.debug(
                "Build ttl node for instance: '%s'\n  -- type: '%s'\n  -- path: '%s'",
                instance["name"],
                instance["type"],
                instance["path"],
            )

            if type(instance) is dict and instance["type"] == "branch":
                log.debug("Build instance path: '%s' as branch node", instance["path"])

                # To make sure we have unique nodes, we use the instance path, similar to VSSNode ttl_name
                ni_path_name = instance["path"].replace(".", "")
                ni_char_name = str_to_uc_first_camel_case(ni_path_name)

                ni_prop_uri = ""
                ni_type_name = ""

                if instance["instance_type"]:
                    # This instance is from a specific type.
                    # For example: instances Row1, Row2, ..., Row# will have an instance_type: Row
                    #
                    # Such instances should share a common characteristic,
                    # i.e. if the instance is DoorRow1, then its characteristic should be: DoorRow,
                    # which later will be shared with all other DoorRow# instances as their shared Characteristic

                    # Instance Type should be prefixed by its parent name to make it more unique, similar to ttl_name
                    ni_type_name = "{}{}".format(instance["parent"]["name"], instance["instance_type"])
                    type_char_name = str_to_uc_first_camel_case(ni_type_name)
                    type_char_uri, type_entity_uri = add_node_instance_characteristic_with_entity(graph, type_char_name)

                    # In this case, the created type_entity will represent a common node for each instance of that type.
                    # Idea is that we can share common type node like characteristic for instances of the same type.
                    ni_entity_uri = type_entity_uri

                    ni_prop_uri = add_node_instance_property(graph, ni_path_name, type_char_uri)

                else:
                    # If the current instance does not have instance_type, just build it as usual
                    ni_char_uri, ni_entity_uri = add_node_instance_characteristic_with_entity(graph, ni_char_name)
                    ni_prop_uri = add_node_instance_property(graph, ni_path_name, ni_char_uri)

                    # Make sure to turn of skip_siblings_child_nodes,
                    # to handle properly children of the current instance
                    skip_siblings_child_nodes = False

                # Add created instance node uri to its entity properties.
                # NOTE: All instance child nodes should be optional
                instance_entity_properties.append((ni_prop_uri, ("optional", True), ("payloadName", instance["name"])))

                if not skip_siblings_child_nodes:
                    # Build instance - entity properties (children) nodes of current instance
                    add_instance_entity_properties(
                        graph, instance["children"], ni_type_name, node_char_uri, ni_entity_uri
                    )

                    if ni_type_name:
                        # Set flag to skip adding properties for instance_typed nodes.
                        # This is to avoid adding of duplicate properties
                        # of instances of same type to their main - type node
                        skip_siblings_child_nodes = True

            elif type(instance) is dict and instance["type"] == "attribute":
                # Attribute instance is like a VSSNode leaf node
                log.debug("Build instance path: '%s' as leaf node.", instance["path"])

                leaf_path_name = instance["path"].replace(".", "")
                leaf_uri = add_node_instance_property(graph, leaf_path_name, node_char_uri)

                instance_entity_properties.append((leaf_uri, ("optional", True), ("payloadName", instance["name"])))

            else:
                log.warning("Instance: '%s' with type: '%s' cannot be processed yet.\n", instance, type(instance))

        add_node_properties(instance_entity_properties, graph, instance_entity_uri)

    return instance_char_uri


# Helper function to support handling of creation of instance nodes for a VSSNode
def add_node_instance_characteristic_with_entity(graph: Graph, node_name: str):
    # NOTE: Node instance characteristic should be of type:
    #       SammCConcepts.SINGLE_ENTITY instead of SammConcepts.CHARACTERISTIC

    # Append the characteristic class (type) to its name uri
    node_char_uri = get_vspec_uri("{}{}".format(node_name, SammCConcepts.SINGLE_ENTITY.vsso_name))

    node_entity_name = str_to_uc_first_camel_case(node_name + "Entity")
    node_entity_uri = get_vspec_uri(node_entity_name)

    if __add_node_tuple(graph, node_char_uri, RDF.type, SammCConcepts.SINGLE_ENTITY.uri) is False:
        # This characteristic is already present, just return its URI and
        return node_char_uri, node_entity_uri

    # ELSE: continue with node creation as usual

    __add_node_tuple(graph, node_char_uri, SammConcepts.NAME.uri, Literal(node_name))
    __add_node_tuple(
        graph, node_char_uri, SammConcepts.PREFERRED_NAME.uri, Literal(str_camel_case_split(node_name), "en")
    )

    # Add the node entity to the graph
    __add_node_tuple(graph, node_entity_uri, RDF.type, SammConcepts.ENTITY.uri)

    # Add the node entity to its characteristic as data type
    __add_node_tuple(graph, node_char_uri, SammConcepts.DATA_TYPE.uri, node_entity_uri)

    return node_char_uri, node_entity_uri


def add_node_instance_property(graph: Graph, instance_name: str, instance_char_uri: URIRef):
    property_name = str_to_lc_first_camel_case(instance_name)
    property_uri = get_vspec_uri(property_name)

    if __add_node_tuple(graph, property_uri, RDF.type, SammConcepts.PROPERTY.uri) is False:
        log.warning("Return: '%s'.\n", property_uri)

        return property_uri

    __add_node_tuple(
        graph, property_uri, SammConcepts.PREFERRED_NAME.uri, Literal(str_camel_case_split(instance_name), "en")
    )

    # Bind this instance node to the provided instance_char_uri
    __add_node_tuple(graph, property_uri, SammConcepts.CHARACTERISTIC_RELATION.uri, instance_char_uri)

    return property_uri


def add_instance_entity_properties(
    graph: Graph, instance_children: list[dict], instance_type: str, characteristic_uri: URIRef, entity_uri: URIRef
):
    if instance_children and len(instance_children) > 0:
        entity_properties = []

        for child_instance in instance_children:
            child_path_name = ""
            if instance_type:
                # Use parent instance type + name for a child name
                child_path_name = "{}{}".format(instance_type, child_instance["name"])
            else:
                # Use usual child path for its name, similar to VSSNode ttl_name
                child_path_name = child_instance["path"].replace(".", "")

            # Add node instance as property node with characteristic of its main - parent VSSNode
            # NOTE: at this point each instance property node will be linked to the VSS defined node (characteristic)
            # FOR EXAMPLE: Door.Row1.DriverSide instance will have a DoorCharacteristic node as defined in VSS.
            child_uri = add_node_instance_property(graph, child_path_name, characteristic_uri)

            # Instance child properties should be optional and with payloadName without its parent prefix.
            # For more details check function: add_node_properties
            entity_properties.append((child_uri, ("optional", True), ("payloadName", child_instance["name"])))

        # Add child properties nodes to this instance's entity node
        add_node_properties(entity_properties, graph, entity_uri)

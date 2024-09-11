# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import re
from ast import literal_eval
from typing import Any

from rdflib import URIRef
from vss_tools import log
from vss_tools.vspec.datatypes import Datatypes
from vss_tools.vspec.model import NodeType, VSSDataBranch
from vss_tools.vspec.tree import VSSNode

from ..config import config as cfg
from .data_types_and_units import DataTypes, DataUnits
from .samm_concepts import SammCConcepts, SammConcepts
from .string_helper import str_to_lc_first_camel_case, str_to_uc_first_camel_case

#
# Helper script.
# Provides set of functions to work with VSSNodes.
#


# A DICT collection of key => value entries, where:
#   :key   - vss_node.name of a node from provided VSSNote (tree) for parsing.
#   :value - object of type: { counter: int, vss_paths: [str]}
#            where:
#                  - counter   - holds number of occurrences of the corresponding :key in the main VSSNode
#                  - vss_paths - array of qualified VSS path, for each node which name is matching the current :key
#
# This collection will be populated on the very first call of parse_vss_tree
# so to have a full overview of available VSS nodes' names, if there is any duplicated ones etc.
# Then it will be used to defined whether the corresponding vss_node should be prefixed with its parent name or not,
# as implemented in the should_use_parent_prefix function.
top_vss_tree_unique_node_names: dict[str, Any] = {}


def count_vss_tree_unique_node_names(vss_node: VSSNode) -> None:
    if type(top_vss_tree_unique_node_names) is dict and len(top_vss_tree_unique_node_names.keys()) == 0:
        # THIS SHOULD BE DONE ONLY ONCE,
        # i.e. when we parse the top level tree and we have not yet read all of its nodes
        populate_unique_node_names(top_vss_tree_unique_node_names, vss_node)


# Traverse through each node of provided vss_node tree and record unique node names,
# their number of occurrences and vss_paths for their duplicates if there is any.
# For more details, check comment for: top_vss_tree_unique_node_names field on lines: 33-44.
def populate_unique_node_names(node_names_dict: dict[str, Any], vss_node: VSSNode) -> None:
    if not node_names_dict.get(vss_node.name):
        # ADD vss_node to node_names_dict
        node_names_dict.__setitem__(vss_node.name, {"counter": 1, "vss_paths": [vss_node.get_fqn()]})
    else:
        # UPDATE vss_node counters in the node_names_dict
        node_names_dict[vss_node.name]["counter"] += 1  # type: ignore
        node_names_dict[vss_node.name]["vss_paths"].append(vss_node.get_fqn())  # type: ignore

    # Process vss_node children
    if vss_node.children and len(vss_node.children) > 0:
        for vss_child_node in vss_node.children:
            populate_unique_node_names(node_names_dict, vss_child_node)


def get_parent_prefix_for_ttl_name(vss_node: VSSNode, ttl_name: str, use_vehicle_prefix=False) -> str:
    parent_prefix = ""

    if vss_node.parent and (vss_node.parent.name != "Vehicle" or use_vehicle_prefix):
        # There is a special case.
        # EXAMPLE: Issuer signal, which parent is: Identifier
        # and it appears in two separate branches:
        #   Vehicle.Cabin.Seat.Occupant.Identifier.Issuer
        # and
        #   Vehicle.Driver.Identifier.Issuer
        #
        # In this case we need to take current vss_node parent ttl_name, instead of just its name,
        # so this will make the current vss_node ttl_name unique enough,
        # in order it can be loaded across different models.
        #
        # This is specially, when a user is using the split option
        if (
            vss_node.parent.name != vss_node.parent.ttl_name
            and top_vss_tree_unique_node_names[vss_node.name]["counter"] > 0
            and sum(
                vss_node.parent.name in vss_path
                for vss_path in top_vss_tree_unique_node_names[vss_node.name]["vss_paths"]
            )
            > 1
        ):
            parent_prefix = vss_node.parent.ttl_name

        else:
            parent_prefix = vss_node.parent.name

        if ttl_name.startswith(parent_prefix):
            return get_parent_prefix_for_ttl_name(vss_node.parent, ttl_name, use_vehicle_prefix=True)

    return parent_prefix


# Set ttl_name for provided vss_node.
# BY DEFAULT: ttl_name will be set to the current vss_node.name.
#   vss_node           - the VSSNode to be updated
#   use_parent_prefix  - when provided, the vss_node.parent.name will be used as prefix to its vss_node.name,
#                        if the vss_node has a parent
#   overwrite_ttl_name - if specified and the provided vss_node, already has a ttl_name,
#                        it will be overwritten based on preserve_ttl_name
#   preserve_ttl_name  - if specified and the provided vss_node, already has a ttl_name,
#                        then its ttl_name will be preserved and will be prefixed with its parent name
def set_ttl_name(vss_node: VSSNode, use_parent_prefix: bool, overwrite_ttl_name=False, preserve_ttl_name=False) -> None:
    log.debug("Set ttl name for VSS Node: '%s'.", vss_node.name)

    if hasattr(vss_node, "ttl_name") is False:
        # Make sure that ttl_name - placeholder is set for current node
        vss_node.__setattr__("ttl_name", "")

    if vss_node.ttl_name and not overwrite_ttl_name:
        log.debug("  -- node ttl name: '%s' is already set.", vss_node.ttl_name)

    else:
        ttl_name = vss_node.ttl_name if vss_node.ttl_name and preserve_ttl_name else vss_node.name

        if use_parent_prefix:
            parent_prefix = get_parent_prefix_for_ttl_name(vss_node, ttl_name)
            vss_node.ttl_name = parent_prefix + ttl_name

        else:
            vss_node.ttl_name = ttl_name

        log.debug("  -- %s node ttl name: '%s'.", "updated" if overwrite_ttl_name else "added", vss_node.ttl_name)


# Helper function, to check whether to use parent prefix for a vss_node or not
def should_use_parent_prefix(vss_node: VSSNode) -> bool:
    if top_vss_tree_unique_node_names[vss_node.name]["counter"] > 1 or (
        vss_node.is_leaf
        and hasattr(vss_node.data, "datatype")
        and vss_node.data.datatype is Datatypes.BOOLEAN
        and (vss_node.name.lower().startswith("is"))
        and (vss_node.parent and vss_node.parent.name not in vss_node.name)
    ):
        # Use prefix when:
        #  1) the current vss_node.name occurs multiple time in the top level VSS tree
        # or
        #  2) for leaf nodes of type BOOLEAN,
        #     which name starts with 'Is' or 'is'
        #     and their parent name is not included within their own vss_node.name
        return True
    else:
        return False


# Helper function to check, whether specified vss_node is selected to be converted to a TTL model
def is_vss_node_selected_for_processing(selected_signals_paths: list[str], vss_node: VSSNode) -> bool:
    if not selected_signals_paths:
        return True

    # VSSNode get_fqn returns the VSS path in form: PARENT_NAME.PATH.TO.NODE.NODE_NAME
    vss_node_path = vss_node.get_fqn()
    node_is_selected = False

    # NOTE: if the expand_opt is used in vss2samm exporter,
    #       there will be required additional logic to make sure that "expanded" paths like:
    #
    #           Vehicle.Cabin.Door.Row1.DriverSide.Window.Position
    #
    #       would map to selected path:
    #
    #           Vehicle.Cabin.Door.Window.Position

    for selected_signal_path in selected_signals_paths:
        node_is_selected = selected_signal_path.startswith(vss_node_path) or vss_node_path.startswith(
            selected_signal_path
        )

        if node_is_selected:
            break

    return node_is_selected


# Traverse through provided vss_node, based on specified selected_paths
# and mark each Node which is NOT "selected" for removal from the provided vss_node
def filter_vss_tree_for_deletion(vss_node: VSSNode, selected_paths: list[str]) -> None:
    if vss_node is not None:
        if isinstance(vss_node.data, VSSDataBranch):
            # Filter branch node and its children
            for child_node in vss_node.children:
                filter_vss_tree_for_deletion(child_node, selected_paths)

            children_to_delete = len(list(filter(lambda n: n.get_vss_data().delete, vss_node.children)))

            if len(vss_node.children) == children_to_delete:
                # Mark this node for deletion since none of its children have been selected for processing
                vss_node.data.delete = True

            # TODO: if needed, add support for filtering of instances
            #       when vss_node.data.delete is False and len(vss_node.data.instances) > 0
        else:
            # Handle node as it is a leaf
            if not is_vss_node_selected_for_processing(selected_paths, vss_node):
                vss_node.data.delete = True  # type: ignore


def get_node_property_name(vss_node: VSSNode) -> str:
    # Property names are based on the vss_node.ttl_name => make sure it is set
    set_ttl_name(vss_node, should_use_parent_prefix(vss_node))

    # Graph - property names are in camel case format, where 1st character is in lower case
    return str_to_lc_first_camel_case(vss_node.ttl_name)  # type: ignore


# Helper function to build VSSnode description in the form:
# VSS path   : ...
# Description: ...
# Comment    : ...
# and return it for addition to a graph node for specified vss_node
def get_node_description(vss_node: VSSNode) -> str:
    # Set description for this vss_node.
    # Will include its: VSS path, Description, Comment and Unit if any of these is available.
    description = ""

    # Use spacer to align ":" in "VSS path:" with "Description:" and / or "Comment:"
    spacer = ""

    if (
        hasattr(vss_node.data, "description")
        and vss_node.data.description
        and len(vss_node.data.description.strip()) > 0
    ):
        if '"' in vss_node.data.description:
            # Escape double quotes within vss_node.description
            vss_node.data.description = vss_node.data.description.replace('"', f'{cfg.CUSTOM_ESCAPE_CHAR}"')

        # Set 3 spaces spacer, so to align 'VSS path:' with 'Description:'
        spacer = "    "
        description = f"\n\nDescription: {vss_node.data.description}"

    # NOTE: there is also a vss_node.comment field which also holds some details
    #       Add the vss_node.comment to its description
    if hasattr(vss_node.data, "comment") and vss_node.data.comment and len(vss_node.data.comment.strip()) > 0:
        if '"' in vss_node.data.comment:
            vss_node.data.comment = vss_node.data.comment.replace('"', f'{cfg.CUSTOM_ESCAPE_CHAR}"')

        # Use the 3 empty spaces spacer, when there is description,
        # otherwise set it to align 'VSS path:' with 'Comment:'
        spacer = spacer if description else " "

        # Align 'Comment:' with 'Description:' and 'VSS path:'
        description = f"{description}\n\nComment{'   ' if description else ''}: {vss_node.data.comment}"

    if hasattr(vss_node.data, "unit") and vss_node.data.unit and len(vss_node.data.unit.strip()) > 0:
        description = f"{description}\n\nUnit{'             ' if description else ''}: {vss_node.data.unit}"

    return f"\nVSS path{spacer}: {vss_node.get_fqn()}{description}"


def has_constraints(vss_node: VSSNode) -> bool:
    return (
        hasattr(vss_node.data, "type")
        and vss_node.data.type in [NodeType.ACTUATOR, NodeType.SENSOR]
        and (
            hasattr(vss_node.data, "max")
            and vss_node.data.max is not None
            or hasattr(vss_node.data, "min")
            and vss_node.data.min is not None
        )
    )


def get_instances_dict_tree(vss_node_instances: list | None, node_instance_name: str) -> dict[str, Any]:
    log.debug("Create instances node tree for node instance name: '%s'.", node_instance_name)

    parsed_instances = []

    if type(vss_node_instances) is list and len(vss_node_instances) > 0:
        for instance_key in range(len(vss_node_instances)):
            instance = vss_node_instances[instance_key]

            parsed_instance = parse_instance(instance)
            parsed_instances.append(parsed_instance)

    log.debug("  -- convert parsed_instances: \n%s\n     to a tree now...", parsed_instances)

    node_instance_dict: dict[str, Any] = get_instance_dict(node_instance_name, None, "")

    add_instance_to_dict_tree(node_instance_dict, parsed_instances, "")

    # TODO: maybe try to return a VSSNode(vss_node.name, vss_node_dict)
    #       IF so, this will require further rework on the whole instance node generation
    #       implemented in TTLBuilderHelper::add_node_instances
    return node_instance_dict


def parse_instance(instance_to_parse: str | Any) -> str | list[str] | Any:
    parsed_instance = None

    if type(instance_to_parse) is str and instance_to_parse.__contains__("[") and instance_to_parse.endswith("]"):
        # More likely, current instance is in the form: "Row[1,2]" or Row[1,4] or "SomeOtherName[x,y]"
        # Example: Row[1, 2] or Row[1, 4]
        parsed_instance = []

        # Take the name of this instance
        instance_parts = instance_to_parse.split("[")
        instance_name = instance_parts[0]
        instance_entries = literal_eval("[" + instance_parts[1])

        if (
            len(instance_entries) == 2
            and instance_entries[0] == 1
            and sum(float(entry).is_integer() for entry in instance_entries) == 2
        ):
            # Here instances are set as a range, starting with 1 up to some other number
            # EXAMPLE: Row[1,4] - i.e. rows from 1st to 4th or: Row1, Row2, Row3, Row4
            start = instance_entries[0]
            end = instance_entries[1]

            while start <= end:
                parsed_instance.append(f"{instance_name}{start}")
                start += 1

        else:
            for instance_entry in instance_entries:
                parsed_instance.append(f"{instance_name}{instance_entry}")
    else:
        parsed_instance = instance_to_parse  # type: ignore

    return parsed_instance


# Helper function, which builds an instance object dict for specified instance_name,
# which then can be added to an instances_dict_tree
def get_instance_dict(instance_name: str, parent_dict: dict | None, instance_type: str) -> dict[str, Any]:
    name = str_to_uc_first_camel_case(instance_name)

    # Default type is: attribute for a string. Branch is for instance with children
    instance = {
        "type": "attribute",
        "name": name,
        "children": None,
        "path": name,
        "description": "",
        "instance_type": instance_type,
        "parent": parent_dict,
    }

    return instance


def add_instance_to_dict_tree(parent_dict_tree: dict[str, Any], instance_to_add, instance_type: str) -> None:
    if type(instance_to_add) is str:
        # ADD instance to the provided parent_tree

        # Default type is: attribute for a string. Branch is for instance with children
        instance_dict = get_instance_dict(instance_to_add, parent_dict_tree, instance_type)

        if type(parent_dict_tree) is dict:
            # Make sure to set parent type to: branch
            parent_dict_tree["type"] = "branch"

            if not parent_dict_tree["children"]:
                # Make sure to initialize parent children
                parent_dict_tree["children"] = []

            # Add path up to this instance node
            instance_dict["path"] = f"{parent_dict_tree['path']}.{instance_dict['name']}"

            parent_dict_tree["children"].append(instance_dict)

        elif type(parent_dict_tree) is list:
            # TODO: can we ever get into this point!?!?!?!
            # Add path up to this instance node
            # instance["path"] = instance["name"]
            parent_dict_tree.append(instance_dict)  # type: ignore

        else:
            log.warning("Provided parent_tree: '%s' must be either a dict or list (array).\n", parent_dict_tree)

    elif type(instance_to_add) is list:
        # Handle instance_to_add as list of instances to be added to the parent_tree
        # Call this function recursively to add each instance entry to the provided parent_tree

        # Get instance entries type. If these are in the form: Name1, Name2, Name3 etc
        # then their type will be: Name, otherwise it will be None
        instance_type = get_instances_type_from_list(instance_to_add)

        if type(parent_dict_tree) is dict and parent_dict_tree["children"] and len(parent_dict_tree["children"]) > 0:
            # Add each entry in instance_to_add as a child of the parent_tree["children"]
            for inst_dict in parent_dict_tree["children"]:
                for entry in instance_to_add:
                    add_instance_to_dict_tree(inst_dict, entry, instance_type)

        else:
            # Add each entry in instance_to_add as sibling in current parent_tree
            for entry in instance_to_add:
                add_instance_to_dict_tree(parent_dict_tree, entry, instance_type)

    else:
        log.warning(
            "Provided instance_to_add: '%s' type: '%s' is not supported.\n", instance_to_add, type(instance_to_add)
        )


def get_instances_type_from_list(instances_list: list) -> str:
    instance_type = ""
    # Check if instance entries are of same type, based on their name prefix
    if sum(type(entry) is str for entry in instances_list) == len(instances_list):
        # Check if each entry has a common name
        for entry in instances_list:
            # Make sure to strip any numbers of the entry (instance_name)
            instance_name = re.sub(r"[0-9]", "", entry)
            if not instance_type:
                # Read instance_type from very first entry
                instance_type = instance_name

            elif instance_type != instance_name:
                instance_type = ""
                # Break the checks as there is at least 1 entry,
                # which is not in same format as the 1st one
                break

    return instance_type


def get_node_rdf_type(vss_node: VSSNode) -> SammConcepts | SammCConcepts:
    if hasattr(vss_node.data, "allowed") and vss_node.data.allowed and type(vss_node.data.allowed) is list:
        # NOTE: ENUM does not have defaultValue
        #       Instead defaultValue is part of STATE characteristic which inherits from ENUM
        return SammCConcepts.ENUM if not vss_node.data.default else SammCConcepts.STATE  # type: ignore

    elif hasattr(vss_node.data, "datatype") and vss_node.data.datatype and vss_node.data.datatype.endswith("[]"):
        return SammCConcepts.LIST

    elif (
        hasattr(vss_node.data, "type")
        and vss_node.data.type in [NodeType.ATTRIBUTE, NodeType.ACTUATOR, NodeType.SENSOR]
        and hasattr(vss_node.data, "unit")
        and vss_node.data.unit
        and vss_node.data.unit != "iso8601"
    ):
        # NOTE: DateTime vss_nodes should have an SammConcepts.CHARACTERISTIC data_type
        return SammCConcepts.MEASUREMENT

    elif hasattr(vss_node.data, "allowed") and vss_node.data.allowed and type(vss_node.data.allowed) is not list:
        log.warning(
            "VSSNode: '%s' with path: '%s',\nhas allowed data of type: '%s', which is not handled yet.\n"
            "Allowed data: '%s'.\n",
            vss_node.name,
            vss_node.get_fqn(),
            type(vss_node.allowed),
            vss_node.allowed,
        )

        # For unset / unmatched vss_node units - just leave its characteristic type to: Characteristic
        return SammConcepts.CHARACTERISTIC

    else:
        # Return vss_node RDF.type to be a general Characteristic
        return SammConcepts.CHARACTERISTIC


def get_data_type(vss_node: VSSNode) -> URIRef:
    if hasattr(vss_node.data, "unit") and vss_node.data.unit == "iso8601":
        # DateTime VSSNodes data_type should be based on their unit
        # instead of their datatype, which is more likely to be set as 'string'.
        return DataTypes[vss_node.data.unit]

    if not hasattr(vss_node.data, "datatype"):
        log.warning(
            "DataType field is missing in VSSNode: '%s'\nDEFAULTING it to: '%s'\n",
            vss_node.name,
            DataTypes["anyURI"],
        )

        return DataTypes["anyURI"]

    # Set data_type based on VssNode datatype as usual or default it to: anyURI
    data_type = vss_node.data.datatype if vss_node.data.datatype else "anyURI"

    # VssNode datatype has been set as array
    if data_type.endswith("[]"):
        # Read just the type of the array / list
        data_type = data_type[:-2]

    if DataTypes.get(data_type):
        return DataTypes[data_type]
    else:
        log.warning("DataType: '%s' not found\nDEFAULTING it to: '%s'\n", data_type, DataTypes["anyURI"])

        return DataTypes["anyURI"]


def get_data_unit_uri(unit: str):
    if DataUnits.get(unit):
        return DataUnits[unit]
    else:
        log.warning("No DataUnit found for unit: '%s'.\nDEFAULTING it to: '%s'\n", unit, DataUnits["blank"])

        return DataUnits["blank"]

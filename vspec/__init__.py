#
# (C) 2021 Robert Bosch GmbH
# (C) 2018 Volvo Cars
# (C) 2016 Jaguar Land Rover
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# VSpec file parser.
#

import yaml
import os
import uuid
import sys
import collections
import logging
from copy import deepcopy
from typing import List, Optional

from anytree import (Resolver, LevelOrderIter, PreOrderIter, RenderTree)  # type: ignore[import]

from .model.vsstree import VSSNode
from .model.exceptions import ImpossibleMergeException, IncompleteElementException
from .model.constants import VSSTreeType, Unit

nestable_types = set(["branch", "struct"])


class VSpecError(Exception):
    def __init__(self, *args, **kwargs):
        self.file_name = args[0]
        self.line_nr = args[1]
        self.message = args[2]
        Exception.__init__(self, *args, **kwargs)

    def __str__(self):
        return "{}: {}: {}".format(self.file_name, self.line_nr, self.message)


# Try to open a file name that can reside
# in any directory listed in incude_paths.
# If successful, read context and return file
#
def search_and_read(file_name, include_paths):
    # If absolute path, then ignore include paths
    if file_name[0] == '/':
        with open(file_name, "r") as fp:
            text = fp.read()
            fp.close()
            return os.path.dirname(file_name), text

    for directory in include_paths:
        try:
            path = "{}/{}".format(directory, file_name)
            with open(path, "r") as fp:
                text = fp.read()
                fp.close()
                return os.path.dirname(path), text
        except IOError:
            pass

    # We failed, raise last exception we ran into.
    raise VSpecError(file_name, 0, "File error")


def convert_yaml_to_list(raw_yaml):
    if isinstance(raw_yaml, list):
        return raw_yaml

    # Sort the dictionary according to line number.
    # The reason is that when the YAML file is loaded
    # the object order is not preserved in the created
    # dictionary
    raw_yaml = collections.OrderedDict(
        sorted(raw_yaml.items(), key=lambda x: x[1]['$line$']))
    lst = []
    for elem in raw_yaml:
        if isinstance(raw_yaml[elem], dict):
            raw_yaml[elem]['$name$'] = elem
            lst.append(raw_yaml[elem])

    return lst


def load_tree(
        file_name,
        include_paths,
        tree_type: VSSTreeType,
        break_on_name_style_violation=False,
        expand_inst=True,
        data_type_tree: Optional[VSSNode] = None):
    if expand_inst and tree_type == VSSTreeType.DATA_TYPE_TREE:
        logging.error("Instance expansion is not supported for VSS type tree.")
        sys.exit(-1)

    flat_model = load_flat_model(file_name, "", include_paths, tree_type)
    absolute_path_flat_model = create_absolute_paths(flat_model)
    deep_model = create_nested_model(absolute_path_flat_model, file_name)
    cleanup_deep_model(deep_model)
    dict_tree = deep_model["children"]
    tree = render_tree(
        dict_tree,
        tree_type,
        break_on_name_style_violation=break_on_name_style_violation)
    if expand_inst:
        expand_tree_instances(tree)
    return tree


def check_type_usage(tree: VSSNode, tree_type: VSSTreeType, type_tree: Optional[VSSNode] = None):
    """
    Check usages of types within the tree.
    This methods shall be called after overlays (or additional type files) have been merged.
    """
    if tree_type == VSSTreeType.DATA_TYPE_TREE:
        check_data_type_references(tree)
    elif tree_type == VSSTreeType.SIGNAL_TREE:
        check_data_type_references_across_trees(tree, type_tree)


def load_flat_model(file_name, prefix, include_paths, tree_type: VSSTreeType):
    # Hooks into YAML parser to add line numbers
    # and file name into each element
    def yaml_compose_node(parent, index):
        # the line number where the previous token has ended (plus empty lines)
        line = loader.line
        try:
            node = yaml.composer.Composer.compose_node(loader, parent, index)
        except yaml.scanner.ScannerError as e:
            raise VSpecError(file_name, line + 1, e)
        except yaml.parser.ParserError as e:
            raise VSpecError(file_name, line + 1, e)

        if node.value == '$include$':
            node.value = f'$include${load_flat_model.include_index}'
            load_flat_model.include_index = load_flat_model.include_index + 1

        # Avoid having root-level line numbers as non-dictionary entries
        if parent:
            node.__line__ = line + 1
            node.__file_name__ = file_name
        else:
            node.__line__ = None
            node.__file_name = None
        return node

    def yaml_construct_mapping(node, deep=True):
        mapping = yaml.constructor.Constructor.construct_mapping(
            loader, node, deep=deep)

        # Replace
        # { 'Vehicle.Speed': { 'datatype': 'boolean', 'type': 'sensor' }}
        # with
        # { '$name$': 'Vehicle.Speed', 'datatype': 'boolean', 'type': 'sensor' }

        for key, val in list(mapping.items()):
            if key[0] == '$':
                continue

            if val is None:
                mapping['$name$'] = key
                del mapping[key]
                break

        # Add line number and file name to element.
        if node.__line__ is not None:
            mapping['$line$'] = node.__line__
            mapping['$file_name$'] = node.__file_name__

        return mapping

    directory, text = search_and_read(file_name, include_paths)

    # Do a trial pasing of the file to find out if it is list- or
    # object-formatted.
    loader = yaml.Loader(text)
    loader.compose_node = yaml_compose_node  # type: ignore[assignment]

    loader.construct_mapping = yaml_construct_mapping  # type: ignore[assignment]
    test_yaml = loader.get_data()

    # Depending on if this is a list or an object, expand
    # the #include diretives differently
    #
    if isinstance(test_yaml, list):
        text = yamilify_includes(text, True)
    else:
        text = yamilify_includes(text, False)

    # Re-initialize loader with the new text hosting the
    # yamilified includes.
    loader = yaml.Loader(text)
    loader.compose_node = yaml_compose_node  # type: ignore[assignment]

    loader.construct_mapping = yaml_construct_mapping  # type: ignore[assignment]
    raw_yaml = loader.get_data()

    # Check for file with no objects.
    if not raw_yaml:
        return []

    raw_yaml = convert_yaml_to_list(raw_yaml)

    # Sanity check of loaded code
    check_yaml_usage(raw_yaml, file_name)

    # Recursively expand all include files.
    if directory not in include_paths:
        include_paths = [directory] + include_paths
    expanded_includes = expand_includes(
        raw_yaml, prefix, include_paths, tree_type)

    flat_model = cleanup_flat_entries(expanded_includes, tree_type)

    return flat_model


def cleanup_flat_entries(flat_model, tree_type: VSSTreeType):
    """
    # 1. Check that the declared type is part of the available types for the tree.
    # 2. Check that allowed values are provided as arrays.
    """
    available_types = tree_type.available_types()

    # Traverse the flat list of the parsed specification
    for elem in flat_model:
        # Is this an include element?
        if "type" not in elem:
            raise VSpecError(elem["$file_name$"], elem["$line$"], "No type specified!")

        # Check, with case sensitivity that we do have
        # a validated type.
        if not elem["type"] in available_types:
            raise VSpecError(elem["$file_name$"], elem["$line$"],
                             "Unknown type: {}".format(elem["type"]))

        if "allowed" in elem and not isinstance(elem["allowed"], list):
            raise VSpecError(elem["$file_name$"], elem["$line$"],
                             "Allowed values are not represented as array.")

    return flat_model


#
# Delete parser-specific elements
#
# Parser metadata is cleaned in two steps. An initial step just after vspec files are parsed.
# Then some data is removed but not all as it is used for error messages.
# That needs to be removed in a second step, just before exporting.
#
def cleanup_deep_model(deep_model):

    if "$line$" in deep_model:
        del deep_model["$line$"]

    if "$prefix$" in deep_model:
        del deep_model["$prefix$"]

    if "$name$" in deep_model:
        del deep_model['$name$']

    # children as of today exists only for branches and structs
    if "children" in deep_model:
        children = deep_model["children"]
        for child in deep_model["children"]:
            cleanup_deep_model(children[child])

    return None

#
# Meta data on extended attributes needs to be cleaned as part of the second cleaning step.
# as it is not included in first step.
#


def clean_metadata(node):

    if isinstance(node, VSSNode):
        clean_metadata(node.extended_attributes)
        for child in node.children:
            clean_metadata(child)
    elif isinstance(node, dict):
        for k in list(node.keys()):
            clean_metadata(node[k])
            if k in ["$file_name$", "$line$"]:
                del node[k]
    elif isinstance(node, list):
        for elem in node:
            clean_metadata(elem)


def verify_mandatory_attributes(node, abort_on_unknown_attribute: bool):
    """
    Verify that mandatory attributes are present.
    Need to be checked first after overlays (if any) have been applied, as attributes are not
    mandatory in individual files but only in the final tree
    """
    if isinstance(node, VSSNode):
        node.verify_attributes(abort_on_unknown_attribute)
        for child in node.children:
            verify_mandatory_attributes(child, abort_on_unknown_attribute)


#
# Verify that we are using correct YAML in the model
#
def check_yaml_usage(flat_model, file_name):
    for elem in flat_model:
        if isinstance(elem, list):
            raise VSpecError(
                file_name,
                0,
                "Element {} is not a list entry. (Did you forget a ':'?)".format(elem))

    # FIXME:
    # Add more usage checks, such as absence of nested models.
    # and mutually exclusive elements.


# Expand yaml include elements (inserted by yamilify_include())
#
def expand_includes(flat_model, prefix, include_paths, tree_type: VSSTreeType):
    # Build up a new spec model based on the old one, but
    # with expanded include directives.

    new_flat_model: List[VSSNode] = []

    # Traverse the flat list of the parsed specification
    for elem in flat_model:
        # Is this an include element?
        if elem['$name$'][0:9] == "$include$":
            include_prefix = elem.get("prefix", "")

            if include_prefix != "":
                prefix_found = False
                for dict_elem in new_flat_model:
                    if dict_elem["$name$"] == include_prefix:
                        prefix_found = True
                        break
                if not prefix_found:
                    # Printing line number does not make sense, as we work on a
                    # modified tree
                    logging.warning(
                        f"No branch matching prefix {include_prefix} for #include in {elem['$file_name$']}")

            # Append include prefix to our current prefix.
            # Make sure we do not start new prefix with a "."
            if prefix != "":
                if include_prefix != "":
                    include_prefix = "{}.{}".format(prefix, include_prefix)
                else:
                    include_prefix = prefix

            # Recursively load included file
            inc_elem = load_flat_model(
                elem["file"], include_prefix, include_paths, tree_type)

            # Add the loaded elements at the end of the new spec model
            new_flat_model.extend(inc_elem)
        else:
            # Add a prefix to the element
            elem["$prefix$"] = prefix
            # Add the existing elements at the end of the new spec model
            new_flat_model.append(elem)

    return new_flat_model


def expand_tree_instances(tree: VSSNode):
    tree_node: VSSNode

    def rollout_list(instance_entry):
        '''
        Converts "Prefix[1,n] to [Prefix1, Prefix2, ..., Prefixn]"
        '''
        prefix = ""
        if "[" in instance_entry:  # if so unroll
            unrolled_items = []
            prefix = instance_entry[:instance_entry.find("[")]
            start = instance_entry[instance_entry.find(
                "[") + 1:instance_entry.find(",")]
            end = instance_entry[instance_entry.find(
                ",") + 1:instance_entry.find("]")]
            for i in range(int(start), int(end) + 1):
                unrolled_items.append(f"{prefix}{i}")
        else:  # if not, add
            unrolled_items = instance_entry
        return unrolled_items, prefix

    def is_instance_branch(node, unrolled_instances, prefix):
        '''
        Check if node is a branch that has the same name as an instance for parent node
        '''
        for instance in unrolled_instances:
            if isinstance(instance, list):
                # This means the element of the instances is a list, e.g. it was
                # something like Row[1,4]
                for element in instance:
                    if element == node.name:
                        return True
            else:
                # in this case our instances have been a simple list of elements
                # (as opposed to a list of lists), e.g. ['Left', 'Right'], so we just compare by name
                if instance == node.name:
                    return True

        # Now we try to be smarter - check if it seems to be an instance by prefix, e.g. Pos3 and prefix is Pos
        # This is only for specifying instances outside specified range, e.g.
        # specifying Row5 while instance is specified as Row[1,4]
        if prefix != "" and prefix in node.name:
            number = node.name.split(prefix, 1)[1]
            return number.isnumeric()
        return False

    def create_instantiated_branch(branch_name, parent, nodes_to_expand):
        # Check if the branch we want to create as part of expansion (e.g.
        # Row1, Pos2, Left, ...) already exist
        old_node = None
        for child in parent.children:
            if child.name == branch_name:
                old_node = child
        instantiated_branch = VSSNode(
            branch_name,
            # autopep8: off
            {"type": "branch",
             "description": parent.description,
             "comment": parent.comment,
             "$file_name$": "Generated"
             },
            # autopep8: on
            VSSTreeType.SIGNAL_TREE.available_types(),
            parent)
        if old_node is not None:
            # If it exist we take the new one as default (to give e.g. default descriptions and comments)
            # Then merge anything from the old (expanded) instance above, to get e.g. updated comment
            # Finally remove the old node by removing parent
            instantiated_branch.merge(old_node)
            for child in old_node.children:
                child.parent = instantiated_branch
            old_node.parent = None

        # Deep copy needed so that we can change attributes/dict/children
        # independently
        for expand_node in deepcopy(nodes_to_expand):
            # Check if this branch/signal already exists in the instantiated
            # branch
            for existing_item in instantiated_branch.children:
                if expand_node.name == existing_item.name:
                    # A child with the same name already exists
                    # Typical use-case is that a single instance of this signal has been re-defined in an overlay
                    # Then data from the overlay (for example A.B.Row2.Column2.Sig)
                    # shall have precedence over the expanded instance
                    # This is handled by removing the old node from tree and
                    # instead merging it to the new node
                    existing_item.parent = None
                    expand_node.merge(existing_item)
                    break
            expand_node.parent = instantiated_branch
        return instantiated_branch

    # Checking each node for instances and expand them
    # The walking order makes sure, we do not need to recurse
    for tree_node in PreOrderIter(tree):
        if tree_node.has_instances():
            # print(f"This node has instances: {tree_node.qualified_name()}, they are *{tree_node.instances}*")

            # Instances can be  many things: A string Row[1,4] that is shorthand for a list,
            # a simple list of of strings  ['Left', 'Right'],
            # or a list of lists ['Row[1,4]', ['Left', 'Right']], which expresses
            # multidimensional instances, where the n'th entry will be expanded at the
            # n'th level under the current node, i.e. in the example above you expect
            # children branches Row1, Row2, Row3, Row4, where each of them has a "left"
            # and a "right" child.
            # See
            # https://covesa.github.io/vehicle_signal_specification/rule_set/instances/
            # for an explanation.
            # This is a bit painful

            unrolled_instances = []
            array_prefix = ""

            # Instances are a list in .vspec e.g. ["left", "right"]
            if isinstance(tree_node.instances, list):
                for instance_entry in tree_node.instances:
                    # check every entry whether it is shorthand for a list
                    # e.g. Prefix[1,3]
                    unrolled_items, tmpprefix = rollout_list(instance_entry)
                    if array_prefix == "":
                        # For "smart" comparison only use prefix from first
                        # level
                        array_prefix = tmpprefix
                    unrolled_instances.append(unrolled_items)

            # it is not a list, e.g. instance in vspec is just Sensor[1,10]
            else:
                unrolled_items, array_prefix = rollout_list(
                    tree_node.instances)
                unrolled_instances.append(unrolled_items)

            # When a node has instances we need to decide what to do with the children
            # The default behavior is to duplicate each child under each created instance,
            # but there are exceptions.
            #
            # The first exception is nodes marked in vspec to be excluded from instantiation
            # (instantiate: False)
            #
            # The other exception is nodes/branches that actually already are expanded.
            # This shall typically only occur when analyzing overlays, where you may find
            # a signal specified as e.g. Vehicle.Cabin.Door.Row2.Right.Window.Tint
            # which then shall not be copied for each instance of Door as it is valid only
            # for one of the instances

            nodes_to_stay = []  # < nodes excluded from instantiation
            nodes_to_expand = []  # < nodes shall use the instances as parent

            for child in tree_node.children:
                if is_instance_branch(child, unrolled_instances, array_prefix):
                    # Child is already an instance, for example Row2.Right.X
                    nodes_to_stay.append(child)
                elif child.is_instantiated():
                    # Child has an explicit or implicit "instantiate:true",
                    # this is the default
                    nodes_to_expand.append(child)
                else:
                    nodes_to_stay.append(child)

            tree_node.children = deepcopy(nodes_to_stay)

            # now iterate over instances
            for instance in unrolled_instances:
                if isinstance(instance, list):
                    # This means the element of the instances is a list, e.g. it was
                    # something like Row[1,4]
                    # In that case the expectation is, that further elements in the
                    # unrolled instances list will be expanded under it.
                    # We will only expand the first layer, and come back later, e.g.
                    # instances are ['Row[1,2]', 'Pos[1,3]']. In that case we will
                    # add Row1 and Row2 branches under the current node and duplicate
                    # the subtree, and we set instances property of the new "RowX"
                    # branches to 'Pos[1,3]'
                    # The PreOrderIter will pass the newly created "RowX" instances
                    # next so they will be expanded

                    for element in instance:
                        instantiated_branch = create_instantiated_branch(
                            element, tree_node, nodes_to_expand)

                        if len(unrolled_instances) > 1:
                            # We need to expand more (see above). PreOrderIter
                            # allows us to do this without recursing
                            instantiated_branch.instances = unrolled_instances[1:]
                    # break outer for loop,
                    break

                else:
                    # in this case our instances have been a simple list of elements
                    # (as opposed to a list of lists), e.g. ['Left', 'Right'], so we
                    # just add them all in parallel as childs of the current
                    # loop
                    create_instantiated_branch(
                        instance, tree_node, nodes_to_expand)

    # As instance expansions moves signals in the tree, we need to recreate
    # UUIDs
    create_tree_uuids(tree)


#
# Take the flat model created by _load() and merge all $prefix$ with its name
# I.e: $prefix$ = "Cabin.Doors.1"
#      name = "Window.Pos"
#      -> name = "Cabin.Doors.1.Window.Pos"
#
# $prefix$ is deleted
#
#
def create_absolute_paths(flat_model):
    for elem in flat_model:
        # Create a list of path components to the given element
        #
        # $prefix$='body.door.front.left' name='lock' ->
        # [ 'body', 'door', 'front', 'left', 'lock' ]
        name = elem['$name$']

        if elem["$prefix$"] == "":
            new_name = name
        else:
            new_name = "{}.{}".format(elem["$prefix$"], name)

        elem['$name$'] = new_name
        del elem["$prefix$"]

    return flat_model


#
# Take the flat model with absolute signal names parsed from the vspec
# file and create a nested variant where each component of a prefix
# becomes a branch.
#

def create_nested_model(flat_model, file_name):
    deep_model = {
        "children": {},
        "type": "branch",
        "$file_name$": file_name,
        "$line$": 0
    }

    # Traverse the flat list of the parsed specification
    for elem in flat_model:
        # Create children for branch type objects
        if elem["type"] in nestable_types:
            elem["children"] = {}

        # Create a list of path components to the given element
        #  name='body.door.front.left.lock' ->
        # [ 'body', 'door', 'front', 'left', 'lock' ]
        name_list = elem['$name$'].split(".")

        # Extract name
        name = name_list[-1]

        # Locate the correct branch in the tree
        parent_branch = find_branch_or_struct(deep_model, name_list[:-1], 0)

        # If an element with name is already in the parent branch
        # we update its fields with the fields from the new element
        if name in parent_branch["children"]:
            old_elem = parent_branch["children"][name]
            # never update the type
            elem.pop("type", None)
            # concatenate file names
            fname = "{}:{}".format(
                old_elem["$file_name$"], elem["$file_name$"])
            old_elem.update(elem)
            old_elem["$file_name$"] = fname
        else:
            parent_branch["children"][name] = elem

    return deep_model


# Find the given prefix somewhere under the tree rooted in elem.
# If the branch referred to by prefix is not found, create it implicitly
# if autocreate is True. Note that structs are not auto-created.
def find_branch_or_struct(elem, name_list, index, autocreate=True):
    # Have we reached the end of the name list
    if len(name_list) == index:
        if (elem['type'] not in nestable_types):
            raise VSpecError(
                elem.get(
                    "$file_name$", "??"), elem.get(
                    "$line$", "??"), "Not a branch or struct: {}.".format(
                    elem['$name$']))

        return elem

    if (elem['type'] not in nestable_types):
        raise VSpecError(elem.get("$file_name$", "??"),
                         elem.get("$line$", "??"),
                         "{} is not a branch or struct.".format(list_to_path(name_list[:index])))

    children = elem["children"]

    if name_list[index] not in children:
        if autocreate and elem['type'] != "struct":
            logging.info(f"Autocreating implicit branch {name_list[index]}")

            # If we are above Vehicle (e.g. vehicle not defined), we are
            # missing a name
            if "$name$" not in elem:
                elem['$name$'] = ""
            # autopep8: off
            newelem = {'type': elem['type'],
                       'children': {},
                       '$line$': '0',
                       '$file_name$':
                       '<generated>',
                       '$name$': f"{elem['$name$']}.{name_list[index]}"}
            # autopep8: on
            children[name_list[index]] = newelem
            # Search again
            find_branch_or_struct(elem, name_list, index, autocreate)
        else:
            raise VSpecError(
                elem.get(
                    "$file_name$", "??"), elem.get(
                    "$line$", "??"), "Missing branch: {} in {}.".format(
                    name_list[index], list_to_path(name_list)))

    # Traverse all children, looking for the
    # Move on to next element in prefix.
    return find_branch_or_struct(
        children[name_list[index]], name_list, index + 1, autocreate)


def list_to_path(name_list):
    path = ""
    for name in name_list:
        if path == "":
            path = name
        else:
            path = "{}.{}".format(path, name)

    return path


#
# Convert
#   #include door.vspec, body.door.front.left
# to
#   - $include$:
#     file: door.vspec
#     prefix: body.door.front.left
#
# This yaml version of the include directive will
# then be further processed to actually include
# the given file.
#
def yamilify_includes(text, is_list):

    # Logic below expects a new line after "#include", to support vspec files where there
    # is no newline at end we add a newline here
    text += '\n'

    while True:
        st_index = text.find("\n#include")
        if st_index == -1:
            return text

        end_index = text.find("\n", st_index + 1)
        if end_index == -1:
            return text

        include_arg = text[st_index + 10:end_index].split()
        if len(include_arg) == 2:
            [include_file, include_prefix] = include_arg
        else:
            include_prefix = '""'
            [include_file] = include_arg

        if is_list:
            fmt_str = """{}

- $name$: $include$
  file: {}
  prefix: {}
{}"""
        else:
            fmt_str = """{}

$include$:
  file: {}
  prefix: {}
{}"""

        text = fmt_str.format(
            text[:st_index], include_file, include_prefix, text[end_index:])

    return text


def render_tree(
        tree_dict,
        tree_type: VSSTreeType,
        break_on_name_style_violation=False) -> VSSNode:
    if len(tree_dict) != 1:
        for item in tree_dict.keys():
            logging.info(f"Found root node {item}")
        raise Exception(
            f"Invalid VSS model, must have single root node, found {len(tree_dict)}")

    root_element_name = next(iter(tree_dict.keys()))
    root_element = tree_dict[root_element_name]
    if root_element['type'] != 'branch':
        raise Exception(
            f"Invalid VSS model, root must be branch, found {root_element_name} of type {root_element['type']}")

    tree_root = VSSNode(
        root_element_name,
        root_element,
        tree_type.available_types(),
        break_on_name_style_violation=break_on_name_style_violation)

    if "children" in root_element.keys():
        child_nodes = root_element["children"]
        render_subtree(
            child_nodes,
            tree_type,
            tree_root,
            break_on_name_style_violation=break_on_name_style_violation)

    create_tree_uuids(tree_root)
    return tree_root


def render_subtree(
        subtree,
        tree_type: VSSTreeType,
        parent,
        break_on_name_style_violation=False):
    for element_name in subtree:
        current_element = subtree[element_name]

        try:
            new_element = VSSNode(
                element_name,
                current_element,
                tree_type.available_types(),
                parent=parent,
                break_on_name_style_violation=break_on_name_style_violation)
        except IncompleteElementException as e:
            logging.error(f"Invalid VSS: {e}")
            logging.error("Terminating.")
            sys.exit(-1)
        if "children" in current_element.keys():
            child_nodes = current_element["children"]
            render_subtree(
                child_nodes,
                tree_type,
                new_element,
                break_on_name_style_violation=break_on_name_style_violation)


def merge_elem(base, overlay_element):
    r = Resolver()
    element_name = "/" + overlay_element.qualified_name("/")

    if not VSSNode.node_exists(base, element_name):
        # The node in the overlay does not exist, so we connect it
        # print(f"Not exists {overlay_element.qualified_name()} does not exist, creating.")
        new_parent_name = "/" + overlay_element.parent.qualified_name("/")
        new_parent = r.get(base, new_parent_name)
        overlay_element.parent = new_parent

    else:
        # else we merge the node. The merge function of VSSNode is not recursive
        # so children in base will not be overwritten
        # print(f"Merging {overlay_element.qualified_name()}")
        other_node: VSSNode = r.get(base, element_name)
        try:
            other_node.merge(overlay_element)
        except ImpossibleMergeException as e:
            logging.error(f"Merging impossible: {e}")
            sys.exit(-1)


def merge_tree(base: VSSNode, overlay: VSSNode):
    overlay_element: VSSNode
    for overlay_element in LevelOrderIter(overlay):
        merge_elem(base, overlay_element)


def create_tree_uuids(root: VSSNode):
    VSS_NAMESPACE = "vehicle_signal_specification"
    namespace_uuid = uuid.uuid5(uuid.NAMESPACE_OID, VSS_NAMESPACE)
    vss_element: VSSNode
    for vss_element in PreOrderIter(root):
        vss_element.uuid = uuid.uuid5(
            namespace_uuid, vss_element.qualified_name()).hex


def load_units(vspec_file: str, unit_files: List[str]):

    total_nbr_units = 0
    if not unit_files:
        # Search for a file units.yaml in same directory as vspec file
        vspec_dir = os.path.dirname(os.path.realpath(vspec_file))
        default_vss_unit_file = vspec_dir + os.path.sep + 'units.yaml'
        if os.path.exists(default_vss_unit_file):
            total_nbr_units = Unit.load_config_file(default_vss_unit_file)
            logging.info(f"Added {total_nbr_units} units from {default_vss_unit_file}")
    else:
        for unit_file in unit_files:
            nbr_units = Unit.load_config_file(unit_file)
            if (nbr_units == 0):
                logging.warning(f"Warning: No units found in {unit_file}")
            else:
                logging.info(f"Added {nbr_units} units from {unit_file}")
                total_nbr_units += nbr_units

    if (total_nbr_units == 0):
        logging.error("No units defined! Terminating!")
        sys.exit(-1)


def check_data_type_references(tree: VSSNode):
    """
    Check that the data type names referenced by tree nodes exist in the tree.
    """
    errors: List[str] = []
    check_data_type_references_recursive(
        tree, [
            str(attr) for attr in VSSNode.get_tree_attrs(
                tree, lambda n: n.qualified_name(), lambda n: n.is_struct())], errors)
    if len(errors) > 0:
        error_str = ",".join(errors)
        logging.error(
            f"{len(errors)} data type reference errors detected. Errors: {error_str}")
        sys.exit(-1)


def check_data_type_references_recursive(
        node: VSSNode, data_type_qualified_names: List[str], errors: List[str]):
    """
    Check that the data type names referenced by tree nodes exist in the tree.
    """
    if node.is_property() or node.is_signal():
        if node.datatype is None:
            undecorated_data_type = node.data_type_str.replace('[]', '')
            if undecorated_data_type not in data_type_qualified_names:
                errors.append(
                    f"Data Type reference invalid. Node Name: {node.name}. "
                    f"Node Qualified Name: {node.qualified_name()}. "
                    f"Data Type: {undecorated_data_type}")

            separator = "."
            # is the property circularly refereing to the struct in which it is defined?
            member_of = separator.join(node.qualified_name(separator).split(separator)[:-1])
            if member_of == undecorated_data_type:
                errors.append(
                    "Circular reference detected in data type. "
                    f"Data Type: {member_of}. Property: {node.name}")

    for n in node.children:
        check_data_type_references_recursive(
            n, data_type_qualified_names, errors)


def check_data_type_references_across_trees(
        signal_root: VSSNode, data_type_root: Optional[VSSNode]):
    """
    Check that the data type names referenced by nodes in the signal tree are present in the data types tree.
    """
    nonexistant_types = []
    for _, _, node in RenderTree(signal_root):
        # signals with user-defined data types
        if node.is_signal() and node.datatype is None:
            if data_type_root is None or (not node.does_attribute_exist(
                    data_type_root,
                    lambda n: n.base_data_type_str(),
                    lambda n: n.qualified_name(),
                    lambda n: n.is_struct())):
                nonexistant_types.append(f'{node.data_type_str}')

    if len(nonexistant_types) > 0:
        error_str = ", ".join(nonexistant_types)
        logging.error(
            f"Following types were referenced in signals but have not been defined: {error_str}")
        sys.exit(-1)


load_flat_model.include_index = 1  # type: ignore[attr-defined]

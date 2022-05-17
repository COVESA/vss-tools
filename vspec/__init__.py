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
import re
import collections

from anytree import (Resolver, ChildResolverError, LevelOrderIter)
import deprecation

from .model.vsstree import VSSNode


class VSpecError(Exception):
    def __init__(self, *args, **kwargs):
        self.file_name = args[0]
        self.line_nr = args[1]
        self.message = args[2]
        Exception.__init__(self, *args, **kwargs)

    def __str__(self):
        return "{}: {}: {}".format(self.file_name, self.line_nr, self.message)


#
# Manager of all SignalUUID instances.
#
class SignalUUIDManager:
    NAMESPACE = "vehicle_signal_specification"

    def __init__(self):
        self.signal_uuid_db = SignalUUID_DB()
        self.namespace_uuid = uuid.uuid5(uuid.NAMESPACE_OID, self.NAMESPACE)

    # Return the parent of the provided signal
    def parent_signal(self, signal_name):
        last_period = signal_name.rfind('.')

        if last_period == -1:
            return ""

        return signal_name[0:last_period]

    # Return the namespace UUID
    #
    # Returns the namespace UUID5 computed on instantiaton of the class.
    # If hex = True the UUID is returned as hex number rather than the UUID
    # string.
    #
    def get_namespace_uuid(self, hex=False):
        if hex:
            return self.namespace_uuid.hex
        else:
            return self.namespace_uuid

    # Locate and return an existing signal ID, or create and return a new one.
    # If no UUID has been assigned, a new UUID is created and assigned to
    # 'signal_name' in the specified SignalUUID_DB object.
    #
    def get_or_assign_signal_uuid(self, signal_name):

        try:
            return self.signal_uuid_db.db[signal_name]
        except:
            # Generate a new UUID, using the class namespace for UUID v5.
            uuid_val = uuid.uuid5(self.namespace_uuid, signal_name).hex
            self.signal_uuid_db.db[signal_name] = uuid_val
            return uuid_val


#
# Manage the UUIDs of a set of signals with a given prefix.
#
class SignalUUID_DB:
    # Create a new SignalUUID object.
    def __init__(self):
        self.db = {}



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
        except IOError as e:
            pass

    # We failed, raise last exception we ran into.
    raise VSpecError(file_name, 0, "File error")


def assign_signal_uuids(flat_model):
    for elem in flat_model:
        elem["uuid"] = db_mgr.get_or_assign_signal_uuid(elem["$name$"])

    return flat_model


@deprecation.deprecated(deprecated_in="2.0", removed_in="2.0",
                        current_version="2.1",
                        details="Anytree as tree library introduced for typesafe handling of vss structure.")
def load(file_name, include_paths):
    flat_model = load_flat_model(file_name, "", include_paths)
    flat_model_instances = expand_instances(flat_model)
    absolute_path_flat_model = create_absolute_paths(flat_model_instances)
    absolute_path_flat_model_with_id = assign_signal_uuids(absolute_path_flat_model)
    deep_model = create_nested_model(absolute_path_flat_model_with_id, file_name)
    cleanup_deep_model(deep_model)
    return deep_model["children"]


def convert_yaml_to_list(raw_yaml):
    if isinstance(raw_yaml, list):
        return raw_yaml

    # Sort the dictionary according to line number.
    # The reason is that when the YAML file is loaded
    # the object order is not preserved in the created
    # dictionary
    raw_yaml = collections.OrderedDict(sorted(raw_yaml.items(), key=lambda x: x[1]['$line$']))
    lst = []
    for elem in raw_yaml:
        if isinstance(raw_yaml[elem], dict):
            raw_yaml[elem]['$name$'] = elem
            lst.append(raw_yaml[elem])

    return lst



def load_tree(file_name, include_paths, merge_private=False, break_on_noncore_attribute=False, break_on_name_style_violation=False, expand_inst = True):
    flat_model = load_flat_model(file_name, "", include_paths)
    if expand_inst:
        flat_model = expand_instances(flat_model)
    absolute_path_flat_model = create_absolute_paths(flat_model)
    absolute_path_flat_model_with_id = assign_signal_uuids(absolute_path_flat_model)
    deep_model = create_nested_model(absolute_path_flat_model_with_id, file_name)
    cleanup_deep_model(deep_model)
    dict_tree = deep_model["children"]
    return render_tree(dict_tree, merge_private, break_on_noncore_attribute=break_on_noncore_attribute, break_on_name_style_violation=break_on_name_style_violation)


def load_flat_model(file_name, prefix, include_paths):
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
        mapping = yaml.constructor.Constructor.construct_mapping(loader, node, deep=deep)

        # Replace
        # { 'Vehicle.Speed': { 'datatype': 'boolean', 'type': 'sensor' }}
        # with
        # { '$name$': 'Vehicle.Speed', 'datatype': 'boolean', 'type': 'sensor' }

        for key, val in list(mapping.items()):
            if key[0] == '$':
                continue

            if val == None:
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
    loader.compose_node = yaml_compose_node

    loader.construct_mapping = yaml_construct_mapping
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
    loader.compose_node = yaml_compose_node

    loader.construct_mapping = yaml_construct_mapping
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
    expanded_includes = expand_includes(raw_yaml, prefix, include_paths)

    # Add type: branch when type is missing.
    flat_model = cleanup_flat_entries(expanded_includes)

    return flat_model


#
# 1. If no type is specified, default it to "branch".
# 2. Check that the declared type is a FrancaIDL.
# 3. Correct the  casing of type.
# 4, Check that allowed values are provided as arrays.
#
def cleanup_flat_entries(flat_model):
    available_types = ["sensor", "actuator", "branch", "attribute", "UInt8", "Int8", "UInt16", "Int16",
                       "UInt32", "Int32", "UInt64", "Int64", "Boolean",
                       "Float", "Double", "String"]

    available_downcase_types = ["sensor", "actuator", "branch", "attribute", "uint8", "int8", "uint16",
                                "int16",
                                "uint32", "int32", "uint64", "int64", "boolean",
                                "float", "double", "string"]

    # Traverse the flat list of the parsed specification
    for elem in flat_model:
        # Is this an include element?
        if "type" not in elem:
            elem["type"] = "branch"

        # Check, without case sensitivity that we do have
        # a validated type.
        if not elem["type"].lower() in available_downcase_types:
            raise VSpecError(elem["$file_name$"], elem["$line$"], "Unknown type: {}".format(elem["type"]))

        # Get the correct casing for the type.
        elem["type"] = available_types[available_downcase_types.index(elem["type"].lower())]

        if "allowed" in elem and not isinstance(elem["allowed"], list):
            raise VSpecError(elem["$file_name$"], elem["$line$"], "Allowed values are not represented as array.")

    return flat_model


#
# Delete parser-specific elements
#
def cleanup_deep_model(deep_model):
    
    if "$line$" in deep_model:
        del deep_model["$line$"]

    if "$prefix$" in deep_model:
        del deep_model["$prefix$"]

    if "$name$" in deep_model:
        del deep_model['$name$']

    if (deep_model["type"] == "branch"):
        children = deep_model["children"]
        for child in deep_model["children"]:
            cleanup_deep_model(children[child])

    return None


#
# Verify that we are using correct YAML in the model
#
def check_yaml_usage(flat_model, file_name):
    for elem in flat_model:
        if isinstance(elem, list):
            raise VSpecError(file_name, 0,
                             "Element {} is not a list entry. (Did you forget a ':'?)".format(elem))

    # FIXME:
    # Add more usage checks, such as absence of nested models.
    # and mutually exclusive elements.


# Expand yaml include elements (inserted by yamilify_include())
#
def expand_includes(flat_model, prefix, include_paths):
    # Build up a new spec model based on the old one, but
    # with expanded include directives.

    new_flat_model = []

    # Traverse the flat list of the parsed specification
    for elem in flat_model:
        # Is this an include element?
        if elem['$name$'][0:9] == "$include$":
            include_prefix = elem.get("prefix", "")
            # Append include prefix to our current prefix.
            # Make sure we do not start new prefix with a "."
            if prefix != "":
                if include_prefix != "":
                    include_prefix = "{}.{}".format(prefix, include_prefix)
                else:
                    include_prefix = prefix

            # Recursively load included file
            inc_elem = load_flat_model(elem["file"], include_prefix, include_paths)

            # Add the loaded elements at the end of the new spec model
            new_flat_model.extend(inc_elem)
        else:
            # Add a prefix to the element
            elem["$prefix$"] = prefix
            # Add the existing elements at the end of the new spec model
            new_flat_model.append(elem)

    return new_flat_model


def expand_instances(flat_model):
    # create instances from specification

    cont = True

    def extend_entry(new_entry, instance, name):
        # It is expected that name exist in new_entry, either in "name" or "prefix", so two use-cases exist
        # 1. Name part shall be refactored, e.g. Axle.TireAspectRatio -> Axle.Row1.TireAspectRatio
        # 2. Prefix part shall be instantiated, e.g. Vehicle.Chassis.Axle.Wheel -> Vehicle.Chassis.Axle.Row2.Wheel

        if (name==new_entry["$name$"]) or new_entry["$name$"].startswith(name + "."):
            new_entry["$name$"] = new_entry["$name$"].replace(name, "{}.{}".format(name, instance), 1)
        else:
            tmp = new_entry["$prefix$"]
            search_str = "." + name
            if tmp.endswith(search_str):
              # If base is "Seat" and prefix "Vehicle.CabinSeat.Seat" then we want to match last Seat
              new_entry["$prefix$"] = tmp[:-len(search_str)] + "." + "{}.{}".format(name, instance)
            else:
              # If base is "Axle" and prefix "Vehicle.ChassisAxle.Axle.Wheel" then we want to match last Axle
              new_entry["$prefix$"] = new_entry["$prefix$"].replace("." + name + ".", "." + "{}.{}".format(name, instance) + ".", 1)
        return new_entry

    # repetition for nested instances
    while cont:
        cont = False
        new_flat_model = []
        elements_to_instantiate = []
        base_name = ''
        instances = []
        current_inst_path = ''

        for elem in flat_model:
            # search for instantiations and related signals
            # element that shall be affected by this instantiation (must start with <branch_name>.)
            # only add "." if there actually is prefix to support instances on top level
            elem_inst_path =  '.'.join([x for x in (elem["$prefix$"], elem["$name$"]) if x])
            if current_inst_path and (current_inst_path + ".") in elem_inst_path:
                elements_to_instantiate.append(elem)
            # If not affected just keep it for next round
            else:
                new_flat_model.append(elem)

            # check if current item is an instantiated branch
            if 'instances' in elem.keys():
                # ignore nested/other instances for now and do it in the next run
                if instances:
                    # check if this is a redefinition of the current branch to change instantiation
                    if elem_inst_path == current_inst_path:
                      instances = createInstantiationEntries([elem['instances']])
                      del elem['instances']
                    else:
                      # continue iterations until all instantiations have been handled
                      cont = True
                else:
                    instances = createInstantiationEntries([elem['instances']])
                    del elem['instances']
                    elements_to_instantiate.append(elem)
                    base_name = elem["$name$"]
                    current_inst_path = elem_inst_path

        # Now instantiate all items affected
        for i in instances:
            # if multiple instances, only attach children under last instance
            # e.g. row1.left.{children}
            new_flat_model.append(extend_entry(dict(elements_to_instantiate[0]), i[0], base_name))
            if i[1]:
                for e in elements_to_instantiate[1:]:
                    if isinstance(i[0], str):
                        new_flat_model.append(extend_entry(dict(e), i[0], base_name))

        flat_model = new_flat_model
    return flat_model


def createInstantiationEntries(instances, prefix=''):
    # create instances according to the spec

    reg_ex = r"\w+\[\d+,(\d+)\]"

    if not instances:
        return

    rest = None
    i = []
    result = []

    if len(instances) == 1:
        i = instances[0]
    else:
        i = instances[0]
        rest = instances[1:]

    if prefix and not prefix.endswith("."):
        prefix += "."
    # parse string instantiation elements (e.g. Row[1,5])
    if isinstance(i, str):
        if re.match(reg_ex, i):

            inst_range_arr = re.split(r"\[+|,+|\]", i)

            for r in range(int(inst_range_arr[1]), int(inst_range_arr[2]) + 1):
                next_prefix = prefix + inst_range_arr[0] + str(r)
                if rest:
                    result.append([next_prefix, False])
                    result.extend(createInstantiationEntries(rest, next_prefix))
                else:
                    result.append([next_prefix, True])
        else:
            raise VSpecError("", "", "instantiation type not supported")

    # Use list elements for instances (e.g. ["LEFT","RIGHT"])
    elif isinstance(i, list):

        complex_list = False

        for r in i:
            # if in case of multiple instances in one branch
            # it has to be distinguished from a list of
            # string instantiations, like ["LEFT","RIGHT"]
            if isinstance(r, str):
                if re.match(reg_ex, r):
                    if rest:
                        rest.append(r)
                    else:
                        rest = [r]
                    complex_list = True
                else:
                    next_prefix = prefix + str(r)

                    if rest:
                        result.append([next_prefix, False])
                        result.extend(createInstantiationEntries(rest, next_prefix))
                    else:
                        result.append([next_prefix, True])

            else:
                # in case of multiple instances, the list is
                # has to be parsed, like ["LEFT","RIGHT"]
                if rest:
                    rest.append(r)
                else:
                    rest = [r]
                complex_list = True

        if complex_list:
            result.extend(createInstantiationEntries(rest, prefix))
    return result


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
        if elem["type"] == "branch":
            deep_model["type"] = "branch"
            elem["children"] = {}

        # Create a list of path components to the given element
        #  name='body.door.front.left.lock' ->
        # [ 'body', 'door', 'front', 'left', 'lock' ]
        name_list = elem['$name$'].split(".")

        # Extract prefix and name
        prefix = list_to_path(name_list[:-1])
        name = name_list[-1]

        # Locate the correct branch in the tree
        parent_branch = find_branch(deep_model, name_list[:-1], 0)

        # If an element with name is already in the parent branch
        # we update its fields with the fields from the new element
        if name in parent_branch["children"]:
            old_elem = parent_branch["children"][name]
            # never update the type
            elem.pop("type", None)
            # concatenate file names
            fname = "{}:{}".format(old_elem["$file_name$"], elem["$file_name$"])
            old_elem.update(elem)
            old_elem["$file_name$"] = fname
        else:
            parent_branch["children"][name] = elem

    return deep_model


# Find the given prefix somewhere under the tree rooted in branch.
def find_branch(branch, name_list, index):
    # Have we reached the end of the name list
    if len(name_list) == index:
        if (branch["type"] != "branch"):
            raise VSpecError(branch.get("$file_name$", "??"),
                             branch.get("$line$", "??"),
                             "Not a branch: {}.".format(branch['$name$']))

        return branch

    if (branch["type"] != "branch"):
        raise VSpecError(branch.get("$file_name$", "??"),
                         branch.get("$line$", "??"),
                         "{} is not a branch.".format(list_to_path(name_list[:index])))

    children = branch["children"]

    if name_list[index] not in children:
        raise VSpecError(branch.get("$file_name$", "??"),
                         branch.get("$line$", "??"),
                         "Missing branch: {} in {}.".format(name_list[index],
                                                            list_to_path(name_list)))

    # Traverse all children, looking for the
    # Move on to next element in prefix.
    return find_branch(children[name_list[index]], name_list, index + 1)


def list_to_path(name_list):
    path = ""
    for name in name_list:
        if path == "":
            path = name
        else:
            path = "{}.{}".format(path, name)

    return path


# Convert a dot-notated element name to a list.
def element_to_list(elem):
    name = elem['$name$']

    if elem["$prefix$"] == "":
        path = name
    else:
        path = "{}.{}".format(elem["$prefix$"], name)

    return


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

        text = fmt_str.format(text[:st_index], include_file, include_prefix, text[end_index:])

    return text


def render_tree(tree_dict, merge_private=False, break_on_noncore_attribute=False, break_on_name_style_violation=False) -> VSSNode:
    if len(tree_dict) != 1:
        raise Exception('Invalid VSS model, must have single root node')

    root_element_name = next(iter(tree_dict.keys()))
    root_element = tree_dict[root_element_name]
    tree_root = VSSNode(root_element_name, root_element, break_on_noncore_attribute=break_on_noncore_attribute, break_on_name_style_violation=break_on_name_style_violation)

    if "children" in root_element.keys():
        child_nodes = root_element["children"]
        render_subtree(child_nodes, tree_root, break_on_noncore_attribute=break_on_noncore_attribute, break_on_name_style_violation=break_on_name_style_violation)

    if merge_private:
        merge_private_into_main_tree(tree_root)
    return tree_root


def render_subtree(subtree, parent, break_on_noncore_attribute=False, break_on_name_style_violation=False):
    for element_name in subtree:
        current_element = subtree[element_name]

        new_element = VSSNode(element_name, current_element, parent=parent, break_on_noncore_attribute=break_on_noncore_attribute, break_on_name_style_violation=break_on_name_style_violation)
        if "children" in current_element.keys():
            child_nodes = current_element["children"]
            render_subtree(child_nodes, new_element, break_on_noncore_attribute, break_on_name_style_violation=break_on_name_style_violation)


def merge_private_into_main_tree(tree_root: VSSNode):
    r = Resolver()
    try:
        private = r.get(tree_root, "/Vehicle/Private")
        detect_and_merge(tree_root, private)
        private.parent = None
    except ChildResolverError:
        print("No private Attribute branch detected")


def detect_and_merge(tree_root: VSSNode, private_root: VSSNode):
    r = Resolver()
    private_element: VSSNode
    for private_element in LevelOrderIter(private_root):
        if private_element == private_root:
            continue

        if not private_element.is_private():
            continue

        element_name = "/" + private_element.qualified_name("/")
        candidate_name = element_name.replace("Private/", "")

        if not VSSNode.node_exists(tree_root, candidate_name):
            new_parent_name = "/" + private_element.parent.qualified_name("/").replace("/Private", "")
            new_parent = r.get(tree_root, new_parent_name)
            private_element.parent = new_parent

        elif private_element.is_leaf:
            other_node = r.get(tree_root, candidate_name)
            other_node.merge(private_element)
            private_element.parent = None


def merge_tree(base: VSSNode, overlay: VSSNode):
    r = Resolver()
    overlay_element: VSSNode
    for overlay_element in LevelOrderIter(overlay):
        element_name = "/" + overlay_element.qualified_name("/")

        if not VSSNode.node_exists(base, element_name):
            new_parent_name = "/" + overlay_element.parent.qualified_name("/")
            new_parent = r.get(base, new_parent_name)
            overlay_element.parent = new_parent

        elif overlay_element.is_leaf:
            other_node = r.get(base, element_name)
            other_node.merge(overlay_element)
            overlay_element.parent = None

db_mgr = SignalUUIDManager()

load_flat_model.include_index = 1

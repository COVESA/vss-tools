#
# Copyright (C) 2016, Jaguar Land Rover
#
# This program is licensed under the terms and conditions of the
# Mozilla Public License, version 2.0.  The full text of the 
# Mozilla Public License is at https://www.mozilla.org/MPL/2.0/
#
# 
# VSpec file parser.
#  

import yaml
import json

class VSpecError(Exception):
    def __init__(self, *args, **kwargs):
        self.file_name=args[0]
        self.line_nr=args[1]
        self.message = args[2]
        Exception.__init__(self, *args, **kwargs)
    
    def __str__(self):
        return  "{}: {}: {}".format(self.file_name, self.line_nr, self.message)


# Try to open a file name that can reside
# in any directory listed in incude_paths.
# If successful, read context and return file
#
def search_and_read(file_name, include_paths):
    for directory in include_paths:
        try:
            with open ("{}/{}".format(directory, file_name), "r") as fp:
                text = fp.read()
                fp.close()
                return text
        except IOError as e:
            pass

    # We failed, raise last exception we ran into.
    raise VSpecError(file_name, 0, "File not found")


def load(file_name, include_paths):
    flat_model = _load(file_name, "", include_paths)
    deep_model = create_nested_model(flat_model, file_name)
    cleanup_deep_model(deep_model)
    return deep_model["children"]

def _load(file_name, prefix, include_paths):
    # Hooks into YAML parser to add line numbers 
    # and file name into each elemeent
    def yaml_compose_node(parent, index):
        # the line number where the previous token has ended (plus empty lines)
        line = loader.line
        try: 
            node = yaml.composer.Composer.compose_node(loader, parent, index)
        except yaml.scanner.ScannerError as e:
            raise VSpecError(file_name, line + 1, e)
        except yaml.parser.ParserError as e:
            raise VSpecError(file_name, line + 1, e)

        node.__line__ = line + 1
        node.__file_name__ = file_name
        return node

    def yaml_construct_mapping(node, deep=False):
        mapping = yaml.constructor.Constructor.construct_mapping(loader, node, deep=deep)
        mapping['$line$'] = node.__line__
        mapping['$file_name$'] = node.__file_name__
        return mapping


    text = search_and_read(file_name, include_paths)
    text = yamilify_includes(text)


    # Setup a loader to include $line$ and $file_name$ as
    # added python objects to the parsed tree.
    loader = yaml.Loader(text)
    loader.compose_node = yaml_compose_node
    loader.construct_mapping = yaml_construct_mapping
    raw_yaml = loader.get_data()

    check_yaml_usage(raw_yaml, file_name)
    # Expand all includes. Will call back to _load() to
    # recursively expand all include files.
    expanded_includes = expand_includes(raw_yaml, prefix, include_paths)

    # Add type: branch when type is missing.
    flat_model = add_default_type(expanded_includes)

    # FIXME: Syntax and semantic checks of loaded nodes.

    return flat_model

#
# If no type is specified, default it to "branch"
#
def add_default_type(flat_model):
    # Traverse the flat list of the parsed specification
    for elem in flat_model:
        # Is this an include element?
        if not elem.has_key("type"):
            elem["type"] = "branch"

    return flat_model

#
# Delete parser-specific elements
#
def cleanup_deep_model(deep_model):
    # Traverse the flat list of the parsed specification
    # Is this an include element?
    if deep_model.has_key("$file_name$"):
            del deep_model["$file_name$"]

    if deep_model.has_key("$line$"):
        del deep_model["$line$"]

    if deep_model.has_key("$prefix$"):
        del deep_model["$prefix$"]

    try:
        del deep_model[find_element_name(deep_model)]
    except:
        pass

    if deep_model["type"] == "branch":
        children = deep_model["children"]
        for child in deep_model["children"]:
            cleanup_deep_model(children[child])

    return None

#
# Verify that we are using correct YAML in the model
#
def check_yaml_usage(flat_model, file_name):
    for elem in flat_model:
        if isinstance(elem, basestring):
            raise VSpecError(file_name,  0,
                             "Element {} is not a list entry. (Did you forget a ':'?)".format(elem))

        
    # FIXME:
    # Add more usage checks, such as absence of nested models.
    # and mutually exclusive elements.


#


# Expand yaml include elements (inserted by yamilify_include())
#
def expand_includes(flat_model, prefix, include_paths):
    # Build up a new spec model based on the old one, but
    # with expanded include directives.
    
    new_flat_model = []

    # Traverse the flat list of the parsed specification
    for elem in flat_model:
        # Is this an include element?
        if elem.has_key("$include$"):
            include_elem = elem["$include$"]
            include_prefix = include_elem.get("prefix", "")
            # Append include prefix to our current prefix.
            # Make sure we do not start new prefix with a "."
            if prefix != "":
                include_prefix = "{}.{}".format(prefix, include_prefix)
            
            # Recursively load included file

            inc_elem = _load(include_elem["file"], include_prefix, include_paths)
            
            # Add the loaded elements at the end of the new spec model
            new_flat_model.extend(inc_elem)
        else:
            # Add a prefix to the element
            elem["$prefix$"] = prefix
            # Add the existing elements at the end of the new spec model
            new_flat_model.append(elem)
           
    return new_flat_model


#
# Take the flat model parsed from the vspec file and create a nested
# variant where each component of a prefix becomes a branch.
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
            elem["children"] = {}

        # Create a list of path components to the given element
        #
        # $prefix$='body.door.front.left' name='lock' ->
        # [ 'body', 'door', 'front', 'left', 'lock' ]
        name_list = elemnent_to_list(elem)

        # Extract prefix and name 
        prefix = list_to_path(name_list[:-1])
        name = name_list[-1]

        # Locate the correct branch in the tree
        parent_branch = find_branch(deep_model, name_list[:-1], 0)

        # Delete redundant element

        parent_branch["children"][name] = elem

    return deep_model
        

# Find the given prefix somewhere under the tree rooted in branch.
def find_branch(branch, name_list, index):
    # Have we reached the end of the name list
    if len(name_list) == index:
        if branch["type"] != "branch":
            raise VSpecError(branch.get("$file_name$","??"),
                             branch.get("$line$", "??"),
                             "Not a branch: {}.".format(find_element_name(branch)))
            
        return branch
    
    if branch["type"] != "branch":
        raise VSpecError(branch.get("$file_name$","??"),
                         branch.get("$line$", "??"),
                         "{} is not a branch.".format(list_to_path(name_list[:index])))

    children = branch["children"]
    
    if not children.has_key(name_list[index]):
        raise VSpecError(branch.get("$file_name$","??"),
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


def find_element_name(elem):
    # Find the name of the branch / signal
    for key, val in elem.iteritems():
        if val == None:
            return key

    raise VSpecError(elem.get("$file_name$","??"),
                     elem.get("$line$", "??"),
                     "Could not find element name.")


def elemnent_to_list(elem):
    name = find_element_name(elem)

    if elem["$prefix$"] == "":
        path = name
    else:
        path = "{}.{}".format(elem["$prefix$"], name)

    return path.split(".")
    
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
def yamilify_includes(text):
    while True:
        st_index = text.find("\n#include")
        if st_index == -1:
            return text

        end_index = text.find("\n", st_index+1)
        if end_index == -1:
            return text

        include_arg = text[st_index+10:end_index].split()
        if len(include_arg) == 2:
            [ include_file, include_prefix] = include_arg
        else:
            include_prefix = '""'
            [include_file] = include_arg 

        text = """{}
- $include$:
    file: {}
    prefix: {}
{}""".format(text[:st_index], include_file, include_prefix, text[end_index:])

        


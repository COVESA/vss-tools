#!/usr/bin/env python3

#
# (c) 2021 Robert Bosch GmbH
# (c) 2021 Pavel Sokolov (pavel.sokolov@gmail.com)
# (c) 2016 Jaguar Land Rover
#
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert all vspec input files to a single flat YAML file.
#


import argparse
from vspec.model.vsstree import VSSNode, VSSType
import yaml

def add_arguments(parser: argparse.ArgumentParser):
   #no additional output for YAML at this moment
   parser.description="The YAML exporter does not have additional options"

def export_node(yaml_dict, node, generate_uuid):

    node_path = node.qualified_name()

    yaml_dict[node_path] = {}

    yaml_dict[node_path]["type"] = str(node.type.value)

    if node.type == VSSType.SENSOR or node.type == VSSType.ACTUATOR or node.type == VSSType.ATTRIBUTE:
        yaml_dict[node_path]["datatype"] = str(node.data_type.value)

    # many optional attributes are initilized to "" in vsstree.py
    if node.min != "":
        yaml_dict[node_path]["min"] = node.min
    if node.max != "":
        yaml_dict[node_path]["max"] = node.max
    if node.allowed != "":
        yaml_dict[node_path]["allowed"] = node.allowed
    if node.default_value != "":
        yaml_dict[node_path]["default"] = node.default_value
    if node.deprecation != "":
        yaml_dict[node_path]["deprecation"] = node.deprecation

    # in case of unit or aggregate, the attribute will be missing
    try:
        yaml_dict[node_path]["unit"] = str(node.unit.value)
    except AttributeError:
        pass
    try:
        yaml_dict[node_path]["aggregate"] = node.aggregate
    except AttributeError:
        pass

    yaml_dict[node_path]["description"] = node.description
    if generate_uuid:
        yaml_dict[node_path]["uuid"] = node.uuid

    for child in node.children:
        export_node(yaml_dict, child, generate_uuid)


def export_yaml(file, root, generate_uuids):
    yaml_dict = {}
    export_node(yaml_dict, root, generate_uuids)
    yaml.dump(yaml_dict, file, default_flow_style=False, Dumper=NoAliasDumper,
              sort_keys=True, width=1024, indent=2, encoding='utf-8', allow_unicode=True)


# create dumper to remove aliases from output and to add nice new line after each object for a better readability
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()



def export(config: argparse.Namespace, root: VSSNode):
    print("Generating YAML output...")
    yaml_out=open(config.output_file,'w')
    export_yaml(yaml_out, root, not config.no_uuid)

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
from vspec.model.vsstree import VSSNode
import yaml
import logging
from vspec.loggingconfig import initLogging
from typing import Dict, Any


def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument('--yaml-all-extended-attributes', action='store_true',
                        help=("Generate all extended attributes found in the model "
                              "(default is generating only those given by the "
                              "-e/--extended-attributes parameter)."))


def export_node(yaml_dict, node, config, print_uuid):

    node_path = node.qualified_name()

    yaml_dict[node_path] = {}

    yaml_dict[node_path]["type"] = str(node.type.value)

    if node.is_signal() or node.is_property():
        yaml_dict[node_path]["datatype"] = node.get_datatype()

    # many optional attributes are initilized to "" in vsstree.py
    if node.min != "":
        yaml_dict[node_path]["min"] = node.min
    if node.max != "":
        yaml_dict[node_path]["max"] = node.max
    if node.allowed != "":
        yaml_dict[node_path]["allowed"] = node.allowed
    if node.default != "":
        yaml_dict[node_path]["default"] = node.default
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

    if node.comment != "":
        yaml_dict[node_path]["comment"] = node.comment

    if print_uuid:
        yaml_dict[node_path]["uuid"] = node.uuid

    for k, v in node.extended_attributes.items():
        if not config.yaml_all_extended_attributes and k not in VSSNode.whitelisted_extended_attributes:
            continue
        yaml_dict[node_path][k] = v

    for child in node.children:
        export_node(yaml_dict, child, config, print_uuid)


def export_yaml(file_name, content_dict):
    with open(file_name, 'w') as f:
        yaml.dump(content_dict, f, default_flow_style=False, Dumper=NoAliasDumper,
                  sort_keys=True, width=1024, indent=2, encoding='utf-8', allow_unicode=True)


# create dumper to remove aliases from output and to add nice new line after each object for a better readability
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()


def export(config: argparse.Namespace, signal_root: VSSNode, print_uuid, data_type_root: VSSNode):
    logging.info("Generating YAML output...")

    signals_yaml_dict: Dict[str, Any] = {}
    export_node(signals_yaml_dict, signal_root, config, print_uuid)

    if data_type_root is not None:
        data_types_yaml_dict: Dict[str, Any] = {}
        export_node(data_types_yaml_dict, data_type_root, config, print_uuid)
        if config.types_output_file is None:
            logging.info("Adding custom data types to signal dictionary")
            signals_yaml_dict["ComplexDataTypes"] = data_types_yaml_dict
        else:
            export_yaml(config.types_output_file, data_types_yaml_dict)

    export_yaml(config.output_file, signals_yaml_dict)


if __name__ == "__main__":
    initLogging()

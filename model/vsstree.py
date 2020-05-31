#!/usr/bin/python

#
#
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

#
# Convert vspec file to GraphQL
#
import re
import stringcase
from anytree import (Node, Resolver, ChildResolverError)

from model.constants import VSSType, VSSDataType, StringStyle, Unit

DEFAULT_SEPARATOR = "."


class VSSNode(Node):
    """Representation of an VSS element according to the vehicle signal specification."""
    description = None
    uuid = None
    type: VSSType
    data_type: VSSDataType

    unit: Unit
    min = ""
    max = ""
    enum = ""

    default_value = ""
    value = ""

    instances = None

    def __init__(self, name, source_dict: dict, parent=None, children=None):
        """Creates an VSS Node object from parsed yaml instance represented as a dict.

            Args:
                name: Name of this VSS instance.
                source_dict: VSS instance represented as dict from yaml parsing.
                parent: Optional parent of this node instance.
                children: Optional children instances of this node.

            Returns:
                VSSNode object according to the Vehicle Signal Specification.

        """

        super().__init__(name, parent, children)
        VSSNode.validate_vss_element(source_dict, name)
        self.description = source_dict["description"]
        self.type = VSSType.from_str(source_dict["type"])
        self.uuid = source_dict["uuid"]

        if "datatype" in source_dict.keys():
            self.data_type = VSSDataType.from_str(source_dict["datatype"])

        if "unit" in source_dict.keys():
            self.unit = Unit.from_str(source_dict["unit"])

        if "min" in source_dict.keys():
            self.min = source_dict["min"]

        if "max" in source_dict.keys():
            self.max = source_dict["max"]

        if "enum" in source_dict.keys():
            self.enum = source_dict["enum"]

        if "aggregate" in source_dict.keys():
            self.aggregate = source_dict["aggregate"]

        if "default" in source_dict.keys():
            self.default_value = source_dict["default"]

        if "value" in source_dict.keys():
            self.value = source_dict["value"]

        if "instances" in source_dict.keys():
            self.instances = source_dict["instances"]

    def is_private(self) -> bool:
        """Checks weather this instance is in private branch of VSS.

            Returns:
                True, if this instance is in Private sub tree, false otherwise.
        """

        node = self
        while node:
            if node.name == "Private":
                return True
            node = node.parent
        return False

    @staticmethod
    def case_conversion(source, style: StringStyle) -> str:
        """Case conversion of the input (usually fully qualified vss node inlcuding the path) into a supported
         string style representation.
            Args:
                source: Source string to apply conversion to.
                style: Target string style to convert source to.

            Returns:
                Converted source string according to provided string style.
         """

        if style == StringStyle.ALPHANUM_CASE:
            return stringcase.alphanumcase(source)
        elif style == StringStyle.CAMEL_CASE:
            return camel_case(source)
        elif style == StringStyle.CAMEL_BACK:
            return camel_back(source)
        elif style == StringStyle.CAPITAL_CASE:
            return stringcase.capitalcase(source)
        elif style == StringStyle.CONST_CASE:
            return stringcase.constcase(source)
        elif style == StringStyle.LOWER_CASE:
            return stringcase.lowercase(source)
        elif style == StringStyle.PASCAL_CASE:
            return stringcase.pascalcase(source)
        elif style == StringStyle.SENTENCE_CASE:
            return stringcase.sentencecase(source)
        elif style == StringStyle.SNAKE_CASE:
            return stringcase.snakecase(source)
        elif style == StringStyle.SPINAL_CASE:
            return stringcase.spinalcase(source)
        elif style == StringStyle.TITLE_CASE:
            return stringcase.titlecase(source)
        elif style == StringStyle.TRIM_CASE:
            return stringcase.trimcase(source)
        elif style == StringStyle.UPPER_CASE:
            return stringcase.uppercase(source)
        else:
            return source

    def qualified_name(self, separator=DEFAULT_SEPARATOR, style=StringStyle.NONE) -> str:
        """Returns fully qualified name of a VSS object (including path) using the defined separator (or default ='.')
        and string style (or default = no change)
            Args:
                separator: Optional parameter as custom separator between path elements of this instance
                style: Optional parameter to convert VSS instance name using specified string style

            Returns:
                Fully Qualified VSS Node string representation including complete path.

        """

        name = VSSNode.case_conversion(self.name, style)

        path = self
        while not path.is_root:
            path = path.parent
            node_name = path.name
            node_name = VSSNode.case_conversion(node_name, style)

            name = "%s%s%s" % (node_name, separator, name)
        return name

    def is_orphan(self) -> bool:
        """Checks if this instance is a (r)branch without any child nodes

            Returns:
                True if this instance is a (r)branch and has no children.
        """
        if self.type == VSSType.BRANCH or self.type == VSSType.RBRANCH:
            return self.is_leaf
        return False

    def has_unit(self) -> bool:
        """Checks if this instance has a unit

            Returns:
                True if this instance has a unit, False otherwise
        """
        return hasattr(self, "unit") and self.unit is not None

    def has_data_type(self) -> bool:
        """Check if this instance has a data_type

            Returns:
                True if this instance has a data type, False otherwise
        """
        return hasattr(self, "data_type") and self.data_type is not None

    def merge(self, other: "VSSNode"):
        """Merges two VSSNode, other parameter overwrites the caller object
            Args:
                other: other node to merge into the caller object
        """
        for prop in other.__dir__():
            if not prop.startswith("_") and not hasattr(super(), prop):
                if hasattr(other, prop):
                    setattr(self, prop, getattr(other, prop))

    @staticmethod
    def node_exists(root, node_name) -> bool:
        """Checks if a node with the name provided to this method exists
            Args:
                root: root node of tree or root of search if search is applied to subtree
                node_name: name of the node that is searched for.
        """
        try:
            r = Resolver()
            r.get(root, node_name)
            return True
        except ChildResolverError:
            return False

    @staticmethod
    def validate_vss_element(element: dict, name: str):
        """Validates a VSS object. Checks if it has the minimum paramaters (description, type, uuid) and if the optional
        parameters are supported within the specification
            Args:
                element: dict parsed from yaml representing one VSS instance
                name: name of the VSS instances
        """

        if "description" not in element.keys():
            raise Exception("Invalid VSS element %s, must have description" % name)

        if "type" not in element.keys():
            raise Exception("Invalid VSS element %s, must have type" % name)

        if "uuid" not in element.keys():
            raise Exception("Invalid VSS element %s, must have UUID" % name)

        for aKey in element.keys():
            if aKey not in ["type", "children", "datatype", "description", "unit", "uuid", "min", "max", "enum",
                            "aggregate", "default", "value", "instances"]:
                raise Exception("Unsupported attribute tree element %s found: %s" % (name, aKey))


def camel_case(st):
    """Camel case string conversion"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', st)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    return re.sub(r'(?:^|_)([a-z])', lambda x: x.group(1).upper(), s2)


def camel_back(st):
    """Camel back string conversion"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', st)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    return re.sub(r'_([a-z])', lambda x: x.group(1).upper(), s2)

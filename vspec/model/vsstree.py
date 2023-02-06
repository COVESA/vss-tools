#!/usr/bin/env python3

#
#
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#


import sys
import re
import copy
from anytree import Node, Resolver, ChildResolverError
from .exceptions import IncompleteElementException, NameStyleValidationException, ImpossibleMergeException, UnknownAttributeException

from .constants import VSSType, VSSDataType, Unit

DEFAULT_SEPARATOR = "."


class VSSNode(Node):
    """Representation of an VSS element according to the vehicle signal specification."""
    description = None
    comment = ""
    uuid = None
    type: VSSType
    datatype: VSSDataType

    core_attributes = ["type", "children", "datatype", "description", "unit", "uuid", "min", "max", "allowed", "instantiate",
                       "aggregate", "default", "instances", "deprecation", "arraysize", "comment", "$file_name$"]

    # List of accepted extended attributes. In strict terminate if an attribute is
    # neither in core or extended,
    whitelisted_extended_attributes = []

    unit: Unit

    min = ""
    max = ""
    allowed = ""
    instantiate = True

    ttl_name = ""

    default = ""

    instances = None
    deprecation = ""

    def __deepcopy__(self, memo):
        return VSSNode(self.name, self.source_dict.copy(),
                       parent=None, children=copy.deepcopy(self.children, memo))

    def __init__(self, name, source_dict: dict, parent=None, children=None,
                 break_on_unknown_attribute=False, break_on_name_style_violation=False):
        """Creates an VSS Node object from parsed yaml instance represented as a dict.

            Args:
                name: Name of this VSS instance.
                source_dict: VSS instance represented as dict from yaml parsing.
                parent: Optional parent of this node instance.
                children: Optional children instances of this node.
                break_on_unknown_attribute: Throw an exception if the node contains attributes not in core VSS specification
                break_on_name_style_vioation: Throw an exception if this node's name is not follwing th VSS recommended style

            Returns:
                VSSNode object according to the Vehicle Signal Specification.

        """

        super().__init__(name, parent, children)
        try:
            VSSNode.validate_vss_element(source_dict, name)
        except UnknownAttributeException as e:
            print("Warning: {}".format(e))
            if break_on_unknown_attribute:
                print("You asked for strict checking. Terminating.")
                sys.exit(-1)

        self.source_dict = source_dict
        self.unpack_source_dict()

        if not self.is_branch() and ("datatype" not in self.source_dict.keys()):
            raise IncompleteElementException(
                f"Incomplete element {self.name} from {self.source_dict['$file_name$']}: Elements of type {self.type.value} need to have a datatype declared.")

        try:
            self.validate_name_style(self.source_dict["$file_name$"])
        except NameStyleValidationException as e:
            print(f"Warning: {e}")
            if break_on_name_style_violation:
                print("You asked for strict checking. Terminating.")
                sys.exit(-1)

    def unpack_source_dict(self):
        self.extended_attributes = self.source_dict.copy()

        # Clean special cases
        if "children" in self.extended_attributes:
            del self.extended_attributes["children"]
        if "type" in self.extended_attributes:
            del self.extended_attributes["type"]

        def extractCoreAttribute(name: str):
            if name != "children" and name != "type" and name in self.source_dict.keys():
                setattr(self, name, self.source_dict[name])
                del self.extended_attributes[name]

        self.type = VSSType.from_str(self.source_dict["type"])

        for attribute in VSSNode.core_attributes:
            extractCoreAttribute(attribute)

        # Datatype and unit need special handling, so we extract them again
        if "datatype" in self.source_dict.keys():
            self.datatype = VSSDataType.from_str(self.source_dict["datatype"])

        if "unit" in self.source_dict.keys():
            self.unit = Unit.from_str(self.source_dict["unit"])

        if self.has_instances() and not self.is_branch():
            print(
                f"Error: Only branches can be instantiated. {self.qualified_name()} is of type {self.type}")
            sys.exit(-1)

    def validate_name_style(self, sourcefile):
        """Checks wether this node is adhering to VSS style conventions.

            Throws NameStyleValidationException when deviations are detected. A VSS model violating
            this conventions can still be a valid model.

        """
        camel_regexp = p = re.compile('[A-Z][A-Za-z0-9]*$')
        if self.type != VSSType.BRANCH and self.datatype == VSSDataType.BOOLEAN and not self.name.startswith(
                "Is"):
            raise NameStyleValidationException(
                f'Boolean node "{self.name}" found in file "{sourcefile}" is not following naming conventions. It is recommended that boolean nodes start with "Is".')
        if not camel_regexp.match(self.name):
            raise NameStyleValidationException(
                f'Node "{self.name}" found in file "{sourcefile}" is not following naming conventions. It is recommended that node names use camel case, starting with a capital letter, only using letters A-z and numbers 0-9.')

    def qualified_name(self, separator=DEFAULT_SEPARATOR) -> str:
        """Returns fully qualified name of a VSS object (including path) using the defined separator (or default ='.')
            Args:
                separator: Optional parameter as custom separator between path elements of this instance

            Returns:
                Fully Qualified VSS Node string representation including complete path.

        """

        name = self.name

        path = self
        while not path.is_root:
            path = path.parent
            node_name = path.name

            name = "%s%s%s" % (node_name, separator, name)
        return name

    def is_branch(self):
        return self.type == VSSType.BRANCH

    def is_orphan(self) -> bool:
        """Checks if this instance is a branch without any child nodes

            Returns:
                True if this instance is a branch and has no children.
        """
        if self.type == VSSType.BRANCH:
            return self.is_leaf
        return False

    def is_instantiated(self) -> bool:
        """Checks if node shall be instantiated through its parent

            Returns:
                True if it shall be instantiated
        """
        return self.instantiate

    def has_unit(self) -> bool:
        """Checks if this instance has a unit

            Returns:
                True if this instance has a unit, False otherwise
        """
        return hasattr(self, "unit") and self.unit is not None

    def has_datatype(self) -> bool:
        """Check if this instance has a datatype

            Returns:
                True if this instance has a data type, False otherwise
        """
        return hasattr(self, "datatype") and self.datatype is not None

    def has_instances(self) -> bool:
        """Check if this instance has a VSS instances

            Returns:
                True if this instance declares instances, False otherwise
        """
        return hasattr(self, "instances") and self.instances is not None

    def merge(self, other: "VSSNode"):
        """Merges two VSSNode, other parameter overwrites the caller object,
           if it is not None
            Args:
                other: other node to merge into the caller object
        """
        if self.is_branch() and not other.is_branch():
            raise ImpossibleMergeException(
                f"Impossible merging {self.name} from {self.source_dict['$file_name$']} with {other.name} from {other.source_dict['$file_name$']}, can not change branch to {other.type.value}.")
        elif not self.is_branch() and other.is_branch():
            raise ImpossibleMergeException(
                f"Impossible merging {self.name} from {self.source_dict['$file_name$']} with {other.name} from {other.source_dict['$file_name$']}, can not change {self.type.value} to branch.")

        self.source_dict.update(other.source_dict)
        self.unpack_source_dict()

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
        """Validates a VSS object. Checks if it has the minimum parameters (description, type, uuid) and if the optional
        parameters are supported within the specification
            Args:
                element: dict parsed from yaml representing one VSS instance
                name: name of the VSS instances
        """

        if "type" not in element.keys():
            raise Exception("Invalid VSS element %s, must have type" % name)

        unknown = []
        for aKey in element.keys():
            if aKey not in VSSNode.core_attributes and aKey not in VSSNode.whitelisted_extended_attributes:
                unknown.append(aKey)

        if len(unknown) > 0:
            raise UnknownAttributeException(
                f"Attribute(s) {', '.join(map(str, unknown))} in element {name} not a core or known extended attribute.")

        if "default" in element.keys():
            if element["type"] != "attribute":
                raise UnknownAttributeException(
                    "Invalid VSS element %s, only attributes can use default" % name)

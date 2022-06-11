#!/usr/bin/env python3

#
#
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#


import sys
import re
import stringcase
import copy
from anytree import Node, Resolver, ChildResolverError

from .constants import VSSType, VSSDataType, StringStyle, Unit

DEFAULT_SEPARATOR = "."

class UnknownAttributeException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class NameStyleValidationException(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

class VSSNode(Node):
    """Representation of an VSS element according to the vehicle signal specification."""
    description = None
    comment = ""
    uuid = None
    type: VSSType
    datatype: VSSDataType

    core_attributes = ["type", "children", "datatype", "description", "unit", "uuid", "min", "max", "allowed",
                            "aggregate", "default" , "instances", "deprecation", "arraysize", "comment", "$file_name$"]

    # List of accepted extended attributes. In strict terminate if an attribtute is 
    # neither in core or extended, 
    whitelisted_extended_attributes = []

    unit: Unit
    min = ""
    max = ""
    allowed = ""

    ttl_name = ""

    default_value = ""

    instances = None
    deprecation = ""

    def __deepcopy__(self,memo):
        return VSSNode(self.name, self.source_dict, parent=self.parent, children=copy.deepcopy(self.children,memo))

    def __init__(self, name, source_dict: dict, parent=None, children=None, break_on_noncore_attribute=False, break_on_name_style_violation=False):
        """Creates an VSS Node object from parsed yaml instance represented as a dict.

            Args:
                name: Name of this VSS instance.
                source_dict: VSS instance represented as dict from yaml parsing.
                parent: Optional parent of this node instance.
                children: Optional children instances of this node.
                break_on_noncore_attribute: Throw an exception if the node contains attributes not in core VSS specification
                break_on_name_style_vioation: Throw an exception if this node's name is not follwing th VSS recommended style

            Returns:
                VSSNode object according to the Vehicle Signal Specification.

        """

        super().__init__(name, parent, children)
        try:
            VSSNode.validate_vss_element(source_dict, name)
        except UnknownAttributeException as e:
            print("Warning: {}".format(e))
            if break_on_noncore_attribute:
                print("You asked for strict checking. Terminating.")
                sys.exit(-1)

        self.source_dict=source_dict

        self.extended_attributes =  source_dict.copy()

        # Clean special cases
        if "children" in self.extended_attributes:
            del self.extended_attributes["children"]
        if "type" in self.extended_attributes:
            del self.extended_attributes["type"]

        def extractCoreAttribute(name: str):
            if name != "children" and name != "type" and name in source_dict.keys():
                setattr(self,name, source_dict[name])
                del self.extended_attributes[name]

        self.type = VSSType.from_str(source_dict["type"])

        for attribute in VSSNode.core_attributes:
            extractCoreAttribute(attribute)

        if "datatype" in source_dict.keys():
            self.datatype = VSSDataType.from_str(source_dict["datatype"])

        try:
            self.validate_name_style(source_dict["$file_name$"])
        except NameStyleValidationException as e:
            print(f"Warning: {e}")
            if break_on_name_style_violation:
                print("You asked for strict checking. Terminating.")
                sys.exit(-1)

        if self.has_instances() and not self.is_branch():
            print(f"Error: Only branches can be instantiated. {self.qualified_name()} is of type {self.type}")
            sys.exit(-1)
            
    def validate_name_style(self,sourcefile):
        """Checks wether this node is adhering to VSS style conventions.

            Throws NameStyleValidationException when deviations are detected. A VSS model violating
            this conventions can still be a valid model.

        """
        camel_regexp=p = re.compile('[A-Z][A-Za-z0-9]*$')
        if self.type != VSSType.BRANCH and self.datatype==VSSDataType.BOOLEAN and not self.name.startswith("Is"):
            raise NameStyleValidationException(f'Boolean node "{self.name}" found in file "{sourcefile}" is not following naming conventions. It is recommended that boolean nodes start with "Is".')
        if not camel_regexp.match(self.name):
            raise NameStyleValidationException(f'Node "{self.name}" found in file "{sourcefile}" is not following naming conventions. It is recommended that node names use camel case, starting with a capital letter, only using letters A-z and numbers 0-9.')
        

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
        for prop in vars(other):
            if not prop.startswith("_") and not getattr(other, prop) is None and not hasattr(super(), prop):
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
        """Validates a VSS object. Checks if it has the minimum parameters (description, type, uuid) and if the optional
        parameters are supported within the specification
            Args:
                element: dict parsed from yaml representing one VSS instance
                name: name of the VSS instances
        """

        if "type" not in element.keys():
            raise Exception("Invalid VSS element %s, must have type" % name)

        for aKey in element.keys():
            if aKey not in VSSNode.core_attributes and aKey not in VSSNode.whitelisted_extended_attributes:
                raise UnknownAttributeException('Attribute "%s" in element %s is not a core or known extended attribute.' % (aKey, name))

        if "default" in element.keys():
            if element["type"] != "attribute":
                raise UnknownAttributeException("Invalid VSS element %s, only attributes can use default" % name)


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

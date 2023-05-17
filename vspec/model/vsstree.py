#!/usr/bin/env python3

#
#
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

from anytree import Node, Resolver, ChildResolverError, RenderTree  # type: ignore[import]
from .constants import VSSType, VSSDataType, Unit, VSSConstant
from .exceptions import NameStyleValidationException, \
    ImpossibleMergeException, IncompleteElementException
from typing import Any, Optional, Set, List
import copy
import re
import sys
import logging

DEFAULT_SEPARATOR = "."
ARRAY_SUBSCRIPT_OP = '[]'


class VSSNode(Node):
    """Representation of an VSS element according to the vehicle signal specification."""

    type: VSSType
    description = None
    comment: str = ""
    uuid: str = ""
    # data type - string representation. For struct names, this is the fully
    # qualified struct name.
    data_type_str: str = ""
    # data type - enum representation if available
    datatype: Optional[VSSDataType]

    # The node types that the nodes can take
    available_types: Set[str] = set()

    core_attributes = ["type", "children", "datatype", "description", "unit", "uuid", "min", "max", "allowed",
                       "instantiate", "aggregate", "default", "instances", "deprecation", "arraysize",
                       "comment", "$file_name$"]

    # List of accepted extended attributes. In strict terminate if an attribute is
    # neither in core or extended,
    whitelisted_extended_attributes: List[str] = []

    unit: Optional[VSSConstant]

    min = ""
    max = ""
    allowed = ""
    instantiate = True

    ttl_name = ""

    default = ""

    instances = None
    deprecation = ""

    def __deepcopy__(self, memo):
        return VSSNode(self.name, self.source_dict.copy(), self.available_types.copy(),
                       parent=None, children=copy.deepcopy(self.children, memo))

    def __init__(self, name, source_dict: dict, available_types: Set[str], parent=None,
                 children=None, break_on_unknown_attribute=False, break_on_name_style_violation=False):
        """Creates an VSS Node object from parsed yaml instance represented as a dict.

            Args:
                name: Name of this VSS instance.
                source_dict: VSS instance represented as dict from yaml parsing.
                available_types: Available node types asa string list
                parent: Optional parent of this node instance.
                children: Optional children instances of this node.
                break_on_unknown_attribute: Throw if the node contains attributes not in core VSS specification
                break_on_name_style_vioation: Throw if this node's name is not follwing th VSS recommended style

            Returns:
                VSSNode object according to the Vehicle Signal Specification.

        """

        super().__init__(name, parent, children)
        self.available_types = available_types

        if (source_dict["type"] not in available_types):
            logging.error(
                f'Invalid type provided for VSSNode: {source_dict["type"]}. Allowed types are {self.available_types}')
            sys.exit(-1)

        self.source_dict = source_dict
        self.unpack_source_dict()

        if (self.is_property() and not self.parent.is_struct()):
            logging.error(f"Orphan property detected. {self.name} is not defined under a struct")
            sys.exit(-1)

        if (self.is_signal() or self.is_property()) and "datatype" not in self.source_dict.keys():
            raise IncompleteElementException(
                (f"Incomplete element {self.name} from {self.source_dict['$file_name$']}: "
                 f"Elements of type {self.type.value} need to have a datatype declared."))

        try:
            self.validate_name_style(self.source_dict["$file_name$"])
        except NameStyleValidationException as e:
            logging.warning(f"Exception: {e}")
            if break_on_name_style_violation:
                logging.error("You asked for strict checking. Terminating.")
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
            if not self.is_struct():
                self.data_type_str = self.source_dict["datatype"]
                self.validate_and_set_datatype()
            else:
                logging.warning(f"Data type specified for struct node: {self.name}. Ignoring it")

        # Units are applicable only for primitives. Not user defined types.
        if "unit" in self.source_dict.keys() and self.has_datatype():
            unit = self.source_dict["unit"]
            try:
                self.unit = Unit.from_str(unit)
            except KeyError:
                logging.error(f"Unknown unit {unit} for signal {self.qualified_name()}. Terminating.")
                sys.exit(-1)
        else:
            self.unit = None

        if self.has_instances() and not self.is_branch():
            logging.error(
                f"Only branches can be instantiated. {self.qualified_name()} is of type {self.type}")
            sys.exit(-1)

    def validate_name_style(self, sourcefile):
        """Checks wether this node is adhering to VSS style conventions.

            Throws NameStyleValidationException when deviations are detected. A VSS model violating
            this conventions can still be a valid model.

        """
        camel_regexp = re.compile('[A-Z][A-Za-z0-9]*$')
        if self.is_signal() and self.datatype == VSSDataType.BOOLEAN and not self.name.startswith("Is"):
            raise NameStyleValidationException(
                (f'Boolean node "{self.name}" found in file "{sourcefile}" is not following naming conventions. ',
                 'It is recommended that boolean nodes start with "Is".'))

        # relax camel case requirement for struct properties
        if not self.is_property() and not camel_regexp.match(self.name):
            raise NameStyleValidationException(
                (f'Node "{self.name}" found in file "{sourcefile}" is not following naming conventions. ',
                 'It is recommended that node names use camel case, starting with a capital letter, ',
                 'only using letters A-z and numbers 0-9.'))

    def base_data_type_str(self) -> str:
        """
        This gives the base type of the type, i.e. without array suffix if present
        """
        suffix = "[]"
        if self.data_type_str.endswith(suffix):
            return self.data_type_str[:-len(suffix)]
        return self.data_type_str

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

    def is_sensor(self):
        return self.type == VSSType.SENSOR

    def is_actuator(self):
        return self.type == VSSType.ACTUATOR

    def is_attribute(self):
        return self.type == VSSType.ATTRIBUTE

    def is_struct(self):
        return self.type == VSSType.STRUCT

    def is_property(self):
        return self.type == VSSType.PROPERTY

    def is_signal(self):
        return self.is_sensor() or self.is_actuator() or self.is_attribute()

    def is_orphan(self) -> bool:
        """Checks if this instance is a branch without any child nodes

            Returns:
                True if this instance is a branch and has no children.
        """
        if self.is_branch() or self.is_struct():
            return self.is_leaf
        return False

    def get_struct_qualified_name(self, struct_name) -> Optional[str]:
        """
        Returns whether a struct node with the given relative name is defined under the branch of this node.
        A relative name is the fully qualified name of the struct without the branch prefix under which it is defined.

        Example 1:
        struct: VehicleTypes.Branch1.StructA
        this: VehicleTypes.Branch1.StructB.Property1 can use data type "StructA"

        Example 2:
        struct: VehicleTypes.Branch1.StructA
        this: VehicleTypes.Branch1.Branch2.StructB.Property1 CANNOT use data type "StructA" since they are not defined
        under the same branch


        Keyword arguments:
        struct_name - The struct name to search for.

        Returns:
        Fully qualified name of the struct if one exists. Otherwise None.
        """
        path = self

        # find the ancestor branch
        root = None
        while not path.is_branch():
            path = path.parent
            root = path

        # find the struct node under the branch
        if root is None:
            return None

        for child in root.children:
            if child.is_struct() and child.name == struct_name:
                return child.qualified_name()

        return None

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

    def get_unit(self) -> str:
        """Returns:
                The name of the unit or empty string if no unit
        """
        if hasattr(self, "unit") and self.unit is not None:
            return self.unit.value
        else:
            return ''

    def has_datatype(self) -> bool:
        """Check if this instance has a datatype

            Returns:
                True if this instance has a data type, False otherwise
        """
        return hasattr(self, "datatype") and self.datatype is not None

    def get_datatype(self) -> str:
        """Returns:
                The name of the dataype or empty string if no datatype
        """
        return self.data_type_str

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
                (f"Impossible merging {self.name} from {self.source_dict['$file_name$']} with {other.name} ",
                 f"from {other.source_dict['$file_name$']}, can not change branch to {other.type.value}."))
        elif not self.is_branch() and other.is_branch():
            raise ImpossibleMergeException(
                (f"Impossible merging {self.name} from {self.source_dict['$file_name$']} with {other.name} "
                 f"from {other.source_dict['$file_name$']}, can not change {self.type.value} to branch."))

        self.source_dict.update(other.source_dict)
        self.unpack_source_dict()

    def validate_and_set_datatype(self):
        """
        For signals:
        Validate that the data type string represents the corresponding VSSDataType enumeration

        For properties:
        Validate that
        1. the data type string represents the corresponding VSSDataType enumeration, OR
        2. the data type string refers to a struct name that is defined under the same branch.
        Note that only struct names relative to the branch under which they are defined are checked.
        Data types provided as fully qualified struct names are skipped from validation as they
        require the entire tree to be rendered first. These are validated after the entire tree is rendered.
        """
        is_array = ARRAY_SUBSCRIPT_OP in self.data_type_str
        try:
            self.datatype = VSSDataType.from_str(self.data_type_str)
        except KeyError as e:
            if self.type == VSSType.PROPERTY:
                # Fully Qualified name as data type name
                if DEFAULT_SEPARATOR in self.data_type_str:
                    logging.info(
                        (f"Qualified datatype name {self.data_type_str} provided in node {self.qualified_name()}. ",
                         "Semantic checks will be performed after the entire tree is rendered. SKIPPING NOW..."))
                else:
                    # get the base name without subscript decoration
                    undecorated_datatype_str = self.data_type_str.split(
                        DEFAULT_SEPARATOR)[-1].replace(ARRAY_SUBSCRIPT_OP, '')
                    # Custom data types can contain names defined under the
                    # same branch
                    struct_fqn = self.get_struct_qualified_name(
                        undecorated_datatype_str)
                    if struct_fqn is None:
                        logging.error(
                            f"Data type not found. Data Type: {undecorated_datatype_str}")
                        sys.exit(-1)

                    # replace data type with qualified name
                    if is_array:
                        self.data_type_str = struct_fqn + ARRAY_SUBSCRIPT_OP
                    else:
                        self.data_type_str = struct_fqn
            elif self.is_signal():
                # This is a signal possibly referencing a user-defined type.
                # Just assign the string value for now. Validation will be
                # performed after the entire tree is rendered.
                logging.debug(f"Possible struct-type encountered - {self.data_type_str} in node {self.name}. ")
            else:
                raise e
            self.datatype = None  # reset the enum

    def does_attribute_exist(self, other: 'VSSNode',
                             attr_fn, other_attr_fn, other_filter_fn):
        """
        Returns whether the an attribute of this node exists as another attribute in the specified tree

        Keyword arguments:
        other: Tree root of the search tree
        attr_fn: Attribute projection function for this node that takes in a VSSNode as argument.
        other_attr_fn: Attribute projection function for nodes in the search tree. The argument is of type VSSNode.
        other_filter_fn: A filter function for node search in the "other" tree. The argument is of type VSSNode.
        """
        key = attr_fn(self)
        return key in set(VSSNode.get_tree_attrs(
            other, other_attr_fn, other_filter_fn))

    @staticmethod
    def node_exists(root, node_name) -> bool:
        """Checks if a node with the name provided to this method exists
            Args:
                root: root node of tree or root of search if search is applied to subtree
                node_name: name of the node that is searched for. Full path (excluding root) is required.
        """
        try:
            r = Resolver()
            r.get(root, node_name)
            return True
        except ChildResolverError:
            return False

    def verify_attributes(self, abort_on_unknown_attribute: bool):
        """
        Validates a VSS object. Checks if it has the minimum parameters (description, type, uuid) and if the optional
        parameters are supported within the specification.
        Should not be used directly on overlays as the requirement to have all present is not relevant for
        overlays, but rather for the final result after emrging.
        """

        # Type presence should have been tested earlier, but is tested here again for completeness
        if "type" not in self.source_dict.keys():
            logging.error("Invalid VSS element %s, must have type", self.name)
            sys.exit(-1)

        if "description" not in self.source_dict.keys():
            logging.error("Invalid VSS element %s, must have description", self.name)
            sys.exit(-1)

        unknown = []
        for aKey in self.source_dict.keys():
            if aKey not in VSSNode.core_attributes and aKey not in VSSNode.whitelisted_extended_attributes:
                unknown.append(aKey)

        unknown_found = False
        if len(unknown) > 0:
            logging.warning(f"Attribute(s) {', '.join(map(str, unknown))} in element {self.name} not a core "
                            "or known extended attribute.")
            unknown_found = True

        if "default" in self.source_dict.keys():
            if self.source_dict["type"] not in {"attribute", "property", "sensor", "actuator"}:
                logging.warning("Invalid VSS element %s, %s cannot use default", self.name, self.source_dict["type"])
                unknown_found = True

        if unknown_found and abort_on_unknown_attribute:
            logging.error("You asked for strict checking. Terminating.")
            sys.exit(-1)

    @staticmethod
    def get_tree_attrs(node: "VSSNode", proj_fn, filter_fn) -> List[Any]:
        """
        Collect all attributes of tree nodes rooted at `node` by applying the specified projection and filter function.

        Keyword arguments:
        node: The tree root node
        proj_fn: A function that takes in the tree node as input and returns a node attribute (projection)
        filter_fn: A function that takes in the tree node as input and
                   returns True if the node should be processed in the result set/False otherwise.

        Returns:
        Projection of nodes that meet the filter criterion specified.
        """
        return [proj_fn(n) for _, _, n in RenderTree(node) if filter_fn(n)]

from anytree import PreOrderIter  # type: ignore
import argparse
from enum import Enum
import logging
from typing import Optional
from vspec.model.vsstree import VSSNode


class OverwriteMethod(Enum):
    ASSIGN_NEW_ID = 1
    OVERWRITE_WITH_VAL_ID = 2
    SKIP = 3


def validate_static_uids(
    signals_dict: dict, validation_tree: VSSNode, config: argparse.Namespace
):
    """Check if static UIDs have changed or if new ones need to be added

    Args:
        signals_dict (dict): _description_
        validation_tree (VSSNode): _description_
        config (argparse.Namespace): _description_
    Returns:
        Optional[dict]: _description_
    """
    highest_id: int = 0
    assigned_new_uid: bool = False

    def check_length(k: str, v: dict, decimal_output):
        """Check if static UID exists and if it's of correct length

        Args:
            k (str): Current key of the dict, evaluates to the qualified name of the node
            v (dict): dict of attributes e.g. static UID
            decimal_output (bool): boolean if you want to generate decimal static UIDs
        """
        if not v["staticUID"]:
            logging.error(f"Static UID for node '{k}' has not been assigned!")
        else:
            if decimal_output:
                try:
                    assert len(v["staticUID"]) == 8
                except AssertionError:
                    logging.error(
                        "[Validation] "
                        f"AssertionError: Length of hex static UID of {k} is incorrect, "
                        "did you check your command line arguments and if they match with "
                        "the validation file? There are multiple options e.g. "
                        "'--gen-no-layer' or '--gen-decimal-ID'."
                    )
            else:
                try:
                    if config.gen_no_layer:
                        assert len(v["staticUID"]) == 8
                    else:
                        assert len(v["staticUID"]) == 10
                except AssertionError:
                    logging.error(
                        "[Validation] "
                        f"AssertionError: Length of hex static UID of {k} is incorrect, "
                        "did you check your command line arguments and if they match with "
                        "the validation file? There are multiple options e.g. "
                        "'--gen-no-layer' or '--gen-decimal-ID'."
                    )

    def check_description(k: str, v: dict, match_tuple: tuple):
        validation_node: VSSNode = validation_tree_nodes[match_tuple[1]]

        try:
            assert v["description"] == validation_node.description

        except AssertionError:
            logging.warning(
                "[Validation] "
                f"DESCRIPTION MISMATCH: The description of {k} has changed from "
                f"\n\t   Validation: '{validation_node.description}' to \n\t   Current "
                f"vspec: '{v['description']}'"
            )

    def check_vss_path(k: str, v: dict, match_tuple: tuple):
        validation_node: VSSNode = validation_tree_nodes[match_tuple[1]]

        if (
            k != validation_node.qualified_name()
            and k.split(".")[-1] == validation_node.name
        ):
            logging.warning(
                "[Validation] "
                f"VSS PATH MISMATCH: The node or leaf was moved from {k} to "
                f"{validation_node.qualified_name()} which is a different position in the tree."
                f"However, this is a non-breaking change, the static ID will remain the same."
            )

    def check_uid(k: str, v: dict, match_tuple: tuple):
        """Validates uid and either assigns next higher id or overwrites with validation id.
        If used in automatic mode it will always assign a new higher id for mismatches. In
        manual mode it will ask you what you would like to do.

        Args:
            k (str): current key in signals dict
            v (dict): current value contains another dict
            match_tuple (tuple): is the name and id of the matched names in validation tree
        """
        nonlocal highest_id
        nonlocal assigned_new_uid
        validation_node: VSSNode = validation_tree_nodes[match_tuple[1]]

        try:
            assert v["staticUID"] == validation_node.extended_attributes["staticUID"]

        except AssertionError:
            if assigned_new_uid:
                logging.warning(
                    "[Validation] "
                    f"UID MISMATCH also, but new static UID for '{k}' has already "
                    "been assigned."
                )
            else:
                logging.warning(
                    "[Validation] "
                    f"UID MISMATCH: IDs don't match. Current tree's node '{k}' has "
                    f"static UID '{v['staticUID']}' and validation tree's node "
                    f"'{validation_node.qualified_name()}' has static UID "
                    f"'{validation_node.extended_attributes['staticUID']}'!"
                )
                if config.validate_automatic_mode:
                    assign_new_id(k, v)
                else:
                    user_interaction(k, v, match_tup=match_tuple)
                assigned_new_uid = True

    def check_unit(k: str, v: dict, match_tuple: tuple):
        """Validates if the unit of a node has changed in comparison to the validation file

        Args:
            k (str): current key in signals dict
            v (dict): current value contains another dict
            match_tuple (tuple): is the name and id of the matched names in validation tree
        """
        nonlocal config
        nonlocal highest_id
        nonlocal assigned_new_uid

        validation_node: VSSNode = validation_tree_nodes[match_tuple[1]]

        if "unit" in v.keys() and "unit" in validation_node.source_dict.keys():
            try:
                assert v["unit"] == validation_node.source_dict["unit"]
            except AssertionError:
                if assigned_new_uid:
                    logging.warning(
                        "[Validation] "
                        f"UNIT MISMATCH also, but a new id for '{k}' has already "
                        "been assigned."
                    )
                else:
                    logging.warning(
                        "[Validation] "
                        f"UNIT MISMATCH: Units of '{k}' in unit: '{v['unit']}' "
                        f"in the current specification and the validation file "
                        f"'{k}' in unit: '{validation_node.unit}' don't "
                        f"match which causes a breaking change, so we need to "
                        f"assign a new id!"
                    )
                    assign_new_id(k, v)
                    assigned_new_uid = True

    def check_datatype(k: str, v: dict, match_tuple: tuple):
        """Validates if the data type of the current node has changed compared to a validation
        file.

        Args:
            k (str): current key in signals dict
            v (dict): current value contains another dict
            match_tuple (tuple): is the name and id of the matched names in validation tree
        """
        nonlocal config
        nonlocal highest_id
        nonlocal assigned_new_uid

        validation_node: VSSNode = validation_tree_nodes[match_tuple[1]]

        if "datatype" in v.keys() and "datatype" in validation_node.source_dict.keys():
            try:
                assert v["datatype"] == validation_node.source_dict["datatype"]
            except AssertionError:
                if assigned_new_uid:
                    logging.warning(
                        f"DATATYPE MISMATCH also, but new id for '{k}' has already "
                        "been assigned"
                    )
                else:
                    logging.warning(
                        "[Validation] "
                        f"DATATYPE MISMATCH: Types of '{k}' of datatype: "
                        f"'{v['datatype']}' in the current specification and "
                        f"the validation file '{k}' of datatype: "
                        f"'{validation_node.get_datatype()}' don't match which "
                        f"causes a breaking change, so we need to assign a new id!"
                    )
                    assign_new_id(k, v)
                    assigned_new_uid = True

    def check_names(k: str, v: dict, match_tuple: tuple):
        pass

    def assign_new_id(k: str, v: dict) -> None:
        """Assignment of next higher static UID if there is a mismatch of the current
        file and the validation file

        Args:
            k (str): current key of dict
            v (dict): current value of dict (also a dict)
        """
        nonlocal config
        nonlocal highest_id

        highest_id += 1

        assign_static_uid: str
        if config.gen_decimal_ID:
            assign_static_uid = str(highest_id).zfill(6)
        else:
            if config.gen_no_layer:
                assign_static_uid = "0x" + format(highest_id, "06X")
            else:
                assign_static_uid = "0x" + format(
                    highest_id << 8 | config.gen_layer_ID_offset, "08X"
                )

        v["staticUID"] = assign_static_uid
        logging.info(f"Assigned new ID '{assign_static_uid}' for {k}")

    def overwrite_current_id(k: str, v: dict, validation_id: str) -> None:
        """Overwrite method for the validation step of static UID assignment.
        This only makes sense if you are sure that there was no breaking
        change in the node, and you want to assign the old id from the
        validation file.

        Args:
            k (str): current key of dict
            v (dict): current value of dict (also a dict)
            validation_id (str): the validation id that you want to overwrite
            the current ID with
        """
        v["staticUID"] = validation_id
        logging.info(f"Assigned new ID '{validation_id}' for {k}")

    def get_id_from_string(hex_string: str) -> int:
        nonlocal config
        curr_value: int
        if not config.gen_no_layer and not config.gen_decimal_ID:
            curr_value = int(hex_string, 16) - config.gen_ID_offset
            curr_value = (curr_value ^ config.gen_layer_ID_offset) >> 8
        else:
            curr_value = int(hex_string, 16)
        return curr_value

    def user_interaction(k: str, v: dict, match_tup: Optional[tuple]):
        match_none_str: str = ""
        if match_tup is None:
            match_none_str = " --- Not available here!"

        logging.warning(
            "What would you like to do?\n1) Assign new ID\n2) Overwrite ID "
            f"with validation ID{match_none_str}\n3) Skip"
        )

        while True:
            try:
                overwrite_method = OverwriteMethod(int(input()))
                if overwrite_method == OverwriteMethod.ASSIGN_NEW_ID:
                    assign_new_id(k, v)
                elif (
                    overwrite_method == OverwriteMethod.OVERWRITE_WITH_VAL_ID
                    and match_tup is not None
                ):
                    overwrite_current_id(
                        k,
                        v,
                        validation_tree_nodes[match_tup[1]].extended_attributes[
                            "staticUID"
                        ],
                    )
                elif (
                    overwrite_method == OverwriteMethod.OVERWRITE_WITH_VAL_ID
                    and match_tup is None
                ):
                    raise ValueError
                elif overwrite_method == OverwriteMethod.SKIP:
                    logging.warning(
                        "You just skipped a new ID assignment this is dangerous! "
                        "You could end up with a missing static UID if you don't "
                        "know exactly what you are doing."
                    )
                    break
            except ValueError:
                logging.warning(
                    "Wrong input please choose again\n1) Assign new ID\n"
                    f"2) Overwrite ID with validation ID {match_none_str}"
                    "\n3) Skip"
                )
                continue
            else:
                break

    def sequential_number_pipeline():
        nonlocal highest_id
        nonlocal assigned_new_uid
        nonlocal validation_tree_nodes

        # need current highest id new assignments during validation
        for key, value in signals_dict.items():
            current_id: int = get_id_from_string(value["staticUID"])
            if current_id > highest_id:
                highest_id = current_id

        for node in PreOrderIter(validation_tree):
            current_id_val: int = get_id_from_string(
                node.extended_attributes["staticUID"]
            )
            if current_id_val > highest_id:
                highest_id = current_id_val

        # check if all nodes have staticUID of correct length
        for key, value in signals_dict.items():
            check_length(key, value, decimal_output=config.gen_decimal_ID)

            matched_names = [
                (key, id_validation_tree)
                for id_validation_tree, other_node in enumerate(validation_tree_nodes)
                if key == other_node.qualified_name()
            ]
            matched_uids = [
                (key, id_validation_tree)
                for id_validation_tree, other_node in enumerate(validation_tree_nodes)
                if value["staticUID"] == other_node.extended_attributes["staticUID"]
            ]

            len_matched_names = len(matched_names)
            len_matched_uids = len(matched_uids)

            # track if new id was assigned
            assigned_new_uid = False

            # CASE 1: NODE ADDED => no match in names and no match in UIDs
            if len_matched_names == 0 and len_matched_uids == 0:
                logging.warning(
                    "[Validation] "
                    f"NODE ADDED: No matches in names and uid for {key} in validation file "
                    f"found. The node must have been added since the last validation."
                )
                if config.validate_automatic_mode:
                    assign_new_id(key, value)
                else:
                    user_interaction(key, value, match_tup=None)
                assigned_new_uid = True

            # CASE 2: UID CHANGE => exactly one matched name but no uid match
            #  --> means that the UID was already updated since the last validation? Maybe
            #  we can put a warning for the user if you are using an old validation file?
            elif len_matched_names == 1 and len_matched_uids == 0:
                logging.warning(
                    "[Validation] "
                    f"UID CHANGE: The same node '{key}' was matched by name to the validation "
                    f"file but the static UID '{value['staticUID']}' was "
                    "not found in the validation file."
                )

            # CASE 3: NAME CHANGE => no matched name but exactly one UID match
            #  --> the name has changed since last validation => do we assign new id?
            elif len_matched_names == 0 and len_matched_uids == 1:
                # check if name or path was changed
                if key.split(".")[-1] == validation_tree_nodes[matched_uids[0][1]].name:
                    check_vss_path(key, value, matched_uids[0])
                else:
                    # if name was changed we want to keep the validation ID
                    logging.warning(
                        "[Validation] "
                        "NAME CHANGE: The name of the node in the current vspec was "
                        "changed from "
                        f"'{validation_tree_nodes[matched_uids[0][1]].qualified_name()}' "
                        f"to '{key}'. This is a non-breaking change if the static UID "
                        "stays the same. Continuing..."
                    )

            # CASE 4: NO CHANGE => exactly one matched name and one matched UID
            #  this is the normal case, here for completeness
            elif len_matched_names == 1 and len_matched_uids == 1:
                # NO CHANGE so no log needed
                assigned_new_uid = False

            # CASE 5: NAME DUPLICATE => multiple names with same UID
            elif len_matched_names > 1 and len_matched_uids == 1:
                logging.warning(
                    "[Validation] "
                    f"NAME DUPLICATE: Caution there were multiple matches with "
                    f"same names for '{key}'. Please check your validation file "
                    f"for duplicates! Still this is a non-breaking change if the "
                    f"UIDs are the same, which is the case. Continuing..."
                )

            # CASE 6: UID DUPLICATE => one name and multiple UIDs
            elif len_matched_names == 1 and len_matched_uids > 1:
                name_list = [
                    validation_tree_nodes[match[1]].qualified_name()
                    for match in matched_uids
                ]
                logging.warning(
                    "[Validation] "
                    + "UID DUPLICATE: There are multiple nodes with the same UID "
                    + len(name_list) * "\n'%s' "
                    + "\nbut different names this is a non-breaking change, so we "
                    + "are continuing..",
                    *name_list,
                )

            # CASE 7: NODE DUPLICATE => multiple names and multiple UIDs
            elif len_matched_names > 1 and len_matched_uids > 1:
                # ToDo implement a cross check if all attributes the same? if yes --> duplicate
                logging.warning(
                    "[Validation] "
                    f"NODE DUPLICATE: Node '{key}' is duplicated with different UIDs, "
                    "please check your validation file for duplicates."
                )

            # CASE 8: DEFAULT => send error
            else:
                logging.error("Please check your input files, something must be wrong!")
                exit()

            # Now check all other attributes, we still want to log if there was a change,
            #  so we need to check if a new ID was already assigned and if so only log
            #  that the attribute has also changed.
            for match in matched_names:
                check_description(key, value, match)
                check_uid(key, value, match)
                check_unit(key, value, match)
                check_datatype(key, value, match)

            for match in matched_uids:
                if len_matched_names == 0:
                    check_description(key, value, match)
                    check_uid(key, value, match)
                    check_unit(key, value, match)
                    check_datatype(key, value, match)

                check_names(key, value, match)

        # ToDo same loop as above but match static UIDs and check for name changes

    def hashed_pipeline():
        nonlocal validation_tree_nodes

        for key, value in signals_dict.items():
            matched_uids = [
                (key, id_validation_tree)
                for id_validation_tree, other_node in enumerate(validation_tree_nodes)
                if value["staticUID"] == other_node.extended_attributes["staticUID"]
            ]

            if len(matched_uids) == 0:
                logging.warning(
                    "[Validation ]"
                    "There was a change in the vspec the current static UID was not found"
                )
                # ToDo all breaking changes here
                #  1. semantic
                #  2. change unit
                #  3. add unit to existing attribute
                #  4. change datatype
                #  5. add enum / rename enum value
                #  6. delete enum value
                #  7. add/change/delete min/max value

                # matched_names = [
                #     (key, id_validation_tree)
                #     for id_validation_tree, other_node in enumerate(
                #         validation_tree_nodes
                #     )
                #     if key == other_node.qualified_name()
                # ]
                # # breakpoint()

            elif len(matched_uids) == 1:
                # ToDo all non-breaking changes here
                #  1. add new attribute
                #  2. deprecate attribute
                #  3. delete attribute
                #  4. move attribute to other VSS path
                #  5. change description
                validation_tree_nodes.pop(matched_uids[0][1])

            else:
                print(
                    "Multiple matches?? Impossible with the way we load data, what's going on"
                )

    # ToDo: CHECK ALL ENTRIES OF CURRENT VSPEC!
    #  FIRST CHECK IF ALL UIDs HAVE BEEN ASSIGNED AND THEN CHECK IF
    #  THERE ARE DUPLICATED NAMES OR UIDs? IF NOT CONTINUE WITH VALIDATION FILE

    # go to top in case we are not
    if validation_tree.parent:
        while validation_tree.parent:
            validation_tree = validation_tree.parent

    validation_tree_nodes: list = []
    for val_node in PreOrderIter(validation_tree):
        validation_tree_nodes.append(val_node)

    if config.use_fnv1_hash:
        hashed_pipeline()
    else:
        sequential_number_pipeline()

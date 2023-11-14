from anytree import PreOrderIter  # type: ignore
import argparse
import logging
from vspec.model.vsstree import VSSNode
from vspec.utils.idgen_utils import fnv1_32_wrapper


def validate_static_uids(
    signals_dict: dict, validation_tree: VSSNode, config: argparse.Namespace
):
    """Check if static UIDs have changed or if new ones need to be added

    @param signals_dict: to be exported dict of all signals containing static UID
    @param validation_tree: tree loaded from validation file
    @param config: the command line arguments the script was run with
    @return: None
    """

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

    def check_semantics(k: str, v: dict) -> bool:
        """Checks if the change was a semantic or path change. This can be triggered by
        manually adding a fka (formerly known as) attribute to the vspec. The result
        is that the old hash can be matched such that a node keeps the same UID.

        @param k: the current key
        @param v: the current value (dict)
        @return: boolean if it was a semantic or path change
        """
        if "fka" in v.keys():
            is_semantic: bool = False
            for fka_val in v["fka"]:
                old_static_uid = "0x" + fnv1_32_wrapper(fka_val, v)
                for i, validation_node in enumerate(validation_tree_nodes):
                    if (
                        old_static_uid
                        == validation_node.extended_attributes["staticUID"]
                    ):
                        logging.warning(
                            f"[Validation] SEMANTIC NAME CHANGE or PATH CHANGE for '{k}'."
                        )
                        is_semantic = True
            return True if is_semantic else False
        else:
            return False

    def check_deprecation(k: str, v: dict, match_tuple: tuple):
        pass

    def hashed_pipeline():
        """This pipeline uses FNV-1 hash for static UIDs.

        If no match UID was matched we check if the user has written an old path or old name,
        so we can tell if it was a semantic or path change. If not we have to assign a new ID
        which causes to throw a `BREAKING CHANGE` warning.
        If there was a match we will continue to check for non-breaking changes and throw
        corresponding logs.
        """
        nonlocal validation_tree_nodes

        for key, value in signals_dict.items():
            matched_uids = [
                (key, id_validation_tree)
                for id_validation_tree, other_node in enumerate(validation_tree_nodes)
                if value["staticUID"] == other_node.extended_attributes["staticUID"]
            ]

            # if not matched via UID check semantics or path change
            if len(matched_uids) == 0:
                if check_semantics(key, value) is False:
                    logging.warning(
                        f"[Validation] BREAKING CHANGE: "
                        f"There was a breaking change for '{key}' which "
                        f"means it is a new node or name, unit, datatype, "
                        f"enum or min/max has changed."
                    )

            # if matched continue with non-breaking checks
            elif len(matched_uids) == 1:
                # ToDo all non-breaking changes here
                #  1. add new attribute
                #  2. deprecate attribute
                #  3. delete attribute
                #  4. move attribute to other VSS path --> handled by semantic change
                #  5. change description
                check_description(key, value, matched_uids[0])

                # now remove the element to speed up things
                validation_tree_nodes.pop(matched_uids[0][1])

            else:
                logging.error(
                    "Multiple matches do not make sense for the way we load the data. "
                    "Please check your input vspec!"
                )
                exit(-1)

    # go to top in case we are not
    if validation_tree.parent:
        while validation_tree.parent:
            validation_tree = validation_tree.parent

    validation_tree_nodes: list = []
    for val_node in PreOrderIter(validation_tree):
        validation_tree_nodes.append(val_node)

    hashed_pipeline()

# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import sys
from typing import Optional

from anytree import PreOrderIter

from vss_tools import log
from vss_tools.vspec.tree import VSSNode
from vss_tools.vspec.utils.idgen_utils import fnv1_32_wrapper


def validate_static_uids(signals_dict: dict, validation_tree: VSSNode, strict: bool):
    """Check if static UIDs have changed or if new ones need to be added

    @param signals_dict: to be exported dict of all signals containing static UID
    @param validation_tree: tree loaded from validation file
    @param strict
    @return: None
    """

    def check_description(k: str, v: dict, match_tuple: tuple):
        validation_node: VSSNode = validation_tree_nodes[match_tuple[1]]

        data = validation_node.get_vss_data()
        try:
            assert v["description"] == data.description

        except AssertionError:
            log.warning(
                "[Validation] "
                f"DESCRIPTION MISMATCH: The description of {k} has changed from "
                f"\n\t   Validation: '{data.description}' to \n\t   Current "
                f"vspec: '{v['description']}'"
            )

    def check_semantics(k: str, v: dict, strict_mode: bool) -> Optional[int]:
        """Checks if the change was a semantic or path change. This can be triggered by
        manually adding a fka (formerly known as) attribute to the vspec. The result
        is that the old hash can be matched such that a node keeps the same UID.

        @param k: the current key
        @param v: the current value (dict)
        @param strict_mode: strict mode means case sensitivity for static UID generation
        @return: boolean if it was a semantic or path change
        """
        if "fka" in v.keys():
            semantic_match: Optional[int] = None
            for fka_val in v["fka"]:
                old_static_uid = "0x" + fnv1_32_wrapper(fka_val, v, strict_mode)
                for i, validation_node in enumerate(validation_tree_nodes):
                    if old_static_uid == validation_node.data.staticUID:
                        log.warning(
                            f"[Validation] SEMANTIC NAME CHANGE or PATH CHANGE for '{k}', "
                            f"it used to be '{validation_node.get_fqn()}'."
                        )
                        semantic_match = i
            return semantic_match
        else:
            return None

    def check_deprecation(k: str, v: dict, match_tuple: tuple):
        if "deprecation" in v.keys() and validation_tree_nodes[match_tuple[1]].data.deprecation:
            if v["deprecation"] != validation_tree_nodes[match_tuple[1]].data.deprecation:
                log.warning(
                    f"[Validation] DEPRECATION MSG CHANGE: Deprecation message "
                    f"for '{k}' was "
                    f"'{validation_tree_nodes[match_tuple[1]].data.deprecation}' "
                    f"in validation but now is '{v['deprecation']}'."
                )

    def hashed_pipeline():
        """This pipeline uses FNV-1 hash for static UIDs.

        If no UID was matched we check if the user has written an old path or old name,
        so we can tell if it was a semantic or path change. If semantic or path change
        we trigger a corresponding warning.
        If not semantic or path change we try to match the key:
        If key was matched we know that it was a unit, datatype, type, enum, min/max change
        which triggers `BREAKING CHANGE` warning. If key cannot be matched the node must have
        been added since the last validation, so it triggers an `ADDED ATTRIBUTE` warning.
        If there was a UID match we will continue to check for non-breaking changes and throw
        corresponding logs.
        In the end the remaining nodes correspond to deleted nodes, so we throw a
        `DELETED ATTRIBUTE` warning.
        """
        nonlocal validation_tree_nodes

        for key, value in signals_dict.items():
            matched_uids = []
            for id_validation_tree, other_node in enumerate(validation_tree_nodes):
                other_sUID = getattr(other_node.data, "staticUID", None)
                if value["staticUID"] == other_sUID:
                    if key != other_node.get_fqn():
                        _ = check_semantics(key, value, strict)
                    matched_uids.append((key, id_validation_tree))
            # if not matched via UID check semantics or path change
            if len(matched_uids) == 0:
                semantic_match = check_semantics(key, value, strict)
                if semantic_match is None:
                    key_found = False
                    for i, node in enumerate(validation_tree_nodes):
                        if key == node.get_fqn():
                            key_found = True
                            validation_tree_nodes.pop(i)
                            break

                    if key_found:
                        log.warning(
                            f"[Validation] BREAKING CHANGE: "
                            f"There was a breaking change for '{key}' which "
                            f"means its name, unit, datatype, type, enum or "
                            f"min/max has changed."
                        )
                    else:
                        log.warning(
                            f"[Validation] ADDED ATTRIBUTE: " f"The node '{key}' was added since the last validation."
                        )
                else:
                    validation_tree_nodes.pop(semantic_match)

            elif len(matched_uids) == 1:
                check_deprecation(key, value, matched_uids[0])
                check_description(key, value, matched_uids[0])

                validation_tree_nodes.pop(matched_uids[0][1])

            else:
                log.error(
                    "[Validation] Multiple matches do not make sense "
                    "for the way we load the data. Please check your "
                    "input vspec!"
                )
                sys.exit(-1)

        for node in validation_tree_nodes:
            log.warning(
                "[Validation] DELETED ATTRIBUTE: "
                f"'{node.get_fqn()}' was not matched so it must have "
                f"been deleted."
            )

    if validation_tree.parent:
        while validation_tree.parent:
            validation_tree = validation_tree.parent

    validation_tree_nodes: list = []
    for val_node in PreOrderIter(validation_tree):
        validation_tree_nodes.append(val_node)

    hashed_pipeline()

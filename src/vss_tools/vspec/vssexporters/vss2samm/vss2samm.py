# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

#
# Convert all vspec input files to a ESMF - Aspect Model Editor (SAMM) - ttl formatted file(s).
#


import importlib
from pathlib import Path
from types import ModuleType
from typing import Optional

import rich_click as click
import vss_tools.vspec.cli_options as clo
from anytree import findall
from vss_tools import log
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.tree import VSSNode

from .config import config as cfg

VSSConcepts: Optional[ModuleType] = None
vss_helper: Optional[ModuleType] = None
ttl_helper: Optional[ModuleType] = None


def __setup_environment(output_namespace, vspec_version, split_depth: int) -> None:
    # Initialize config before to load other helpers / libraries, based on defined by user input, config data
    cfg.init(output_namespace, vspec_version, split_depth)

    global VSSConcepts
    VSSConcepts = importlib.import_module("vss_tools.vspec.vssexporters.vss2samm.helpers.samm_concepts").VSSConcepts

    global vss_helper
    vss_helper = importlib.import_module("vss_tools.vspec.vssexporters.vss2samm.helpers.vss_helper")

    global ttl_helper
    ttl_helper = importlib.import_module("vss_tools.vspec.vssexporters.vss2samm.helpers.ttl_helper")


# TODO: Currently this is a workaround to read the Vehicle.VersionVSS, which is provided from COVESA/VSS
#       and provides the supported VSS version.
#       In best case this functionality should be provided by the vspec tool, loaded in this script.
#
#       Once we migrate the vss2samm tool under the COVESA/vss-tools,
#       we could move this functionality under the vspec script
#       and make sure that we read the version from the COVESA/vehicle_signal_specification/VERSION
#       or as helper function under the VSSNode - root tree.
def __get_version_vss(vss_tree: VSSNode) -> str:
    # DEFAULT version would be 1.0.0
    major = 1
    minor = 0
    patch = 0

    if vss_tree.children and len(vss_tree.children) > 0:
        # Get the VersionVSS node so to extract current VSS version from it.
        vss_version_node = vss_tree.get_child(vss_tree.get_fqn() + ".VersionVSS")

        if vss_version_node:
            for v_child in vss_version_node.children:
                if (
                    v_child.name in ["Major", "Minor", "Patch"]
                    and hasattr(v_child.data, "default")
                    and type(v_child.data.default) is int
                    and v_child.data.default > 1
                ):
                    match v_child.name:
                        case "Major":
                            major = v_child.data.default
                        case "Minor":
                            minor = v_child.data.default
                        case "Patch":
                            patch = v_child.data.default

    return f"{major}.{minor}.{patch}"


# Exporter specific options
@clo.option(
    "-sigf",
    "--signals-file",
    type=click.Path(dir_okay=False, readable=True, path_type=Path, exists=True),
    help="""\b
Path to file with selected VSS signals to be converted.
Allows to convert just selected VSS signals into aspect model(s), if '-spl / --split' is enabled.
\033[36mNOTE:\033[0m each signal in the file should be on a new line and in the format of:
      \033[96mPARENT_SIGNAL.PATH.TO.CHILD_SIGNAL\033[0m as defined in VSS.
\033[33mEXAMPLE:\033[0m \033[96m-sigf PATH_TO_FILE/selected_signals.txt\033[0m
 """,
)
@clo.option(
    "--split-depth",
    "-spld",
    type=int,
    default=1,
    show_default=False,
    help="""\b
Number - used to define, up to which level, VSS branches will be converted into single aspect models.
Can be used in addition to the \033[32m-spl, --split\033[0m option.
Default value of 1 means that only 1st level VSS branches like Vehicle.Cabin, Vehicle.Chassis etc.,
will be converted to separate aspect models.
\033[30m[default: 1]\033[0m
 """,
)
@clo.option(
    "--split/--no-split",
    "-spl",
    default=True,
    show_default=False,
    help="""\b
Boolean flag - used to indicate whether to convert VSS specifications in separate ESMF Aspect(s)
or the whole (selected) VSS specification(s) will be combined into single ESMF Aspect model.
\033[30m[default: True]\033[0m
 """,
)
@clo.option(
    "--target-namespace",
    "-tns",
    "output_namespace",
    type=str,
    default="com.covesa.vss.spec",
    show_default=False,
    help="""\b
Namespace for VSS library, located in specified '--target-folder'.
Will be used as name of the folder where VSS Aspect models (TTLs) are to be stored.
This folder will be created as subfolder of the specified '--target-folder' parameter.
\033[30m[default: com.covesa.vss.spec]\033[0m
 """,
)
@clo.option(
    "--target-folder",
    "-tf",
    type=click.Path(dir_okay=True, file_okay=False, writable=True, path_type=Path),
    default="vss_ttls",
    show_default=False,
    help="""\b
Path to or name for the target folder, where generated aspect models (.ttl files) will be stored.
\033[36mNOTE:\033[0m This folder will be created relatively to the folder from which this script is called.
\033[30m[default: vss_ttls/]\033[0m
""",
)
# END of VSS2SAMM CUSTOM OPTIONS
@click.command()
@clo.vspec_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.uuid_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@clo.types_output_opt
def cli(
    vspec: Path,
    target_folder: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    uuid: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    types_output: Path,
    signals_file,
    output_namespace,
    split,
    split_depth,
) -> None:
    """
    Export COVESA VSS to Eclipse Semantic Modeling Framework (ESMF) - Semantic Aspect Meta Model (SAMM) - .ttl files.
    """

    log.info("Loading VSS Tree...\n")

    # NOTE: Currently the VSS Tree is loaded as "--no-expand"-ed i.e., VSSNode's instances will not be instantiated.
    #       In order to save some redundancy in expanded nodes,
    #       this script will instantiate corresponding instances directly on the aspect model contents.
    #
    #       If required to handle --expand / --no-expand options, the expand_opt can be included.
    #       Just keep in mind that this might lead to some additional logic,
    #       to make sure that each case is handled correctly.
    vss_tree, datatype_tree = get_trees(
        vspec, include_dirs, aborts, strict, extended_attributes, uuid, quantities, units, types, overlays, False
    )

    # Get the VSS version from the vss_tree::VersionVSS
    vss_version = __get_version_vss(vss_tree)

    __setup_environment(output_namespace, vss_version, split_depth)

    included_signals = []
    included_branches = []
    included_signals_input = []

    if signals_file:
        log.info("Using signals from:\n    '%s'\n", signals_file)

        with open(signals_file, "r") as f:
            included_signals_input = f.read().splitlines()

    else:
        log.info("No signals selected.\nCreating model for the whole VSS tree.\n")

    log.info(
        "Update output: '%s' with ESMF namespace: '%s' and VSS Version: '%s'.\n",
        target_folder,
        output_namespace,
        cfg.VSPEC_VERSION,
    )

    # Make sure that target folder gets reflected with respect to current output_namespace and VSPEC_VERSION
    target_folder = Path(f"{target_folder}/{output_namespace}/{cfg.VSPEC_VERSION}")

    log.info("Generating SAMM output...\n")

    if included_signals_input:
        log.info("Included paths:\n%s\n", included_signals_input)

        for signal in included_signals_input:
            path = signal.split(".")
            included_signals.append(path[-1])
            if len(path) > 1:
                for x in path[:-1]:
                    if x not in included_branches:
                        # Add only unique entries (branches)
                        included_branches.append(x)

    if included_branches:
        log.info("Included branches:\n%s\n", included_branches)

    if included_signals:
        log.info("Included signals:\n%s\n", included_signals)

    parsed_tree_uri = None

    if vss_helper is not None and ttl_helper is not None:
        # NOTE: below used parse_vss_tree function will store generated RDF Graph to dedicated TTL file
        if len(included_signals_input) > 0:
            # Filter the VSS tree based on included_signals_input
            vss_helper.filter_vss_tree_for_deletion(vss_tree, included_signals_input)

            # Remove nodes, which were marked as "not selected" i.e. to be deleted
            vss_tree.delete_nodes(findall(vss_tree, filter_=lambda n: n.get_vss_data().delete))

            if vss_tree:
                # Parse the filtered tree to AME TTL.
                parsed_tree_uri = ttl_helper.parse_vss_tree(target_folder, vss_tree, split)

            else:
                # Parse the whole tree as usual.
                parsed_tree_uri = ttl_helper.parse_vss_tree(target_folder, vss_tree, split)

        else:
            # Work with vss_tree as usual.
            parsed_tree_uri = ttl_helper.parse_vss_tree(target_folder, vss_tree, split)

        if parsed_tree_uri != "DEPRECATED":
            log.info(
                "\nVSS to ESMF - SAMM processing - COMPLETED\n\nAll ttl files are located in: '%s'\n\n", target_folder
            )
        else:
            log.warning(
                "VSS to ESMF - SAMM processing - COMPLETED\n\n"
                "VSS tree was not converted because it is DEPRECATED.\n\n"
            )

    else:
        log.warning(
            "VSS to ESMF - SAMM processing - COMPLETED\n\n"
            "VSS tree was not converted because required helpers were not initialized.\n\n"
        )

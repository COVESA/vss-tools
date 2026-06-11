# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from rdflib import Graph
from vss_tools import log

from ..config import config as cfg


# Write RDF Graph data to specified file
def write_graph_to_file(path_to_file: Path, file_name: str, graph: Graph):
    log.debug(
        "Writing RDF Graph to \n  -- file: '%s' \n  -- location: '%s'\n  -- current working directory: '%s'\n",
        file_name,
        path_to_file,
        Path.cwd(),
    )  # type: ignore

    filedata = graph.serialize(format="ttl")

    # Clean up entries like: samm:operations "()" OR samm:operations "( )"
    filedata = filedata.replace(' "()" ', " () ")
    filedata = filedata.replace(' "( )" ', " ( ) ")
    filedata = filedata.replace(' "( ', " ( ")
    filedata = filedata.replace(' )" ', " ) ")

    # Cleanup other escape characters, that were introduced automatically by some of used libraries/tools
    filedata = filedata.replace("\\", "")

    # Cleanup some CUSTOM ESCAPED, by this script characters.
    # Usually double and single quotes in node.description or node.comment field
    filedata = filedata.replace(cfg.CUSTOM_ESCAPE_CHAR, "\\")

    # Cleanup xsd:anyURI with xsd:double
    filedata = filedata.replace("xsd:anyURI", "xsd:double")

    # Make sure that output_folder is created with default permissions
    output_folder: Path = Path(path_to_file)
    output_folder.mkdir(parents=True, exist_ok=True)

    # Create and write data to ttl file. Use a context manager so the file
    # is closed even if .write() raises, and pin the encoding to UTF-8 so
    # RDF graphs containing non-ASCII characters serialise consistently
    # across platforms (matches the encoding fix applied to the other
    # exporters in the previous commit).
    output_file: Path = output_folder / f"{file_name}.ttl"
    with output_file.open("w", encoding="utf-8") as file_writer:
        file_writer.write(filedata)
        file_writer.write("\n")

    # Return file location
    return output_file

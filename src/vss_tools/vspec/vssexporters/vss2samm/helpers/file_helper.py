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

from ..config import Config


# Write RDF Graph data to specified file
def write_graph_to_file(path: Path, name: str, graph: Graph):
    log.debug(
        "Writing RDF Graph to \n  -- file: '%s' \n  -- location: '%s'\n  -- current working directory: '%s'\n",
        name,
        path,
        Path.cwd(),
    )

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
    filedata = filedata.replace(Config.CUSTOM_ESCAPE_CHAR, "\\")

    # Cleanup xsd:anyURI with xsd:double
    filedata = filedata.replace("xsd:anyURI", "xsd:double")

    path.mkdir(parents=True, exist_ok=True)

    # Create and write data to ttl file
    output_file = path / f"{name}.ttl"

    with open(output_file, "w") as f:
        f.write(filedata)
        f.write("\n")

    return output_file

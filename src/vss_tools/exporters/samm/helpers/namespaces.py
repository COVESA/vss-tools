# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from rdflib import URIRef
from vss_tools import log

from ..config import config as cfg


def get_vspec_uri(node_name: str):
    return URIRef(f"{samm_output_namespace}{node_name}")


def get_node_name_from_vspec_uri(node_uri: URIRef):
    return node_uri.replace(samm_output_namespace, "")


def get_unit_uri(unit_name: str):
    return URIRef(f"{samm_base_namespace}:unit:{cfg.SAMM_VERSION}#{unit_name}")


log.debug("VSS to SAMM CONFIG:\n  -- SAMM_TYPE   : %s\n  -- SAMM_VERSION: %s\n", cfg.SAMM_TYPE, cfg.SAMM_VERSION)

# NOTE: samm_base_namespace is more for the ESMF core libraries
samm_prefix = "urn:samm"
samm_base_namespace = f"{samm_prefix}:org.eclipse.esmf.samm"
Namespaces = {
    "samm": f"{samm_base_namespace}:meta-model:{cfg.SAMM_VERSION}#",
    "samm-c": f"{samm_base_namespace}:characteristic:{cfg.SAMM_VERSION}#",
    "samm-e": f"{samm_base_namespace}:entity:{cfg.SAMM_VERSION}#",
    "unit": f"{samm_base_namespace}:unit:{cfg.SAMM_VERSION}#",
}

# Below formatted namespace should look like: urn:samm:com.covesa.vss.spec:5.0.0#
# and is used for the ":" bindings of the converted to TTLs, VSS Aspect models
# that will refer to the user specified output_namespace
samm_output_namespace = f"{samm_prefix}:{cfg.OUTPUT_NAMESPACE}:{cfg.VSPEC_VERSION}#"

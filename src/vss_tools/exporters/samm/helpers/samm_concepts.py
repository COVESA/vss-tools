# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0


from enum import Enum

from rdflib import URIRef

from ..config import config as cfg
from . import string_helper as str_helper
from .namespaces import samm_base_namespace, samm_output_namespace


class VSSConcepts(Enum):
    EMPTY = ""
    BELONGS_TO = "belongsToVehicleComponent"
    HAS_ATTRIBUTE = "hasStaticVehicleProperty"
    HAS_SIGNAL = "hasDynamicVehicleProperty"
    HAS_COMP_INST = "hasInstance"
    HOLDS_VALUE = "holdsState"
    PART_OF_VEHICLE = "partOfVehicle"
    PART_OF_VEH_COMP = "partOf"
    VEHICLE = "Vehicle"
    VEHICLE_ACT = "ActuatableVehicleProperty"
    VEHICLE_COMP = "VehicleComponent"
    VEHICLE_PROP = "DynamicVehicleProperty"
    VEHICLE_SIGNAL = "ObservableVehicleProperty"
    VEHICLE_STAT = "StaticVehicleProperty"

    def __init__(self, vss_name):
        self.ns = samm_output_namespace
        self.vsso_name = vss_name

    @property
    def uri(self):
        return URIRef(self.uri_string)

    @property
    def uri_string(self):
        return f"{self.ns}{self.value}"


class SammConcepts(Enum):
    ASPECT = "Aspect"
    CHARACTERISTIC = "Characteristic"
    CHARACTERISTIC_RELATION = "characteristic"
    DATA_TYPE = "dataType"
    DESCRIPTION = "description"
    ENTITY = "Entity"
    EVENTS = "events"
    EXAMPLE_VALUE = "exampleValue"
    NAME = "name"
    OPERATIONS = "operations"
    OPTIONAL = "optional"
    PAYLOAD_NAME = "payloadName"
    PREFERRED_NAME = "preferredName"
    PROPERTIES = "properties"
    PROPERTY = "Property"

    def __init__(self, vss_name):
        self.ns = f"{samm_base_namespace}:meta-model:{cfg.SAMM_VERSION}#"
        self.vsso_name = vss_name

    @property
    def uri(self):
        return URIRef(self.uri_string)

    @property
    def uri_string(self):
        return f"{self.ns}{self.value}"

    @property
    def samm_name(self):
        # Make sure that enum value is lc_first
        return f"samm:{str_helper.str_to_lc_first_camel_case(self.value)}"


class SammCConcepts(Enum):
    BASE_CHARACTERISTICS = "baseCharacteristic"
    BOOLEAN = "Boolean"
    CONSTRAINT = "constraint"
    DEFAULT_VALUE = "defaultValue"
    ENUM = "Enumeration"
    LIST = "List"
    MAX_VALUE = "maxValue"
    MEASUREMENT = "Measurement"
    MIN_VALUE = "minValue"
    QUANTIFIABLE = "Quantifiable"
    RANGE_CONSTRAINT = "RangeConstraint"
    SINGLE_ENTITY = "SingleEntity"
    STATE = "State"
    TIMESTAMP = "Timestamp"
    TRAIT = "Trait"
    UNIT = "unit"
    VALUES = "values"

    def __init__(self, vss_name):
        self.ns = f"{samm_base_namespace}:characteristic:{cfg.SAMM_VERSION}#"
        self.vsso_name = vss_name

    @property
    def uri(self):
        return URIRef(self.uri_string)

    @property
    def uri_string(self):
        return f"{self.ns}{self.value}"

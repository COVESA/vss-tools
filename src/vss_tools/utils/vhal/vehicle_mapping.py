# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass
from typing import List, Optional, Union

from dataclasses_json import LetterCase, dataclass_json


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True)
class VehicleMappingItem:
    """
    Represents a single vehicle mapping item.
    """

    name: str
    property_id: int
    area_id: int
    access: int
    change_mode: int
    unit: str
    source: str
    formula: Optional[str] = None
    comment: Optional[str] = None
    config_string: Optional[str] = None

    datatype: Optional[str] = None
    type: Optional[str] = None
    min: Optional[int] = None
    max: Optional[int] = None
    allowed: Optional[List[str]] = None
    default: Optional[Union[Union[int, str], Union[List[int], List[str]]]] = None
    deprecation: Optional[str] = None

    @property
    def vhal_group(self):
        """
        VHAL group component of the property ID.
        """
        return (self.property_id & 0xF0000000) >> 28

    @property
    def vhal_area(self):
        """
        VHAL area component of the property ID.
        """
        return (self.property_id & 0x0F000000) >> 24

    @property
    def vhal_type(self):
        """
        VHAL type component of the property ID.
        """
        return (self.property_id & 0x00FF0000) >> 16

    @property
    def vhal_id(self):
        """
        VHAL unique ID component of the property ID.
        """
        return self.property_id & 0x0000FFFF

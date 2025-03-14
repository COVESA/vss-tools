# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class VehicleMappingItem:
    """
    Represents a single vehicle mapping item.
    """

    name: str
    propertyId: int
    areaId: int
    access: int
    changeMode: int
    unit: str
    source: str
    formula: Optional[str] = None
    comment: Optional[str] = None
    configString: Optional[str] = None

    datatype: Optional[str] = None
    type: Optional[str] = None
    min: Optional[int] = None
    max: Optional[int] = None
    allowed: Optional[List[str]] = None
    default: Optional[int] = None
    deprecation: Optional[str] = None

    @property
    def vhalGroup(self):
        """
        VHAL group component of the property ID.
        """
        return (self.propertyId & 0xF0000000) >> 28

    @property
    def vhalArea(self):
        """
        VHAL area component of the property ID.
        """
        return (self.propertyId & 0x0F000000) >> 24

    @property
    def vhalType(self):
        """
        VHAL type component of the property ID.
        """
        return (self.propertyId & 0x00FF0000) >> 16

    @property
    def vhalId(self):
        """
        VHAL unique ID component of the property ID.
        """
        return self.propertyId & 0x0000FFFF

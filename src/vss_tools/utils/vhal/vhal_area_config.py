# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator
from pydantic.alias_generators import to_camel

from vss_tools.utils.vhal.area_constants import (
    VEHICLE_AREA_TYPES,
    VSS_POSITIONAL_KEYWORDS,
    get_area_id,
    get_explicit_area_id,
)
from vss_tools.utils.vhal.property_constants import VhalAreaType


class VhalAreaRuleItem(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        alias_generator=to_camel,
        extra="ignore",
        populate_by_name=True,
    )
    """
    Represents a single raw JSON mapping rule item.

    :param area_type: The target Android AOSP Area Type (e.g., "SEAT").
    :param map: Explicit overrides translating specific VSS instances to AOSP-specific strings.
                JSON comma-separated keys (e.g., "row1, left") are parsed into Python tuples.
    :param ignore: A deny-list of instances. If a VSS path contains any of these single words
                   (e.g., "front") or exact combinations (e.g., ["row1", "left"]), its
                   resolution will fall back to "GLOBAL".
    :param keep: An allow-list of instances. If populated, a VSS path MUST contain at least one
                 of these words or combinations. If it does not, it falls back to "GLOBAL".
    """
    area_type: str
    map: Dict[Tuple[str, ...], str] = Field(default_factory=dict)
    ignore: List[Union[str, List[str]]] = Field(default_factory=list)
    keep: List[Union[str, List[str]]] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce_string(cls, data: Any) -> Any:
        """
        Convert raw string into dictionary.
        """
        if isinstance(data, str):
            return {"area_type": data}
        return data

    @field_validator("map", mode="before")
    @classmethod
    def _parse_explicit_map(cls, v: Dict[str, str]) -> Dict[Tuple[str, ...], str]:
        parsed_map = {}
        for src, dest in v.items():
            key_tuple = tuple(s.strip().lower() for s in src.split(","))
            parsed_map[key_tuple] = dest.upper()

        return parsed_map

    @field_validator("area_type")
    @classmethod
    def _check_possible_area_types(cls, value: str) -> str:
        if value not in VEHICLE_AREA_TYPES:
            raise ValueError(f"area_type must be one of {VEHICLE_AREA_TYPES}, got {value}")
        return value


class VhalAreaConfigItem(BaseModel):
    """
    Internal container to hold a compiled area configuration - optimized runtime model for matching and resolving VSS
    paths.
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
    )
    pattern: str
    """
    The raw VSS path pattern from the JSON (e.g., "Vehicle.Cabin.Door.*").
    """
    depth: int
    """
    Number of segments in the pattern (determines priority for longest-match).
    """
    rule: VhalAreaRuleItem
    """
    The validated rule for this pattern.
    """
    compiled_regex: re.Pattern = Field(default=None, validate_default=True)
    """
    The precompiled regular expression generated from the pattern.
    """

    @field_validator("compiled_regex", mode="before")
    @classmethod
    def _compile_pattern(cls, _: re.Pattern | None, info: ValidationInfo) -> re.Pattern:
        pattern = info.data["pattern"]
        regex_str = pattern.replace(".", r"\.").replace("*", r".*")
        return re.compile(f"^{regex_str}$", flags=re.IGNORECASE)

    def resolve_area_type(self, path: str) -> Optional[Tuple[VhalAreaType, int]]:
        """
        Resolve the effective area_type for a given VSS path.

        Falls back to "GLOBAL" in any of the following cases:
          1. Any instance extracted from `path` is listed in `item.rule.ignore`, or (when `item.rule.keep` is non-empty)
             any extracted instance is NOT listed in `item.rule.keep`.
          2. If `item.rule.map` is non-empty: the extracted instances can be found as a key in `item.rule.map`, but the
             value in `item.rule.map` cannot be mapped at all.
          3. If `item.rule.map` is empty: the extracted instances cannot be mapped at all.

        :param path: the dotted VSS path string.
        :returns: The resolved area type and area ID or `None`.
        """
        match = self.compiled_regex.match(path)
        global_area = (VhalAreaType.VEHICLE_AREA_TYPE_GLOBAL, 0)
        if match is None:
            return None

        instances = tuple(p for p in path.lower().split(".") if p.lower() in VSS_POSITIONAL_KEYWORDS)
        instances_set = set(instances)
        rule = self.rule

        # Evaluate IGNORE / KEEP
        if rule.ignore and self.__matches_any(rule.ignore, instances_set):
            return global_area
        if rule.keep and not self.__matches_any(rule.keep, instances_set):
            return global_area

        # Evaluate explicit mapping
        area_id: int | None
        area_type = VhalAreaType.get(rule.area_type)
        explicit_map: Dict[Tuple[str, ...], str] = rule.map
        if explicit_map and instances in explicit_map:
            mapped = explicit_map.get(instances)
            if mapped is None:
                return global_area
            area_id = get_explicit_area_id(area_type, mapped)
            if area_id is None:
                return global_area
        elif instances:
            area_id = get_area_id(area_type, instances)
            if area_id is None:
                return global_area
        else:
            return global_area

        return area_type, area_id

    @staticmethod
    def __matches_any(sources: list[Union[str, List[str]]], targets: set[str]) -> bool:
        """
        Check whether any entry in `sources` matches `targets`.
        """
        for s in sources:
            if isinstance(s, list):
                if set(i for i in s).issubset(targets):
                    return True
            else:
                if s in targets:
                    return True
        return False

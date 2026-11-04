# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path

import yaml
from pydantic import ValidationError

from vss_tools import log
from vss_tools.model import ModelValidationException, VSSQuantity, VSSUnit
from vss_tools.vspec import deep_update


class MalformedDictException(Exception):
    pass


class DuplicatedUnitException(Exception):
    pass


def load_units_or_quantities(
    files: list[Path], class_type: type[VSSUnit | VSSQuantity]
) -> dict[str, VSSUnit | VSSQuantity]:
    # Accumulates the raw (pre-validation) dict per key across files, so that a key
    # redeclared in a later file only overrides the fields it actually mentions,
    # instead of replacing the whole definition (e.g. a later file adding a
    # 'string' allowed-datatype must not silently drop an earlier 'qudt:' block).
    raw_data: dict[str, dict] = {}
    data: dict[str, VSSUnit | VSSQuantity] = {}
    for file in files:
        content = yaml.safe_load(file.read_text())
        if not content:
            log.warning(f"{file}, empty")
            continue
        log.info(f"Loaded '{class_type.__name__}', file={file.absolute()}, elements={len(content)}")
        for k, v in content.items():
            k_original = k
            k = k.lower()
            if v is None:
                raise MalformedDictException(f"'{class_type.__name__}', '{k}' is 'None'")
            # For VSSUnit, inject the canonical key (original casing) from the YAML key
            if class_type == VSSUnit and isinstance(v, dict):
                v["key"] = k_original
            if k in raw_data:
                log.warning(
                    f"'{class_type.__name__}', merging additional definition of '{k}' from '{file}' "
                    "(fields not mentioned there are kept from the earlier definition)."
                )
                deep_update(raw_data[k], v)
            else:
                raw_data[k] = v
            try:
                data[k] = class_type(**raw_data[k])
            except ValidationError as e:
                raise ModelValidationException(k, e) from None
    return data


def load_units(unit_files: list[Path]) -> dict[str, VSSUnit]:
    units: dict[str, VSSUnit] = load_units_or_quantities(unit_files, VSSUnit)  # type: ignore[assignment]
    _validate_unique_unit_descriptions(units)
    return units


def _validate_unique_unit_descriptions(units: dict[str, VSSUnit]) -> None:
    """
    Validate that unit descriptions are globally unique.

    Args:
        units: Dictionary of loaded units

    Raises:
        DuplicatedUnitException: If duplicate unit descriptions are found
    """
    # <unit>: <first-key-using-it>
    unit_defs: dict[str, str] = {}
    for key, value in units.items():
        unit = value.unit
        if not unit:
            continue
        if unit in unit_defs:
            raise DuplicatedUnitException(f"Duplicated unit: '{value.unit}'. Used by: {[unit_defs[unit], key]}")
        unit_defs[unit] = key


def load_quantities(quantities: list[Path]) -> dict[str, VSSQuantity]:
    return load_units_or_quantities(quantities, VSSQuantity)  # type: ignore[return-value]

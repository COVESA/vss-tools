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
from vss_tools.vspec.model import ModelValidationException, VSSQuantity, VSSUnit


class UnitQuantityRedefinitionException(Exception):
    pass


class MalformedDictException(Exception):
    pass


def load_units_or_quantities(
    files: list[Path], class_type: type[VSSUnit | VSSQuantity]
) -> dict[str, VSSUnit | VSSQuantity]:
    data = {}
    for file in files:
        content = yaml.safe_load(file.read_text())
        if not content:
            log.warning(f"{file}, empty")
            continue
        log.info(f"Loaded '{class_type.__name__}', file={file.absolute()}, elements={len(content)}")
        for k, v in content.items():
            if v is None:
                log.error(f"'{class_type.__name__}', '{k}' is 'None'")
                raise MalformedDictException()
            if k in data:
                log.error(f"'{class_type.__name__}', redefinition of '{k}'")
                raise UnitQuantityRedefinitionException()
            try:
                data[k] = class_type(**v)
            except ValidationError as e:
                raise ModelValidationException(k, e) from None
    return data


def load_units(unit_files: list[Path]) -> dict[str, VSSUnit]:
    return load_units_or_quantities(unit_files, VSSUnit)  # type: ignore[return-value]


def load_quantities(quantities: list[Path]) -> dict[str, VSSQuantity]:
    return load_units_or_quantities(quantities, VSSQuantity)  # type: ignore[return-value]

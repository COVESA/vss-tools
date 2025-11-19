# Copyright (c) 2025 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel


class StrictExceptions:
    def __init__(self) -> None:
        self.names: set[str] = set()
        self.attributes: set[str] = set()


class StrictOption(str, Enum):
    NAME_STYLE = "name-style"
    UNKNOWN_ATTRIBUTE = "unknown-attribute"


class StrictException(BaseModel):
    fqn: str
    options: set[StrictOption] | None = None


def load_strict_exceptions(file: Path | None) -> StrictExceptions:
    exceptions = StrictExceptions()

    if not file:
        return exceptions

    with open(file) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid exceptions file format (not a dict): {file}")

    key: str
    value: set[StrictOption] | None
    for key, value in data.items():
        exception = StrictException(fqn=key, options=value)

        if exception.options:
            for e in exception.options:
                if e == StrictOption.NAME_STYLE:
                    exceptions.names.add(exception.fqn)
                elif e == StrictOption.UNKNOWN_ATTRIBUTE:
                    exceptions.attributes.add(exception.fqn)
        else:
            exceptions.names.add(exception.fqn)
            exceptions.attributes.add(exception.fqn)

    return exceptions

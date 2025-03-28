# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
from typing import Any

import pydantic
import pytest
from vss_tools.model import VSSDataDatatype


@pytest.mark.parametrize(
    "data, ok",
    [
        ({"datatype": "foo"}, False),
        ({"datatype": "int8"}, True),
        ({"datatype": "int8", "arraysize": 1}, False),
        ({"datatype": "int8[]", "arraysize": 1}, True),
        ({"datatype": "int8", "min": -300}, False),
        ({"datatype": "int8", "min": "foo"}, False),
        ({"datatype": "int8", "min": -100}, True),
        ({"datatype": "uint8", "max": -2}, False),
        ({"datatype": "uint8", "max": 100}, True),
        ({"datatype": "string", "max": 100}, False),
        ({"datatype": "uint8", "max": 100, "default": 110}, False),
        ({"datatype": "uint8", "max": 100, "default": 90}, True),
        ({"datatype": "uint8", "min": 10, "default": 5}, False),
        ({"datatype": "uint8", "min": 10, "default": 10}, True),
        ({"datatype": "uint8", "default": 300}, False),
        ({"datatype": "uint8", "default": 200}, True),
        ({"datatype": "boolean", "default": True}, True),
        ({"datatype": "uint8[]", "arraysize": 1, "default": [1, 2]}, False),
        ({"datatype": "uint8[]", "arraysize": 2, "default": [1, 2]}, True),
        ({"datatype": "uint8", "allowed": [1, 2, 3], "default": 4}, False),
        ({"datatype": "uint8", "allowed": [1, 2, 3], "default": 3}, True),
        ({"datatype": "uint8", "allowed": [1, "foo"]}, False),
        ({"datatype": "uint8", "allowed": [1, 2]}, True),
        ({"datatype": "uint8", "allowed": [1, 2, 3], "min": 3}, False),
        ({"datatype": "uint8", "allowed": [1, 2, 3], "max": 3}, False),
        ({"datatype": "uint8", "pattern": "xy"}, False),
        ({"datatype": "string", "pattern": "xy"}, True),
        ({"datatype": "string", "pattern": "x.*", "default": "ay"}, False),
        ({"datatype": "string", "pattern": "x.*", "default": "xy"}, True),
        ({"datatype": "string", "pattern": "x.*", "allowed": ["ay"]}, False),
        ({"datatype": "string", "pattern": "x.*", "allowed": ["xy", "xz"]}, True),
    ],
)
def test_vss_data_datatype(data: dict[str, Any], ok: bool) -> None:
    data.update({"type": "attribute", "description": "test"})
    data_ok = True
    try:
        VSSDataDatatype(**data)
    except pydantic.ValidationError as e:
        data_ok = False
        print(e)

    assert ok == data_ok

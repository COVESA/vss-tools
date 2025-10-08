# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
import re
from typing import Any


def getattr_nn(o: object, name: str, default: Any | None = None) -> Any:
    """
    Wraps getattr() but will also use 'default' if result is None
    """
    result = getattr(o, name, default)
    if result is None and default is not None:
        result = default
    return result


def camel_case(st):
    """Camel case string conversion"""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", st)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return re.sub(r"(?:^|_)([a-z])", lambda x: x.group(1).upper(), s2)


def camel_back(st):
    """Camel back string conversion"""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", st)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return re.sub(r"_([a-z])", lambda x: x.group(1).upper(), s2)


def str_to_screaming_snake_case(text: str) -> str:
    """Converts a string to screaming snake case (i.e., CAPITAL LETTERS)"""
    text = re.sub(r"[^a-zA-Z0-9]", " ", text)
    words = text.split()
    return "_".join(word.upper() for word in words)


def to_snake(name: str) -> str:
    # PascalCase -> snake_case, hyphens/spaces -> underscores, collapse
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"[^0-9a-zA-Z_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s.lower()

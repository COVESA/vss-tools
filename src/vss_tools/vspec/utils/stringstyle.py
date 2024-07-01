#!/usr/bin/env python3

# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import re


def camel_case(st):
    """Camel case string conversion"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', st)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    return re.sub(r'(?:^|_)([a-z])', lambda x: x.group(1).upper(), s2)


def camel_back(st):
    """Camel back string conversion"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', st)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    return re.sub(r'_([a-z])', lambda x: x.group(1).upper(), s2)

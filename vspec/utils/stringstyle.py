#!/usr/bin/env python3

#
#
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

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
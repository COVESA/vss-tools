#!/usr/bin/env python3
#
# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
#
# Initialize static IDs.
#

import sys
import vspec2x

if __name__ == "__main__":
    vspec2x.main(["--format", "idgen"] + sys.argv[1:])

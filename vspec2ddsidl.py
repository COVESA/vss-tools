#!/usr/bin/env python3
#
#
# (c) 2022 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec2idl wrapper for vspec2x
#

import sys
import vspec2x

if __name__ == "__main__":
    vspec2x.main(["--format", "idl"]+sys.argv[1:])

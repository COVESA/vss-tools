#!/usr/bin/env python3

#
# (C) 2022 Geotab Inc
# (C) 2018 Volvo Cars
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec file to a platform binary format.
#

import sys
import vspec2x

if __name__ == "__main__":
    vspec2x.main(["--format", "binary"]+sys.argv[1:])

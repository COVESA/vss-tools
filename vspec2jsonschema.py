#!/usr/bin/env python3
#
#
# Convert vspec2jsonschema wrapper for vspec2x
#

import sys
import vspec2x

if __name__ == "__main__":
    vspec2x.main(["--format", "jsonschema"]+sys.argv[1:])

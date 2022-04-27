#!/usr/bin/env python3

# (c) 2022 BMW Group
# (C) 2016 Jaguar Land Rover
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec file to FrancaIDL spec.
#

import sys
import vspec2x

if __name__ == "__main__":
    vspec2x.main(["--format", "franca"]+sys.argv[1:])
#!/usr/bin/env python3

# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec files to various other formats
#

import logging

def initLogging():
    """
    Initialize logging
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')

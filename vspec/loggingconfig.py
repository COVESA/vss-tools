#!/usr/bin/env python3

# (c) 2022 BMW Group
# (c) 2022 Robert Bosch GmbH
# (c) 2016 Jaguar Land Rover
#
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
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

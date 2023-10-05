
# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import argparse


def remove_options_argparse(parser: argparse.ArgumentParser, options) -> None:
    # ToDo: this allows removing arguments from argparse but involves accessing protected members
    #  also when removing '--format' it removes the positional argument vspec_file
    for option in options:
        for action in parser._actions:
            if (
                vars(action)["option_strings"]
                and vars(action)["option_strings"][0] == option
            ):
                parser._handle_conflict_resolve(action, [(option, action)])
                break

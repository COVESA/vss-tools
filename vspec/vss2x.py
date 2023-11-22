#!/usr/bin/env python3

# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from abc import ABC, abstractmethod
import argparse
from typing import Optional
from vspec.model.vsstree import VSSNode
from vspec.vspec2vss_config import Vspec2VssConfig


class Vss2X(ABC):
    """
    Abstract class for something that takes a VSS model as input
    (signal tree plus optionally a type tree)
    and does "something". For now it is assumed that output is either files
    or text output.
    The generator may use both command line config as well as specific configs used for
    creating the VSS model to control the generation.
    """

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.description = "This generator does not support any additional arguments."

    @abstractmethod
    def generate(self, config: argparse.Namespace, signal_root: VSSNode, vspec2vss_config: Vspec2VssConfig,
                 data_type_root: Optional[VSSNode] = None) -> None:
        """
        Previously called export, but changing to a more generic name.
        Must be defined by the tool.
        """
        pass

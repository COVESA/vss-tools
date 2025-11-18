# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

"""
Generic string conversion utilities.

This module provides reusable string preprocessing functions that can be used
across different modules for consistent text transformation and normalization.
"""

from typing import Callable


def clean_name_for_conversion(name: str) -> str:
    """Clean name by replacing dots and dashes with underscores for standard case conversion."""
    return name.replace(".", "_").replace("-", "_")


def handle_fqn_conversion(name: str, case_func: Callable[..., str], delimiters: str = " -_") -> str:
    """
    Handle fully qualified names by converting each part separately and joining with underscores.

    Args:
        name: The FQN string to convert (e.g., "Vehicle.Body.Lights")
        case_func: The case conversion function to apply to each part
        delimiters: Delimiters to pass to the case conversion function

    Returns:
        Converted FQN with underscores between parts
    """
    # Split by dots and convert each part individually
    parts = [case_func(part, delimiters=delimiters) for part in name.split(".") if part]
    return "_".join(parts)


def add_digit_prefix_if_needed(converted: str) -> str:
    """Add underscore prefix if name starts with a digit (for enum values)."""
    if converted and converted[0].isdigit():
        return f"_{converted}"
    return converted

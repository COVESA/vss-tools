# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0


def str_to_lc_first(string_to_update: str) -> str:
    """Helper function to convert string_to_update to a lower case first string and preserve its remaining case.

       For example - input like:

            - SomeStringToUpdate will be converted to: someStringToUpdate

            - SomeOTHERstringToUpdate will be converted to: someOTHERstringToUpdate

    Args:
        string_to_update (str): The string to be updated.

    Returns:
        str: Returns a first character lower case string, with untouched remainder of the string_to_update.
    """

    if len(string_to_update) > 0:
        return f"{string_to_update[0].lower()}{string_to_update[1:]}"
    else:
        return string_to_update


def str_to_uc_first(string_to_update: str):
    """Helper function to convert string_to_update to an upper case first string and preserve its remaining case.

       For example - input like:

            - someStringToUpdate will be converted to: SomeStringToUpdate

            - someOTHERstringToUpdate will be converted to: SomeOTHERstringToUpdate

        NOTE: in comparison with the Python function: capitalize(), which will return: Somestringtoupdate,
              this one will preserve the remainder of the string_to_update untouched.

    Args:
        string_to_update (str): The string to be updated.

    Returns:
        _type_: Returns a first character upper case string, with untouched remainder of the string_to_update.
    """

    if len(string_to_update) > 0:
        return f"{string_to_update[0].upper()}{string_to_update[1:]}"
    else:
        return string_to_update


# Helper function, which will make sure that passed string_to_update
# will be converted in camel case,
# based on this guide: https://google.github.io/styleguide/javaguide.html#s5.3-camel-case
def str_to_camel_case(string_to_update: str) -> str:
    updated_str = ""

    string_to_update_length = len(string_to_update)

    for char_index in range(0, string_to_update_length, 1):
        char_to_read = string_to_update[char_index]

        if char_to_read.isnumeric() or len(updated_str) == 0:
            # Read numeric characters and first one as they are
            updated_str = updated_str + char_to_read

        else:
            # Handle any subsequent character in camel case
            prev_char = updated_str[char_index - 1]

            next_index = char_index + 1
            if string_to_update_length == next_index:
                # Rollback next_index as we will get index out of boundaries error.
                # In this case the next_char will be same as char_to_read.
                next_index = next_index - 1

            next_char = string_to_update[next_index]

            if (
                char_to_read.isupper()
                and (prev_char.isupper() or prev_char.islower() or len(prev_char.strip()) > 0)
                and (next_char.isupper() or next_char.isnumeric())
            ):
                # Convert case of char_to_read from UPPER to LOWER
                char_to_read = char_to_read.lower()

            elif len(prev_char.strip()) == 0 and next_char.islower():
                # Convert case of char_to_read from LOWER to UPPER
                char_to_read = char_to_read.upper()

            # ELSE: read char_to_read as it is

            updated_str = updated_str + char_to_read

    # Make sure to remove any empty space from updated_str
    return updated_str.replace(" ", "")


def str_to_uc_first_camel_case(string_to_update: str):
    # Make sure that first character of string_to_update is UPPER CASE
    string_to_update = str_to_uc_first(string_to_update)

    # Return converted to camelCase string
    return str_to_camel_case(string_to_update)


def str_to_lc_first_camel_case(string_to_update: str) -> str:
    # Make sure that first character of string_to_update is UPPER CASE
    string_to_update = str_to_lc_first(string_to_update)

    # Return converted to camelCase string
    return str_to_camel_case(string_to_update)


def str_camel_case_split(string_to_update: str) -> str:
    updated_str = ""

    string_to_update_length = len(string_to_update)

    for char_index in range(0, string_to_update_length, 1):
        char = string_to_update[char_index]

        if len(updated_str) == 0:
            # Read first character as it is
            updated_str = updated_str + char

        else:
            # Read next character so to define whether to split or not
            # NOTE: abbreviations in ALL UPPER CASE should not be split
            next_index = char_index + 1
            if string_to_update_length == next_index:
                next_index = next_index - 1
            next_char = string_to_update[next_index]

            if char.isupper() and next_char.islower():
                updated_str = updated_str + " " + char
            else:
                updated_str = updated_str + char

    return updated_str

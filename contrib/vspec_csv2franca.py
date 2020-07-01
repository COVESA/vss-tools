#!/usr/bin/python3
# vim: nw ts=4 noet tw=0

#
# (C) 2020 GENIVI Alliance
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
# Concert vspec file to Franca interfaces
#

import sys
import getopt
import re
import csv

# SETTINGS
YEAR = 2020
DEBUG_ENABLED = False
indentation_string = "    "  # 4 spaces at the moment

# The license of the output can be changed depending on the input database
# being used. The standard VSS database is however licensed using MPLv2 and
# the conditions therein should be followed when creating derivative
# works.  (This typically means to keep the same license on the output, but
# you may delve into the details)
license = """// This program is licensed under the terms and conditions of the
// Mozilla Public License, version 2.0.  The full text of the
// Mozilla Public License is at https://www.mozilla.org/MPL/2.0/
"""

# Handle indentation.  All operations are kept here, but depend on a shared
# global variable
INDENTATION_STRING = "    "  # 4 spaces at the moment
indentlevel = 0 # It is easiest to keep this variable in global scope

franca_file=""

def prefix():
   return INDENTATION_STRING * indentlevel

def indent():
    global indentlevel 
    indentlevel += 1

def unindent():
    global indentlevel 
    indentlevel -= 1

def usage():
    print("Usage:", sys.argv[0], "-p <package>  -n <interface-name> -s <signal_pattern_match> -P <provider-name> [-t strip-prefix] [-v vss-version] [-V if-version] <vspec-CSV-file franca_file")
    print("  vspec-CSV-file       VSS database in the CSV format from vspec2csv script")
    print("  -p package           Fully qualified Franca package name (mandatory, once, arbitrary)")
    print("  -n interface         Interface name (mandatory, once, should match namespace hierarchy (i.e. it should be a VSS Branch name))")
    print("  -s signals           Pattern for signals to include (mandatory, once or repeated, Case-Sensitive, full names or use * for wildcard)")
    print("  -P provider          Name of the service component (a.k.a. Provider) in the SOME/IP deployment file (mandatory, just provide dummy if SOME/IP not used))")
    print("  -t strip_prefix      Part of the VSS hierarchy to strip away from namespacing (optional, but this is often set to 'Vehicle')")
    print("  -v version           VSS version/variant (string, optional, should typically match the used VSS version)")
    print("  -V major,minor       Franca interface version (mandatory, write *two numbers* with a *comma* between)")
    print()
    print(" vspec-CSV-file        The vehicle specification file to parse.  Must be the CSV format")
    print(" franca_file           The (.fidl) file to output the Franca IDL spec to. A .fdepl file with similar name is created automatically.")
    sys.exit(255)

def debug(s):
    if DEBUG_ENABLED:
        print(s)

def tree_matches(fqn, interface):
    if fqn.startswith(interface):
        return True
    else:
        debug("No match for TREE %s against %s" % (fqn, interface))

def signal_matches(fqn, signal_patterns):
    # To prepare regexps we need to replace "*" with ".*" but
    # also escape the ".", making it an explicit "."
    for p in signal_patterns:
        p = p.replace(".", '\\.')   # Replace . with explicit .
        p = p.replace("*", ".*")    # Then for every *, use .*
        if re.search(p, fqn):
            debug("%s matches pattern %s" % (fqn, p))
            return True
        else:
            debug("No match for SIGNAL %s against %s" % (fqn, p))
    return False

def convert_to_franca_type(t):
    tbl={'uint8': 'UInt8',
         'uint16': 'UInt16',
         'uint32': 'UInt32',
         'uint64': 'UInt64',
         'sint8': 'Int8',
         'sint16': 'Int16',
         'sint32': 'Int32',
         'sint64': 'Int64',
         'float':  'Float',
         'boolean':  'Boolean',
         'string': 'String',
         'enum': 'TODO-ENUM-UNSUPPORTED'
         }
    try:
        return tbl[t]
    except KeyError as e:
        return 'UNSUPPORTED_TYPE'

# This can be replaced by str.removeprefix in Python 3.9+
# but I'm using an older python...
def remove_at_beginning(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

# Convert a A.B.C hierarchy to A_B_C, which is a permitted Franca IDL identifier
# And remove prefix that should be stripped (-t flag)
def flatten_hierarchical_name(dotname):
    return remove_at_beginning(dotname, strip).replace('.','_')

attribute_collection = []
def generate_attribute(fqn, datatype, interface):
    global attribute_collection
    # The trick here is to remove the "parent" path that leads up to the
    # signal from the generated name, because it is covered by the
    # namespace of the Interfaces (one or several).
    # In a typical case only the leaf node name remains, but if the user
    # requested it that way, some part of the branch hierarchy may remain
    # in the generated attribute name, each part separated by underscore (_).

    parent_path = interface + '.'

    # Remove the parent-path (parent namespaces) from result so that only the
    # necessary path specifier is left.  Also, if there is any hierarchy left
    # (in other words any "." left) then replace it with underscore.
    attr_name = flatten_hierarchical_name(fqn.replace(parent_path,""))
    attribute_collection.append(attr_name) # Remember all processed attributes
    return "attribute %s %s" % (convert_to_franca_type(datatype), attr_name)

if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args= getopt.getopt(sys.argv[1:], "I:i:p:P:t:n:s:v:V:")

    # Always search current directory for include_file
    package = None
    strip = "." # Default
    signal_patterns=[]
    vss_version = "version not specified"
    interface_version = ""
    for o, a in opts:
        # This just for "compatibility" with other converters:
        if o == "-I":
            print("WARNING: -I flag is not used in this command!\n")
        elif o == "-i":
            print("WARNING: -i flag is not used in this command!\n")
        elif o == "-p":
            package = a
        elif o == "-n":
            interface = a
        elif o == "-s":
            signal_patterns.append(a)
        elif o == "-t":
            if a.endswith('.'):
               strip = a
            else:
               strip = a + '.'
            debug("strip is %s" % strip)
        elif o == "-P":
            provider = a
        elif o == "-v":
            vss_version = a
        elif o == "-V":
            if re.match("[\d]+,[\d]+", a):
                interface_version = a
            else:
                print("ERROR: Franca interface version (-V) should be specified with major,minor number (use numbers, comma, no space)")
                usage()
        else:
            usage()

    if package == None:
        print("ERROR: Must specify package name (-p)")
        usage()

    if len(interface) == 0:
        print("ERROR: Must specify at least one interface name (-n)")
        usage()

    if len(signal_patterns) == 0:
        print("ERROR: Must specify at least one signal pattern match (-s)")
        usage()

    if len(args) != 2:
        print("Please specify two (2) file arguments at the end:  Input VSS file in CSV format, and output Franca IDL file")
        print("Length args is: ")
        print(len(args))
        usage()

    try:
        csv_in = open (args[0], "r")
    except OSError as e:
        print("Error opening file %s for reading" % args[0])
        print("Error: {}".format(e))
        exit(254)

    try:
        franca_file = args[1]
        franca_out = open (franca_file, "w")
    except OSError as e:
        print("Error opening file %s for writing?" % franca_file)
        print("Error: {}".format(e))
        exit(255)


    print(signal_patterns)

    attribute_count = 0

    franca_out.write(
"""// Copyright (C) {} 
// Contributors to Vehicle Signal Specification
// (https://gitub.com/GENIVI/vehicle_signal_specification)
//
{}

// Vehicle signal attributes generated from VSS specification version FIXME

package {}

""".format(YEAR, license, package))

    franca_out.write(prefix() + "interface {} {{\n".format(flatten_hierarchical_name(interface)))
    indent()

    if interface_version != "":
        major=interface_version[0:interface_version.find(",")]
        minor=interface_version[interface_version.find(",")+1:]
        franca_out.write(prefix() + "version {{ major {}, minor {} }}\n".format(major, minor))

    franca_out.write(prefix() + 'const UTF8String VSS_INTERFACE_VERSION = "{}"\n'.format(vss_version))

    for row in csv.DictReader(csv_in):
        # Get Fully qualified node name (fqn) and type from respective
        # column
        fqn = row['Signal']
        datatype = row['DataType']

        # This limits any matches to the specified subtree, and filters out
        # only leaf nodes.  Each step is separate for clarity:
        if row['Type'] != 'branch':
            if tree_matches(fqn, interface):
                if signal_matches(fqn, signal_patterns):
                    franca_out.write(prefix() + generate_attribute(fqn, datatype, interface) + "\n")
                    attribute_count += 1
        else:
            debug("No match for %s" % fqn)

    # Close the open brace
    unindent()
    franca_out.write(prefix() + "}\n")

    franca_out.write("""
// End of file
""")

if attribute_count == 0:
    print("WARNING: No signals matched -- adjust signal match pattern or interface hierarchy (NOTE, hierarchy must match in name and order to the branch names).  All matches are case-sensitive.)")

print(attribute_count)

franca_out.close()


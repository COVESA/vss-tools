#!/usr/bin/python3

#
# (C) 2019 Jaguar Land Rover
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Concert vspec file to C header and source file.
#

import sys
import os
import vspec
import getopt
import hashlib
import json
def usage():
    print("Usage:", sys.argv[0], "[-I include-dir] ... [-i prefix:id-file] vspec-file output-header-file output-macro-file")
    print("  -I include-dir       Add include directory to search for included vspec")
    print("                       files. Can be used multiple timees.")
    print()
    print("  -i prefix:uuid-file  File to use for storing generated UUIDs for signals with")
    print("                       a given path prefix. Can be used multiple times to store")
    print("                       UUIDs for signal sub-trees in different files.")
    print()
    print(" output-header-file    The file to output the signal spec-encoding header info to.")
    sys.exit(255)


type_map =  {
    "int8": "VSS_INT8",
    "uint8": "VSS_UINT8",
    "int16": "VSS_INT16",
    "uint16": "VSS_UINT16",
    "int32": "VSS_INT32",
    "uint32": "VSS_UINT32",
    "int64": "VSS_INT64",
    "uint64": "VSS_UINT64",
    "float": "VSS_FLOAT",
    "double": "VSS_DOUBLE",
    "bool": "VSS_BOOLEAN",
    "boolean": "VSS_BOOLEAN",
    "string": "VSS_STRING",
    "stream": "VSS_STREAM",
    "na": "VSS_NA"
}

element_map = {
    "attribute": "VSS_ATTRIBUTE",
    "branch": "VSS_BRANCH",
    "sensor": "VSS_SENSOR",
    "actuator": "VSS_ACTUATOR",
    "rbranch": "VSS_RBRANCH",
    "element": "VSS_ELEMENT"
}

signal_count = 0

def emit_signal(signal_name, vspec_data):
    try:
        index = vspec_data['_index_'];
        parent_index = vspec_data['_parent_index_'];
        uuid = vspec_data['uuid'];
        elem_type = element_map[vspec_data['type'].lower()];
    except KeyError as e:
        print("Missing in vspec element key: {}".format(e))
        print("Path: {}".format(vspec_data['_signal_path_']))
        exit(255)

    data_type = 'VSS_NA'
    unit = ''
    min = 'VSS_LIMIT_UNDEFINED' # not defined.
    max = 'VSS_LIMIT_UNDEFINED' # not defined.
    desc = ''
    enum = '{ 0 }'
    sensor = ''
    actuator = ''
    children = '{ 0 }'

    if 'datatype' in vspec_data:
        try:
            data_type = type_map[vspec_data['datatype'].lower()];
        except KeyError as e:
            print("Illegal data type: {}".format(e))
            print("Signal: {}".format(vspec_data['_signal_path_']))
            print("Try: int8 uint8 int16 uint16 int32 uint32 int64 uint64")
            print("     float double string boolean stream")
            exit(255)

    if 'unit' in vspec_data:
        unit = vspec_data['unit']

    if 'min' in vspec_data:
        if not elem_type in [ "int8", "uint8", "int16", "uint16", "int32" , "uint32", "double", "float"]:
            min = vspec_data['min']
        else:
            print("Signal {}: Ignoring specified min value for type {}".format(vspec_data['_signal_path_'], data_type))


    if 'max' in vspec_data:
        if not elem_type in [ "int8", "uint8", "int16", "uint16", "int32" , "uint32", "double", "float"]:
            max = vspec_data['max']
        else:
            print("Signal {}: Ignoring specified max value for type {}".format(vspec_data['_signal_path_'], data_type))


    if 'description' in vspec_data:
        desc = vspec_data['description']

    children = '{ '
    if 'children' in vspec_data:
        for k, v in sorted(vspec_data['children'].items(), key=lambda item: item[0]):
            children += '&vss_signal[{}], '.format(v['_index_'])

    children += ' 0 }'


    enum = '{ '
    if 'enum' in vspec_data:
        for enum_elem in vspec_data['enum']:
            enum += '"{}", '.format(enum_elem)
    enum += ' 0 }'

    if 'sensor' in vspec_data:
        sensor = vspec_data['sensor']

    actuator = ''
    if 'actuator' in vspec_data:
        actuator = vspec_data['actuator']

    if parent_index == -1:
        parent = "0"
    else:
        parent = "&vss_signal[{}]".format(vspec_data['_parent_index_'])

    return f'    {{ {index}, {parent}, (vss_signal_t*[]) {children}, "{signal_name}", "{uuid}", {elem_type}, {data_type}, "{unit}", {min}, {max}, "{desc}", (const char*[]) {enum}, "{sensor}", "{actuator}", (void*) 0 }},\n'



#
# Return a blob of self's and all childrens' uuid value
#
# This is used to calculate a unique signature for the entire spec.
#
def generate_hash(vspec_data, sha256hash):
    for k, v in sorted(vspec_data.items(), key=lambda item: item[0]):
        sha256hash.update(v['uuid'].encode("utf-8"))
        if (v['type'] == 'branch'):
            generate_hash(v['children'], sha256hash)


def add_signal_index(vspec_data,  index = 0, parent_index = -1):
    for k, v in sorted(vspec_data.items(), key=lambda item: item[0]):
        v['_index_'] = index;
        index += 1
        v['_parent_index_'] = parent_index;

        if (v['type'] == 'branch'):
            index = add_signal_index(v['children'], index, v['_index_'])

    return index

def add_signal_path(vspec_data, parent_signal = ""):
    for k, v in sorted(vspec_data.items(), key=lambda item: item[0]):
        if (len(parent_signal) > 0):
            signal_path = parent_signal + "_" + k
        else:
            signal_path = k

        v['_signal_path_'] = signal_path

        if (v['type'] == 'branch'):
            add_signal_path(v['children'], signal_path)


def generate_binary_sha(sha256_hex):
    res = ''
    while len(sha256_hex) > 0:
        hex_byte = sha256_hex[0:1].zfill(2)
        sha256_hex = sha256_hex[2:]
        res += '\\0x{}'.format(hex_byte)

    return res

def generate_source(vspec_data):
    global signal_count
    sig_decl = ''
    for k, v in sorted(vspec_data.items(), key=lambda item: item[0]):
        sig_decl += emit_signal(k, v)
        signal_count += 1

        if (v['type'] == 'branch'):
            sig_decl += generate_source(v['children'])

    return sig_decl


def generate_header(vspec_data):
    macro = ''
    for k, v in sorted(vspec_data.items(), key=lambda item: item[0]):
        macro += '#define VSS_{}() vss_get_signal_by_index({})\n'.format(v['_signal_path_'],v['_index_'])

        if (v['type'] == 'branch'):
            macro += generate_header(v['children'])

    return macro


if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args= getopt.getopt(sys.argv[1:], "I:i:")

    # Always search current directory for include_file
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        elif o == "-i":
            id_spec = a.split(":")
            if len(id_spec) != 2:
                print("ERROR: -i needs a 'prefix:id_file' argument.")
                usage()

            [prefix, file_name] = id_spec
            vspec.db_mgr.create_signal_uuid_db(prefix, file_name)
        else:
            usage()

    if len(args) != 3:
        usage()

    try:
        tree = vspec.load(args[0], include_dirs)
    except vspec.VSpecError as e:
        print("Error: {}".format(e.__str__()))
        exit(255)

    add_signal_index(tree)
    add_signal_path(tree)

    # Generate a hash
    sha256hash = hashlib.sha256()
    generate_hash(tree, sha256hash)

    # Generate header file

    with open (args[1], "w") as hdr_out:
        hdr_out.write("// Automatically generated by vspec2c.py (https://github.com/GENIVI/vehicle_signal_specification)\n")
        hdr_out.write("// Do not edit\n\n")
        hdr_out.write("// SHA256 hash of vehicle spec\n")
        hdr_out.write("""const char vss_sha256_signature[] = "{}";""".format(sha256hash.hexdigest()))
        hdr_out.write("\n\n// VSS Signal Array\n")
        hdr_out.write("vss_signal_t vss_signal[] = {\n")
        hdr_out.write(generate_source(tree))
        hdr_out.write("};\n")
        hdr_out.write("\n\n// VSS Signal Array size\n")
        hdr_out.write("const int vss_signal_count = {};\n".format(signal_count));

    with open (args[2], "w") as macro_out:
        macro_out.write("// Automatically generated by vspec2c.py (https://github.com/GENIVI/vehicle_signal_specification)\n")
        macro_out.write("// Do not edit\n\n")
        macro_out.write("// Macro definitions\n")
        macro_out.write(generate_header(tree))

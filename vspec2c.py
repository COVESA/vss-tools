#!/usr/bin/python3

#
# (C) 2016 Jaguar Land Rover
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
#
# C Header file template code.
#
vss_hdr_template = """
//
// Auto generated code by vspec2c.py
// See github.com/GENIVI/vehicle_signal_specification for details.
//
#include <stdint.h>
#include <float.h>
#include <errno.h>
typedef enum _vss_data_type_e {
    VSS_INT8 = 0,
    VSS_UINT8 = 1,
    VSS_INT16 = 2,
    VSS_UINT16 = 3,
    VSS_INT32 = 4,
    VSS_UINT32 = 5,
    VSS_DOUBLE = 6,
    VSS_FLOAT = 7,
    VSS_BOOLEAN = 8,
    VSS_STRING = 9,
    VSS_STREAM = 10,

    // Usd for VSS_BRANCH and VSS_RBRANCH etnries
    VSS_NA = 11,
} vss_data_type_e;

typedef enum _vss_element_type_e {
    VSS_ATTRIBUTE = 0,
    VSS_BRANCH = 1,
    VSS_SENSOR = 2,
    VSS_ACTUATOR = 3,
    VSS_RBRANCH = 4,
    VSS_ELEMENT = 5,
} vss_element_type_e;

// A single signal.
// The vss_signal[] array hosts all the signals from the specification.
// The array is pre-populated and initialized at build time, meaning
// that it can be accessed directly from a program without any
// further initialization.
//
typedef struct _vss_signal_t {
    // Unique index for a signal. Based on the signal's position
    // in the array.
    //
    const int index;

    // Pointer to parent signal. Null if this is root signal
    //
    const struct _vss_signal_t* parent;

    // Pointer to null-termianted array of all children.
    // Traverse using children[index].
    // If there are no children, then children[0] == 0
    //
    struct _vss_signal_t** children;

    // Name of this signal or branch.
    // Use vss_get_signal_path() to get complete path to a signal.
    // Always set.
    //
    const char *name;

    // UUID of signal or branch.
    // Always set.
    //
    const char *uuid;

    // Element type of signal
    // Use this to determine if this is a signal or a branch.
    //
    const vss_element_type_e element_type;

    // Data type of signal.
    // Will be set to VSS_NA if this is a branch.
    //
    const vss_data_type_e data_type;

    // Unit type of signal.
    // Set to "" if not definedf.
    //
    const char *const unit_type;

    // Minimum allowed value for a signal.
    // Use min_val.d if signal.data_type is VSS_FLOAT or VSS_DOUBLE.
    // Use min_val.i if signal.data_type is one of the integer types.
    //
    const union  {
        int64_t i;
        double d;
    } min_val;

    // Maximum allowed value for a signal.
    // Use max_val.d if signal.data_type is VSS_FLOAT or VSS_DOUBLE.
    // Use max_val.i if signal.data_type is one of the integer types.
    //
    const union {
        int64_t i;
        double d;
    } max_val;

    // Signal description.
    // Set to "" if not specified.
    //
    const char* description;

    // Pointer to null-termianted array of values that signal can have
    // Traverse using enum_values[index].
    // If there are no enumerated values specifed, then enum_values[0] == 0
    //
    const char* const* enum_values;

    // Sensor specification of signal.
    // Set to "" if not specified.
    //
    const char* sensor;

    // Actuator specification of signal.
    // Set to "" if not specified.
    //
    const char* actuator;

    // User Data element that can be used to
    // connect the signal to application-managed structures.
    void* user_data;
} vss_signal_t;


// Return a signal struct pointer based on signal index.
//
// The index of a signal is available in its 'index'
// struct member and is guaranteed to have the same
// signal - index mapping across all vspec2c-generated
// code for a given signal specification.
//
// Use index 0 to get root signal ("Vehicle")
//
// The returned signal can have its members inspected (but not modified).
//
// The 'children' member will always be a null terminated array
// of vsd_signal_t pointers that can be traversed by accessing
// sig->children[index] untila null pointer is encountered.
// If there are no children sig->children[0] will be null.
//
// The 'enum_values' member will likewise be a null terminated
// array of char pointers with the enum values.
// If there are no enum values sig->enum_values[0] will be null.
//
// If the index argument is less than zero or greater to or equal
// than the size of the index array.
//
extern vss_signal_t* vss_get_signal_by_index(int index);

// Locate a signal by its path.
// Path is in the format "Branch.Branch.[...].Signal.
// If
extern int vss_get_signal_by_path(char* path,
                                   vss_signal_t ** result);

const char* vss_element_type_string(vss_element_type_e elem_type);

const char* vss_data_type_string(vss_data_type_e data_type);

// Populate the full path name to the given signal.
// The name will be stored in 'result'.
// No more than 'result_max_len' bytes will be copied.
// The copied name will always be null terminated.
// 'result' is returned.
// In case of error, an empty string is copiec into result.
extern char* vss_get_signal_path(vss_signal_t* signal,
                                 char* result,
                                 int result_max_len);

// A unique hash generated across all signals' combined
// UUID values.
// This signature can be used by two networked systems to
// verify that they are both using the same signal
// specification version.
//
extern const char* vss_get_sha256_signature(void);

// The number of signals in vss_signal array.
// The max value for vss_get_signal_by_index() is
// the return value of this function - 1.
extern const int vss_get_signal_count(void);

extern vss_signal_t vss_signal[];

// Tag to denote that a signal's min_value or max_value has
// not been specified.
#define VSS_LIMIT_UNDEFINED INT64_MIN

:MACRO_DEFINITION_BLOCK:
"""

#
# C Source file template code.
#
vss_src_template = """
//
// Auto generated code by vspec2c.py
// See github.com/GENIVI/vehicle_signal_specification for details/
//
#include <string.h>
#include <stdio.h>
#include ":HEADER_FILE_NAME:"

vss_signal_t vss_signal[] = {
:VSS_SIGNAL_ARRAY:
};


const char* vss_element_type_string(vss_element_type_e elem_type)
{
    switch(elem_type) {
    case VSS_ATTRIBUTE: return "attribute";
    case VSS_BRANCH: return "branch";
    case VSS_SENSOR: return "sensor";
    case VSS_ACTUATOR: return "actuator";
    case VSS_RBRANCH: return "rbranch";
    case VSS_ELEMENT: return "element";
    default: return "*unknown*";
    }
}

const char* vss_data_type_string(vss_data_type_e data_type)
{
    switch(data_type) {
    case VSS_INT8: return "INT8";
    case VSS_UINT8: return "UINT8";
    case VSS_INT16: return "INT16";
    case VSS_UINT16: return "uint16";
    case VSS_INT32: return "int32";
    case VSS_UINT32: return "uint32";
    case VSS_DOUBLE: return "double";
    case VSS_FLOAT: return "float";
    case VSS_BOOLEAN: return "boolean";
    case VSS_STRING: return "string";
    case VSS_STREAM: return "stream";
    case VSS_NA: return "na";
    default: return "*unknown*";
    }
}

int vss_get_signal_count(void)
{
   return (int) (sizeof(vss_signal) / sizeof(vss_signal[0]));
}

const char* vss_get_sha256_signature(void)
{
    return ":VSS_HASH_TEXT:";
}



vss_signal_t* vss_get_signal_by_index(int index)
{
    if (index < 0 || index >= sizeof(vss_signal) / sizeof(vss_signal[0]))
        return 0;

    return &vss_signal[index];
}

int vss_get_signal_by_path(char* path,
                            vss_signal_t ** result)
{
    vss_signal_t * cur_signal = &vss_signal[0]; // Start at root.
    char *path_separator = 0;

    if (!path || !result)
        return EINVAL;

    // Ensure that first element in root matches
    path_separator = strchr(path, '.');

    // If we found a path component separator, nil it out and
    // move to the next char after the separator
    // If no separator is found, path_separator == NULL, allowing
    // us to detect end of path
    if (strncmp(cur_signal->name, path, path_separator?path_separator-path:strlen(path))) {
        printf("Root signal mismatch between %s and %*s\\n",
               cur_signal->name,
               (int)(path_separator?path_separator-path:strlen(path)), path);
        return ENOENT;
    }

    if (path_separator)
        path_separator++;

    path = path_separator;

    while(path) {
        int ind = 0;
        path_separator = strchr(path, '.');
        int path_len = path_separator?path_separator-path:strlen(path);

        // We have to go deeper into the tree. Is our current
        // signal a branch that we can traverse into?
        if (cur_signal->element_type != VSS_BRANCH) {
            printf ("signal %*s is not a branch under %s. ENODIR\\n",
                     path_len, path, cur_signal->name);
            return ENOTDIR;
        }

        // Step through all children and check for a path componment match.
        while(cur_signal->children[ind]) {
            if (!strncmp(path, cur_signal->children[ind]->name, path_len) &&
                strlen(cur_signal->children[ind]->name) == path_len)
                break;

            ind++;
        }
        if (!cur_signal->children[ind]) {
            printf ("Child %*s not found under %s. ENOENT\\n",
                     path_len, path, cur_signal->name);

            return ENOENT;
        }
        cur_signal = cur_signal->children[ind];

        // If we found a path component separator, nil it out and
        // move to the next char after the separator
        // If no separator is found, path_separator == NULL, allowing
        // us to detect end of path
        if (path_separator)
            path_separator++;

        path = path_separator;
    }

    *result = cur_signal;

    return 0;
}

"""

def usage():
    print("Usage:", sys.argv[0], "[-I include-dir] ... [-i prefix:id-file] vspec-file c-header-file c-source-file")
    print("  -I include-dir       Add include directory to search for included vspec")
    print("                       files. Can be used multiple timees.")
    print()
    print("  -i prefix:uuid-file  File to use for storing generated UUIDs for signals with")
    print("                       a given path prefix. Can be used multiple times to store")
    print("                       UUIDs for signal sub-trees in different files.")
    print()
    print(" vspec-file            The vehicle specification file to parse.")
    print(" c-header-file         The file to output the C header file to.")
    print(" c-source-file         The file to output the C source file to.")
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
    sig_decl = ''
    for k, v in sorted(vspec_data.items(), key=lambda item: item[0]):
        sig_decl += emit_signal(k, v)

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
        print("Error: {}".format(e))
        exit(255)

    add_signal_index(tree)
    add_signal_path(tree)

    # Generate a hash
    sha256hash = hashlib.sha256()
    generate_hash(tree, sha256hash)

    # Generate header file

    macro = generate_header(tree)
    with open (args[1], "w") as hdr_out:
        hdr_out.write(vss_hdr_template.
                      replace(':MACRO_DEFINITION_BLOCK:', macro))

    # Generate source file
    sig_decl = generate_source(tree)
    with open (args[2], "w") as src_out:
        src_out.write(vss_src_template.
                      replace(':VSS_SIGNAL_ARRAY:', sig_decl).
                      replace(':HEADER_FILE_NAME:', os.path.basename(args[1])).
                      replace(':VSS_HASH_TEXT:', sha256hash.hexdigest()))

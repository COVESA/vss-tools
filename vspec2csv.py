#!/usr/bin/python3

#
#
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

#
# Convert vspec file to CSV
#

import sys
import vspec
import json
import getopt
import csv


def usage():
    print ( \
f"""
Usage: {sys.argv[0]} [options] vspec_file csv_file

  where [options] are:

  -I include_dir       Add include directory to search for included vspec
                       files. Can be used multiple timees.

  -i prefix:uuid_file  "prefix" is an optional string that will be
                       prepended to each signal name defined in the
                       vspec file.

                       "uuid_file" is the name of the file containing the
                       static UUID values for the signals.  This file is
                       read/write and will be updated if necessary.

                       This option can be specified several times in
                       to store the UUIDs of different parts of the
                       signal tree in different files.

  vspec_file           The vehicle specification file to parse.

  csv_file             The file to output the CSV data to.
""" )
    sys.exit(255)


def format_data(json_data):
    Uuid = '""'
    Type = '""'
    DataType = '""'
    Unit = '""'
    Min = '""'
    Max = '""'
    Desc = '""'
    Enum = '""'
    Sensor = '""'
    Actuator = '""'

    if ('uuid' in json_data):
        Uuid = '"' + str(json_data['uuid']) + '"'
    if ('type' in json_data):
        Type = '"' + json_data['type'] + '"'
    if ('datatype' in json_data):
        DataType = '"' + json_data['datatype'] + '"'
    if ('unit' in json_data):
        Unit = '"' + json_data['unit'] + '"'
    if ('min' in json_data):
        Min = '"' + str(json_data['min']) + '"'
    if ('max' in json_data):
        Max = '"' + str(json_data['max']) + '"'
    if ('description' in json_data):
        Desc = '"' + json_data['description'] + '"'
    if ('enum' in json_data):
        Enum = '"' + ' / '.join(json_data['enum']) + '"'
    if ('sensor' in json_data):
        Sensor = '"' + str(json_data['sensor']) + '"'
    if ('actuator' in json_data):
        Actuator = '"' + str(json_data['actuator']) + '"'
    return f"{Uuid},{Type},{DataType},{Unit},{Min},{Max},{Desc},{Enum},{Sensor},{Actuator}"


def json2csv(json_data, file_out, parent_signal):
    for k in list(json_data.keys()):
        if (len(parent_signal) > 0):
            signal = parent_signal + "." + k
        else:
            signal = k

        if (json_data[k]['type'] == 'branch'):
            file_out.write(signal + ',' + format_data(json_data[k]) + '\n')
            json2csv(json_data[k]['children'], file_out, signal)
        else:
            file_out.write(signal + ',' + format_data(json_data[k]) + '\n')


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

    if len(args) != 2:
        usage()

    csv_out = open (args[1], "w")

    try:
        tree = vspec.load(args[0], include_dirs)
    except vspec.VSpecError as e:
        print ( f"Error: {e}" )
        exit(255)

    #
    #   Write out the column name line.
    #
    csv_out.write ( "Signal,Id,Type,DataType,Unit,Min,Max,Desc,Enum,Sensor,Actuator\n" )

    #
    #   Go process all of the data records in the input JSON file.
    #
    json2csv(tree, csv_out, "")
    csv_out.write("\n")
    csv_out.close()

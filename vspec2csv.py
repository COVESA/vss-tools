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
import re


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


def json2csv(json_data, file_out, parent_signal, ext=[]):
    for k in json_data.keys():
        if (len(parent_signal) > 0):
            signal = parent_signal + "." + k
        else:
            signal = k

        local_ext = ext
        if ('extension' in json_data[k].keys()):
            local_ext = ext + [(json_data[k]['extension'])]

        # if it's a branch, create an entry and continue
        # with its children
        if (json_data[k]['type'] == 'branch'):
            file_out.write(signal + ',' + format_data(json_data[k]) + '\n')
            # if postion attribute exists, keep it
            json2csv(json_data[k]['children'], file_out, signal, local_ext)

        # if it's a leave, make an entry, check the extension entries and
        # create an entry for every extension
        else:
            if not local_ext:
                file_out.write(signal + ',' + format_data(json_data[k]) + "," + str(ext) + '\n')

            createExtensionEntries(local_ext, file_out, json_data[k], signal)



def createExtensionEntries(ext, file_out, json_data, prefix=''):
    """Function creates the extension entries to a given node as
       postfix of the node name (e.g. node.Row1.LEFT)

    Parameters
    ----------
    ext : list
        list of branches with extension argument in the path
    file_out : file
        csv file to write into
    json_data : json object
        json encoded information about the node
    prefix : string
        node name before the extension information
    """

    REG_EX = "\w+\[\d+,(\d+)\]"

    if not ext and file_out and json_data:
        return

    rest = None
    i = []
    if len(ext) == 1:
        i = ext[0]
    else:
        i = ext[0]
        rest = ext[1:]



    if prefix and not prefix.endswith("."):
        prefix += "."


    # parse string extension elements (e.g. Row[1,5])
    if isinstance(i,str):
        if re.match(REG_EX, i):
            extRangeArr = re.split("\[+|,+|\]",i)
            for r in range(int(extRangeArr[1]),int(extRangeArr[2])+1):
                nextPrefix = prefix + extRangeArr[0]+str(r)
                if rest:
                    createExtensionEntries(rest, file_out, json_data, nextPrefix)
                else:
                    file_out.write(nextPrefix + ',' + format_data(json_data) + "," + '\n')


        # TODO: right now dynamic extensions not supported
        else:
            raise vspec.VSpecError("","","Extension type not supported")
    # Use list elements for extension (e.g. [LEFT,RIGHT])
    elif (isinstance(i,list)):
        for r in i:
            # if in case of multiple extensions in one branch
            # it has to be distinguished from a list of
            # string extensions, like [LEFT,RIGHT]
            if (isinstance(r,str)):
                if re.match(REG_EX, r):
                    if (rest):
                        rest.append(r)
                    else:
                        rest = [r]
                    createExtensionEntries(rest, file_out, json_data, prefix)
                else:
                    nextPrefix = prefix + str(r)
                    if rest:
                        createExtensionEntries(rest, file_out, json_data, nextPrefix)
                    else:
                        # create a new type instance for now for
                        # better recognition, of what it is
                        json_data["type"] = "instance"
                        file_out.write(nextPrefix + ',' + format_data(json_data) + "," + '\n')

            else:
                # in case of multiple extensions, the list is
                # has to be parsed, like [LEFT,RIGHT]
                if (rest):
                    rest.append(r)
                else:
                    rest = [r]
                createExtensionEntries(rest, file_out, json_data, prefix)


    else:
        print (i)
        raise vspec.VSpecError("","","not supported")



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

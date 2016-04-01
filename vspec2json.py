#!/usr/bin/python

#
# Copyright (C) 2016, Jaguar Land Rover
#
# This program is licensed under the terms and conditions of the
# Mozilla Public License, version 2.0.  The full text of the 
# Mozilla Public License is at https://www.mozilla.org/MPL/2.0/
#
# 
# Concert vspec file to JSON
#  

import sys
import vspec
import json
import getopt

def usage():
    print "Usage:", sys.argv[0], "[-I include_dir] ... vpsec_file"
    print "  -I include_dir   Add include directory to search for included vspec"
    print "                   files. Can be used multiple timees."
    print
    print " vspec_file        The vehicle specification file to parse."     
    sys.exit(255)

if __name__ == "__main__":
    # 
    # Check that we have the correct arguments
    #
    opts, args= getopt.getopt(sys.argv[1:], "I:")

    # Always search current directory for include_file
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        else:
            usage()

    if len(args) != 1:
        usage()

    try:
        tree = vspec.load(args[0], include_dirs)
    except vspec.VSpecError as e:
        print "Error: {}".format(e)
        exit(255)

    print json.dumps(tree, indent=2)
    

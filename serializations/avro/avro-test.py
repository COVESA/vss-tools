#!/usr/bin/env python3

import avro.schema
import sys
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter

if len(sys.argv) < 2:
#    print(f"usage: #{sys.argv[0]} <schemafile.avsc>")
#    sys.exit(1)
    schemafile = "TimeStampedRecord.avsc"
    print(f"Using default schema: {schemafile}")
else:
    schemafile = sys.argv[1]

schema = avro.schema.parse(open(schemafile, "rb").read())

# Test output a sequence of timeseries records

#{
#  "type": "record",
#  "name": "TimeStampedRecord",
#  "fields" : [
#         { "name" : "ts", "type" : "string" },
#         { "name" : "value", "type" : [ "int", "long", "float", "double", "string", "boolean" ] }
#  ]
#}

# Encode data into file

# (Note this follows (only) the TimeStampedRecord schema)

writer = DataFileWriter(open("testoutput.avro", "wb"), DatumWriter(), schema)
writer.append({ "ts" : "20210826123100.45Z", "value" : int(2304) })
writer.append({ "ts" : "20210826123101.35Z", "value" : int(2314) })
writer.append({ "ts" : "20210826123102.41Z", "value" : int(2388) })
writer.append({ "ts" : "20210826123103.50Z", "value" : int(2481) })
writer.append({ "ts" : "20210826123104.39Z", "value" : int(2500) })
writer.append({ "ts" : "20210826123105.44Z", "value" : int(2533) })
#writer.append({"values": "Vehicle.Powertrain.CombustionEngine.Engine.Speed", "count": 4})
writer.close()

# Read back the file, decode and print the data
reader = DataFileReader(open("testoutput.avro", "rb"), DatumReader())
for user in reader:
    print(user)
reader.close()


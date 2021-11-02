#!/usr/bin/env python3

import os
import fastavro
import json
import sys
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter

# Schemas are here defined recursively, starting with the
# innermost fundamental types, and then building up more complex types from
# them.

# While doing so, "schemadict" is used by fastavro to remember the
# previously parsed Types, so that they can be referred to by name in the
# subsequent schemas.

# Read an AVRO schema in JSON format from "filename"
# Each new type will be added to the given schemadict incrementally 
# at each call.
def read_schema(filename, schemas):
    with open(filename, 'r') as f:
        return fastavro.parse_schema(json.load(f), schemas)


schemadict = {}
# These must be parsed in order since the latter types embed the former
# ones, and thus refer to them
read_schema('schemas/Value.avsc', schemadict)
read_schema('schemas/TimeStampedRecord.avsc', schemadict)
schema_TimeSeries = read_schema('schemas/TimeSeries.avsc', schemadict)

sa = {}
read_schema('schemas/Value.avsc', sa)
read_schema('schemas/TimeStampedRecord.avsc', sa)
read_schema('schemas/TimeSeries.avsc', sa)
read_schema('schemas/SpecifiedTimeStampedRecord.avsc', sa)
read_schema('schemas/Snapshot.avsc', sa)
read_schema('schemas/Message.avsc', sa)
#read_schema('schemas/SpecifiedRecord.avsc', sa)
schema_MessageSequence = read_schema('schemas/MessageSequence.avsc', sa)

# Print, for information...

print("Time SeriesSchema:")
print("------------------------------------------------------")
print(schema_TimeSeries)
print()
print("MessageSequence Schema:")
print("------------------------------------------------------")
print(schema_MessageSequence)

# OK, schemas contain the full schema definition(s)

# Encode data into file
# (Note this follows (only) the TimeSeries schema)

# Examples of time series instances.  First one has
# a sequence of Temperatures, which are just ints
val = { "signal_identifier" : "Vehicle.Cabin.Temperature",
          "count" : 4,
          "items" : [
             { "ts" : 0, "value" : { "item" : -11 } },
             { "ts" : 1, "value" : { "item" : 2 } },
             { "ts" : 2, "value" : { "item" : -21 } },
             { "ts" : 3, "value" : { "item" : 5 } },
             { "ts" : 4, "value" : { "item" : 2 } },
             { "ts" : 5, "value" : { "item" : 230 } },
             { "ts" : 6, "value" : { "item" : 2 } },
             { "ts" : 7, "value" : { "item" : 7 } },
             { "ts" : 8, "value" : { "item" : 3811 } },
             { "ts" : 9, "value" : { "item" : 2 } },
             { "ts" : 10, "value" : { "item" : 2 } },
             { "ts" : 11, "value" : { "item" : -14 } },
             { "ts" : 12, "value" : { "item" : 2 } },
             { "ts" : 13, "value" : { "item" : -147 } },
             { "ts" : 14, "value" : { "item" : 0 } }
      ]
}

# Example with an array-typed signal (array of strings)
val2 = { "signal_identifier" : "Vehicle.ExampleStringInfo",
            "count" : 4,
            "items" : [
                { "ts" : 0, "value" : { "item" : [  "one" , "two" , "three" ] } },
                { "ts" : 1, "value" : { "item" : [ "another" , "value" , "sequence", "of", "stringvalues" ] } },
                { "ts" : 2, "value" : { "item" : [ "foo" , "bar" , "baz" ] } },
                ]
}


# Write data to avro encoded (binary) file
file1 = 'testoutput.avro'
file2 = 'testoutput2.avro'
os.remove(file1)
with open(file1, 'wb') as fout:
     fastavro.writer(fout, schema_TimeSeries , [ val, val2 ] )
     #fastavro.writer(fout, schema_MessageSequence, seq)

# A sequence of Message make up a MessageSequence
# In this case both messages are TimeSeries.  But they could
# be single records (SpecifiedTimeStampedRecord most likely)
# or a Snapshot.
seq = [ { "seq" : [ { "item" : val }, { "item" : val2 } ] } ]

print ()
print("... Writing data ...")

with open(file2, 'wb') as fout:
     fastavro.writer(fout, schema_MessageSequence, seq)

print ()
print("... Reading back the data ...")

print ()
# Read back the Time Series file and print
with open(file1, 'rb') as fin:
   avro_reader = fastavro.reader(fin, schema_TimeSeries)
   for record in avro_reader:
       print("Got TimeSeries record:" + str(record))
   print("------------------------------------------------------")

print()
# Read back the Message Sequence file and print
with open(file2, 'rb') as fin:
   avro_reader = fastavro.reader(fin, schema_MessageSequence)
   for record in avro_reader:
       print("Got MessageSequence record:" + str(record))
   print("------------------------------------------------------")


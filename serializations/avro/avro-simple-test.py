#!/usr/bin/env python3

import os
import fastavro
import sys
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter

# Schemas are here defined recursively, starting with the
# innermost fundamental types, and then building up more complex types from
# them.

# While doing so, "schemadict" is used by fastavro to remember the
# previously parsed Types, so that they can be referred to by name in the
# subsequent schemas.

schemadict = {}

# Next one specifies that a value can be either a single simple type (
# one of several choices), or an Array of such items.  Value specifies all
# possible encodings of a single VSS value.
s = {
   "type" : "record",
   "name" : "Value",
   "fields" : [
      { "name" : "item", "type" : [
            # VSS values are either one of a choice of simple values:
            # (simplified down to available AVRO types here)
            "int", "long", "float", "double", "string", "boolean",
            # ... or a signal value can be an array of values.
            { "type" : "array",
              "items" : [ "int", "long", "float", "double", "string", "boolean" ]
            }
         ]
      }
   ]
}
fastavro.parse_schema(s, schemadict)

# A Time Stamped Record keeps a single VSS signal value, and a time stamp
# In this case we use a long integer to encode time stamps.
s = {
   "type" : "record",
   "name" : "TimeStampedRecord",
   "fields" : [
      { "name" : "ts", "type" : "long" },
      { "name" : "value", "type" : "Value" }
   ]
}

fastavro.parse_schema(s, schemadict)

# A Time Series is a definition of a single signal name
# and then a sequence of values with time stams
s = {
   "type" : "record",
   "name" : "TimeSeries",
   "fields" : [
      { "name" : "signal_identifier", "type": "string"},
      { "name" : "count", "type" : "int" },
      { "name" : "items", "type" :  { "type" : "array", "items" : "TimeStampedRecord" } }
   ]
}

# Final parsing defines the TimeSeries schema
schema_TimeSeries = fastavro.parse_schema(s, schemadict)

# OK, schema now contains the full schema definition

# Encode data into file
# (Note this follows (only) the TimeSeries schema)

# Example time series values
vals = [
        { "signal_identifier" : "Vehicle.Cabin.Temperature",
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
]

# Example with an array-typed signal (array of strings)
vals2 = [
        { "signal_identifier" : "Vehicle.Cabin.Temperature",
            "count" : 4,
            "items" : [
                { "ts" : 0, "value" : { "item" : [  "one" , "two" , "three" ] } },
                { "ts" : 1, "value" : { "item" : [ "another" , "value" , "sequence", "of", "stringvalues" ] } },
                { "ts" : 2, "value" : { "item" : [ "foo" , "bar" , "baz" ] } },
                ]
            }
]

# Write data to avro encoded (binary) file
fn = 'testoutput.avro'

# Remove output file if it exists
try:
    os.remove(fn)
except FileNotFoundError:
    pass

with open(fn, 'wb') as fout:
     fastavro.writer(fout, schema_TimeSeries , vals + vals2)

# Read back the file, decode and print the data
with open('testoutput.avro', 'rb') as fin:
   avro_reader = fastavro.reader(fin, schema_TimeSeries)
   for record in avro_reader:
       print("Read record:" + str(record))


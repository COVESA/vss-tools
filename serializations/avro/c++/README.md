Plan:  
-----

Write a basic client library (C++) with convenience
classes/functions that allows 'application code' to easily encode and
decode AVRO-encoded VSS-value messages according to the "Data serialization
/ value formats" previous analysis.

This only builds the VSS + "Data serialization / value formats" mechanisms.
It shall of course delegate any AVRO encoding/decoding work to existing C++
AVRO implementation(s).

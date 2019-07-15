# ENCODE  AVEHICLE SIGNAL SPECIFICATION IN C

**(C) 2019 Jaguar Land Rover**

The vspec2c tooling allows a vehicle signal specification to be
translated from its source YAML file to native C code that
has the entire specification encoded in it.

The specification is encoded as two header files, one hosting a struct
array with all signal specification data, and one with a set of macros
to access signals.

The two header files are included by the application, which is then
linked with the vehicle signal specification built in this repo.

Please see schematics for details.

[Schematics](schematics.png)

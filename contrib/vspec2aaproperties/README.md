Usage:
## 1. CPP adaptation code generation
You can run the CPP generator with following parameters:
- This code should be run from the VSS-tools folder:
```
./vspec2aaprop_test.sh
```

The script runs the following generator

usage: vspec2aaprop [-h] [-v VSPEC] [-m MAP] [-a ANDROID] [-t TYPEMAP] [-j JINJA] [-I INCLUDE [INCLUDE ...]] [output]

Convert vss specification to Android Auto properties according to the input map file.

positional arguments:
  output                Output .cpp file name (default: AndroidVssConverter.cpp)

optional arguments:
  -h, --help            show this help message and exit
  -v VSPEC, --vspec VSPEC
                        Vehicle Signal Specification (default: ../../../spec/VehicleSignalSpecification.vspec)
  -m MAP, --map MAP     Conversion Item Map File (default: vspec2prop_mapping.yml)
  -a ANDROID, --android ANDROID
                        Android Type Mapping (Android types.hal file) (default: types.hal)
  -t TYPEMAP, --typemap TYPEMAP
                        VSS/VHAL/Android CPP type mapping (default: typemap.yml)
  -j JINJA, --jinja JINJA
                        Jinja2 generator file (default: android_vhal_mapping_cpp.tpl)
  -I INCLUDE [INCLUDE ...], --include INCLUDE [INCLUDE ...]
                        Include directories (default: ['templates'])

python3 vspec2aaprop.py -v ../../../spec/VehicleSignalSpecification.vspec -m vspec2prop_mapping.yml -t types.hal android_vhal_mapping_cpp.tpl typemap.yml test.cpp
Explanation of the parameters:
vspec2aaprop.py:
	Generator host python code. Code uses Jinja2 to actual conversion.
-v ../../../spec/VehicleSignalSpecification.vspec:
	Vehicle Signal Specification (VSS). Used to grab the VSS variable type for the items.
-m vspec2prop_mapping.yml:
	Map. YAML representation of the VSS-Android VHAL mapping with scaling/complex conversions.
	C++ code is gererated only for the signals defined in the map.
-a types.hal:
	General Android header for the VHAL types. Used to grab the Android variable type for the items.
-j android_vhal_mapping_cpp.tpl:
	Actual Jinja2 generator for generating the CPP conversion code.
-t typemap:
	General Mapping of types and type conversions between VSS/vhal/C++.
test.cpp: 
	Output. Name of the generated CPP file (output).

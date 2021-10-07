Usage:
## 1. CPP adaptation code generation
You can run the CPP generator with following parameters:
- This code should be run from the VSS-tools folder:
```
./test.sh
```

The script runs the following generator
python3 contrib/vspec2aaproperties/vspec2aaprop.py ../spec/VehicleSignalSpecification.vspec contrib/vspec2aaproperties/vspec2prop_mapping.yml contrib/vspec2aaproperties/types.hal android_vhal_mapping_cpp.tpl test.cpp

Explanation of the input parameters:
contrib/vspec2aaproperties/vspec2aaprop.py: Generator host python code. Code uses Jinja2 to actual conversion.
../spec/VehicleSignalSpecification.vspec: VSS. Used to grab the VSS variable type for the items.
contrib/vspec2aaproperties/vspec2prop_mapping.yml: YAML representation of the VSS-Android VHAL mapping with scaling/complex conversions.
contrib/vspec2aaproperties/types.hal: Android header for the VHAL. Used to grab the Android variable type for the items.
android_vhal_mapping_cpp.tpl: Actual Jinja2 generator for generating the CPP conversion code.

Explanation of the output parameters:
test.cpp: Name of the generated CPP file.


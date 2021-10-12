Usage:
## 1. CPP adaptation code generation
You can run the CPP generator with following parameters:
- This code should be run from the VSS-tools folder:
```
./vspec2aaprop_test.sh
```

The script runs the following generator
python3 vspec2aaprop.py ../../../spec/VehicleSignalSpecification.vspec vspec2prop_mapping.yml types.hal android_vhal_mapping_cpp.tpl test.cpp

Explanation of the parameters:
vspec2aaprop.py:
	Generator host python code. Code uses Jinja2 to actual conversion.
../../../spec/VehicleSignalSpecification.vspec:
	VSS. Used to grab the VSS variable type for the items.
vspec2prop_mapping.yml:
	YAML representation of the VSS-Android VHAL mapping with scaling/complex conversions.
types.hal:
	Android header for the VHAL. Used to grab the Android variable type for the items.
android_vhal_mapping_cpp.tpl:
	Actual Jinja2 generator for generating the CPP conversion code.
test.cpp: 
	Name of the generated CPP file (output).


Plans for VSS code generator (Android)

* [ ] Create a new directory in contrib/ for the code generator vspec2aaprop
* [ ] Create a subdirectory for templates
* [ ] Create main generator program vspec2aaprop.py
* [ ] Create a new module / file to read/process: read_mapping_layer.py
* [ ] Input files to vspec2aaprop.py are both vspec directory and a vspec2prop_mapping.yml
* [ ] vspec can be processed with vspec.py as usual (exists)
* [ ] vspec2prop_mapping.yml can be processed with read_mapping_layer.py as usual (exists)
* [ ] => Import vspec and read_mapping_layer into main generator program vspec2aaprop.py
* [ ] Import jinja2
* [ ] Write code to set up jinja2 generation environment, just copy from vsc-tools
* [ ] Write generator logic - likely it needs a gen() function to be called from the template, which takes a VSS node as input.
* [ ] Write some test files
* [ ] Write some unit tests and integrat pytest
* [ ] Set up a C++ project that can be compiled, which is fed with the generated code
* [ ] Make compilation part of sanity-test
* [ ] Try a bigger VSS example
* [ ] Plan and develop demonstration of the project

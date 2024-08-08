# DDS IDL Test

DDS IDL output is not tested by pytest as installing `cyclonedds`is not straightforward on all target enviroments.
Instead we do a sanity check of the output only in [CI](../../.github/workflows/buildcheck.yml).
If you want to test manually (on amd64 Linux) you can run commands like below and verify
that grep finds the text `A.String` in the generated Python file.


```bash
~/vss-tools/tests/ddsidl$ vspec export ddsidl -u ../vspec/test_units.yaml -s test.vspec -o test.idl
[13:54:51] INFO     No quantities defined!
           INFO     Added 7 units from ../vspec/test_units.yaml
           INFO     Loading vspec from test.
           INFO     Check type usage
           INFO     Generating DDS-IDL output...
           INFO     IDL file generated at location : test.idl
~/vss-tools/tests/ddsidl$ idlc -l py test.idl
No default extensibility provided. For one or more of the aggregated types in the IDL the extensibility is not explicitly set. Currently the default extensibility for these types is 'final', but this may change to 'appendable' in a future release because that is the default in the DDS XTypes specification.
~/vss-tools/tests/ddsidl$ grep -i A.String A/_test.py
class String(idl.IdlStruct, typename="A.String"):
~/vss-tools/tests/ddsidl$ rm -rf A test.idl

```
VSS2DDSIDL converter is used to export VSS file data to DDS IDL file _(4.2 version)_

## Acronyms used:
- DDS : Data Distribution Service
- IDL : Interface Definition Language
- VSS : Vehicle Signal Specification

## Reference to the specifications:

- VSS description can be found at : [link](https://covesa.github.io/vehicle_signal_specification/introduction/)
- DDS  IDL specification can be found at : [link](https://www.omg.org/spec/IDL/4.2/PDF)

## Various VSS elements considered for conversion:
- Name
- datatype (also single dimensional array is supported)
- allowed

### Special handling
Below elements are considered only if the switch ***--all-idl-features*** is supplied as a command line argument
- type
- min, max
- unit
- description


## Datatypes mapping between VSS and DDS-IDL

| VSS    | DDS-IDL        |
|--------|----------------|
| uint8  | octet          |
| int8   | octet          |
| uint16 | unsigned short |
| int16  | short          |
| uint32  | unsigned long |
| int32  | long           |
| uint64  | unsigned long long|
| int64  | long long          |
| boolean  | boolean          |
| float  | float              |
| double  | double            |
| string  | string            |

## Examples of VSS data and converted DDS-IDL data

### Input VSS block with "arraysize" attribute
| VSS    | DDS-IDL         |
|--------|----------------|
| <pre>Safety.SpeedLimit:<br>    datatype : float[]<br>    arraysize: 5<br>    type: actuator<br>    unit: m/s<br>    description: Maximum allowed speed of the vehicle</pre>  | <pre>struct SpeedLimit{<br>string uuid;<br>sequence&lt;float&gt; value;<br>}<br></pre>          |
### Input VSS block with "allowed" attribute

| VSS    | DDS-IDL         |
|--------|----------------|
| <pre>Direction:<br> datatype:string<br> type: actuator<br> allowed: ['FORWARD','BACKWARD']<br> description: Driving direction of the vehicle</pre>  | <pre>module Direction_M {<br>enum DirectionValues{FORWARD,BACKWARD};<br>};<br>struct Direction<br>{<br>string uuid;<br>DirectionValues value;<br>};</pre>

To comply with DDS-IDL rules and limitations in IDL compilers VSS string literals that start with a digit will get a `d` as prefix.

Example VSS:

```
allowed: ['FORWARD','BACKWARD', '123']
```


Resulting DDS-IDL::

```
enum DirectionValues{FORWARD,BACKWARD,d123}
```

*Initially an underscore was used a prefix. That made the IDL correct according to tools,*
*but could not be correctly handled by tools like "Eclipse Cyclone DDS idlc Python Backend"*
*resulting in invalid Python code.*

## Checking generated DDS-IDL file and generating code stubs from it

IDL files can be supplied as input to one of the DDS implementation (e.g: CycloeDDS, FastDDS) and the data can be validated, and also stubs (python/c++/java code) can be generated from the contents in the IDL file.

### Installation of CycloneDDS


```Shell
$ git clone https://github.com/eclipse-cyclonedds/cyclonedds.git
$ pip3 install cyclonedds conan
$ cd cyclonedds/ \
      && mkdir build \
      && cd build \
      && conan install .. --build missing \
      && cmake .. \
      && cmake --build . --target install
```

**Usage of CycloneDDS to take IDL file as input and generate Python file with types**

> idlc **-l py**  ./results/res.idl
### FastDDS

**Installation of FastDDS**

Follow the instructions mentioned in page : [https://fast-dds.docs.eprosima.com/en/latest/installation/binaries/binaries_linux.html](https://fast-dds.docs.eprosima.com/en/latest/installation/binaries/binaries_linux.html)

**Usage of FastDDS to take IDL file as input and generate Python file with types**

> ./fastddsgen **-replace** ./results/res.idl

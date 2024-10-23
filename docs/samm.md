# Vspec - Semantic Aspect Meta Model (SAMM) exporter

Helper exporter to convert VSS specification (.vspec) file(s) into [ESMF - Semantic Aspect Meta Model](https://eclipse-esmf.github.io/samm-specification/2.1.0/index.html) (.ttl) files,
which then can be further used in the [Eclipse Semantic Modeling Framework (ESMF) - Aspect Model Editor (AME)](https://github.com/eclipse-esmf/esmf-aspect-model-editor#readme).
<br />
<br />

## What is this script about?

This script is built to provide functionalities to convert COVESA VSS specification (.vspec) files
into ESMF Aspect Model (.ttl) formatted files and following the [Resource Description Format (RDF11)](https://www.w3.org/TR/rdf11-concepts/) and Terse [RDF Tripple Language](https://www.w3.org/TR/turtle/) syntax,
which then can be loaded in [ESMF - AME](https://github.com/eclipse-esmf/esmf-aspect-model-editor#readme).

The editor latest version, can be downloaded from [ESMF AME - releases](https://github.com/eclipse-esmf/esmf-aspect-model-editor/releases).
Select the corresponding package, based on your operating system and follow the instructions.

The ESMF - Aspect model Editor, provides a number of functions to design, edit and work with UML like diagrams,
which then, can be used to generate example JSON loads, can be exported into OPEN API - JSON formatted specifications,
which further can be loaded in tools like [SWAGGER](https://swagger.io/) or other API generating tools and so on an dso forth.
<br/>
<br/>

## User Guide:
</br>

### Get Help:
To get help information about this script, use:

```bash
vspec export samm --help
```
<br/>

### Example Usage:

This script is provided pre-configured, unless some other requirements like:

1. where to store the converted ttl files?
2. whether to have the full VSS converted into a single Aspect model or split into separate Aspect models?
    - **Please Note:** if the full VSS is selected to be converted to a single aspect model (.ttl),
                   this would lead to one pretty big Aspect model (.ttl) file.
                   Very large aspect models can slow down the work with the ESMF AME or could lead to some unpredicted results.
                   Therefore, it is recommended to use the **--split/--spl** option.

are needed.
<br/>

#### Convert complete VSS to single ESMF ttl model:
Below command will call this script with its default options.

```bash
vspec export samm -s PATH_TO_VSS/vehicle_signal_specification/spec/VehicleSignalSpecification.vspec
```

>**Please Note:**
>
> Above command will run the samm exporter with its default options.
> The above mentioned **help** command will provide a full list of VSS Tools supported options
> and the additional ones, listed below, which are handled by this script.
>
<br/>

### Vspec - SAMM exporter dedicated options:

Below are listed only the specific and handled by this exporter options, which can be used to further control its behavior.

1. **--target-folder** or **-tf** - path to or name for the target folder, where generated aspect models (.ttl files) will be stored.

    >**Please Note:**
    > This folder will be created relatively to the folder from which this script is called.
    >
    > **DEFAULT:** vss_ttls/
    >

2. **--target-namespace** or **-tns** - Namespace for VSS library, located in specified **--target-folder**.
    Will be used as name of the folder where VSS Aspect models (TTLs) are to be stored.
    This folder will be created as subfolder of the specified **--target-folder** parameter.

    > **DEFAULT:** com.covesa.vss.spec
    >

3. **--split** or **-spl** / **--no-split** - Boolean flag - used to indicate whether to convert VSS specifications in separate ESMF Aspect(s)
    or the whole (selected) VSS specification(s) will be combined into single ESMF Aspect model.

    >**Please Note:**
    > Since the size of the VSS is pretty big, it is recommended to use the **DEFAULT** value of this option i.e.,
    > **--split**. Otherwise the generated *Vehicle.ttl* will be very big and hard to work with it in the [ESMF - Aspect Model Editor (AME)](https://github.com/eclipse-esmf/esmf-aspect-model-editor#readme)
    >
    > **DEFAULT:** *--split* or *-spl*
    >

4. **--split-depth** or **-spld** - Number - used to define, up to which level, VSS branches will be converted into single aspect models.
    Can be used in addition to the **--split, -spl** option.

    > **DEFAULT:** 1
    > Default value of 1 means that only 1st level VSS branches like Vehicle.Cabin, Vehicle.Chassis etc.,
    > will be converted to separate aspect models i.e. **.ttl** files.
    >

5. **--signals-file**  or **-sigf** - Path to file with selected VSS signals to be converted.
    Allows to convert just selected VSS signals into aspect model(s), when **--split, -spl** is enabled
    or build one single *Vehicle.ttl* aspect model with selected VSS signals.

    >**Please Note:**
    > Each signal in the file should be on a new line and in the format of:
    >
    > ```
    > PARENT_SIGNAL.PATH.TO.CHILD_SIGNAL
    > ```
    >
    > as defined in VSS.
    >
<br/>

### Convert selected VSS signals to ESMF ttl models:

In order to convert just selected COVESA VSS signals, you can create a simple text file, where each selected signal is added on a new line.

For example, this **selected-vss-signals-to-convert.txt** can look like:

```
Vehicle.Cabin.Door
Vehicle.CurrentLocation.Accuracy
Vehicle.CurrentLocation.Latitude
Vehicle.CurrentLocation.Longitude
Vehicle.Powertrain.FuelSystem.InstantConsumption
```

An example call would be:

```bash
vspec export samm \
    -s PATH_TO_VSS/vehicle_signal_specification/spec/VehicleSignalSpecification.vspec \
    -sigf PATH_TO_FILE/selected-vss-signals-to-convert.txt
```

>**Please Note:**
> We used just the **--vspec, -s** and **--signals-file, -sigf** options,
> leaving other ones to their default values.
>

As result, you will get the following folder with below listed contents, placed in the location, from which you called this exporter.

```
vss_ttls/
    com.covesa.vss.spec/
        5.0.0/
            Cabin.ttl
            CurrentLocation.ttl
            Powertrain.ttl
            Vehicle.ttl
```

>**Please Note:**
> The version folder: **5.0.0/** is dynamically read from the COVESA VSS - *Vehicle.VersionVSS* node.
>
> In other words, if you happen to call an older VSS version, lets say *4.2.0* with same selected signals file,
> then the result will be:
>
> ```
> vss_ttls/
>    com.covesa.vss.spec/
>        4.2.0/
>            Cabin.ttl
>            CurrentLocation.ttl
>            Powertrain.ttl
>            Vehicle.ttl
> ```
>
<br/>

### Validation and verification of generated Aspect Models

Once you have your generated VSS aspect models, you can do a simple validation in the context of [Eclipse Semantic Modeling Framework (ESMF)](https://github.com/eclipse-esmf)
using either their UI tool, the [ESMF - Aspect Model Editor (AME)](https://github.com/eclipse-esmf/esmf-aspect-model-editor#readme) or their CLI one, the [ESMF - Command Line Interface (CLI)](https://eclipse-esmf.github.io/esmf-developer-guide/tooling-guide/samm-cli.html).

The validation with the [ESMF - Aspect Model Editor (AME)](https://github.com/eclipse-esmf/esmf-aspect-model-editor#readme) is relatively easy.
First of all you need to have it installed on your machine, then move the generated **com.covesa.vss.spec/** folder under the AME workspace,
which usually should be located in your User **Home** directory and be named: **aspect-model-editor**.

All you will need to do is move the generated **com.covesa.vss.spec/** folder to: **YOUR HOME DIRECTORY/aspect-model-editor/models**,
load the aspect in the editor and hit the validate button, as shown below:

![Validate aspect model on the ESMF - AME](assets/Validate%20aspect%20model%20on%20ESMF-AME.png)<br/>
*Example: How to validate aspect model on the Aspect Model Editor*


The validation, using the [ESMF - Command Line Interface](https://eclipse-esmf.github.io/esmf-developer-guide/tooling-guide/samm-cli.html)
will save the extra steps to copy aspect models to the AME workspace, and will allow you to directly validate the generated VSS aspect model, using the below command.

```bash
samm aspect vss_ttls/com.covesa.vss.spec/5.0.0/Vehicle.ttl validate
```

>**Please Note:**
> In order to be able to use the [ESMF - SAMM CLI](https://eclipse-esmf.github.io/esmf-developer-guide/tooling-guide/samm-cli.html)
> you will need to have it installed on your environment.
>

Both tools [ESMF - AME](https://github.com/eclipse-esmf/esmf-aspect-model-editor#readme) and [ESMF - SAMM CLI](https://eclipse-esmf.github.io/esmf-developer-guide/tooling-guide/samm-cli.html)
provide for validation of aspect models and generation of other documents like: OpenAPI specifications, HTML Documents, Sample JSON Payload and JSON Schemas.
Also, please keep in mind that since the CLI tool also provides functionality to generate and SQL Schemas.
<br/>

### Running this exporter in DEBUG or other mode

As per available functionality, provided by the [vspec](vspec.md), the DEFAULT mode of execution of this and other exporters is INFO.

Other possible modes are: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".

In order to switch these when calling this exporter you can use the option: [--log-level](vspec.md#--log-level).
Also there is an option to redirect the console output i.e. logged information to a text file. To do so, you can use the [--log-file](vspec.md#--log-file) option.

A complete example, where you can call this exporter in DEBUG mode and store the logged information into a simple text file would be:

```bash
vspec --log-level DEBUG --log-file PATH_TO_LOGS/export_vss2samm.log export samm \
    -s PATH_TO_VSS/vehicle_signal_specification/spec/VehicleSignalSpecification.vspec \
    -sigf PATH_TO_FILE/selected-vss-signals-to-convert.txt
```

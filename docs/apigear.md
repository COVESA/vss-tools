# Vspec ApiGear exporter

Generates a solution and a module file. All signals and types are added to a single module. This is due to a limitation of ApiGear.

ApiGear has a limitation with constructing multiple modules. Each module is generated as a separate submodule in a solution. This means, if we create multiple modules and use unreal template, it will generate as many plugins, as there are modules. This is not ideal.
Furthermore, ApiGear does not support importing modules within other modules - thus, cannot create a module substructure, which would be useful to define a type / signal structure. Therefore, we have to use the naming within a single module to recreate the VSS substructure.

To simplify the running the generator, ApiGear exporter creates a `solution` file. This let's
developer run a single command to generate all specified templates:

```sh
apigear generate solution <solution-file>
```

## --output-dir
Required output directory for the solution and module files.

## --apigear-template-unreal-path
Add Unreal layer to solution file at the specified path, uses the ApiGear `apigear-io/template-unreal` template. Relative path relates to the `--output-dir`.

## --apigear-template-cpp-path
Add Cpp14 layer to solution file at the specified path, uses the ApiGear `apigear-io/template-cpp14` template. Relative path relates to the `--output-dir`.

## --apigear-template-qt5-path
Add Qt5 layer to solution file at the specified path, uses the ApiGear `apigear-io/template-qt5` template. Relative path relates to the `--output-dir`.

## --apigear-template-qt6-path
Add Qt6 layer to solution file at the specified path, uses the ApiGear `apigear-io/template-qtcpp` template. Relative path relates to the `--output-dir`.

## Example usage

```sh
vspec --log-level DEBUG export apigear \
--output-dir ./solution \
--apigear-template-unreal-path ./unreal \
--apigear-template-cpp-path ./cpp14 \
--apigear-template-qt5-path ./qt5 \
--apigear-template-qt6-path ./qt6 \
-I ./spec \
-u ./spec/units.yaml \
-s ./spec/VehicleSignalSpecification.vspec
```

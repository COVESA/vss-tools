#include "inc/AndroidVssConverter.h"

#define LOG_TAG "AndroidVssConverter"

#include <log/log.h>
#include <vhal_v2_0/VehicleUtils.h>

#include "inc/ConverterUtils.h"


namespace android {
namespace hardware {
namespace automotive {
namespace vehicle {
namespace V2_0 {

namespace impl {

VehiclePropValue AndroidVssConverter::convertProperty(std::string id, std::string value, VehicleHal* vhal) 
{
    if (conversionMap.empty()) {
        initConversionMap(vhal);
    }

    // TODO error handling like missing id
    return conversionMap[id](value);
}

VehiclePropValue initializeProp(VehicleProperty id, int32_t area) 
{
    VehiclePropValue val = {
        .timestamp = elapsedRealtimeNano(),
        .areaId = area,
        .prop = toInt(id),
        .status = VehiclePropertyStatus::AVAILABLE
    };

    return val;
}

typedef bool BOOLEAN;
typedef int16 INT16;
typedef uint16 UINT16;
typedef float FLOAT;
typedef uint8 UINT8;
bool str2BOOLEAN(std::string value)
{
    return (value == "true");
}
int16 str2INT16 (std::string value)
{
    return (int16)std::atoi(value);
}
uint16 str2UINT16 (std::string value)
{
    return (uint16)std::atoi(value);
}
float str2FLOAT(std::string value)
{
    return (float)std::atof(value);
}
int8 str2UINT8(std::string value)
{
    return (uint8)std::atoi(value);
}

/** BEGIN GENERATED SECTION: STR CONVERSIONS REQUIRED **/
{% set converters = {} %}
{% for key,item in map_tree.items() %}
 {% set name = "str2"+str(vss_tree[key].data_type).split(".")[-1] %}
 {% if name not in converters %}
  {% set x=converters.__setitem__(name,name) %}
{{str(vss_tree[key].data_type).split(".")[-1]}} str2{{str(vss_tree[key].data_type).split(".")[-1]}}(std::string value);
 {% endif %}
{% endfor %}
/** END GENERATED SECTION: STR CONVERSIONS REQUIRED **/

VehiclePropValue convertBOOLEAN2BOOLEAN(std::string value, VehicleProperty id, int32_t area)
{
    VehiclePropValue prop = initializeProp(id, area);
    bool v = value == "true";
    prop.value.int32Values = std::vector<int32_t> { v };
    return prop;
}

VehiclePropValue convertLinearINT162FLOAT(std::string value, VehicleProperty id, int32_t area, float K, float m)
{
    VehiclePropValue prop = initializeProp(id, area);
    float v = (float)str2INT16(value);
    prop.value.floatValues = std::vector<float> { v }; 
    return prop;
}

/** BEGIN GENERATED SECTION: TYPE CONVERTERS **/
{% for key,item in map_tree.items() %}
 {% if item["translation"] %}
 {% elif item["multiplier"] %}
  {% set name = "convertLinear"+str(str(vss_tree[key].data_type).split(".")[-1])+"2"+type_table[item['aospId']] %}
  {% if name not in converters %}
   {% set x=converters.__setitem__(name,name) %}
VehiclePropValue {{name}}(std::string value, VehicleProperty id, int32_t area, float K, float m)
{
    VehiclePropValue prop = initializeProp(id, area);
    float v = (float)str2{{str(vss_tree[key].data_type).split(".")[-1]}}(value);
    prop.value.floatValues = std::vector<float> { v * K + m }; 
    return prop;
}
  {% endif %}
 {% else %}
  {% set name = "convert"+str(str(vss_tree[key].data_type).split(".")[-1])+"2"+type_table[item['aospId']] %}
  {% if name not in converters %}
   {% set x=converters.__setitem__(name,name) %}
{{ type_table[item['aospId']] }} {{name}}(std::string value, VehicleProperty id, int32_t area);
  {% endif %}
 {% endif %}
{% endfor %}
/** END GENERATED SECTION: TYPE CONVERTERS **/

/** BEGIN GENERATED SECTION: TRANSLATION CONVERTERS **/
{% for key,item in map_tree.items() %}
{% if item["translation"] %}
static VehiclePropValue convert{{"_".join(key.split(".")[1:])}}(std::string value, VehicleProperty id, int32_t area, VehicleHal* vhal)
{
    VehiclePropValue prop = initializeProp(id, area);
{% if False %}
// {{item["translation"]["complex"]}}
// float fuelCapacity = getVehiclePropertyFloatValue(toInt(VehicleProperty::INFO_FUEL_CAPACITY), vhal);
// input:{{item["translation"]["input"]}}
{% endif %}
{% for invalue in item["translation"]["input"] %}
{% if False %}
// typetable: {{type_table[invalue]}}
{% endif %}
    {{type_table[invalue]}} value{{invalue}} = getVehicleProperty{{type_table[invalue]}}Value(toInt(VehicleProperty::{{invalue}}), vhal);
{% endfor %}
    {{str(vss_tree[key].data_type).split(".")[-1]}} v = str2{{str(vss_tree[key].data_type).split(".")[-1]}}(value);
    prop.value.floatValues = std::vector<float> { {{item["translation"]["complex"].replace("$","value").replace("_VAL_","((float)v)")}} };
    return prop;
}
{% endif %}
{% endfor %}
/** END GENERATED SECTION: TRANSLATION CONVERTERS **/


/** BEGIN GENERATED SECTION: TRANSLATION TABLE **/
void AndroidVssConverter::initConversionMap(VehicleHal* vhal) {
    conversionMap.clear();
{% if False %}
//conversionMap["Vehicle.ADAS.ABS.IsActive"] = std::bind(convertBool,
//            std::placeholders::_1, VehicleProperty::ABS_ACTIVE, toInt(VehicleArea::GLOBAL));
{% endif %}
{% for key,item in map_tree.items() %}
{% if False %}
// VSS item: {{ key }}
// VSS type: {{ vss_tree[key].data_type }}
// AOSP item: {{ item['aospId'] }}
// AOSP area: {{ item['aospArea'] }}
// Android type: {{ type_table['aospId'] }}
{% endif %}
{% if item["multiplier"] %}
    conversionMap["{{ key }}"] = std::bind(convertLinear{{str(vss_tree[key].data_type).split(".")[-1]}}2{{ type_table[item['aospId']] }},
        std::placeholders::_1, {{ item['aospId'] }}, (int32_t) {{item['aospArea']}},{{item["multiplier"]}},{{item["offset"]}});
{% elif item["translation"]%}
    conversionMap["{{ key }}"] = std::bind(convert{{"_".join(key.split(".")[1:])}},
        std::placeholders::_1, {{ item['aospId'] }}, (int32_t) {{item['aospArea']}}, vhal);
{% else %}
    conversionMap["{{ key }}"] = std::bind(convert{{str(vss_tree[key].data_type).split(".")[-1]}}2{{ type_table[item['aospId']] }},
        std::placeholders::_1, {{ item['aospId'] }}, toInt({{item['aospArea']}}));
{% endif %}
{% endfor %}
}
/** END GENERATED SECTION: TRANSLATION TABLE **/


}  // impl

}  // namespace V2_0
}  // namespace vehicle
}  // namespace automotive
}  // namespace hardware
}  // namespace android

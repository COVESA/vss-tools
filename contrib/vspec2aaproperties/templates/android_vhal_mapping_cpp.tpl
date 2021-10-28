{% set debug = False %}
#include "inc/AndroidVssConverter.h"

#define LOG_TAG "AndroidVssConverter"

#include <log/log.h>
#include <vhal_v2_0/VehicleUtils.h>
#include <utils/SystemClock.h>
#include "inc/ConverterUtils.h"


namespace android {
namespace hardware {
namespace automotive {
namespace vehicle {
namespace V2_0 {

namespace impl {

/** BEGIN Predefined Property helper functions **/
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
/** END Predefined Property helper functions **/

/** BEGIN GENERATED SECTION: STR CONVERSIONS REQUIRED **/
{% set converters = {} %}
{% for key,item in map_tree.items() %}
 {% set name = "str2"+str(vss_tree[key].data_type).split(".")[-1] %}
 {% if name not in converters %}
  {% set x=converters.__setitem__(name,name) %}
{{typemap[str(vss_tree[key].data_type).split(".")[-1]]["cpp"]}} str2{{str(vss_tree[key].data_type).split(".")[-1]}}(std::string _val_)
{
    return {{typemap[str(vss_tree[key].data_type).split(".")[-1]]["from"]["string"]}};
};
 {% endif %}
{% endfor %}
/** END GENERATED SECTION: STR CONVERSIONS REQUIRED **/

/** BEGIN GENERATED SECTION: TYPE CONVERTERS **/
{% for key,item in map_tree.items() %}
 {% if item["translation"] %}
 {% elif item["multiplier"] %}
  {% set name = "convertLinear"+str(str(vss_tree[key].data_type).split(".")[-1])+"2"+type_table[item['aospId']] %}
  {% if name not in converters %}
   {% set x=converters.__setitem__(name,name) %}
VehiclePropValue {{name}}(std::string value, VehicleProperty id, int32_t area, float K, float m)
{
    {% if debug %}
    // C++ type for {{item['aospId']}}: {{typemap[type_table[item['aospId']]]["cpp"]}}
    // C++ type for vss: {{typemap[str(vss_tree[key].data_type).split(".")[-1]]["cpp"]}}
    {% endif %}
    VehiclePropValue prop = initializeProp(id, area);
    {{typemap[str(vss_tree[key].data_type).split(".")[-1]]["cpp"]}} v = {{typemap[(str(vss_tree[key].data_type).split(".")[-1])]["from"]["string"].replace("_val_","value")}};
    float _val_ = v * K + m;
    {{typemap[type_table[item['aospId']]]["cpp"]}} result = {{typemap[str(vss_tree[key].data_type).split(".")[-1]]["to"][type_table[item['aospId']]]}};
    prop.value.{{typemap[type_table[item['aospId']]]["vhal"]}}Values = std::vector<{{typemap[type_table[item['aospId']]]["cpp"]}}> { result }; 
    return prop;
}
  {% endif %}
 {% else %}
  {% set name = "convert"+str(str(vss_tree[key].data_type).split(".")[-1])+"2"+type_table[item['aospId']] %}
  {% if name not in converters %}
   {% set x=converters.__setitem__(name,name) %}
VehiclePropValue {{name}}(std::string value, VehicleProperty id, int32_t area) {
    VehiclePropValue prop = initializeProp(id, area);
    {{typemap[str(vss_tree[key].data_type).split(".")[-1]]["cpp"]}} _val_ = {{typemap[(str(vss_tree[key].data_type).split(".")[-1])]["from"]["string"].replace("_val_","value")}};
    {{typemap[type_table[item['aospId']]]["cpp"]}} result = {{typemap[str(vss_tree[key].data_type).split(".")[-1]]["to"][type_table[item['aospId']]]}};
    prop.value.{{typemap[type_table[item['aospId']]]["vhal"]}}Values = std::vector<{{typemap[type_table[item['aospId']]]["cpp"]}}> { result }; 
    return prop;
}
  {% endif %}
 {% endif %}
{% endfor %}
/** END GENERATED SECTION: TYPE CONVERTERS **/

/** BEGIN GENERATED SECTION: TRANSLATION CONVERTERS **/
{% for key,item in map_tree.items() %}
{% if item["translation"] %}
VehiclePropValue convert{{"_".join(key.split(".")[1:])}}(std::string value, VehicleProperty id, int32_t area, VehicleHal* vhal)
{
    VehiclePropValue prop = initializeProp(id, area);
{% if debug %}
// {{item["translation"]["complex"]}}
// float fuelCapacity = getVehiclePropertyFloatValue(toInt(VehicleProperty::INFO_FUEL_CAPACITY), vhal);
// input:{{item["translation"]["input"]}}
{% endif %}
{% for invalue in item["translation"]["input"] %}
{% if debug %}
// typetable: {{type_table[invalue]}}
{% endif %}
    {{typemap[type_table[invalue]]["cpp"]}} value{{invalue}} = getVehicleProperty{{typemap[type_table[invalue]]["vhal"]}}Value(toInt(VehicleProperty::{{invalue}}), vhal);
{% endfor %}
    {{typemap[str(vss_tree[key].data_type).split(".")[-1]]["cpp"]}} v = str2{{str(vss_tree[key].data_type).split(".")[-1]}}(value);
    float _val_ = {{item["translation"]["complex"].replace("$","value").replace("_VAL_","((float)v)")}};
    {{typemap[type_table[item['aospId']]]["cpp"]}} result = {{ typemap[str(vss_tree[key].data_type).split(".")[-1]]["to"][type_table[item['aospId']]] }};
    prop.value.{{typemap[type_table[item['aospId']]]["vhal"]}}Values = std::vector<{{typemap[type_table[item['aospId']]]["vhal"]}}> { result };
    return prop;
}
{% endif %}
{% endfor %}
/** END GENERATED SECTION: TRANSLATION CONVERTERS **/


/** BEGIN GENERATED SECTION: TRANSLATION TABLE **/
void AndroidVssConverter::initConversionMap(VehicleHal* vhal) {
    conversionMap.clear();
{% if debug %}
//conversionMap["Vehicle.ADAS.ABS.IsActive"] = std::bind(convertBool,
//            std::placeholders::_1, VehicleProperty::ABS_ACTIVE, toInt(VehicleArea::GLOBAL));
{% endif %}
{% for key,item in map_tree.items() %}
{% if debug %}
// VSS item: {{ key }}
// VSS type: {{ vss_tree[key].data_type }}
// AOSP item: {{ item['aospId'] }}
// AOSP area: {{ item['aospArea'] }}
// Android type: {{ type_table[item['aospId']] }}
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

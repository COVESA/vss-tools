{% set debug = False %}
#include "inc/AndroidVssConverter.h"
#include <functional> // for bind()
#include <string>
#include <vector>

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
 {% set name = "str2"+vss_tree.vsstype(key) %}
 {% if name not in converters %}
  {% set x=converters.__setitem__(name,name) %}

{{typemap.vss2cpp(key)}} str2{{vss_tree.vsstype(key)}}(std::string _val_)
{
    return {{typemap.vss_from_string(key)}};
};

 {% endif %}
{% endfor %}
/** END GENERATED SECTION: STR CONVERSIONS REQUIRED **/

/** BEGIN GENERATED SECTION: TYPE CONVERTERS **/
{% for key,item in map_tree.items() %}
 {% if item["translation"] %}
 {% elif item["multiplier"] %}
  {% set name = "convertLinear"+vss_tree.vsstype(key)+"2"+vhal_type[item['aospId']] %}
  {% if name not in converters %}
   {% set x=converters.__setitem__(name,name) %}

VehiclePropValue {{name}}(std::string value, VehicleProperty id, int32_t area, float K, float m)
{
    {% if debug %}
    // C++ type for {{item['aospId']}}: {{typemap[vhal_type[item['aospId']]]["cpp"]}}
    // C++ type for vss: {{typemap.vss2cpp(key)}}
    {% endif %}
    VehiclePropValue prop = initializeProp(id, area);
    {{typemap.vss2cpp(key)}} v = {{typemap.vss_from_string(key)}};
    float _val_ = v * K + m;
    {{typemap.vhal2cpp(item)}} result = {{typemap.vss2vhal(key,item)}};
    {{typemap.vhal_prop(item)}} = std::vector<{{typemap.vhal2cpp(item)}}> { result }; 
    return prop;
}

  {% endif %}
 {% else %}
  {% set name = "convert"+vss_tree.vsstype(key)+"2"+vhal_type[item['aospId']] %}
  {% if name not in converters %}
   {% set x=converters.__setitem__(name,name) %}

VehiclePropValue {{name}}(std::string value, VehicleProperty id, int32_t area) {
    VehiclePropValue prop = initializeProp(id, area);
    {{typemap.vss2cpp(key)}} _val_ = {{typemap.vss_from_string(key)}};
    {{typemap.vhal2cpp(item)}} result = {{typemap.vss2vhal(key,item)}};
    prop.value.{{typemap[vhal_type[item['aospId']]]["vhal"]}}Values = std::vector<{{typemap[vhal_type[item['aospId']]]["cpp"]}}> { result }; 
    return prop;
}

  {% endif %}
 {% endif %}
{% endfor %}
/** END GENERATED SECTION: TYPE CONVERTERS **/

/** BEGIN GENERATED SECTION: PROPERTY RETRIEVE FUNCTIONS **/
{% for key,item in map_tree.items() %}
    {% if item["translation"] %}
        {% if debug %}
        // {{item["translation"]["complex"]}}
        // input:{{item["translation"]["input"]}}
        {% endif %}
        {% for invalue in item["translation"]["input"] %}
            {% if debug %}
            // typetable: {{vhal_type[invalue]}}
            {% endif %}

{{typemap[vhal_type[invalue]]["cpp"]}} getVehicleProperty{{typemap[vhal_type[invalue]]["vhal"]}}Value(int propId, VehicleHal* vhal)
{
    VehiclePropValue request = VehiclePropValue {
        .areaId = toInt(VehicleArea::GLOBAL),
        .prop = propId,
    };
    StatusCode halStatus;
    auto valPtr = vhal->get(request, &halStatus);
    // TODO: check status, check if floatValues is not empty
    {{typemap[vhal_type[invalue]]["cpp"]}} value = ({{typemap[vhal_type[invalue]]["cpp"]}})0;
    if (valPtr != nullptr) {
        value = ({{typemap[vhal_type[invalue]]["cpp"]}}) valPtr->value.{{typemap[vhal_type[invalue]]["vhal"]}}Values[0];
    }
    return value;
}

        {% endfor %}
    {% endif %}
{% endfor %}
/** END GENERATED SECTION: PROPERTY RETRIEVE FUNCTIONS **/

/** BEGIN GENERATED SECTION: TRANSLATION CONVERTERS **/
{% for key,item in map_tree.items() %}
{% if item["translation"] %}
VehiclePropValue convert{{"_".join(key.split(".")[1:])}}(std::string value, VehicleProperty id, int32_t area, VehicleHal* vhal)
{
    VehiclePropValue prop = initializeProp(id, area);
{% if debug %}
// {{item["translation"]["complex"]}}
// float fuelCapacity = getVehiclePropertyfloatValue(toInt(VehicleProperty::INFO_FUEL_CAPACITY), vhal);
// input:{{item["translation"]["input"]}}
{% endif %}
{% for invalue in item["translation"]["input"] %}
{% if debug %}
// typetable: {{vhal_type[invalue]}}
{% endif %}
    {{typemap[vhal_type[invalue]]["cpp"]}} value{{invalue}} = getVehicleProperty{{typemap[vhal_type[invalue]]["vhal"]}}Value(toInt(VehicleProperty::{{invalue}}), vhal);
{% endfor %}
    {{typemap.vss2cpp(key)}} v = str2{{vss_tree.vsstype(key)}}(value);
    float _val_ = {{item["translation"]["complex"].replace("$","value").replace("_VAL_","((float)v)")}};
    {{typemap[vhal_type[item['aospId']]]["cpp"]}} result = {{ typemap.vss2vhal(key,item)}};
    prop.value.{{typemap[vhal_type[item['aospId']]]["vhal"]}}Values = std::vector<{{typemap[vhal_type[item['aospId']]]["vhal"]}}> { result };
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
// Android type: {{ vhal_type[item['aospId']] }}
{% endif %}
{% if item["multiplier"] %}
    conversionMap["{{ key }}"] = std::bind(convertLinear{{vss_tree.vsstype(key)}}2{{ vhal_type[item['aospId']] }},
        std::placeholders::_1, {{ item['aospId'] }}, (int32_t) {{item['aospArea']}},{{item["multiplier"]}},{{item["offset"]}});
{% elif item["translation"]%}
    conversionMap["{{ key }}"] = std::bind(convert{{"_".join(key.split(".")[1:])}},
        std::placeholders::_1, {{ item['aospId'] }}, (int32_t) {{item['aospArea']}}, vhal);
{% else %}
    conversionMap["{{ key }}"] = std::bind(convert{{vss_tree.vsstype(key)}}2{{ vhal_type[item['aospId']] }},
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

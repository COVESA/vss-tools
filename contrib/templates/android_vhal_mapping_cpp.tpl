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

VehiclePropValue AndroidVssConverter::convertProperty(std::string id, std::string value, VehicleHal* vhal) {
    if (conversionMap.empty()) {
        initConversionMap(vhal);
    }

    // TODO error handling like missing id
    return conversionMap[id](value);
}

/** BEGIN GENERATED SECTION **/
{% for key,item in map_tree.items() %}
{% if item["translation"] %}
static VehiclePropValue convert{{key.replace(".","_")}}(std::string value, VehicleProperty id, int32_t area, VehicleHal* vhal) {
{% if False %}
// {{item["translation"]["complex"]}}
// float fuelCapacity = getVehiclePropertyFloatValue(toInt(VehicleProperty::INFO_FUEL_CAPACITY), vhal);
// input:{{item["translation"]["input"]}}
{% endif %}
{% for invalue in item["translation"]["input"] %}
{% if False %}
// typetable: {{type_table[invalue]}}
{% endif %}
   float value{{invalue}} = getVehiclePropertyFloatValue(toInt(VehicleProperty::{{invalue}}), vhal);
{% endfor %}
   return ({{item["translation"]["complex"].replace("$","value").replace("_VAL_","value")}})
}
{% endif %}
{% endfor %}

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
    conversionMap["{{ key }}"] = std::bind(convertLinear{{ type_table[item['aospId']] }},
        std::placeholders::_1, {{ item['aospId'] }}, (int32_t) {{item['aospArea']}},{{item["multiplier"]}},{{item["offset"]}});
{% elif item["translation"]%}
    conversionMap["{{ key }}"] = std::bind(convert{{key.replace(".","_")}},
        std::placeholders::_1, {{ item['aospId'] }}, (int32_t) {{item['aospArea']}});
{% else %}
    conversionMap["{{ key }}"] = std::bind(convert{{ type_table[item['aospId']] }},
        std::placeholders::_1, {{ item['aospId'] }}, toInt({{item['aospArea']}}));
{% endif %}
{% endfor %}
}
 /** END GENERATED SECTION **/


}  // impl

}  // namespace V2_0
}  // namespace vehicle
}  // namespace automotive
}  // namespace hardware
}  // namespace android

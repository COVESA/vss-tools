
void AndroidVssConverter::initConversionMap(VehicleHal* vhal) {
    conversionMap.clear();
//conversionMap["Vehicle.ADAS.ABS.IsActive"] = std::bind(convertBool,
//            std::placeholders::_1, VehicleProperty::ABS_ACTIVE, toInt(VehicleArea::GLOBAL));

{% for key,item in map_tree.items() %}
// VSS item: {{ key }}
// VSS Unit: {{ vss_tree[key].data_type }}
// AOSP item: {{ item['aospId'] }}
// AOSP area: {{ item['aospArea'] }}
    conversionMap["{{ key }}"] = std::bind(convert{{ type_table[item['aospId']] }},
        std::placeholders::_1, {{ item['aospId'] }}, toInt({{item['aospArea']}}));
{% endfor %}
}
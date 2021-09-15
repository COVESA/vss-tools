
void AndroidVssConverter::initConversionMap(VehicleHal* vhal) {
    conversionMap.clear();

{% for key,item in map_tree.items() %}
// VSS item: {{ key }}
// AOSP item: {{ item['aospId'] }}
// AOSP area: {{ item['aospArea'] }}
{% endfor %}
}
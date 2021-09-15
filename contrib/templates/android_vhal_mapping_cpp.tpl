
void AndroidVssConverter::initConversionMap(VehicleHal* vhal) {
    conversionMap.clear();

{% for item in map_tree %}
// VSS item: {{ item }}
// AOSP item: {{ item[aospId] }}
// AOSP area: {{ item.aospArea }}
{% endfor %}
}
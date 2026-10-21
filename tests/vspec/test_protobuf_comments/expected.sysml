
// A string with allowed values
enum def StringWithAllowed {
	enum VALUE_A;
	enum VALUE_B;
	enum VALUE_C;
}

part def A {

	// actuator: A string with allowed values
	stringWithAllowed : StringWithAllowed;

	// sensor: A uint8 with min and max
	// unit: percent
	// interval [0..100]
	uInt8WithMinMax : ScalarValues::Integer;

	// sensor: A deprecated node
	deprecatedString : ScalarValues::String;

	// sensor: Only a description
	// unit: mm
	descOnly : ScalarValues::Real;

	// sensor: A node with no extra metadata
	noMetadata : ScalarValues::Integer;
}

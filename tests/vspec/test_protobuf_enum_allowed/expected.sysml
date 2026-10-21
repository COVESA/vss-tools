
// Media source with allowed values
enum def Source {
	enum UNKNOWN;
	enum AM;
	enum FM;
	enum BLUETOOTH;
}

// Road surface condition list (array with allowed values)
enum def Surface {
	enum DRY;
	enum WET;
	enum SNOW;
	enum ICE;
}

part def A {

	// actuator: Media source with allowed values
	source : Source;

	// sensor: Road surface condition list (array with allowed values)
	surface : Surface;

	// sensor: Speed without allowed values — must remain float
	speed : ScalarValues::Real;
}

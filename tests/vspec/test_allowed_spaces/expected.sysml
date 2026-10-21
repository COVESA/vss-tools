
// Gear selection mode.
enum def GearSelect {
	enum Park Brake;
	enum Drive Forward;
}

part def A {

	// actuator: Gear selection mode.
	gearSelect : GearSelect;
}

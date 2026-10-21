part def DoorIS0 {

	// attribute: Door kind - cannot be hoisted.
	kind : ScalarValues::String;
	row1 : Door_IS1;
	row2 : Door_IS1;
}
part def Door_IS1 {
	left : Door;
	right : Door;
}
part def Door {

	// actuator: Is door open or closed?
	isOpen : ScalarValues::Boolean;
}

part def Vehicle {
	door : PDoor::DoorIS0;
}
// All doors.
package PDoor {
	part def DoorIS0 {

		// attribute: A door signal that should be hoisted to Vehicle.
		someSignal : ScalarValues::Integer;
		row1 : PDoor::Door_IS1;
		row2 : PDoor::Door_IS1;
	}
	part def Door_IS1 {
		left : PDoor::Door;
		right : PDoor::Door;
	}
	part def Door {

		// actuator: Is door open or closed?
		isOpen : ScalarValues::Boolean;
	}
}

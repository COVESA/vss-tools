part def Vehicle {
	cabin : PCabin::Cabin;
}
// All in-cabin components, controls, and features.
package PCabin {
	part def Cabin {
		door : PCabin::PDoor::DoorIS0;
	}
	// All doors, including windows and switches.
	package PDoor {
		part def DoorIS0 {

			// attribute: A door signal that should not be instantiated.
			someSignal : ScalarValues::Integer;
			row1 : PCabin::PDoor::Door_IS1;
			row2 : PCabin::PDoor::Door_IS1;
		}
		part def Door_IS1 {
			left : PCabin::PDoor::Door;
			right : PCabin::PDoor::Door;
		}
		part def Door {

			// actuator: Is door open or closed?
			isOpen : ScalarValues::Boolean;

			// actuator: Is door locked or unlocked?
			isLocked : ScalarValues::Boolean;
		}
	}
}

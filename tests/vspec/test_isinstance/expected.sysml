part def Vehicle {
	door : PDoor::DoorIS;
}
// Door
package PDoor {
	part def DoorIS {
		row1 : PDoor::PRow1::Row1;

		// branch: Door
		row2 : None;
	}
	// Door
	package PRow1 {
		part def Row1 {

			// branch: Special
			special : None;
		}
	}
}

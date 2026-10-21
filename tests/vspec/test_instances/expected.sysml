part def AIS {
	b : PB::BIS0;
	y : PY::Y;
	x : PX::XIS;
	y1 : A;
	y2 : A;
}
// This description will be duplicated.
package PB {
	part def BIS0 {
		row1 : PB::B_IS1;
		row2 : PB::B_IS1;
	}
	part def B_IS1 {
		left : PB::B;
		right : PB::B;
	}
	part def B {

		// sensor: This description will also exist multiple times.
		// unit: km
		c : ScalarValues::Integer;
	}
}
// d
package PY {
	part def Y {

		// attribute: d
		count : ScalarValues::Integer;
	}
}
// d
package PX {
	part def XIS {
		b : PX::PB::B;
		c : PX::PC::C;
		b1 : PX::X;
		b2 : PX::X;
		c1 : PX::X;
		c2 : PX::X;
	}
	// d
	package PB {
		part def B {

			// attribute: d
			count : ScalarValues::Integer;
		}
	}
	// d
	package PC {
		part def C {

			// attribute: d
			count : ScalarValues::Integer;
		}
	}
	part def X {

		// sensor: d
		value : ScalarValues::Boolean;
	}
}
part def A {
	z : PZ::ZIS;
}
// d
package PZ {
	part def ZIS {

		// branch: d
		z1 : None;

		// branch: d
		z2 : None;
	}
}

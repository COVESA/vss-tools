part def A {
	b : PB::BIS;
	c : PC::CIS;
	d : PD::DIS0;
	e : PE::E;
}
// Branch with explicit instances.
package PB {
	part def BIS {
		test1 : PB::B;
		test2 : PB::B;
		test3 : PB::B;
	}
	part def B {

		// sensor: Signal A.B.S.
		// unit: km
		s : ScalarValues::Integer;
	}
}
// Branch with instance range.
package PC {
	part def CIS {
		test1 : PC::C;
		test2 : PC::C;
		test3 : PC::C;
		test4 : PC::C;
	}
	part def C {

		// sensor: Signal A.C.S.
		// unit: km
		s : ScalarValues::Integer;
	}
}
// Branch with complex instance combination.
package PD {
	part def DIS0 {
		test1 : PD::D_IS1;
	}
	part def D_IS1 {
		test2 : PD::D_IS1;
		test3 : PD::D_IS1;
	}
	part def D_IS1 {
		test4 : PD::Test1_IS1;
		test5 : PD::Test1_IS1;
		test6 : PD::Test1_IS1;
	}
	part def Test1_IS1 {
		test7 : PD::Test2_IS1;
		test8 : PD::Test2_IS1;
		test9 : PD::Test2_IS1;
		test10 : PD::Test2_IS1;
	}
	part def Test2_IS1 {
		test11 : PD::Test4;
	}
	part def Test4 {

		// sensor: Signal A.D.S.
		// unit: km
		s : ScalarValues::Integer;
	}
}
// Branch without instances for reference.
package PE {
	part def E {

		// sensor: Signal A.E.S.
		// unit: km
		s : ScalarValues::Integer;
	}
}

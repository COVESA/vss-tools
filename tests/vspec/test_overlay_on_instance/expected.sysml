part def A {
	b : PB::BIS0;
	s : PS::SIS;
}
// Branch A.B, instances defined in list
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

		// sensor: Signal A.B.C.
		// unit: km
		c : ScalarValues::Integer;
	}
}
// Branch with instances, not in list
package PS {
	part def SIS {
		front : PS::S;
		rear : PS::S;
	}
	part def S {

		// sensor: Signal A.S.T
		// unit: km
		t : ScalarValues::Integer;
		tT : PS::PTT::TTIS;
	}
	// Second level instance
	package PTT {
		part def TTIS {
			left : PS::PTT::TT;
			right : PS::PTT::TT;
		}
		part def TT {
			tTT : PS::PTT::PTTT::TTT;
		}
		// Another branch level
		package PTTT {
			part def TTT {

				// sensor: Some temperature.
				// unit: celsius
				tTTT : ScalarValues::Real;
				t4 : PS::PTT::PTTT::PT4::T4;
			}
			// A very nasty branchzhs
			package PT4 {
				part def T4 {

					// sensor: A very nasty sensor
					tTTTR : ScalarValues::Real;
				}
			}
		}
	}
}

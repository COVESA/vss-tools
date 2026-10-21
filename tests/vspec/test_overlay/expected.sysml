part def A {

	// sensor: This is the first signal.
	// unit: km
	signalA : ScalarValues::Integer;
	aA : PAA::AA;
}
// Branch A.AA.
package PAA {
	part def AA {

		// sensor: This is yet another signal.
		// unit: km
		signalAA : ScalarValues::Integer;
	}
}

part def A {
	row1 : PRow1::Row1;
	row2 : PRow2::Row2;

	// sensor: Unrelated signal.
	other : ScalarValues::Integer;
}
// Row 1.
package PRow1 {
	part def Row1 {

		// sensor: First row signal.
		signal : ScalarValues::Real;
	}
}
// Row 2.
package PRow2 {
	part def Row2 {

		// sensor: Second row signal.
		signal : ScalarValues::Real;
	}
}

part def A {

	// sensor: No Min Max.
	intNoMinMax : ScalarValues::Integer;

	// sensor: Only Max.
	// interval (..32]
	intOnlyMax : ScalarValues::Integer;

	// sensor: Only Min.
	// interval [3..)
	intOnlyMin : ScalarValues::Integer;

	// sensor: Min & Max.
	// interval [3..6]
	intMinMax : ScalarValues::Integer;

	// sensor: Max Zero.
	// interval (..0]
	intMaxZero : ScalarValues::Integer;

	// sensor: Min Zero.
	// interval [0..)
	intMinZero : ScalarValues::Integer;

	// sensor: No Min Max.
	floatNoMinMax : ScalarValues::Real;

	// sensor: Only Max.
	// interval (..32.3]
	floatOnlyMax : ScalarValues::Real;

	// sensor: Only Min.
	// interval [-2.5..)
	floatOnlyMin : ScalarValues::Real;

	// sensor: Min & Max.
	// interval [-165.56323..236723.4]
	floatMinMax : ScalarValues::Real;

	// sensor: Max Zero.
	// interval (..0.0]
	floatMaxZero : ScalarValues::Real;

	// sensor: Min Zero.
	// interval [0.0..)
	floatMinZero : ScalarValues::Real;

	// sensor: Max Zero.
	// interval (..0]
	floatMaxZeroInt : ScalarValues::Real;

	// sensor: Min Zero.
	// interval [0..)
	floatMinZeroInt : ScalarValues::Real;
}

package vss

type A struct {
	B B
}
type B struct {
	Row1 BI1
	Row2 BI1
}
type BI1 struct {
	Left BI2
	Right BI2
}
type BI2 struct {
	C int8
}

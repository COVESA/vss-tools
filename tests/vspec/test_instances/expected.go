package vss

type A struct {
	B BI2
}
type BI2 struct {
	Row1 BI1
	Row2 BI1
}
type BI1 struct {
	Left B
	Right B
}
type B struct {
	C int8
}

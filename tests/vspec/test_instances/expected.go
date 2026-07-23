package vss

type AI1 struct {
	B BI2
	Y Y
	Y1 A
	Y2 A
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
type Y struct {
	Count uint8
}
type A struct {
	Z Y2ZI1
}
type ZI1 struct {
	Z1 Z
	Z2 Z
}
type Z struct {
}
type Y2ZI1 struct {
	Z1 Y2Z
	Z2 Y2Z
}
type Y2Z struct {
}

package vss

type Vehicle struct {
	Struct Struct
	StructA []Struct
	AllTypes AllTypes
}
type AllTypes struct {
	Uint8 uint8
	Uint8A []uint8
	Uint16 uint16
	Uint16A []uint16
	Uint32 uint32
	Uint32A []uint32
	Uint64 uint64
	Uint64A []uint64
	Int8 int8
	Int8A []int8
	Int16 int16
	Int16A []int16
	Int32 int32
	Int32A []int32
	Int64 int64
	Int64A []int64
	Bool bool
	BoolA []bool
	Float float32
	FloatA []float32
	Double float64
	DoubleA []float64
	String string
	StringA []string
	Numeric float64
	NumericA []float64
}
type Struct struct {
	x StructEmbedded
	y uint8
}
type StructEmbedded struct {
	z []uint8
}

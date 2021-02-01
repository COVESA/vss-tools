module github.com/GENIVI/vss-tools/binary/go_parser

go 1.14

replace (
	github.com/GENIVI/vss-tools/binary/go_parser/datamodel => ./datamodel
	github.com/GENIVI/vss-tools/binary/go_parser/parserlib => ./parserlib
)

require (
	github.com/GENIVI/vss-tools/binary/go_parser/datamodel v0.0.0
	github.com/GENIVI/vss-tools/binary/go_parser/parserlib v0.0.0
)

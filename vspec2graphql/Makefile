
.PHONY: protobuf

# adjust this path if need be. 
# Then execute this file with `make graphql`
SPEC_DIR?=../../spec

#parse the vspec, and create a result.graphql file
# in ./generated directory. 
graphql:
	python3 ../vspec2graphql.py \
		"-i:${SPEC_DIR}/VehicleSignalSpecification.id" \
		"-I:${SPEC_DIR}" \
		"${SPEC_DIR}/VehicleSignalSpecification.vspec" \
		"./generated/result.graphql"

def get_node_identifier_bytes(
    qualified_name: str, data_type: str, node_type: str, unit: str
) -> bytes:
    # ToDo extended this for full functionality
    #  we need all breaking changes in the hash
    #  1. name
    #  2. change unit
    #  3. add unit to existing attribute
    #  4. change datatype
    #  5. add enum / rename enum value
    #  6. delete enum value
    #  7. add/change/delete min/max value
    return (
        f"{qualified_name}: "
        f"unit: {unit}, "
        f"datatype: {data_type}, "
        f"type: {node_type}"
    ).encode("utf-8")


def fnv1_32_hash(identifier: bytes) -> int:
    # data: bytes = get_node_identifier_bytes(node)
    id_hash = 2166136261
    for byte in identifier:
        id_hash = (id_hash * 16777619) & 0xFFFFFFFF
        id_hash ^= byte

    return id_hash


def fnv1_24_hash(identifier: bytes) -> int:
    # data = get_node_identifier_bytes(node)
    id_hash = 2166136261
    for byte in identifier:
        id_hash = (id_hash * 16777619) & 0xFFFFFF
        id_hash ^= byte

    return id_hash


def fnv1_32_wrapper(name: str, source: dict):
    identifier = get_node_identifier_bytes(
        name, source["datatype"], source["type"], source["unit"]
    )
    return format(fnv1_32_hash(identifier), "08X")

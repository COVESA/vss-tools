from vspec import VSSNode


def get_node_identifier_bytes(node: VSSNode) -> bytes:
    # ToDo extended this for full functionality
    return (
        f"{node.qualified_name()}: "
        f"datatype: {node.data_type_str}, "
        f"type: {node.type.value}, "
        f"unit: {node.get_unit()}"
    ).encode("utf-8")


def fnv1_32_hash(node: VSSNode) -> int:
    data: bytes = get_node_identifier_bytes(node)
    id_hash = 2166136261
    for byte in data:
        id_hash = (id_hash * 16777619) & 0xFFFFFFFF
        id_hash ^= byte

    return id_hash


def fnv1_24_hash(node: VSSNode) -> int:
    data = get_node_identifier_bytes(node)
    id_hash = 2166136261
    for byte in data:
        id_hash = (id_hash * 16777619) & 0xFFFFFF
        id_hash ^= byte

    return id_hash

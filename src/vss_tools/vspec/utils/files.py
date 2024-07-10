from vss_tools import log
from typing import Any, Optional
import json
from pathlib import Path


def write_json(data: dict[str, Any], file: Path, indent: Optional[int] = None) -> None:
    log.info(f"Writing json: {file.resolve()}")
    file.parent.mkdir(exist_ok=True, parents=True)
    with open(file, "w") as f:
        json.dump(data, f, indent=indent)

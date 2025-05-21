import json
from pathlib import Path
from typing import Dict, Any, Tuple
import ifcopenshell
from ifcopenshell.util.element import get_psets


def load_mapping(name: str) -> Dict[str, Any]:
    path = Path("src/ifc_processing/mappings") / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Mapping nicht gefunden: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_custom_pset(el) -> Dict[str, Any]:
    return get_psets(el)
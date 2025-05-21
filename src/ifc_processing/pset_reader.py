# ifc_processing/pset_reader.py

import ifcopenshell
from ifcopenshell.util.element import get_psets
from typing import Dict, Any


def read_psets_from_model(ifc) -> Dict[str, Dict[str, Any]]:
    """Return a mapping of GlobalId → all Psets and type."""
    result = {}
    for el in ifc.by_type("IfcElement"):
        global_id = el.GlobalId
        psets = get_psets(el)  # returns {PsetName: {key: val}}
        result[global_id] = {
            "type": el.is_a(),
            "psets": psets
        }
    return result


def flatten_psets(pset_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Flatten nested Pset data per element to one flat key-value layer with float-convertible values."""
    flattened = {}
    for gid, entry in pset_data.items():
        row = {"type": entry["type"]}
        for pset_name, pset in entry["psets"].items():
            for k, v in pset.items():
                key = f"{pset_name}.{k}"
                # Convert numeric strings to float if possible
                if isinstance(v, (int, float)):
                    val = v
                else:
                    val = str(v).strip()

                row[key] = val
        flattened[gid] = row
    return flattened

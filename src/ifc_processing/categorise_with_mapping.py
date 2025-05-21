from typing import Dict, Any, Tuple, List
from ifcopenshell.util.element import get_psets

def categorise_with_mapping(el, mapping: Dict[str, Any]) -> Tuple[str, Tuple[str, str, str], Dict[str, Any]]:
    psets = get_psets(el)
    name = el.Name or ""
    cat = el.is_a()
    gid = el.GlobalId

    rules = mapping.get("rules", {}).get(cat, {})
    selected_keys = set(rules.get("group", []) + rules.get("group2", []) +
                        rules.get("group3", []) + rules.get("sum", []) +
                        rules.get("text", []) + rules.get("ignore", []))

    props = {}
    for pset_name, keys in psets.items():
        for k, v in keys.items():
            combined = f"{pset_name}.{k}"
            if combined in selected_keys:
                props[combined] = v

    def label_from(keys: List[str]) -> str:
        return " / ".join(str(props.get(k, "")).strip() for k in keys) if keys else ""

    gruppe = label_from(rules.get("group", []))
    art    = label_from(rules.get("group2", []))
    status = label_from(rules.get("group3", []))

    return cat, (gruppe, art, status), props

# 📁 tools/aggregate_rows_custom.py
from typing import List, Dict, Any
from ifcopenshell.file import file
from ifc_processing.categorise_with_mapping import categorise_with_mapping

def _make_row(cat, grp, art, status, prop, val, never_convert_fields=[], ifc_class="") -> Dict[str, Any]:
    try:
        s = str(val).replace(",", ".").strip()

        if prop not in never_convert_fields:
            if s.lstrip("-").replace(".", "", 1).isdigit():
                val = float(s)
        else:
            # 🚫 NEW: prevent "531.0" and convert to clean string
            if s.endswith(".0"):
                val = s[:-2]
            else:
                val = s
    except:
        pass

    return {
        "Kategorie": cat,
        "Gruppe": grp,
        "Status": status,
        "Art": art,
        "Eigenschaft": prop,
        "Wert": val,
        "OriginalClass": ifc_class,
    }

def aggregate_rows_custom(ifc: file, mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for el in ifc.by_type("IfcElement"):
        cat, grp, props = categorise_with_mapping(el, mapping)

        status = el.ObjectType or ""
        art = grp[1] if isinstance(grp, (tuple, list)) and len(grp) > 1 else ""
        grp = grp[0] if isinstance(grp, (tuple, list)) and len(grp) > 0 else ""


        ifc_class = el.is_a()
        rules = mapping.get("rules", {}).get(ifc_class, {})
        text_fields = rules.get("text", [])

        for k, v in props.items():
            rows.append(_make_row(cat, grp, art, status, k, v, text_fields, ifc_class))

        rows.append(_make_row(cat, grp, art, status, "Stückzahl", 1, text_fields, ifc_class))

        if "Status" in text_fields or "Status" in rules.get("sum", []):
            rows.append(_make_row(cat, grp, art, status, "Status", status, text_fields, ifc_class))

        if "Art" in text_fields or "Art" in rules.get("sum", []):
            rows.append(_make_row(cat, grp, art, status, "Art", art, text_fields, ifc_class))

    return rows
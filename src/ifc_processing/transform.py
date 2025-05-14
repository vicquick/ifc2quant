from collections import defaultdict
import pandas as pd
from typing import Dict, List, Tuple
from .helpers import (
    categorise, 
    get_bq, 
    LENGTH_KEYS, 
    is_dtm_site, 
    get_all_psets,
    DISPLAY_NAMES
)

def aggregate(ifc, scale):
    """Process IFC elements with fixed columns and dynamic BQ summation"""
    groups: defaultdict = defaultdict(lambda: defaultdict(float))
    extra_bq_keys: set = set()
    pset_keys: set = set()

    for el in ifc.by_type("IfcElement"):
        cat, grp, thick_m, thick_raw = categorise(el, scale)
        g = groups[(cat, grp)]
        q = get_bq(el)

        # Handle DTM sites first
        if is_dtm_site(el):
            cat = "Site"
            grp = "Geländemodell"
            g = groups[(cat, grp)]
            all_props = get_all_psets(el)
            for k, v in all_props.items():
                if isinstance(v, (int, float, str)):
                    pset_keys.add(k)
                    g[k] = v
            continue

        # Fixed columns
        g["area"] += q.get("NetArea", 0) or q.get("GrossArea", 0) or q.get("Area", 0)
        g["length"] += (q.get("NetLength", 0) or q.get("GrossLength", 0) or q.get("Length", 0)) * scale
        
        # Height calculation
        h = q.get("NetHeight") or q.get("Height") or q.get("GrossHeight")
        if h:
            g.setdefault("height_sum", 0)
            g.setdefault("height_n", 0)
            g["height_sum"] += h * scale
            g["height_n"] += 1

        # Hedgerow specific
        if cat == "Hedgerow":
            hedge_plants = q.get("Count") or q.get("NumberOfPlants") or 0
            g["plant_count"] += hedge_plants
            g.setdefault("hedge_objects", 0)
            g["hedge_objects"] += 1

        # Thickness
        g["count"] += 1
        if thick_m is not None:
            g["thick_m"] = thick_m
            g["thick_raw"] = thick_raw

        # Dynamic BQ summation
        for k, v in q.items():
            if isinstance(v, (int, float)):
                key = k
                extra_bq_keys.add(key)
                g[key] += v if k not in LENGTH_KEYS else v * scale

    return groups, sorted(extra_bq_keys), sorted(pset_keys)

def to_dataframe(groups, bq_keys):
    """Convert to DataFrame with fixed columns first"""
    fixed_cols_order = [
        "area", "length", "thick_m", "thick_raw", 
        "height_sum", "height_n", "hedge_objects", 
        "plant_count", "count"
    ]
    
    rows = []
    for (cat, grp), d in groups.items():
        row = {
            "Kategorie": DISPLAY_NAMES.get(cat, cat),
            "Gruppe": grp,
            "Fläche_m2": d.get("area", 0),
            "Länge_m": d.get("length", 0),
            "Dicke_m": d.get("thick_m", ""),
            "Dicke_roh_mm": d.get("thick_raw", ""),
            "Höhe_m": round(d["height_sum"]/d["height_n"], 3) if d.get("height_n", 0) > 0 else "",
            "Anzahl_Hecken": d.get("hedge_objects", ""),
            "Anzahl_Pflanzen": d.get("plant_count", ""),
            "Anzahl": d.get("count", 0),
            **{k: d.get(k, 0) for k in bq_keys}
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    return df.set_index(["Kategorie", "Gruppe"])
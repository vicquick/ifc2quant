#!/usr/bin/env python3
"""
ifc_processing/helpers.py
=========================
Basis‐Utilities für den LL-AM-Workflow (Stand Mai 2025):

• Laden des zentralen LL-AM-Mappings (ll_am.json)
• Einheitenerkennung & Skalierung (mm ↔ m)
• Layer- und Status-Erkennung
• Rohdicke (Slab/Wall) aus PSet „LL AM“
• Element-Kategorisierung: Slab, Wall, Ramp, Stair, Tree, Hedgerow,
  Strauchpflanzung, Flächenpflanzung, Ausstattung/DGM/DTM, Other
"""
import json
import re
from pathlib import Path
from functools import lru_cache
from statistics import median
from typing import Dict, Any, List, Tuple
import pandas as pd


import ifcopenshell
from ifcopenshell.util.element import get_psets

@lru_cache(maxsize=1)
def ll_am_fields() -> List[Dict[str, Any]]:
    mapping_path = Path(__file__).resolve().parent / "mappings" / "ll_am.json"
    if not mapping_path.exists():
        raise FileNotFoundError(f"LL-AM-Mapping nicht gefunden: {mapping_path}")
    return json.loads(mapping_path.read_text(encoding="utf-8"))

DISPLAY_NAMES = {
    "Slab":             "Belag/Weg",
    "Wall":             "Wand",
    "Ramp":             "Rampe",
    "Stair":            "Treppe",
    "Tree":             "Baum",
    "Hedgerow":         "Hecke",
    "Strauchpflanzung": "Strauchpflanzung",
    "Flächenpflanzung": "Flächenpflanzung",
    "Furniture":        "Ausstattung",
    "Other":            "Sonstige",
    "Site":             "Geländemodell",
}
BOARD_MAPPING = {"RB": "Rasenbord", "TB": "Tiefbord"}

def declared_scale(ifc) -> float:
    pj = ifc.by_type("IfcProject")
    if not pj:
        return 1.0
    for u in pj[0].UnitsInContext.Units:
        if u.is_a("IfcSIUnit") and u.UnitType == "LENGTHUNIT":
            return {"MILLI": 0.001, "CENTI": 0.01, "DECI": 0.1}.get(getattr(u, "Prefix", None), 1.0)
        if u.is_a("IfcConversionBasedUnit") and u.UnitType == "LENGTHUNIT":
            return float(u.ConversionFactor.ValueComponent.wrappedValue)
    return 1.0

def auto_scale(ifc) -> float:
    s = declared_scale(ifc)
    if s != 1.0:
        return s
    samples = []
    for cls in ("IfcSlab", "IfcWall", "IfcWallStandardCase"):
        for el in ifc.by_type(cls)[:100]:
            r = raw_thickness(el)
            if r:
                samples.append(r)
    return 0.001 if samples and median(samples) > 5 else 1.0

def get_llam_pset(el) -> Dict[str, Any]:
    return get_psets(el).get("LL AM", {})

def get_layer(el) -> str:
    for rel in getattr(el, "HasAssignments", []):
        if rel.is_a("IfcPresentationLayerAssignment"):
            return rel.Name or ""
    return ""

def status_from_layer(layer: str) -> str:
    l = layer.lower()
    if "bestand" in l:
        return "Bestand"
    if "neu" in l or "neupflanz" in l:
        return "Neu"
    return ""

def material_name(el) -> str:
    for rel in getattr(el, "HasAssociations", []):
        if rel.is_a("IfcRelAssociatesMaterial"):
            mats = rel.RelatingMaterial
            if hasattr(mats, "Name"):
                return mats.Name
            if isinstance(mats, (list, tuple)) and mats:
                return mats[0].Name
            if hasattr(mats, "ForLayerSet") and mats.ForLayerSet.MaterialLayers:
                return mats.ForLayerSet.MaterialLayers[0].Material.Name
    return ""

def raw_thickness(el) -> float:
    p = get_llam_pset(el)
    if el.is_a("IfcSlab"):
        v = p.get("Höhe")
    elif el.is_a("IfcWall") or el.is_a("IfcWallStandardCase"):
        v = p.get("Breite")
    else:
        return 0.0
    try:
        return float(str(v).replace(",", ".")) if v not in (None, "") else 0.0
    except:
        return 0.0

def categorise(el, scale: float) -> Tuple[str, str, float, float, str, str, float]:
    name       = (el.Name or "").strip()
    layer      = get_layer(el)
    status     = status_from_layer(layer)
    pset       = get_llam_pset(el)
    raw_name   = (pset.get("Name") or "").upper()
    pset_names = [nm.upper() for nm in get_psets(el).keys()]

    if any("DGM" in nm or "DTM" in nm for nm in pset_names) or ("DGM" in raw_name or "DTM" in raw_name):
        return "Site", DISPLAY_NAMES["Site"], 0.0, 0.0, status, name, 1

    if el.is_a("IfcPlantingElement") or "FLÄCHENPFLANZUNG" in raw_name or "PFLANZFLÄCHE" in raw_name:
        art  = "Flächenpflanzung gesamt"
        area = float(str(pset.get("Fläche", 0) or 0).replace(",", "."))
        return "Flächenpflanzung", "Flächenpflanzung", 0.0, area, status, art, 0.0

    if el.is_a("IfcStair"):
        width = float(str(pset.get("Breite", 0) or 0).replace(",", "."))
        run   = float(str(pset.get("Auftritt Stufen", 0) or 0).replace(",", "."))
        steep = float(str(pset.get("Steigung Stufen", 0) or 0).replace(",", "."))
        grp_label = f"B:{round(width)} / A:{round(run)} / S:{round(steep)}"
        return "Stair", grp_label, 0.0, 0.0, status, grp_label, 0.0

    if el.is_a("IfcRamp"):
        width  = float(str(pset.get("Breite", 0) or 0).replace(",", "."))
        slope  = float(str(pset.get("Steigung Rampe", 0) or 0).replace(",", "."))
        tread  = float(str(pset.get("Auftritt Stufen", 0) or 0).replace(",", "."))
        grp_label = f"B:{round(width)} / A:{round(tread)} / S:{round(slope)}"
        return "Ramp", grp_label, 0.0, 0.0, status, grp_label, 0.0

    ...
    if raw_name.startswith("LL-"):
        parts      = [p for p in re.split(r"[-_]", raw_name) if p]
        domain     = parts[1] if len(parts) > 1 else ""
        obj        = parts[2] if len(parts) > 2 else ""
        status_tag = parts[3].capitalize() if len(parts) > 3 else ""

        if domain == "VEG" and obj == "HECKE":
            gruppe = pset.get("dt. Bezeichnung") or name
            art = pset.get("lat. Bezeichnung") or name
            return "Hedgerow", gruppe, 0.0, 0.0, status, art, 0.0

        if domain == "VEG" and obj == "STRAUCHPFLANZUNG":
            gruppe = pset.get("dt. Bezeichnung") or name
            art = pset.get("lat. Bezeichnung") or name
            try:
                height = float(str(pset.get("Höhe", 0)).replace(",", "."))
            except:
                height = 0.0
            try:
                kron = float(str(pset.get("Kronendurchmesser", 0)).replace(",", "."))
            except:
                kron = 0.0
            return "Strauchpflanzung", gruppe, 0.0, height, status, art, kron

        if domain == "VEG":
            gruppe = pset.get("dt. Bezeichnung") or name
            art = pset.get("lat. Bezeichnung") or name
            try:
                height = float(str(pset.get("Höhe", 0)).replace(",", "."))
            except:
                height = 0.0
            try:
                kron = float(str(pset.get("Kronendurchmesser", 0)).replace(",", "."))
            except:
                kron = 0.0
            return "Tree", gruppe, 0.0, height, status_tag or status, art, kron

        if domain in ("AUS", "EIN"):
            suffix = parts[-1].title()
            grp    = BOARD_MAPPING.get(parts[-1].upper(), suffix)
            return "Furniture", grp, 0.0, 0.0, status, grp, 0.0

        if obj.upper() in ("MÜLL", "FAHRRAD", "BANK", "TISCH", "SITZ", "SITZGELEGENHEIT", "SPIEL"):
            grp = obj.title()
            return "Furniture", grp, 0.0, 0.0, status, grp, 0.0

        if domain == "TGA":
            grp = obj.title() if obj else name
            return "Furniture", grp, 0.0, 0.0, status, grp, 0.0

        return "Other", name or el.is_a(), 0.0, 0.0, status, name, 0.0

    if el.is_a("IfcFurnishingElement") or el.is_a("IfcFurniture") or el.is_a("IfcFurnitureType"):
        grp = (el.ObjectType or el.Name or "Unbenannt").strip()
        return "Furniture", grp, 0.0, 0.0, status, grp, 0.0

    if "STRAUCH" in raw_name or "STRAUCH" in name.upper():
        gruppe = pset.get("dt. Bezeichnung") or name
        art    = pset.get("lat. Bezeichnung") or name
        try:
            height = float(str(pset.get("Höhe", 0)).replace(",", "."))
        except:
            height = 0.0
        try:
            kron = float(str(pset.get("Kronendurchmesser", 0)).replace(",", "."))
        except:
            kron = 0.0
        return "Strauchpflanzung", gruppe, 0.0, height, status, art, kron


    if el.is_a("IfcBuildingElementProxy") and (pset.get("dt. Bezeichnung") or pset.get("lat. Bezeichnung")) and not any(x in raw_name or x in name.upper() for x in ["STRAUCH", "FLÄCHENPFLANZUNG", "HECKE"]):
        gruppe = pset.get("dt. Bezeichnung") or name
        art = pset.get("lat. Bezeichnung") or name
        try:
            height = float(str(pset.get("Höhe", 0)).replace(",", "."))
        except:
            height = 0.0
        try:
            kron = float(str(pset.get("Kronendurchmesser", 0)).replace(",", "."))
        except:
            kron = 0.0
        return "Tree", gruppe, 0.0, height, status, art, kron

    if "BAUM" in name.upper() and "STRAUCH" not in name.upper():
        gruppe = pset.get("dt. Bezeichnung") or name
        art = pset.get("lat. Bezeichnung") or name
        try:
            height = float(str(pset.get("Höhe", 0)).replace(",", "."))
        except:
            height = 0.0
        try:
            kron = float(str(pset.get("Kronendurchmesser", 0)).replace(",", "."))
        except:
            kron = 0.0
        return "Tree", gruppe, 0.0, height, status, art, kron


    if el.is_a("IfcSlab"):
        raw = raw_thickness(el)
        m   = raw * scale
        mat = material_name(el) or name or "Unspecified"
        return "Slab", mat, m, raw, status, mat, 0.0

    if el.is_a("IfcWall") or el.is_a("IfcWallStandardCase"):
        raw = raw_thickness(el)
        m   = raw * scale
        return "Wall", name or "Unnamed Wall", m, raw, status, name, 0.0

    tag = getattr(el, "Tag", "") or el.is_a()
    return "Other", tag, 0.0, 0.0, status, name, 0.0

def convert_units_mm_to_m(df: pd.DataFrame) -> pd.DataFrame:
    """Converts all mm-defined LL-AM fields in the wide dataframe to meters, and adds '[m]' suffix."""
    for f in ll_am_fields():
        key, unit = f["key"], f.get("unit")
        if unit == "mm" and key in df.columns:
            # Try to convert to numeric first
            df_numeric = pd.to_numeric(df[key], errors="coerce")
            df[f"{key} [m]"] = df_numeric * 0.001
            df.drop(columns=[key], inplace=True)
    return df


def add_mm_suffix(df: pd.DataFrame) -> pd.DataFrame:
    """Appends '(mm)' to all LL-AM fields that have unit == mm."""
    rename_map = {}
    for f in ll_am_fields():
        key, unit = f["key"], f.get("unit")
        if unit == "mm" and key in df.columns:
            rename_map[key] = f"{key} (mm)"
    return df.rename(columns=rename_map)
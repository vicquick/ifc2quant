#!/usr/bin/env python3
"""
ifc_processing/helpers.py - Core IFC processing functions
==============================================
Contains all fundamental IFC processing functionality:
- Unit detection and scaling
- Element categorization
- Property extraction
"""

from collections import defaultdict
from statistics import median
from typing import Dict, List, Tuple, Optional, DefaultDict, Any
import ifcopenshell
from ifcopenshell.util.element import get_psets

# Constants
TREE_KEYWORDS = [
    "baum", "tree", "arbor", "gehölz", "ahorn", "acer", "eiche", "oak",
    "birke", "betula", "linde", "tilia", "kastanie", "chestnut", "pinus",
    "kiefer", "pine", "fichte", "spruce", "platan", "plane", "ulme", "elm",
    "esche", "ash", "laub", "malus", "prunus", "sorbus", "alnus", "robinie",
    "robinia", "feldahorn", "quercus"
]

DISPLAY_NAMES = {
    "Slab": "Belag/Weg",
    "Hedgerow": "Hecke",
    "Wall": "Wand",
    "Tree": "Baum",
    "Furniture": "Ausstattung",
    "Other": "Sonstige",
    "Site": "Geländemodell"
}

LENGTH_KEYS = {"Length", "NetLength", "GrossLength", "Perimeter", "Width", "NetWidth"}

# --------------------------- Unit Detection -----------------------------

def declared_scale(ifc):
    """Detect declared length units in IFC file"""
    pj = ifc.by_type("IfcProject")
    if not pj:
        return 1.0
    units = pj[0].UnitsInContext.Units
    for u in units:
        if u.is_a("IfcSIUnit") and u.UnitType == "LENGTHUNIT":
            return {"MILLI": 0.001, "CENTI": 0.01, "DECI": 0.1}.get(getattr(u, "Prefix", None), 1.0)
        if u.is_a("IfcConversionBasedUnit") and u.UnitType == "LENGTHUNIT":
            return float(u.ConversionFactor.ValueComponent.wrappedValue)
    return 1.0

def auto_scale(ifc):
    """Auto-detect scaling factor (mm→m if needed)"""
    s = declared_scale(ifc)
    if s != 1.0:
        return s
    samples = [raw_thickness(el) for cls in ("IfcSlab", "IfcWall", "IfcWallStandardCase")
               for el in ifc.by_type(cls)[:100] if raw_thickness(el)]
    return 0.001 if samples and median(samples) > 5 else 1.0

# --------------------------- Property Extraction -----------------------------

def get_bq(el) -> Dict[str, float]:
    """Get BaseQuantities property set"""
    return get_psets(el).get("BaseQuantities", {})

def raw_thickness(el):
    """Get raw thickness from wall/slab properties"""
    t = get_psets(el).get("Pset_WallCommon", {}).get("NominalThickness") or \
        get_psets(el).get("Pset_SlabCommon", {}).get("NominalThickness")
    if t:
        return float(t)
    q = get_bq(el)
    return float(q.get("Width") or q.get("NetWidth") or 0.0)

def material_name(el):
    """Extract material name from element"""
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

# --------------------------- Categorization -----------------------------

def is_tree(text: str) -> bool:
    """Check if element should be categorized as tree"""
    low = text.lower()
    return any(kw in low for kw in TREE_KEYWORDS)

def categorise(el, scale):
    """Categorize IFC element and determine grouping key"""
    name = (el.Name or "").strip()
    obj = (getattr(el, "ObjectType", "") or "").strip()
    tag = getattr(el, "Tag", "") or ""

    if el.is_a("IfcSlab"):
        t_raw = raw_thickness(el)
        t_m = t_raw * scale
        mat = material_name(el) or name or "Unspecified"
        grp = f"{mat}|{round(t_m,3)}" if t_m else mat
        return "Slab", grp, t_m, t_raw

    if el.is_a("IfcWall") or el.is_a("IfcWallStandardCase"):
        t_raw = raw_thickness(el)
        t_m = t_raw * scale
        grp = f"{name or 'Unnamed Wall'}|{round(t_m,3)}"
        return "Wall", grp, t_m, t_raw

    blob = f"{name} {obj} {tag}"
    if is_tree(blob):
        return "Tree", (name or tag or "Tree"), None, None
    if "hedge" in blob.lower() or "hecke" in blob.lower():
        return "Hedgerow", (name or tag or "Hecke"), None, None

    if el.is_a("IfcFurniture") or el.is_a("IfcFurnishingElement") or el.is_a("IfcBuildingElementProxy"):
        desc = (getattr(el, "Description", "") or name or obj or tag or "Unnamed").strip()
        return "Furniture", desc, None, None

    return "Other", (tag or el.is_a()), None, None

def get_all_psets(el):
    """Get all property sets for an element"""
    psets = get_psets(el)
    return {k: v for pset in psets.values() for k, v in pset.items()}

def is_dtm_site(el):
    """Check if element is a DTM site"""
    return (el.is_a("IfcSite") and 
           el.Name and "Geländemodell" in el.Name)

def get_site_properties(ifc) -> Dict[str, Any]:
    """Get all properties from DTM sites in the model"""
    sites = [s for s in ifc.by_type("IfcSite") if is_dtm_site(s)]
    if not sites:
        return {}
    
    # Merge properties from all DTM sites
    all_props = {}
    for site in sites:
        all_props.update(get_all_psets(site))
    return all_props
# 📁 tools/ifchelper.py — Extraction logic for grouped quantities with SmartHash support

import ifcopenshell
from collections import defaultdict
import hashlib


def get_elements_by_class(ifc_model, class_names):
    """Return elements of multiple IFC classes."""
    elements = []
    for cls in class_names:
        elements.extend(ifc_model.by_type(cls))
    return elements


def compute_volume(element):
    """Stub for volume extraction (extend as needed)."""
    return float(element.get_info().get("Volume", 0.0))


def extract_psets(element):
    """Flatten all Pset properties into a key-value dict."""
    props = {}
    for definition in element.IsDefinedBy:
        if definition.is_a("IfcRelDefinesByProperties"):
            prop_set = definition.RelatingPropertyDefinition
            if prop_set.is_a("IfcPropertySet"):
                for p in prop_set.HasProperties:
                    props[f"{prop_set.Name}.{p.Name}"] = getattr(p, "NominalValue", None)
    return props


def smart_hash(element, keys=None):
    """
    Generate a stable hash based on type, selected props, and volume.
    `keys` can be a list of keys to include (optional).
    """
    info = element.get_info()
    class_name = info["type"]
    volume = compute_volume(element)
    props = extract_psets(element)

    if keys:
        relevant = [(k, str(props.get(k, ""))) for k in sorted(keys)]
    else:
        relevant = [(k, str(v)) for k, v in sorted(props.items())]

    base = class_name + str(volume) + "".join([f"{k}:{v}" for k, v in relevant])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def extract_grouped_quantities(ifc_model, mapping):
    """
    Applies mapping to elements and returns dict of ((Group, Category, Key) → Sum).
    """
    quantities = defaultdict(float)

    for class_name, rules in mapping.get("rules", {}).items():
        elements = ifc_model.by_type(class_name)
        for el in elements:
            props = extract_psets(el)
            volume = compute_volume(el)

            for rule in rules:
                group = rule.get("group", "")
                category = rule.get("category", class_name)
                key = rule.get("key", "Volume")

                val = props.get(key, volume if key == "Volume" else 0.0)
                try:
                    val = float(val)
                except:
                    val = 0.0

                quantities[(group, category, key)] += val

    return dict(quantities)

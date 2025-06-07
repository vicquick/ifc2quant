# 📁 tools/indexer.py — Build ID and hash indexes for comparison

from collections import defaultdict
from tools.ifchelper import extract_psets, smart_hash

def build_index_dict(ifc_model, mapping, smart_keys=None):
    """
    Returns dictionaries:
    - global_id → smart_hash
    - smart_hash → [global_ids] (to allow reverse lookup)
    - global_id → grouped_key (for quantity comparison alignment)
    """
    gid_to_hash = {}
    hash_to_gids = defaultdict(list)
    gid_to_groupkey = {}

    for class_name, rules in mapping.get("rules", {}).items():
        elements = ifc_model.by_type(class_name)

        for el in elements:
            gid = el.GlobalId
            shash = smart_hash(el, keys=smart_keys)
            gid_to_hash[gid] = shash
            hash_to_gids[shash].append(gid)

            cat = rules.get("category", class_name)
            group = ", ".join(rules.get("group", []))
            art = el.Name or ""
            status = el.ObjectType or ""
            gid_to_groupkey[gid] = (cat, group, art, status)

    return gid_to_hash, hash_to_gids, gid_to_groupkey

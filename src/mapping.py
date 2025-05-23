import streamlit as st
from translations import translations

def render_rename_tab():
    lang = st.session_state.get("lang", "en")
    t = translations[lang]

    if "all_classes" not in st.session_state or "class_keys_map" not in st.session_state:
        st.warning("⚠️ " + t.get("upload_warning", "Please upload an IFC file first."))
        return

    all_classes = st.session_state["all_classes"]
    class_keys_map = st.session_state["class_keys_map"]
    loaded_mapping = st.session_state.get("loaded_mapping", {})

    st.session_state.setdefault("category_mapping", loaded_mapping.get("categories", {}))
    st.session_state.setdefault("class_rules", loaded_mapping.get("rules", {}))

    st.subheader("📚 " + t.get("rename_ifc_classes", "Rename IFC classes (optional)"))
    category_mapping = {}

    for cls in all_classes:
        default = st.session_state["category_mapping"].get(cls, cls)
        label = st.text_input(f"{cls} →", value=default, key=f"cat_{cls}")
        category_mapping[cls] = label.strip() if label.strip() else cls

    st.subheader("🎛️ " + t.get("rules_per_class", "Rules per class (only if activated)"))

    class_rules = {}
    activation_map = {}

    for cls in all_classes:
        existing = st.session_state["class_rules"].get(cls, {})
        group_keys = class_keys_map.get(cls, [])

        active = st.checkbox("✅ " + t.get("activate_class", "{cls} aktivieren").format(cls=cls), value=cls in st.session_state.get("active_classes", []), key=f"active_{cls}")
        activation_map[cls] = active

        with st.expander(f"Regeln für {cls}", expanded=active):
            group = st.multiselect("🔑 " + t.get("rule_group", "Group"), group_keys, default=existing.get("group", []), key=f"group_{cls}")
            group2 = st.multiselect("🎨 " + t.get("rule_type", "Type"), group_keys, default=existing.get("group2", []), key=f"group2_{cls}")
            group3 = st.multiselect("📌 " + t.get("rule_status", "Status"), group_keys, default=existing.get("group3", []), key=f"group3_{cls}")
            sum_keys = st.multiselect("➕ " + t.get("rule_sum", "Summed fields"), group_keys, default=existing.get("sum", []), key=f"sum_{cls}")
            text = st.multiselect("📝 " + t.get("rule_text", "Text fields"), group_keys, default=existing.get("text", []), key=f"text_{cls}")
            ignore = st.multiselect("🚫 " + t.get("rule_ignore", "Ignored"), group_keys, default=existing.get("ignore", []), key=f"ignore_{cls}")

            class_rules[cls] = {
                "group": group,
                "group2": group2,
                "group3": group3,
                "sum": sum_keys,
                "text": text,
                "ignore": ignore,
            }

    active_classes = [cls for cls in all_classes if activation_map.get(cls)]

    st.session_state["category_mapping"] = category_mapping
    st.session_state["class_rules"] = class_rules
    st.session_state["rules"] = class_rules  # optional for legacy use
    st.session_state["active_classes"] = active_classes
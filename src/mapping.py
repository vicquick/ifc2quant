import streamlit as st

def render_rename_tab():
    if "all_classes" not in st.session_state or "class_keys_map" not in st.session_state:
        st.warning("⚠️ Bitte zuerst eine IFC-Datei hochladen.")
        return

    all_classes = st.session_state["all_classes"]
    class_keys_map = st.session_state["class_keys_map"]
    loaded_mapping = st.session_state.get("loaded_mapping", {})

    # Apply loaded mappings into session
    st.session_state.setdefault("category_mapping", loaded_mapping.get("categories", {}))
    st.session_state.setdefault("class_rules", loaded_mapping.get("rules", {}))

    st.subheader("📚 IFC-Klassen umbenennen (optional)")
    category_mapping = {}

    for cls in all_classes:
        default = st.session_state["category_mapping"].get(cls, cls)
        label = st.text_input(f"{cls} →", value=default, key=f"cat_{cls}")
        category_mapping[cls] = label.strip() if label.strip() else cls

    st.subheader("🎛️ Regeln für jede Klasse (nur bei Aktivierung berücksichtigt)")

    class_rules = {}
    activation_map = {}

    for cls in all_classes:
        existing = st.session_state["class_rules"].get(cls, {})
        group_keys = class_keys_map.get(cls, [])

        active = st.checkbox(f"✅ {cls} aktivieren", value=cls in st.session_state.get("active_classes", []), key=f"active_{cls}")
        activation_map[cls] = active

        with st.expander(f"Regeln für {cls}", expanded=active):
            group = st.multiselect("🔑 Gruppierung", group_keys, default=existing.get("group", []), key=f"group_{cls}")
            group2 = st.multiselect("🎨 Art", group_keys, default=existing.get("group2", []), key=f"group2_{cls}")
            group3 = st.multiselect("📌 Status", group_keys, default=existing.get("group3", []), key=f"group3_{cls}")
            sum_keys = st.multiselect("➕ Summenfelder", group_keys, default=existing.get("sum", []), key=f"sum_{cls}")
            text = st.multiselect("📝 Textfelder", group_keys, default=existing.get("text", []), key=f"text_{cls}")
            ignore = st.multiselect("🚫 Ignorieren", group_keys, default=existing.get("ignore", []), key=f"ignore_{cls}")

            class_rules[cls] = {
                "group": group,
                "group2": group2,
                "group3": group3,
                "sum": sum_keys,
                "text": text,
                "ignore": ignore,
            }

    active_classes = [cls for cls in all_classes if activation_map.get(cls)]

    # Final save into session state
    st.session_state["category_mapping"] = category_mapping
    st.session_state["class_rules"] = class_rules
    st.session_state["rules"] = class_rules  # optional for legacy use
    st.session_state["active_classes"] = active_classes

    # Optional debug
    #st.write("📥 Gespeicherte Regeln:", class_rules)

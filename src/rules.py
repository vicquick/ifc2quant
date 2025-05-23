import streamlit as st
from mapping_editor import edit_mapping_ui
from translations import translations

def render_rules_tab():
    lang = st.session_state.get("lang", "en")
    t = translations[lang]

    if "all_classes" not in st.session_state or "class_keys_map" not in st.session_state:
        st.warning("⚠️ " + t.get("upload_warning", "Please upload and rename an IFC file first."))
        return

    all_classes = st.session_state["all_classes"]
    class_keys_map = st.session_state["class_keys_map"]
    loaded_mapping = st.session_state.get("loaded_mapping", {})
    loaded_mapping["categories"] = st.session_state.get("category_mapping", {})
    loaded_mapping["rules"] = st.session_state.get("class_rules", {})

    _, class_rules, active_classes = edit_mapping_ui(
        all_classes, class_keys_map, loaded_mapping
    )

    st.session_state["class_rules"] = class_rules
    st.session_state["rules"] = class_rules  # for legacy fallback
    st.session_state["active_classes"] = active_classes

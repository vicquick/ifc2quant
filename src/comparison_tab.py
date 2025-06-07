# 📁 comparison_tab.py

import streamlit as st
import pandas as pd
from pathlib import Path
import ifcopenshell

from translations import translations
from ifc_processing.pset_reader import read_psets_from_model, flatten_psets
from ifc_processing.render_rule_block import render_rule_block
from tools.comparison_logic import prepare_comparison, format_diff_table_with_styles

def render_comparison_tab():
    lang = st.session_state.get("lang", "en")
    t = translations[lang]

    st.header("🔁 " + t.get("comparison_tab_title", "Compare with Second IFC Model"))

    model_a = st.session_state.get("ifc_model")
    model_a_name = st.session_state.get("ifc_filename")

    # 🔄 Pick up live mapping from session state if modified in mapping tab
    live_mapping = st.session_state.get("loaded_mapping", {}).copy()
    if "category_mapping" in st.session_state:
        live_mapping["categories"] = st.session_state["category_mapping"]
    if "class_rules" in st.session_state:
        live_mapping["rules"] = st.session_state["class_rules"]

    mapping = live_mapping  # use updated version

    if model_a is None or model_a_name is None:
        st.warning("⚠️ " + t.get("comparison_model_a_missing", "Please upload and map Model A first."))
        return

    uploaded_b = st.file_uploader("📂 " + t.get("comparison_upload_model_b", "Upload Model B"), type="ifc")

    if uploaded_b:
        cache_dir = Path(__file__).resolve().parent.parent / "cache"
        cache_dir.mkdir(exist_ok=True)
        model_b_path = cache_dir / uploaded_b.name
        model_b_path.write_bytes(uploaded_b.getbuffer())
        model_b = ifcopenshell.open(str(model_b_path))

        st.success(f"✅ {t.get('comparison_model_b_loaded', 'Model B')} '{uploaded_b.name}' {t.get('upload_success', 'loaded.')}" )

        # 🔧 Build keys from Model B
        psets = read_psets_from_model(model_b)
        flat_data = flatten_psets(psets)
        all_classes = sorted({el.is_a() for el in model_b.by_type("IfcElement")})
        class_keys_map_b = {
            cls: sorted({
                k for gid, props in flat_data.items() if props.get("type") == cls
                for k in props if not k.lower().startswith("type")
            })
            for cls in all_classes
        }

        st.subheader("🛠️ " + t.get("rules_per_class", "Rules per class (only if activated)"))
        mapping_b = {}
        activation_map = {}

        for cls in all_classes:
            existing = mapping.get("rules", {}).get(cls, {})
            group_keys = class_keys_map_b.get(cls, [])

            active_class_list = st.session_state.get("active_classes", [])
            active = st.checkbox("✅ " + t["activate_class"].format(cls=cls), value=cls in active_class_list, key=f"active_b_{cls}")
            activation_map[cls] = active

            def filter_defaults(field: str):
                return [v for v in existing.get(field, []) if v in group_keys]

            with st.expander(f"{t.get('rules_for', 'Regeln für')} {cls}", expanded=active):
                rule_set = {
                    "group": st.multiselect("🔑 " + t.get("rule_group", "Group"), group_keys, default=filter_defaults("group"), key=f"group_b_{cls}"),
                    "group2": st.multiselect("🎨 " + t.get("rule_type", "Type"), group_keys, default=filter_defaults("group2"), key=f"group2_b_{cls}"),
                    "group3": st.multiselect("📌 " + t.get("rule_status", "Status"), group_keys, default=filter_defaults("group3"), key=f"group3_b_{cls}"),
                    "sum": st.multiselect("➕ " + t.get("rule_sum", "Summed fields"), group_keys, default=filter_defaults("sum"), key=f"sum_b_{cls}"),
                    "text": st.multiselect("📝 " + t.get("rule_text", "Text fields"), group_keys, default=filter_defaults("text"), key=f"text_b_{cls}"),
                    "ignore": st.multiselect("🚫 " + t.get("rule_ignore", "Ignored"), group_keys, default=filter_defaults("ignore"), key=f"ignore_b_{cls}")
                }
                mapping_b[cls] = rule_set

        active_classes = [cls for cls in all_classes if activation_map.get(cls)]
        derived_mapping_b = {"rules": {cls: mapping_b[cls] for cls in active_classes}}

        # 🔍 Run comparison
        diff_df = prepare_comparison(model_a, model_b, mapping, derived_mapping_b)

        st.subheader("🔎 " + t.get("preview_tab", "Preview"))

        if diff_df.empty or diff_df.dropna(how="all").empty:
            st.info("ℹ️ " + t.get("no_differences", "No differences detected between Model A and Model B."))
        else:
            st.dataframe(diff_df, use_container_width=True)

            # 📅 Export
            csv = diff_df.to_csv(index=False).encode("utf-8")
            st.download_button("📅 " + t.get("download_csv", "CSV Export"), data=csv, file_name="comparison.csv", mime="text/csv")

            styled_excel = format_diff_table_with_styles(diff_df)
            st.download_button("📅 " + t.get("download_excel", "Styled Excel"), data=styled_excel, file_name="comparison.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
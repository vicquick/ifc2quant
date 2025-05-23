import streamlit as st
import pandas as pd
from ifc_processing.categorise_with_mapping import categorise_with_mapping
from ifc_processing.aggregate_rows_custom import _make_row
from ifc_processing.transform import (
    aggregate_by_mapping_per_class,
    simplify_text_fields,
    format_display,
)
from translations import translations

def render_preview_tab():
    lang = st.session_state.get("lang", "en")
    t = translations[lang]

    if "ifc_model" not in st.session_state or "active_classes" not in st.session_state:
        st.warning("⚠️ " + t.get("preview_warning", "Please upload an IFC file and define rules first."))
        return

    ifc_model = st.session_state["ifc_model"]
    active_classes = st.session_state["active_classes"]
    category_mapping = st.session_state["category_mapping"]
    class_rules = st.session_state["class_rules"]

    mapping = {
        "categories": category_mapping,
        "rules": {
            cls: class_rules.get(cls, {"text": [], "sum": []}) for cls in active_classes
        },
    }

    never_convert_fields = set()
    for cls, rules in mapping["rules"].items():
        never_convert_fields.update(rules.get("text", []))
        never_convert_fields.update(rules.get("group", []))
        never_convert_fields.update(rules.get("group2", []))
        never_convert_fields.update(rules.get("group3", []))
        never_convert_fields.update(rules.get("ignore", []))

    st.session_state["final_mapping"] = mapping

    preview_rows = []
    seen_ids = set()
    for el in ifc_model.by_type("IfcElement"):
        if el.id() in seen_ids:
            continue
        seen_ids.add(el.id())
        if el.is_a() not in active_classes:
            continue

        original_cat, grp, props = categorise_with_mapping(el, mapping)
        cat = mapping["categories"].get(el.is_a(), original_cat)

        if grp and len(grp) == 3:
            group_label, art, status = grp
        else:
            group_label, art, status = "", "", ""

        cat_label = t.get("Kategorie", "Category")
        group_label_name = t.get("Gruppe", "Group")
        art_label = t.get("Art", "Type")
        status_label = t.get("Status", "Status")
        count_label = t.get("Stückzahl", "Count")

        for k, v in props.items():
            if k in never_convert_fields:
                v = str(v)
            preview_rows.append(_make_row(cat, group_label, art, status, k, v, never_convert_fields) | {"OriginalClass": el.is_a()})

        preview_rows.append(_make_row(cat, group_label, art, status, count_label, 1, never_convert_fields) | {"OriginalClass": el.is_a()})

    if preview_rows:
        df = pd.DataFrame(preview_rows)
        df_final = aggregate_by_mapping_per_class(df, mapping)
        df_final = simplify_text_fields(df_final, mapping)

        for col in ["Status", "Art"]:
            is_used = any(col in rules.get("text", []) or col in rules.get("sum", []) for rules in mapping["rules"].values())
            if col in df_final.columns and not is_used:
                if df_final[col].replace("", pd.NA).isna().all():
                    df_final.drop(columns=[col], inplace=True)

        for col in df_final.select_dtypes(include="object").columns:
            df_final[col] = df_final[col].astype(str)

        if count_label in df_final.columns:
            df_final[count_label] = pd.to_numeric(df_final[count_label], errors="coerce").fillna(0).astype("Int64")

        df_final.fillna("", inplace=True)
        df_final.rename(columns={
            "Kategorie": t.get("Kategorie", "Category"),
            "Gruppe": t.get("Gruppe", "Group"),
            "Art": t.get("Art", "Type"),
            "Status": t.get("Status", "Status"),
            "Stückzahl": count_label
        }, inplace=True)

        st.session_state["df_final"] = df_final

        display_df = df_final

        # 🔘 Format toggle UI
        format_style = st.radio(
            t.get("number_format_label", "Choose number format:"),
            options=["🇩🇪 Deutsch (1.234,56)", "🇬🇧 English (1,234.56)"],
            index=0,
            horizontal=True,
        )
        style_key = "de" if "Deutsch" in format_style else "en"

        display_df = format_display(display_df, style=style_key, never_convert_fields=never_convert_fields)
        st.dataframe(display_df, use_container_width=True)

        suffix = "quantity_export" if lang == "en" else "Mengenauswertung"
        csv_data = display_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 " + t.get("download_csv", "Download CSV"), csv_data, f"{st.session_state.get('ifc_filename', 'export')}_{suffix}.csv", "text/csv")
    else:
        st.warning("⚠️ " + t.get("no_data_warning", "No data to display."))
        st.write(t.get("possible_causes", "🔍 Possible causes:"))
        st.write("- " + t.get("rules_not_set", "Have rules been defined for the classes?"))
        st.write("- " + t.get("groups_not_detected", "Were groups detected correctly?"))
        st.write("- " + t.get("props_empty", "Were props empty?"))

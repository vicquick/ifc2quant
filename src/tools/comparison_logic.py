# 📁 tools/comparison_logic.py — Prepare and align grouped tables for comparison

import streamlit as st
import pandas as pd
from ifc_processing.aggregate_rows_custom import aggregate_rows_custom
from ifc_processing.transform import aggregate_by_mapping_per_class, simplify_text_fields
from tools.diff import compare_grouped_quantities
from tools.text_diff import compare_text_fields
from tools.excel_export import format_diff_table_with_styles
from translations import translations


def prepare_comparison(model_a, model_b, mapping_a, mapping_b):
    """
    Generate and align comparison-ready dataframes from both models.
    Only compares mapped numeric and text fields, always includes count (©Stückzahl).
    """
    lang = st.session_state.get("lang", "en")
    t = translations[lang]

    df_a = pd.DataFrame(aggregate_rows_custom(model_a, mapping_a))
    df_b = pd.DataFrame(aggregate_rows_custom(model_b, mapping_b))

    grouped_a = simplify_text_fields(aggregate_by_mapping_per_class(df_a, mapping_a), mapping_a)
    grouped_b = simplify_text_fields(aggregate_by_mapping_per_class(df_b, mapping_b), mapping_b)

    index_cols = [col for col in ["Kategorie", "Gruppe", "Art", "Status"] if col in grouped_a.columns and col in grouped_b.columns]
    diff_rows = []

    # Collect all explicitly mapped fields (preserve order)
    mapped_fields = []
    for rules in mapping_a.get("rules", {}).values():
        for field in rules.get("sum", []) + rules.get("text", []):
            if field not in mapped_fields:
                mapped_fields.append(field)

    def append_numeric_diff(field, custom_label=None):
        if field in grouped_a.columns and field in grouped_b.columns:
            a_series = grouped_a.set_index(index_cols)[field].astype(float)
            b_series = grouped_b.set_index(index_cols)[field].astype(float)
            diff = compare_grouped_quantities(a_series, b_series, lang=lang)
            if diff is not None and "Delta" in diff.columns:
                diff = diff[diff["Delta"].ne(0)]
            if diff is not None and not diff.empty:
                label = custom_label if custom_label else (field.split(".")[-1] if "." in field else field)
                diff["Eigenschaft"] = label
                diff_rows.append(diff)

    # Always include count comparison
    count_key = "Stückzahl"
    append_numeric_diff(count_key, custom_label=count_key)

    for field in mapped_fields:
        if field in grouped_a.columns:
            append_numeric_diff(field)

    # Text comparison: only mapped fields if column exists
    if "Eigenschaft" in df_a.columns and "Eigenschaft" in df_b.columns:
        df_a_text = df_a[df_a["Eigenschaft"].isin(mapped_fields)]
        df_b_text = df_b[df_b["Eigenschaft"].isin(mapped_fields)]
        text_diff = compare_text_fields(df_a_text, df_b_text, lang=lang)
        if text_diff is not None and not text_diff.empty:
            text_diff = text_diff[text_diff["Delta"] != ""]
            diff_rows.append(text_diff)

    combined = pd.concat(diff_rows, ignore_index=True, sort=False) if diff_rows else pd.DataFrame()

    # Rename only once at the end
    rename = {
        "Kategorie": t["Kategorie"],
        "Gruppe": t["Gruppe"],
        "Art": t["Art"],
        "Status": t["Status"],
        "Eigenschaft": t["Property"],
        "Wert A": t["Wert A"],
        "Wert B": t["Wert B"],
        "Change": t["Change"]
    }
    for col in ["Kategorie", "Gruppe", "Art", "Status", "Eigenschaft", "Wert A", "Wert B", "Delta", "Change"]:
        if col not in combined.columns:
            combined[col] = ""

    combined.rename(columns=rename, inplace=True)

    return combined[[
        t["Kategorie"], t["Gruppe"], t["Art"], t["Status"],
        t["Property"], t["Wert A"], t["Wert B"], "Delta", t["Change"]
    ]]

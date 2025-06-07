# 📁 tools/text_diff.py — Compare non-aggregated text fields between models

import pandas as pd
import streamlit as st
from translations import translations

def compare_text_fields(df_a: pd.DataFrame, df_b: pd.DataFrame, lang=None) -> pd.DataFrame:
    """
    Compare text fields between two dataframes on grouped keys.
    Keys: Kategorie, Gruppe, Art, Status, Eigenschaft
    """
    lang = lang or st.session_state.get("lang", "en")
    t = translations[lang]

    # Always use internal column keys for logic
    key_cols = [col for col in ["Kategorie", "Gruppe", "Art", "Status", "Eigenschaft"] if col in df_a.columns and col in df_b.columns]

    lookup_a = df_a.set_index(key_cols)["Wert"].astype(str)
    lookup_b = df_b.set_index(key_cols)["Wert"].astype(str)

    all_keys = set(lookup_a.index).union(lookup_b.index)
    rows = []

    for key in sorted(all_keys):
        val_a = lookup_a[key] if key in lookup_a else ""
        val_b = lookup_b[key] if key in lookup_b else ""

        if isinstance(val_a, pd.Series):
            val_a = val_a.values[0]
        if isinstance(val_b, pd.Series):
            val_b = val_b.values[0]

        val_a_str = str(val_a)
        val_b_str = str(val_b)

        if val_a_str == val_b_str:
            status = t["unchanged"]
        elif val_a_str == "":
            status = t["added"]
        elif val_b_str == "":
            status = t["removed"]
        else:
            status = t["changed"]

        row = {
            "Kategorie": key[0] if len(key) > 0 else None,
            "Gruppe": key[1] if len(key) > 1 else None,
            "Art": key[2] if len(key) > 2 else None,
            "Status": key[3] if len(key) > 3 else None,
            "Eigenschaft": key[4] if len(key) > 4 else None,
            "Wert A": val_a_str,
            "Wert B": val_b_str,
            "Change": status
        }

        # Set Eigenschaft as shortened name
        if isinstance(row["Eigenschaft"], str) and "." in row["Eigenschaft"]:
            row["Eigenschaft"] = row["Eigenschaft"].split(".")[-1]

        rows.append(row)

    df = pd.DataFrame(rows)

    def try_delta(row):
        try:
            a, b = float(row["Wert A"]), float(row["Wert B"])
            return "" if abs(b - a) < 1e-6 else b - a
        except:
            return ""

    df["Delta"] = df.apply(try_delta, axis=1)

    # Ensure all necessary columns are present
    for col in ["Kategorie", "Gruppe", "Art", "Status", "Eigenschaft", "Wert A", "Wert B", "Delta", "Change"]:
        if col not in df.columns:
            df[col] = ""

    # Drop duplicate columns if somehow appended twice
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    return df

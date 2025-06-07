# 📁 tools/diff.py — Comparison logic for grouped quantities

import streamlit as st
import pandas as pd
from translations import translations

def compare_grouped_quantities(grouped_a: pd.Series, grouped_b: pd.Series, lang=None) -> pd.DataFrame:
    """
    Compare two grouped quantity Series (multi-indexed by Kategorie, Gruppe, Art, Status)
    and return a DataFrame with deltas, direction, and change status.
    """
    lang = lang or st.session_state.get("lang", "en")
    t = translations[lang]

    all_keys = grouped_a.index.union(grouped_b.index)
    rows = []

    for key in all_keys:
        val_a = grouped_a[key] if key in grouped_a else ""
        val_b = grouped_b[key] if key in grouped_b else ""

        if isinstance(val_a, pd.Series):
            val_a = val_a.values[0]
        if isinstance(val_b, pd.Series):
            val_b = val_b.values[0]

        if str(val_a) == str(val_b):
            status = t["unchanged"]
        elif str(val_a) == "":
            status = t["added"]
        elif str(val_b) == "":
            status = t["removed"]
        else:
            status = t["changed"]

        kategorie, gruppe, art, status_val = (None, None, None, None)
        if isinstance(key, tuple):
            kategorie = key[0] if len(key) > 0 else None
            gruppe = key[1] if len(key) > 1 else None
            art = key[2] if len(key) > 2 else None
            status_val = key[3] if len(key) > 3 else None

        rows.append({
            "Kategorie": kategorie,
            "Gruppe": gruppe,
            "Art": art,
            "Status": status_val,
            "Wert A": val_a,
            "Wert B": val_b,
            "Delta": val_b - val_a if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)) else "",
            "Change": status
        })

    df = pd.DataFrame(rows)

    # Drop empty columns if needed
    for col in ["Gruppe", "Art", "Status"]:
        if col in df.columns and df[col].replace("", pd.NA).isna().all():
            df.drop(columns=col, inplace=True)

    return df

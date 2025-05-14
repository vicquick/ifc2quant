import streamlit as st
from pathlib import Path
import pandas as pd
import ifcopenshell
from cache.manager import CacheManager
from ifc_processing.transform import aggregate, to_dataframe
from ifc_processing.helpers import auto_scale, DISPLAY_NAMES
from comparison.core import compare_models, prepare_comparison_data
from comparison.excel import export_comparison_to_excel
from comparison.csv import export_comparison_to_csv
from utils.file_io import safe_write_bytes, ensure_directory

# Initialize cache and downloads directory
cache = CacheManager()
cache.setup()

# Session state initialization
for k in ("model_a", "model_b"):
    st.session_state.setdefault(k, {})

st.title("IFC-Mengenexport & Vergleich")

# ══════════ 1) Load Model A ════════════════════════════════════════════════
up_a = st.file_uploader("IFC A auswählen", type=["ifc"], key="up_a")

if st.button("1. AUSWERTEN – Modell A") and up_a:
    # Clear previous cache and downloads
    cache.clear()

    # Save uploaded IFC to cache
    tmp_a = cache.cache_dir / "temp_a.ifc"
    safe_write_bytes(tmp_a, up_a.getbuffer())

    with st.spinner("IFC A wird ausgewertet …"):
        ifc_a = ifcopenshell.open(str(tmp_a))
        scale_a = auto_scale(ifc_a)
        groups_a, bqa, psets_a = aggregate(ifc_a, scale_a)
        df_a = to_dataframe(groups_a, bqa + psets_a)

    st.session_state["model_a"] = dict(
        name=Path(up_a.name).stem,
        groups=groups_a,
        bq=bqa,
        psets=psets_a,
        df=df_a
    )
    st.success("Modell A geladen!")

# ───────── Export Configuration for Model A ────────────────────────────────
if (mA := st.session_state.get("model_a")):
    st.subheader(f"1. Export für „{mA['name']}“")
    cats = sorted(mA["df"].index.get_level_values(0).unique())
    sel_cat = st.multiselect("Kategorien", cats, default=cats)
    sel_bq = st.multiselect("Base-Quantities", mA["bq"], default=mA["bq"])
    sel_psets = st.multiselect("Pset Properties", mA["psets"], default=mA["psets"])

    preview_df = mA["df"].loc[pd.IndexSlice[sel_cat, :], :]
    st.dataframe(preview_df)

    if st.button("CSV A herunterladen"):
        out = cache.download_dir / f"{mA['name']}_Mengenzusammenfassung.csv"
        ensure_directory(out.parent)
        export_comparison_to_csv(preview_df, out)
        st.download_button("Download CSV A", out.read_bytes(), out.name, "text/csv")

# ══════════ 2) Optional Model B Comparison ═════════════════════════════════
up_b = st.file_uploader("Optional: IFC B zum Vergleich", type=["ifc"], key="up_b")

if st.button("2. VERGLEICH erstellen") and up_b and st.session_state.get("model_a"):
    mA = st.session_state["model_a"]
    tmp_b = cache.cache_dir / "temp_b.ifc"
    safe_write_bytes(tmp_b, up_b.getbuffer())

    with st.spinner("IFC B wird ausgewertet …"):
        ifc_b = ifcopenshell.open(str(tmp_b))
        scale_b = auto_scale(ifc_b)
        groups_b, bqb, psets_b = aggregate(ifc_b, scale_b)
        df_b = to_dataframe(groups_b, bqb + psets_b)

    st.session_state["model_b"] = dict(
        name=Path(up_b.name).stem,
        groups=groups_b,
        bq=bqb,
        psets=psets_b,
        df=df_b
    )
    st.success("Modell B geladen – Delta berechnet!")

# ───────── Enhanced Delta Display & Export ─────────────────────────────────
if (mB := st.session_state.get("model_b")):
    mA = st.session_state["model_a"]
    # Prepare dataframes for comparison
    df_a = mA["df"].reset_index()
    df_b = mB["df"].reset_index()
    for col in df_a.columns:
        if col not in [*df_a.columns[:2]]:
            df_a[col] = pd.to_numeric(df_a[col], errors='coerce').fillna(0)
    for col in df_b.columns:
        if col not in [*df_b.columns[:2]]:
            df_b[col] = pd.to_numeric(df_b[col], errors='coerce').fillna(0)

    merged = compare_models(df_a, df_b)
    all_cols = [c for c in df_a.columns if c not in [*df_a.columns[:2]]]
    compare_df = prepare_comparison_data(merged, all_cols)

    st.subheader("Vergleichsergebnis")
    st.dataframe(compare_df)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Δ-Excel herunterladen"):
            xlsx_path = cache.download_dir / f"Delta_{mA['name']}_vs_{mB['name']}.xlsx"
            ensure_directory(xlsx_path.parent)
            export_comparison_to_excel(compare_df, xlsx_path)
            st.download_button(
                "Download Δ-Excel", 
                xlsx_path.read_bytes(), 
                xlsx_path.name,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    with col2:
        if st.button("Vergleichs-CSV herunterladen"):
            comp_out = cache.download_dir / f"Vergleich_{mA['name']}_vs_{mB['name']}.csv"
            ensure_directory(comp_out.parent)
            export_comparison_to_csv(compare_df, comp_out)
            st.download_button(
                "Download Vergleichs-CSV",
                comp_out.read_bytes(),
                comp_out.name,
                "text/csv"
            )

# ───────── Reset Button ────────────────────────────────────────────────────
if st.button("↺ Reset"):
    cache.clear(full=True)
    st.session_state.clear()
    st.rerun()

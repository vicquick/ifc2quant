import streamlit as st
from pathlib import Path
import pandas as pd
import ifcopenshell

from cache.manager import CacheManager
from ifc_processing.transform import aggregate
from comparison.core import compare_models, prepare_comparison_data
from comparison.excel import export_comparison_to_excel
from comparison.csv import export_comparison_to_csv
from utils.file_io import safe_write_bytes, ensure_directory

# Cache & Session
cache = CacheManager()
cache.setup()
for k in ("model_a", "model_b"):
    st.session_state.setdefault(k, {})

st.title("IFC-Mengensummen & Δ-Vergleich (LL AM)")

# Toggle for unit conversion
st.session_state.setdefault("convert_mm", True)
convert_mm = st.checkbox("🔁 Längeneinheiten: mm → m umrechnen", value=st.session_state["convert_mm"])
st.session_state["convert_mm"] = convert_mm

# Model A
up_a = st.file_uploader("IFC A auswählen", type=["ifc"], key="up_a")
if st.button("1 · AUSWERTEN – Modell A") and up_a:
    cache.clear()
    tmp_a = cache.cache_dir / "model_a.ifc"
    safe_write_bytes(tmp_a, up_a.getbuffer())
    with st.spinner("IFC A wird ausgewertet …"):
        df_a = aggregate(ifcopenshell.open(str(tmp_a)), convert_mm_to_m=convert_mm)
    st.session_state["model_a"] = {"name": Path(up_a.name).stem, "df": df_a}
    st.success("Modell A geladen!")

# Export Model A
if (mA := st.session_state.get("model_a")):
    st.subheader(f"1. Export – „{mA['name']}“")
    cats = sorted(mA["df"]["Kategorie"].unique())
    sel_cat = st.multiselect("Kategorien filtern", cats, default=cats)

    all_cols = [c for c in mA["df"].columns if c not in ("Kategorie", "Gruppe")]
    sel_cols = st.multiselect("Spalten wählen", all_cols, default=all_cols)

    preview_df = (
        mA["df"]
        .query("Kategorie in @sel_cat")[["Kategorie", "Gruppe", *sel_cols]]
        .copy()
    )
    preview_df = preview_df.dropna(subset=sel_cols, how="all")

    text_cols = ["Status", "Art", "Gruppe", "Kategorie"]

    for col in sel_cols:
        if col == "Kostengruppe Beschreibung":
            preview_df[col] = preview_df[col].astype(str).replace("nan", "")
            continue

        try:
            preview_df[col] = pd.to_numeric(preview_df[col], errors="coerce")
        except:
            continue

        if col in ("Stückzahl", "Kostengruppe", "Anzahl Stufen", "Anzahl Pflanzen"):
            preview_df[col] = preview_df[col].apply(
                lambda x: f"{int(x)}" if pd.notna(x) and x == int(x) and x != 0 else (f"{x:.1f}".replace(".", ",") if pd.notna(x) and x != 0 else "")
            )
        elif col in text_cols:
            continue
        else:
            preview_df[col] = preview_df[col].apply(
                lambda x: f"{x:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) and x != 0 else ""
            )

    preview_df = preview_df.fillna("")
    preview_df = preview_df.loc[:, (preview_df != "").any()]

    if convert_mm:
        st.markdown("ℹ️ Alle Längenfelder wurden von **mm → m** umgerechnet.")
    else:
        st.markdown("ℹ️ Längen bleiben in **mm**.")

    st.dataframe(preview_df, use_container_width=True)

    if st.button("CSV A herunterladen"):
        out = cache.download_dir / f"{mA['name']}_Summen.csv"
        ensure_directory(out.parent)
        preview_df.to_csv(out, index=False, sep=";", decimal=",")
        st.download_button("Download CSV A", out.read_bytes(), out.name, "text/csv")

# Optional Model B
up_b = st.file_uploader("Optional: IFC B zum Vergleich", type=["ifc"], key="up_b")
if st.button("2 · Δ-Vergleich erstellen") and up_b and st.session_state.get("model_a"):
    tmp_b = cache.cache_dir / "model_b.ifc"
    safe_write_bytes(tmp_b, up_b.getbuffer())
    with st.spinner("IFC B wird ausgewertet …"):
        df_b = aggregate(ifcopenshell.open(str(tmp_b)), convert_mm_to_m=convert_mm)
    st.session_state["model_b"] = {"name": Path(up_b.name).stem, "df": df_b}
    st.success("Modell B geladen – Vergleich verfügbar!")

# Delta comparison
if (mB := st.session_state.get("model_b")):
    mA = st.session_state["model_a"]
    st.subheader(f"Δ-Vergleich: {mA['name']}  ↔  {mB['name']}")

    df_a = mA["df"].copy()
    df_b = mB["df"].copy()
    num_cols = [c for c in df_a.columns if c not in ("Kategorie", "Gruppe")]
    for col in num_cols:
        df_a[col] = pd.to_numeric(df_a[col], errors="coerce").fillna(0)
        df_b[col] = pd.to_numeric(df_b[col], errors="coerce").fillna(0)

    merged = compare_models(df_a, df_b)
    compare_df = prepare_comparison_data(merged, num_cols)

    st.dataframe(compare_df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Δ-Excel herunterladen"):
            xlsx = cache.download_dir / f"Delta_{mA['name']}_vs_{mB['name']}.xlsx"
            ensure_directory(xlsx.parent)
            export_comparison_to_excel(compare_df, xlsx)
            st.download_button(
                "Download Δ-Excel",
                xlsx.read_bytes(),
                xlsx.name,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    with col2:
        if st.button("Δ-CSV herunterladen"):
            csv = cache.download_dir / f"Delta_{mA['name']}_vs_{mB['name']}.csv"
            ensure_directory(csv.parent)
            export_comparison_to_csv(compare_df, csv)
            st.download_button(
                "Download Δ-CSV",
                csv.read_bytes(),
                csv.name,
                "text/csv",
            )

# Reset
if st.button("↺ Reset"):
    cache.clear(full=True)
    st.session_state.clear()
    st.rerun()
import streamlit as st
import json
import io
import pandas as pd
from pathlib import Path

def render_download_tab():
    if "final_mapping" not in st.session_state:
        st.warning("⚠️ Bitte erst Regeln definieren und Vorschau generieren.")
        return

    mapping = st.session_state["final_mapping"]

    # Download via browser
    json_bytes = io.BytesIO(json.dumps(mapping, indent=2, ensure_ascii=False).encode("utf-8"))
    st.download_button(
        label="📥 Mapping als JSON herunterladen",
        data=json_bytes,
        file_name="mapping_custom.json",
        mime="application/json"
    )

    # Save to project_root/mappings
    if st.button("💾 Mapping im Ordner speichern"):
        ifc_name = st.session_state.get("ifc_filename", "ifc2quant")

        # Resolve path to project root/mappings (1 level above /src/)
        project_root = Path(__file__).resolve().parent.parent
        mappings_path = project_root / "mappings"
        mappings_path.mkdir(parents=True, exist_ok=True)

        target_path = mappings_path / f"{ifc_name}_mapping.json"
        with target_path.open("w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)

        st.success(f"✅ Gespeichert als {target_path.name}")
        st.caption(f"📂 Gespeichert unter: `{target_path}`")

    # CSV + Excel Export
    if "df_final" in st.session_state:
        df = st.session_state["df_final"]
        ifc_name = st.session_state.get("ifc_filename", "ifc2quant")

        # CSV
        csv_bytes = io.BytesIO()
        df.to_csv(csv_bytes, sep=";", index=False)
        st.download_button(
            label="📄 CSV herunterladen",
            data=csv_bytes.getvalue(),
            file_name=f"{ifc_name}_Mengenauswertung.csv",
            mime="text/csv"
        )

        # Excel
        excel_bytes = io.BytesIO()
        with pd.ExcelWriter(excel_bytes, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Preview")
        st.download_button(
            label="📊 Excel herunterladen",
            data=excel_bytes.getvalue(),
            file_name=f"{ifc_name}_Mengenauswertung.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Reset
    if st.button("🔄 Alles zurücksetzen"):
        st.session_state.clear()

        project_root = Path(__file__).resolve().parent.parent
        project_cache = project_root / "cache"
        if project_cache.exists():
            for file in project_cache.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    st.warning(f"⚠️ Datei konnte nicht gelöscht werden: {file.name} – {e}")

        st.success("🧹 Zurückgesetzt. Bitte Seite neu laden.")

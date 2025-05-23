import streamlit as st
import json
import io
import pandas as pd
from pathlib import Path
from translations import translations

def render_download_tab():
    lang = st.session_state.get("lang", "en")
    t = translations[lang]

    if "final_mapping" not in st.session_state:
        st.warning("⚠️ " + t.get("download_warning", "Please define rules and generate a preview first."))
        return

    mapping = st.session_state["final_mapping"]

    # Download via browser
    json_bytes = io.BytesIO(json.dumps(mapping, indent=2, ensure_ascii=False).encode("utf-8"))
    st.download_button(
        label="📥 " + t.get("download_json", "Download mapping as JSON"),
        data=json_bytes,
        file_name="mapping_custom.json",
        mime="application/json"
    )

    if st.button("💾 " + t.get("save_mapping_button", "Save mapping to folder")):
        ifc_name = st.session_state.get("ifc_filename", "ifc2quant")
        project_root = Path(__file__).resolve().parent.parent
        mappings_path = project_root / "mappings"
        mappings_path.mkdir(parents=True, exist_ok=True)

        target_path = mappings_path / f"{ifc_name}_mapping.json"
        with target_path.open("w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)

        st.success(f"✅ {t.get('saved_as', 'Saved as')} {target_path.name}")
        st.caption(f"📂 {t.get('saved_under', 'Saved under')}: `{target_path}`")

    if "df_final" in st.session_state:
        df = st.session_state["df_final"]
        ifc_name = st.session_state.get("ifc_filename", "ifc2quant")

        suffix = "quantity_export" if lang == "en" else "Mengenauswertung"

        csv_bytes = io.BytesIO()
        df.to_csv(csv_bytes, sep=";", index=False)
        st.download_button(
            label="📄 " + t.get("download_csv", "Download CSV"),
            data=csv_bytes.getvalue(),
            file_name=f"{ifc_name}_{suffix}.csv",
            mime="text/csv"
        )

        excel_bytes = io.BytesIO()
        with pd.ExcelWriter(excel_bytes, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Preview")
        st.download_button(
            label="📊 " + t.get("download_excel", "Download Excel"),
            data=excel_bytes.getvalue(),
            file_name=f"{ifc_name}_{suffix}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if st.button("🔄 " + t.get("reset_all", "Reset all")):
        st.session_state.clear()

        project_root = Path(__file__).resolve().parent.parent
        project_cache = project_root / "cache"
        if project_cache.exists():
            for file in project_cache.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    st.warning(f"⚠️ {t.get('delete_failed', 'Could not delete file')}: {file.name} – {e}")

        st.success("🧹 " + t.get("reset_success", "Reset complete. Please reload the page."))

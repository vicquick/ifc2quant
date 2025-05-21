import streamlit as st

st.set_page_config(page_title="IFC Mengenauswertung")
st.title("📐 IFC Mengenauswertung")
st.caption("powered by Streamlit + IfcOpenShell")


tab_upload, tab_mapping, tab_preview, tab_download = st.tabs([
    "📂 Upload",
    "🛠️ Mapping",
    "📊 Vorschau",
    "📥 Download"
])

with tab_upload:
    from upload import render_upload_tab
    render_upload_tab()

with tab_mapping:
    from mapping import render_rename_tab
    render_rename_tab()

with tab_preview:
    from preview import render_preview_tab
    render_preview_tab()

with tab_download:
    from download import render_download_tab
    render_download_tab()

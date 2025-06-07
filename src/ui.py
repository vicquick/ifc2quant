import streamlit as st
from translations import translations

# Import tabs
from upload import render_upload_tab
from mapping import render_rename_tab
from preview import render_preview_tab
from download import render_download_tab
from comparison_tab import render_comparison_tab

# Load language
lang = st.session_state.get("lang", "en")
t = translations[lang]

st.set_page_config(page_title=t["app_title"])
st.title(f"📐 {t['app_title']}")
st.caption("powered by Streamlit + IfcOpenShell")

# Create tabs (now 5)
(
    tab_upload,
    tab_mapping,
    tab_preview,
    tab_download,
    tab_comparison,
) = st.tabs([
    f"📂 {t['upload_tab']}",
    f"🛠️ {t['mapping_tab']}",
    f"📊 {t['preview_tab']}",
    f"📥 {t['download_tab']}",
    f"🔁 {t.get('comparison_tab_title', 'Comparison')}",
])

with tab_upload:
    render_upload_tab()

with tab_mapping:
    render_rename_tab()

with tab_preview:
    render_preview_tab()

with tab_download:
    render_download_tab()

with tab_comparison:
    render_comparison_tab()
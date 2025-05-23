import streamlit as st
from translations import translations


# Load language from session or default to English
lang = st.session_state.get("lang", "en")
t = translations[lang]

st.set_page_config(page_title=t["app_title"])
st.title(f"📐 {t['app_title']}")
st.caption("powered by Streamlit + IfcOpenShell")

# Translate tab names dynamically
tab_upload, tab_mapping, tab_preview, tab_download = st.tabs([
    f"📂 {t['upload_tab']}",
    f"🛠️ {t['mapping_tab']}",
    f"📊 {t['preview_tab']}",
    f"📥 {t['download_tab']}"
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

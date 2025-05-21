import streamlit as st
import ifcopenshell
import json
from pathlib import Path
from ifc_processing.pset_reader import read_psets_from_model, flatten_psets

def render_upload_tab():
    uploaded_ifc = st.file_uploader("📂 IFC-Datei auswählen", type=["ifc"])

    if uploaded_ifc:
        project_root = Path(__file__).resolve().parent.parent
        cache_dir = project_root / "cache"
        cache_dir.mkdir(exist_ok=True)

        ifc_path = cache_dir / uploaded_ifc.name
        ifc_path.write_bytes(uploaded_ifc.getbuffer())
        st.write("📁 IFC gespeichert unter:", ifc_path)

        st.session_state["ifc_filename"] = ifc_path.stem

        ifc_model = ifcopenshell.open(str(ifc_path))
        st.session_state["ifc_model"] = ifc_model

        with st.spinner("🔍 PropertySets auslesen …"):
            psets = read_psets_from_model(ifc_model)
            flat_data = flatten_psets(psets)

        st.session_state["flat_data"] = flat_data

        # Classification info
        all_classes = sorted({el.is_a() for el in ifc_model.by_type("IfcElement")})
        class_keys_map = {
            cls: sorted({k for gid, props in flat_data.items()
                         if ifc_model.by_id(gid).is_a() == cls
                         for k in props if not k.lower().startswith("type")})
            for cls in all_classes
        }
        st.session_state["all_classes"] = all_classes
        st.session_state["class_keys_map"] = class_keys_map

        st.success("✅ IFC geladen und PropertySets gelesen.")

    uploaded_json = st.file_uploader("🗂️ Vorhandene Mapping-Datei (JSON) laden", type=["json"], key="map_json")
    if uploaded_json:
        try:
            project_root = Path(__file__).resolve().parent.parent
            cache_dir = project_root / "cache"
            cache_dir.mkdir(exist_ok=True)

            json_path = cache_dir / "loaded_mapping.json"
            mapping_text = uploaded_json.getvalue().decode("utf-8")
            loaded_mapping = json.loads(mapping_text)


            json_path.write_text(mapping_text, encoding="utf-8")
            st.session_state["loaded_mapping"] = loaded_mapping
            st.session_state["category_mapping"] = loaded_mapping.get("categories", {})
            st.session_state["class_rules"] = loaded_mapping.get("rules", {})
            st.session_state["rules"] = loaded_mapping.get("rules", {})  # legacy fallback
            st.session_state["active_classes"] = list(loaded_mapping.get("rules", {}).keys())

            st.success("✅ Mapping erfolgreich geladen.")
        except Exception as e:
            st.error(f"❌ Fehler beim Laden der Mapping-Datei: {e}")

    # 📂 Load mapping from local mappings folder
    project_root = Path(__file__).resolve().parent.parent
    mappings_path = project_root / "mappings"
    mappings_path.mkdir(exist_ok=True)

    mapping_files = sorted(mappings_path.glob("*.json"))
    if mapping_files:
        selected = st.selectbox("📂 Mapping aus Ordner wählen", [f.name for f in mapping_files], key="mapping_selector")
        if st.button("📥 Ausgewähltes Mapping laden"):
            path = mappings_path / selected
            try:
                loaded_mapping = json.loads(path.read_text(encoding="utf-8"))
                st.session_state["loaded_mapping"] = loaded_mapping
                st.session_state["category_mapping"] = loaded_mapping.get("categories", {})
                st.session_state["class_rules"] = loaded_mapping.get("rules", {})
                st.session_state["rules"] = loaded_mapping.get("rules", {})  # legacy fallback
                st.session_state["active_classes"] = list(loaded_mapping.get("rules", {}).keys())

                st.success(f"✅ Mapping geladen: {selected}")
            except Exception as e:
                st.error(f"❌ Fehler beim Laden: {e}")
    else:
        st.info("ℹ️ Noch keine gespeicherten Mappings im Ordner 'mappings/' gefunden.")
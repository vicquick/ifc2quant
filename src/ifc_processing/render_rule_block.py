from typing import Dict, List, Any
import streamlit as st

def filter_existing(keys: List[str], default: List[str]) -> List[str]:
    return [v for v in default if v in keys]

def render_rule_block(cls: str, all_keys: List[str], existing: Dict[str, Any], label2="Art", label3="Status") -> Dict[str, List[str]]:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        group = st.multiselect("🔗 Gruppe", all_keys, default=filter_existing(all_keys, existing.get("group", [])), key=f"{cls}_group")
    with col2:
        art = st.multiselect(f"🎨 {label2}", all_keys, default=filter_existing(all_keys, existing.get("group2", [])), key=f"{cls}_group2")
    with col3:
        status = st.multiselect(f"📌 {label3}", all_keys, default=filter_existing(all_keys, existing.get("group3", [])), key=f"{cls}_group3")
    with col4:
        summe = st.multiselect("➕ Summe", all_keys, default=filter_existing(all_keys, existing.get("sum", [])), key=f"{cls}_sum")

    col5, col6 = st.columns(2)
    with col5:
        text = st.multiselect("📝 Text", all_keys, default=filter_existing(all_keys, existing.get("text", [])), key=f"{cls}_text")
    with col6:
        ignore = st.multiselect("🚫 Ignorieren", all_keys, default=filter_existing(all_keys, existing.get("ignore", [])), key=f"{cls}_ignore")

    return {
        "group": group,
        "group2": art,
        "group3": status,
        "sum": summe,
        "text": text,
        "ignore": ignore
    }

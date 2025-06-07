# 📁 tools/excel_export.py

import pandas as pd
from io import BytesIO
from translations import translations

def format_diff_table_with_styles(df: pd.DataFrame, lang="de") -> bytes:
    """
    Export DataFrame to styled Excel where changes are color-coded.
    Fallbacks gracefully if empty.
    """
    t = translations[lang]
    output = BytesIO()

    # ✅ Fallback if completely empty (or filtered to all unchanged)
    if df.empty or df.dropna(how='all').empty or df.shape[1] == 0:
        dummy_df = pd.DataFrame([[t.get("no_differences", "No differences detected.")]], columns=["Info"])
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dummy_df.to_excel(writer, sheet_name=t.get("comparison_tab_title", "Comparison"), index=False)
        return output.getvalue()

    # ✅ Define highlight logic based on change type
    def highlight(change_type):
        if change_type == 'added':
            return 'background-color: #fffacd'  # light yellow
        elif change_type == 'removed':
            return 'background-color: #d3d3d3'  # light grey
        elif change_type == 'changed':
            return 'background-color: #ffcccc'  # light red
        return ''

    # ✅ Apply row-wise styling
    def style_row(row):
        return [
            '',  # Kategorie
            '',  # Gruppe
            '',  # Art
            '',  # Status
            '',  # Eigenschaft
            highlight(row.get("Change", "")),  # Wert A
            highlight(row.get("Change", "")),  # Wert B
            highlight(row.get("Change", "")),  # Delta
            ''   # Change
        ]

    styled_df = df.style.apply(style_row, axis=1)

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        styled_df.to_excel(writer, sheet_name=t.get("comparison_tab_title", "Comparison"), index=False)

    return output.getvalue()

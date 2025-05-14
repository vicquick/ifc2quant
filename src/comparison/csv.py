# src/comparison/csv.py
from pathlib import Path
import pandas as pd

def export_comparison_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Foolproof CSV export that preserves everything"""
    # Make absolutely sure categories/groups are included
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()
    
    # Force German formatting
    df.to_csv(
        output_path,
        sep=";",
        index=False,
        encoding='utf-8-sig',  # UTF-8 with BOM for Excel
        decimal=","
    )
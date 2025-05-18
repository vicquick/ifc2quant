# src/comparison/core.py
import pandas as pd
from typing import List

def compare_models(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.DataFrame:
    """Safe comparison that preserves categories/groups"""
    # Reset indexes to make categories/groups regular columns
    df_A = df_a.reset_index()
    df_B = df_b.reset_index()
    
    # Identify all properties (excluding index columns)
    common_cols = list(set(df_A.columns) & set(df_B.columns))
    prop_cols = [col for col in common_cols if col not in ["Kategorie", "Gruppe"]]
    
    # Merge with protection for categories/groups
    merged = df_A.merge(
        df_B,
        on=["Kategorie", "Gruppe"],
        suffixes=('_A', '_B'),
        how='outer'
    ).fillna(0)
    
    # Calculate deltas safely
    for col in prop_cols:
        # Force numeric conversion
        merged[f'{col}_A'] = pd.to_numeric(merged[f'{col}_A'], errors='coerce').fillna(0)
        merged[f'{col}_B'] = pd.to_numeric(merged[f'{col}_B'], errors='coerce').fillna(0)
        merged[f'delta_{col}'] = merged[f'{col}_B'] - merged[f'{col}_A']
    
    return merged

def prepare_comparison_data(merged: pd.DataFrame, all_cols: List[str]) -> pd.DataFrame:
    """Prepare display with locked categories/groups"""
    compare_df = pd.DataFrame()
    # Preserve categories/groups as regular columns
    compare_df["Kategorie"] = merged["Kategorie"]
    compare_df["Gruppe"] = merged["Gruppe"]
    
    # Add compared properties
    for col in all_cols:
        compare_df[f"A {col}"] = merged[f"{col}_A"]
        compare_df[f"B {col}"] = merged[f"{col}_B"]
        compare_df[f"Δ {col}"] = merged[f"delta_{col}"]
    
    # Only show rows with changes
    delta_cols = [f"Δ {col}" for col in all_cols]
    return compare_df[compare_df[delta_cols].abs().sum(axis=1) > 0]
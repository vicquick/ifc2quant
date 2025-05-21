import pandas as pd
from typing import Dict, Any
from collections import OrderedDict

def ordered_text_join_debug(x, label=None):
    values = [str(v).strip() for v in x if str(v).strip()]
    joined = " | ".join(OrderedDict.fromkeys(values))
    #print(f"[DEBUG] Group: {label or ''} -> Ordered Join: {joined} from values: {values}")
    return joined

def aggregate_by_mapping_per_class(df: pd.DataFrame, mapping: Dict[str, Any]) -> pd.DataFrame:
    grouped_dfs = []

    for ifc_class in df["Kategorie"].unique():
        print(f"\n[DEBUG] Processing class: {ifc_class}")
        class_df = df[df["Kategorie"] == ifc_class].copy()
        rules = mapping.get("rules", {}).get(ifc_class, {})
        group_cols = ["Kategorie", "Gruppe", "Art", "Status"]

        explicit_text_fields = set(rules.get("text", []))
        explicit_sum_fields = set(rules.get("sum", []))

        text_fields = set(explicit_text_fields)
        sum_fields = set(explicit_sum_fields)

        all_fields = set(class_df["Eigenschaft"].unique())
        known_fields = text_fields.union(sum_fields)
        undefined_fields = sorted(all_fields - known_fields)

        #print(f"[DEBUG] User-defined text fields: {explicit_text_fields}")
        #print(f"[DEBUG] User-defined sum fields: {explicit_sum_fields}")
        #print(f"[DEBUG] Undefined Fields: {undefined_fields}")

        for field in undefined_fields:
            try:
                pd.to_numeric(class_df[class_df["Eigenschaft"] == field]["Wert"], errors="raise")
                sum_fields.add(field)
            except Exception:
                text_fields.add(field)

        #print(f"[DEBUG] Final Sum Fields: {sum_fields}")
        #print(f"[DEBUG] Final Text Fields: {text_fields}")

        result_df = class_df[group_cols].drop_duplicates().reset_index(drop=True)

        for field in sum_fields:
            numeric_agg = (
                class_df[class_df["Eigenschaft"] == field]
                .groupby(group_cols)["Wert"]
                .apply(lambda x: pd.to_numeric(x, errors="coerce").sum())
                .reset_index()
                .rename(columns={"Wert": field})
            )
            result_df = result_df.merge(numeric_agg.fillna(0), on=group_cols, how="left")

        for field in text_fields:
            field_df = class_df[class_df["Eigenschaft"] == field]
            text_agg = (
                field_df.groupby(group_cols)["Wert"]
                .agg(lambda x: ordered_text_join_debug(x, label=field_df[group_cols].iloc[0].to_dict()))
                .reset_index()
                .rename(columns={"Wert": field})
            )
            result_df = result_df.merge(text_agg, on=group_cols, how="left")

        grouped_dfs.append(result_df)

    if not grouped_dfs:
        return pd.DataFrame()

    df_final = pd.concat(grouped_dfs, ignore_index=True)

    # Rename columns like 'LL AM.Höhe' → 'Höhe'
    rename_map = {
        col: col.split(".")[-1] for col in df_final.columns
        if "." in col and col not in ["Kategorie", "Gruppe", "Art", "Status"]
    }
    df_final = df_final.rename(columns=rename_map)

    for col in df_final.columns:
        if col in ["Kategorie", "Gruppe", "Art", "Status"]:
            continue
        if col in text_fields:
            df_final[col] = df_final[col].fillna("").astype(str)
        else:
            df_final[col] = df_final[col].fillna(0)
    group_keys = set()
    for rule in mapping["rules"].values():
        group_keys.update(rule.get("group", []))
        group_keys.update(rule.get("group2", []))
        group_keys.update(rule.get("group3", []))

    df_final.drop(columns=[col.split(".")[-1] for col in group_keys if col.split(".")[-1] in df_final.columns], inplace=True)

    return df_final


def simplify_text_fields(df: pd.DataFrame, mapping: Dict[str, Any]) -> pd.DataFrame:
    text_fields = {field for rule in mapping.get("rules", {}).values() for field in rule.get("text", [])}
    for field in text_fields:
        if field in df.columns:
            df[field] = df[field].apply(simplify_text_value)
    return df



def simplify_text_value(x):
    try:
        # Handle actual float values: 80.0 → "80", 25.4 → "25.4"
        if isinstance(x, float) and x.is_integer():
            return str(int(x))
        return str(x).strip()
    except Exception:
        return str(x)



def format_german_display(df: pd.DataFrame, never_convert_fields: set) -> pd.DataFrame:
    display_df = df.copy()
    for col in display_df.columns:
        if col in never_convert_fields:
            continue
        if pd.api.types.is_numeric_dtype(display_df[col]):
            if col == "Stückzahl":
                display_df[col] = display_df[col].astype("Int64")
            else:
                display_df[col] = display_df[col].round(2)
                display_df[col] = display_df[col].apply(
                    lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                )
    return display_df


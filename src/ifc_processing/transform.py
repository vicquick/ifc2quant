
from typing import List, Dict, Any
import pandas as pd
from ifcopenshell.util.element import get_psets

from .helpers import (
    auto_scale,
    categorise,
    ll_am_fields,
    get_llam_pset,
    DISPLAY_NAMES,
    convert_units_mm_to_m,
    add_mm_suffix,
)

NO_SUM_FIELDS = {
    "Kostengruppe",
    "Kostengruppe Beschreibung",
    "Steigung Rampe",
    "Steigung Stufen",
    "Breite",
    "Auftritt Stufen",
}

LENGTH_SUM_CATEGORIES = {"Wand", "Hecke", "Ausstattung", "Sonstige"}

def aggregate_rows(ifc) -> List[Dict[str, Any]]:
    scale = auto_scale(ifc)
    valid = {f["key"] for f in ll_am_fields()}
    rows: List[Dict[str, Any]] = []

    for el in ifc.by_type("IfcElement"):
        cat, grp, thick_m, thick_raw, status, art, kron = categorise(el, scale)

        if cat == "Flächenpflanzung":
            grp = cat

        pset = get_llam_pset(el)
        if not pset:
            continue

        for k, v in pset.items():
            if k in valid:
                try:
                    s = str(v).replace(",", ".").strip()
                    fval = float(s)
                    if k in ("Anzahl Pflanzen", "Anzahl Stufen") and fval == 0:
                        continue
                except:
                    pass
                rows.append(_make_row(cat, grp, thick_m, status, art, kron, k, v))

        rows.append(_make_row(cat, grp, thick_m, status, art, kron, "Stückzahl", 1.0))

        if cat == "Ramp" and "Steigung Rampe" in pset:
            rows.append(_make_row(cat, grp, thick_m, status, art, kron, "Steigung Rampe", pset["Steigung Rampe"]))

    return rows

def _make_row(cat, grp, thick_m, status, art, kron, prop, val) -> Dict[str, Any]:
    try:
        s = str(val).replace(",", ".").strip()
        if s.lstrip("-").replace(".", "", 1).isdigit():
            val = float(s)
    except:
        pass

    return {
        "Kategorie": DISPLAY_NAMES.get(cat, cat),
        "Gruppe": grp,
        "Status": status,
        "Art": art,
        "Kronendurchmesser": kron,
        "Dicke_m": thick_m,
        "Eigenschaft": prop,
        "Wert": val,
    }

def to_long_dataframe(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    # Remove any duplicate Länge columns by keeping only one
    df = df[~((df["Eigenschaft"].isin(["Länge_x", "Länge_y"])))]
    df.loc[df["Eigenschaft"].str.startswith("Länge"), "Eigenschaft"] = "Länge"

    # Remove 0 rows for specific fields
    df = df[~((df["Eigenschaft"].isin(["Anzahl Stufen", "Anzahl Pflanzen"])) & (df["Wert"] == 0))]

    cols = [
        "Kategorie",
        "Gruppe",
        "Status",
        "Art",
        "Kronendurchmesser",
        "Dicke_m",
        "Eigenschaft",
        "Wert",
    ]
    return df[cols].sort_values(cols[:-2]).reset_index(drop=True)

def summarise_special_max(field: str, df: pd.DataFrame) -> pd.DataFrame:
    subset = df[df["Eigenschaft"] == field].copy()
    if subset.empty:
        return None

    subset["Wert"] = pd.to_numeric(subset["Wert"], errors="coerce")
    subset = subset.dropna(subset=["Wert"])

    out = (
        subset.groupby([
            "Kategorie",
            "Gruppe",
            "Status",
            "Art",
            "Dicke_m",
        ])["Wert"]
        .max()
        .round(2)
        .reset_index()
        .rename(columns={"Wert": field})
    )
    return out

def summarise(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df["is_no_sum"] = df.apply(
        lambda row: row["Eigenschaft"] in NO_SUM_FIELDS
        or (row["Eigenschaft"] == "Länge" and row["Kategorie"] not in LENGTH_SUM_CATEGORIES),
        axis=1,
    )
    
    # Process all numeric fields
    num = df[~df["is_no_sum"] & ~df["Eigenschaft"].isin({"Höhe", "Kronendurchmesser"})].copy()
    num["Wert"] = pd.to_numeric(num["Wert"], errors="coerce")
    num = num.dropna(subset=["Wert"])

    # Create pivot table
    wide = (
        num.pivot_table(
            index=["Kategorie", "Gruppe", "Status", "Art", "Dicke_m"],
            columns="Eigenschaft",
            values="Wert",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )

    # Handle special max fields
    for field in ("Kronendurchmesser", "Höhe"):
        summary = summarise_special_max(field, df)
        if summary is not None:
            wide = wide.merge(summary, on=["Kategorie", "Gruppe", "Status", "Art", "Dicke_m"], how="left")

    # Process text fields
    txt = df[df["is_no_sum"]]
    if not txt.empty:
        txt_p = (
            txt.pivot_table(
                index=["Kategorie", "Gruppe", "Status", "Art", "Dicke_m"],
                columns="Eigenschaft",
                values="Wert",
                aggfunc=lambda s: " | ".join(sorted({str(v) for v in s if v})),
                fill_value="",
            )
            .reset_index()
            .rename_axis(None, axis=1)
        )
        wide = wide.merge(txt_p, on=["Kategorie", "Gruppe", "Status", "Art", "Dicke_m"], how="left")

    # Combine Länge_x and Länge_y into single Länge column
    if "Länge_x" in wide.columns or "Länge_y" in wide.columns:
        # Convert both columns to numeric, treating errors as NaN
        if "Länge_x" in wide.columns:
            wide["Länge_x"] = pd.to_numeric(wide["Länge_x"], errors="coerce")
        else:
            wide["Länge_x"] = 0.0
            
        if "Länge_y" in wide.columns:
            wide["Länge_y"] = pd.to_numeric(wide["Länge_y"], errors="coerce")
        else:
            wide["Länge_y"] = 0.0
            
        # Sum the numeric values
        wide["Länge"] = wide["Länge_x"].fillna(0) + wide["Länge_y"].fillna(0)
        
        # Drop the original columns
        columns_to_drop = []
        if "Länge_x" in wide.columns:
            columns_to_drop.append("Länge_x")
        if "Länge_y" in wide.columns:
            columns_to_drop.append("Länge_y")
        wide.drop(columns_to_drop, axis=1, inplace=True)

    return wide

def aggregate(ifc, convert_mm_to_m: bool = True) -> pd.DataFrame:
    rows = aggregate_rows(ifc)
    df_long = to_long_dataframe(rows)
    df_wide = summarise(df_long)

    if convert_mm_to_m:
        df_wide = convert_units_mm_to_m(df_wide)
    else:
        df_wide = add_mm_suffix(df_wide)

    return df_wide

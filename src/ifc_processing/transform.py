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
}

def aggregate_rows(ifc) -> List[Dict[str, Any]]:
    scale = auto_scale(ifc)
    valid = {f["key"] for f in ll_am_fields()}
    rows: List[Dict[str, Any]] = []

    for el in ifc.by_type("IfcElement"):
        cat, grp, thick_m, thick_raw, status, art, kron = categorise(el, scale)

        if cat in ("Ramp", "Stair"):
            grp = cat
        if cat == "Flächenpflanzung":
            grp = cat

        pset = get_llam_pset(el)
        if not pset:
            continue

        rows.append(_make_row(cat, grp, thick_m, status, art, kron, "Stückzahl", 1.0))

        for k, v in pset.items():
            if k in valid:
                rows.append(_make_row(cat, grp, thick_m, status, art, kron, k, v))

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

    display_grp = grp
    if cat in ("Ramp", "Stair"):
        display_grp = DISPLAY_NAMES.get(cat, grp)

    return {
        "Kategorie": DISPLAY_NAMES.get(cat, cat),
        "Gruppe": display_grp,
        "Status": status,
        "Art": art,
        "Kronendurchmesser": kron,
        "Dicke_m": thick_m,
        "Eigenschaft": prop,
        "Wert": val,
    }

def to_long_dataframe(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
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

    num = df[~df["Eigenschaft"].isin(NO_SUM_FIELDS | {"Höhe", "Kronendurchmesser"})].copy()
    num["Wert"] = pd.to_numeric(num["Wert"], errors="coerce")
    num = num.dropna(subset=["Wert"])

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

    for field in ("Kronendurchmesser", "Höhe"):
        summary = summarise_special_max(field, df)
        if summary is not None:
            wide = wide.merge(summary, on=["Kategorie", "Gruppe", "Status", "Art", "Dicke_m"], how="left")

    txt = df[df["Eigenschaft"].isin(NO_SUM_FIELDS)]
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
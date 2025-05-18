import argparse
from pathlib import Path
import ifcopenshell
from ifc_processing.helpers import auto_scale
from ifc_processing.transform import aggregate
from comparison.csv import export_comparison_to_csv

def main():
    p = argparse.ArgumentParser(description="IFC→CSV v3.7")
    p.add_argument("ifc_file")
    p.add_argument("-o", "--output", default="", help="Output CSV")
    args = p.parse_args()

    src = Path(args.ifc_file).expanduser().resolve()
    out = Path(args.output).expanduser().resolve() if args.output else src.with_name(src.stem + "_summary.csv")

    ifc = ifcopenshell.open(str(src))
    scale = auto_scale(ifc)
    groups, bq_keys, _ = aggregate(ifc, scale)
    df = to_dataframe(groups, bq_keys)
    export_comparison_to_csv(df, out)

if __name__ == "__main__":
    main()
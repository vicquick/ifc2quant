
<p align="center">
  <img src="assets/filipp-romanovski-pOlwrv3yxWI-unsplash.jpg" alt="ifc2quant Banner" width="450"/>
</p>

# ifc2quant

## Description

**ifc2quant** is an open-source tool for professionals working with BIM models in IFC format, providing an interactive platform to analyze, group, rename, and compare quantities across model versions. Built for high precision and transparency, it simplifies the process of quantity extraction through a streamlined Streamlit interface.

Ideal for landscape architects, infrastructure planners, and BIM coordinators, the app allows you to define your own logic for aggregating volume, area, or count or listing any other string key from nested property sets. You can fully customize grouping, map IFC classes to categories, and produce CSV/Excel outputs suitable for AVA, cost estimation, or quality control workflows.

## Features

* IFC model processing using IfcOpenShell and custom rules.
* Dynamic property grouping and field mapping with JSON configs.
* Interactive tabbed interface to define mapping, preview quantities, and compare models.
* Output of grouped data or model deltas (changes) in CSV and Excel format.
* Caching and unit conversion support.
* Model comparison tab for highlighting changes between two IFCs using consistent mapping logic.
* Clean, extensible modular codebase with separation between logic and UI.

## Project Structure

```markdown
ifc2quant/
├── .gitignore                     # Files and folders to exclude from version control
├── LICENSE.md                     # License file (Open-GPL)
├── README.md                      # Project overview and usage guide
├── requirements.txt               # Python package dependencies
├── mappings/                      # Saved user mapping configurations (.json)
└── src/                           # Main application source
    ├── ui.py                      # Streamlit entrypoint with all tab navigation
    ├── upload.py                  # IFC upload + preprocessing
    ├── mapping.py                 # Class mapping and grouping logic setup
    ├── preview.py                 # Real-time preview of quantity outputs
    ├── download.py                # CSV/XLSX export functionality
    ├── rules.py                   # Rule block generation for each class
    ├── translations.py            # Multilingual label support
    ├── comparison_tab.py          # UI logic for model vs model comparison
    ├── cache/
    │   ├── manager.py             # Handles in-session cache and uploaded file management
    │   └── __init__.py
    ├── ifc_processing/            # Core IFC model transformation logic
    │   ├── aggregate_rows_custom.py  # Aggregation engine for quantities
    │   ├── apply_mapping.py          # Applies saved user mappings
    │   ├── categorise_with_mapping.py# Category tagging for IFC classes
    │   ├── pset_reader.py            # Pset parser (Property Sets)
    │   ├── render_rule_block.py      # UI logic to render rule components
    │   ├── transform.py              # Final transformation pipeline
    │   └── __init__.py
    └── tools/                    # Comparison engine utilities
        ├── comparison_logic.py    # Combines aggregation + text change analysis
        ├── diff.py                # Prepares simplified difference tables
        ├── excel_export.py        # Exports differences as formatted Excel
        ├── ifchelper.py           # Smart hashing, name lookups, and Pset helpers
        ├── indexer.py             # Builds hash-based indices for model comparison
        ├── text_diff.py           # Compares text fields across grouped rows
        └── __init__.py
```

## Installation

Clone the repository from your Gitea server:

```bash
git clone https://git.budinic.art/victor/ifc2quant.git
cd ifc2quant
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:

```bash
streamlit run ui.py
```

Use the tabs to:

📂 **Upload** your IFC file  
🧩 **Define mapping rules** for grouping, renaming, and aggregation  
🔍 **Preview grouped quantities** in real time per category  
📤 **Export results** to `.csv` or `.xlsx`  
🧮 **Sum or list keys** from all relevant property sets  
♻️ **Reset** the session to load another IFC  
🪞 **Compare models** side by side using the same mapping logic to highlight added, removed, or modified entries  

## Comparison Tab

The **comparison tab** lets you upload and compare two versions of the same IFC model using the exact same grouping logic. It highlights:

- **Added elements** in the new model
- **Removed elements** no longer present
- **Modified values** based on a stable hash of IFC attributes

Results can be exported for auditing or version tracking.

## Dependencies

* `streamlit`
* `ifcopenshell`
* `pandas`
* `xlsxwriter`
* `python-dotenv`

## License

Open-GPL License. See LICENSE.md for full terms.
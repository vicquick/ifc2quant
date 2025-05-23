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
* Clean, extensible modular codebase with separation between logic and UI.

## Project Structure

```markdown
ifc2quant/
├── ui.py                         # Streamlit UI entrypoint with multi-tab navigation
├── mapping.py                    # Rule and category mapping editor tab
├── preview.py                    # Aggregation preview and grouped table output
├── upload.py                     # IFC file uploader and unit conversion
├── rules.py                      # Dynamic rule block rendering for sum/text fields
├── download.py                   # Export logic for CSV/XLSX and mapping files
├── ifc_processing/               # Core logic for handling IFC data
│   ├── pset_reader.py            # Reads and flattens property sets
│   ├── categorise_with_mapping.py# Applies class-to-category mappings
│   ├── aggregate_rows_custom.py  # Groups and sums values per rule set
│   ├── apply_mapping.py          # Applies mappings to raw IFC data
│   ├── render_rule_block.py      # Builds rule input blocks per class
│   ├── transform.py              # Aggregation pipeline and data reshaping
│   └── __init__.py
├── cache/
│   ├── manager.py                # Temporary file cache and model state
│   └── __init__.py
├── assets/                       # UI banner and optional images
│   └── *.png / *.jpg             # Optional decorative assets
├── requirements.txt              # Python dependencies
└── README.md                     # Project documentation
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

📂 Upload your IFC file

🧩 Define per-class aggregation and renaming rules

🔍 Preview grouped quantities in real time

🧮 Sum or list all unique keys available in your model

💾 Save your current mapping configuration as .json

📤 Export quantity results to .csv or .xlsx

♻️ Reset session state to load new models or restart mapping

## Dependencies

* `streamlit`
* `ifcopenshell`
* `pandas`
* `xlsxwriter`
* `python-dotenv`

## License

Open-GPL License. See LICENSE.md for full terms.
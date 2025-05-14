# IFC Comparison Tool

## Description

This tool provides functionality for processing and comparing IFC (Industry Foundation Classes) files. It allows for efficient extraction, transformation, caching, and comparison of IFC data, with results exportable to CSV and Excel formats.

## Features

* IFC file processing and caching for optimized performance.
* Command Line Interface (CLI) and Streamlit Web Application (`app.py`) for ease of use.
* Detailed comparison of IFC files, including handling of changes in geometry, properties, and metadata.
* Export comparison results to CSV and Excel formats.

## Project Structure

```
ifc_comparison_tool/
├── requirements.txt
├── .gitignore
└── src/
    ├── app.py                  # Streamlit UI
    ├── cli.py                  # Command Line Interface
    ├── cache/
    │   ├── manager.py          # Cache handling
    │   └── __init__.py
    ├── comparison/
    │   ├── core.py             # Core comparison logic
    │   ├── csv.py              # CSV output logic
    │   ├── excel.py            # Excel output logic
    │   └── __init__.py
    ├── ifc_processing/
    │   ├── helpers.py          # IFC processing helpers
    │   ├── transform.py        # IFC transformations
    │   └── __init__.py
    └── utils/
        ├── file_io.py          # File I/O utilities
        └── __init__.py
```

## Installation

Clone the repository from your Gitea server:

```sh
git clone https://git.budinic.art/victor/ifc2csv.git
```

Navigate to the project directory and install dependencies:

```sh
cd ifc_comparison_tool
pip install -r requirements.txt
```

## Usage

### Web Interface

Run the Streamlit application:

```sh
streamlit run src/app.py
```

### Command Line

Execute the CLI script with your IFC files:

```sh
python src/cli.py --input path/to/your/file.ifc --output path/to/output
```

## Dependencies

* `streamlit`
* `ifcopenshell`
* `pandas`
* `xlsxwriter`
* `python-dotenv`

For a complete list, see `requirements.txt`.

## Contributing

Contributions are welcome! Please submit pull requests and issues through our Gitea server.

## License

Open-GPL License. Please read LICENSE.md

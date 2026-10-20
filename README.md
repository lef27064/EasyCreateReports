# EasyCreateReports 📄🚀

**EasyCreateReports** is a powerful, metadata-driven reporting engine designed to automate the generation of professional administrative and technical documents (such as *Διαβιβαστικό*, *Αίτημα*, and *Μελέτη*). It bridges the gap between raw structured data and polished PDF reports through a clean Domain-Specific Language (DSL), on-the-fly mathematical processing, and strict type handling.

---

## Key Features

- **Metadata-Driven Architecture**: Write documents using an intuitive DSL combining YAML-based `@data` blocks, `@calc` expressions, reusable `@common` components, and `@output` templates.
- **Dynamic Table Engine (`@detail table`)**:
  - Automatic column calculations and aliases (e.g., `Ποσότητα * Κόστος * 0.24 AS ΦΠΑ`).
  - Row filtering using `where` clauses.
  - Explicit column typing (`types: [int, str, float, float]`) to prevent unwanted number formatting (e.g., keeping IDs as clean integers like `1` instead of `1,00`).
  - Automatic calculation of column totals and unit labeling (e.g., `Euro`).
- **Robust Math & Localization**: Built-in support for locale-aware number and currency formatting (`fmt`) and safe mathematical expression evaluation.
- **Seamless HTML-to-PDF Pipeline**: Converts structured Markdown and custom HTML templates into print-ready, professional PDF documents.

---

## 📂 Project Structure

```text
EasyCreateReports/
├── EasyCreatateReports.py  # Main engine orchestrator and parser
├── engine_data.py          # XML and external data source loader
├── engine_math.py          # Safe math evaluation and sum expressions
├── engine_pdf.py           # HTML-to-PDF conversion utilities
├── engine_converter.py     # DSL <-> XML converter tools
├── md_dictionary.py        # Markdown formatting rules
├── styles.css              # Document layout and styling
└── document.txt            # Main project definition file (DSL)
```

## How it works
Below is an example of how data and dynamic tables are defined inside document.txt:

@data
protokollo: 452
date: 15/06/2024
titlos: "Καθαρισμός δασικών δρόμων"
enotita: Λάβδανης

tbl_aitima:
  headers: ["ΑΑ", "Περιγραφή", "Ποσότητα", "Κόστος"]
  types: [int, str, float, float]
  rows:
    - [1, "Καθαρισμός Δασικών Δρόμων Δ.Δ. Λάβδανης", 1, 11286.01]
@end

@output "report_aitima.html"
$header_block$

**Θέμα:** Υποβολή αιτήματος για παροχή υπηρεσιών $titlos$ $enotita$.

@detail table{name="tbl_aitima", title="", select="ΑΑ, Περιγραφή, Ποσότητα, Κόστος, Ποσότητα * Κόστος * 0.24 AS ΦΠΑ, Ποσότητα * Κόστος * 1.24 AS Συνολικό", totals="Συνολικό: Euro"}

@end

## Getting Started
Prerequisites
    Python 3.x
    Required libraries (PyYAML, etc.)

Running the Engine

Execute the main script to compile your document.txt into HTML reports and automatically render the corresponding PDFs:
python EasyCreatateReports.py

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
## License

This project is open-source and available under the MIT License.



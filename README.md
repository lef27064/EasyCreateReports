# EasyCreateReports 📄🚀

**EasyCreateReports** is a powerful, metadata-driven reporting engine designed to automate the generation of professional administrative and technical documents (such as *Διαβιβαστικό*, *Αίτημα*, and *Μελέτη*). It bridges the gap between raw structured data and polished PDF reports through a clean Domain-Specific Language (DSL), on-the-fly mathematical processing, and strict type handling.

---

## Key Features

- **Metadata-Driven Architecture**: Write documents using an intuitive DSL combining YAML-based `@data` blocks, `@calc` expressions, reusable `@common` components, and `@output` templates.
- **Advanced DSL Syntax**: 
  - Support for single-line comments (`//`) and inline arithmetic expressions (e.g., `=24000/1.24`).
  - Dynamic variable formatting and precision using `$var:.decimals$` syntax (e.g., `:2`, `:4`, `:0`).
- **Dynamic Table Engine (`@detail table`)**:
  - Automatic column calculations and aliases (e.g., `Ποσότητα * Κόστος * 0.24 AS ΦΠΑ`).
  - Row filtering using `where` clauses.
  - Explicit column typing (`types: [int, str, float, float]`) to prevent unwanted number formatting.
  - Automatic calculation of column totals and unit labeling (e.g., `Euro`).
- **Interactive Preview & Synchronization**: Real-time HTML preview backed by QWebEngine, featuring automated scroll synchronization and a right-click context menu ("Jump to this position in preview") for effortless document navigation.
- **Robust Math & Localization**: Built-in support for locale-aware number and currency formatting and safe mathematical expression evaluation.
- **Seamless HTML-to-PDF Pipeline**: Converts structured Markdown and custom HTML templates into print-ready, professional PDF documents using `xhtml2pdf`.

---

## 📂 Project Structure

```text
EasyCreateReports/
├── app_gui.py             # Main PyQt6 graphical user interface
├── core_engine.py         # Main engine orchestrator and parser
├── engine_data.py         # XML and external data source loader
├── engine_math.py         # Safe math evaluation and sum expressions
├── engine_pdf.py          # HTML-to-PDF conversion utilities
├── engine_converter.py    # DSL <-> XML converter tools
├── md_dictionary.py       # Markdown formatting rules
├── styles.css             # Document layout and styling
├── document.txt           # Main project definition file (DSL)
├── install.sh             # Automated installation script for Ubuntu/Linux
└── install.bat            # Automated installation script for Windows
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

📥 Installation
EasyCreateReports provides automated installation scripts for both Linux (Ubuntu) and Windows environments to set up dependencies and shortcuts instantly.

For Ubuntu / Linux
Download or clone the repository.

Open a terminal inside the project folder and run:

Bash
chmod +x install.sh
./install.sh
This script automatically installs system dependencies (python3-pyqt6, python3-pyqt6.qtwebengine, python3-yaml, python3-xhtml2pdf), copies the application files to your local user directory, and creates a desktop entry shortcut in your application menu.

For Windows
Download or clone the repository.

Right-click on install.bat and select "Run as administrator".This script installs required Python packages (pyqt6, pyqt6-webengine, pyyaml, xhtml2pdf), sets up the local application directory, and creates a ready-to-use shortcut on your Desktop.

Getting Started
Execute the main script manually if running from source:

Bash
python3 app_gui.py
Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

License
This project is open-source and available under the MIT License.
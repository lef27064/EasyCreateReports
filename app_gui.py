import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTextEdit, QPushButton, QSplitter, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Εισαγωγή των δύο modes από τον πυρήνα
from core_engine import compile_for_preview, compile_document


class ReportDesignerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EasyCreateReports - Visual Template Designer")
        self.resize(1300, 850)

        self.current_file_path = None

        # Μενού
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Αρχείο")

        open_action = QAction("📂 Άνοιγμα...", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("💾 Αποθήκευση", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("📄 Αποθήκευση ως .txt...", self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Νέα καθαρή επιλογή για την αποθήκευση των HTML και PDF στον δίσκο
        export_action = QAction("🌐 Εξαγωγή HTML Αρχείων & PDF στον δίσκο", self)
        export_action.triggered.connect(self.export_report_files)
        file_menu.addAction(export_action)

        # Κεντρικό Splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)

        # Αριστερό Παράθυρο (Editor & Toolbar)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)

        toolbar_layout = QHBoxLayout()
        btn_data = QPushButton("📋 @data Block")
        btn_table = QPushButton("📊 Πίνακας + ΦΠΑ")
        btn_section = QPushButton("📌 Ενότητα (##)")

        btn_data.setStyleSheet("background-color: #e1f5fe; font-weight: bold; padding: 6px;")
        btn_table.setStyleSheet("background-color: #e8f5e9; font-weight: bold; padding: 6px;")
        btn_section.setStyleSheet("background-color: #fff3e0; font-weight: bold; padding: 6px;")

        toolbar_layout.addWidget(btn_data)
        toolbar_layout.addWidget(btn_table)
        toolbar_layout.addWidget(btn_section)
        left_layout.addLayout(toolbar_layout)

        self.editor = QTextEdit()
        self.editor.setFontFamily("Consolas")
        self.editor.setFontPointSize(11)
        # --- ΕΝΕΡΓΟΠΟΙΗΣΗ ΔΕΞΙΟΥ ΚΛΙΚ ΓΙΑ ΣΥΓΧΡΟΝΙΣΜΟ ---
        self.editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self.show_editor_context_menu)
        # ------------------------------------------------
        left_layout.addWidget(self.editor)

        # Δεξί Παράθυρο (Preview)
        self.web_view = QWebEngineView()

        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(self.web_view)
        main_splitter.setSizes([600, 700])

        btn_data.clicked.connect(self.insert_data_snippet)
        btn_table.clicked.connect(self.insert_table_snippet)
        btn_section.clicked.connect(self.insert_section_snippet)
        self.editor.textChanged.connect(self.update_preview)

        # Φόρτωση document.txt αν υπάρχει
        if os.path.exists("document.txt"):
            self.open_initial_file("document.txt")
        else:
            self.load_default_template()

    def insert_data_snippet(self):
        snippet = """@data
title: "Τίτλος Μελέτης"
protokollo: "123/2026"
tbl_meleti:
  - Περιγραφή: "Εργασία Α'"
    μ.μ.: "Τμχ"
    dapani: 100.00
    Ποσότητα: 5
@end\n\n"""
        self.editor.insertPlainText(snippet)

    def insert_table_snippet(self):
        snippet = '@detail table{name="tbl_meleti", title="Α. Πίνακας Δαπανών:", select="Α/Α, Περιγραφή, μ.μ., dapani AS Τιμή, Ποσότητα, dapani * Ποσότητα AS Μερική Δαπάνη", totals="Μερική Δαπάνη: €", vat="0.24"}\n'
        self.editor.insertPlainText(snippet)

    def insert_section_snippet(self):
        snippet = "\n## 1.0 ΤΕΧΝΙΚΗ ΠΕΡΙΓΡΑΦΗ\nΚείμενο παραγράφου εδώ...\n\n"
        self.editor.insertPlainText(snippet)

    def load_default_template(self):
        default_content = """@data
title: "Συντήρηση Δημοτικών Οδών"
protokollo: "452/2026"
tbl_meleti:
  - Περιγραφή: "Μίσθωση καταλλήλου Μηχανήματος (φορτωτής JCB)"
    μ.μ.: "Ώρα"
    dapani: 35.00
    Ποσότητα: 158.00
@end

## 1.2 ΠΡΟΥΠΟΛΟΓΙΣΜΟΣ
@detail table{name="tbl_meleti", title="Ενδεικτικός Προϋπολογισμός", select="Α/Α, Περιγραφή, μ.μ., dapani AS Τιμή, Ποσότητα, dapani * Ποσότητα AS Μερική Δαπάνη", totals="Μερική Δαπάνη: €", vat="0.24"}
"""
        self.editor.setPlainText(default_content)
        self.current_file_path = None

    def open_initial_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.current_file_path = file_path
            self.setWindowTitle(f"EasyCreateReports - Visual Template Designer [{os.path.basename(file_path)}]")
        except Exception:
            self.load_default_template()

    def update_preview(self):
        """Ενημερώνει τη ζωντανή προεπισκόπηση στη μνήμη με σωστό Base URL για τις εικόνες."""
        raw_text = self.editor.toPlainText()
        temp_path = "_temp_preview.txt"
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(raw_text)
            html_output = compile_for_preview(temp_path)
            
            base_dir = os.path.dirname(self.current_file_path) if self.current_file_path else os.getcwd()
            base_url = QUrl.fromLocalFile(os.path.abspath(base_dir) + os.path.sep)
            
            self.web_view.setHtml(html_output, base_url)
        except Exception:
            pass

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Άνοιγμα Αρχείου DSL", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            self.open_initial_file(file_path)

    def save_file(self):
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                QMessageBox.information(self, "Επιτυχία", "Το αρχείο αποθηκεύτηκε επιτυχώς.")
            except Exception as e:
                QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα αποθήκευσης:\n{e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Αποθήκευση ως .txt", "document.txt", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                self.current_file_path = file_path
                self.setWindowTitle(f"EasyCreateReports - Visual Template Designer [{os.path.basename(file_path)}]")
                QMessageBox.information(self, "Επιτυχία", f"Το αρχείο αποθηκεύτηκε στο:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα αποθήκευσης:\n{e}")

    def show_editor_context_menu(self, pos):
        """Δημιουργεί προσαρμοσμένο δεξί κλικ στον editor με επιλογή συγχρονισμού."""
        menu = self.editor.createStandardContextMenu()
        menu.addSeparator()
        jump_action = menu.addAction("📍 Μετάβαση σε αυτό το σημείο στην προεπισκόπηση")
        jump_action.triggered.connect(self.jump_preview_to_cursor)
        menu.exec(self.editor.mapToGlobal(pos))

    def jump_preview_to_cursor(self):
        """Εντοπίζει την πλησιέστερη ενότητα στον κέρσορα και κάνει scroll στο preview."""
        cursor = self.editor.textCursor()
        block_number = cursor.blockNumber()
        
        raw_text = self.editor.toPlainText()
        lines = raw_text.split('\n')
        
        # Μετράμε πόσες επικεφαλίδες (#) υπάρχουν από την αρχή μέχρι τη γραμμή του κέρσορα
        header_count = 0
        for i in range(min(block_number + 1, len(lines))):
            if lines[i].strip().startswith('#'):
                header_count += 1
                
        target_id_index = max(0, header_count - 1)
        
        # Εκτέλεση JavaScript στο QWebEngineView για ομαλή κύλιση
        js_code = f"""
        var el = document.getElementById('sec-{target_id_index}');
        if (el) {{
            el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
        """
        self.web_view.page().runJavaScript(js_code)

    def export_report_files(self):
        """Εκτελεί την παραγωγή και αποθήκευση των ξεχωριστών HTML αρχείων και PDF στον δίσκο."""
        if not self.current_file_path:
            self.save_file_as()
            if not self.current_file_path:
                return
        
        try:
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            
            compile_document(self.current_file_path)
            
            QMessageBox.information(self, "Επιτυχία", "Τα αρχεία HTML και τα PDF αποθηκεύτηκαν επιτυχώς στον δίσκο!")
        except Exception as e:
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα κατά την εξαγωγή:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReportDesignerApp()
    window.show()
    sys.exit(app.exec())
import os
from xhtml2pdf import pisa

def convert_html_to_pdf(html_filepath, pdf_filepath=None):
    if not pdf_filepath:
        pdf_filepath = os.path.splitext(html_filepath)[0] + ".pdf"

    if not os.path.exists(html_filepath):
        print(f"Σφάλμα: Το αρχείο HTML '{html_filepath}' δεν βρέθηκε.")
        return False

    try:
        base_dir = os.path.dirname(os.path.abspath(html_filepath))

        with open(html_filepath, "r", encoding="utf-8") as html_file:
            html_content = html_file.read()

        with open(pdf_filepath, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                html_content, 
                dest=pdf_file, 
                encoding='utf-8',
                path=base_dir
            )

        if pisa_status.err:
            print(f"Σφάλμα κατά τη μετατροπή σε PDF για το {html_filepath}: {pisa_status.err}")
            if os.path.exists(pdf_filepath):
                os.remove(pdf_filepath)
            return False
        
        print(f"Δημιουργήθηκε επιτυχώς το PDF: {pdf_filepath}")
        return True
        
    except Exception as e:
        print(f"Σφάλμα κατά την παραγωγή PDF: {e}")
        if os.path.exists(pdf_filepath):
            os.remove(pdf_filepath)
        return False
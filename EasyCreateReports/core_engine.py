import re
import os
import locale
import yaml
from md_dictionary import MARKDOWN_RULES
from engine_math import SAFE_MATH_DICT, create_sum_expression
from engine_data import load_xml_data
from engine_converter import txt_to_xml
from engine_pdf import convert_html_to_pdf
from engine_dates import get_dates_env

# Αρχικοποίηση τοπικών ρυθμίσεων από το ΛΣ
try:
    locale.setlocale(locale.LC_ALL, '')
except Exception:
    try:
        locale.setlocale(locale.LC_ALL, 'el_GR.UTF-8')
    except Exception:
        pass

def load_styles(css_filepath="styles.css"):
    if os.path.exists(css_filepath):
        with open(css_filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return "body { font-family: sans-serif; padding: 20px; }"


def _evaluate_expressions(data):
    """Αναδρομική αξιολόγηση αριθμητικών παραστάσεων που ξεκινούν με '=' στο @data."""
    if isinstance(data, dict):
        return {k: _evaluate_expressions(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_evaluate_expressions(item) for item in data]
    elif isinstance(data, str) and data.strip().startswith('='):
        expr = data.strip()[1:].strip()
        expr = expr.replace(',', '.')  # Μετατροπή ελληνικού κόμματος σε τελεία για την python
        try:
            local_dict = SAFE_MATH_DICT.copy()
            val = eval(expr, {"__builtins__": {}}, local_dict)
            return float(val)
        except Exception:
            return data
    return data


def _prepare_environment(input_filepath):
    """Κοινή προετοιμασία περιβάλλοντος, δεδομένων, common blocks και μαθηματικών."""
    with open(input_filepath, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    # --- 1. ΦΙΛΤΡΑΡΙΣΜΑ ΣΧΟΛΙΩΝ (Αφαίρεση γραμμών που ξεκινούν με //) ---
    lines = raw_content.split('\n')
    clean_lines = []
    for line in lines:
        if line.strip().startswith('//'):
            continue  # Αγνοούμε τα σχόλια
        clean_lines.append(line)
    content = '\n'.join(clean_lines)
    # ----------------------------------------------------------------
        
    css_content = load_styles()
        
    config_match = re.search(r'@config\s*(.*?)\s*@end', content, re.DOTALL)
    config_env = yaml.safe_load(config_match.group(1)) if config_match else {}
    
    data_match = re.search(r'@data\s*(.*?)\s*@end', content, re.DOTALL)
    calc_match = re.search(r'@calc\s*(.*?)\s*@end', content, re.DOTALL)
    
    if not data_match:
        raise ValueError("Σφάλμα: Λείπει το απαραίτητο block @data.")
        
    data_env = yaml.safe_load(data_match.group(1)) or {}
    
    # --- 2. ΥΠΟΛΟΓΙΣΜΟΣ ΑΡΙΘΜΗΤΙΚΩΝ ΠΑΡΑΣΤΑΣΕΩΝ (=...) ---
    data_env = _evaluate_expressions(data_env)
    # ----------------------------------------------------
    
    # --- ΕΛΕΓΧΟΣ ΚΑΙ ΦΟΡΤΩΣΗ ΕΞΩΤΕΡΙΚΩΝ XML ΠΗΓΩΝ ---
    for k, v in list(data_env.items()):
        if isinstance(v, dict) and "xml_source" in v:
            xml_file = v["xml_source"]
            row_tag = v.get("row_tag", "row")
            data_env[k] = load_xml_data(xml_file, row_tag)
    # -----------------------------------------------
    
    def fmt(value, decimals=2):
        try:
            val_float = float(value)
            use_grouped = config_env.get("thousand_separator", True)
            if use_grouped:
                return locale.format_string(f"%.{decimals}f", val_float, grouping=True)
            else:
                return f"{val_float:.{decimals}f}"
        except (ValueError, TypeError):
            return str(value)

    data_env["fmt"] = fmt

    # Common blocks
    common_blocks = re.findall(r'@common\s+([a-zA-Z0-9_]+)\s*(.*?)\s*@end', content, re.DOTALL)
    common_env = {name.strip(): c_text.strip() for name, c_text in common_blocks}

    for c_key, c_val in common_env.items():
        for k, v in data_env.items():
            if isinstance(v, (str, int, float)):
                c_val = c_val.replace(f"${k}$", str(v))
        common_env[c_key] = c_val

    data_env.update(common_env)
    
    # Μαθηματικός κινητήρας
    sum_expr = create_sum_expression(data_env)
    calc_env = data_env.copy()
    calc_env["sum_expression"] = sum_expr
    calc_env["fmt"] = fmt
    
    # --- ΦΟΡΤΩΣΗ ΑΥΤΟΜΑΤΩΝ ΗΜΕΡΟΜΗΝΙΩΝ ΑΠΟ ΤΟ ENGINE_DATES ---
    calc_env.update(get_dates_env())
    # ---------------------------------------------------------

    if calc_match:
        exec(calc_match.group(1), {}, calc_env)
        
    data_env.update(calc_env)
    return content, data_env, css_content



def _process_body_text(body_text, data_env):
    """Επεξεργάζεται το κείμενο σώματος (αντικατάσταση μεταβλητών, πίνακες, markdown)."""
    body_text = body_text.strip()
        
    # --- ΑΝΤΙΚΑΤΑΣΤΑΣΗ ΜΕΤΑΒΛΗΤΩΝ ΜΕ ΥΠΟΣΤΗΡΙΞΗ ΜΟΡΦΟΠΟΙΗΣΗΣ (π.χ. $var:.4$, $var:.0$) ---
    def replace_var(match):
        key = match.group(1)
        decimals_str = match.group(2)
        
        if key not in data_env:
            return match.group(0)  # Αν δεν βρεθεί η μεταβλητή, την αφήνουμε ως έχει
            
        val = data_env[key]
        
        # Αν έχει δοθεί ρητά ένδειξη δεκαδικών (π.χ. :4 ή :0)
        if decimals_str is not None:
            try:
                decimals = int(decimals_str)
                return data_env["fmt"](val, decimals=decimals)
            except Exception:
                return str(val)
        else:
            # Τυπική συμπεριφορά
            if isinstance(val, (int, float)):
                return data_env["fmt"](val)
            elif isinstance(val, str):
                return val
            return str(val)

    # Regex που ψάχνει για $key$ ή $key:.decimals$
    body_text = re.sub(r'\$([a-zA-Z0-9_]+)(?::\.([0-9]+))?\$', replace_var, body_text)
    # ----------------------------------------------------------------------------------

    for key, val in data_env.items():
        if isinstance(val, (int, float)):
            body_text = body_text.replace(f"${key}$", data_env["fmt"](val))
        elif isinstance(val, str):
            body_text = body_text.replace(f"${key}$", val)

    def replace_table(match):
        content_inside = match.group(1)
        
        name_match = re.search(r'name="([^"]+)"', content_inside)
        if not name_match:
            return ""
        tbl_name = name_match.group(1)
        
        title_match = re.search(r'title="([^"]+)"', content_inside)
        tbl_title = title_match.group(1) if title_match else ""
        
        vat_match = re.search(r'vat="([^"]+)"', content_inside)
        vat_rate = float(vat_match.group(1)) if vat_match else 0.0
        
        table_data = data_env.get(tbl_name, {})
        
        if isinstance(table_data, list):
            if not table_data:
                return f"<!-- Ο πίνακας {tbl_name} είναι κενός -->"
            orig_headers = list(table_data[0].keys())
            rows = [[row.get(h, "") for h in orig_headers] for row in table_data]
            column_types = []
        else:
            orig_headers = list(table_data.get("headers", []))
            rows = [list(r) for r in table_data.get("rows", [])]
            column_types = table_data.get("types", [])
            
        headers = list(orig_headers)
        
        if not rows and not orig_headers:
            return f"<!-- Ο πίνακας {tbl_name} δεν βρέθηκε ή είναι κενός -->"

        # --- ΜΗΧΑΝΙΣΜΟΣ SELECT / WHERE & CALCULATIONS ---
        select_match = re.search(r'select="([^"]+)"', content_inside)
        if select_match:
            select_query = select_match.group(1).strip()
            
            if " where " in select_query.lower():
                parts = re.split(r'\s+where\s+', select_query, flags=re.IGNORECASE)
                sel_cols_str = parts[0].strip()
                where_cond = parts[1].strip()
            else:
                sel_cols_str = select_query
                where_cond = None
            
            if where_cond and orig_headers:
                filtered_rows = []
                for row in rows:
                    try:
                        local_env = SAFE_MATH_DICT.copy()
                        for idx, h in enumerate(orig_headers):
                            try:
                                local_env[h] = float(row[idx])
                            except (ValueError, TypeError):
                                local_env[h] = row[idx]
                        if eval(where_cond, {"__builtins__": {}}, local_env):
                            filtered_rows.append(row)
                    except Exception:
                        pass
                rows = filtered_rows

            if sel_cols_str != "*" and orig_headers:
                requested_items = [item.strip() for item in sel_cols_str.split(',')]
                new_rows = []
                new_headers = []
                
                for row in rows:
                    row_dict = SAFE_MATH_DICT.copy()
                    for idx, h in enumerate(orig_headers):
                        try:
                            row_dict[h] = float(row[idx])
                        except (ValueError, TypeError):
                            row_dict[h] = row[idx]
                
                    new_row_values = []
                    row_headers = []
                    
                    for item in requested_items:
                        if re.search(r'\s+AS\s+', item, flags=re.IGNORECASE):
                            expr, alias = re.split(r'\s+AS\s+', item, maxsplit=1, flags=re.IGNORECASE)
                            expr = expr.strip()
                            alias = alias.strip()
                            if alias not in row_headers:
                                row_headers.append(alias)
                            try:
                                val = eval(expr, {"__builtins__": {}}, row_dict)
                                new_row_values.append(val)
                                row_dict[alias] = val
                            except Exception:
                                new_row_values.append(0.0)
                                row_dict[alias] = 0.0
                        elif item in orig_headers:
                            if item not in row_headers:
                                row_headers.append(item)
                            val = row_dict.get(item, 0.0)
                            new_row_values.append(val)
                        else:
                            expr = item
                            if expr not in row_headers:
                                row_headers.append(expr)
                            try:
                                val = eval(expr, {"__builtins__": {}}, row_dict)
                                new_row_values.append(val)
                                row_dict[expr] = val
                            except Exception:
                                new_row_values.append(0.0)
                                row_dict[expr] = 0.0
                    
                    if not new_headers:
                        new_headers = row_headers
                    new_rows.append(new_row_values)
                
                headers = new_headers
                rows = new_rows

        calc_blocks = re.findall(r'calc\d*=\s*\((.*?)\)', content_inside)
        for block in calc_blocks:
            name_m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', block)
            form_m = re.search(r'formula\s*=\s*["\']([^"\']+)["\']', block)
            
            if name_m and form_m:
                col_name = name_m.group(1).strip()
                formula = form_m.group(1).strip()
                headers.append(col_name)
                
                for row_idx, row in enumerate(rows):
                    try:
                        local_env = SAFE_MATH_DICT.copy()
                        for idx, h in enumerate(orig_headers):
                            try:
                                local_env[h] = float(row[idx])
                            except (ValueError, TypeError):
                                local_env[h] = 0.0
                        
                        val = eval(formula, {"__builtins__": {}}, local_env)
                        row.append(float(val))
                    except Exception:
                        row.append(0.0)

        hide_match = re.search(r'hide="([^"]+)"', content_inside)
        hidden_cols = [h.strip() for h in hide_match.group(1).split(',')] if hide_match else []
        
        totals_match = re.search(r'totals="([^"]+)"', content_inside)
        column_units = {}
        if totals_match:
            items = totals_match.group(1).split(',')
            for item in items:
                if ':' in item:
                    col, unit = item.split(':', 1)
                    column_units[col.strip()] = unit.strip()
                else:
                    column_units[item.strip()] = "€"

        visible_indices = [i for i, h in enumerate(headers) if h not in hidden_cols]
        visible_headers = [headers[i] for i in visible_indices]
        
        html = []
        if tbl_title:
            html.append(f"<h3>{tbl_title}</h3>")
        html.append('<table class="printable-table" border="1" style="width:100%; border-collapse:collapse;">')
        html.append("<thead><tr style='background-color:#f2f2f2;'>" + "".join(f"<th style='padding:8px;'>{h}</th>" for h in visible_headers) + "</tr></thead>")
        html.append("<tbody>")
        
        col_sums = {h: 0.0 for h in visible_headers}
        
        for row in rows:
            for i, h in zip(visible_indices, visible_headers):
                try:
                    col_sums[h] += float(row[i])
                except (ValueError, TypeError):
                    pass

            visible_row = []
            for idx, (i, h) in enumerate(zip(visible_indices, visible_headers)):
                val = row[i] if i < len(row) else ""
                
                col_type = None
                if idx < len(column_types):
                    t_val = column_types[idx]
                    if isinstance(t_val, str):
                        col_type = t_val.lower()
                    else:
                        col_type = getattr(t_val, '__name__', str(t_val)).lower()

                if col_type in ['int', 'integer']:
                    try:
                        visible_row.append(str(int(float(val))))
                    except (ValueError, TypeError):
                        visible_row.append(str(val))
                elif col_type in ['float', 'double']:
                    try:
                        visible_row.append(data_env["fmt"](float(val)))
                    except (ValueError, TypeError):
                        visible_row.append(str(val))
                elif isinstance(val, (int, float)):
                    visible_row.append(data_env["fmt"](val))
                else:
                    visible_row.append(str(val))

            html.append("<tr>" + "".join(f"<td style='padding:6px; text-align:center;'>{c}</td>" for c in visible_row) + "</tr>")
                
        # --- ΔΗΜΙΟΥΡΓΙΑ ΕΠΙΠΛΕΟΝ ΓΡΑΜΜΩΝ (Σύνολο, ΦΠΑ, Τελικό) ---
        if column_units:
            colspan = len(visible_headers) - 1
            total_col_key = list(column_units.keys())[0]
            subtotal_val = col_sums.get(total_col_key, 0.0)
            unit = column_units[total_col_key]

            html.append(f"<tr><td colspan='{colspan}' style='text-align:right; font-weight:bold; padding:8px;'>Σύνολο Δαπάνης:</td><td style='text-align:center; font-weight:bold; padding:8px;'>{data_env['fmt'](subtotal_val)} {unit}</td></tr>")
            
            if vat_rate > 0:
                vat_val = subtotal_val * vat_rate
                grand_total = subtotal_val + vat_val
                vat_percent = int(vat_rate * 100)
                
                html.append(f"<tr><td colspan='{colspan}' style='text-align:right; font-weight:bold; padding:8px;'>Φ.Π.Α. {vat_percent}%:</td><td style='text-align:center; font-weight:bold; padding:8px;'>{data_env['fmt'](vat_val)} {unit}</td></tr>")
                html.append(f"<tr style='background-color:#e6f2ff;'><td colspan='{colspan}' style='text-align:right; font-weight:bold; padding:8px;'>Σύνολο Σύμβασης:</td><td style='text-align:center; font-weight:bold; padding:8px;'>{data_env['fmt'](grand_total)} {unit}</td></tr>")

        html.append("</tbody></table>")
        return "\n".join(html)

    body_text = re.sub(
        r'@detail\s+table\{(.*?)\}',
        replace_table,
        body_text,
        flags=re.DOTALL
    )

    def parse_markdown(text):
        lines = text.split('\n')
        parsed_lines = []
        in_list = False
        h_index = 0  # Μετρητής για μοναδικά IDs στις επικεφαλίδες

        for line in lines:
            line_str = line.strip()
            
            if line_str.startswith('<table') or line_str.startswith('<h3>') or line_str.startswith('<tr') or line_str.startswith('<div'):
                if in_list:
                    parsed_lines.append('</ul>')
                    in_list = False
                parsed_lines.append(line)
                continue

            if re.match(MARKDOWN_RULES['horizontal_rule']['pattern'], line_str):
                if in_list:
                    parsed_lines.append('</ul>')
                    in_list = False
                parsed_lines.append(MARKDOWN_RULES['horizontal_rule']['replacement'])
                continue

            if line_str.startswith('#'):
                if in_list:
                    parsed_lines.append('</ul>')
                    in_list = False
                h_match = re.match(r'^(#{1,6})\s+(.+)$', line_str)
                if h_match:
                    level = len(h_match.group(1))
                    header_content = h_match.group(2)
                    header_content = re.sub(MARKDOWN_RULES['bold']['pattern'], MARKDOWN_RULES['bold']['replacement'], header_content)
                    header_content = re.sub(MARKDOWN_RULES['italic']['pattern'], MARKDOWN_RULES['italic']['replacement'], header_content)
                    # Προσθήκη μοναδικού id για συγχρονισμό κύλισης
                    parsed_lines.append(f'<h{level} id="sec-{h_index}">{header_content}</h{level}>')
                    h_index += 1
                    continue

            if line_str.startswith('>'):
                if in_list:
                    parsed_lines.append('</ul>')
                    in_list = False
                parsed_lines.append(f'<blockquote>{line_str[1:].strip()}</blockquote>')
                continue

            list_match = re.match(r'^[\*\-]\s+(.+)$', line_str)
            if list_match:
                if not in_list:
                    parsed_lines.append('<ul>')
                    in_list = True
                parsed_lines.append(f'<li>{list_match.group(1)}</li>')
                continue
            else:
                if in_list:
                    parsed_lines.append('</ul>')
                    in_list = False

            if line_str:
                parsed_lines.append(f'<p>{line_str}</p>')
            else:
                parsed_lines.append('')

        if in_list:
            parsed_lines.append('</ul>')

        html_out = '\n'.join(parsed_lines)
        html_out = re.sub(MARKDOWN_RULES['bold']['pattern'], MARKDOWN_RULES['bold']['replacement'], html_out)
        html_out = re.sub(MARKDOWN_RULES['italic']['pattern'], MARKDOWN_RULES['italic']['replacement'], html_out)
        
        return html_out

    body_text = parse_markdown(body_text)
    return body_text


def compile_for_preview(input_filepath):
    """MODE 1: IN-MEMORY (Προεπισκόπηση) - Συγκεντρώνει αποκλειστικά τα @output blocks χωρίς διπλοεγγραφές."""
    content, data_env, css_content = _prepare_environment(input_filepath)

    # Εντοπισμός όλων των @output blocks
    output_blocks = re.findall(r'@output\s*["\']([^"\']+)["\']\s*(.*?)\s*@end', content, re.DOTALL)
    
    if output_blocks:
        extracted_sections = []
        for output_filename, raw_body in output_blocks:
            processed_body = _process_body_text(raw_body, data_env)
            extracted_sections.append(processed_body)
        
        # Συνένωση των τμημάτων των @output blocks ακριβώς μία φορά
        combined_body = "\n<hr style='margin: 40px 0; border: 1px dashed #ccc;'>\n".join(extracted_sections)
    else:
        # Fallback: Αν δεν υπάρχουν @output blocks, καθαρίζουμε τα control blocks και παίρνουμε το σώμα
        body_text = content
        body_text = re.sub(r'@config\s*.*?\s*@end', '', body_text, flags=re.DOTALL)
        body_text = re.sub(r'@data\s*.*?\s*@end', '', body_text, flags=re.DOTALL)
        body_text = re.sub(r'@calc\s*.*?\s*@end', '', body_text, flags=re.DOTALL)
        body_text = re.sub(r'@common\s+[a-zA-Z0-9_]+\s*.*?\s*@end', '', body_text, flags=re.DOTALL)
        combined_body = _process_body_text(body_text, data_env)

    full_html = f"""<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <title>Preview Mode</title>
    <style>
{css_content}
    </style>
</head>
<body>
    {combined_body}
</body>
</html>
"""
    return full_html


def compile_document(input_filepath):
    """MODE 2: HARD DRIVE (Εξαγωγή) - Χωρίζει τα αρχεία κανονικά στον δίσκο και παράγει PDF."""
    content, data_env, css_content = _prepare_environment(input_filepath)

    output_blocks = re.findall(r'@output\s*["\']([^"\']+)["\']\s*(.*?)\s*@end', content, re.DOTALL)
    
    if not output_blocks:
        body_match = re.search(r'@body\s*(.*?)$', content, re.DOTALL)
        if body_match:
            b_text = body_match.group(1).strip()
            if b_text.endswith('@end'):
                b_text = b_text[:-4].strip()
            output_blocks = [("report.html", b_text)]
        else:
            raise ValueError("Σφάλμα: Δεν βρέθηκαν blocks @output ή @body.")

    for output_filename, raw_body in output_blocks:
        body_text = _process_body_text(raw_body, data_env)

        html_template = f"""<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <title>{output_filename}</title>
    <style>
{css_content}
    </style>
</head>
<body>
    {body_text}
</body>
</html>
"""

        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_template)
            
        print(f"Δημιουργήθηκε επιτυχώς: {output_filename}")
        
        pdf_filename = os.path.splitext(output_filename)[0] + ".pdf"
        convert_html_to_pdf(output_filename, pdf_filename)


if __name__ == "__main__":
    compile_document("document.txt")
    txt_to_xml("document.txt","document.xml")
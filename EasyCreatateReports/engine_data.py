import xml.etree.ElementTree as ET

def load_xml_data(filepath, table_tag="row"):
    """
    Διαβάζει ένα αρχείο XML και επιστρέφει ένα λεξικό με headers και rows
    κατάλληλο για το data_env του parser.
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        return {"headers": [], "rows": []}
    
    headers = []
    rows = []
    
    # Εντοπισμός όλων των εγγραφών (π.χ. <row> ή <record>)
    items = root.findall(f".//{table_tag}") if table_tag else list(root)
    
    for item in items:
        row_data = []
        for child in item:
            tag = child.tag
            if tag not in headers:
                headers.append(tag)
            
            val = child.text.strip() if child.text else ""
            # Προσπάθεια μετατροπής σε αριθμό αν είναι εφικτό
            try:
                if "." in val or "," in val:
                    val = float(val.replace(',', '.'))
                else:
                    val = int(val)
            except ValueError:
                pass
            
            row_data.append(val)
            
        rows.append(row_data)
        
    return {
        "headers": headers,
        "rows": rows
    }
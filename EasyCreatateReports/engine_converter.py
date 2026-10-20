import re
import yaml
import xml.etree.ElementTree as ET
from xml.dom import minidom

def dict_to_xml_nodes(parent, data):
    """Μετατρέπει αναδρομικά ένα Python Dictionary σε δομημένα XML nodes."""
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                node = ET.SubElement(parent, "entry", name=str(k), type="dict")
                dict_to_xml_nodes(node, v)
            elif isinstance(v, list):
                node = ET.SubElement(parent, "entry", name=str(k), type="list")
                for item in v:
                    item_node = ET.SubElement(node, "item")
                    dict_to_xml_nodes(item_node, item)
            else:
                node = ET.SubElement(parent, "entry", name=str(k), type="value")
                node.text = str(v) if v is not None else ""
    elif isinstance(data, list):
        for item in data:
            item_node = ET.SubElement(parent, "item")
            if isinstance(item, (dict, list)):
                dict_to_xml_nodes(item_node, item)
            else:
                item_node.text = str(item)
    else:
        parent.text = str(data)

def xml_nodes_to_dict(node):
    """Μετατρέπει αναδρομικά τα δομημένα XML nodes ξανά σε Python Dictionary."""
    if node.attrib.get("type") == "value" or len(node) == 0:
        return node.text
    
    if node.attrib.get("type") == "list" or node.tag == "list":
        lst = []
        for child in node:
            if len(child) > 0:
                lst.append(xml_nodes_to_dict(child))
            else:
                lst.append(child.text)
        return lst

    d = {}
    for child in node:
        name = child.attrib.get("name")
        if name:
            if child.attrib.get("type") in ["dict", "list"]:
                d[name] = xml_nodes_to_dict(child)
            else:
                d[name] = child.text
    return d


def txt_to_xml(txt_filepath, xml_output_filepath):
    """
    Μετατρέπει το αρχείο DSL (document.txt) σε πλήρως δομημένο XML για το GUI,
    αναλύοντας τα @data μέσω YAML parser.
    """
    with open(txt_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    root = ET.Element("report_project")

    # 1. @config
    cfg_m = re.search(r'@config\s*(.*?)\s*@end', content, re.DOTALL)
    if cfg_m:
        cfg_el = ET.SubElement(root, "config")
        for line in cfg_m.group(1).strip().split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                item = ET.SubElement(cfg_el, k.strip())
                item.text = v.strip()

    # 2. @data (Πλήρης Ανάλυση σε XML Nodes)
    data_m = re.search(r'@data\s*(.*?)\s*@end', content, re.DOTALL)
    if data_m:
        data_el = ET.SubElement(root, "data")
        parsed_yaml = yaml.safe_load(data_m.group(1)) or {}
        dict_to_xml_nodes(data_el, parsed_yaml)

    # 3. @calc
    calc_m = re.search(r'@calc\s*(.*?)\s*@end', content, re.DOTALL)
    if calc_m:
        calc_el = ET.SubElement(root, "calc")
        calc_el.text = calc_m.group(1).strip()

    # 4. @common
    commons = re.findall(r'@common\s+([a-zA-Z0-9_]+)\s*(.*?)\s*@end', content, re.DOTALL)
    if commons:
        commons_el = ET.SubElement(root, "commons")
        for c_name, c_body in commons:
            c_el = ET.SubElement(commons_el, "common", name=c_name.strip())
            c_el.text = c_body.strip()

    # 5. @output
    outputs = re.findall(r'@output\s*["\']([^"\']+)["\']\s*(.*?)\s*@end', content, re.DOTALL)
    if outputs:
        outputs_el = ET.SubElement(root, "outputs")
        for out_name, out_body in outputs:
            out_el = ET.SubElement(outputs_el, "output", filename=out_name)
            out_el.text = out_body.strip()

    # Pretty Print XML
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed = minidom.parseString(xml_str)
    pretty_xml = parsed.toprettyxml(indent="  ")

    with open(xml_output_filepath, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    print(f"Δομημένη Μετατροπή: {txt_filepath} -> {xml_output_filepath}")


def xml_to_txt(xml_filepath, txt_output_filepath):
    """
    Ανασυνθέτει το αρχείο DSL (document.txt) από το δομημένο XML του GUI.
    """
    tree = ET.parse(xml_filepath)
    root = tree.getroot()

    lines = []

    # 1. Config
    cfg_el = root.find("config")
    if cfg_el is not None and len(cfg_el) > 0:
        lines.append("@config")
        for child in cfg_el:
            lines.append(f"{child.tag}: {child.text}")
        lines.append("@end\n")

    # 2. Data (Μετατροπή των XML nodes ξανά σε καθαρό YAML block)
    data_el = root.find("data")
    if data_el is not None:
        data_dict = xml_nodes_to_dict(data_el)
        yaml_str = yaml.safe_dump(data_dict, allow_unicode=True, sort_keys=False)
        lines.append("@data")
        lines.append(yaml_str.strip())
        lines.append("@end\n")

    # 3. Calc
    calc_el = root.find("calc")
    if calc_el is not None and calc_el.text:
        lines.append("@calc")
        lines.append(calc_el.text.strip())
        lines.append("@end\n")

    # 4. Commons
    commons_el = root.find("commons")
    if commons_el is not None:
        for c in commons_el.findall("common"):
            lines.append(f"@common {c.attrib.get('name')}")
            lines.append((c.text or "").strip())
            lines.append("@end\n")

    # 5. Outputs
    outputs_el = root.find("outputs")
    if outputs_el is not None:
        for out in outputs_el.findall("output"):
            lines.append(f'@output "{out.attrib.get("filename")}"')
            lines.append((out.text or "").strip())
            lines.append("@end\n")

    with open(txt_output_filepath, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"Ανασύνθεση DSL: {xml_filepath} -> {txt_output_filepath}")
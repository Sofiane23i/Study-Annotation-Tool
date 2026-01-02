"""Pascal VOC XML format exporter."""

import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


def export_voc(boxes, image_path, output_dir, image_size=None):
    """
    Export annotations in Pascal VOC XML format.
    
    Args:
        boxes: List of dicts with 'coords' and 'label'
        image_path: Source image path
        output_dir: Output directory
        image_size: (width, height) tuple
    
    Returns:
        Path to exported file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.xml")
    
    # Create root element
    annotation = Element('annotation')
    
    # Add folder
    folder = SubElement(annotation, 'folder')
    folder.text = os.path.basename(os.path.dirname(image_path))
    
    # Add filename
    filename = SubElement(annotation, 'filename')
    filename.text = os.path.basename(image_path)
    
    # Add path
    path = SubElement(annotation, 'path')
    path.text = os.path.abspath(image_path)
    
    # Add source
    source = SubElement(annotation, 'source')
    database = SubElement(source, 'database')
    database.text = 'Study Annotation Tool'
    
    # Add size
    size = SubElement(annotation, 'size')
    width_elem = SubElement(size, 'width')
    width_elem.text = str(image_size[0] if image_size else 0)
    height_elem = SubElement(size, 'height')
    height_elem.text = str(image_size[1] if image_size else 0)
    depth_elem = SubElement(size, 'depth')
    depth_elem.text = '3'
    
    # Add segmented
    segmented = SubElement(annotation, 'segmented')
    segmented.text = '0'
    
    # Add objects
    for box in boxes:
        x1, y1, x2, y2 = box['coords']
        label = box.get('label', 'unknown')
        
        obj = SubElement(annotation, 'object')
        
        name = SubElement(obj, 'name')
        name.text = label
        
        pose = SubElement(obj, 'pose')
        pose.text = 'Unspecified'
        
        truncated = SubElement(obj, 'truncated')
        truncated.text = '0'
        
        difficult = SubElement(obj, 'difficult')
        difficult.text = '0'
        
        bndbox = SubElement(obj, 'bndbox')
        
        xmin = SubElement(bndbox, 'xmin')
        xmin.text = str(int(min(x1, x2)))
        
        ymin = SubElement(bndbox, 'ymin')
        ymin.text = str(int(min(y1, y2)))
        
        xmax = SubElement(bndbox, 'xmax')
        xmax.text = str(int(max(x1, x2)))
        
        ymax = SubElement(bndbox, 'ymax')
        ymax.text = str(int(max(y1, y2)))
    
    # Pretty print XML
    xml_str = minidom.parseString(tostring(annotation)).toprettyxml(indent="  ")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    return output_path

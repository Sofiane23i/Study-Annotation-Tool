"""COCO JSON format exporter."""

import os
import json
from datetime import datetime


def export_coco(boxes, image_path, output_dir, image_size=None):
    """
    Export annotations in COCO format.
    
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
    output_path = os.path.join(output_dir, f"{base_name}_coco.json")
    
    # Build category mapping
    categories = {}
    cat_id = 1
    
    for box in boxes:
        label = box.get('label', 'unknown')
        if label not in categories:
            categories[label] = cat_id
            cat_id += 1
    
    # Build COCO structure
    coco = {
        'info': {
            'description': 'Handwriting Annotation Dataset',
            'version': '1.0',
            'year': datetime.now().year,
            'contributor': 'Study Annotation Tool',
            'date_created': datetime.now().isoformat()
        },
        'licenses': [],
        'images': [{
            'id': 1,
            'file_name': os.path.basename(image_path),
            'width': image_size[0] if image_size else 0,
            'height': image_size[1] if image_size else 0
        }],
        'annotations': [],
        'categories': [
            {'id': cid, 'name': name, 'supercategory': 'text'}
            for name, cid in categories.items()
        ]
    }
    
    # Add annotations
    for idx, box in enumerate(boxes):
        x1, y1, x2, y2 = box['coords']
        label = box.get('label', 'unknown')
        
        x, y = min(x1, x2), min(y1, y2)
        w, h = abs(x2 - x1), abs(y2 - y1)
        
        coco['annotations'].append({
            'id': idx + 1,
            'image_id': 1,
            'category_id': categories[label],
            'bbox': [x, y, w, h],
            'area': w * h,
            'segmentation': [[x, y, x+w, y, x+w, y+h, x, y+h]],
            'iscrowd': 0,
            'attributes': {
                'text': label
            }
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coco, f, indent=2, ensure_ascii=False)
    
    return output_path

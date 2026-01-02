"""JSON Lines format exporter (one JSON object per line)."""

import os
import json


def export_jsonl(boxes, image_path, output_dir, image_size=None):
    """
    Export annotations in JSON Lines format.
    
    Each line is a valid JSON object representing one annotation.
    
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
    output_path = os.path.join(output_dir, f"{base_name}.jsonl")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for idx, box in enumerate(boxes):
            x1, y1, x2, y2 = box['coords']
            label = box.get('label', '')
            
            record = {
                'id': idx,
                'image': os.path.basename(image_path),
                'label': label,
                'bbox': {
                    'x1': int(min(x1, x2)),
                    'y1': int(min(y1, y2)),
                    'x2': int(max(x1, x2)),
                    'y2': int(max(y1, y2)),
                    'width': int(abs(x2 - x1)),
                    'height': int(abs(y2 - y1))
                }
            }
            
            if image_size:
                record['image_size'] = {
                    'width': image_size[0],
                    'height': image_size[1]
                }
            
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    return output_path

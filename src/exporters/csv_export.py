"""CSV format exporter."""

import os
import csv


def export_csv(boxes, image_path, output_dir, image_size=None):
    """
    Export annotations in CSV format.
    
    Columns: image_path, label, x1, y1, x2, y2, width, height
    
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
    output_path = os.path.join(output_dir, f"{base_name}.csv")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'image_path', 'label', 'x1', 'y1', 'x2', 'y2', 
            'width', 'height', 'image_width', 'image_height'
        ])
        
        img_w = image_size[0] if image_size else ''
        img_h = image_size[1] if image_size else ''
        
        for box in boxes:
            x1, y1, x2, y2 = box['coords']
            label = box.get('label', '')
            
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            
            writer.writerow([
                os.path.basename(image_path),
                label,
                int(min(x1, x2)),
                int(min(y1, y2)),
                int(max(x1, x2)),
                int(max(y1, y2)),
                int(w),
                int(h),
                img_w,
                img_h
            ])
    
    return output_path

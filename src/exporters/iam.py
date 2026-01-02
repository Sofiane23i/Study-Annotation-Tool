"""IAM Handwriting Database format exporter."""

import os


def export_iam(boxes, image_path, output_dir, image_size=None):
    """
    Export annotations in IAM format.
    
    Format: id ok graylevel x y w h tag transcription
    
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
    output_path = os.path.join(output_dir, f"{base_name}.txt")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for idx, box in enumerate(boxes):
            x1, y1, x2, y2 = box['coords']
            label = box.get('label', '-')
            
            # Skip empty labels
            if label == '-' or not label.strip():
                continue
            
            x, y = int(min(x1, x2)), int(min(y1, y2))
            w, h = int(abs(x2 - x1)), int(abs(y2 - y1))
            
            # IAM format: id ok graylevel x y w h tag transcription
            f.write(f"{idx} ok 0 {x} {y} {w} {h} X {label}\n")
    
    return output_path

"""YOLO format exporter (YOLOv5/v8 compatible)."""

import os


def export_yolo(boxes, image_path, output_dir, image_size=None):
    """
    Export annotations in YOLO format.
    
    Format: class_id x_center y_center width height (normalized 0-1)
    
    Args:
        boxes: List of dicts with 'coords' and 'label'
        image_path: Source image path
        output_dir: Output directory
        image_size: (width, height) tuple - REQUIRED for YOLO
    
    Returns:
        Tuple of (labels_path, classes_path)
    """
    if not image_size or image_size[0] == 0 or image_size[1] == 0:
        raise ValueError("image_size (width, height) is required for YOLO format")
    
    os.makedirs(output_dir, exist_ok=True)
    
    img_w, img_h = image_size
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    # Build class mapping
    classes = {}
    class_id = 0
    
    for box in boxes:
        label = box.get('label', 'unknown')
        if label not in classes:
            classes[label] = class_id
            class_id += 1
    
    # Write labels file
    labels_path = os.path.join(output_dir, f"{base_name}.txt")
    
    with open(labels_path, 'w', encoding='utf-8') as f:
        for box in boxes:
            x1, y1, x2, y2 = box['coords']
            label = box.get('label', 'unknown')
            
            # Calculate normalized center and dimensions
            x_center = ((x1 + x2) / 2) / img_w
            y_center = ((y1 + y2) / 2) / img_h
            width = abs(x2 - x1) / img_w
            height = abs(y2 - y1) / img_h
            
            # Clamp values to [0, 1]
            x_center = max(0, min(1, x_center))
            y_center = max(0, min(1, y_center))
            width = max(0, min(1, width))
            height = max(0, min(1, height))
            
            class_idx = classes[label]
            f.write(f"{class_idx} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
    
    # Write classes file
    classes_path = os.path.join(output_dir, "classes.txt")
    with open(classes_path, 'w', encoding='utf-8') as f:
        for name, idx in sorted(classes.items(), key=lambda x: x[1]):
            f.write(f"{name}\n")
    
    # Write data.yaml for YOLOv5/v8
    yaml_path = os.path.join(output_dir, "data.yaml")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(f"# YOLO Dataset Configuration\n")
        f.write(f"path: {os.path.abspath(output_dir)}\n")
        f.write(f"train: images\n")
        f.write(f"val: images\n")
        f.write(f"nc: {len(classes)}\n")
        f.write(f"names: {list(classes.keys())}\n")
    
    return labels_path, classes_path

"""
Multi-format annotation exporters.
Supports: IAM, COCO, YOLO, VOC XML, CSV, JSONL
"""

from .iam import export_iam
from .coco import export_coco
from .yolo import export_yolo
from .voc import export_voc
from .csv_export import export_csv
from .jsonl import export_jsonl

__all__ = [
    'export_iam',
    'export_coco', 
    'export_yolo',
    'export_voc',
    'export_csv',
    'export_jsonl'
]


def export_annotations(boxes, image_path, output_dir, format='iam', image_size=None):
    """
    Export annotations in the specified format.
    
    Args:
        boxes: List of dicts with 'coords' (x1,y1,x2,y2) and 'label' keys
        image_path: Path to the source image
        output_dir: Directory to save exported files
        format: One of 'iam', 'coco', 'yolo', 'voc', 'csv', 'jsonl'
        image_size: Tuple (width, height) of the image
    
    Returns:
        Path to the exported file(s)
    """
    exporters = {
        'iam': export_iam,
        'coco': export_coco,
        'yolo': export_yolo,
        'voc': export_voc,
        'csv': export_csv,
        'jsonl': export_jsonl
    }
    
    if format not in exporters:
        raise ValueError(f"Unknown format: {format}. Supported: {list(exporters.keys())}")
    
    return exporters[format](boxes, image_path, output_dir, image_size)

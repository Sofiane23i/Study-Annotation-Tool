"""
Corpus Statistics Module
Analyzes annotation files to provide insights for HTR training data preparation.
"""

import os
import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional, Any
import glob


class CorpusAnalyzer:
    """Analyzes annotation data to extract corpus statistics."""
    
    def __init__(self):
        self.reset_stats()
    
    def reset_stats(self):
        """Reset all statistics."""
        self.total_annotations = 0
        self.annotation_type = "unknown"  # line, word, or character
        self.characters = Counter()
        self.words = Counter()
        self.bigrams = Counter()
        self.trigrams = Counter()
        self.sequence_lengths = []  # word/line lengths
        self.char_positions = defaultdict(list)  # char -> list of positions
        self.handwriting_styles = set()
        self.images = []
        self.raw_annotations = []
        
    def analyze_folder(self, folder_path: str) -> Dict[str, Any]:
        """Analyze all annotation files in a folder."""
        self.reset_stats()
        
        if not os.path.exists(folder_path):
            return {"error": f"Folder not found: {folder_path}"}
        
        # Detect annotation type and load data
        results = {
            "folder": folder_path,
            "annotation_type": "unknown",
            "total_annotations": 0,
            "total_images": 0,
            "character_stats": {},
            "word_stats": {},
            "sequence_stats": {},
            "ngram_stats": {},
            "style_stats": {},
        }
        
        # Check for different annotation formats
        if self._is_gan_annotation_folder(folder_path):
            results["annotation_type"] = "gan_generated"
            self._analyze_gan_annotations(folder_path)
        elif self._is_character_annotation_folder(folder_path):
            results["annotation_type"] = "character"
            self._analyze_character_annotations(folder_path)
        elif self._is_iam_annotation_folder(folder_path):
            results["annotation_type"] = "word/line"
            self._analyze_iam_annotations(folder_path)
        else:
            # Try generic JSON/COCO format
            self._analyze_generic_annotations(folder_path)
            results["annotation_type"] = self.annotation_type
        
        # Compile results
        results["total_annotations"] = self.total_annotations
        results["total_images"] = len(set(self.images))
        results["annotation_type"] = self.annotation_type
        
        results["character_stats"] = self._compute_character_stats()
        results["word_stats"] = self._compute_word_stats()
        results["sequence_stats"] = self._compute_sequence_stats()
        results["ngram_stats"] = self._compute_ngram_stats()
        results["style_stats"] = self._compute_style_stats()
        
        # Count crop images if folder contains crops subdirectory
        crop_dir = os.path.join(folder_path, "crops")
        if os.path.isdir(crop_dir):
            cnt = 0
            for root, dirs, files in os.walk(crop_dir):
                for f in files:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                        cnt += 1
            results['crop_count'] = cnt
        else:
            results['crop_count'] = 0
        
        return results
    
    def _is_gan_annotation_folder(self, folder_path: str) -> bool:
        """Check if folder contains GAN output annotations."""
        # Check both singular and plural naming conventions
        for name in ("annotation.txt", "annotations.txt"):
            ann_file = os.path.join(folder_path, name)
            if os.path.exists(ann_file):
                return True
        return False
    
    def _is_character_annotation_folder(self, folder_path: str) -> bool:
        """Check if folder contains character annotations."""
        ann_file = os.path.join(folder_path, "annotations.json")
        if os.path.exists(ann_file):
            try:
                with open(ann_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Check for character annotation structure
                if "categories" in data:
                    cats = data.get("categories", [])
                    if cats and len(cats[0].get("name", "")) <= 2:
                        return True
            except:
                pass
        return False
    
    def _is_iam_annotation_folder(self, folder_path: str) -> bool:
        """Check if folder contains IAM-format annotations."""
        # Look for .txt files with IAM format or output folders
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        for tf in txt_files:
            try:
                with open(tf, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue
                        # IAM format: index ok/err writer x y w h GT text
                        parts = line.split()
                        if len(parts) >= 8 and parts[1] in ('ok', 'err'):
                            return True
                        break  # only check the first non-comment line
            except:
                pass
        return False
    
    def _analyze_gan_annotations(self, folder_path: str):
        """Analyze GAN-generated annotation files."""
        self.annotation_type = "line"
        # Check both singular and plural naming conventions
        ann_file = os.path.join(folder_path, "annotation.txt")
        if not os.path.exists(ann_file):
            ann_file = os.path.join(folder_path, "annotations.txt")
        
        try:
            with open(ann_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 8:
                        # IAM format: index ok/err writer x y w h GT text
                        self.total_annotations += 1
                        writer = parts[2]  # writer/style ID
                        text = ' '.join(parts[8:]) if len(parts) > 8 else parts[7]
                        
                        self.handwriting_styles.add(writer)
                        self._process_text(text)
                        self.images.append(parts[0])
                    elif len(parts) >= 2:
                        # simple format: image_name followed by transcription
                        self.total_annotations += 1
                        writer = 'gan'
                        text = ' '.join(parts[1:])
                        self.handwriting_styles.add(writer)
                        self._process_text(text)
                        self.images.append(parts[0])
        except Exception as e:
            print(f"Error reading GAN annotations: {e}")
    
    def _analyze_character_annotations(self, folder_path: str):
        """Analyze character-level annotation files."""
        self.annotation_type = "character"
        ann_file = os.path.join(folder_path, "annotations.json")
        
        try:
            with open(ann_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Build category ID to name mapping
            cat_map = {}
            for cat in data.get("categories", []):
                cat_map[cat["id"]] = cat["name"]
            
            # Process annotations
            for ann in data.get("annotations", []):
                self.total_annotations += 1
                cat_id = ann.get("category_id", 0)
                char = cat_map.get(cat_id, "?")
                
                # Track character position (x coordinate from bbox)
                bbox = ann.get("bbox", [0, 0, 0, 0])
                x_pos = bbox[0]
                
                self.characters[char] += 1
                self.char_positions[char].append(x_pos)
                self.images.append(ann.get("image_id", 0))
            
            # For character annotations, also look at image files
            for img in data.get("images", []):
                if img.get("file_name"):
                    self.images.append(img["file_name"])
                    
        except Exception as e:
            print(f"Error reading character annotations: {e}")
    
    def _analyze_iam_annotations(self, folder_path: str):
        """Analyze IAM-format annotation files."""
        self.annotation_type = "word"
        
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        for tf in txt_files:
            try:
                with open(tf, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        parts = line.split()
                        if len(parts) >= 8:
                            self.total_annotations += 1
                            writer = parts[2]
                            text = ' '.join(parts[8:]) if len(parts) > 8 else parts[7]
                            
                            self.handwriting_styles.add(writer)
                            self._process_text(text)
                            self.images.append(parts[0])
            except Exception as e:
                print(f"Error reading file {tf}: {e}")
    
    def _analyze_generic_annotations(self, folder_path: str):
        """Analyze generic annotation formats (COCO JSON, JSONL, etc.)."""
        # Try JSON files
        json_files = glob.glob(os.path.join(folder_path, "*.json"))
        for jf in json_files:
            try:
                with open(jf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    # List of annotations
                    for item in data:
                        self.total_annotations += 1
                        text = item.get("text", item.get("transcription", ""))
                        self._process_text(text)
                        
                elif isinstance(data, dict):
                    # COCO-like format
                    if "annotations" in data:
                        for ann in data["annotations"]:
                            self.total_annotations += 1
                            text = ann.get("text", ann.get("transcription", ""))
                            self._process_text(text)
                            self.images.append(ann.get("image_id", 0))
                            
            except Exception as e:
                print(f"Error reading {jf}: {e}")
        
        # Try JSONL files
        jsonl_files = glob.glob(os.path.join(folder_path, "*.jsonl"))
        for jf in jsonl_files:
            try:
                with open(jf, 'r', encoding='utf-8') as f:
                    for line in f:
                        data = json.loads(line.strip())
                        self.total_annotations += 1
                        text = data.get("text", data.get("transcription", ""))
                        self._process_text(text)
            except Exception as e:
                print(f"Error reading {jf}: {e}")
        
        # Determine annotation type based on sequence lengths
        if self.sequence_lengths:
            avg_len = sum(self.sequence_lengths) / len(self.sequence_lengths)
            if avg_len < 3:
                self.annotation_type = "character"
            elif avg_len < 15:
                self.annotation_type = "word"
            else:
                self.annotation_type = "line"
    
    def _process_text(self, text: str):
        """Process a text string to extract statistics."""
        if not text:
            return
        
        text = text.strip()
        self.sequence_lengths.append(len(text))
        
        # Character frequency
        for i, char in enumerate(text):
            self.characters[char] += 1
            self.char_positions[char].append(i)
        
        # Word frequency (split by whitespace and punctuation)
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            self.words[word] += 1
        
        # N-grams (character level)
        for i in range(len(text) - 1):
            self.bigrams[text[i:i+2]] += 1
        for i in range(len(text) - 2):
            self.trigrams[text[i:i+3]] += 1
    
    def _compute_character_stats(self) -> Dict:
        """Compute character-level statistics."""
        if not self.characters:
            return {}
        
        total_chars = sum(self.characters.values())
        
        # Character frequency with positions
        char_data = []
        for char, count in self.characters.most_common():
            positions = self.char_positions.get(char, [])
            avg_pos = sum(positions) / len(positions) if positions else 0
            char_data.append({
                "char": char,
                "count": count,
                "frequency": count / total_chars if total_chars > 0 else 0,
                "avg_position": avg_pos,
                "positions": positions[:100]  # Limit stored positions
            })
        
        return {
            "total_characters": total_chars,
            "unique_characters": len(self.characters),
            "characters": char_data,
            "alphabet": sorted(self.characters.keys()),
        }
    
    def _compute_word_stats(self) -> Dict:
        """Compute word-level statistics."""
        if not self.words:
            return {}
        
        total_words = sum(self.words.values())
        
        return {
            "total_words": total_words,
            "unique_words": len(self.words),
            "vocabulary": [{"word": w, "count": c} for w, c in self.words.most_common(200)],
            "top_50_words": dict(self.words.most_common(50)),
        }
    
    def _compute_sequence_stats(self) -> Dict:
        """Compute sequence length statistics."""
        if not self.sequence_lengths:
            return {}
        
        lengths = self.sequence_lengths
        sorted_lengths = sorted(lengths)
        
        return {
            "total_sequences": len(lengths),
            "min_length": min(lengths),
            "max_length": max(lengths),
            "avg_length": sum(lengths) / len(lengths),
            "median_length": sorted_lengths[len(lengths) // 2],
            "length_distribution": dict(Counter(lengths).most_common(50)),
            "percentiles": {
                "10th": sorted_lengths[int(len(lengths) * 0.1)] if lengths else 0,
                "25th": sorted_lengths[int(len(lengths) * 0.25)] if lengths else 0,
                "50th": sorted_lengths[int(len(lengths) * 0.5)] if lengths else 0,
                "75th": sorted_lengths[int(len(lengths) * 0.75)] if lengths else 0,
                "90th": sorted_lengths[int(len(lengths) * 0.9)] if lengths else 0,
            }
        }
    
    def _compute_ngram_stats(self) -> Dict:
        """Compute n-gram statistics."""
        return {
            "bigrams": {
                "total": sum(self.bigrams.values()),
                "unique": len(self.bigrams),
                "top_30": dict(self.bigrams.most_common(30)),
            },
            "trigrams": {
                "total": sum(self.trigrams.values()),
                "unique": len(self.trigrams),
                "top_30": dict(self.trigrams.most_common(30)),
            }
        }
    
    def _compute_style_stats(self) -> Dict:
        """Compute handwriting style statistics."""
        return {
            "total_styles": len(self.handwriting_styles),
            "styles": list(self.handwriting_styles),
        }


def get_annotation_paths() -> List[Dict[str, str]]:
    """Get list of known annotation folder paths."""
    base_dir = os.path.dirname(__file__)
    
    paths = []
    
    # GAN output annotations
    gan_path = os.path.join(base_dir, "gan_output_data")
    if os.path.exists(gan_path):
        paths.append({
            "name": "GAN Generated",
            "path": gan_path,
            "icon": "✍️",
            "description": "Synthetic handwriting from GAN model"
        })
    
    # Character annotations
    char_path = os.path.join(base_dir, "character annotation")
    if os.path.exists(char_path):
        paths.append({
            "name": "Character Annotations",
            "path": char_path,
            "icon": "🔤",
            "description": "Character-level bounding box annotations"
        })
    
    # Look for loaded image annotations (output folder pattern)
    output_dirs = [
        os.path.join(base_dir, "output"),
        os.path.join(base_dir, "annotations"),
        os.path.join(base_dir, "data"),
    ]
    
    for out_dir in output_dirs:
        if os.path.exists(out_dir):
            paths.append({
                "name": os.path.basename(out_dir).title(),
                "path": out_dir,
                "icon": "📁",
                "description": f"Annotations in {out_dir}"
            })
    
    # Look for directories containing .txt or .json annotation files
    # in the parent directory (common pattern for datasets)
    parent_dir = os.path.dirname(base_dir)
    for folder_name in ['labels', 'gt', 'ground_truth', 'transcriptions']:
        folder_path = os.path.join(parent_dir, folder_name)
        if os.path.exists(folder_path):
            paths.append({
                "name": folder_name.replace('_', ' ').title(),
                "path": folder_path,
                "icon": "📑",
                "description": f"External annotations in {folder_name}"
            })
    
    # Also check for recently used paths from state
    try:
        import state as S
        if hasattr(S, 'pathDirectory') and S.pathDirectory:
            # Check if there's an annotations subfolder
            ann_subdir = os.path.join(S.pathDirectory, 'annotations')
            if os.path.exists(ann_subdir) and ann_subdir not in [p['path'] for p in paths]:
                paths.append({
                    "name": "Current Session",
                    "path": ann_subdir,
                    "icon": "📂",
                    "description": f"Annotations from loaded images"
                })
    except ImportError:
        pass
    
    return paths


def format_stats_summary(stats: Dict) -> str:
    """Format statistics as a human-readable summary."""
    if "error" in stats:
        return f"Error: {stats['error']}"
    
    lines = []
    lines.append(f"📊 Corpus Statistics Summary")
    lines.append(f"{'='*40}")
    lines.append(f"📂 Folder: {stats.get('folder', 'Unknown')}")
    lines.append(f"📋 Type: {stats.get('annotation_type', 'Unknown').title()}")
    lines.append(f"📝 Total annotations: {stats.get('total_annotations', 0):,}")
    lines.append(f"🖼️ Total images: {stats.get('total_images', 0):,}")
    lines.append("")
    
    # Character stats
    char_stats = stats.get("character_stats", {})
    if char_stats:
        lines.append(f"🔤 Characters:")
        lines.append(f"   Total: {char_stats.get('total_characters', 0):,}")
        lines.append(f"   Unique: {char_stats.get('unique_characters', 0)}")
        alphabet = char_stats.get('alphabet', [])
        if alphabet:
            lines.append(f"   Alphabet: {' '.join(alphabet[:50])}")
        lines.append("")
    
    # Word stats
    word_stats = stats.get("word_stats", {})
    if word_stats:
        lines.append(f"📖 Words:")
        lines.append(f"   Total: {word_stats.get('total_words', 0):,}")
        lines.append(f"   Vocabulary size: {word_stats.get('unique_words', 0)}")
        lines.append("")
    
    # Sequence stats
    seq_stats = stats.get("sequence_stats", {})
    if seq_stats:
        lines.append(f"📏 Sequence Lengths:")
        lines.append(f"   Min: {seq_stats.get('min_length', 0)}")
        lines.append(f"   Max: {seq_stats.get('max_length', 0)}")
        lines.append(f"   Average: {seq_stats.get('avg_length', 0):.1f}")
        lines.append("")
    
    # Style stats
    style_stats = stats.get("style_stats", {})
    if style_stats and style_stats.get("total_styles", 0) > 0:
        lines.append(f"✍️ Handwriting Styles: {style_stats.get('total_styles', 0)}")
        lines.append("")
    
    return "\n".join(lines)


# For testing
if __name__ == "__main__":
    analyzer = CorpusAnalyzer()
    
    # Test with GAN output folder
    test_path = os.path.join(os.path.dirname(__file__), "gan_output_data")
    if os.path.exists(test_path):
        results = analyzer.analyze_folder(test_path)
        print(format_stats_summary(results))

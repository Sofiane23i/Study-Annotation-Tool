"""
Step 4 – Model Recommendation & Dataset Guidance
Maps dataset characteristics to suitable architectures.
Provides augmentation and refinement recommendations.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List
import webbrowser


# Architecture database (expanded from the existing home_panel)
ARCHITECTURE_DB = {
    "character_detection": {
        "title": "🔍 Character Detection",
        "desc": "Object detection models for character-level bounding box detection",
        "applicable_types": ["character", "raw"],
        "models": [
            {
                "name": "YOLOv8",
                "paper": "https://arxiv.org/abs/2305.09972",
                "github": "https://github.com/ultralytics/ultralytics",
                "desc": "State-of-the-art real-time detector. Excellent for character-level detection.",
                "pros": ["Fast inference", "Easy training", "Pre-trained weights"],
                "dataset_reqs": "Character bounding box annotations (COCO/YOLO format)",
                "min_samples": 200,
            },
            {
                "name": "Faster R-CNN",
                "paper": "https://arxiv.org/abs/1506.01497",
                "github": "https://github.com/facebookresearch/detectron2",
                "desc": "Two-stage detector with high accuracy for character detection.",
                "pros": ["High precision", "Well-established"],
                "dataset_reqs": "Bounding box + class labels (COCO format)",
                "min_samples": 500,
            },
            {
                "name": "DETR",
                "paper": "https://arxiv.org/abs/2005.12872",
                "github": "https://github.com/facebookresearch/detr",
                "desc": "End-to-end transformer detector. No NMS needed.",
                "pros": ["End-to-end", "Set-based prediction"],
                "dataset_reqs": "COCO-format annotations",
                "min_samples": 1000,
            },
        ],
    },
    "word_level": {
        "title": "📝 Word-Level Recognition",
        "desc": "Best for recognizing individual words or short text segments",
        "applicable_types": ["word", "word/line", "preannotated", "external", "gan_generated"],
        "models": [
            {
                "name": "CRNN (CNN + RNN + CTC)",
                "paper": "https://arxiv.org/abs/1507.05717",
                "github": "https://github.com/bgshih/crnn",
                "desc": "Classic architecture combining CNN + bidirectional LSTM + CTC loss.",
                "pros": ["Fast training", "Good baseline", "Well-documented"],
                "dataset_reqs": "Word images + text transcriptions",
                "min_samples": 300,
            },
            {
                "name": "Attention Seq2Seq",
                "paper": "https://arxiv.org/abs/1603.03101",
                "github": "https://github.com/emedvedev/attention-ocr",
                "desc": "Encoder-decoder with attention. Handles variable-length outputs.",
                "pros": ["Handles irregular text", "Interpretable attention maps"],
                "dataset_reqs": "Word images + text labels",
                "min_samples": 500,
            },
            {
                "name": "STN + CRNN",
                "paper": "https://arxiv.org/abs/1603.03915",
                "github": "https://github.com/clovaai/deep-text-recognition-benchmark",
                "desc": "Spatial Transformer for geometric correction before CRNN.",
                "pros": ["Handles distortion", "Robust to rotation"],
                "dataset_reqs": "Word images + transcriptions",
                "min_samples": 500,
            },
        ],
    },
    "line_level": {
        "title": "📄 Line-Level Recognition",
        "desc": "For recognizing full text lines — most common for HTR",
        "applicable_types": ["line", "word/line", "preannotated", "external", "gan_generated", "raw"],
        "models": [
            {
                "name": "TrOCR",
                "paper": "https://arxiv.org/abs/2109.10282",
                "github": "https://github.com/microsoft/unilm/tree/master/trocr",
                "desc": "Transformer-based OCR using pre-trained ViT + GPT-2/RoBERTa.",
                "pros": ["State-of-the-art", "Pre-trained models available"],
                "dataset_reqs": "Line images + text transcriptions",
                "min_samples": 200,
            },
            {
                "name": "PyLaia",
                "paper": "https://arxiv.org/abs/1604.01949",
                "github": "https://github.com/jpuigcerver/PyLaia",
                "desc": "Efficient line OCR. Widely used for historical documents.",
                "pros": ["Efficient", "Good for historical HTR", "Easy to train"],
                "dataset_reqs": "Line images + text",
                "min_samples": 300,
            },
            {
                "name": "Start-Follow-Read",
                "paper": "https://arxiv.org/abs/1812.07688",
                "github": "https://github.com/cwig/start_follow_read",
                "desc": "Full page HTR without explicit segmentation.",
                "pros": ["End-to-end", "No line segmentation required"],
                "dataset_reqs": "Full page images + transcriptions",
                "min_samples": 500,
            },
        ],
    },
    "page_level": {
        "title": "📰 Page / Document Level",
        "desc": "End-to-end document understanding without segmentation",
        "applicable_types": ["line", "word/line", "preannotated", "raw"],
        "models": [
            {
                "name": "Donut",
                "paper": "https://arxiv.org/abs/2111.15664",
                "github": "https://github.com/clovaai/donut",
                "desc": "OCR-free document understanding using image-to-text generation.",
                "pros": ["No OCR pipeline needed", "Handles complex layouts"],
                "dataset_reqs": "Document images + structured text",
                "min_samples": 1000,
            },
            {
                "name": "LayoutLMv3",
                "paper": "https://arxiv.org/abs/2204.08387",
                "github": "https://github.com/microsoft/unilm/tree/master/layoutlmv3",
                "desc": "Multi-modal model combining text, layout, and image.",
                "pros": ["Multi-modal", "Pre-trained", "Layout-aware"],
                "dataset_reqs": "Document images + layout + text",
                "min_samples": 500,
            },
        ],
    },
    "synthetic_data": {
        "title": "🎨 Synthetic Data Generation",
        "desc": "For creating synthetic training data and augmentation",
        "applicable_types": ["synthetic", "raw", "gan_generated"],
        "models": [
            {
                "name": "Handwriting Synthesis (Graves)",
                "paper": "https://arxiv.org/abs/1308.0850",
                "github": "https://github.com/sjvasquez/handwriting-synthesis",
                "desc": "LSTM-based handwriting generation for realistic samples.",
                "pros": ["Style transfer", "Unlimited synthetic samples"],
                "dataset_reqs": "Text input for generation",
                "min_samples": 0,
            },
            {
                "name": "GANwriting",
                "paper": "https://arxiv.org/abs/2003.02567",
                "github": "https://github.com/omni-us/research-GANwriting",
                "desc": "GAN-based style-conditioned handwriting synthesis.",
                "pros": ["High-quality synthesis", "Writer style control"],
                "dataset_reqs": "Reference style samples",
                "min_samples": 100,
            },
            {
                "name": "ScrabbleGAN",
                "paper": "https://arxiv.org/abs/2003.10557",
                "github": "https://github.com/AmmieQi/ScrabbleGAN",
                "desc": "Semi-supervised varying-length handwritten text generation.",
                "pros": ["Semi-supervised", "Variable length output"],
                "dataset_reqs": "Mix of labeled and unlabeled data",
                "min_samples": 100,
            },
        ],
    },
}

AUGMENTATION_DB = [
    {
        "name": "Elastic Distortion",
        "desc": "Simulate handwriting variation by warping the image.",
        "when": "Always recommended for HTR datasets.",
        "impact": "High — improves model robustness to writing styles.",
    },
    {
        "name": "Random Rotation (±5°)",
        "desc": "Slight rotations to handle scanner/camera misalignment.",
        "when": "Recommended for scanned documents.",
        "impact": "Medium — helps with slightly rotated inputs.",
    },
    {
        "name": "Gaussian Noise",
        "desc": "Add random noise to simulate scanning artifacts.",
        "when": "Recommended for clean/synthetic images to improve robustness.",
        "impact": "Medium.",
    },
    {
        "name": "Brightness / Contrast Variation",
        "desc": "Randomly adjust brightness and contrast.",
        "when": "Always recommended.",
        "impact": "Medium — helps with variable lighting conditions.",
    },
    {
        "name": "Horizontal Stretch (±10%)",
        "desc": "Slight horizontal scaling to simulate handwriting width variation.",
        "when": "Recommended for word-level and line-level HTR.",
        "impact": "Medium.",
    },
    {
        "name": "Morphological Erosion/Dilation",
        "desc": "Thin or thicken strokes to simulate pen pressure variation.",
        "when": "Recommended when stroke variation is limited.",
        "impact": "High for character recognition.",
    },
    {
        "name": "GAN Synthesis (Built-in)",
        "desc": "Generate synthetic handwriting using the built-in GAN module.",
        "when": "Strongly recommended for datasets < 500 samples.",
        "impact": "Very High — can multiply effective dataset size.",
    },
]


class RecommendationPanel(tk.Frame):
    """Model recommendation and dataset guidance panel."""

    def __init__(self, parent: tk.Widget, colors: Dict[str, str],
                 dataset_ctx: Dict[str, Any]):
        super().__init__(parent, bg=colors["bg_dark"])
        self.colors = colors
        self.ctx = dataset_ctx
        self._build_ui()
        self.after(300, self._generate_recommendations)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        hdr = tk.Frame(self, bg=self.colors["bg_section"], pady=12, padx=15)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🤖  Step 5 — Model Recommendation & Dataset Guidance",
                 font=("Segoe UI", 15, "bold"),
                 bg=self.colors["bg_section"], fg=self.colors["text_light"]).pack(side=tk.LEFT)

        tk.Button(hdr, text="🔄 Refresh", command=self._generate_recommendations,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 9, "bold"), relief=tk.FLAT,
                  padx=10, pady=4, cursor="hand2").pack(side=tk.RIGHT)

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab: Model Suggestions
        self.tab_models = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_models, text="🏗️ Model Suggestions")

        # Tab: Augmentation Guidance
        self.tab_augment = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_augment, text="📈 Augmentation Guidance")

        # Tab: Dataset Quality
        self.tab_quality = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_quality, text="✅ Dataset Quality Score")

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _generate_recommendations(self):
        stats = self.ctx.get("stats", {})
        ds_type = self.ctx.get("type", "raw")
        ann_type = stats.get("annotation_type", "unknown")
        total = stats.get("total_annotations", len(self.ctx.get("images", [])))

        self._populate_models(ds_type, ann_type, total)
        self._populate_augmentations(ds_type, total, stats)
        self._populate_quality(stats, total)

    def _populate_models(self, ds_type, ann_type, total):
        for w in self.tab_models.winfo_children():
            w.destroy()

        # Scrollable
        canvas = tk.Canvas(self.tab_models, bg=self.colors["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_models, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.colors["bg_dark"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Header badge
        badge = tk.Label(scroll_frame,
                         text=f"📊 Dataset: {ds_type} | Annotation: {ann_type} | Samples: {total:,}",
                         font=("Segoe UI", 11, "bold"),
                         bg=self.colors["accent"], fg="white",
                         padx=15, pady=6)
        badge.pack(fill=tk.X, padx=10, pady=(10, 5))

        shown = 0
        for cat_key, cat_data in ARCHITECTURE_DB.items():
            # Check applicability
            applicable = cat_data["applicable_types"]
            if ds_type in applicable or ann_type in applicable:
                section = tk.LabelFrame(scroll_frame, text=f' {cat_data["title"]} ',
                                         font=("Segoe UI", 11, "bold"),
                                         bg=self.colors["bg_section"],
                                         fg=self.colors["text_light"])
                section.pack(fill=tk.X, padx=10, pady=5)
                tk.Label(section, text=cat_data["desc"],
                         font=("Segoe UI", 9, "italic"),
                         bg=self.colors["bg_section"],
                         fg=self.colors["text_muted"]).pack(anchor="w", padx=10, pady=(5, 8))

                for model in cat_data["models"]:
                    suitable = total >= model.get("min_samples", 0)
                    self._model_card(section, model, suitable)
                    shown += 1

        if shown == 0:
            tk.Label(scroll_frame,
                     text="No specific model recommendations for this dataset type.\n"
                          "Try loading annotations or changing dataset type.",
                     font=("Segoe UI", 11),
                     bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"]).pack(expand=True, pady=40)

    def _model_card(self, parent, model: Dict, suitable: bool):
        card = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=1)
        card.pack(fill=tk.X, padx=10, pady=4)

        # Header
        top = tk.Frame(card, bg="white")
        top.pack(fill=tk.X, padx=10, pady=(8, 4))

        suitability_icon = "✅" if suitable else "⚠️"
        tk.Label(top, text=f"{suitability_icon} {model['name']}",
                 font=("Segoe UI", 11, "bold"),
                 bg="white", fg=self.colors["text_light"]).pack(side=tk.LEFT)

        # Links
        links_frame = tk.Frame(top, bg="white")
        links_frame.pack(side=tk.RIGHT)

        paper_btn = tk.Label(links_frame, text="📖 Paper",
                              font=("Segoe UI", 9, "underline"),
                              bg="white", fg="#2980b9", cursor="hand2")
        paper_btn.pack(side=tk.LEFT, padx=5)
        paper_btn.bind("<Button-1>", lambda e, u=model["paper"]: webbrowser.open(u))

        gh_btn = tk.Label(links_frame, text="💻 GitHub",
                          font=("Segoe UI", 9, "underline"),
                          bg="white", fg="#27ae60", cursor="hand2")
        gh_btn.pack(side=tk.LEFT, padx=5)
        gh_btn.bind("<Button-1>", lambda e, u=model["github"]: webbrowser.open(u))

        # Description
        tk.Label(card, text=model["desc"], font=("Segoe UI", 10),
                 bg="white", fg=self.colors["text_light"],
                 wraplength=600, justify=tk.LEFT).pack(anchor="w", padx=10, pady=2)

        # Pros + dataset requirements
        bottom = tk.Frame(card, bg="white")
        bottom.pack(fill=tk.X, padx=10, pady=(2, 8))
        pros_text = " • ".join(model.get("pros", []))
        tk.Label(bottom, text=f"✅ {pros_text}",
                 font=("Segoe UI", 9), bg="white",
                 fg="#4caf50").pack(anchor="w")
        tk.Label(bottom, text=f"📋 Requires: {model.get('dataset_reqs', '—')}",
                 font=("Segoe UI", 9), bg="white",
                 fg=self.colors["text_muted"]).pack(anchor="w")
        if not suitable:
            tk.Label(bottom,
                     text=f"⚠️ Dataset may be too small (need ≥{model.get('min_samples', 0)} samples)",
                     font=("Segoe UI", 9, "italic"), bg="white",
                     fg="#ff9800").pack(anchor="w")

    def _populate_augmentations(self, ds_type, total, stats):
        for w in self.tab_augment.winfo_children():
            w.destroy()

        tk.Label(self.tab_augment,
                 text="📈 Recommended Data Augmentation Strategies",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["bg_dark"],
                 fg=self.colors["text_light"]).pack(pady=10)

        # Multiplier suggestion
        if total == 0:
            mult = "N/A (no data)"
        elif total < 100:
            mult = "10–20× augmentation strongly recommended"
        elif total < 500:
            mult = "5–10× augmentation recommended"
        elif total < 2000:
            mult = "2–5× augmentation suggested"
        else:
            mult = "1–2× light augmentation (optional)"

        tk.Label(self.tab_augment,
                 text=f"💡 Suggested augmentation multiplier: {mult}",
                 font=("Segoe UI", 11, "bold"),
                 bg=self.colors["accent"], fg="white",
                 padx=15, pady=6).pack(fill=tk.X, padx=10, pady=5)

        # Augmentation cards
        for aug in AUGMENTATION_DB:
            card = tk.Frame(self.tab_augment, bg="white", relief=tk.RAISED, bd=1)
            card.pack(fill=tk.X, padx=10, pady=3)
            inner = tk.Frame(card, bg="white", padx=10, pady=8)
            inner.pack(fill=tk.X)
            tk.Label(inner, text=f"🔧 {aug['name']}", font=("Segoe UI", 10, "bold"),
                     bg="white", fg=self.colors["text_light"]).pack(anchor="w")
            tk.Label(inner, text=aug["desc"], font=("Segoe UI", 9),
                     bg="white", fg=self.colors["text_muted"],
                     wraplength=600, justify=tk.LEFT).pack(anchor="w")
            tk.Label(inner, text=f"When: {aug['when']}  |  Impact: {aug['impact']}",
                     font=("Segoe UI", 9, "italic"),
                     bg="white", fg=self.colors["text_muted"]).pack(anchor="w")

    def _populate_quality(self, stats, total):
        for w in self.tab_quality.winfo_children():
            w.destroy()

        tk.Label(self.tab_quality,
                 text="✅ Dataset Quality Assessment",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["bg_dark"],
                 fg=self.colors["text_light"]).pack(pady=10)

        # Compute quality score (0-100)
        score = 0
        criteria = []

        # Size
        if total >= 5000:
            score += 25
            criteria.append(("✅ Dataset size", f"{total:,} samples (excellent)", 25))
        elif total >= 1000:
            score += 20
            criteria.append(("✅ Dataset size", f"{total:,} samples (good)", 20))
        elif total >= 100:
            score += 10
            criteria.append(("⚠️ Dataset size", f"{total:,} samples (small)", 10))
        elif total > 0:
            score += 5
            criteria.append(("❌ Dataset size", f"{total:,} samples (very small)", 5))
        else:
            criteria.append(("❌ Dataset size", "No data loaded", 0))

        # Annotations
        has_ann = stats.get("has_annotations", False)
        if has_ann:
            score += 20
            criteria.append(("✅ Annotations", "Present", 20))
        else:
            criteria.append(("⚠️ Annotations", "Missing — annotate to improve", 0))

        # Character diversity
        char_stats = stats.get("character_stats", {})
        unique_chars = char_stats.get("unique_characters", 0)
        if unique_chars > 50:
            score += 15
            criteria.append(("✅ Character diversity", f"{unique_chars} unique characters", 15))
        elif unique_chars > 20:
            score += 10
            criteria.append(("⚠️ Character diversity", f"{unique_chars} unique characters", 10))
        elif unique_chars > 0:
            score += 5
            criteria.append(("⚠️ Character diversity", f"{unique_chars} characters (low)", 5))

        # Writer diversity
        style_stats = stats.get("style_stats", {})
        writers = style_stats.get("total_styles", 0)
        if writers > 10:
            score += 15
            criteria.append(("✅ Writer diversity", f"{writers} writers", 15))
        elif writers > 1:
            score += 10
            criteria.append(("⚠️ Writer diversity", f"{writers} writers", 10))
        elif writers == 1:
            score += 5
            criteria.append(("⚠️ Writer diversity", "Single writer", 5))

        # Split configured
        if self.ctx.get("split_result"):
            score += 10
            criteria.append(("✅ Data split", "Configured", 10))
        else:
            criteria.append(("ℹ️ Data split", "Not yet configured", 0))

        # Vocabulary
        word_stats = stats.get("word_stats", {})
        vocab = word_stats.get("unique_words", 0)
        if vocab > 500:
            score += 15
            criteria.append(("✅ Vocabulary", f"{vocab:,} unique words", 15))
        elif vocab > 100:
            score += 10
            criteria.append(("⚠️ Vocabulary", f"{vocab:,} unique words", 10))
        elif vocab > 0:
            score += 5
            criteria.append(("⚠️ Vocabulary", f"{vocab} words (limited)", 5))

        score = min(score, 100)

        # Score display
        score_color = "#4caf50" if score >= 70 else "#ff9800" if score >= 40 else "#f44336"
        score_frame = tk.Frame(self.tab_quality, bg=self.colors["bg_section"])
        score_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(score_frame, text=f"Quality Score: {score}/100",
                 font=("Segoe UI", 22, "bold"),
                 bg=self.colors["bg_section"], fg=score_color).pack(pady=15)

        # Progress bar
        from tkinter import ttk
        style = ttk.Style()
        style.configure("Quality.Horizontal.TProgressbar",
                        troughcolor=self.colors["bg_dark"],
                        background=score_color)
        pb = ttk.Progressbar(score_frame, style="Quality.Horizontal.TProgressbar",
                              maximum=100, value=score, length=400)
        pb.pack(pady=(0, 15))

        # Criteria details
        for icon_text, desc, pts in criteria:
            row = tk.Frame(self.tab_quality, bg="white", relief=tk.RAISED, bd=1)
            row.pack(fill=tk.X, padx=10, pady=2)
            inner = tk.Frame(row, bg="white", padx=10, pady=6)
            inner.pack(fill=tk.X)
            tk.Label(inner, text=icon_text, font=("Segoe UI", 10, "bold"),
                     bg="white", fg=self.colors["text_light"]).pack(side=tk.LEFT)
            tk.Label(inner, text=desc, font=("Segoe UI", 10),
                     bg="white", fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=10)
            tk.Label(inner, text=f"+{pts}", font=("Segoe UI", 10, "bold"),
                     bg="white", fg=score_color).pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    def refresh(self, ctx):
        self.ctx = ctx
        self._generate_recommendations()

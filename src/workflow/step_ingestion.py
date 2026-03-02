"""
Step 1 – Dataset Ingestion Panel
Supports four ingestion modes:
  A) Upload raw images (scanner/camera)
  B) Load synthetic / generated images
  C) Upload pre-annotated dataset (images + annotations bundled)
  D) Load images with external annotation files
Also provides a dataset preview & integrity check.
"""

import os
import glob
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, Callable, List
from PIL import Image, ImageTk
import threading

import state as S


class DatasetFolderDialog(tk.Toplevel):
    """Dialog for selecting folder structure when loading a dataset."""

    def __init__(self, parent, colors):
        super().__init__(parent)
        self.title("Load Dataset — Folder Structure")
        self.geometry("500x230")
        self.resizable(False, False)
        self.configure(bg=colors["bg_dark"])
        self.colors = colors
        self.result = None
        self.transient(parent)
        self.grab_set()

        # --- Header ---
        hdr = tk.Frame(self, bg=colors["bg_section"], pady=10, padx=14)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="📂  Load Dataset",
                 font=("Segoe UI", 13, "bold"),
                 bg=colors["bg_section"], fg=colors["text_light"]).pack(anchor="w")
        tk.Label(hdr, text="Choose how your image folder is organised, then pick a folder.",
                 font=("Segoe UI", 9), bg=colors["bg_section"],
                 fg=colors["text_muted"]).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(self, bg=colors["bg_dark"], padx=14, pady=10)
        body.pack(fill=tk.BOTH, expand=True)

        # --- Folder Structure ---
        struct_frame = tk.LabelFrame(body, text=" 📁 Folder Structure ",
                                      font=("Segoe UI", 10, "bold"),
                                      bg=colors["bg_section"],
                                      fg=colors["text_light"],
                                      relief=tk.GROOVE, bd=1, padx=10, pady=8)
        struct_frame.pack(fill=tk.X, pady=(0, 10))

        self.struct_var = tk.StringVar(value="flat")
        structures = [
            ("flat", "Flat folder",
             "All images in a single folder"),
            ("subfolders", "Sub-folder structure (IAM-style)",
             "Images organised in nested sub-folders (e.g. writer/form/…)"),
        ]
        for val, label, desc in structures:
            row = tk.Frame(struct_frame, bg=colors["bg_section"])
            row.pack(fill=tk.X, pady=1)
            tk.Radiobutton(row, text=label, variable=self.struct_var, value=val,
                           font=("Segoe UI", 9, "bold"),
                           bg=colors["bg_section"], fg=colors["text_light"],
                           activebackground=colors["bg_section"],
                           selectcolor=colors["bg_dark"]).pack(side=tk.LEFT)
            tk.Label(row, text=f"  — {desc}", font=("Segoe UI", 8),
                     bg=colors["bg_section"],
                     fg=colors["text_muted"]).pack(side=tk.LEFT)

        # --- Buttons ---
        btn_row = tk.Frame(body, bg=colors["bg_dark"])
        btn_row.pack(fill=tk.X, pady=(6, 0))

        tk.Button(btn_row, text="Cancel", command=self._cancel,
                  font=("Segoe UI", 9), bg="#e0e0e0", fg="#333",
                  relief=tk.FLAT, padx=16, pady=5,
                  cursor="hand2").pack(side=tk.RIGHT, padx=(6, 0))
        tk.Button(btn_row, text="📂 Select Folder & Load",
                  command=self._ok,
                  font=("Segoe UI", 10, "bold"),
                  bg=colors["accent"], fg="white",
                  activebackground=colors.get("accent_hover", "#005fc5"),
                  relief=tk.FLAT, padx=16, pady=5,
                  cursor="hand2").pack(side=tk.RIGHT)

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.update_idletasks()
        pw = parent.winfo_width(); ph = parent.winfo_height()
        px = parent.winfo_rootx(); py = parent.winfo_rooty()
        w = self.winfo_width(); h = self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _ok(self):
        self.result = {"folder_structure": self.struct_var.get()}
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class AnnotationFormatDialog(tk.Toplevel):
    """Dialog for selecting annotation format when loading an annotation file."""

    def __init__(self, parent, colors):
        super().__init__(parent)
        self.title("Load Annotation — Format")
        self.geometry("520x340")
        self.resizable(False, False)
        self.configure(bg=colors["bg_dark"])
        self.colors = colors
        self.result = None
        self.transient(parent)
        self.grab_set()

        # --- Header ---
        hdr = tk.Frame(self, bg=colors["bg_section"], pady=10, padx=14)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="📝  Load Annotation",
                 font=("Segoe UI", 13, "bold"),
                 bg=colors["bg_section"], fg=colors["text_light"]).pack(anchor="w")
        tk.Label(hdr, text="Choose the annotation format, then select the file.",
                 font=("Segoe UI", 9), bg=colors["bg_section"],
                 fg=colors["text_muted"]).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(self, bg=colors["bg_dark"], padx=14, pady=10)
        body.pack(fill=tk.BOTH, expand=True)

        # --- Annotation Format ---
        fmt_frame = tk.LabelFrame(body, text=" 📝 Annotation Format ",
                                   font=("Segoe UI", 10, "bold"),
                                   bg=colors["bg_section"],
                                   fg=colors["text_light"],
                                   relief=tk.GROOVE, bd=1, padx=10, pady=8)
        fmt_frame.pack(fill=tk.X, pady=(0, 10))

        self.fmt_var = tk.StringVar(value="iam")
        formats = [
            ("iam", "IAM Format",
             "word/line-level .txt (image ok writer x y w h text)"),
            ("coco", "COCO JSON (Object Detection)",
             "Standard COCO .json with images, annotations, categories"),
            ("yolo", "YOLO (Object Detection)",
             ".txt per image — class xc yc w h (normalised)"),
            ("voc", "Pascal VOC XML (Object Detection)",
             "One .xml per image with <object><bndbox> elements"),
            ("auto", "Auto-Detect",
             "Let the tool guess the format from the files found"),
        ]
        for val, label, desc in formats:
            row = tk.Frame(fmt_frame, bg=colors["bg_section"])
            row.pack(fill=tk.X, pady=1)
            tk.Radiobutton(row, text=label, variable=self.fmt_var, value=val,
                           font=("Segoe UI", 9, "bold"),
                           bg=colors["bg_section"], fg=colors["text_light"],
                           activebackground=colors["bg_section"],
                           selectcolor=colors["bg_dark"]).pack(side=tk.LEFT)
            tk.Label(row, text=f"  — {desc}", font=("Segoe UI", 8),
                     bg=colors["bg_section"],
                     fg=colors["text_muted"]).pack(side=tk.LEFT)

        # --- Buttons ---
        btn_row = tk.Frame(body, bg=colors["bg_dark"])
        btn_row.pack(fill=tk.X, pady=(6, 0))

        tk.Button(btn_row, text="Cancel", command=self._cancel,
                  font=("Segoe UI", 9), bg="#e0e0e0", fg="#333",
                  relief=tk.FLAT, padx=16, pady=5,
                  cursor="hand2").pack(side=tk.RIGHT, padx=(6, 0))
        tk.Button(btn_row, text="📝 Select File & Load",
                  command=self._ok,
                  font=("Segoe UI", 10, "bold"),
                  bg="#5c6bc0", fg="white",
                  activebackground="#3f51b5",
                  relief=tk.FLAT, padx=16, pady=5,
                  cursor="hand2").pack(side=tk.RIGHT)

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.update_idletasks()
        pw = parent.winfo_width(); ph = parent.winfo_height()
        px = parent.winfo_rootx(); py = parent.winfo_rooty()
        w = self.winfo_width(); h = self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _ok(self):
        self.result = {"annotation_format": self.fmt_var.get()}
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class IngestionPanel(tk.Frame):
    """Dataset ingestion with four loading options and preview."""

    def __init__(self, parent: tk.Widget, colors: Dict[str, str],
                 dataset_ctx: Dict[str, Any],
                 on_loaded: Callable = None):
        super().__init__(parent, bg=colors["bg_dark"])
        self.colors = colors
        self.ctx = dataset_ctx
        self.on_loaded = on_loaded

        self.preview_photos = []  # keep references to prevent GC

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=self.colors["bg_section"], pady=12, padx=15)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="📥  Step 1 — Dataset Ingestion",
                 font=("Segoe UI", 15, "bold"),
                 bg=self.colors["bg_section"], fg=self.colors["text_light"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Choose how to load your dataset",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_section"], fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=15)

        # Two-column layout: options on left, preview on right
        body = tk.Frame(self, bg=self.colors["bg_dark"])
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- LEFT: Ingestion options + tool controls (scrollable) ---
        left_outer = tk.Frame(body, bg=self.colors["bg_dark"], width=260)
        left_outer.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_outer.pack_propagate(False)

        # Canvas + scrollbar for left column
        left_canvas = tk.Canvas(left_outer, bg=self.colors["bg_dark"],
                                highlightthickness=0, width=240)
        left_scroll = tk.Scrollbar(left_outer, orient=tk.VERTICAL,
                                   command=left_canvas.yview)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_canvas.configure(yscrollcommand=left_scroll.set)

        left = tk.Frame(left_canvas, bg=self.colors["bg_dark"])
        left_canvas.create_window((0, 0), window=left, anchor="nw")

        def _on_left_configure(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        left.bind("<Configure>", _on_left_configure)

        # Mouse-wheel scroll support
        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        left_canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")

        # ---- Unified load dataset card ----
        self._build_load_dataset_card(left)

        # ---- Generate HTR card ----
        self._build_generate_htr_card(left)

        # --- RIGHT: switchable panel (preview / load image / generate HTR) ---
        self.right_panel = tk.Frame(body, bg=self.colors["bg_section"])
        self.right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Sub-frame A: dataset preview & integrity (default)
        self.preview_frame = tk.Frame(self.right_panel, bg=self.colors["bg_section"])
        self._build_preview_panel(self.preview_frame)

        # Sub-frame B: load image interface
        self.load_frame = tk.Frame(self.right_panel, bg=self.colors["bg_section"])
        self._build_load_image_panel(self.load_frame)

        # Sub-frame C: generate HTR interface
        self.generate_frame = tk.Frame(self.right_panel, bg=self.colors["bg_section"])
        self._build_generate_htr_panel(self.generate_frame)

        # Show preview by default
        self.preview_frame.pack(fill=tk.BOTH, expand=True)

    def _build_load_dataset_card(self, parent):
        """Single card that loads any dataset folder and auto-detects annotations."""
        card = tk.Frame(parent, bg=self.colors["bg_section"],
                        relief=tk.RAISED, bd=1, cursor="hand2")
        card.pack(fill=tk.X, pady=3, padx=5)

        inner = tk.Frame(card, bg=self.colors["bg_section"], padx=8, pady=6)
        inner.pack(fill=tk.X)

        badge = tk.Label(inner, text="📂",
                         font=("Segoe UI", 11, "bold"),
                         bg=self.colors["accent"], fg="white",
                         padx=4, pady=1)
        badge.pack(side=tk.LEFT, padx=(0, 8))

        txt = tk.Frame(inner, bg=self.colors["bg_section"])
        txt.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(txt, text="📂 Load Dataset",
                 font=("Segoe UI", 10, "bold"),
                 bg=self.colors["bg_section"], fg=self.colors["text_light"],
                 anchor="w").pack(fill=tk.X)
        tk.Label(txt,
                 text="Select format (IAM / Object Detection) & folder structure.",
                 font=("Segoe UI", 8),
                 bg=self.colors["bg_section"], fg=self.colors["text_muted"],
                 anchor="w", wraplength=160).pack(fill=tk.X)

        # hover effect
        def enter(e):
            card.config(bg=self.colors["secondary_bg"])
            inner.config(bg=self.colors["secondary_bg"])
            txt.config(bg=self.colors["secondary_bg"])
            for w in txt.winfo_children():
                w.config(bg=self.colors["secondary_bg"])

        def leave(e):
            card.config(bg=self.colors["bg_section"])
            inner.config(bg=self.colors["bg_section"])
            txt.config(bg=self.colors["bg_section"])
            for w in txt.winfo_children():
                w.config(bg=self.colors["bg_section"])

        # Whole card is clickable
        def on_click(e):
            self._switch_to_load()

        for w in [card, inner, txt] + list(txt.winfo_children()) + [badge]:
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<Button-1>", on_click)

    # ------------------------------------------------------------------
    # Load Annotation File + conditional actions
    # ------------------------------------------------------------------

    def _build_annotation_actions(self, parent):
        """Build the conditional action buttons (hidden by default)."""
        # Annotation status label
        self.ann_status_var = tk.StringVar(value="")
        self.ann_status_label = tk.Label(
            parent, textvariable=self.ann_status_var,
            font=("Segoe UI", 9), bg=self.colors["bg_section"],
            fg="#4caf50", wraplength=500, justify=tk.LEFT)
        self.ann_status_label.pack(fill=tk.X, padx=12, pady=(8, 4))

        btn_row = tk.Frame(parent, bg=self.colors["bg_section"])
        btn_row.pack(fill=tk.X, padx=12, pady=(0, 8))

        # Button: View Annotation Result
        self.btn_view_annotation = tk.Button(
            btn_row, text="🔎 View Annotation Result",
            command=self._view_annotation_result,
            font=("Segoe UI", 9, "bold"),
            bg="#5c6bc0", fg="white",
            activebackground="#3f51b5",
            relief=tk.FLAT, padx=10, pady=5, cursor="hand2")
        self.btn_view_annotation.pack(side=tk.LEFT, padx=(0, 6))

        # Button: Statistical Analysis
        self.btn_goto_analysis = tk.Button(
            btn_row, text="📊 Statistical Analysis",
            command=self._goto_analysis,
            font=("Segoe UI", 9, "bold"),
            bg="#43a047", fg="white",
            activebackground="#388e3c",
            relief=tk.FLAT, padx=10, pady=5, cursor="hand2")
        self.btn_goto_analysis.pack(side=tk.LEFT, padx=(0, 6))

        # Button: Preprocessing
        self.btn_goto_preprocessing = tk.Button(
            btn_row, text="🔍 Preprocessing",
            command=self._goto_preprocessing,
            font=("Segoe UI", 9, "bold"),
            bg="#fb8c00", fg="white",
            activebackground="#ef6c00",
            relief=tk.FLAT, padx=10, pady=5, cursor="hand2")
        self.btn_goto_preprocessing.pack(side=tk.LEFT)

    def _browse_annotation_file(self):
        """Show annotation format dialog, then open a file dialog to select an annotation file."""
        # --- Show annotation format dialog ---
        dlg = AnnotationFormatDialog(self, self.colors)
        self.wait_window(dlg)
        if dlg.result is None:
            return

        ann_format = dlg.result["annotation_format"]  # iam|coco|yolo|voc|auto

        # For per-image formats (YOLO / VOC) the user selects a folder
        # containing the images + their sidecar annotation files.
        if ann_format in ("yolo", "voc"):
            folder = filedialog.askdirectory(
                title="Select folder with images and annotation files")
            if not folder:
                return
            images = self.ctx.get("images") or self._scan_images(folder)
            self._parse_annotation_file(None, fmt=ann_format,
                                        image_dir=folder, images=images)
            self.ctx["annotation_format"] = ann_format
            self.ctx["metadata"]["has_annotations"] = True
            ann_count = len(self.ctx.get("annotations", []))
            self.ann_card_info.set(
                f"✅ {ann_format.upper()} ({ann_count} entries)")
            if self._annotation_matches_dataset():
                self._show_annotation_actions()
            else:
                self._hide_annotation_actions()
            return

        # For single-file formats, build appropriate file-type filter
        if ann_format == "iam":
            filetypes = [("IAM text files", "*.txt"), ("All files", "*.*")]
        elif ann_format == "coco":
            filetypes = [("COCO JSON files", "*.json"), ("All files", "*.*")]
        else:  # auto
            filetypes = [
                ("Annotation files", "*.json *.txt *.csv *.jsonl *.xml"),
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ]

        path = filedialog.askopenfilename(
            title="Select Annotation File", filetypes=filetypes)
        if not path:
            return

        # Parse the annotation file with the chosen format
        self._parse_annotation_file(path, fmt=ann_format,
                                    image_dir=self.ctx.get("image_dir", ""),
                                    images=self.ctx.get("images"))
        self.ctx["annotation_file"] = path
        self.ctx["annotation_format"] = ann_format
        self.ctx["metadata"]["has_annotations"] = True

        ann_count = len(self.ctx.get("annotations", []))
        self.ann_card_info.set(f"✅ {os.path.basename(path)} ({ann_count} entries)")
        self._update_meta_cards()

        # Check if annotation relates to the loaded image folder
        if self._annotation_matches_dataset():
            self._show_annotation_actions()
        else:
            self._hide_annotation_actions()
            messagebox.showwarning(
                "Annotation Mismatch",
                "The annotation file does not appear to match the loaded "
                "image folder.\n\nPlease load the correct image folder first, "
                "or load an annotation file that corresponds to the current dataset.")
        self._update_annotation_preview()

    def _annotation_matches_dataset(self) -> bool:
        """Check whether the loaded annotation file relates to the current dataset."""
        images = self.ctx.get("images", [])
        annotations = self.ctx.get("annotations", [])
        if not images or not annotations:
            return False

        img_basenames = {os.path.splitext(os.path.basename(p))[0].lower() for p in images}
        img_filenames = {os.path.basename(p).lower() for p in images}

        # Check if annotation IDs / image references overlap with loaded images
        matched = 0
        for ann in annotations:
            ann_id = str(ann.get("image_id", ann.get("filename", ann.get("file", "")))).strip()
            if not ann_id:
                continue
            ann_id_lower = ann_id.lower()
            ann_id_no_ext = os.path.splitext(ann_id_lower)[0]
            if ann_id_lower in img_filenames or ann_id_no_ext in img_basenames:
                matched += 1

        # Also accept if annotation and images share the same parent directory
        ann_file = self.ctx.get("annotation_file", "")
        img_dir = self.ctx.get("image_dir", "")
        same_dir = False
        if ann_file and img_dir:
            ann_dir = os.path.dirname(os.path.abspath(ann_file))
            img_dir_abs = os.path.abspath(img_dir)
            same_dir = (ann_dir == img_dir_abs
                        or ann_dir == os.path.dirname(img_dir_abs)
                        or img_dir_abs.startswith(ann_dir))

        # Consider a match if at least 10% of annotations match, or same dir
        threshold = max(1, len(annotations) * 0.1)
        return matched >= threshold or same_dir

    def _show_annotation_actions(self):
        """Show the conditional action buttons below the status bar in the right panel."""
        ann_count = len(self.ctx.get("annotations", []))
        img_count = len(self.ctx.get("images", []))
        self.ann_status_var.set(
            f"✅ Annotation matched: {ann_count} entries for {img_count} images")
        self.annotation_actions_frame.pack(fill=tk.X)

        # Update preview/integrity if dataset is already loaded
        if self.ctx.get("images"):
            self._show_preview(self.ctx["images"], has_annotations=True)

    def _hide_annotation_actions(self):
        """Hide the conditional action buttons."""
        self.annotation_actions_frame.pack_forget()

    def _view_annotation_result(self):
        """Show the annotation result — jump to annotation step."""
        wm = getattr(S, "workflow_manager", None)
        if wm:
            wm.step_states["ingestion"] = "completed"
            wm._show_step(2)  # Annotation step (index 2)
        else:
            messagebox.showinfo(
                "View Annotation",
                f"Annotation file: {self.ctx.get('annotation_file', 'N/A')}\n"
                f"Entries: {len(self.ctx.get('annotations', []))}")

    def _goto_analysis(self):
        """Jump directly to the Statistical Analysis step."""
        wm = getattr(S, "workflow_manager", None)
        if not wm:
            messagebox.showinfo("Statistical Analysis",
                                "Workflow manager not available.")
            return

        # Check if we already have annotations from ingestion
        ctx_annotations = self.ctx.get("annotations", [])
        has_ctx_annotations = (isinstance(ctx_annotations, list)
                               and ctx_annotations
                               and isinstance(ctx_annotations[0], dict))

        if not has_ctx_annotations:
            # If no annotations loaded from ingestion, try the annotation panel
            ann_panel = wm.step_panels.get('annotation') if hasattr(wm, 'step_panels') else None
            if ann_panel:
                try:
                    data, total, mode = ann_panel._collect_annotations_data()
                    if total > 0:
                        base_dir = getattr(S, 'pathDirectory', None) or self.ctx.get('image_dir') or os.getcwd()
                        target_dir = base_dir
                        os.makedirs(target_dir, exist_ok=True)
                        save_path = os.path.join(target_dir, 'annotations_auto.json')
                        saved = ann_panel.save_annotations_to_path(save_path, mode=mode, show_message=False)
                        if saved:
                            self.ctx['annotation_file'] = save_path
                            self.ctx['annotations'] = data
                            self.ctx['metadata']['has_annotations'] = True
                            self.ann_card_info.set(f"✅ annotations_auto.json ({total} entries)")
                    else:
                        messagebox.showwarning("No Annotations",
                                               "At least one image must be annotated before statistical analysis.")
                        return
                except Exception:
                    pass

            # Still no annotations?
            if not self.ctx.get("annotations") and not self.ctx.get("annotation_file"):
                messagebox.showwarning("No Annotations",
                                       "Please load an annotation file or annotate images first.")
                return

        # Proceed to Analysis
        wm.step_states["ingestion"] = "completed"
        wm._show_step(3)  # Analysis step (index 3)

    def _goto_preprocessing(self):
        """Jump to the Preprocessing step."""
        wm = getattr(S, "workflow_manager", None)
        if wm:
            wm.step_states["ingestion"] = "completed"
            wm._show_step(1)  # Preprocessing step (index 1)
        else:
            messagebox.showinfo("Preprocessing",
                                "Workflow manager not available.")

    def _build_generate_htr_card(self, parent):
        """Card to open the Generate HTR interface (same style as Load Dataset)."""
        card = tk.Frame(parent, bg=self.colors["bg_section"],
                        relief=tk.RAISED, bd=1, cursor="hand2")
        card.pack(fill=tk.X, pady=3, padx=5)

        inner = tk.Frame(card, bg=self.colors["bg_section"], padx=8, pady=6)
        inner.pack(fill=tk.X)

        badge = tk.Label(inner, text="✍️",
                         font=("Segoe UI", 11, "bold"),
                         bg=self.colors["accent"], fg="white",
                         padx=4, pady=1)
        badge.pack(side=tk.LEFT, padx=(0, 8))

        txt = tk.Frame(inner, bg=self.colors["bg_section"])
        txt.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(txt, text="✍️ Generate HTR",
                 font=("Segoe UI", 10, "bold"),
                 bg=self.colors["bg_section"], fg=self.colors["text_light"],
                 anchor="w").pack(fill=tk.X)
        tk.Label(txt,
                 text="Create synthetic handwriting from text using GAN.",
                 font=("Segoe UI", 8),
                 bg=self.colors["bg_section"], fg=self.colors["text_muted"],
                 anchor="w", wraplength=160).pack(fill=tk.X)

        # hover effect
        def enter(e):
            card.config(bg=self.colors["secondary_bg"])
            inner.config(bg=self.colors["secondary_bg"])
            txt.config(bg=self.colors["secondary_bg"])
            for w in txt.winfo_children():
                w.config(bg=self.colors["secondary_bg"])

        def leave(e):
            card.config(bg=self.colors["bg_section"])
            inner.config(bg=self.colors["bg_section"])
            txt.config(bg=self.colors["bg_section"])
            for w in txt.winfo_children():
                w.config(bg=self.colors["bg_section"])

        # Whole card is clickable
        def on_click(e):
            self._switch_to_generate()

        for w in [card, inner, txt] + list(txt.winfo_children()) + [badge]:
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<Button-1>", on_click)

    # ------------------------------------------------------------------
    # Right‑panel switcher
    # ------------------------------------------------------------------

    def _show_right_panel(self, which):
        """Switch the right panel between 'preview', 'load', 'generate'."""
        for frame in (self.preview_frame, self.load_frame, self.generate_frame):
            frame.pack_forget()
        target = {"preview": self.preview_frame,
                  "load": self.load_frame,
                  "generate": self.generate_frame}.get(which, self.preview_frame)
        target.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    # Load Image panel (right column)
    # ------------------------------------------------------------------

    def _build_load_image_panel(self, parent):
        """Build a Load‑Image interface inside the right panel."""
        # Header
        tk.Label(parent, text="📂  Load Image",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(anchor="w", padx=12, pady=(12, 4))
        tk.Label(parent, text="Browse for a folder of handwriting images, enter text, "
                              "and preview the current image.",
                 font=("Segoe UI", 9), wraplength=500,
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(anchor="w", padx=12, pady=(0, 8))

        # ---- Folder selector ----
        folder_frame = tk.LabelFrame(parent, text=" 📁 Image Folder ",
                                     font=("Segoe UI", 10, "bold"),
                                     bg=self.colors["bg_section"],
                                     fg=self.colors["text_light"],
                                     relief=tk.GROOVE, bd=1, padx=10, pady=8)
        folder_frame.pack(fill=tk.X, padx=12, pady=(0, 8))

        row = tk.Frame(folder_frame, bg=self.colors["bg_section"])
        row.pack(fill=tk.X)

        self.load_folder_var = tk.StringVar(value="No folder selected")
        tk.Label(row, textvariable=self.load_folder_var,
                 font=("Segoe UI", 9), bg="white", fg="#333",
                 anchor="w", padx=8, pady=4, relief=tk.SUNKEN).pack(
                     side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        tk.Button(row, text="📁 Browse", command=self._browse_folder,
                  font=("Segoe UI", 9, "bold"),
                  bg=self.colors["accent"], fg="white",
                  relief=tk.FLAT, padx=12, pady=4, cursor="hand2").pack(side=tk.RIGHT)

        self.load_folder_info = tk.StringVar(value="Select a folder containing handwriting images")
        tk.Label(folder_frame, textvariable=self.load_folder_info,
                 font=("Segoe UI", 8), bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(anchor="w", pady=(4, 0))

        # ---- Text input ----
        text_frame = tk.LabelFrame(parent, text=" 📝 Input Text (ASCII Transcription) ",
                                   font=("Segoe UI", 10, "bold"),
                                   bg=self.colors["bg_section"],
                                   fg=self.colors["text_light"],
                                   relief=tk.GROOVE, bd=1, padx=10, pady=8)
        text_frame.pack(fill=tk.X, padx=12, pady=(0, 8))

        tf = tk.Frame(text_frame, bg=self.colors["bg_section"])
        tf.pack(fill=tk.X)
        self.load_text_area = tk.Text(tf, width=60, height=5,
                                      font=("Segoe UI", 10), bg="white",
                                      fg="black", wrap=tk.WORD)
        self.load_text_area.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ts = tk.Scrollbar(tf, orient=tk.VERTICAL, command=self.load_text_area.yview)
        ts.pack(side=tk.RIGHT, fill=tk.Y)
        self.load_text_area.config(yscrollcommand=ts.set)

        self.load_char_count = tk.StringVar(value="Characters: 0 | Words: 0")
        tk.Label(text_frame, textvariable=self.load_char_count,
                 font=("Segoe UI", 8), bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(anchor="w", pady=(4, 0))

        def _update_load_text(_evt=None):
            c = self.load_text_area.get("1.0", "end-1c")
            self.load_char_count.set(
                f"Characters: {len(c)} | Words: {len(c.split()) if c.strip() else 0}")
            S.input_text = c
            S.gan_input_text = c
            if hasattr(S, "input_text_area"):
                S.input_text_area.delete("1.0", tk.END)
                S.input_text_area.insert("1.0", c)
        self.load_text_area.bind("<KeyRelease>", _update_load_text)

        # ---- Image preview ----
        prev_frame = tk.LabelFrame(parent, text=" 🖼️ Image Preview ",
                                   font=("Segoe UI", 10, "bold"),
                                   bg=self.colors["bg_section"],
                                   fg=self.colors["text_light"],
                                   relief=tk.GROOVE, bd=1, padx=8, pady=8)
        prev_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        self.load_preview_canvas = tk.Canvas(prev_frame, bg="#eef2f7",
                                             highlightthickness=0, height=260)
        self.load_preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.load_preview_canvas.create_text(
            300, 130, text="No image loaded\n\nBrowse a folder above to get started",
            fill="#7f8c8d", font=("Segoe UI", 11), justify=tk.CENTER)

        # Navigation
        nav = tk.Frame(prev_frame, bg=self.colors["bg_section"])
        nav.pack(fill=tk.X, pady=(6, 0))
        self.btn_load_prev = tk.Button(nav, text="◀ Prev",
                                       command=self._load_prev_img,
                                       font=("Segoe UI", 9),
                                       bg=self.colors["accent"], fg="white",
                                       padx=10, pady=3)
        self.btn_load_prev.pack(side=tk.LEFT, padx=2)
        self.btn_load_next = tk.Button(nav, text="Next ▶",
                                       command=self._load_next_img,
                                       font=("Segoe UI", 9),
                                       bg=self.colors["accent"], fg="white",
                                       padx=10, pady=3)
        self.btn_load_next.pack(side=tk.LEFT, padx=2)
        self.load_img_info = tk.StringVar(value="No images loaded")
        tk.Label(nav, textvariable=self.load_img_info,
                 font=("Segoe UI", 9), bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=12)

        # Back to preview button
        tk.Button(parent, text="⬅ Back to Dataset Preview",
                  command=lambda: self._show_right_panel("preview"),
                  font=("Segoe UI", 9),
                  bg=self.colors["bg_section"], fg=self.colors["text_light"],
                  relief=tk.GROOVE, padx=10, pady=4, cursor="hand2").pack(
                      anchor="w", padx=12, pady=(0, 8))

    # ------------------------------------------------------------------
    # Generate HTR panel (right column)
    # ------------------------------------------------------------------

    def _build_generate_htr_panel(self, parent):
        """Build a Generate‑HTR interface inside the right panel."""
        # Header
        tk.Label(parent, text="✍️  Generate HTR",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(anchor="w", padx=12, pady=(12, 4))
        tk.Label(parent, text="Create synthetic handwriting images from text using the GAN model.",
                 font=("Segoe UI", 9), wraplength=500,
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(anchor="w", padx=12, pady=(0, 8))

        # ---- Text input ----
        text_section = tk.LabelFrame(parent, text=" 📝 Text to Generate ",
                                     font=("Segoe UI", 10, "bold"),
                                     bg=self.colors["bg_section"],
                                     fg=self.colors["text_light"],
                                     relief=tk.GROOVE, bd=1, padx=10, pady=8)
        text_section.pack(fill=tk.X, padx=12, pady=(0, 8))

        tf = tk.Frame(text_section, bg=self.colors["bg_section"])
        tf.pack(fill=tk.X)
        self.gen_text_area = tk.Text(tf, width=60, height=5,
                                     font=("Segoe UI", 10), bg="white",
                                     fg="black", wrap=tk.WORD)
        self.gen_text_area.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ts = tk.Scrollbar(tf, orient=tk.VERTICAL, command=self.gen_text_area.yview)
        ts.pack(side=tk.RIGHT, fill=tk.Y)
        self.gen_text_area.config(yscrollcommand=ts.set)

        self.gen_char_count = tk.StringVar(value="0 / 500")
        tk.Label(text_section, textvariable=self.gen_char_count,
                 font=("Segoe UI", 8), bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(anchor="w", pady=(4, 0))

        def _update_gen_counter(_evt=None):
            c = self.gen_text_area.get("1.0", "end-1c")
            if len(c) > 500:
                self.gen_text_area.delete("1.0+500c", "end-1c")
                c = c[:500]
            self.gen_char_count.set(f"{len(c)} / 500")
            S.gan_input_text = c
        self.gen_text_area.bind("<KeyRelease>", _update_gen_counter)

        # ---- Options row ----
        opts = tk.LabelFrame(parent, text=" ⚙️ Generation Options ",
                             font=("Segoe UI", 10, "bold"),
                             bg=self.colors["bg_section"],
                             fg=self.colors["text_light"],
                             relief=tk.GROOVE, bd=1, padx=10, pady=8)
        opts.pack(fill=tk.X, padx=12, pady=(0, 8))

        orow = tk.Frame(opts, bg=self.colors["bg_section"])
        orow.pack(fill=tk.X)
        tk.Label(orow, text="Style:", font=("Segoe UI", 9),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT)
        self.gen_style_var = tk.IntVar(value=9)
        tk.Scale(orow, from_=0, to=12, orient=tk.HORIZONTAL,
                 variable=self.gen_style_var, length=120,
                 bg=self.colors["bg_section"], fg=self.colors["text_light"],
                 troughcolor=self.colors["bg_dark"],
                 highlightthickness=0).pack(side=tk.LEFT, padx=6)

        tk.Label(orow, text="Language:", font=("Segoe UI", 9),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT, padx=(16, 4))
        self.gen_lang_var = tk.StringVar(value="English")
        tk.OptionMenu(orow, self.gen_lang_var,
                      "English", "French", "German", "Spanish").pack(side=tk.LEFT)

        # Generate button
        self.btn_generate = tk.Button(
            parent, text="🚀 Generate",
            command=self._run_generate_htr,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["accent"], fg="white",
            activebackground=self.colors["accent_hover"],
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2")
        self.btn_generate.pack(anchor="w", padx=12, pady=(0, 8))

        # Preview canvas
        gen_prev = tk.LabelFrame(parent, text=" 🖼️ Generated Preview ",
                                 font=("Segoe UI", 10, "bold"),
                                 bg=self.colors["bg_section"],
                                 fg=self.colors["text_light"],
                                 relief=tk.GROOVE, bd=1, padx=8, pady=8)
        gen_prev.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        self.gen_preview_canvas = tk.Canvas(gen_prev, bg="#eef2f7",
                                            highlightthickness=0, height=200)
        self.gen_preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.gen_preview_canvas.create_text(
            300, 100,
            text="No generated image yet\n\nEnter text and click Generate above",
            fill="#7f8c8d", font=("Segoe UI", 11), justify=tk.CENTER)

        # Navigation for generated batch
        gnav = tk.Frame(gen_prev, bg=self.colors["bg_section"])
        gnav.pack(fill=tk.X, pady=(6, 0))
        self.btn_gen_prev = tk.Button(gnav, text="◀ Prev",
                                      command=self._gen_prev_img,
                                      font=("Segoe UI", 9),
                                      bg=self.colors["accent"], fg="white",
                                      padx=10, pady=3, state="disabled")
        self.btn_gen_prev.pack(side=tk.LEFT, padx=2)
        self.btn_gen_next = tk.Button(gnav, text="Next ▶",
                                      command=self._gen_next_img,
                                      font=("Segoe UI", 9),
                                      bg=self.colors["accent"], fg="white",
                                      padx=10, pady=3, state="disabled")
        self.btn_gen_next.pack(side=tk.LEFT, padx=2)
        self.gen_img_info = tk.StringVar(value="")
        tk.Label(gnav, textvariable=self.gen_img_info,
                 font=("Segoe UI", 9), bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=12)

    def _build_preview_panel(self, parent):
        # Load Dataset + Load Annotation buttons pinned at the top
        load_bar = tk.Frame(parent, bg=self.colors["bg_section"])
        load_bar.pack(fill=tk.X, padx=12, pady=(8, 4))

        tk.Button(load_bar, text="📂 Load Dataset",
                  command=self._load_dataset,
                  font=("Segoe UI", 10, "bold"),
                  bg=self.colors["accent"], fg="white",
                  activebackground=self.colors.get("accent_hover", "#005fc5"),
                  relief=tk.FLAT, padx=14, pady=5, cursor="hand2").pack(side=tk.LEFT)

        tk.Button(load_bar, text="📝 Load Annotation",
                  command=self._browse_annotation_file,
                  font=("Segoe UI", 10, "bold"),
                  bg="#5c6bc0", fg="white",
                  activebackground="#3f51b5",
                  relief=tk.FLAT, padx=14, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=(8, 0))

        self.ann_card_info = tk.StringVar(value="")
        self.ann_info_label = tk.Label(load_bar, textvariable=self.ann_card_info,
                                       font=("Segoe UI", 8),
                                       bg=self.colors["bg_section"],
                                       fg="#4caf50")
        self.ann_info_label.pack(side=tk.LEFT, padx=(10, 0))

        # --- Scrollable content area ---
        preview_canvas = tk.Canvas(parent, bg=self.colors["bg_section"],
                                   highlightthickness=0)
        self._preview_scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL,
                                               command=preview_canvas.yview)
        preview_canvas.configure(yscrollcommand=self._preview_scrollbar.set)
        self._preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = tk.Frame(preview_canvas, bg=self.colors["bg_section"])
        preview_canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_preview_configure(event):
            preview_canvas.configure(scrollregion=preview_canvas.bbox("all"))
            # Match inner width to canvas width
            preview_canvas.itemconfig("all", width=preview_canvas.winfo_width())
        inner.bind("<Configure>", _on_preview_configure)

        def _on_canvas_resize(event):
            preview_canvas.itemconfig(
                preview_canvas.find_withtag("all")[0], width=event.width)
        preview_canvas.bind("<Configure>", _on_canvas_resize)

        # Mouse-wheel scroll
        def _on_pw_mousewheel(event):
            preview_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        preview_canvas.bind("<Enter>",
                            lambda e: preview_canvas.bind_all("<MouseWheel>", _on_pw_mousewheel, add="+"))
        preview_canvas.bind("<Leave>",
                            lambda e: preview_canvas.unbind_all("<MouseWheel>"))

        # --- All content goes into `inner` ---
        tk.Label(inner, text="🔎 Dataset Preview & Integrity",
                 font=("Segoe UI", 12, "bold"),
                 bg=self.colors["bg_section"], fg=self.colors["text_light"]).pack(anchor="w", padx=12, pady=(12, 5))

        # Status bar
        self.status_var = tk.StringVar(value="No dataset loaded yet.")
        tk.Label(inner, textvariable=self.status_var,
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_section"], fg=self.colors["text_muted"]).pack(anchor="w", padx=12)

        # ---- Conditional annotation actions (hidden until annotation matches) ----
        self.annotation_actions_frame = tk.Frame(inner, bg=self.colors["bg_section"])
        self._build_annotation_actions(self.annotation_actions_frame)
        # Initially hidden
        # (will be shown via _show_annotation_actions when annotation matches)

        sep = tk.Frame(inner, height=1, bg=self.colors["border"])
        sep.pack(fill=tk.X, padx=12, pady=8)

        # Metadata cards row
        self.meta_frame = tk.Frame(inner, bg=self.colors["bg_section"])
        self.meta_frame.pack(fill=tk.X, padx=12)

        self.meta_cards = {}
        for key, label in [("images", "🖼️ Images"), ("annotations", "📝 Annotations"),
                           ("resolution", "📐 Avg Resolution"), ("size", "💾 Total Size")]:
            f = tk.Frame(self.meta_frame, bg="white", relief=tk.RIDGE, bd=1)
            f.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3, pady=3)
            tk.Label(f, text=label, font=("Segoe UI", 8),
                     bg="white", fg=self.colors["text_muted"]).pack(padx=6, pady=(6, 0))
            val = tk.Label(f, text="—", font=("Segoe UI", 14, "bold"),
                           bg="white", fg=self.colors["text_light"])
            val.pack(padx=6, pady=(0, 6))
            self.meta_cards[key] = val

        # ---- Text input (ASCII Transcription) ----
        text_frame = tk.LabelFrame(inner, text=" 📝 Input Text (ASCII Transcription) ",
                                   font=("Segoe UI", 10, "bold"),
                                   bg=self.colors["bg_section"],
                                   fg=self.colors["text_light"],
                                   relief=tk.GROOVE, bd=1, padx=10, pady=8)
        text_frame.pack(fill=tk.X, padx=12, pady=(12, 8))

        tf = tk.Frame(text_frame, bg=self.colors["bg_section"])
        tf.pack(fill=tk.X)
        self.preview_text_area = tk.Text(tf, width=60, height=4,
                                         font=("Segoe UI", 10), bg="white",
                                         fg="black", wrap=tk.WORD)
        self.preview_text_area.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ts = tk.Scrollbar(tf, orient=tk.VERTICAL, command=self.preview_text_area.yview)
        ts.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text_area.config(yscrollcommand=ts.set)

        self.preview_char_count = tk.StringVar(value="Characters: 0 | Words: 0")
        tk.Label(text_frame, textvariable=self.preview_char_count,
                 font=("Segoe UI", 8), bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(anchor="w", pady=(4, 0))

        def _update_preview_text(_evt=None):
            c = self.preview_text_area.get("1.0", "end-1c")
            self.preview_char_count.set(
                f"Characters: {len(c)} | Words: {len(c.split()) if c.strip() else 0}")
            S.input_text = c
            S.gan_input_text = c
            if hasattr(S, "input_text_area"):
                S.input_text_area.delete("1.0", tk.END)
                S.input_text_area.insert("1.0", c)
        self.preview_text_area.bind("<KeyRelease>", _update_preview_text)

        # ---- Side-by-side: Image Preview + Integrity Report ----
        row_frame = tk.Frame(inner, bg=self.colors["bg_section"])
        row_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        # Left: Image Preview
        prev_frame = tk.LabelFrame(row_frame, text=" 🖼️ Image Preview ",
                                   font=("Segoe UI", 10, "bold"),
                                   bg=self.colors["bg_section"],
                                   fg=self.colors["text_light"],
                                   relief=tk.GROOVE, bd=1, padx=8, pady=8)
        prev_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        self.preview_img_canvas = tk.Canvas(prev_frame, bg="#eef2f7",
                                            highlightthickness=0, height=220)
        self.preview_img_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_img_canvas.create_text(
            200, 110, text="No image loaded\n\nLoad a dataset to preview",
            fill="#7f8c8d", font=("Segoe UI", 10), justify=tk.CENTER)

        # Navigation
        nav = tk.Frame(prev_frame, bg=self.colors["bg_section"])
        nav.pack(fill=tk.X, pady=(6, 0))
        self.btn_preview_prev = tk.Button(nav, text="◀ Prev",
                                          command=self._preview_prev_img,
                                          font=("Segoe UI", 9),
                                          bg=self.colors["accent"], fg="white",
                                          padx=10, pady=3)
        self.btn_preview_prev.pack(side=tk.LEFT, padx=2)
        self.btn_preview_next = tk.Button(nav, text="Next ▶",
                                          command=self._preview_next_img,
                                          font=("Segoe UI", 9),
                                          bg=self.colors["accent"], fg="white",
                                          padx=10, pady=3)
        self.btn_preview_next.pack(side=tk.LEFT, padx=2)
        self.preview_img_info = tk.StringVar(value="No images loaded")
        tk.Label(nav, textvariable=self.preview_img_info,
                 font=("Segoe UI", 9), bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=8)
        self.preview_img_index = 0

        # Right: Integrity Report
        integrity_frame = tk.LabelFrame(row_frame, text=" ✅ Integrity Report ",
                                        font=("Segoe UI", 10, "bold"),
                                        bg=self.colors["bg_section"],
                                        fg=self.colors["text_light"],
                                        relief=tk.GROOVE, bd=1, padx=8, pady=8,
                                        width=220)
        integrity_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))
        integrity_frame.pack_propagate(False)

        self.integrity_text = tk.Text(integrity_frame, height=10, font=("Segoe UI", 9),
                                      bg="white", fg=self.colors["text_light"],
                                      wrap=tk.WORD, state="disabled", width=24)
        self.integrity_text.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    # Sidebar tool sections (embedded in left column)
    # ------------------------------------------------------------------

    def _build_input_mode_section(self, parent):
        """Input mode section with Load Image button."""
        frame = tk.LabelFrame(parent, text=" 📂 Input Mode ",
                               font=("Segoe UI", 10, "bold"),
                               bg=self.colors["bg_section"],
                               fg=self.colors["text_light"],
                               relief=tk.FLAT, bd=1, padx=10, pady=8)
        frame.pack(fill=tk.X, padx=5, pady=(0, 6))

        self.btn_mode_load = tk.Button(
            frame, text="📁 Load Image",
            command=self._switch_to_load,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["accent"], fg="white",
            relief=tk.FLAT, padx=10, pady=5, cursor="hand2")
        self.btn_mode_load.pack(fill=tk.X, pady=4)

        self.seg_mode_var = tk.StringVar(value="Segmentation mode: not chosen")
        tk.Label(frame, textvariable=self.seg_mode_var,
                 font=("Segoe UI", 8, "italic"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(anchor="w", pady=(4, 0))

    def _build_detection_section(self, parent):
        """Line / Word / Character detection buttons."""
        det = tk.LabelFrame(parent, text=" 🔍 Detection ",
                            font=("Segoe UI", 10, "bold"),
                            bg=self.colors["bg_section"],
                            fg=self.colors["text_light"],
                            relief=tk.FLAT, bd=1, padx=10, pady=8)
        det.pack(fill=tk.X, padx=5, pady=(0, 6))

        # Line detection
        self.btn_line = tk.Button(
            det, text="📄 Detect Lines", command=self._detect_lines,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["accent"], fg="white",
            activebackground=self.colors["accent_hover"],
            relief=tk.FLAT, cursor="hand2", padx=10, pady=5)
        self.btn_line.pack(fill=tk.X, pady=2)

        # Word detection
        self.btn_word = tk.Button(
            det, text="🎯 Detect Words", command=self._detect_words,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["accent"], fg="white",
            activebackground=self.colors["accent_hover"],
            relief=tk.FLAT, cursor="hand2", padx=10, pady=5)
        self.btn_word.pack(fill=tk.X, pady=2)

        # Character detection
        self.btn_char = tk.Button(
            det, text="🔤 Detect Characters", command=self._detect_chars,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["accent"], fg="white",
            activebackground=self.colors["accent_hover"],
            relief=tk.FLAT, cursor="hand2", padx=10, pady=5)
        self.btn_char.pack(fill=tk.X, pady=2)

        # Initially disable until images are loaded
        self.btn_line.config(state="disabled")
        self.btn_word.config(state="disabled")
        self.btn_char.config(state="disabled")

    def _build_params_section(self, parent):
        """Scale and Padding sliders."""
        params = tk.LabelFrame(parent, text=" ⚙️ Scale & Padding ",
                               font=("Segoe UI", 10, "bold"),
                               bg=self.colors["bg_section"],
                               fg=self.colors["text_light"],
                               relief=tk.FLAT, bd=1, padx=10, pady=8)
        params.pack(fill=tk.X, padx=5, pady=(0, 6))

        # Scale
        self.scale_label = tk.Label(
            params,
            text=f"🔎 Scale: {getattr(S, 'image_scale', 1.0):.1f}x",
            font=("Segoe UI", 9),
            bg=self.colors["bg_section"],
            fg=self.colors["text_light"], anchor="w")
        self.scale_label.pack(fill=tk.X)
        self.scale_slider = tk.Scale(
            params, from_=0.5, to=3.0, resolution=0.1,
            orient=tk.HORIZONTAL,
            bg=self.colors["bg_section"], fg=self.colors["text_light"],
            troughcolor=self.colors["bg_dark"],
            activebackground=self.colors["accent"],
            highlightthickness=0, sliderrelief=tk.FLAT,
            command=self._on_scale_change)
        self.scale_slider.set(getattr(S, 'image_scale', 1.0))
        self.scale_slider.pack(fill=tk.X)

        # Padding
        self.padding_label = tk.Label(
            params,
            text=f"📏 Padding: {getattr(S, 'bbox_padding', 0)}px",
            font=("Segoe UI", 9),
            bg=self.colors["bg_section"],
            fg=self.colors["text_light"], anchor="w")
        self.padding_label.pack(fill=tk.X, pady=(6, 0))
        self.padding_slider = tk.Scale(
            params, from_=-20, to=50, resolution=1,
            orient=tk.HORIZONTAL,
            bg=self.colors["bg_section"], fg=self.colors["text_light"],
            troughcolor=self.colors["bg_dark"],
            activebackground=self.colors["accent"],
            highlightthickness=0, sliderrelief=tk.FLAT,
            command=self._on_padding_change)
        self.padding_slider.set(getattr(S, 'bbox_padding', 0))
        self.padding_slider.pack(fill=tk.X)

    # ------------------------------------------------------------------
    # Input mode helpers
    # ------------------------------------------------------------------

    def _switch_to_load(self):
        if hasattr(S, "input_mode_var"):
            S.input_mode_var.set("load")
        # Show the default preview panel (initial state)
        self._show_right_panel("preview")

    def _switch_to_generate(self):
        if hasattr(S, "input_mode_var"):
            S.input_mode_var.set("generate")
        # Show generate‑HTR interface in the right panel
        self._show_right_panel("generate")

    # ------------------------------------------------------------------
    # Load Image panel helpers
    # ------------------------------------------------------------------

    def _browse_folder(self):
        """Open a folder dialog and load images."""
        folder = filedialog.askdirectory(title="Select folder with images")
        if not folder:
            return
        images = self._scan_images(folder)
        if not images:
            messagebox.showwarning("No Images",
                                   "No image files found in the selected folder.")
            return
        # Update context
        self.ctx["type"] = "raw"
        self.ctx["image_dir"] = folder
        self.ctx["images"] = images
        self.ctx["annotations"] = []
        self.ctx["metadata"]["has_annotations"] = False
        # Sync legacy state
        S.pathDirectory = folder
        S.list_of_files = images
        S.pos = 0
        # Subfolders
        S.directoryout = os.path.join(folder, "out")
        S.directorytmp = os.path.join(folder, "tmp")
        S.directorydone = os.path.join(folder, "done")
        for d in (S.directoryout, S.directorytmp, S.directorydone):
            os.makedirs(d, exist_ok=True)
        # Update load‑image panel
        self.load_folder_var.set(folder)
        self.load_folder_info.set(f"Found {len(images)} images")
        self._refresh_load_preview()
        # Update preview & integrity panel as well
        self._extract_metadata(images)
        self._show_preview(images, has_annotations=False)
        # Enable detection
        self._enable_detection_buttons()
        # Sync main GUI folder info
        if hasattr(S, "folder_path_var"):
            S.folder_path_var.set(folder)
        if hasattr(S, "folder_info_var"):
            S.folder_info_var.set(f"Found {len(images)} images")
        if hasattr(S, "update_detection_visibility"):
            S.update_detection_visibility()
        # Ensure Next button is enabled after loading
        self._enable_next_button()

    def _refresh_load_preview(self):
        """Refresh the load‑image preview canvas with the current image."""
        self.load_preview_canvas.delete("all")
        imgs = getattr(S, "list_of_files", []) or self.ctx.get("images", [])
        if not imgs:
            self.load_preview_canvas.create_text(
                300, 130,
                text="No image loaded\n\nBrowse a folder above to get started",
                fill="#7f8c8d", font=("Segoe UI", 11), justify=tk.CENTER)
            self.load_img_info.set("No images loaded")
            return
        pos = getattr(S, "pos", 0)
        pos = max(0, min(pos, len(imgs) - 1))
        path = imgs[pos]
        try:
            img = Image.open(path)
            cw, ch = 600, 260
            iw, ih = img.size
            scale = min(cw / iw, ch / ih, 1.5)
            nw, nh = int(iw * scale), int(ih * scale)
            img_r = img.resize((nw, nh), Image.LANCZOS)
            self._load_preview_photo = ImageTk.PhotoImage(img_r)
            xo = max(0, (cw - nw) // 2)
            yo = max(0, (ch - nh) // 2)
            self.load_preview_canvas.create_image(xo, yo, anchor=tk.NW,
                                                  image=self._load_preview_photo)
        except Exception as e:
            self.load_preview_canvas.create_text(
                300, 130, text=f"Error: {e}",
                fill="red", font=("Segoe UI", 10))
        self.load_img_info.set(f"Image {pos + 1} of {len(imgs)}")
        # Sync main GUI preview
        if hasattr(S, "update_preview_image"):
            S.update_preview_image(path)
        if hasattr(S, "image_info_var"):
            S.image_info_var.set(f"Image {pos + 1} of {len(imgs)}")

    def _load_prev_img(self):
        imgs = getattr(S, "list_of_files", []) or self.ctx.get("images", [])
        if imgs and S.pos > 0:
            S.pos -= 1
            self._refresh_load_preview()

    def _load_next_img(self):
        imgs = getattr(S, "list_of_files", []) or self.ctx.get("images", [])
        if imgs and S.pos < len(imgs) - 1:
            S.pos += 1
            self._refresh_load_preview()

    # ------------------------------------------------------------------
    # Preview panel image navigation
    # ------------------------------------------------------------------

    def _refresh_preview_image(self):
        """Refresh the preview panel canvas with the current image."""
        self.preview_img_canvas.delete("all")
        imgs = self.ctx.get("images", [])
        if not imgs:
            self.preview_img_canvas.create_text(
                300, 110,
                text="No image loaded\n\nLoad a dataset to preview images",
                fill="#7f8c8d", font=("Segoe UI", 11), justify=tk.CENTER)
            self.preview_img_info.set("No images loaded")
            return
        idx = max(0, min(self.preview_img_index, len(imgs) - 1))
        self.preview_img_index = idx
        path = imgs[idx]
        try:
            img = Image.open(path)
            cw, ch = 600, 220
            iw, ih = img.size
            scale = min(cw / iw, ch / ih, 1.5)
            nw, nh = int(iw * scale), int(ih * scale)
            img_r = img.resize((nw, nh), Image.LANCZOS)
            self._preview_panel_photo = ImageTk.PhotoImage(img_r)
            xo = max(0, (cw - nw) // 2)
            yo = max(0, (ch - nh) // 2)
            self.preview_img_canvas.create_image(xo, yo, anchor=tk.NW,
                                                 image=self._preview_panel_photo)
        except Exception as e:
            self.preview_img_canvas.create_text(
                300, 110, text=f"Error: {e}",
                fill="red", font=("Segoe UI", 10))
        self.preview_img_info.set(f"Image {idx + 1} of {len(imgs)}")

        # Update annotation text for the current image
        self._update_annotation_preview()

    def _get_annotations_for_image(self, image_path: str) -> List[str]:
        """Return annotation texts matching the given image path."""
        annotations = self.ctx.get("annotations", [])
        if not annotations:
            return []

        img_basename = os.path.basename(image_path).lower()
        img_no_ext = os.path.splitext(img_basename)[0]

        texts = []
        for ann in annotations:
            ann_id = str(ann.get("image_id", ann.get("filename", ann.get("file", "")))).strip()
            if not ann_id:
                continue
            ann_id_lower = ann_id.lower()
            ann_id_no_ext = os.path.splitext(ann_id_lower)[0]
            if ann_id_lower == img_basename or ann_id_no_ext == img_no_ext:
                # Prefer 'label', fall back to 'text', then 'caption'
                text = ann.get("label", ann.get("text", ann.get("caption", "")))
                if text:
                    texts.append(str(text))
        return texts

    def _update_annotation_preview(self):
        """Populate the ASCII text area with annotation text for the current preview image."""
        imgs = self.ctx.get("images", [])
        if not imgs:
            return
        idx = max(0, min(self.preview_img_index, len(imgs) - 1))
        path = imgs[idx]

        texts = self._get_annotations_for_image(path)
        if texts:
            combined = "\n".join(texts)
            self.preview_text_area.delete("1.0", tk.END)
            self.preview_text_area.insert("1.0", combined)
            # Update char/word count
            c = combined
            self.preview_char_count.set(
                f"Characters: {len(c)} | Words: {len(c.split()) if c.strip() else 0}")
            # Sync to state
            S.input_text = combined
            S.gan_input_text = combined
            if hasattr(S, "input_text_area"):
                S.input_text_area.delete("1.0", tk.END)
                S.input_text_area.insert("1.0", combined)

    def _preview_prev_img(self):
        imgs = self.ctx.get("images", [])
        if imgs and self.preview_img_index > 0:
            self.preview_img_index -= 1
            self._refresh_preview_image()

    def _preview_next_img(self):
        imgs = self.ctx.get("images", [])
        if imgs and self.preview_img_index < len(imgs) - 1:
            self.preview_img_index += 1
            self._refresh_preview_image()

    # ------------------------------------------------------------------
    # Generate HTR panel helpers
    # ------------------------------------------------------------------

    def _run_generate_htr(self):
        """Trigger the GAN model directly to generate synthetic handwriting."""
        content = self.gen_text_area.get("1.0", "end-1c").strip()
        if not content:
            messagebox.showinfo("Generate HTR",
                                "Please enter some text first.")
            return
        S.gan_input_text = content
        # Sync input_text for annotation
        S.input_text = content
        if hasattr(S, "input_text_area"):
            S.input_text_area.delete("1.0", tk.END)
            S.input_text_area.insert("1.0", content)

        style_val = self.gen_style_var.get()

        # Show "generating" feedback
        self.btn_generate.config(state="disabled", text="⏳ Generating...")
        self.gen_preview_canvas.delete("all")
        self.gen_preview_canvas.create_text(
            300, 100, text="Generating handwriting…\nPlease wait.",
            fill="#7f8c8d", font=("Segoe UI", 11), justify=tk.CENTER)
        self.update_idletasks()

        # Run generation in a background thread so UI doesn't freeze
        def _do_generate():
            try:
                import sys, tempfile
                current_dir = os.path.dirname(os.path.abspath(__file__))
                gan_dir = os.path.abspath(os.path.join(current_dir, '..', 'gan'))

                # Import Hand class
                if gan_dir not in sys.path:
                    sys.path.insert(0, gan_dir)
                old_cwd = os.getcwd()
                os.chdir(gan_dir)
                try:
                    from demo import Hand
                    hand = Hand()
                except Exception as e:
                    os.chdir(old_cwd)
                    self.after(0, lambda: self._on_generate_error(
                        f"Failed to load GAN model:\n{e}"))
                    return

                # Split content into lines, wrap at 75 chars
                lines = []
                maxlen = 75
                for input_line in content.splitlines():
                    if input_line.strip() == "":
                        lines.append("")
                        continue
                    words = input_line.split()
                    cur = ""
                    for w in words:
                        add_len = len(w) + (1 if cur else 0)
                        if len(cur) + add_len <= maxlen:
                            cur = (cur + " " + w) if cur else w
                        else:
                            if cur:
                                lines.append(cur)
                            if len(w) > maxlen:
                                for i in range(0, len(w), maxlen):
                                    lines.append(w[i:i + maxlen])
                                cur = ""
                            else:
                                cur = w
                    if cur:
                        lines.append(cur)

                if not lines:
                    os.chdir(old_cwd)
                    self.after(0, lambda: self._on_generate_error("No valid text to generate."))
                    return

                # Check available styles
                available_styles = []
                styles_dir_path = os.path.join(gan_dir, 'styles')
                if os.path.isdir(styles_dir_path):
                    for i in range(21):
                        if (os.path.isfile(os.path.join(styles_dir_path, f'style-{i}-strokes.npy'))
                                and os.path.isfile(os.path.join(styles_dir_path, f'style-{i}-chars.npy'))):
                            available_styles.append(i)

                if style_val in available_styles:
                    styles = [style_val] * len(lines)
                elif available_styles:
                    styles = [available_styles[0]] * len(lines)
                else:
                    styles = None

                # Generate in batches of 7 lines
                preview_dir = tempfile.mkdtemp(prefix="htr_preview_")
                batch_size = 7
                batches = [lines[i:i + batch_size] for i in range(0, len(lines), batch_size)]
                generated_files = []

                from actions.generate_htr import svg_to_jpeg

                for bidx, b_lines in enumerate(batches, start=1):
                    b_lines = [l for l in b_lines]
                    if not any(b_lines):
                        continue
                    out_svg = os.path.join(preview_dir, f'batch_{bidx}.svg')
                    out_jpg = os.path.join(preview_dir, f'batch_{bidx}.jpg')
                    biases_b = [0.75] * len(b_lines)
                    styles_b = ([styles[0]] * len(b_lines)) if styles else None
                    stroke_colors_b = ['black'] * len(b_lines)
                    stroke_widths_b = [1] * len(b_lines)

                    os.chdir(gan_dir)
                    try:
                        hand.write(
                            filename=out_svg,
                            lines=b_lines,
                            biases=biases_b,
                            styles=styles_b,
                            stroke_colors=stroke_colors_b,
                            stroke_widths=stroke_widths_b
                        )
                    finally:
                        os.chdir(old_cwd)

                    try:
                        svg_to_jpeg(out_svg, out_jpg, 1200, 600)
                    except Exception:
                        pass
                    generated_files.append((out_svg, out_jpg, b_lines))

                if not generated_files:
                    self.after(0, lambda: self._on_generate_error("No valid batches generated."))
                    return

                # Populate shared state
                S.gan_batch_images = [
                    jp if os.path.isfile(jp) else sv
                    for sv, jp, _ in generated_files
                ]
                S.gan_generated_files = generated_files
                S.gan_batch_index = 0
                S.gan_generated_ready = True

                # Update UI on the main thread
                self.after(0, self._on_generate_success)

            except Exception as e:
                self.after(0, lambda: self._on_generate_error(str(e)))

        threading.Thread(target=_do_generate, daemon=True).start()

    def _on_generate_success(self):
        """Called on main thread after successful GAN generation."""
        self.btn_generate.config(state="normal", text="🚀 Generate")
        self._gen_retry = 0
        self._update_gen_preview()
        messagebox.showinfo("Generate HTR",
                            f"Generated {len(S.gan_batch_images)} batch(es) of handwriting images.")

    def _on_generate_error(self, msg):
        """Called on main thread when generation fails."""
        self.btn_generate.config(state="normal", text="🚀 Generate")
        self.gen_preview_canvas.delete("all")
        self.gen_preview_canvas.create_text(
            300, 100, text=f"Generation failed:\n{msg}",
            fill="red", font=("Segoe UI", 10), justify=tk.CENTER)
        messagebox.showerror("Generation Error", msg)

    def _update_gen_preview(self):
        """Refresh generate preview canvas with the latest GAN output."""
        batch = getattr(S, "gan_batch_images", [])
        if not batch:
            # Generation may still be running – retry a few times
            retries = getattr(self, "_gen_retry", 0)
            if retries < 10:
                self._gen_retry = retries + 1
                self.after(1000, self._update_gen_preview)
            return
        self._gen_retry = 0
        idx = getattr(S, "gan_batch_index", 0)
        idx = max(0, min(idx, len(batch) - 1))
        S.gan_batch_index = idx
        self._render_gen_preview(batch, idx)
        self.btn_gen_prev.config(state="normal" if idx > 0 else "disabled")
        self.btn_gen_next.config(state="normal" if idx < len(batch) - 1 else "disabled")
        self.gen_img_info.set(f"Image {idx + 1} of {len(batch)}")
        # Also sync legacy state
        S.gan_generated_ready = True
        imgs = [p for p in batch if os.path.isfile(p)]
        if imgs:
            self.ctx["type"] = "synthetic"
            self.ctx["image_dir"] = os.path.dirname(imgs[0])
            self.ctx["images"] = imgs
            S.list_of_files = imgs
            S.pos = idx
            self._enable_detection_buttons()
        # Enable Next button whenever generation produces output
        self._enable_next_button()

    def _render_gen_preview(self, batch, idx):
        self.gen_preview_canvas.delete("all")
        path = batch[idx]
        try:
            img = Image.open(path)
            cw, ch = 600, 200
            iw, ih = img.size
            scale = min(cw / iw, ch / ih, 1.5)
            nw, nh = int(iw * scale), int(ih * scale)
            img_r = img.resize((nw, nh), Image.LANCZOS)
            self._gen_preview_photo = ImageTk.PhotoImage(img_r)
            xo, yo = max(0, (cw - nw) // 2), max(0, (ch - nh) // 2)
            self.gen_preview_canvas.create_image(xo, yo, anchor=tk.NW,
                                                 image=self._gen_preview_photo)
        except Exception as e:
            self.gen_preview_canvas.create_text(
                300, 100, text=f"Error: {e}",
                fill="red", font=("Segoe UI", 10))

    def _gen_prev_img(self):
        batch = getattr(S, "gan_batch_images", [])
        idx = getattr(S, "gan_batch_index", 0)
        if batch and idx > 0:
            S.gan_batch_index = idx - 1
            self._update_gen_preview()

    def _gen_next_img(self):
        batch = getattr(S, "gan_batch_images", [])
        idx = getattr(S, "gan_batch_index", 0)
        if batch and idx < len(batch) - 1:
            S.gan_batch_index = idx + 1
            self._update_gen_preview()

    # ------------------------------------------------------------------
    # Detection delegates
    # ------------------------------------------------------------------

    def _ensure_images_ready(self):
        imgs = self.ctx.get("images", [])
        if imgs and (not S.list_of_files or S.list_of_files != imgs):
            S.list_of_files = list(imgs)
            S.pos = min(getattr(S, "pos", 0), len(imgs) - 1)
            S.pathDirectory = self.ctx.get("image_dir", "")
            if S.pathDirectory:
                S.directoryout = os.path.join(S.pathDirectory, "out")
                S.directorytmp = os.path.join(S.pathDirectory, "tmp")
                S.directorydone = os.path.join(S.pathDirectory, "done")
                os.makedirs(S.directoryout, exist_ok=True)
                os.makedirs(S.directorytmp, exist_ok=True)
                os.makedirs(S.directorydone, exist_ok=True)
        if not S.list_of_files:
            messagebox.showwarning(
                "No Images",
                "Please load a dataset first using one of the options above.")
            return False
        return True

    def _detect_lines(self):
        if not self._ensure_images_ready():
            return
        func = getattr(S, "_workflow_detect_lines", None)
        if func:
            func()
        else:
            messagebox.showinfo("Line Detection",
                                "Use the sidebar '📄 Detect Lines' button.")

    def _detect_words(self):
        if not self._ensure_images_ready():
            return
        func = getattr(S, "_workflow_detect_words", None)
        if func:
            func()
        else:
            messagebox.showinfo("Word Detection",
                                "Use the sidebar '🎯 Detect Words' button.")

    def _detect_chars(self):
        if not self._ensure_images_ready():
            return
        func = getattr(S, "_workflow_detect_chars", None)
        if func:
            func()
        else:
            messagebox.showinfo("Character Detection",
                                "Use the sidebar '🔤 Detect Chars' button.")

    def _on_scale_change(self, val):
        S.image_scale = float(val)
        self.scale_label.config(text=f"🔎 Scale: {float(val):.1f}x")

    def _on_padding_change(self, val):
        S.bbox_padding = int(float(val))
        self.padding_label.config(text=f"📏 Padding: {int(float(val))}px")

    def _enable_detection_buttons(self):
        """Enable detection buttons after data is loaded."""
        if not hasattr(self, 'btn_line'):
            return
        self.btn_line.config(state="normal")
        self.btn_word.config(state="normal")
        # Character only if word images already exist
        if getattr(S, "word_image_paths", []):
            self.btn_char.config(state="normal")

    # ------------------------------------------------------------------
    # Option handlers
    # ------------------------------------------------------------------

    def _load_dataset(self):
        """Dataset loader — show folder-structure dialog, pick a folder, load."""
        dlg = DatasetFolderDialog(self, self.colors)
        self.wait_window(dlg)
        if dlg.result is None:
            return

        folder_struct = dlg.result["folder_structure"]  # flat|subfolders

        folder = filedialog.askdirectory(title="Select dataset folder")
        if not folder:
            return

        # --- Scan images ---
        if folder_struct == "subfolders":
            images = self._scan_images_recursive(folder)
        else:
            images = self._scan_images(folder)
            for sub in ("batch", "out_data", "images", "img", "data"):
                sub_path = os.path.join(folder, sub)
                if os.path.isdir(sub_path):
                    images.extend(self._scan_images(sub_path))

        if not images:
            messagebox.showwarning(
                "No Images",
                "No image files found in the selected folder"
                + (" (recursive scan)." if folder_struct == "subfolders" else " (or common subfolders)."))
            return

        # --- Auto-detect annotation file ---
        ann_file = self._find_annotation_file(folder)
        if ann_file is None:
            parent_dir = os.path.dirname(folder)
            candidate = os.path.join(parent_dir, "annotation.txt")
            if os.path.isfile(candidate):
                ann_file = candidate

        has_ann = ann_file is not None

        # Determine dataset type label
        ds_type = "annotated" if has_ann else "raw"

        # Populate context
        self.ctx["type"] = ds_type
        self.ctx["image_dir"] = folder
        self.ctx["images"] = images
        self.ctx["annotations"] = []
        self.ctx["annotation_file"] = ann_file
        self.ctx["folder_structure"] = folder_struct
        self.ctx["metadata"]["has_annotations"] = has_ann

        if has_ann:
            self._parse_annotation_file(ann_file, fmt="auto",
                                        image_dir=folder, images=images)

        # Legacy state sync
        S.pathDirectory = folder
        S.list_of_files = images
        S.pos = 0
        S.directoryout = os.path.join(folder, "out")
        S.directorytmp = os.path.join(folder, "tmp")
        S.directorydone = os.path.join(folder, "done")
        for d in (S.directoryout, S.directorytmp, S.directorydone):
            os.makedirs(d, exist_ok=True)

        # Update preview / metadata
        self._extract_metadata(images)
        self._show_preview(images, has_annotations=has_ann)

        # Show annotation actions if auto-detected annotation matches
        if has_ann and self._annotation_matches_dataset():
            ann_count = len(self.ctx.get("annotations", []))
            self.ann_card_info.set(f"✅ {os.path.basename(ann_file)} ({ann_count} entries)")
            self._show_annotation_actions()
        else:
            self._hide_annotation_actions()

        # Sync main GUI folder info
        if hasattr(S, "folder_path_var"):
            S.folder_path_var.set(folder)
        if hasattr(S, "folder_info_var"):
            S.folder_info_var.set(f"Found {len(images)} images")
        if hasattr(S, "update_detection_visibility"):
            S.update_detection_visibility()
        # Ensure Next button is enabled after loading
        self._enable_next_button()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _scan_images(folder: str) -> List[str]:
        exts = ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tif", "*.tiff")
        files = []
        for ext in exts:
            files.extend(glob.glob(os.path.join(folder, ext)))
        files.sort()
        return files

    @staticmethod
    def _scan_images_recursive(folder: str) -> List[str]:
        """Recursively scan *folder* and all sub-folders for image files.

        This supports IAM-style directory layouts where images are nested
        in multiple levels of sub-folders (e.g. ``forms/a01/a01-000u.png``).
        """
        IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
        files: List[str] = []
        for root, _dirs, filenames in os.walk(folder):
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in IMG_EXTS:
                    files.append(os.path.join(root, fn))
        files.sort()
        return files

    @staticmethod
    def _ask_annotation_file(title: str, filetypes) -> str | None:
        """Open a file dialog for the user to pick an annotation file."""
        path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        return path if path else None

    @staticmethod
    def _find_annotation_file_by_ext(folder: str, exts: List[str]) -> str | None:
        """Find the first annotation file in *folder* whose extension is in *exts*."""
        for name in os.listdir(folder):
            if os.path.splitext(name)[1].lower() in exts:
                full = os.path.join(folder, name)
                if os.path.isfile(full):
                    return full
        return None

    def _find_annotation_file(self, folder: str):
        """Detect annotation file in a folder."""
        for name in ["annotation.txt", "annotations.json", "annotations.txt",
                      "labels.json", "labels.csv", "data.json"]:
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                return path
        # Fall back: any .json or .txt
        for ext in ("*.json", "*.txt", "*.csv"):
            matches = glob.glob(os.path.join(folder, ext))
            if matches:
                return matches[0]
        return None

    def _parse_annotation_file(self, path: str, *,
                                fmt: str = "auto",
                                image_dir: str = "",
                                images: List[str] | None = None):
        """Parse annotation file and populate context.

        Parameters
        ----------
        path : str | None
            Path to the main annotation file.  May be *None* for per-image
            formats (YOLO, VOC) where annotations live beside the images.
        fmt : str
            Annotation format hint — ``"iam"``, ``"coco"``, ``"yolo"``,
            ``"voc"``, or ``"auto"`` (detect from extension / content).
        image_dir : str
            Root image directory (used by YOLO / VOC to locate per-image
            annotation files).
        images : list[str] | None
            Full list of image paths (for YOLO / VOC per-image lookup).
        """
        annotations: List[Dict[str, Any]] = []
        writers: set = set()

        try:
            # ---- YOLO (per-image .txt) ----
            if fmt == "yolo":
                annotations, writers = self._parse_yolo_annotations(
                    image_dir, images or [])

            # ---- Pascal VOC (per-image .xml) ----
            elif fmt == "voc":
                annotations, writers = self._parse_voc_annotations(
                    image_dir, images or [])

            # ---- COCO JSON ----
            elif fmt == "coco" and path:
                annotations, writers = self._parse_coco_annotation_file(path)

            # ---- IAM .txt ----
            elif fmt == "iam" and path:
                annotations, writers = self._parse_iam_annotation_file(path)

            # ---- Auto-detect ----
            elif path:
                ext = os.path.splitext(path)[1].lower()
                if ext == ".json":
                    annotations, writers = self._parse_coco_annotation_file(path)
                elif ext in (".txt", ""):
                    annotations, writers = self._parse_iam_annotation_file(path)
                elif ext == ".csv":
                    import csv
                    with open(path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            annotations.append(dict(row))
                elif ext == ".jsonl":
                    with open(path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                annotations.append(json.loads(line))
        except Exception as e:
            messagebox.showerror("Parse Error",
                                 f"Failed to parse annotation file:\n{e}")

        self.ctx["annotations"] = annotations
        self.ctx["metadata"]["writers"] = list(writers)
        self.ctx["metadata"]["annotation_count"] = len(annotations)

    # ---- format-specific parsers ----

    @staticmethod
    def _parse_iam_annotation_file(path: str):
        """Parse an IAM-format .txt annotation file."""
        annotations: list = []
        writers: set = set()
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 8:
                    text = " ".join(parts[8:]) if len(parts) > 8 else parts[7]
                    annotations.append({
                        "image_id": parts[0],
                        "status": parts[1],
                        "writer": parts[2],
                        "bbox": parts[3:7],
                        "label": text,
                    })
                    writers.add(parts[2])
        return annotations, writers

    @staticmethod
    def _parse_coco_annotation_file(path: str):
        """Parse a COCO-JSON annotation file."""
        annotations: list = []
        writers: set = set()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "annotations" in data:
            cat_map = {c["id"]: c.get("name", "?")
                       for c in data.get("categories", [])}
            img_map = {im["id"]: im.get("file_name", "")
                       for im in data.get("images", [])}
            for ann in data["annotations"]:
                img_id = ann.get("image_id")
                annotations.append({
                    "image_id": img_map.get(img_id, img_id),
                    "label": cat_map.get(ann.get("category_id"), ""),
                    "bbox": ann.get("bbox"),
                    "text": ann.get("attributes", {}).get("text", ""),
                })
        elif isinstance(data, list):
            annotations = data
        return annotations, writers

    @staticmethod
    def _parse_yolo_annotations(image_dir: str, images: List[str]):
        """Parse YOLO per-image .txt annotation files.

        Each image ``img.jpg`` has a corresponding ``img.txt`` with lines:
        ``class_id x_center y_center width height`` (normalised 0-1).
        A ``classes.txt`` in the same directory maps class IDs to labels.
        """
        annotations: list = []
        writers: set = set()

        # Try to load class names
        classes_path = os.path.join(image_dir, "classes.txt")
        class_names: Dict[int, str] = {}
        if os.path.isfile(classes_path):
            with open(classes_path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    class_names[idx] = line.strip()

        for img_path in images:
            base = os.path.splitext(img_path)[0]
            txt_path = base + ".txt"
            if not os.path.isfile(txt_path):
                continue
            # Read image size for de-normalisation
            try:
                with Image.open(img_path) as im:
                    iw, ih = im.size
            except Exception:
                iw, ih = 0, 0
            with open(txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    cls_id = int(parts[0])
                    xc, yc, w, h = (float(parts[1]), float(parts[2]),
                                    float(parts[3]), float(parts[4]))
                    # Convert normalised coords to pixel values
                    abs_w = w * iw
                    abs_h = h * ih
                    abs_x = xc * iw - abs_w / 2
                    abs_y = yc * ih - abs_h / 2
                    annotations.append({
                        "image_id": os.path.basename(img_path),
                        "label": class_names.get(cls_id, str(cls_id)),
                        "bbox": [abs_x, abs_y, abs_w, abs_h],
                    })
        return annotations, writers

    @staticmethod
    def _parse_voc_annotations(image_dir: str, images: List[str]):
        """Parse Pascal VOC per-image .xml annotation files."""
        import xml.etree.ElementTree as ET

        annotations: list = []
        writers: set = set()

        for img_path in images:
            base = os.path.splitext(img_path)[0]
            xml_path = base + ".xml"
            if not os.path.isfile(xml_path):
                # Also try an Annotations/ sibling folder (common VOC layout)
                parent = os.path.dirname(img_path)
                ann_dir = os.path.join(os.path.dirname(parent), "Annotations")
                candidate = os.path.join(
                    ann_dir, os.path.splitext(os.path.basename(img_path))[0] + ".xml")
                if os.path.isfile(candidate):
                    xml_path = candidate
                else:
                    continue
            try:
                tree = ET.parse(xml_path)
            except Exception:
                continue
            root = tree.getroot()
            filename = img_path
            fn_el = root.find("filename")
            if fn_el is not None and fn_el.text:
                filename = fn_el.text
            for obj in root.findall("object"):
                name_el = obj.find("name")
                label = name_el.text if name_el is not None else "unknown"
                bb = obj.find("bndbox")
                if bb is None:
                    continue
                try:
                    xmin = float(bb.findtext("xmin", "0"))
                    ymin = float(bb.findtext("ymin", "0"))
                    xmax = float(bb.findtext("xmax", "0"))
                    ymax = float(bb.findtext("ymax", "0"))
                except ValueError:
                    continue
                annotations.append({
                    "image_id": os.path.basename(filename),
                    "label": label,
                    "bbox": [xmin, ymin, xmax - xmin, ymax - ymin],
                })
        return annotations, writers

    def _extract_metadata(self, images: List[str]):
        """Extract resolution, file size, etc. from images (run in thread)."""
        def _worker():
            total_size = 0
            widths, heights = [], []
            for p in images[:200]:  # sample up to 200
                try:
                    total_size += os.path.getsize(p)
                    with Image.open(p) as img:
                        w, h = img.size
                        widths.append(w)
                        heights.append(h)
                except Exception:
                    pass
            self.ctx["metadata"]["total_size_bytes"] = total_size
            if widths:
                self.ctx["metadata"]["avg_width"] = sum(widths) // len(widths)
                self.ctx["metadata"]["avg_height"] = sum(heights) // len(heights)
            self.ctx["metadata"]["image_count"] = len(images)

            # Update UI on main thread
            self.after(0, self._update_meta_cards)

        threading.Thread(target=_worker, daemon=True).start()

    def _update_meta_cards(self):
        meta = self.ctx["metadata"]
        self.meta_cards["images"].config(text=str(meta.get("image_count", 0)))
        ann_count = meta.get("annotation_count", len(self.ctx.get("annotations", [])))
        self.meta_cards["annotations"].config(text=str(ann_count) if ann_count else "None")
        w = meta.get("avg_width", 0)
        h = meta.get("avg_height", 0)
        self.meta_cards["resolution"].config(text=f"{w}×{h}" if w else "—")
        size_mb = meta.get("total_size_bytes", 0) / (1024 * 1024)
        self.meta_cards["size"].config(text=f"{size_mb:.1f} MB" if size_mb else "—")

    def _show_preview(self, images: List[str], has_annotations: bool):
        """Populate thumbnail grid, integrity report, and enable proceed."""
        self.status_var.set(
            f"✅ Loaded {len(images)} images"
            + (f" with {len(self.ctx['annotations'])} annotations" if has_annotations else " (no annotations)")
            + f"  —  Type: {self.ctx['type']}"
        )

        # Image preview
        self.preview_img_index = 0
        self._refresh_preview_image()

        # Integrity report
        report = self._run_integrity_check(images, has_annotations)
        self.integrity_text.config(state="normal")
        self.integrity_text.delete("1.0", tk.END)
        self.integrity_text.insert("1.0", report)
        self.integrity_text.config(state="disabled")

        # Enable detection controls
        self._enable_detection_buttons()

        # Enable the Next button in workflow nav bar
        self._enable_next_button()

    def _run_integrity_check(self, images, has_annotations) -> str:
        lines = []
        lines.append(f"📁 Source: {self.ctx['image_dir']}")
        lines.append(f"🖼️ Total images: {len(images)}")

        # Check for unreadable images
        bad = 0
        for p in images[:50]:
            try:
                Image.open(p).verify()
            except Exception:
                bad += 1
        if bad:
            lines.append(f"⚠️ {bad} images could not be read (sampled first 50)")
        else:
            lines.append("✅ All sampled images are readable")

        if has_annotations:
            ann_count = len(self.ctx["annotations"])
            lines.append(f"📝 Annotations: {ann_count}")
            writers = self.ctx["metadata"].get("writers", [])
            if writers:
                lines.append(f"✍️ Writers / styles: {len(writers)}")

            # Check image-annotation alignment
            ann_ids = {str(a.get("image_id", "")) for a in self.ctx["annotations"]}
            img_basenames = {os.path.splitext(os.path.basename(p))[0] for p in images}
            matched = ann_ids & img_basenames
            unmatched_ann = ann_ids - img_basenames
            unmatched_img = img_basenames - ann_ids
            if unmatched_ann:
                lines.append(f"⚠️ {len(unmatched_ann)} annotations without matching image")
            if unmatched_img:
                lines.append(f"ℹ️ {len(unmatched_img)} images without annotation")
            if matched:
                lines.append(f"✅ {len(matched)} matched image–annotation pairs")
        else:
            lines.append("ℹ️ No annotations — only image metadata & statistics will be available.")
            lines.append("   You can annotate images using the tool's detection & annotation workflow.")

        return "\n".join(lines)

    def _enable_next_button(self):
        """Enable the Next button in the workflow nav bar."""
        try:
            wm = getattr(S, "workflow_manager", None)
            if wm and hasattr(wm, "btn_next"):
                wm.btn_next.config(state="normal")
        except Exception:
            pass

    def _proceed(self):
        if self.on_loaded:
            self.on_loaded()

    # ------------------------------------------------------------------
    # Refresh (called when returning to this step)
    # ------------------------------------------------------------------

    def refresh(self, ctx: Dict[str, Any]):
        self.ctx = ctx

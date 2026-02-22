"""
Step 2 – Annotation Panel
Provides word, line, and character detection controls integrated
into the workflow wizard.  Delegates actual detection to the existing
functions in annotationgui.py and shows results in the existing containers.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable
from PIL import Image, ImageTk

import state as S


class AnnotationPanel(tk.Frame):
    """Annotation step - detection buttons + image preview + annotation status."""

    def __init__(self, parent: tk.Widget, colors: Dict[str, str],
                 dataset_ctx: Dict[str, Any]):
        super().__init__(parent, bg=colors["bg_dark"])
        self.colors = colors
        self.ctx = dataset_ctx
        self.preview_photo = None  # prevent GC

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=self.colors["bg_section"], pady=12, padx=15)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="✏️  Step 2 — Annotation",
                 font=("Segoe UI", 15, "bold"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Detect and annotate text in your images",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(side=tk.RIGHT)

        # Main body – two columns
        body = tk.Frame(self, bg=self.colors["bg_dark"])
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left column: image preview + navigation
        left = tk.Frame(body, bg=self.colors["bg_dark"])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self._build_preview(left)

        # Right column: detection controls + status
        right = tk.Frame(body, bg=self.colors["bg_dark"], width=340)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right.pack_propagate(False)

        self._build_detection_controls(right)
        self._build_params_section(right)
        self._build_annotation_status(right)

    # ---- Preview ---------------------------------------------------
    def _build_preview(self, parent):
        pf = tk.LabelFrame(parent, text=" 🖼️ Image Preview ",
                           font=("Segoe UI", 10, "bold"),
                           bg=self.colors["bg_section"],
                           fg=self.colors["text_light"])
        pf.pack(fill=tk.BOTH, expand=True)

        # Nav bar
        nav = tk.Frame(pf, bg=self.colors["bg_section"])
        nav.pack(fill=tk.X, padx=8, pady=(8, 4))

        self.btn_prev_img = tk.Button(nav, text="◀ Prev", command=self._prev_image,
                                      font=("Segoe UI", 9), bg=self.colors["secondary_bg"],
                                      fg=self.colors["text_light"], relief=tk.FLAT,
                                      padx=8, pady=2, cursor="hand2")
        self.btn_prev_img.pack(side=tk.LEFT)

        self.img_counter_var = tk.StringVar(value="No images loaded")
        tk.Label(nav, textvariable=self.img_counter_var,
                 font=("Segoe UI", 10, "bold"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT, expand=True)

        self.btn_next_img = tk.Button(nav, text="Next ▶", command=self._next_image,
                                      font=("Segoe UI", 9), bg=self.colors["secondary_bg"],
                                      fg=self.colors["text_light"], relief=tk.FLAT,
                                      padx=8, pady=2, cursor="hand2")
        self.btn_next_img.pack(side=tk.RIGHT)

        # Canvas
        self.canvas = tk.Canvas(pf, bg="#eef2f7", highlightthickness=1,
                                highlightbackground=self.colors["border"])
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.img_info_var = tk.StringVar(value="")
        tk.Label(pf, textvariable=self.img_info_var,
                 font=("Segoe UI", 9),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(padx=8, pady=(0, 6))

    # ---- Detection controls ----------------------------------------
    def _build_detection_controls(self, parent):
        det = tk.LabelFrame(parent, text=" 🔍 Detection ",
                            font=("Segoe UI", 10, "bold"),
                            bg=self.colors["bg_section"],
                            fg=self.colors["text_light"])
        det.pack(fill=tk.X, pady=(0, 8))

        info = tk.Label(det,
                        text="Choose a detection mode to segment and\n"
                             "annotate your document images.",
                        font=("Segoe UI", 9),
                        bg=self.colors["bg_section"],
                        fg=self.colors["text_muted"],
                        justify=tk.LEFT)
        info.pack(anchor="w", padx=10, pady=(8, 6))

        # WORD detection
        wf = tk.Frame(det, bg=self.colors["bg_section"])
        wf.pack(fill=tk.X, padx=10, pady=3)
        self.btn_word = tk.Button(
            wf, text="🎯 Detect Words", command=self._detect_words,
            font=("Segoe UI", 10, "bold"),
            bg="#e67e22", fg="white", activebackground="#d35400",
            relief=tk.FLAT, cursor="hand2", padx=10, pady=6)
        self.btn_word.pack(fill=tk.X)
        tk.Label(wf, text="Neural-network word segmentation",
                 font=("Segoe UI", 8), bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(anchor="w")

        # LINE detection
        lf = tk.Frame(det, bg=self.colors["bg_section"])
        lf.pack(fill=tk.X, padx=10, pady=3)
        self.btn_line = tk.Button(
            lf, text="📄 Detect Lines", command=self._detect_lines,
            font=("Segoe UI", 10, "bold"),
            bg="#2980b9", fg="white", activebackground="#1f6da0",
            relief=tk.FLAT, cursor="hand2", padx=10, pady=6)
        self.btn_line.pack(fill=tk.X)
        tk.Label(lf, text="Horizontal projection line segmentation",
                 font=("Segoe UI", 8), bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(anchor="w")

        # CHARACTER detection
        cf = tk.Frame(det, bg=self.colors["bg_section"])
        cf.pack(fill=tk.X, padx=10, pady=(3, 8))
        self.btn_char = tk.Button(
            cf, text="🔤 Detect Characters", command=self._detect_characters,
            font=("Segoe UI", 10, "bold"),
            bg="#8e44ad", fg="white", activebackground="#6c3483",
            relief=tk.FLAT, cursor="hand2", padx=10, pady=6)
        self.btn_char.pack(fill=tk.X)
        tk.Label(cf, text="Template matching on detected words",
                 font=("Segoe UI", 8), bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(anchor="w")

        # Segmentation mode indicator
        self.seg_mode_var = tk.StringVar(value="Mode: not chosen")
        tk.Label(det, textvariable=self.seg_mode_var,
                 font=("Segoe UI", 9, "italic"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(padx=10, pady=(0, 8))

    # ---- Scale & Padding -------------------------------------------
    def _build_params_section(self, parent):
        """Scale and Padding sliders."""
        params = tk.LabelFrame(parent, text=" ⚙️ Scale & Padding ",
                               font=("Segoe UI", 10, "bold"),
                               bg=self.colors["bg_section"],
                               fg=self.colors["text_light"])
        params.pack(fill=tk.X, pady=(0, 8))

        # Scale
        self.scale_label = tk.Label(
            params,
            text=f"🔎 Scale: {getattr(S, 'image_scale', 1.0):.1f}x",
            font=("Segoe UI", 9),
            bg=self.colors["bg_section"],
            fg=self.colors["text_light"], anchor="w")
        self.scale_label.pack(fill=tk.X, padx=10, pady=(8, 0))
        self.scale_slider = tk.Scale(
            params, from_=0.5, to=3.0, resolution=0.1,
            orient=tk.HORIZONTAL,
            bg=self.colors["bg_section"], fg=self.colors["text_light"],
            troughcolor=self.colors["bg_dark"],
            activebackground=self.colors.get("accent", "#007bff"),
            highlightthickness=0, sliderrelief=tk.FLAT,
            command=self._on_scale_change)
        self.scale_slider.set(getattr(S, 'image_scale', 1.0))
        self.scale_slider.pack(fill=tk.X, padx=10)

        # Padding
        self.padding_label = tk.Label(
            params,
            text=f"📏 Padding: {getattr(S, 'bbox_padding', 0)}px",
            font=("Segoe UI", 9),
            bg=self.colors["bg_section"],
            fg=self.colors["text_light"], anchor="w")
        self.padding_label.pack(fill=tk.X, padx=10, pady=(6, 0))
        self.padding_slider = tk.Scale(
            params, from_=-20, to=50, resolution=1,
            orient=tk.HORIZONTAL,
            bg=self.colors["bg_section"], fg=self.colors["text_light"],
            troughcolor=self.colors["bg_dark"],
            activebackground=self.colors.get("accent", "#007bff"),
            highlightthickness=0, sliderrelief=tk.FLAT,
            command=self._on_padding_change)
        self.padding_slider.set(getattr(S, 'bbox_padding', 0))
        self.padding_slider.pack(fill=tk.X, padx=10, pady=(0, 8))

    # ---- Annotation status -----------------------------------------
    def _build_annotation_status(self, parent):
        st = tk.LabelFrame(parent, text=" 📋 Annotation Status ",
                           font=("Segoe UI", 10, "bold"),
                           bg=self.colors["bg_section"],
                           fg=self.colors["text_light"])
        st.pack(fill=tk.BOTH, expand=True)

        self.status_text = tk.Text(st, font=("Segoe UI", 9),
                                   bg="white", fg=self.colors["text_light"],
                                   relief=tk.FLAT, wrap=tk.WORD, height=10,
                                   state=tk.DISABLED, padx=8, pady=6)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        btn_frame = tk.Frame(st, bg=self.colors["bg_section"])
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        tk.Button(btn_frame, text="🔄 Refresh Status",
                  command=self._refresh_status,
                  font=("Segoe UI", 9), bg=self.colors["secondary_bg"],
                  fg=self.colors["text_light"], relief=tk.FLAT,
                  padx=8, pady=3, cursor="hand2").pack(side=tk.LEFT)

        tk.Button(btn_frame, text="📝 Open Annotation View",
                  command=self._open_annotation_container,
                  font=("Segoe UI", 9, "bold"), bg=self.colors["accent"],
                  fg="white", relief=tk.FLAT,
                  padx=8, pady=3, cursor="hand2").pack(side=tk.RIGHT)

        self._refresh_status()

    # ------------------------------------------------------------------
    # Image navigation
    # ------------------------------------------------------------------
    def _get_images(self):
        """Return the image list from context or from shared state."""
        ctx_imgs = self.ctx.get("images", [])
        if ctx_imgs:
            return ctx_imgs
        if hasattr(S, "list_of_files") and S.list_of_files:
            return S.list_of_files
        return []

    def _current_index(self):
        return getattr(S, "pos", 0)

    def _prev_image(self):
        imgs = self._get_images()
        if not imgs:
            return
        idx = max(0, self._current_index() - 1)
        S.pos = idx
        self._show_current_image()

    def _next_image(self):
        imgs = self._get_images()
        if not imgs:
            return
        idx = min(len(imgs) - 1, self._current_index() + 1)
        S.pos = idx
        self._show_current_image()

    def _show_current_image(self):
        imgs = self._get_images()
        idx = self._current_index()
        if not imgs:
            self.img_counter_var.set("No images loaded")
            self.img_info_var.set("")
            self.canvas.delete("all")
            return
        idx = min(idx, len(imgs) - 1)
        self.img_counter_var.set(f"Image {idx + 1} / {len(imgs)}")

        path = imgs[idx]
        try:
            img = Image.open(path)
            self.img_info_var.set(
                f"{os.path.basename(path)}  |  {img.size[0]}×{img.size[1]}")
            # Fit to canvas
            self.canvas.update_idletasks()
            cw = max(self.canvas.winfo_width(), 300)
            ch = max(self.canvas.winfo_height(), 300)
            img.thumbnail((cw, ch), Image.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(cw // 2, ch // 2,
                                     image=self.preview_photo, anchor=tk.CENTER)
        except Exception as exc:
            self.img_info_var.set(f"Error: {exc}")

    # ------------------------------------------------------------------
    # Detection delegates
    # ------------------------------------------------------------------
    def _ensure_images_ready(self):
        """Make sure images are loaded into shared state for the
        legacy detection functions to pick up."""
        ctx_imgs = self.ctx.get("images", [])
        if ctx_imgs and (not S.list_of_files or S.list_of_files != ctx_imgs):
            S.list_of_files = list(ctx_imgs)
            S.pos = min(getattr(S, "pos", 0), len(ctx_imgs) - 1)
            S.pathDirectory = self.ctx.get("image_dir", "")
            # Set up output directories alongside the images
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
                "Please complete Step 1 (Dataset Ingestion) first.")
            return False
        return True

    def _detect_words(self):
        if not self._ensure_images_ready():
            return
        self.seg_mode_var.set("Mode: Word Detection 🎯")
        # Call the existing word detection function
        try:
            func = getattr(S, "_workflow_detect_words", None)
            if func:
                func()
            else:
                messagebox.showinfo(
                    "Word Detection",
                    "Word detection will run via the main detection engine.\n"
                    "Use the sidebar '🎯 Detect Words' button or press the "
                    "shortcut key while the workflow is active.")
        except Exception as e:
            messagebox.showerror("Detection Error", str(e))
        self._refresh_status()

    def _detect_lines(self):
        if not self._ensure_images_ready():
            return
        self.seg_mode_var.set("Mode: Line Detection 📄")
        try:
            func = getattr(S, "_workflow_detect_lines", None)
            if func:
                func()
            else:
                messagebox.showinfo(
                    "Line Detection",
                    "Line detection will run via the main detection engine.\n"
                    "Use the sidebar '📄 Detect Lines' button or press the "
                    "shortcut key while the workflow is active.")
        except Exception as e:
            messagebox.showerror("Detection Error", str(e))
        self._refresh_status()

    def _detect_characters(self):
        if not self._ensure_images_ready():
            return
        word_paths = getattr(S, "word_image_paths", [])
        if not word_paths:
            messagebox.showwarning(
                "Words Required",
                "Please run Word Detection first.\n"
                "Character detection works on detected word images.")
            return
        self.seg_mode_var.set("Mode: Character Detection 🔤")
        try:
            func = getattr(S, "_workflow_detect_chars", None)
            if func:
                func()
            else:
                messagebox.showinfo(
                    "Character Detection",
                    "Character detection will run via the main detection engine.\n"
                    "Use the sidebar '🔤 Detect Chars' button or press the "
                    "shortcut key while the workflow is active.")
        except Exception as e:
            messagebox.showerror("Detection Error", str(e))
        self._refresh_status()

    # ------------------------------------------------------------------
    # Scale & Padding helpers
    # ------------------------------------------------------------------
    def _on_scale_change(self, val):
        v = float(val)
        S.image_scale = v
        self.scale_label.config(text=f"🔎 Scale: {v:.1f}x")

    def _on_padding_change(self, val):
        v = int(float(val))
        S.bbox_padding = v
        self.padding_label.config(text=f"📏 Padding: {v}px")

    def _open_annotation_container(self):
        """Switch to the annotation container in the main GUI."""
        if hasattr(S, "annotation_container") and S.annotation_container:
            try:
                S.annotation_container.pack(expand=True, fill=tk.BOTH)
            except Exception:
                pass
        messagebox.showinfo(
            "Annotation",
            "The annotation view is accessible from the detection panels.\n"
            "Run detection first, then click 'Proceed to Annotation'.")

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def _refresh_status(self):
        lines = []
        imgs = self._get_images()
        lines.append(f"📷 Images loaded: {len(imgs)}")

        seg = getattr(S, "segmentation_mode", None)
        lines.append(f"🔧 Segmentation mode: {seg or 'not set'}")

        # Word detection
        word_bboxes = getattr(S, "word_bboxes", [])
        lines.append(f"🎯 Words detected: {len(word_bboxes)}")

        word_paths = getattr(S, "word_image_paths", [])
        lines.append(f"📁 Word images: {len(word_paths)}")

        # Line detection
        det_lines = getattr(S, "detected_lines", [])
        lines.append(f"📄 Lines detected: {len(det_lines)}")

        # Character detection
        char_boxes = getattr(S, "char_detected_boxes", [])
        lines.append(f"🔤 Characters detected: {len(char_boxes)}")

        # Annotation
        entries = getattr(S, "entries", [])
        filled = sum(1 for e in entries if hasattr(e, "get") and e.get())
        lines.append(f"📝 Annotation entries: {len(entries)} ({filled} filled)")

        ann_mode = getattr(S, "current_annotation_mode", None)
        if ann_mode:
            lines.append(f"✏️ Annotation mode: {ann_mode}")

        # Write into context for downstream steps
        self.ctx["annotations"] = {
            "word_bboxes": len(word_bboxes),
            "word_images": len(word_paths),
            "lines": len(det_lines),
            "characters": len(char_boxes),
            "entries": len(entries),
        }

        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, "\n".join(lines))
        self.status_text.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    def refresh(self, ctx):
        self.ctx = ctx
        self._show_current_image()
        self._refresh_status()

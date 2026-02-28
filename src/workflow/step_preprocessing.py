"""
Step 2 – Preprocessing Panel
Unified detection review interface with:
  - Image canvas with drawn bbox overlays (words + lines)
  - Vertical detected-bbox panel (scrollable list, edit, delete)
  - Horizontal manual annotation panel (manual add + mouse draw)
Runs detection on ingested images before passing to the Annotation stage.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

import cv2
import numpy as np
from PIL import Image, ImageTk

import state as S


class PreprocessingPanel(tk.Frame):
    """Preprocessing step — detect words & lines on loaded images."""

    def __init__(self, parent: tk.Widget, colors: Dict[str, str],
                 dataset_ctx: Dict[str, Any]):
        super().__init__(parent, bg=colors["bg_dark"])
        self.colors = colors
        self.ctx = dataset_ctx
        self.preview_photo = None          # prevent GC
        self._canvas_scale = 1.0
        self._canvas_offset = (0, 0)
        self._raw_cv_img = None            # current cv2 image (BGR)
        self._draw_state = {"start": None, "rect": None}
        self._view_zoom = 1.0              # viewport zoom (independent from detection scale)
        self._pan_state = {"start": None}  # for middle-mouse panning
        self._build_ui()

    # ==================================================================
    # UI LAYOUT
    # ==================================================================
    def _build_ui(self):
        # ── Header ─────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=self.colors["bg_section"], pady=8, padx=12)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Step 2 — Preprocessing",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT)
        tk.Label(hdr, text="Detect words, lines, and characters before annotation",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(side=tk.RIGHT)

        # ── Toolbar ────────────────────────────────────────────────────
        self._build_toolbar()

        # ── Main area (left canvas + right bbox panel) ─────────────────
        main = tk.Frame(self, bg=self.colors["bg_dark"])
        main.pack(fill=tk.BOTH, expand=True, padx=6, pady=(4, 0))

        # Left: image canvas with overlays
        left = tk.Frame(main, bg=self.colors["bg_dark"])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_canvas(left)

        # Right: detected bbox vertical panel
        right = tk.Frame(main, bg=self.colors["bg_section"], width=290)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right.pack_propagate(False)
        self._build_bbox_panel(right)

        # ── Bottom: manual annotation horizontal panel ─────────────────
        self._build_manual_panel()

        # ── Annotation type selector ───────────────────────────────────
        self._build_annotation_type_panel()

        # ── Annotation source selector ─────────────────────────────────
        self._build_annotation_source_panel()

    # ── Toolbar ────────────────────────────────────────────────────────
    def _build_toolbar(self):
        tb = tk.Frame(self, bg=self.colors["bg_section"])
        tb.pack(fill=tk.X, padx=6, pady=(4, 2))

        # Image navigation
        self.btn_prev = tk.Button(
            tb, text="<< Prev", command=self._prev_image,
            font=("Segoe UI", 9), bg=self.colors["secondary_bg"],
            fg=self.colors["text_light"], relief=tk.FLAT,
            padx=6, pady=2, cursor="hand2")
        self.btn_prev.pack(side=tk.LEFT, padx=(4, 2))

        self.counter_var = tk.StringVar(value="No images")
        tk.Label(tb, textvariable=self.counter_var,
                 font=("Segoe UI", 9, "bold"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT, padx=4)

        self.btn_next_img = tk.Button(
            tb, text="Next >>", command=self._next_image,
            font=("Segoe UI", 9), bg=self.colors["secondary_bg"],
            fg=self.colors["text_light"], relief=tk.FLAT,
            padx=6, pady=2, cursor="hand2")
        self.btn_next_img.pack(side=tk.LEFT, padx=(2, 8))

        # Separator
        tk.Frame(tb, bg=self.colors["border"], width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=4, pady=2)

        # Detection buttons
        self.btn_word = tk.Button(
            tb, text="Detect Words", command=self._detect_words,
            font=("Segoe UI", 9, "bold"),
            bg="#e67e22", fg="white", activebackground="#d35400",
            relief=tk.FLAT, cursor="hand2", padx=8, pady=2)
        self.btn_word.pack(side=tk.LEFT, padx=2)

        self.btn_line = tk.Button(
            tb, text="Detect Lines", command=self._detect_lines,
            font=("Segoe UI", 9, "bold"),
            bg="#2980b9", fg="white", activebackground="#1f6da0",
            relief=tk.FLAT, cursor="hand2", padx=8, pady=2)
        self.btn_line.pack(side=tk.LEFT, padx=2)

        self.btn_char = tk.Button(
            tb, text="Detect Characters", command=self._detect_characters,
            font=("Segoe UI", 9, "bold"),
            bg="#8e44ad", fg="white", activebackground="#6c3483",
            relief=tk.FLAT, cursor="hand2", padx=8, pady=2)
        self.btn_char.pack(side=tk.LEFT, padx=2)

        self.mode_var = tk.StringVar(value="")
        tk.Label(tb, textvariable=self.mode_var,
                 font=("Segoe UI", 8, "italic"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=6)

        # Separator
        tk.Frame(tb, bg=self.colors["border"], width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=4, pady=2)

        # Scale
        tk.Label(tb, text="Scale:", font=("Segoe UI", 8),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT, padx=(4, 1))
        self.scale_slider = tk.Scale(
            tb, from_=0.5, to=3.0, resolution=0.1,
            orient=tk.HORIZONTAL, length=80,
            bg=self.colors["bg_section"], fg=self.colors["text_light"],
            troughcolor=self.colors["bg_dark"],
            activebackground=self.colors.get("accent", "#007bff"),
            highlightthickness=0, sliderrelief=tk.FLAT, bd=0,
            command=self._on_scale_change)
        self.scale_slider.set(getattr(S, "image_scale", 1.0))
        self.scale_slider.pack(side=tk.LEFT)

        # Padding
        tk.Label(tb, text="Pad:", font=("Segoe UI", 8),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT, padx=(6, 1))
        self.padding_slider = tk.Scale(
            tb, from_=-20, to=50, resolution=1,
            orient=tk.HORIZONTAL, length=80,
            bg=self.colors["bg_section"], fg=self.colors["text_light"],
            troughcolor=self.colors["bg_dark"],
            activebackground=self.colors.get("accent", "#007bff"),
            highlightthickness=0, sliderrelief=tk.FLAT, bd=0,
            command=self._on_padding_change)
        self.padding_slider.set(getattr(S, "bbox_padding", 0))
        self.padding_slider.pack(side=tk.LEFT)

        # Separator
        tk.Frame(tb, bg=self.colors["border"], width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=4, pady=2)

        # Zoom controls
        tk.Label(tb, text="Zoom:", font=("Segoe UI", 8),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT, padx=(4, 1))
        tk.Button(tb, text="−", command=self._zoom_out,
                  font=("Segoe UI", 10, "bold"),
                  bg=self.colors["secondary_bg"],
                  fg=self.colors["text_light"], relief=tk.FLAT,
                  width=2, cursor="hand2").pack(side=tk.LEFT)
        self._zoom_var = tk.StringVar(value="100%")
        tk.Label(tb, textvariable=self._zoom_var,
                 font=("Segoe UI", 8, "bold"), width=5,
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT)
        tk.Button(tb, text="+", command=self._zoom_in,
                  font=("Segoe UI", 10, "bold"),
                  bg=self.colors["secondary_bg"],
                  fg=self.colors["text_light"], relief=tk.FLAT,
                  width=2, cursor="hand2").pack(side=tk.LEFT)
        tk.Button(tb, text="Fit", command=self._zoom_fit,
                  font=("Segoe UI", 8),
                  bg=self.colors["secondary_bg"],
                  fg=self.colors["text_light"], relief=tk.FLAT,
                  padx=4, cursor="hand2").pack(side=tk.LEFT, padx=(2, 0))

        # Refresh button
        tk.Button(tb, text="Refresh", command=self._full_refresh,
                  font=("Segoe UI", 8), bg=self.colors["secondary_bg"],
                  fg=self.colors["text_light"], relief=tk.FLAT,
                  padx=6, pady=1, cursor="hand2").pack(side=tk.RIGHT, padx=4)

        # Info label
        self.info_var = tk.StringVar(value="")
        tk.Label(tb, textvariable=self.info_var,
                 font=("Segoe UI", 8),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(side=tk.RIGHT, padx=4)

    # ── Image canvas with bbox overlays ────────────────────────────────
    def _build_canvas(self, parent):
        canvas_frame = tk.Frame(parent, bg=self.colors["bg_dark"])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Scrollbars
        self._h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self._v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(
            canvas_frame, bg="#eef2f7",
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            xscrollcommand=self._h_scroll.set,
            yscrollcommand=self._v_scroll.set)
        self._h_scroll.config(command=self.canvas.xview)
        self._v_scroll.config(command=self.canvas.yview)

        self._v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Mouse-draw bindings (left button)
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        # Mouse-wheel zoom
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)        # Windows / macOS
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)          # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)          # Linux scroll down

        # Middle-mouse panning
        self.canvas.bind("<ButtonPress-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_move)
        # Also support Ctrl+Left-drag as pan (more natural on some setups)
        self.canvas.bind("<Control-ButtonPress-1>", self._on_pan_start)
        self.canvas.bind("<Control-B1-Motion>", self._on_pan_move)

    # ── Right: Detected BBox Vertical Panel ────────────────────────────
    def _build_bbox_panel(self, parent):
        tk.Label(parent, text="Detected Bounding Boxes",
                 font=("Segoe UI", 10, "bold"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(fill=tk.X, pady=(6, 2), padx=6)

        # Tabs: Words | Lines
        tab_bar = tk.Frame(parent, bg=self.colors["bg_section"])
        tab_bar.pack(fill=tk.X, padx=6)
        self._bbox_tab = tk.StringVar(value="words")
        self.btn_tab_words = tk.Button(
            tab_bar, text="Words", font=("Segoe UI", 9, "bold"),
            bg=self.colors.get("accent", "#007bff"), fg="white",
            relief=tk.FLAT, cursor="hand2", padx=10, pady=2,
            command=lambda: self._switch_bbox_tab("words"))
        self.btn_tab_words.pack(side=tk.LEFT, padx=(0, 2))
        self.btn_tab_lines = tk.Button(
            tab_bar, text="Lines", font=("Segoe UI", 9),
            bg=self.colors["secondary_bg"], fg=self.colors["text_light"],
            relief=tk.FLAT, cursor="hand2", padx=10, pady=2,
            command=lambda: self._switch_bbox_tab("lines"))
        self.btn_tab_lines.pack(side=tk.LEFT, padx=(0, 2))
        self.btn_tab_chars = tk.Button(
            tab_bar, text="Chars", font=("Segoe UI", 9),
            bg=self.colors["secondary_bg"], fg=self.colors["text_light"],
            relief=tk.FLAT, cursor="hand2", padx=10, pady=2,
            command=lambda: self._switch_bbox_tab("chars"))
        self.btn_tab_chars.pack(side=tk.LEFT)

        # Status counters
        self.status_var = tk.StringVar(value="Words: 0  |  Lines: 0  |  Chars: 0")
        tk.Label(parent, textvariable=self.status_var,
                 font=("Segoe UI", 8),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(fill=tk.X, padx=6, pady=(2, 4))

        # Listbox + scrollbar
        list_frame = tk.Frame(parent, bg=self.colors["bg_section"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.bbox_listbox = tk.Listbox(
            list_frame, font=("Segoe UI", 9),
            bg="white", fg=self.colors["text_light"],
            selectbackground=self.colors.get("accent", "#007bff"),
            selectforeground="white",
            yscrollcommand=scrollbar.set, height=10)
        self.bbox_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.bbox_listbox.yview)
        self.bbox_listbox.bind("<<ListboxSelect>>", self._on_bbox_select)

        # ── Edit controls ──────────────────────────────────────────────
        edit_frame = tk.Frame(parent, bg=self.colors["bg_section"])
        edit_frame.pack(fill=tk.X, padx=6, pady=(0, 4))

        tk.Label(edit_frame, text="Edit Selected:",
                 font=("Segoe UI", 9, "bold"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(anchor="w")

        # Word edit row  (X, Y, W, H)
        self.word_edit_row = tk.Frame(edit_frame, bg=self.colors["bg_section"])
        self.word_edit_row.pack(fill=tk.X, pady=2)
        for lbl_text, attr in [("X", "edit_x"), ("Y", "edit_y"),
                                ("W", "edit_w"), ("H", "edit_h")]:
            tk.Label(self.word_edit_row, text=f"{lbl_text}:",
                     bg=self.colors["bg_section"],
                     fg=self.colors["text_light"],
                     font=("Segoe UI", 8)).pack(side=tk.LEFT)
            var = tk.StringVar()
            setattr(self, attr, var)
            tk.Entry(self.word_edit_row, textvariable=var, width=5,
                     font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=1)

        # Line edit row  (X1, Y1, X2, Y2)
        self.line_edit_row = tk.Frame(edit_frame, bg=self.colors["bg_section"])
        # (not packed yet — shown when Lines tab active)
        for lbl_text, attr in [("X1", "edit_lx1"), ("Y1", "edit_ly1"),
                                ("X2", "edit_lx2"), ("Y2", "edit_ly2")]:
            tk.Label(self.line_edit_row, text=f"{lbl_text}:",
                     bg=self.colors["bg_section"],
                     fg=self.colors["text_light"],
                     font=("Segoe UI", 8)).pack(side=tk.LEFT)
            var = tk.StringVar()
            setattr(self, attr, var)
            tk.Entry(self.line_edit_row, textvariable=var, width=5,
                     font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=1)

        # Char edit row  (X, Y, W, H, Label)
        self.char_edit_row = tk.Frame(edit_frame, bg=self.colors["bg_section"])
        # (not packed yet — shown when Chars tab active)
        for lbl_text, attr in [("X", "edit_cx"), ("Y", "edit_cy"),
                                ("W", "edit_cw"), ("H", "edit_ch")]:
            tk.Label(self.char_edit_row, text=f"{lbl_text}:",
                     bg=self.colors["bg_section"],
                     fg=self.colors["text_light"],
                     font=("Segoe UI", 8)).pack(side=tk.LEFT)
            var = tk.StringVar()
            setattr(self, attr, var)
            tk.Entry(self.char_edit_row, textvariable=var, width=5,
                     font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=1)
        tk.Label(self.char_edit_row, text="Lbl:",
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"],
                 font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.edit_clbl = tk.StringVar()
        tk.Entry(self.char_edit_row, textvariable=self.edit_clbl, width=6,
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=1)

        # Buttons
        btn_row = tk.Frame(edit_frame, bg=self.colors["bg_section"])
        btn_row.pack(fill=tk.X, pady=3)
        tk.Button(btn_row, text="Update", command=self._update_bbox,
                  bg=self.colors.get("accent", "#007bff"), fg="white",
                  font=("Segoe UI", 9), padx=8, relief=tk.FLAT,
                  cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row, text="Delete", command=self._delete_bbox,
                  bg="#dc3545", fg="white",
                  font=("Segoe UI", 9), padx=8, relief=tk.FLAT,
                  cursor="hand2").pack(side=tk.LEFT, padx=2)

        # default: show word edit row
        self._switch_bbox_tab("words")

    # ── Bottom: Manual Annotation Horizontal Panel ─────────────────────
    def _build_manual_panel(self):
        mf = tk.LabelFrame(self, text=" Manual Annotation ",
                           font=("Segoe UI", 10, "bold"),
                           bg=self.colors["bg_section"],
                           fg=self.colors["text_light"])
        mf.pack(fill=tk.X, padx=6, pady=(2, 6))

        inner = tk.Frame(mf, bg=self.colors["bg_section"])
        inner.pack(fill=tk.X, padx=8, pady=6)

        # Word manual row
        word_row = tk.Frame(inner, bg=self.colors["bg_section"])
        word_row.pack(fill=tk.X, pady=2)
        tk.Label(word_row, text="Add Word (x, y, w, h):",
                 font=("Segoe UI", 9), bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT)
        self.man_wx = tk.Entry(word_row, width=5, font=("Segoe UI", 9))
        self.man_wx.pack(side=tk.LEFT, padx=2)
        self.man_wy = tk.Entry(word_row, width=5, font=("Segoe UI", 9))
        self.man_wy.pack(side=tk.LEFT, padx=2)
        self.man_ww = tk.Entry(word_row, width=5, font=("Segoe UI", 9))
        self.man_ww.pack(side=tk.LEFT, padx=2)
        self.man_wh = tk.Entry(word_row, width=5, font=("Segoe UI", 9))
        self.man_wh.pack(side=tk.LEFT, padx=2)
        tk.Button(word_row, text="+ Add Word", command=self._add_word_manual,
                  bg="#28a745", fg="white",
                  font=("Segoe UI", 9, "bold"), padx=8, relief=tk.FLAT,
                  cursor="hand2").pack(side=tk.LEFT, padx=6)

        # Line manual row
        line_row = tk.Frame(inner, bg=self.colors["bg_section"])
        line_row.pack(fill=tk.X, pady=2)
        tk.Label(line_row, text="Add Line (x1, y1, x2, y2):",
                 font=("Segoe UI", 9), bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT)
        self.man_lx1 = tk.Entry(line_row, width=5, font=("Segoe UI", 9))
        self.man_lx1.pack(side=tk.LEFT, padx=2)
        self.man_ly1 = tk.Entry(line_row, width=5, font=("Segoe UI", 9))
        self.man_ly1.pack(side=tk.LEFT, padx=2)
        self.man_lx2 = tk.Entry(line_row, width=5, font=("Segoe UI", 9))
        self.man_lx2.pack(side=tk.LEFT, padx=2)
        self.man_ly2 = tk.Entry(line_row, width=5, font=("Segoe UI", 9))
        self.man_ly2.pack(side=tk.LEFT, padx=2)
        tk.Button(line_row, text="+ Add Line", command=self._add_line_manual,
                  bg="#28a745", fg="white",
                  font=("Segoe UI", 9, "bold"), padx=8, relief=tk.FLAT,
                  cursor="hand2").pack(side=tk.LEFT, padx=6)

        # Draw hint
        self.draw_mode_var = tk.StringVar(value="words")
        hint_row = tk.Frame(inner, bg=self.colors["bg_section"])
        hint_row.pack(fill=tk.X, pady=(4, 0))
        tk.Label(hint_row,
                 text="Draw on canvas with mouse  |  Drawing mode:",
                 font=("Segoe UI", 8),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"]).pack(side=tk.LEFT)
        tk.Radiobutton(hint_row, text="Word bbox", variable=self.draw_mode_var,
                       value="words", bg=self.colors["bg_section"],
                       fg=self.colors["text_light"],
                       selectcolor=self.colors["bg_dark"],
                       activebackground=self.colors["bg_section"],
                       font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=4)
        tk.Radiobutton(hint_row, text="Line region", variable=self.draw_mode_var,
                       value="lines", bg=self.colors["bg_section"],
                       fg=self.colors["text_light"],
                       selectcolor=self.colors["bg_dark"],
                       activebackground=self.colors["bg_section"],
                       font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=4)

    # ── Annotation Type Selector ──────────────────────────────────────
    def _build_annotation_type_panel(self):
        af = tk.LabelFrame(self, text=" Annotation Type ",
                           font=("Segoe UI", 10, "bold"),
                           bg=self.colors["bg_section"],
                           fg=self.colors["text_light"])
        af.pack(fill=tk.X, padx=6, pady=(0, 6))

        inner = tk.Frame(af, bg=self.colors["bg_section"])
        inner.pack(fill=tk.X, padx=10, pady=6)

        tk.Label(inner,
                 text="Select the annotation level for the next stage."
                      "  If your images are already cropped, choose the matching level.",
                 font=("Segoe UI", 9),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"],
                 wraplength=700, justify=tk.LEFT).pack(anchor="w", pady=(0, 6))

        self._annotation_type_var = tk.StringVar(
            value=getattr(S, "annotation_type", "word"))

        btn_row = tk.Frame(inner, bg=self.colors["bg_section"])
        btn_row.pack(fill=tk.X)

        options = [
            ("Line",      "line",      "#2980b9",
             "Annotate full text lines"),
            ("Word",      "word",      "#e67e22",
             "Annotate individual words"),
            ("Character", "character", "#8e44ad",
             "Annotate individual characters"),
        ]

        for label, value, color, tip in options:
            rb = tk.Radiobutton(
                btn_row, text=f"  {label}  ", variable=self._annotation_type_var,
                value=value,
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["bg_section"],
                fg=self.colors["text_light"],
                activebackground=self.colors["bg_section"],
                activeforeground=self.colors["text_light"],
                selectcolor=color,
                indicatoron=True,
                cursor="hand2",
                command=self._on_annotation_type_change)
            rb.pack(side=tk.LEFT, padx=(0, 8))
            tk.Label(btn_row, text=tip,
                     font=("Segoe UI", 8),
                     bg=self.colors["bg_section"],
                     fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=(0, 16))

    def _on_annotation_type_change(self):
        chosen = self._annotation_type_var.get()
        S.annotation_type = chosen
        self.ctx["annotation_type"] = chosen

    # ── Annotation source selector ─────────────────────────────────────
    def _build_annotation_source_panel(self):
        """Let the user choose whether annotation uses preprocessing
        crops (detection bbox images) or the original loaded images."""
        sf = tk.LabelFrame(self, text=" Annotation Source ",
                           font=("Segoe UI", 10, "bold"),
                           bg=self.colors["bg_section"],
                           fg=self.colors["text_light"])
        sf.pack(fill=tk.X, padx=6, pady=(0, 6))

        inner = tk.Frame(sf, bg=self.colors["bg_section"])
        inner.pack(fill=tk.X, padx=10, pady=6)

        tk.Label(inner,
                 text="Choose how images are fed into the Annotation stage.",
                 font=("Segoe UI", 9),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_muted"],
                 wraplength=700, justify=tk.LEFT).pack(anchor="w", pady=(0, 6))

        self._annotation_source_var = tk.StringVar(
            value=getattr(S, "annotation_source", "original"))

        btn_row = tk.Frame(inner, bg=self.colors["bg_section"])
        btn_row.pack(fill=tk.X)

        sources = [
            ("With Preprocessing", "preprocessing", "#27ae60",
             "Use detection crops (bbox images from word / line detection)"),
            ("Original Images",    "original",       "#7f8c8d",
             "Use the loaded images as-is, without detection"),
        ]

        for label, value, color, tip in sources:
            rb = tk.Radiobutton(
                btn_row, text=f"  {label}  ",
                variable=self._annotation_source_var,
                value=value,
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["bg_section"],
                fg=self.colors["text_light"],
                activebackground=self.colors["bg_section"],
                activeforeground=self.colors["text_light"],
                selectcolor=color,
                indicatoron=True,
                cursor="hand2",
                command=self._on_annotation_source_change)
            rb.pack(side=tk.LEFT, padx=(0, 8))
            tk.Label(btn_row, text=tip,
                     font=("Segoe UI", 8),
                     bg=self.colors["bg_section"],
                     fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=(0, 16))

    def _on_annotation_source_change(self):
        chosen = self._annotation_source_var.get()
        S.annotation_source = chosen
        self.ctx["annotation_source"] = chosen

    # ==================================================================
    # TAB SWITCHING
    # ==================================================================
    def _switch_bbox_tab(self, tab: str):
        self._bbox_tab.set(tab)
        accent = self.colors.get("accent", "#007bff")
        sec = self.colors["secondary_bg"]
        normal_font = ("Segoe UI", 9)
        bold_font = ("Segoe UI", 9, "bold")
        # Reset all tabs
        for btn in (self.btn_tab_words, self.btn_tab_lines, self.btn_tab_chars):
            btn.config(bg=sec, fg=self.colors["text_light"], font=normal_font)
        # Hide all edit rows
        self.word_edit_row.pack_forget()
        self.line_edit_row.pack_forget()
        self.char_edit_row.pack_forget()
        # Activate selected tab
        if tab == "words":
            self.btn_tab_words.config(bg=accent, fg="white", font=bold_font)
            self.word_edit_row.pack(fill=tk.X, pady=2)
        elif tab == "lines":
            self.btn_tab_lines.config(bg=accent, fg="white", font=bold_font)
            self.line_edit_row.pack(fill=tk.X, pady=2)
        else:  # chars
            self.btn_tab_chars.config(bg=accent, fg="white", font=bold_font)
            self.char_edit_row.pack(fill=tk.X, pady=2)
        self._refresh_bbox_list()
        self._redraw_image()

    # ==================================================================
    # HELPER — unpack line tuples (supports legacy 2-tuple & new 4-tuple)
    # ==================================================================
    def _unpack_line(self, line_t):
        """Return (x1, y1, x2, y2) regardless of stored format."""
        if len(line_t) == 4:
            return line_t
        # Legacy (y1, y2) — use full image width
        y1, y2 = line_t
        img_w = self._raw_cv_img.shape[1] if self._raw_cv_img is not None else 0
        return (0, y1, img_w, y2)

    # ==================================================================
    # BBOX LIST OPERATIONS
    # ==================================================================
    def _refresh_bbox_list(self):
        self.bbox_listbox.delete(0, tk.END)
        word_bboxes = getattr(S, "word_bboxes", [])
        det_lines = getattr(S, "detected_lines", [])
        char_boxes = getattr(S, "char_detected_boxes", [])
        self.status_var.set(
            f"Words: {len(word_bboxes)}  |  Lines: {len(det_lines)}  |  Chars: {len(char_boxes)}")
        tab = self._bbox_tab.get()
        if tab == "words":
            for i, (x, y, w, h) in enumerate(word_bboxes):
                self.bbox_listbox.insert(tk.END,
                    f"#{i+1}: ({x}, {y}, {w} x {h})")
        elif tab == "lines":
            for i, line_t in enumerate(det_lines):
                x1, y1, x2, y2 = self._unpack_line(line_t)
                self.bbox_listbox.insert(tk.END,
                    f"Line #{i+1}: ({x1},{y1})->({x2},{y2})")
        else:  # chars
            for i, cinfo in enumerate(char_boxes):
                coords = cinfo.get("coords", (0, 0, 0, 0))
                label = cinfo.get("label", "?")
                score = cinfo.get("score", 0)
                self.bbox_listbox.insert(tk.END,
                    f"#{i+1}: '{label}' ({coords[0]},{coords[1]},{coords[2]}x{coords[3]}) {score:.0%}")

    def _on_bbox_select(self, _event=None):
        sel = self.bbox_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        tab = self._bbox_tab.get()
        if tab == "words":
            bboxes = getattr(S, "word_bboxes", [])
            if idx < len(bboxes):
                x, y, w, h = bboxes[idx]
                self.edit_x.set(str(x))
                self.edit_y.set(str(y))
                self.edit_w.set(str(w))
                self.edit_h.set(str(h))
        elif tab == "lines":
            lines = getattr(S, "detected_lines", [])
            if idx < len(lines):
                x1, y1, x2, y2 = self._unpack_line(lines[idx])
                self.edit_lx1.set(str(x1))
                self.edit_ly1.set(str(y1))
                self.edit_lx2.set(str(x2))
                self.edit_ly2.set(str(y2))
        else:  # chars
            chars = getattr(S, "char_detected_boxes", [])
            if idx < len(chars):
                c = chars[idx]
                coords = c.get("coords", (0, 0, 0, 0))
                self.edit_cx.set(str(coords[0]))
                self.edit_cy.set(str(coords[1]))
                self.edit_cw.set(str(coords[2]))
                self.edit_ch.set(str(coords[3]))
                self.edit_clbl.set(c.get("label", ""))
        self._redraw_image(highlight_idx=idx)

    def _update_bbox(self):
        sel = self.bbox_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        tab = self._bbox_tab.get()
        try:
            if tab == "words":
                bboxes = getattr(S, "word_bboxes", [])
                if idx < len(bboxes):
                    x = int(self.edit_x.get())
                    y = int(self.edit_y.get())
                    w = int(self.edit_w.get())
                    h = int(self.edit_h.get())
                    S.word_bboxes[idx] = (x, y, w, h)
            elif tab == "lines":
                lines = getattr(S, "detected_lines", [])
                if idx < len(lines):
                    x1 = int(self.edit_lx1.get())
                    y1 = int(self.edit_ly1.get())
                    x2 = int(self.edit_lx2.get())
                    y2 = int(self.edit_ly2.get())
                    S.detected_lines[idx] = (x1, y1, x2, y2)
            else:  # chars
                chars = getattr(S, "char_detected_boxes", [])
                if idx < len(chars):
                    cx = int(self.edit_cx.get())
                    cy = int(self.edit_cy.get())
                    cw = int(self.edit_cw.get())
                    ch = int(self.edit_ch.get())
                    lbl = self.edit_clbl.get().strip()
                    S.char_detected_boxes[idx]["coords"] = (cx, cy, cw, ch)
                    S.char_detected_boxes[idx]["label"] = lbl
        except ValueError:
            messagebox.showerror("Error", "Enter valid integer coordinates.")
            return
        self._refresh_bbox_list()
        self._redraw_image()

    def _delete_bbox(self):
        sel = self.bbox_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        tab = self._bbox_tab.get()
        if tab == "words":
            label = f"word bbox #{idx+1}"
        elif tab == "lines":
            label = f"line #{idx+1}"
        else:
            label = f"char #{idx+1}"
        if not messagebox.askyesno("Delete", f"Delete {label}?"):
            return
        if tab == "words":
            bboxes = getattr(S, "word_bboxes", [])
            if idx < len(bboxes):
                S.word_bboxes.pop(idx)
        elif tab == "lines":
            lines = getattr(S, "detected_lines", [])
            if idx < len(lines):
                S.detected_lines.pop(idx)
        else:  # chars
            chars = getattr(S, "char_detected_boxes", [])
            if idx < len(chars):
                S.char_detected_boxes.pop(idx)
        self._refresh_bbox_list()
        self._redraw_image()

    # ==================================================================
    # MANUAL ADD
    # ==================================================================
    def _add_word_manual(self):
        try:
            x = int(self.man_wx.get())
            y = int(self.man_wy.get())
            w = int(self.man_ww.get())
            h = int(self.man_wh.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid integer values.")
            return
        if not hasattr(S, "word_bboxes") or S.word_bboxes is None:
            S.word_bboxes = []
        S.word_bboxes.append((x, y, w, h))
        for e in (self.man_wx, self.man_wy, self.man_ww, self.man_wh):
            e.delete(0, tk.END)
        self._switch_bbox_tab("words")
        self._redraw_image()

    def _add_line_manual(self):
        try:
            x1 = int(self.man_lx1.get())
            y1 = int(self.man_ly1.get())
            x2 = int(self.man_lx2.get())
            y2 = int(self.man_ly2.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid integer values.")
            return
        if not hasattr(S, "detected_lines") or S.detected_lines is None:
            S.detected_lines = []
        S.detected_lines.append((x1, y1, x2, y2))
        S.detected_lines.sort(key=lambda t: t[1])
        for e in (self.man_lx1, self.man_ly1, self.man_lx2, self.man_ly2):
            e.delete(0, tk.END)
        self._switch_bbox_tab("lines")
        self._redraw_image()

    # ==================================================================
    # MOUSE DRAWING ON CANVAS
    # ==================================================================
    def _on_canvas_press(self, event):
        # Ignore if Ctrl is held (used for panning)
        if event.state & 0x4:
            return
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        self._draw_state["start"] = (cx, cy)
        if self.draw_mode_var.get() == "lines":
            self._draw_state["rect"] = self.canvas.create_rectangle(
                0, cy, self.canvas.winfo_width(), cy,
                outline="blue", width=2, dash=(4, 2))
        else:
            self._draw_state["rect"] = self.canvas.create_rectangle(
                cx, cy, cx, cy,
                outline="blue", width=2, dash=(4, 2))

    def _on_canvas_drag(self, event):
        r = self._draw_state.get("rect")
        s = self._draw_state.get("start")
        if not r or not s:
            return
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        if self.draw_mode_var.get() == "lines":
            y1, y2 = s[1], cy
            self.canvas.coords(r, 0, min(y1, y2),
                               self.canvas.winfo_width(), max(y1, y2))
        else:
            self.canvas.coords(r, s[0], s[1], cx, cy)

    def _on_canvas_release(self, event):
        r = self._draw_state.get("rect")
        s = self._draw_state.get("start")
        if not r or not s:
            return
        self.canvas.delete(r)
        self._draw_state["start"] = None
        self._draw_state["rect"] = None

        scale = self._canvas_scale
        ox, oy = self._canvas_offset
        if scale == 0:
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        if self.draw_mode_var.get() == "lines":
            iy1 = int((min(s[1], cy) - oy) / scale)
            iy2 = int((max(s[1], cy) - oy) / scale)
            if iy2 - iy1 > 5:
                if not hasattr(S, "detected_lines") or S.detected_lines is None:
                    S.detected_lines = []
                # Use full image width for mouse-drawn lines
                img_h_raw, img_w_raw = self._raw_cv_img.shape[:2] if self._raw_cv_img is not None else (0, 0)
                S.detected_lines.append((0, iy1, img_w_raw, iy2))
                S.detected_lines.sort(key=lambda t: t[1])
                self._switch_bbox_tab("lines")
                self._redraw_image()
        else:
            ix1 = int((min(s[0], cx) - ox) / scale)
            iy1 = int((min(s[1], cy) - oy) / scale)
            ix2 = int((max(s[0], cx) - ox) / scale)
            iy2 = int((max(s[1], cy) - oy) / scale)
            w, h = ix2 - ix1, iy2 - iy1
            if w > 5 and h > 5:
                if not hasattr(S, "word_bboxes") or S.word_bboxes is None:
                    S.word_bboxes = []
                S.word_bboxes.append((ix1, iy1, w, h))
                self._switch_bbox_tab("words")
                self._redraw_image()

    # ==================================================================
    # IMAGE NAVIGATION
    # ==================================================================
    def _get_images(self):
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
        S.pos = max(0, self._current_index() - 1)
        self._load_current_image()

    def _next_image(self):
        imgs = self._get_images()
        if not imgs:
            return
        S.pos = min(len(imgs) - 1, self._current_index() + 1)
        self._load_current_image()

    def _load_current_image(self):
        """Load the current image into _raw_cv_img and redraw."""
        imgs = self._get_images()
        idx = self._current_index()
        if not imgs:
            self.counter_var.set("No images")
            self.info_var.set("")
            self.canvas.delete("all")
            self._raw_cv_img = None
            return
        idx = min(idx, len(imgs) - 1)
        self.counter_var.set(f"Image {idx + 1} / {len(imgs)}")
        path = imgs[idx]
        try:
            img = cv2.imread(path)
            if img is None:
                self.info_var.set(f"Cannot read: {os.path.basename(path)}")
                self._raw_cv_img = None
                return
            self._raw_cv_img = img
            h, w = img.shape[:2]
            self.info_var.set(f"{os.path.basename(path)}  |  {w} x {h}")
        except Exception as exc:
            self.info_var.set(f"Error: {exc}")
            self._raw_cv_img = None
        self._redraw_image()
        self._refresh_bbox_list()

    # ==================================================================
    # CANVAS RENDERING (image + bbox overlays)
    # ==================================================================
    def _redraw_image(self, highlight_idx=None):
        """Draw current image with word & line bboxes overlaid."""
        self.canvas.delete("all")
        if self._raw_cv_img is None:
            return

        img_rgb = cv2.cvtColor(self._raw_cv_img, cv2.COLOR_BGR2RGB).copy()
        active_tab = self._bbox_tab.get()
        pad = getattr(S, "bbox_padding", 0)
        img_h, img_w = img_rgb.shape[:2]

        # Detection may have run on a scaled copy of the image.
        # Bbox coordinates are in that scaled space, so map them
        # back to original-image coordinates before drawing.
        det_scale = getattr(S, "detection_scale", 1.0)
        if det_scale == 0:
            det_scale = 1.0

        # Draw word bboxes (with padding applied visually)
        word_bboxes = getattr(S, "word_bboxes", [])
        for i, (bx, by, bw, bh) in enumerate(word_bboxes):
            # Map from detection space → original image space
            x = int(bx / det_scale)
            y = int(by / det_scale)
            w = int(bw / det_scale)
            h = int(bh / det_scale)
            # Apply padding: expand bbox outward, clamp to image bounds
            px = max(x - pad, 0)
            py = max(y - pad, 0)
            px2 = min(x + w + pad, img_w)
            py2 = min(y + h + pad, img_h)
            if active_tab == "words" and i == highlight_idx:
                color, thickness = (0, 255, 0), 3
            else:
                color, thickness = (255, 100, 100), 2
            cv2.rectangle(img_rgb, (px, py), (px2, py2), color, thickness)
            cv2.putText(img_rgb, f"W{i+1}", (px + 2, py + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

        # Draw line regions (with padding applied visually)
        det_lines = getattr(S, "detected_lines", [])
        for i, line_t in enumerate(det_lines):
            lx1, ly1, lx2, ly2 = self._unpack_line(line_t)
            # Map from detection space → original image space
            x1 = int(lx1 / det_scale)
            y1 = int(ly1 / det_scale)
            x2 = int(lx2 / det_scale)
            y2 = int(ly2 / det_scale)
            # Apply padding: expand line region, clamp to image bounds
            px1 = max(x1 - pad, 0)
            py1 = max(y1 - pad, 0)
            px2 = min(x2 + pad, img_w)
            py2 = min(y2 + pad, img_h)
            if active_tab == "lines" and i == highlight_idx:
                color, thickness = (0, 255, 0), 3
            else:
                color, thickness = (30, 144, 255), 2
            cv2.rectangle(img_rgb, (px1, py1), (px2, py2), color, thickness)
            cv2.putText(img_rgb, f"L{i+1}", (px1 + 5, py1 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Draw character bboxes
        char_boxes = getattr(S, "char_detected_boxes", [])
        for i, cinfo in enumerate(char_boxes):
            coords = cinfo.get("coords", (0, 0, 0, 0))
            cx, cy, cw, ch = coords
            # Map character coords from detection space to original image space
            try:
                cx = int(cx / det_scale)
                cy = int(cy / det_scale)
                cw = int(cw / det_scale)
                ch = int(ch / det_scale)
            except Exception:
                # fallback to original values if det_scale invalid
                cx, cy, cw, ch = int(cx), int(cy), int(cw), int(ch)
            if active_tab == "chars" and i == highlight_idx:
                color, thickness = (0, 255, 0), 3
            else:
                color, thickness = (180, 0, 255), 2
            cv2.rectangle(img_rgb, (int(cx), int(cy)),
                          (int(cx + cw), int(cy + ch)), color, thickness)
            label = cinfo.get("label", "")
            cv2.putText(img_rgb, label, (int(cx), max(int(cy) - 3, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # Resize to fit canvas, applying viewport zoom
        self.canvas.update_idletasks()
        cw = max(self.canvas.winfo_width(), 300)
        ch = max(self.canvas.winfo_height(), 300)
        fit_scale = min(cw / img_w, ch / img_h, 1.0)
        scale = fit_scale * self._view_zoom
        new_w, new_h = int(img_w * scale), int(img_h * scale)

        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        resized = cv2.resize(img_rgb, (new_w, new_h), interpolation=interp)
        pil_img = Image.fromarray(resized)
        self.preview_photo = ImageTk.PhotoImage(pil_img)

        x_off = max((cw - new_w) // 2, 0)
        y_off = max((ch - new_h) // 2, 0)
        self.canvas.create_image(x_off, y_off, anchor=tk.NW,
                                 image=self.preview_photo)
        # Update scrollregion so the canvas can scroll when zoomed in
        sr_w = max(cw, new_w + x_off * 2)
        sr_h = max(ch, new_h + y_off * 2)
        self.canvas.config(scrollregion=(0, 0, sr_w, sr_h))

        self._canvas_scale = scale
        self._canvas_offset = (x_off, y_off)

    # ==================================================================
    # DETECTION DELEGATES  (run core logic in-panel, no container switch)
    # ==================================================================
    def _ensure_images_ready(self):
        ctx_imgs = self.ctx.get("images", [])
        if ctx_imgs and (not S.list_of_files or S.list_of_files != ctx_imgs):
            S.list_of_files = list(ctx_imgs)
            S.pos = min(getattr(S, "pos", 0), len(ctx_imgs) - 1)
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
                "Please complete Step 1 (Dataset Ingestion) first.")
            return False
        return True

    def _clear_previous_detections(self, clear_word_crops=False):
        """Remove all previous detection results so modes don't overlap.
        If clear_word_crops is True, also remove crops in out_dir."""
        S.word_bboxes = []
        S.detected_lines = []
        S.char_detected_boxes = []
        if clear_word_crops:
            out_dir = getattr(S, 'directoryout', None)
            if out_dir and os.path.isdir(out_dir):
                for f in os.listdir(out_dir):
                    fp = os.path.join(out_dir, f)
                    try:
                        if os.path.isfile(fp):
                            os.remove(fp)
                    except Exception:
                        pass

    def _detect_words(self):
        """Run word detection directly (core logic only, no UI switch)."""
        if not self._ensure_images_ready():
            return
        self._clear_previous_detections(clear_word_crops=True)
        self.mode_var.set("Word Detection")
        self.btn_word.config(state=tk.DISABLED, text="Detecting...")
        self.update_idletasks()
        try:
            from actions.save_file import save_file
            save_file()                       # populates S.word_bboxes etc.
        except Exception as e:
            messagebox.showerror("Detection Error", str(e))
            import traceback; traceback.print_exc()
        finally:
            self.btn_word.config(state=tk.NORMAL, text="Detect Words")
        # Ensure we stay in the preprocessing panel (undo any container
        # switching that save_file / display_word_bboxes_func may trigger)
        self._restore_workflow_view()
        self._switch_bbox_tab("words")
        self._load_current_image()

    def _detect_lines(self):
        """Run line detection directly (core logic only, no UI switch)."""
        if not self._ensure_images_ready():
            return
        self._clear_previous_detections(clear_word_crops=False)
        self.mode_var.set("Line Detection")
        self.btn_line.config(state=tk.DISABLED, text="Detecting...")
        self.update_idletasks()
        try:
            from actions.line_annotate import detect_text_lines
            imgs = self._get_images()
            idx = min(self._current_index(), len(imgs) - 1)
            path = imgs[idx]
            img = cv2.imread(path)
            if img is None:
                messagebox.showerror("Error", f"Cannot read image:\n{path}")
                return
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            lines = detect_text_lines(img_gray)
            S.detected_lines = lines
            S.line_image_path = path
            self._raw_cv_img = img           # refresh canvas source
        except Exception as e:
            messagebox.showerror("Detection Error", str(e))
            import traceback; traceback.print_exc()
        finally:
            self.btn_line.config(state=tk.NORMAL, text="Detect Lines")
        self._restore_workflow_view()
        self._switch_bbox_tab("lines")
        self._load_current_image()

    def _detect_characters(self):
        """Run character detection via the main engine.
        Works on word images when available, otherwise on the input image."""
        if not self._ensure_images_ready():
            return
        self._clear_previous_detections(clear_word_crops=False)
        self.mode_var.set("Character Detection")
        self.btn_char.config(state=tk.DISABLED, text="Detecting...")
        self.update_idletasks()
        try:
            func = getattr(S, "_workflow_detect_chars", None)
            if func:
                func()
            else:
                messagebox.showinfo(
                    "Character Detection",
                    "Character detection engine not available.")
        except Exception as e:
            messagebox.showerror("Detection Error", str(e))
            import traceback; traceback.print_exc()
        finally:
            self.btn_char.config(state=tk.NORMAL, text="Detect Characters")
        self._restore_workflow_view()
        self._switch_bbox_tab("chars")
        self._load_current_image()

    def _restore_workflow_view(self):
        """Make sure the workflow container stays visible after detection
        (undo any pack_forget that the core detection code may have done)."""
        try:
            wm = getattr(S, "workflow_manager", None)
            if wm and hasattr(wm, "container"):
                c = wm.container
                if c.winfo_exists() and not c.winfo_ismapped():
                    c.pack(expand=True, fill=tk.BOTH)
        except Exception:
            pass

    # ==================================================================
    # SCALE & PADDING
    # ==================================================================
    def _on_scale_change(self, val):
        S.image_scale = float(val)
        self._redraw_image()

    def _on_padding_change(self, val):
        S.bbox_padding = int(float(val))
        self._redraw_image()

    # ==================================================================
    # VIEWPORT ZOOM & PAN
    # ==================================================================
    _ZOOM_LEVELS = [0.25, 0.33, 0.5, 0.67, 0.75, 1.0, 1.25, 1.5,
                    2.0, 2.5, 3.0, 4.0, 5.0]

    def _update_zoom_label(self):
        pct = int(round(self._view_zoom * 100))
        self._zoom_var.set(f"{pct}%")

    def _zoom_in(self):
        for z in self._ZOOM_LEVELS:
            if z > self._view_zoom + 0.01:
                self._view_zoom = z
                break
        else:
            self._view_zoom = self._ZOOM_LEVELS[-1]
        self._update_zoom_label()
        self._redraw_image()

    def _zoom_out(self):
        for z in reversed(self._ZOOM_LEVELS):
            if z < self._view_zoom - 0.01:
                self._view_zoom = z
                break
        else:
            self._view_zoom = self._ZOOM_LEVELS[0]
        self._update_zoom_label()
        self._redraw_image()

    def _zoom_fit(self):
        self._view_zoom = 1.0
        self._update_zoom_label()
        self._redraw_image()

    def _on_mouse_wheel(self, event):
        # Determine scroll direction
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self._zoom_in()
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            self._zoom_out()

    def _on_pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)
        return "break"   # prevent left-button draw when Ctrl held

    def _on_pan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        return "break"

    # ==================================================================
    # FULL REFRESH
    # ==================================================================
    def _full_refresh(self):
        self._load_current_image()

    def refresh(self, ctx):
        """Called when returning to this step."""
        self.ctx = ctx
        # Sync annotation type from context or state
        ann_type = ctx.get("annotation_type",
                           getattr(S, "annotation_type", "word"))
        if hasattr(self, "_annotation_type_var"):
            self._annotation_type_var.set(ann_type)
        S.annotation_type = ann_type
        ctx["annotation_type"] = ann_type
        # Sync annotation source
        ann_src = ctx.get("annotation_source",
                          getattr(S, "annotation_source", "original"))
        if hasattr(self, "_annotation_source_var"):
            self._annotation_source_var.set(ann_src)
        S.annotation_source = ann_src
        ctx["annotation_source"] = ann_src
        self._load_current_image()

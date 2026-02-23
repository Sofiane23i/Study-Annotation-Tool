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
        tk.Label(hdr, text="Detect words and lines before annotation",
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
        self.canvas = tk.Canvas(parent, bg="#eef2f7",
                                highlightthickness=1,
                                highlightbackground=self.colors["border"])
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        # Mouse-draw bindings
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

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
        self.btn_tab_lines.pack(side=tk.LEFT)

        # Status counters
        self.status_var = tk.StringVar(value="Words: 0  |  Lines: 0")
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

        # Line edit row  (Y Start, Y End)
        self.line_edit_row = tk.Frame(edit_frame, bg=self.colors["bg_section"])
        # (not packed yet — shown when Lines tab active)
        tk.Label(self.line_edit_row, text="Y Start:",
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"],
                 font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.edit_y1 = tk.StringVar()
        tk.Entry(self.line_edit_row, textvariable=self.edit_y1, width=6,
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=1)
        tk.Label(self.line_edit_row, text="Y End:",
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"],
                 font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(4, 0))
        self.edit_y2 = tk.StringVar()
        tk.Entry(self.line_edit_row, textvariable=self.edit_y2, width=6,
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
        tk.Label(line_row, text="Add Line (y_start, y_end):",
                 font=("Segoe UI", 9), bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT)
        self.man_ly1 = tk.Entry(line_row, width=6, font=("Segoe UI", 9))
        self.man_ly1.pack(side=tk.LEFT, padx=2)
        self.man_ly2 = tk.Entry(line_row, width=6, font=("Segoe UI", 9))
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

    # ==================================================================
    # TAB SWITCHING
    # ==================================================================
    def _switch_bbox_tab(self, tab: str):
        self._bbox_tab.set(tab)
        accent = self.colors.get("accent", "#007bff")
        sec = self.colors["secondary_bg"]
        if tab == "words":
            self.btn_tab_words.config(bg=accent, fg="white",
                                      font=("Segoe UI", 9, "bold"))
            self.btn_tab_lines.config(bg=sec, fg=self.colors["text_light"],
                                      font=("Segoe UI", 9))
            self.line_edit_row.pack_forget()
            self.word_edit_row.pack(fill=tk.X, pady=2)
        else:
            self.btn_tab_lines.config(bg=accent, fg="white",
                                      font=("Segoe UI", 9, "bold"))
            self.btn_tab_words.config(bg=sec, fg=self.colors["text_light"],
                                      font=("Segoe UI", 9))
            self.word_edit_row.pack_forget()
            self.line_edit_row.pack(fill=tk.X, pady=2)
        self._refresh_bbox_list()
        self._redraw_image()

    # ==================================================================
    # BBOX LIST OPERATIONS
    # ==================================================================
    def _refresh_bbox_list(self):
        self.bbox_listbox.delete(0, tk.END)
        word_bboxes = getattr(S, "word_bboxes", [])
        det_lines = getattr(S, "detected_lines", [])
        self.status_var.set(
            f"Words: {len(word_bboxes)}  |  Lines: {len(det_lines)}")
        if self._bbox_tab.get() == "words":
            for i, (x, y, w, h) in enumerate(word_bboxes):
                self.bbox_listbox.insert(tk.END,
                    f"#{i+1}: ({x}, {y}, {w} x {h})")
        else:
            for i, (y1, y2) in enumerate(det_lines):
                height = y2 - y1
                self.bbox_listbox.insert(tk.END,
                    f"Line #{i+1}: Y={y1} -> {y2}  (h={height})")

    def _on_bbox_select(self, _event=None):
        sel = self.bbox_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if self._bbox_tab.get() == "words":
            bboxes = getattr(S, "word_bboxes", [])
            if idx < len(bboxes):
                x, y, w, h = bboxes[idx]
                self.edit_x.set(str(x))
                self.edit_y.set(str(y))
                self.edit_w.set(str(w))
                self.edit_h.set(str(h))
        else:
            lines = getattr(S, "detected_lines", [])
            if idx < len(lines):
                y1, y2 = lines[idx]
                self.edit_y1.set(str(y1))
                self.edit_y2.set(str(y2))
        self._redraw_image(highlight_idx=idx)

    def _update_bbox(self):
        sel = self.bbox_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        try:
            if self._bbox_tab.get() == "words":
                bboxes = getattr(S, "word_bboxes", [])
                if idx < len(bboxes):
                    x = int(self.edit_x.get())
                    y = int(self.edit_y.get())
                    w = int(self.edit_w.get())
                    h = int(self.edit_h.get())
                    S.word_bboxes[idx] = (x, y, w, h)
            else:
                lines = getattr(S, "detected_lines", [])
                if idx < len(lines):
                    y1 = int(self.edit_y1.get())
                    y2 = int(self.edit_y2.get())
                    S.detected_lines[idx] = (y1, y2)
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
        label = f"word bbox #{idx+1}" if tab == "words" else f"line #{idx+1}"
        if not messagebox.askyesno("Delete", f"Delete {label}?"):
            return
        if tab == "words":
            bboxes = getattr(S, "word_bboxes", [])
            if idx < len(bboxes):
                S.word_bboxes.pop(idx)
        else:
            lines = getattr(S, "detected_lines", [])
            if idx < len(lines):
                S.detected_lines.pop(idx)
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
            y1 = int(self.man_ly1.get())
            y2 = int(self.man_ly2.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid integer values.")
            return
        if not hasattr(S, "detected_lines") or S.detected_lines is None:
            S.detected_lines = []
        S.detected_lines.append((y1, y2))
        S.detected_lines.sort(key=lambda t: t[0])
        self.man_ly1.delete(0, tk.END)
        self.man_ly2.delete(0, tk.END)
        self._switch_bbox_tab("lines")
        self._redraw_image()

    # ==================================================================
    # MOUSE DRAWING ON CANVAS
    # ==================================================================
    def _on_canvas_press(self, event):
        self._draw_state["start"] = (event.x, event.y)
        if self.draw_mode_var.get() == "lines":
            self._draw_state["rect"] = self.canvas.create_rectangle(
                0, event.y, self.canvas.winfo_width(), event.y,
                outline="blue", width=2, dash=(4, 2))
        else:
            self._draw_state["rect"] = self.canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline="blue", width=2, dash=(4, 2))

    def _on_canvas_drag(self, event):
        r = self._draw_state.get("rect")
        s = self._draw_state.get("start")
        if not r or not s:
            return
        if self.draw_mode_var.get() == "lines":
            y1, y2 = s[1], event.y
            self.canvas.coords(r, 0, min(y1, y2),
                               self.canvas.winfo_width(), max(y1, y2))
        else:
            self.canvas.coords(r, s[0], s[1], event.x, event.y)

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

        if self.draw_mode_var.get() == "lines":
            iy1 = int((min(s[1], event.y) - oy) / scale)
            iy2 = int((max(s[1], event.y) - oy) / scale)
            if iy2 - iy1 > 5:
                if not hasattr(S, "detected_lines") or S.detected_lines is None:
                    S.detected_lines = []
                S.detected_lines.append((iy1, iy2))
                S.detected_lines.sort(key=lambda t: t[0])
                self._switch_bbox_tab("lines")
                self._redraw_image()
        else:
            ix1 = int((min(s[0], event.x) - ox) / scale)
            iy1 = int((min(s[1], event.y) - oy) / scale)
            ix2 = int((max(s[0], event.x) - ox) / scale)
            iy2 = int((max(s[1], event.y) - oy) / scale)
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

        # Draw word bboxes
        word_bboxes = getattr(S, "word_bboxes", [])
        for i, (x, y, w, h) in enumerate(word_bboxes):
            x, y, w, h = int(x), int(y), int(w), int(h)
            if active_tab == "words" and i == highlight_idx:
                color, thickness = (0, 255, 0), 3
            else:
                color, thickness = (255, 100, 100), 2
            cv2.rectangle(img_rgb, (x, y), (x + w, y + h), color, thickness)
            cv2.putText(img_rgb, f"W{i+1}", (x + 2, y + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

        # Draw line regions
        det_lines = getattr(S, "detected_lines", [])
        img_h, img_w = img_rgb.shape[:2]
        for i, (y1, y2) in enumerate(det_lines):
            y1, y2 = int(y1), int(y2)
            if active_tab == "lines" and i == highlight_idx:
                color, thickness = (0, 255, 0), 3
            else:
                color, thickness = (30, 144, 255), 2
            cv2.rectangle(img_rgb, (0, y1), (img_w, y2), color, thickness)
            cv2.putText(img_rgb, f"L{i+1}", (5, y1 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Resize to fit canvas
        self.canvas.update_idletasks()
        cw = max(self.canvas.winfo_width(), 300)
        ch = max(self.canvas.winfo_height(), 300)
        scale = min(cw / img_w, ch / img_h, 1.0)
        new_w, new_h = int(img_w * scale), int(img_h * scale)

        resized = cv2.resize(img_rgb, (new_w, new_h),
                             interpolation=cv2.INTER_AREA)
        pil_img = Image.fromarray(resized)
        self.preview_photo = ImageTk.PhotoImage(pil_img)

        x_off = (cw - new_w) // 2
        y_off = (ch - new_h) // 2
        self.canvas.create_image(x_off, y_off, anchor=tk.NW,
                                 image=self.preview_photo)

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

    def _detect_words(self):
        """Run word detection directly (core logic only, no UI switch)."""
        if not self._ensure_images_ready():
            return
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

    def _on_padding_change(self, val):
        S.bbox_padding = int(float(val))

    # ==================================================================
    # FULL REFRESH
    # ==================================================================
    def _full_refresh(self):
        self._load_current_image()

    def refresh(self, ctx):
        """Called when returning to this step."""
        self.ctx = ctx
        self._load_current_image()

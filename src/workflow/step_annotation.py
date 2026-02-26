"""
Step 3 – Annotation Panel
Mode-specific annotation UI for words, lines, or characters.
Assumes Preprocessing (Step 2) has already run detection.
"""

import os
import json
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, Any
from PIL import Image, ImageTk

import state as S


class AnnotationPanel(tk.Frame):
    """Annotation step – shows word / line / character annotation UI
    depending on the type chosen in the Preprocessing step."""

    PAGE_SIZE = 30  # items per page for paginated modes

    def __init__(self, parent: tk.Widget, colors: Dict[str, str],
                 dataset_ctx: Dict[str, Any]):
        super().__init__(parent, bg=colors["bg_dark"])
        self.colors = colors
        self.ctx = dataset_ctx
        self._photo_refs = []      # prevent GC of PhotoImage objects
        self._entries = []         # annotation entry widgets on current page
        self._scroll_canvas = None
        self._ann_image_path = None
        self._ann_img_size = (0, 0)
        self._ann_detected_lines = []
        self._ann_char_boxes = []
        self._word_files = []        # (path, display_name) for word mode

        # -- Pagination state --
        self._page = 0                # current page (0-indexed)
        self._total_pages = 1
        self._all_annotations: Dict[int, str] = {}  # global_index -> text
        self._page_mode = None        # "word" | "line_cropped" | None

        self._build_shell()

    # ==================================================================
    # Skeleton (header + empty body container)
    # ==================================================================
    def _build_shell(self):
        hdr = tk.Frame(self, bg=self.colors["bg_section"], pady=12, padx=15)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="✏️  Step 3 — Annotation",
                 font=("Segoe UI", 15, "bold"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(side=tk.LEFT)
        self._ann_type_label = tk.Label(
            hdr, text="", font=("Segoe UI", 10),
            bg=self.colors["bg_section"],
            fg=self.colors["text_muted"])
        self._ann_type_label.pack(side=tk.RIGHT)

        self._body = tk.Frame(self, bg=self.colors["bg_dark"])
        self._body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _clear_body(self):
        self._sync_page_entries()  # save current page before clearing
        for w in self._body.winfo_children():
            w.destroy()
        self._photo_refs.clear()
        self._entries.clear()
        self._word_files.clear()
        self._scroll_canvas = None

    # ==================================================================
    # Pagination helpers
    # ==================================================================
    def _sync_page_entries(self):
        """Save current page's entry values into the master dict."""
        if self._page_mode is None:
            return
        offset = self._page * self.PAGE_SIZE
        for i, entry in enumerate(self._entries):
            try:
                self._all_annotations[offset + i] = entry.get()
            except Exception:
                pass

    def _goto_page(self, page: int):
        """Navigate to a specific page (save current first, rebuild)."""
        self._sync_page_entries()
        self._page = max(0, min(page, self._total_pages - 1))
        # Rebuild page content only (not the entire body)
        if self._page_mode == "word":
            self._render_word_page()
        elif self._page_mode == "line_cropped":
            self._render_line_cropped_page()
        elif self._page_mode == "line_detected":
            self._render_line_detected_page()

    def _build_pagination_bar(self, parent, total_items: int):
        """Build a pagination bar with prev/next, page indicator, page-size selector."""
        self._total_pages = max(1, (total_items + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if self._page >= self._total_pages:
            self._page = self._total_pages - 1

        bar = tk.Frame(parent, bg='#e8ecf1', pady=6, padx=10)
        bar.pack(fill=tk.X, padx=10, pady=(0, 6))

        self._btn_first = tk.Button(
            bar, text="⏮ First", command=lambda: self._goto_page(0),
            font=("Segoe UI", 9), bg='#6cb6ff', fg='white',
            relief=tk.FLAT, padx=8, pady=3, cursor="hand2")
        self._btn_first.pack(side=tk.LEFT, padx=2)

        self._btn_prev_page = tk.Button(
            bar, text="◀ Prev", command=lambda: self._goto_page(self._page - 1),
            font=("Segoe UI", 9), bg='#6cb6ff', fg='white',
            relief=tk.FLAT, padx=8, pady=3, cursor="hand2")
        self._btn_prev_page.pack(side=tk.LEFT, padx=2)

        self._page_info_var = tk.StringVar()
        tk.Label(bar, textvariable=self._page_info_var,
                 font=("Segoe UI", 10, "bold"), bg='#e8ecf1',
                 fg='#333').pack(side=tk.LEFT, padx=12)

        self._btn_next_page = tk.Button(
            bar, text="Next ▶", command=lambda: self._goto_page(self._page + 1),
            font=("Segoe UI", 9), bg='#6cb6ff', fg='white',
            relief=tk.FLAT, padx=8, pady=3, cursor="hand2")
        self._btn_next_page.pack(side=tk.LEFT, padx=2)

        self._btn_last = tk.Button(
            bar, text="Last ⏭", command=lambda: self._goto_page(self._total_pages - 1),
            font=("Segoe UI", 9), bg='#6cb6ff', fg='white',
            relief=tk.FLAT, padx=8, pady=3, cursor="hand2")
        self._btn_last.pack(side=tk.LEFT, padx=2)

        # Jump-to-page entry
        tk.Label(bar, text="  Go to:", font=("Segoe UI", 9),
                 bg='#e8ecf1', fg='#555').pack(side=tk.LEFT, padx=(16, 4))
        self._page_jump_var = tk.StringVar(value=str(self._page + 1))
        jump_entry = tk.Entry(bar, textvariable=self._page_jump_var,
                              width=4, font=("Segoe UI", 9), justify='center')
        jump_entry.pack(side=tk.LEFT)
        jump_entry.bind("<Return>", lambda e: self._jump_to_page())
        tk.Button(bar, text="Go", command=self._jump_to_page,
                  font=("Segoe UI", 8), bg='#5a9fd4', fg='white',
                  relief=tk.FLAT, padx=6, pady=2, cursor="hand2").pack(side=tk.LEFT, padx=4)

        self._update_page_info(total_items)
        return bar

    def _jump_to_page(self):
        try:
            p = int(self._page_jump_var.get()) - 1
            self._goto_page(p)
        except ValueError:
            pass

    def _update_page_info(self, total_items: int):
        start = self._page * self.PAGE_SIZE + 1
        end = min(start + self.PAGE_SIZE - 1, total_items)
        self._page_info_var.set(
            f"Page {self._page + 1} / {self._total_pages}  "
            f"({start}–{end} of {total_items})")
        self._page_jump_var.set(str(self._page + 1))
        # Enable/disable buttons
        is_first = self._page == 0
        is_last = self._page >= self._total_pages - 1
        self._btn_first.config(state="disabled" if is_first else "normal")
        self._btn_prev_page.config(state="disabled" if is_first else "normal")
        self._btn_next_page.config(state="disabled" if is_last else "normal")
        self._btn_last.config(state="disabled" if is_last else "normal")

    # ==================================================================
    # Scrollable container helper
    # ==================================================================
    def _make_scrollable(self, parent):
        """Return (canvas, scroll_frame) with vertical scroll."""
        canvas = tk.Canvas(parent, bg='#f4f7fb', highlightthickness=0)
        vsb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg='#f4f7fb')

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def _on_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_wheel)

        self._scroll_canvas = canvas
        return canvas, inner

    # ==================================================================
    # Ensure shared state directories are set up
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
        return bool(getattr(S, 'list_of_files', None))

    # ==================================================================
    # WORD annotation (paginated)
    # ==================================================================
    def _build_word_annotation(self):
        self._ensure_images_ready()
        source = getattr(self, '_annotation_source', 'original')

        if source == "preprocessing":
            # Use crops produced by word detection (out dir)
            out_dir = getattr(S, 'directoryout', None)
            crop_files = []
            if out_dir and os.path.isdir(out_dir):
                crop_files = sorted(
                    f for f in os.listdir(out_dir)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')))

            if not crop_files:
                tk.Label(self._body,
                         text="No word detection crops found.\n"
                              "Run 'Detect Words' in Preprocessing first,\n"
                              "or switch Annotation Source to 'Original Images'.",
                         font=("Segoe UI", 12), bg=self.colors["bg_dark"],
                         fg=self.colors["text_muted"]).pack(expand=True)
                return
            word_paths = [(os.path.join(out_dir, f), f) for f in crop_files]
        else:
            # Use original loaded images as-is
            imgs = self.ctx.get("images", []) or getattr(S, 'list_of_files', [])
            if imgs:
                word_paths = [(p, os.path.basename(p)) for p in imgs]
            else:
                word_paths = []

        if not word_paths:
            tk.Label(self._body,
                     text="No images available for word annotation.\n"
                          "Load a dataset first.",
                     font=("Segoe UI", 12), bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"]).pack(expand=True)
            return

        self._word_files = word_paths
        self._page_mode = "word"
        self._page = 0
        self._all_annotations = {}

        # Pre-fill annotations from input text
        input_words = self._get_input_words()
        for i, w in enumerate(input_words):
            if i < len(word_paths):
                self._all_annotations[i] = w

        # Build the persistent shell: header + pagination bar + page container
        self._word_header = tk.Frame(self._body, bg='#6cb6ff', padx=10, pady=8)
        self._word_header.pack(fill=tk.X, padx=10, pady=(0, 0))
        tk.Label(self._word_header,
                 text=f"📝 Word Annotation — {len(word_paths)} words",
                 font=('Segoe UI', 12, 'bold'),
                 bg='#6cb6ff', fg='white').pack(side=tk.LEFT)

        self._pagination_bar = self._build_pagination_bar(self._body, len(word_paths))

        # Scrollable page container
        self._page_container = tk.Frame(self._body, bg=self.colors["bg_dark"])
        self._page_container.pack(fill=tk.BOTH, expand=True)

        self._render_word_page()

    def _render_word_page(self):
        """Render a single page of word annotations."""
        # Destroy previous page content
        for w in self._page_container.winfo_children():
            w.destroy()
        self._photo_refs.clear()
        self._entries.clear()
        self._scroll_canvas = None

        total = len(self._word_files)
        start = self._page * self.PAGE_SIZE
        end = min(start + self.PAGE_SIZE, total)
        page_items = self._word_files[start:end]

        canvas, scroll_frame = self._make_scrollable(self._page_container)

        # Grid container
        grid_frame = tk.Frame(scroll_frame, bg='#f4f7fb')
        grid_frame.pack(fill=tk.BOTH, padx=10)

        COLS = 8
        for local_idx, (fpath, fname) in enumerate(page_items):
            row, col = divmod(local_idx, COLS)
            cell = tk.Frame(grid_frame, bg='white', relief=tk.RIDGE, bd=1)
            cell.grid(row=row, column=col, padx=4, pady=4, sticky='nsew')
            grid_frame.columnconfigure(col, weight=1)

            try:
                thumb = Image.open(fpath).resize((100, 100), Image.LANCZOS)
                photo = ImageTk.PhotoImage(thumb)
                self._photo_refs.append(photo)
                tk.Label(cell, image=photo, bg='white').pack(padx=2, pady=(4, 0))
            except Exception:
                tk.Label(cell, text="[img]", bg='white').pack(padx=2, pady=(4, 0))

            entry = tk.Entry(cell, width=13,
                             font=('Segoe UI', 9), justify='center')
            entry.pack(padx=2, pady=(2, 4))
            # Restore saved annotation
            global_idx = start + local_idx
            saved = self._all_annotations.get(global_idx, "")
            if saved:
                entry.insert(0, saved)
            self._entries.append(entry)

        # Action buttons
        self._build_action_buttons(scroll_frame, mode="word")

        # Update pagination info
        self._update_page_info(total)

    def _get_input_words(self):
        """Get word list from input text."""
        input_text = None
        if hasattr(S, 'input_mode_var') and hasattr(S.input_mode_var, 'get'):
            mode = S.input_mode_var.get()
            if mode == 'generate':
                input_text = getattr(S, 'gan_input_text', None)
        if input_text is None:
            if hasattr(S, 'input_text_area') and S.input_text_area:
                try:
                    input_text = S.input_text_area.get("1.0", "end-1c").strip()
                except Exception:
                    pass
            if not input_text and hasattr(S, 'input_text') and S.input_text:
                input_text = S.input_text.strip()
        if not input_text:
            return []
        words = []
        for line in input_text.splitlines():
            words.extend(line.split())
        return words

    def _autofill_lines(self):
        """Pre-fill line annotations from input text (one line per entry)."""
        input_text = self._get_input_text()
        if not input_text:
            return
        lines = [l for l in input_text.splitlines() if l.strip()]
        for i, entry in enumerate(self._entries):
            global_idx = self._page * self.PAGE_SIZE + i
            if global_idx < len(lines):
                entry.delete(0, tk.END)
                entry.insert(0, lines[global_idx])

    def _get_input_text(self):
        """Get raw input text from state."""
        input_text = None
        if hasattr(S, 'input_mode_var') and hasattr(S.input_mode_var, 'get'):
            mode = S.input_mode_var.get()
            if mode == 'generate':
                input_text = getattr(S, 'gan_input_text', None)
        if input_text is None:
            if hasattr(S, 'input_text_area') and S.input_text_area:
                try:
                    input_text = S.input_text_area.get("1.0", "end-1c").strip()
                except Exception:
                    pass
            if not input_text and hasattr(S, 'input_text') and S.input_text:
                input_text = S.input_text.strip()
        return input_text or ""

    # ==================================================================
    # LINE annotation
    # ==================================================================
    def _build_line_annotation(self):
        self._ensure_images_ready()
        source = getattr(self, '_annotation_source', 'original')

        if source == "preprocessing":
            # Must have detected lines from preprocessing
            detected_lines = getattr(S, 'detected_lines', [])
            image_path = self._current_image_path()

            if not detected_lines or not image_path:
                tk.Label(self._body,
                         text="No detected lines found.\n"
                              "Run 'Detect Lines' in Preprocessing first,\n"
                              "or switch Annotation Source to 'Original Images'.",
                         font=("Segoe UI", 12), bg=self.colors["bg_dark"],
                         fg=self.colors["text_muted"]).pack(expand=True)
                return

            self._build_line_annotation_detected(image_path, detected_lines)
        else:
            # Original images — treat each loaded image as a cropped line
            self._build_line_annotation_cropped()

    # -- Detected lines (preprocessing) with pagination --
    def _build_line_annotation_detected(self, image_path, detected_lines):
        """Show line crops from a single source image, paginated for batching."""
        try:
            original_img = Image.open(image_path)
            img_w, img_h = original_img.size
        except Exception as e:
            tk.Label(self._body, text=f"Cannot load image: {e}",
                     font=("Segoe UI", 11), bg=self.colors["bg_dark"],
                     fg='#cc0000').pack(expand=True)
            return

        self._det_source_img = original_img
        self._det_lines = detected_lines
        self._ann_image_path = image_path
        self._ann_img_size = (img_w, img_h)
        self._ann_detected_lines = detected_lines
        self._page_mode = "line_detected"
        self._page = 0
        self._all_annotations = {}

        # Pre-fill from input text
        input_text = self._get_input_text()
        if input_text:
            text_lines = [l for l in input_text.splitlines() if l.strip()]
            for i, line in enumerate(text_lines):
                if i < len(detected_lines):
                    self._all_annotations[i] = line

        # Header
        self._line_det_header = tk.Frame(self._body, bg='#6cb6ff', padx=10, pady=8)
        self._line_det_header.pack(fill=tk.X, padx=10, pady=(0, 0))
        tk.Label(self._line_det_header,
                 text=f"📄 Line Annotation (detected) — {len(detected_lines)} lines",
                 font=('Segoe UI', 12, 'bold'),
                 bg='#6cb6ff', fg='white').pack(side=tk.LEFT)

        self._pagination_bar = self._build_pagination_bar(self._body, len(detected_lines))

        self._page_container = tk.Frame(self._body, bg=self.colors["bg_dark"])
        self._page_container.pack(fill=tk.BOTH, expand=True)

        self._render_line_detected_page()

    def _render_line_detected_page(self):
        """Render one page of detected-line crops."""
        for w in self._page_container.winfo_children():
            w.destroy()
        self._photo_refs.clear()
        self._entries.clear()
        self._scroll_canvas = None

        detected_lines = self._det_lines
        original_img = self._det_source_img
        img_w = self._ann_img_size[0]
        total = len(detected_lines)
        start = self._page * self.PAGE_SIZE
        end = min(start + self.PAGE_SIZE, total)

        canvas, scroll_frame = self._make_scrollable(self._page_container)

        for local_idx in range(end - start):
            global_idx = start + local_idx
            lt = detected_lines[global_idx]
            if len(lt) == 4:
                x1, y1, x2, y2 = lt
            else:
                y1, y2 = lt
                x1, x2 = 0, img_w

            line_frame = tk.Frame(scroll_frame, bg='white',
                                  relief=tk.RIDGE, bd=1)
            line_frame.pack(fill=tk.X, padx=10, pady=4)

            tk.Label(line_frame, text=f"Line {global_idx + 1}:",
                     font=('Segoe UI', 10, 'bold'),
                     bg='white', fg='#333').pack(anchor='w', padx=10,
                                                  pady=(6, 2))

            try:
                crop = original_img.crop((x1, y1, x2, y2))
                cw, ch = crop.size
                max_w = 600
                if cw > max_w:
                    scale = max_w / cw
                    crop = crop.resize((max_w, int(ch * scale)),
                                       Image.LANCZOS)
                photo = ImageTk.PhotoImage(crop)
                self._photo_refs.append(photo)
                tk.Label(line_frame, image=photo, bg='white',
                         relief=tk.SUNKEN, bd=1).pack(padx=10, pady=4)
            except Exception:
                tk.Label(line_frame, text="[Cannot crop line]",
                         bg='white').pack(padx=10, pady=4)

            tk.Label(line_frame, text="Transcription:",
                     font=('Segoe UI', 9), bg='white',
                     fg='#666').pack(anchor='w', padx=10, pady=(4, 2))
            entry = tk.Entry(line_frame, font=('Segoe UI', 11), width=70)
            entry.pack(fill=tk.X, padx=10, pady=(0, 8))
            # Restore saved annotation
            saved = self._all_annotations.get(global_idx, "")
            if saved:
                entry.insert(0, saved)
            self._entries.append(entry)

        self._build_action_buttons(scroll_frame, mode="line")
        self._update_page_info(total)

    def _build_line_annotation_cropped(self):
        """Treat every loaded image as an individual cropped line for annotation.
        Uses pagination to keep the UI smooth for large datasets."""
        imgs = self.ctx.get("images", []) or getattr(S, 'list_of_files', [])
        if not imgs:
            tk.Label(self._body,
                     text="No images available for line annotation.\n"
                          "Load a dataset first.",
                     font=("Segoe UI", 12), bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"]).pack(expand=True)
            return

        self._line_cropped_imgs = imgs
        self._page_mode = "line_cropped"
        self._page = 0
        self._all_annotations = {}

        # Pre-fill from input text (line-by-line)
        input_text = self._get_input_text()
        if input_text:
            text_lines = [l for l in input_text.splitlines() if l.strip()]
            for i, line in enumerate(text_lines):
                if i < len(imgs):
                    self._all_annotations[i] = line

        # Build persistent shell
        self._line_header = tk.Frame(self._body, bg='#6cb6ff', padx=10, pady=8)
        self._line_header.pack(fill=tk.X, padx=10, pady=(0, 0))
        tk.Label(self._line_header,
                 text=f"📄 Line Annotation (cropped images) — {len(imgs)} lines",
                 font=('Segoe UI', 12, 'bold'),
                 bg='#6cb6ff', fg='white').pack(side=tk.LEFT)

        self._pagination_bar = self._build_pagination_bar(self._body, len(imgs))

        self._page_container = tk.Frame(self._body, bg=self.colors["bg_dark"])
        self._page_container.pack(fill=tk.BOTH, expand=True)

        self._render_line_cropped_page()

    def _render_line_cropped_page(self):
        """Render a single page of cropped-line annotations."""
        for w in self._page_container.winfo_children():
            w.destroy()
        self._photo_refs.clear()
        self._entries.clear()
        self._scroll_canvas = None

        imgs = self._line_cropped_imgs
        total = len(imgs)
        start = self._page * self.PAGE_SIZE
        end = min(start + self.PAGE_SIZE, total)

        canvas, scroll_frame = self._make_scrollable(self._page_container)

        for local_idx in range(end - start):
            global_idx = start + local_idx
            fpath = imgs[global_idx]

            line_frame = tk.Frame(scroll_frame, bg='white',
                                  relief=tk.RIDGE, bd=1)
            line_frame.pack(fill=tk.X, padx=10, pady=4)

            fname = os.path.basename(fpath)
            tk.Label(line_frame, text=f"Line {global_idx + 1}:  {fname}",
                     font=('Segoe UI', 10, 'bold'),
                     bg='white', fg='#333').pack(anchor='w', padx=10,
                                                  pady=(6, 2))

            try:
                img = Image.open(fpath)
                cw, ch = img.size
                max_w = 600
                if cw > max_w:
                    scale = max_w / cw
                    img = img.resize((max_w, int(ch * scale)), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._photo_refs.append(photo)
                tk.Label(line_frame, image=photo, bg='white',
                         relief=tk.SUNKEN, bd=1).pack(padx=10, pady=4)
            except Exception:
                tk.Label(line_frame, text="[Cannot load image]",
                         bg='white').pack(padx=10, pady=4)

            tk.Label(line_frame, text="Transcription:",
                     font=('Segoe UI', 9), bg='white',
                     fg='#666').pack(anchor='w', padx=10, pady=(4, 2))
            entry = tk.Entry(line_frame, font=('Segoe UI', 11), width=70)
            entry.pack(fill=tk.X, padx=10, pady=(0, 8))
            # Restore saved annotation
            saved = self._all_annotations.get(global_idx, "")
            if saved:
                entry.insert(0, saved)
            self._entries.append(entry)

        # Action buttons
        self._build_action_buttons(scroll_frame, mode="line")

        # Update pagination info
        self._update_page_info(total)

    # ==================================================================
    # CHARACTER annotation
    # ==================================================================
    def _build_char_annotation(self):
        image_path = self._current_image_path()
        char_boxes = getattr(S, 'char_detected_boxes', [])

        if not image_path:
            tk.Label(self._body,
                     text="No images loaded.\n"
                          "Complete Dataset Ingestion first.",
                     font=("Segoe UI", 12), bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"]).pack(expand=True)
            return

        if not char_boxes:
            tk.Label(self._body,
                     text="No characters detected.\n"
                          "Run Character Detection in Preprocessing first.",
                     font=("Segoe UI", 12), bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"]).pack(expand=True)
            return

        try:
            original_img = Image.open(image_path)
        except Exception as e:
            tk.Label(self._body, text=f"Cannot load image: {e}",
                     font=("Segoe UI", 11), bg=self.colors["bg_dark"],
                     fg='#cc0000').pack(expand=True)
            return

        canvas, scroll_frame = self._make_scrollable(self._body)

        # Header
        hdr = tk.Frame(scroll_frame, bg='#6cb6ff', padx=10, pady=8)
        hdr.pack(fill=tk.X, pady=(0, 10))
        tk.Label(hdr,
                 text=f"🔤 Character Annotation — {len(char_boxes)} characters",
                 font=('Segoe UI', 12, 'bold'),
                 bg='#6cb6ff', fg='white').pack(side=tk.LEFT)

        for i, ch_info in enumerate(char_boxes):
            x1, y1, x2, y2 = ch_info['coords']
            label = ch_info.get('label', '?')
            score = ch_info.get('score', 0)

            cf = tk.Frame(scroll_frame, bg='white', relief=tk.RIDGE, bd=1)
            cf.pack(fill=tk.X, padx=10, pady=3)

            try:
                crop = original_img.crop((x1, y1, x2, y2))
                cw, ch_h = crop.size
                target_h = 50
                if ch_h > 0:
                    sc = target_h / ch_h
                    crop = crop.resize((max(20, int(cw * sc)), target_h),
                                       Image.LANCZOS)
                photo = ImageTk.PhotoImage(crop)
                self._photo_refs.append(photo)
                tk.Label(cf, image=photo, bg='white',
                         relief=tk.SUNKEN, bd=1).pack(side=tk.LEFT,
                                                       padx=5, pady=5)
            except Exception:
                tk.Label(cf, text="[img]",
                         bg='white').pack(side=tk.LEFT, padx=5, pady=5)

            info = tk.Frame(cf, bg='white')
            info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            tk.Label(info, text=f"#{i + 1}",
                     font=('Segoe UI', 9, 'bold'),
                     bg='white', fg='#666', width=4).pack(side=tk.LEFT)

            entry = tk.Entry(info, font=('Segoe UI', 11, 'bold'),
                             width=5, justify='center')
            entry.insert(0, label)
            entry.pack(side=tk.LEFT, padx=5)
            self._entries.append(entry)

            if score > 0:
                tk.Label(info, text=f"({score:.2f})",
                         font=('Segoe UI', 8), bg='white',
                         fg='#999').pack(side=tk.LEFT, padx=5)

            coords_text = f"[{x1},{y1},{x2 - x1}x{y2 - y1}]"
            tk.Label(info, text=coords_text,
                     font=('Segoe UI', 8), bg='white',
                     fg='#aaa').pack(side=tk.LEFT, padx=5)

        self._ann_image_path = image_path
        self._ann_char_boxes = char_boxes

        self._build_action_buttons(scroll_frame, mode="character")

    # ==================================================================
    # Action buttons (shared by all modes)
    # ==================================================================
    def _build_action_buttons(self, parent, mode="word"):
        bf = tk.Frame(parent, bg='#f4f7fb')
        bf.pack(fill=tk.X, padx=10, pady=(15, 20))

        tk.Button(bf, text="💾 Save JSON",
                  command=lambda: self._save_json(mode),
                  bg='#6cb6ff', fg='white',
                  font=('Segoe UI', 10, 'bold'),
                  padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        tk.Button(bf, text="📄 Export IAM",
                  command=lambda: self._export_iam(mode),
                  bg='#5a9fd4', fg='white',
                  font=('Segoe UI', 10, 'bold'),
                  padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        tk.Button(bf, text="🗑 Clear All",
                  command=self._clear_entries,
                  bg='#dc3545', fg='white',
                  font=('Segoe UI', 10, 'bold'),
                  padx=15, pady=5).pack(side=tk.RIGHT, padx=5)

    def _clear_entries(self):
        for e in self._entries:
            e.delete(0, tk.END)
        # Also clear master annotations for paginated modes
        if self._page_mode:
            offset = self._page * self.PAGE_SIZE
            for i in range(len(self._entries)):
                self._all_annotations.pop(offset + i, None)

    def _get_all_annotation_texts(self, total: int):
        """Sync current page and return a list of texts for all items (across all pages)."""
        self._sync_page_entries()
        return [self._all_annotations.get(i, "").strip() for i in range(total)]

    # ------------------------------------------------------------------
    # Save JSON
    # ------------------------------------------------------------------
    def _save_json(self, mode):
        save_path = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
            title="Save Annotations")
        if not save_path:
            return

        data = {}
        if mode == "word":
            wf = self._word_files
            if self._page_mode == "word":
                texts = self._get_all_annotation_texts(len(wf))
                data = {
                    "mode": "word",
                    "words": [{"file": wf[i][1] if i < len(wf) else "",
                               "text": texts[i]}
                              for i in range(len(wf))]
                }
            else:
                data = {
                    "mode": "word",
                    "words": [{"file": wf[i][1] if i < len(wf) else "",
                               "text": e.get().strip()}
                              for i, e in enumerate(self._entries)]
                }
        elif mode == "line":
            det = self._ann_detected_lines
            if det and self._page_mode == "line_detected":
                # Detected lines (paginated) — use _all_annotations
                img_path = self._ann_image_path or ''
                img_size = self._ann_img_size
                texts = self._get_all_annotation_texts(len(det))
                lines_out = []
                for i in range(len(det)):
                    lt = det[i] if i < len(det) else (0, 0)
                    if len(lt) == 4:
                        x1, y1, x2, y2 = lt
                    else:
                        y1, y2 = lt
                        x1, x2 = 0, img_size[0]
                    lines_out.append({
                        "line_id": i,
                        "y_start": int(y1), "y_end": int(y2),
                        "text": texts[i],
                        "bbox": [int(x1), int(y1),
                                 int(x2 - x1), int(y2 - y1)]
                    })
                data = {
                    "mode": "line",
                    "image": os.path.basename(img_path),
                    "image_size": list(img_size),
                    "lines": lines_out
                }
            else:
                # Cropped line images — paginated
                imgs = getattr(self, '_line_cropped_imgs',
                               self.ctx.get("images", []) or getattr(S, 'list_of_files', []))
                texts = self._get_all_annotation_texts(len(imgs))
                lines_out = []
                for i in range(len(imgs)):
                    fname = os.path.basename(imgs[i]) if i < len(imgs) else f"line_{i}"
                    lines_out.append({
                        "line_id": i,
                        "file": fname,
                        "text": texts[i],
                    })
                data = {
                    "mode": "line",
                    "lines": lines_out
                }
        elif mode == "character":
            img_path = self._ann_image_path or ''
            boxes = self._ann_char_boxes
            chars_out = []
            for i, e in enumerate(self._entries):
                b = boxes[i] if i < len(boxes) else {}
                coords = b.get('coords', (0, 0, 0, 0))
                chars_out.append({
                    "char_id": i,
                    "label": e.get().strip(),
                    "coords": [int(c) for c in coords]
                })
            data = {
                "mode": "character",
                "image": os.path.basename(img_path),
                "characters": chars_out
            }

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Saved",
                                f"Annotations saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    # ------------------------------------------------------------------
    # Export IAM format
    # ------------------------------------------------------------------
    def _export_iam(self, mode):
        save_path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')],
            title="Export IAM Format")
        if not save_path:
            return

        lines_out = []
        if mode == "word":
            wf = self._word_files
            if self._page_mode == "word":
                texts = self._get_all_annotation_texts(len(wf))
                for i in range(len(wf)):
                    t = texts[i]
                    if t:
                        fname = (os.path.splitext(wf[i][1])[0]
                                 if i < len(wf) else f"word{i:04d}")
                        lines_out.append(f"{fname} {t}")
            else:
                for i, e in enumerate(self._entries):
                    t = e.get().strip()
                    if t:
                        fname = (os.path.splitext(wf[i][1])[0]
                                 if i < len(wf) else f"word{i:04d}")
                        lines_out.append(f"{fname} {t}")
        elif mode == "line":
            det = self._ann_detected_lines
            if det and self._page_mode == "line_detected":
                img_path = self._ann_image_path or ''
                base = os.path.splitext(os.path.basename(img_path))[0]
                texts = self._get_all_annotation_texts(len(det))
                for i in range(len(det)):
                    t = texts[i]
                    if t:
                        lines_out.append(f"{base}-line{i:03d} {t}")
            else:
                imgs = getattr(self, '_line_cropped_imgs',
                               self.ctx.get("images", []) or getattr(S, 'list_of_files', []))
                texts = self._get_all_annotation_texts(len(imgs))
                for i in range(len(imgs)):
                    t = texts[i]
                    if t:
                        fname = (os.path.splitext(os.path.basename(imgs[i]))[0]
                                 if i < len(imgs) else f"line{i:03d}")
                        lines_out.append(f"{fname} {t}")
        elif mode == "character":
            img_path = self._ann_image_path or ''
            base = os.path.splitext(os.path.basename(img_path))[0]
            for i, e in enumerate(self._entries):
                t = e.get().strip()
                if t:
                    lines_out.append(f"{base}-char{i:04d} {t}")

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines_out))
            messagebox.showinfo("Exported",
                                f"IAM format exported to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    # ==================================================================
    # Helpers
    # ==================================================================
    def _current_image_path(self):
        imgs = self.ctx.get("images", [])
        if not imgs:
            imgs = getattr(S, 'list_of_files', [])
        if not imgs:
            return None
        idx = min(getattr(S, 'pos', 0), len(imgs) - 1)
        return imgs[idx] if imgs else None

    # ==================================================================
    # refresh (called by WorkflowManager on step change)
    # ==================================================================
    def refresh(self, ctx):
        self.ctx = ctx
        ann_type = ctx.get("annotation_type",
                           getattr(S, "annotation_type", "word"))
        ann_source = ctx.get("annotation_source",
                             getattr(S, "annotation_source", "original"))
        self._annotation_source = ann_source
        self._ann_type_label.config(
            text=f"Annotation type: {ann_type.title()}  |  Source: {ann_source.title()}")

        self._clear_body()

        if ann_type == "line":
            self._build_line_annotation()
        elif ann_type == "character":
            self._build_char_annotation()
        else:
            self._build_word_annotation()

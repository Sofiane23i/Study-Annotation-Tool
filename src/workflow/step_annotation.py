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

    def __init__(self, parent: tk.Widget, colors: Dict[str, str],
                 dataset_ctx: Dict[str, Any]):
        super().__init__(parent, bg=colors["bg_dark"])
        self.colors = colors
        self.ctx = dataset_ctx
        self._photo_refs = []      # prevent GC of PhotoImage objects
        self._entries = []         # annotation entry widgets
        self._scroll_canvas = None
        self._ann_image_path = None
        self._ann_img_size = (0, 0)
        self._ann_detected_lines = []
        self._ann_char_boxes = []
        self._word_files = []        # (path, display_name) for word mode

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
        for w in self._body.winfo_children():
            w.destroy()
        self._photo_refs.clear()
        self._entries.clear()
        self._word_files.clear()
        self._scroll_canvas = None

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
    # WORD annotation
    # ==================================================================
    def _build_word_annotation(self):
        self._ensure_images_ready()

        # 1) Try crops produced by word detection (out dir)
        out_dir = getattr(S, 'directoryout', None)
        crop_files = []
        if out_dir and os.path.isdir(out_dir):
            crop_files = sorted(
                f for f in os.listdir(out_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')))

        # 2) If no crops, treat every loaded image as a word crop
        if crop_files:
            word_paths = [(os.path.join(out_dir, f), f) for f in crop_files]
        else:
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

        canvas, scroll_frame = self._make_scrollable(self._body)

        # Header
        hdr = tk.Frame(scroll_frame, bg='#6cb6ff', padx=10, pady=8)
        hdr.pack(fill=tk.X, pady=(0, 10))
        tk.Label(hdr, text=f"📝 Word Annotation — {len(word_paths)} words",
                 font=('Segoe UI', 12, 'bold'),
                 bg='#6cb6ff', fg='white').pack(side=tk.LEFT)

        # Grid container
        grid_frame = tk.Frame(scroll_frame, bg='#f4f7fb')
        grid_frame.pack(fill=tk.BOTH, padx=10)

        COLS = 8
        for idx, (fpath, fname) in enumerate(word_paths):
            row, col = divmod(idx, COLS)
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
            self._entries.append(entry)

        # Autofill from input text
        self._autofill_words()

        # Action buttons
        self._build_action_buttons(scroll_frame, mode="word")

    def _autofill_words(self):
        """Pre-fill word entries from input text if available."""
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
            return

        words = []
        for line in input_text.splitlines():
            words.extend(line.split())

        for i, entry in enumerate(self._entries):
            if i < len(words):
                entry.delete(0, tk.END)
                entry.insert(0, words[i])

    # ==================================================================
    # LINE annotation
    # ==================================================================
    def _build_line_annotation(self):
        image_path = self._current_image_path()
        detected_lines = getattr(S, 'detected_lines', [])

        if not image_path:
            tk.Label(self._body,
                     text="No images loaded.\n"
                          "Complete Dataset Ingestion first.",
                     font=("Segoe UI", 12), bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"]).pack(expand=True)
            return

        if not detected_lines:
            tk.Label(self._body,
                     text="No lines detected.\n"
                          "Run Line Detection in Preprocessing first.",
                     font=("Segoe UI", 12), bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"]).pack(expand=True)
            return

        try:
            original_img = Image.open(image_path)
            img_w, img_h = original_img.size
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
                 text=f"📄 Line Annotation — {len(detected_lines)} lines",
                 font=('Segoe UI', 12, 'bold'),
                 bg='#6cb6ff', fg='white').pack(side=tk.LEFT)

        for i, lt in enumerate(detected_lines):
            if len(lt) == 4:
                x1, y1, x2, y2 = lt
            else:
                y1, y2 = lt
                x1, x2 = 0, img_w

            line_frame = tk.Frame(scroll_frame, bg='white',
                                  relief=tk.RIDGE, bd=1)
            line_frame.pack(fill=tk.X, padx=10, pady=4)

            tk.Label(line_frame, text=f"Line {i + 1}:",
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
            self._entries.append(entry)

        self._ann_image_path = image_path
        self._ann_img_size = (img_w, img_h)
        self._ann_detected_lines = detected_lines

        self._build_action_buttons(scroll_frame, mode="line")

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
            data = {
                "mode": "word",
                "words": [{"file": wf[i][1] if i < len(wf) else "",
                           "text": e.get().strip()}
                          for i, e in enumerate(self._entries)]
            }
        elif mode == "line":
            img_path = self._ann_image_path or ''
            img_size = self._ann_img_size
            det = self._ann_detected_lines
            lines_out = []
            for i, e in enumerate(self._entries):
                lt = det[i] if i < len(det) else (0, 0)
                if len(lt) == 4:
                    x1, y1, x2, y2 = lt
                else:
                    y1, y2 = lt
                    x1, x2 = 0, img_size[0]
                lines_out.append({
                    "line_id": i,
                    "y_start": int(y1), "y_end": int(y2),
                    "text": e.get().strip(),
                    "bbox": [int(x1), int(y1),
                             int(x2 - x1), int(y2 - y1)]
                })
            data = {
                "mode": "line",
                "image": os.path.basename(img_path),
                "image_size": list(img_size),
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
            for i, e in enumerate(self._entries):
                t = e.get().strip()
                if t:
                    fname = (os.path.splitext(wf[i][1])[0]
                             if i < len(wf) else f"word{i:04d}")
                    lines_out.append(f"{fname} {t}")
        elif mode == "line":
            img_path = self._ann_image_path or ''
            base = os.path.splitext(os.path.basename(img_path))[0]
            for i, e in enumerate(self._entries):
                t = e.get().strip()
                if t:
                    lines_out.append(f"{base}-line{i:03d} {t}")
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
        self._ann_type_label.config(
            text=f"Annotation type: {ann_type.title()}")

        self._clear_body()

        if ann_type == "line":
            self._build_line_annotation()
        elif ann_type == "character":
            self._build_char_annotation()
        else:
            self._build_word_annotation()

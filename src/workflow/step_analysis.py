"""
Step 2 – Annotation-Driven Statistical Analysis
Computes and displays dataset descriptors from available annotations.
If annotations are missing (raw/synthetic), shows image-only insights.
"""

import os
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
import threading
from PIL import Image

# Reuse the existing CorpusAnalyzer
from corpus_stats import CorpusAnalyzer

# Try matplotlib
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


class AnalysisPanel(tk.Frame):
    """Annotation-driven statistical analysis dashboard."""

    def __init__(self, parent: tk.Widget, colors: Dict[str, str],
                 dataset_ctx: Dict[str, Any]):
        super().__init__(parent, bg=colors["bg_dark"])
        self.colors = colors
        self.ctx = dataset_ctx
        self.analyzer = CorpusAnalyzer()
        self.stats = None
        self._build_ui()
        # Auto-run analysis if data already loaded
        self.after(300, self._auto_analyze)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        hdr = tk.Frame(self, bg=self.colors["bg_section"], pady=12, padx=15)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="📊  Step 3 — Annotation-Driven Statistical Analysis",
                 font=("Segoe UI", 15, "bold"),
                 bg=self.colors["bg_section"], fg=self.colors["text_light"]).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Waiting for analysis…")
        tk.Label(hdr, textvariable=self.status_var, font=("Segoe UI", 10),
                 bg=self.colors["bg_section"], fg=self.colors["text_muted"]).pack(side=tk.LEFT, padx=15)

        # Re-analyze button
        self.btn_reanalyze = tk.Button(hdr, text="🔄 Re-Analyze", command=self._run_analysis,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 9, "bold"), relief=tk.FLAT,
                  padx=10, pady=4, cursor="hand2")
        self.btn_reanalyze.pack(side=tk.RIGHT)

        # Progress bar
        progress_frame = tk.Frame(self, bg=self.colors["bg_dark"])
        progress_frame.pack(fill=tk.X, padx=15, pady=(0, 2))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                             maximum=100, mode="determinate", length=400)
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.progress_label = tk.Label(progress_frame, text="",
                                        font=("Segoe UI", 8),
                                        bg=self.colors["bg_dark"],
                                        fg=self.colors["text_muted"])
        self.progress_label.pack(side=tk.LEFT, padx=(8, 0))

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab: Overview
        self.tab_overview = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_overview, text="📊 Overview")

        # Tab: Label Distribution
        self.tab_labels = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_labels, text="🏷️ Label Distribution")

        # Tab: Character Frequency
        self.tab_chars = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_chars, text="🔤 Characters")

        # Tab: Writer Diversity
        self.tab_writers = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_writers, text="✍️ Writers")

        # Tab: Missing / Gaps
        self.tab_gaps = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_gaps, text="⚠️ Gaps & Warnings")

        # Place placeholder in each tab
        for tab in [self.tab_overview, self.tab_labels, self.tab_chars,
                     self.tab_writers, self.tab_gaps]:
            tk.Label(tab, text="Run analysis to populate this tab.",
                     font=("Segoe UI", 11),
                     bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"]).pack(expand=True)

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def _auto_analyze(self):
        if self.ctx.get("image_dir") or self.ctx.get("images"):
            self._run_analysis()

    def _set_progress(self, value: float, text: str = ""):
        """Update progress bar from any thread (schedules on main thread)."""
        def _update():
            self.progress_var.set(value)
            self.progress_label.config(text=text)
            self.update_idletasks()
        self.after(0, _update)

    def _run_analysis(self):
        self.status_var.set("⏳ Analyzing dataset…")
        self.btn_reanalyze.config(state="disabled")
        self._set_progress(0, "Starting…")

        def worker():
            try:
                self._run_analysis_worker()
            except Exception as exc:
                import traceback
                traceback.print_exc()
                self.after(0, lambda: self.status_var.set(f"❌ Error: {exc}"))
            finally:
                self.after(0, lambda: self.btn_reanalyze.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    # ------------------------------------------------------------------
    # Direct analysis from context annotations (fast path)
    # ------------------------------------------------------------------

    def _analyze_from_context(self, annotations, images):
        """Compute stats directly from ctx['annotations'] list-of-dicts.

        This avoids re-reading files from disk and is used when the user
        loaded data via the ingestion stage.
        """
        self.analyzer.reset_stats()
        total = len(annotations)

        for i, ann in enumerate(annotations):
            if i % 50 == 0:
                pct = 30 + int(50 * i / max(total, 1))
                self._set_progress(pct, f"Processing annotation {i+1}/{total}")

            self.analyzer.total_annotations += 1

            # Extract text — different keys depending on format
            text = (ann.get("label") or ann.get("text")
                    or ann.get("caption") or ann.get("transcription") or "")
            if text:
                self.analyzer._process_text(str(text))

            # Writer / style
            writer = ann.get("writer", ann.get("writer_id", ""))
            if writer:
                self.analyzer.handwriting_styles.add(str(writer))

            # Image ID
            img_id = ann.get("image_id", ann.get("filename", ann.get("file", "")))
            if img_id:
                self.analyzer.images.append(str(img_id))

        # Determine annotation type
        if self.analyzer.sequence_lengths:
            avg_len = (sum(self.analyzer.sequence_lengths)
                       / len(self.analyzer.sequence_lengths))
            if avg_len < 3:
                self.analyzer.annotation_type = "character"
            elif avg_len < 15:
                self.analyzer.annotation_type = "word"
            else:
                self.analyzer.annotation_type = "line"

        self._set_progress(85, "Computing statistics…")

        stats = {
            "folder": self.ctx.get("image_dir", ""),
            "annotation_type": self.analyzer.annotation_type,
            "total_annotations": self.analyzer.total_annotations,
            "total_images": len(set(self.analyzer.images)),
            "character_stats": self.analyzer._compute_character_stats(),
            "word_stats": self.analyzer._compute_word_stats(),
            "sequence_stats": self.analyzer._compute_sequence_stats(),
            "ngram_stats": self.analyzer._compute_ngram_stats(),
            "style_stats": self.analyzer._compute_style_stats(),
            "crop_count": 0,
        }
        return stats

    # ------------------------------------------------------------------
    # Main analysis worker (runs in background thread)
    # ------------------------------------------------------------------

    def _run_analysis_worker(self):
        stats = {}
        folder = self.ctx.get("image_dir", "")
        ann_file = self.ctx.get("annotation_file")
        has_ann = (self.ctx.get("metadata", {}).get("has_annotations", False)
                   or bool(ann_file and os.path.isfile(str(ann_file))))

        # ── Fast path: annotations already parsed in context ──
        ctx_annotations = self.ctx.get("annotations")
        is_list_of_dicts = (isinstance(ctx_annotations, list)
                            and ctx_annotations
                            and isinstance(ctx_annotations[0], dict))

        if is_list_of_dicts and self.ctx.get("type") != "synthetic":
            self._set_progress(20, "Analyzing loaded annotations…")
            stats = self._analyze_from_context(
                ctx_annotations, self.ctx.get("images", []))
            has_ann = True

        # ── Synthetic / GAN generation path ──
        elif self.ctx.get("type") == "synthetic":
            self._set_progress(5, "Preparing GAN output…")
            stats = self._run_synthetic_analysis()
            has_ann = stats.get("has_annotations", False)
            folder = stats.pop("_folder", folder)
            ann_file = stats.pop("_ann_file", ann_file)

        # ── Fallback: scan folder with CorpusAnalyzer ──
        elif has_ann and ann_file and os.path.isfile(str(ann_file)):
            self._set_progress(20, "Reading annotation file…")
            try:
                ann_dir = os.path.dirname(ann_file)
                stats = self.analyzer.analyze_folder(ann_dir)
            except Exception as e:
                stats = {"error": str(e)}
        elif folder:
            self._set_progress(20, "Scanning folder…")
            try:
                stats = self.analyzer.analyze_folder(folder)
            except Exception as e:
                stats = {"error": str(e)}

        self._set_progress(90, "Finalising…")

        # Override annotation type if context specifies it
        if self.ctx.get("annotation_type"):
            stats["annotation_type"] = self.ctx.get("annotation_type")
        if self.ctx.get("annotation_source"):
            stats["annotation_source"] = self.ctx.get("annotation_source")

        # Supplement with image metadata
        if folder:
            crops_dir = os.path.join(folder, 'crops')
            if os.path.isdir(crops_dir):
                subdirs = [d for d in os.listdir(crops_dir)
                           if os.path.isdir(os.path.join(crops_dir, d))]
                if subdirs:
                    stats["image_count"] = len(subdirs)
                else:
                    stats["image_count"] = len([
                        f for f in os.listdir(crops_dir)
                        if os.path.isfile(os.path.join(crops_dir, f))])
            else:
                stats.setdefault("image_count", len(self.ctx.get("images", [])))
        else:
            stats.setdefault("image_count", len(self.ctx.get("images", [])))

        stats["dataset_type"] = self.ctx.get("type", "unknown")
        stats["has_annotations"] = has_ann
        meta = self.ctx.get("metadata", {})
        stats["avg_width"] = meta.get("avg_width", 0)
        stats["avg_height"] = meta.get("avg_height", 0)
        stats["total_size_mb"] = meta.get("total_size_bytes", 0) / (1024 * 1024)

        self.stats = stats
        self.ctx["stats"] = stats

        self._set_progress(100, "Done")
        self.after(0, lambda: self._populate_tabs(stats))

    # ------------------------------------------------------------------
    # Synthetic / GAN analysis (heavy path, kept separate)
    # ------------------------------------------------------------------

    def _run_synthetic_analysis(self):
        """Handle GAN-generated synthetic data: export crops + annotations."""
        stats = {}
        folder = self.ctx.get("image_dir", "")
        ann_file = self.ctx.get("annotation_file")

        try:
            import shutil, uuid, datetime as _dt, tempfile
            import state as S
            gen_files = getattr(S, 'gan_generated_files', None)
            if not gen_files:
                # No GAN files — fall back to folder scan
                self._set_progress(30, "No GAN files; scanning folder…")
                if folder:
                    stats = self.analyzer.analyze_folder(folder)
                stats["has_annotations"] = False
                stats["_folder"] = folder
                stats["_ann_file"] = ann_file
                return stats

            src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            gan_root = os.path.join(src_root, 'gan_output_data')
            os.makedirs(gan_root, exist_ok=True)

            for stale in ('out', 'tmp'):
                stale_path = os.path.join(gan_root, stale)
                if os.path.isdir(stale_path):
                    try:
                        shutil.rmtree(stale_path)
                    except Exception:
                        pass

            ann_type = (getattr(S, 'annotation_type', None)
                        or self.ctx.get("annotation_type", "word"))
            label = ann_type if ann_type in ("line", "word") else "word"
            stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            session_dir = os.path.join(gan_root, f"{label}_{stamp}")
            images_dir = os.path.join(session_dir, "images")
            os.makedirs(images_dir, exist_ok=True)

            self._set_progress(10, "Copying generated images…")

            copied = []
            for sv, jp, texts in gen_files:
                src = jp if (jp and os.path.isfile(jp)) else sv
                if not src or not os.path.exists(src):
                    continue
                name = os.path.basename(src)
                dst_name = (f"{os.path.splitext(name)[0]}"
                            f"_{uuid.uuid4().hex[:6]}"
                            f"{os.path.splitext(name)[1]}")
                dst = os.path.join(session_dir, dst_name)
                try:
                    shutil.copyfile(src, dst)
                except Exception:
                    with open(src, 'rb') as fr, open(dst, 'wb') as fw:
                        fw.write(fr.read())
                copied.append((dst_name, texts))

            main_image_list = [os.path.join(session_dir, n) for n, _ in copied]

            try:
                from actions import save_file as save_file_action
            except Exception:
                save_file_action = None
            try:
                from actions.line_annotate import detect_text_lines
            except Exception:
                detect_text_lines = None

            crop_entries = []

            # Build user-annotation lookup
            user_annotations = {}
            ann_data = self.ctx.get('annotations') or {}
            ann_mode = ann_data.get('mode', 'word') if isinstance(ann_data, dict) else 'word'
            if isinstance(ann_data, dict):
                if ann_mode == 'word':
                    for wi, w_entry in enumerate(ann_data.get('words', [])):
                        txt = (w_entry.get('text') or '').strip()
                        if txt:
                            user_annotations[wi] = txt
                elif ann_mode == 'line':
                    for li, l_entry in enumerate(ann_data.get('lines', [])):
                        txt = (l_entry.get('text') or '').strip()
                        if txt:
                            user_annotations[li] = txt

            # Build GAN text lists per source image
            gan_texts_per_image = {}
            for ci, (_, c_texts) in enumerate(copied):
                if label == "line":
                    gan_texts_per_image[ci] = [
                        ln.strip() for ln in (c_texts or []) if ln.strip()]
                else:
                    words = []
                    for ln in (c_texts or []):
                        words.extend(ln.strip().split())
                    gan_texts_per_image[ci] = words

            global_crop_idx = 0
            total_images = len(main_image_list)

            # === LINE detection ===
            if label == "line" and detect_text_lines is not None:
                import cv2, numpy as np

                for idx, src_img in enumerate(main_image_list):
                    self._set_progress(
                        15 + int(55 * idx / max(total_images, 1)),
                        f"Line detection {idx+1}/{total_images}")
                    try:
                        pil_img = Image.open(src_img).convert('RGB')
                        img_w, img_h = pil_img.size
                        img_array = np.array(pil_img)
                        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                        lines_detected = detect_text_lines(img_gray)
                    except Exception as _le:
                        print(f"[step_analysis] Line detection failed "
                              f"for {src_img}: {_le}")
                        continue

                    img_base = os.path.splitext(os.path.basename(src_img))[0]
                    img_lines = gan_texts_per_image.get(idx, [])
                    pad = 5
                    for i, (x1, y1, x2, y2) in enumerate(lines_detected):
                        x1_pad = max(0, int(x1) - pad)
                        y1_pad = max(0, int(y1) - pad)
                        x2_pad = min(img_w, int(x2) + pad)
                        y2_pad = min(img_h, int(y2) + pad)
                        bw = x2_pad - x1_pad
                        bh = y2_pad - y1_pad
                        if bh <= 0 or bw <= 0:
                            continue
                        crop_array = img_array[y1_pad:y2_pad, x1_pad:x2_pad]
                        crop = Image.fromarray(crop_array)
                        crop_name = f"{img_base}_line{i}.png"
                        crop_dst = os.path.join(images_dir, crop_name)
                        try:
                            crop.save(crop_dst, 'PNG')
                        except Exception:
                            continue
                        gt = user_annotations.get(global_crop_idx, '')
                        if not gt and i < len(img_lines):
                            gt = img_lines[i]
                        global_crop_idx += 1
                        crop_entries.append((crop_name,
                                             os.path.basename(src_img),
                                             x1_pad, y1_pad, bw, bh, gt))

            # === WORD detection ===
            elif save_file_action:
                tmp_root = tempfile.mkdtemp(prefix="gan_det_")
                old_path_dir = getattr(S, 'pathDirectory', None)
                S.pathDirectory = session_dir
                S.list_of_files = main_image_list
                S.directoryout = os.path.join(tmp_root, 'out')
                S.directorytmp = os.path.join(tmp_root, 'tmp')
                os.makedirs(S.directoryout, exist_ok=True)
                os.makedirs(S.directorytmp, exist_ok=True)

                old_input_mode = None
                if hasattr(S, 'input_mode_var'):
                    old_input_mode = S.input_mode_var.get()
                    S.input_mode_var.set('load')

                for idx, src_img in enumerate(main_image_list):
                    self._set_progress(
                        15 + int(55 * idx / max(total_images, 1)),
                        f"Word detection {idx+1}/{total_images}")
                    try:
                        S.pos = idx
                        save_file_action.save_file()
                    except Exception as _det_err:
                        print(f"[step_analysis] Detection failed for "
                              f"{src_img}: {_det_err}")
                        continue

                    img_base = os.path.splitext(os.path.basename(src_img))[0]
                    wp = getattr(S, 'word_image_paths', []) or []
                    wbb = getattr(S, 'word_bboxes', []) or []
                    img_words = gan_texts_per_image.get(idx, [])
                    local_crop_i = 0

                    for i, crop_path in enumerate(wp):
                        if not os.path.exists(crop_path):
                            continue
                        crop_name = f"{img_base}_{i}.png"
                        crop_dst = os.path.join(images_dir, crop_name)
                        try:
                            shutil.move(crop_path, crop_dst)
                        except Exception:
                            try:
                                shutil.copyfile(crop_path, crop_dst)
                            except Exception:
                                continue
                        if i < len(wbb):
                            bb = wbb[i]
                            try:
                                bx, by, bw, bh = (int(bb[0]), int(bb[1]),
                                                   int(bb[2]), int(bb[3]))
                            except Exception:
                                bx, by, bw, bh = 0, 0, 0, 0
                        else:
                            bx, by, bw, bh = 0, 0, 0, 0
                        gt = user_annotations.get(global_crop_idx, '')
                        if not gt and local_crop_i < len(img_words):
                            gt = img_words[local_crop_i]
                        local_crop_i += 1
                        global_crop_idx += 1
                        crop_entries.append((crop_name,
                                             os.path.basename(src_img),
                                             bx, by, bw, bh, gt))

                if old_path_dir is not None:
                    S.pathDirectory = old_path_dir
                if old_input_mode is not None and hasattr(S, 'input_mode_var'):
                    S.input_mode_var.set(old_input_mode)
                try:
                    shutil.rmtree(tmp_root)
                except Exception:
                    pass

            else:
                # Detector unavailable – copy main images as crops
                for c_idx, (c_name, c_texts) in enumerate(copied):
                    src_p = os.path.join(session_dir, c_name)
                    if not os.path.isfile(src_p):
                        continue
                    try:
                        shutil.copy2(src_p, os.path.join(images_dir, c_name))
                    except Exception:
                        continue
                    gt = user_annotations.get(global_crop_idx, '')
                    if not gt:
                        gt = ' '.join(
                            [t.strip() for t in (c_texts or []) if t]) or ''
                    global_crop_idx += 1
                    try:
                        im = Image.open(src_p)
                        iw, ih = im.size
                    except Exception:
                        iw, ih = 0, 0
                    crop_entries.append(
                        (c_name, c_name, 0, 0, iw, ih, gt))

            self._set_progress(75, "Writing annotation file…")

            # Write IAM-format annotations.txt
            ann_path = os.path.join(images_dir, 'annotations.txt')
            with open(ann_path, 'w', encoding='utf-8') as af:
                af.write(f'# {label}-level annotations (IAM format)\n')
                af.write('# crop_name ok writer_id x y w h transcription\n')
                for crop_name, src_img, bx, by, bw, bh, gt in crop_entries:
                    af.write(f"{crop_name} ok 0 {bx} {by} {bw} {bh} {gt}\n")

            try:
                import json as _json
                meta_path = os.path.join(images_dir, 'annotation_meta.json')
                with open(meta_path, 'w', encoding='utf-8') as mf:
                    _json.dump({"annotation_type": label,
                                "total_crops": len(crop_entries),
                                "created": stamp}, mf)
            except Exception:
                pass

            folder = images_dir
            ann_file = ann_path
            self.ctx['image_dir'] = images_dir
            self.ctx['annotation_file'] = ann_path
            self.ctx['images'] = [os.path.join(images_dir, e[0])
                                  for e in crop_entries]

            self._set_progress(80, "Running corpus analysis…")
            stats = self.analyzer.analyze_folder(images_dir)
            stats["has_annotations"] = True

        except Exception as _synth_err:
            import traceback
            traceback.print_exc()
            print(f"[step_analysis] Synthetic export error: {_synth_err}")
            stats = {"error": str(_synth_err)}
            folder = self.ctx.get("image_dir", "")
            ann_file = self.ctx.get("annotation_file")

        stats["_folder"] = folder
        stats["_ann_file"] = ann_file
        return stats

    def _export_crops_from_annotation(self, folder: str, ann_file: str, ann_type: str):
        """Read an IAM-style annotation file and save crops per image.

        Crops are written to ``folder/crops/<image_basename>/``. If the crops
        directory already exists and contains files, the method does nothing.
        The ``ann_type`` is saved to ``annotation_meta.json`` alongside the
        annotations.
        """
        crops_base = os.path.join(folder, 'crops')
        if os.path.exists(crops_base) and any(os.scandir(crops_base)):
            return  # already generated
        os.makedirs(crops_base, exist_ok=True)
        try:
            with open(ann_file, 'r', encoding='utf-8') as af:
                for line in af:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) < 8:
                        continue
                    imgname = parts[0]
                    # coordinates in IAM format: x y w h after status+writer
                    try:
                        x = int(parts[3]); y = int(parts[4])
                        w = int(parts[5]); h = int(parts[6])
                    except Exception:
                        continue
                    # locate image path
                    imgpath = imgname
                    if not os.path.isabs(imgpath):
                        candidate = os.path.join(folder, imgname)
                        if os.path.exists(candidate):
                            imgpath = candidate
                        else:
                            # try context list
                            for p in self.ctx.get('images', []):
                                if os.path.basename(p) == imgname:
                                    imgpath = p
                                    break
                    if not os.path.exists(imgpath):
                        continue
                    try:
                        im = Image.open(imgpath)
                        crop = im.crop((x, y, x + w, y + h))
                    except Exception:
                        continue
                    img_base = os.path.splitext(os.path.basename(imgpath))[0]
                    outdir = os.path.join(crops_base, img_base)
                    os.makedirs(outdir, exist_ok=True)
                    # name by coordinates to avoid clashes
                    cname = f"{img_base}_{x}_{y}_{w}_{h}.png"
                    try:
                        crop.save(os.path.join(outdir, cname))
                    except Exception:
                        pass
        except Exception:
            pass
        # write metadata
        try:
            meta_path = os.path.join(folder, 'annotation_meta.json')
            with open(meta_path, 'w', encoding='utf-8') as mf:
                import json as _json
                _json.dump({"annotation_type": ann_type}, mf)
        except Exception:
            pass

    def _populate_tabs(self, stats):
        if "error" in stats:
            self.status_var.set(f"❌ Error: {stats['error']}")
            self._set_progress(0, "")
            return
        self.status_var.set("✅ Analysis complete")
        self._set_progress(100, "Done")

        self._populate_overview(stats)
        self._populate_labels(stats)
        self._populate_chars(stats)
        self._populate_writers(stats)
        self._populate_gaps(stats)

    def _populate_overview(self, stats):
        for w in self.tab_overview.winfo_children():
            w.destroy()

        cards = tk.Frame(self.tab_overview, bg=self.colors["bg_dark"])
        cards.pack(fill=tk.X, padx=10, pady=10)

        data = [
            ("📁 Dataset Type", str(stats.get("dataset_type", "—")).title()),
            ("🖼️ Images", f'{stats.get("image_count", 0):,}'),
            ("📝 Annotations", f'{stats.get("total_annotations", 0):,}'),
            ("� Crop Images", f'{stats.get("crop_count", 0):,}'),
            ("�📐 Avg Resolution", f'{stats.get("avg_width", 0)}×{stats.get("avg_height", 0)}'),
            ("💾 Size", f'{stats.get("total_size_mb", 0):.1f} MB'),
        ]
        char_stats = stats.get("character_stats", {})
        data.append(("🔤 Unique Chars", str(char_stats.get("unique_characters", 0))))
        word_stats = stats.get("word_stats", {})
        data.append(("📖 Vocabulary", f'{word_stats.get("unique_words", 0):,}'))
        style_stats = stats.get("style_stats", {})
        data.append(("✍️ Writers", str(style_stats.get("total_styles", 0))))

        for title, value in data:
            self._stat_card(cards, title, value)

        # Annotation type badge
        ann_type = stats.get("annotation_type", "unknown")
        badge_frame = tk.Frame(self.tab_overview, bg=self.colors["bg_dark"])
        badge_frame.pack(pady=5)
        tk.Label(badge_frame,
                 text=f"Annotation Type: {ann_type.upper()}" if stats.get("has_annotations") else "No Annotations (image-only analysis)",
                 font=("Segoe UI", 11, "bold"),
                 bg=self.colors["accent"] if stats.get("has_annotations") else "#ff9800",
                 fg="white", padx=15, pady=4).pack()

        # Sequence length summary
        seq = stats.get("sequence_stats", {})
        if seq:
            seq_frame = tk.LabelFrame(self.tab_overview, text=" 📏 Sequence Length ",
                                       font=("Segoe UI", 10, "bold"),
                                       bg=self.colors["bg_section"],
                                       fg=self.colors["text_light"])
            seq_frame.pack(fill=tk.X, padx=10, pady=5)
            txt = (f'Min: {seq.get("min_length", 0)}  |  '
                   f'Avg: {seq.get("avg_length", 0):.1f}  |  '
                   f'Max: {seq.get("max_length", 0)}  |  '
                   f'Median: {seq.get("median_length", 0)}')
            tk.Label(seq_frame, text=txt, font=("Segoe UI", 10),
                     bg=self.colors["bg_section"],
                     fg=self.colors["text_light"]).pack(padx=10, pady=8)

    def _stat_card(self, parent, title, value):
        f = tk.Frame(parent, bg="white", relief=tk.RIDGE, bd=1)
        f.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=4)
        tk.Label(f, text=title, font=("Segoe UI", 8),
                 bg="white", fg=self.colors["text_muted"]).pack(padx=8, pady=(6, 0))
        tk.Label(f, text=value, font=("Segoe UI", 14, "bold"),
                 bg="white", fg=self.colors["text_light"]).pack(padx=8, pady=(0, 6))

    # ------------------------------------------------------------------
    # Tab: Label Distribution
    # ------------------------------------------------------------------

    def _populate_labels(self, stats):
        for w in self.tab_labels.winfo_children():
            w.destroy()

        if not stats.get("has_annotations"):
            tk.Label(self.tab_labels,
                     text="ℹ️ No annotation labels available.\n\n"
                          "Upload annotations or annotate images to see label distribution.",
                     font=("Segoe UI", 11), bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"], justify=tk.CENTER).pack(expand=True)
            return

        word_stats = stats.get("word_stats", {})
        vocab = word_stats.get("vocabulary", [])

        if not vocab:
            tk.Label(self.tab_labels, text="No label data found.",
                     font=("Segoe UI", 11), bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"]).pack(expand=True)
            return

        # Chart
        if HAS_MPL and vocab:
            chart_frame = tk.Frame(self.tab_labels, bg=self.colors["bg_section"])
            chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            top_n = vocab[:30]
            fig = Figure(figsize=(9, 4), dpi=100,
                         facecolor=self.colors["bg_section"])
            ax = fig.add_subplot(111)
            labels = [v["word"] for v in top_n]
            counts = [v["count"] for v in top_n]
            ax.barh(range(len(labels)), counts, color=self.colors["accent"])
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels, fontsize=8)
            ax.invert_yaxis()
            ax.set_xlabel("Count")
            ax.set_title("Top 30 Labels / Words by Frequency", fontsize=11, fontweight="bold")
            ax.set_facecolor(self.colors["bg_section"])
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Table
        table_frame = tk.Frame(self.tab_labels, bg=self.colors["bg_section"])
        table_frame.pack(fill=tk.X, padx=10, pady=5)
        cols = ("label", "count", "percentage")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
        tree.heading("label", text="Label")
        tree.heading("count", text="Count")
        tree.heading("percentage", text="%")
        tree.column("label", width=200)
        tree.column("count", width=100, anchor="center")
        tree.column("percentage", width=100, anchor="center")
        total = sum(v["count"] for v in vocab) or 1
        for v in vocab[:200]:
            pct = v["count"] / total * 100
            tree.insert("", tk.END, values=(v["word"], f'{v["count"]:,}', f"{pct:.2f}%"))
        sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    # ------------------------------------------------------------------
    # Tab: Characters
    # ------------------------------------------------------------------

    def _populate_chars(self, stats):
        for w in self.tab_chars.winfo_children():
            w.destroy()

        char_stats = stats.get("character_stats", {})
        characters = char_stats.get("characters", [])

        if not characters:
            tk.Label(self.tab_chars,
                     text="No character data available.\nAnnotations are needed for character analysis.",
                     font=("Segoe UI", 11), bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"], justify=tk.CENTER).pack(expand=True)
            return

        # Chart
        if HAS_MPL:
            chart_frame = tk.Frame(self.tab_chars, bg=self.colors["bg_section"])
            chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            top = characters[:40]
            fig = Figure(figsize=(9, 3.5), dpi=100, facecolor=self.colors["bg_section"])
            ax = fig.add_subplot(111)
            chars = [c["char"] if c["char"] != " " else "⎵" for c in top]
            counts = [c["count"] for c in top]
            ax.bar(range(len(chars)), counts, color=self.colors["accent"])
            ax.set_xticks(range(len(chars)))
            ax.set_xticklabels(chars, fontsize=8)
            ax.set_ylabel("Frequency")
            ax.set_title("Character Frequency Distribution", fontsize=11, fontweight="bold")
            ax.set_facecolor(self.colors["bg_section"])
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Table
        table_frame = tk.Frame(self.tab_chars, bg=self.colors["bg_section"])
        table_frame.pack(fill=tk.X, padx=10, pady=5)
        cols = ("char", "count", "freq")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
        tree.heading("char", text="Character")
        tree.heading("count", text="Count")
        tree.heading("freq", text="Frequency %")
        tree.column("char", width=80, anchor="center")
        tree.column("count", width=100, anchor="center")
        tree.column("freq", width=100, anchor="center")
        for c in characters[:100]:
            ch = c["char"] if c["char"] != " " else "⎵"
            tree.insert("", tk.END, values=(ch, f'{c["count"]:,}', f'{c["frequency"]*100:.2f}%'))
        sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    # ------------------------------------------------------------------
    # Tab: Writers
    # ------------------------------------------------------------------

    def _populate_writers(self, stats):
        for w in self.tab_writers.winfo_children():
            w.destroy()

        style_stats = stats.get("style_stats", {})
        total_styles = style_stats.get("total_styles", 0)
        style_distribution = style_stats.get("distribution", {})

        if total_styles == 0:
            tk.Label(self.tab_writers,
                     text="ℹ️ No writer / style information found.\n\n"
                          "Writer IDs are extracted from IAM-format annotations.",
                     font=("Segoe UI", 11), bg=self.colors["bg_dark"],
                     fg=self.colors["text_muted"], justify=tk.CENTER).pack(expand=True)
            return

        # Summary
        summary = tk.Frame(self.tab_writers, bg=self.colors["bg_section"])
        summary.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(summary, text=f"✍️ Total unique writers/styles: {total_styles}",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(padx=10, pady=10)

        if style_distribution:
            # Chart
            if HAS_MPL:
                chart_frame = tk.Frame(self.tab_writers, bg=self.colors["bg_section"])
                chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

                sorted_styles = sorted(style_distribution.items(), key=lambda x: -x[1])[:30]
                fig = Figure(figsize=(9, 4), dpi=100, facecolor=self.colors["bg_section"])
                ax = fig.add_subplot(111)
                names = [s[0] for s in sorted_styles]
                counts = [s[1] for s in sorted_styles]
                ax.bar(range(len(names)), counts, color=self.colors["accent"])
                ax.set_xticks(range(len(names)))
                ax.set_xticklabels(names, fontsize=7, rotation=45, ha="right")
                ax.set_ylabel("Samples")
                ax.set_title("Writer/Style Distribution (Top 30)", fontsize=11, fontweight="bold")
                ax.set_facecolor(self.colors["bg_section"])
                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Diversity metrics
        metrics = tk.LabelFrame(self.tab_writers, text=" 📊 Diversity Metrics ",
                                 font=("Segoe UI", 10, "bold"),
                                 bg=self.colors["bg_section"],
                                 fg=self.colors["text_light"])
        metrics.pack(fill=tk.X, padx=10, pady=5)
        if style_distribution:
            counts_list = list(style_distribution.values())
            avg_samples = sum(counts_list) / len(counts_list) if counts_list else 0
            max_samples = max(counts_list) if counts_list else 0
            min_samples = min(counts_list) if counts_list else 0
            txt = (f"Average samples per writer: {avg_samples:.1f}\n"
                   f"Max: {max_samples}  |  Min: {min_samples}\n"
                   f"Imbalance ratio: {max_samples / min_samples:.1f}:1" if min_samples > 0 else "")
            tk.Label(metrics, text=txt, font=("Segoe UI", 10),
                     bg=self.colors["bg_section"],
                     fg=self.colors["text_light"], justify=tk.LEFT).pack(padx=10, pady=8)

    # ------------------------------------------------------------------
    # Tab: Gaps & Warnings
    # ------------------------------------------------------------------

    def _populate_gaps(self, stats):
        for w in self.tab_gaps.winfo_children():
            w.destroy()

        warnings = []
        has_ann = stats.get("has_annotations", False)

        if not has_ann:
            warnings.append(("⚠️ Missing Annotations",
                             "No annotation data found. Upload annotations for full analysis.",
                             "warning"))

        # Check character coverage
        char_stats = stats.get("character_stats", {})
        characters = char_stats.get("characters", [])
        rare = [c for c in characters if c["count"] < 5]
        if rare:
            warnings.append(("⚠️ Rare Characters",
                             f"{len(rare)} characters appear fewer than 5 times:\n  "
                             + ", ".join([c["char"] for c in rare[:20]]),
                             "warning"))

        # Check class imbalance
        if characters and len(characters) > 1:
            ratio = characters[0]["count"] / (characters[-1]["count"] or 1)
            if ratio > 50:
                warnings.append(("⚠️ Class Imbalance",
                                 f"Most-frequent vs least-frequent character ratio: {ratio:.0f}:1\n"
                                 "Consider oversampling or weighted loss.",
                                 "warning"))

        # Small dataset
        total = stats.get("total_annotations", 0)
        if 0 < total < 100:
            warnings.append(("⚠️ Small Dataset",
                             f"Only {total} annotations. Consider data augmentation or GAN synthesis.",
                             "warning"))

        # Missing labels
        word_stats = stats.get("word_stats", {})
        if has_ann and word_stats.get("unique_words", 0) == 0:
            warnings.append(("⚠️ No Labels Found",
                             "Annotations exist but no text labels were extracted.",
                             "error"))

        # Writer diversity
        style_stats = stats.get("style_stats", {})
        if style_stats.get("total_styles", 0) == 1:
            warnings.append(("ℹ️ Single Writer",
                             "Only one writer/style detected. Multi-writer diversity may be needed.",
                             "info"))

        if not warnings:
            warnings.append(("✅ No Issues Found",
                             "Dataset looks good! Proceed to splitting.",
                             "success"))

        # Render
        for title, desc, level in warnings:
            colors_map = {
                "warning": "#ff9800", "error": "#f44336",
                "info": self.colors["accent"], "success": "#4caf50"
            }
            frame = tk.Frame(self.tab_gaps, bg="white", relief=tk.RAISED, bd=1)
            frame.pack(fill=tk.X, padx=10, pady=5)
            bar = tk.Frame(frame, bg=colors_map.get(level, self.colors["accent"]), width=5)
            bar.pack(side=tk.LEFT, fill=tk.Y)
            inner = tk.Frame(frame, bg="white")
            inner.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=8)
            tk.Label(inner, text=title, font=("Segoe UI", 11, "bold"),
                     bg="white", fg=self.colors["text_light"]).pack(anchor="w")
            tk.Label(inner, text=desc, font=("Segoe UI", 10), bg="white",
                     fg=self.colors["text_muted"], wraplength=600,
                     justify=tk.LEFT).pack(anchor="w")

    # ------------------------------------------------------------------
    def refresh(self, ctx):
        self.ctx = ctx
        self._run_analysis()

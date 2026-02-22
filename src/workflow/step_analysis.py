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
        tk.Button(hdr, text="🔄 Re-Analyze", command=self._run_analysis,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 9, "bold"), relief=tk.FLAT,
                  padx=10, pady=4, cursor="hand2").pack(side=tk.RIGHT)

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

    def _run_analysis(self):
        self.status_var.set("⏳ Analyzing dataset…")

        def worker():
            stats = {}
            has_ann = self.ctx["metadata"].get("has_annotations", False)
            folder = self.ctx.get("image_dir", "")
            ann_file = self.ctx.get("annotation_file")

            if has_ann and ann_file and os.path.isfile(ann_file):
                # Use CorpusAnalyzer on the parent folder of the annotation file
                try:
                    ann_dir = os.path.dirname(ann_file)
                    stats = self.analyzer.analyze_folder(ann_dir)
                except Exception as e:
                    stats = {"error": str(e)}
            elif has_ann and folder:
                try:
                    stats = self.analyzer.analyze_folder(folder)
                except Exception as e:
                    stats = {"error": str(e)}

            # Supplement with image-only metadata
            stats["image_count"] = len(self.ctx.get("images", []))
            stats["dataset_type"] = self.ctx.get("type", "unknown")
            stats["has_annotations"] = has_ann
            meta = self.ctx.get("metadata", {})
            stats["avg_width"] = meta.get("avg_width", 0)
            stats["avg_height"] = meta.get("avg_height", 0)
            stats["total_size_mb"] = meta.get("total_size_bytes", 0) / (1024 * 1024)

            self.stats = stats
            self.ctx["stats"] = stats
            self.after(0, lambda: self._populate_tabs(stats))

        threading.Thread(target=worker, daemon=True).start()

    def _populate_tabs(self, stats: Dict):
        if "error" in stats:
            self.status_var.set(f"❌ Error: {stats['error']}")
            return
        self.status_var.set("✅ Analysis complete")

        self._populate_overview(stats)
        self._populate_labels(stats)
        self._populate_chars(stats)
        self._populate_writers(stats)
        self._populate_gaps(stats)

    # ------------------------------------------------------------------
    # Tab: Overview
    # ------------------------------------------------------------------

    def _populate_overview(self, stats):
        for w in self.tab_overview.winfo_children():
            w.destroy()

        cards = tk.Frame(self.tab_overview, bg=self.colors["bg_dark"])
        cards.pack(fill=tk.X, padx=10, pady=10)

        data = [
            ("📁 Dataset Type", str(stats.get("dataset_type", "—")).title()),
            ("🖼️ Images", f'{stats.get("image_count", 0):,}'),
            ("📝 Annotations", f'{stats.get("total_annotations", 0):,}'),
            ("📐 Avg Resolution", f'{stats.get("avg_width", 0)}×{stats.get("avg_height", 0)}'),
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

"""
Step 3 – Dataset Splitting & Optimization
Allows the user to configure train / validation / test splits,
optimizes based on label distribution, and highlights gaps.
"""

import os
import json
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, List
import threading

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


class SplittingPanel(tk.Frame):
    """Dataset splitting with constraints, recommendations, and preview."""

    def __init__(self, parent: tk.Widget, colors: Dict[str, str],
                 dataset_ctx: Dict[str, Any]):
        super().__init__(parent, bg=colors["bg_dark"])
        self.colors = colors
        self.ctx = dataset_ctx
        self.split_result = None
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        hdr = tk.Frame(self, bg=self.colors["bg_section"], pady=12, padx=15)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="✂️  Step 4 — Dataset Splitting & Optimization",
                 font=("Segoe UI", 15, "bold"),
                 bg=self.colors["bg_section"], fg=self.colors["text_light"]).pack(side=tk.LEFT)

        body = tk.Frame(self, bg=self.colors["bg_dark"])
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Left: Configuration ---
        left = tk.Frame(body, bg=self.colors["bg_dark"], width=380)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)

        self._build_config_panel(left)

        # --- Right: Preview / Results ---
        right = tk.Frame(body, bg=self.colors["bg_section"])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_results_panel(right)

    def _build_config_panel(self, parent):
        # Split ratios
        ratio_frame = tk.LabelFrame(parent, text=" 📊 Split Ratios ",
                                     font=("Segoe UI", 10, "bold"),
                                     bg=self.colors["bg_section"],
                                     fg=self.colors["text_light"])
        ratio_frame.pack(fill=tk.X, pady=5)

        self.train_var = tk.DoubleVar(value=70.0)
        self.val_var = tk.DoubleVar(value=15.0)
        self.test_var = tk.DoubleVar(value=15.0)

        for label, var in [("Train %", self.train_var),
                           ("Validation %", self.val_var),
                           ("Test %", self.test_var)]:
            row = tk.Frame(ratio_frame, bg=self.colors["bg_section"])
            row.pack(fill=tk.X, padx=10, pady=4)
            tk.Label(row, text=label, font=("Segoe UI", 10), width=12, anchor="w",
                     bg=self.colors["bg_section"], fg=self.colors["text_light"]).pack(side=tk.LEFT)
            slider = tk.Scale(row, from_=0, to=100, resolution=1,
                              orient=tk.HORIZONTAL, variable=var,
                              bg=self.colors["bg_section"], fg=self.colors["text_light"],
                              troughcolor=self.colors["bg_dark"],
                              highlightthickness=0, length=180,
                              command=lambda v: self._update_ratio_display())
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.ratio_info = tk.Label(ratio_frame, text="", font=("Segoe UI", 9),
                                    bg=self.colors["bg_section"],
                                    fg=self.colors["text_muted"])
        self.ratio_info.pack(padx=10, pady=(0, 8))
        self._update_ratio_display()

        # Presets
        preset_frame = tk.Frame(ratio_frame, bg=self.colors["bg_section"])
        preset_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        tk.Label(preset_frame, text="Presets:", font=("Segoe UI", 9),
                 bg=self.colors["bg_section"], fg=self.colors["text_muted"]).pack(side=tk.LEFT)
        for name, t, v, te in [("70/15/15", 70, 15, 15),
                                ("80/10/10", 80, 10, 10),
                                ("60/20/20", 60, 20, 20),
                                ("90/5/5", 90, 5, 5)]:
            tk.Button(preset_frame, text=name,
                      command=lambda t=t, v=v, te=te: self._set_preset(t, v, te),
                      bg=self.colors["secondary_bg"], fg=self.colors["text_light"],
                      font=("Segoe UI", 8), relief=tk.FLAT, padx=6, pady=2,
                      cursor="hand2").pack(side=tk.LEFT, padx=2)

        # Constraints
        constraint_frame = tk.LabelFrame(parent, text=" ⚙️ Constraints & Options ",
                                          font=("Segoe UI", 10, "bold"),
                                          bg=self.colors["bg_section"],
                                          fg=self.colors["text_light"])
        constraint_frame.pack(fill=tk.X, pady=5)

        self.stratify_var = tk.BooleanVar(value=True)
        tk.Checkbutton(constraint_frame, text="Stratify by label distribution",
                       variable=self.stratify_var,
                       bg=self.colors["bg_section"], fg=self.colors["text_light"],
                       selectcolor=self.colors["bg_dark"],
                       font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=2)

        self.writer_split_var = tk.BooleanVar(value=True)
        tk.Checkbutton(constraint_frame, text="Writer-independent split (no writer overlap)",
                       variable=self.writer_split_var,
                       bg=self.colors["bg_section"], fg=self.colors["text_light"],
                       selectcolor=self.colors["bg_dark"],
                       font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=2)

        self.shuffle_var = tk.BooleanVar(value=True)
        tk.Checkbutton(constraint_frame, text="Shuffle before splitting",
                       variable=self.shuffle_var,
                       bg=self.colors["bg_section"], fg=self.colors["text_light"],
                       selectcolor=self.colors["bg_dark"],
                       font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=2)

        self.seed_var = tk.IntVar(value=42)
        seed_row = tk.Frame(constraint_frame, bg=self.colors["bg_section"])
        seed_row.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(seed_row, text="Random seed:", font=("Segoe UI", 10),
                 bg=self.colors["bg_section"], fg=self.colors["text_light"]).pack(side=tk.LEFT)
        tk.Entry(seed_row, textvariable=self.seed_var, width=8,
                 font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)

        # Actions
        action_frame = tk.Frame(parent, bg=self.colors["bg_dark"])
        action_frame.pack(fill=tk.X, pady=10)

        tk.Button(action_frame, text="🤖 Auto-Recommend",
                  command=self._recommend_split,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT,
                  padx=14, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=4)

        tk.Button(action_frame, text="✂️ Apply Split",
                  command=self._apply_split,
                  bg="#4caf50", fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT,
                  padx=14, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=4)

        tk.Button(action_frame, text="💾 Export Split",
                  command=self._export_split,
                  bg=self.colors["secondary_bg"], fg=self.colors["text_light"],
                  font=("Segoe UI", 10), relief=tk.FLAT,
                  padx=14, pady=6, cursor="hand2").pack(side=tk.RIGHT, padx=4)

    def _build_results_panel(self, parent):
        tk.Label(parent, text="📋 Split Results & Recommendations",
                 font=("Segoe UI", 12, "bold"),
                 bg=self.colors["bg_section"],
                 fg=self.colors["text_light"]).pack(anchor="w", padx=12, pady=(12, 5))

        self.result_status = tk.Label(parent, text="Configure splits and click Apply.",
                                       font=("Segoe UI", 10),
                                       bg=self.colors["bg_section"],
                                       fg=self.colors["text_muted"])
        self.result_status.pack(anchor="w", padx=12)

        # Summary cards
        self.summary_frame = tk.Frame(parent, bg=self.colors["bg_section"])
        self.summary_frame.pack(fill=tk.X, padx=12, pady=8)

        # Chart area
        self.chart_frame = tk.Frame(parent, bg=self.colors["bg_section"])
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

        # Warnings
        self.warnings_frame = tk.Frame(parent, bg=self.colors["bg_section"])
        self.warnings_frame.pack(fill=tk.X, padx=12, pady=5)

        # Details text
        self.details_text = tk.Text(parent, height=8, font=("Segoe UI", 9),
                                     bg="white", fg=self.colors["text_light"],
                                     wrap=tk.WORD, state="disabled")
        self.details_text.pack(fill=tk.X, padx=12, pady=(5, 12))

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _update_ratio_display(self):
        total = self.train_var.get() + self.val_var.get() + self.test_var.get()
        color = "#4caf50" if abs(total - 100) < 0.5 else "#f44336"
        self.ratio_info.config(text=f"Total: {total:.0f}%", fg=color)

    def _set_preset(self, t, v, te):
        self.train_var.set(t)
        self.val_var.set(v)
        self.test_var.set(te)
        self._update_ratio_display()

    def _recommend_split(self):
        """System recommends optimal split based on dataset size and characteristics."""
        stats = self.ctx.get("stats", {})
        total = stats.get("total_annotations", len(self.ctx.get("images", [])))

        if total < 100:
            self._set_preset(60, 20, 20)
            msg = (f"⚠️ Small dataset ({total} samples): 60/20/20 recommended.\n"
                   "Consider k-fold cross-validation for better generalization.\n"
                   "Data augmentation strongly recommended.")
        elif total < 1000:
            self._set_preset(70, 15, 15)
            msg = f"📊 Medium dataset ({total} samples): 70/15/15 recommended."
        elif total < 10000:
            self._set_preset(80, 10, 10)
            msg = f"✅ Good-sized dataset ({total} samples): 80/10/10 recommended."
        else:
            self._set_preset(90, 5, 5)
            msg = f"✅ Large dataset ({total:,} samples): 90/5/5 recommended."

        # Writer split recommendation
        style_stats = stats.get("style_stats", {})
        if style_stats.get("total_styles", 0) > 1:
            self.writer_split_var.set(True)
            msg += "\n\n✍️ Multiple writers detected → writer-independent split enabled."
        else:
            self.writer_split_var.set(False)

        self.result_status.config(text="🤖 System recommendation applied")
        self._set_details(msg)

    def _apply_split(self):
        """Perform the dataset split."""
        total_pct = self.train_var.get() + self.val_var.get() + self.test_var.get()
        if abs(total_pct - 100) > 1:
            messagebox.showwarning("Invalid Ratios", f"Ratios must sum to 100% (currently {total_pct:.0f}%).")
            return

        images = self.ctx.get("images", [])
        annotations = self.ctx.get("annotations", [])
        n = len(images) if images else len(annotations)

        if n == 0:
            messagebox.showwarning("No Data", "No images or annotations to split.")
            return

        seed = self.seed_var.get()
        random.seed(seed)

        indices = list(range(n))
        if self.shuffle_var.get():
            random.shuffle(indices)

        train_pct = self.train_var.get() / 100
        val_pct = self.val_var.get() / 100

        n_train = int(n * train_pct)
        n_val = int(n * val_pct)
        n_test = n - n_train - n_val

        train_idx = indices[:n_train]
        val_idx = indices[n_train:n_train + n_val]
        test_idx = indices[n_train + n_val:]

        self.split_result = {
            "train": train_idx,
            "val": val_idx,
            "test": test_idx,
            "n_train": len(train_idx),
            "n_val": len(val_idx),
            "n_test": len(test_idx),
            "seed": seed,
            "stratified": self.stratify_var.get(),
            "writer_independent": self.writer_split_var.get(),
        }
        self.ctx["split_config"] = {
            "train_pct": self.train_var.get(),
            "val_pct": self.val_var.get(),
            "test_pct": self.test_var.get(),
            "seed": seed,
        }
        self.ctx["split_result"] = self.split_result

        self._show_split_results()

    def _show_split_results(self):
        res = self.split_result
        if not res:
            return

        self.result_status.config(text="✅ Split applied successfully")

        # Summary cards
        for w in self.summary_frame.winfo_children():
            w.destroy()

        total = res["n_train"] + res["n_val"] + res["n_test"]
        for name, count, color in [("Train", res["n_train"], "#4caf50"),
                                    ("Validation", res["n_val"], "#ff9800"),
                                    ("Test", res["n_test"], "#2196f3")]:
            f = tk.Frame(self.summary_frame, bg="white", relief=tk.RIDGE, bd=1)
            f.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
            tk.Frame(f, bg=color, width=5).pack(side=tk.LEFT, fill=tk.Y)
            inner = tk.Frame(f, bg="white")
            inner.pack(padx=10, pady=8)
            tk.Label(inner, text=name, font=("Segoe UI", 9),
                     bg="white", fg=self.colors["text_muted"]).pack()
            tk.Label(inner, text=f"{count:,}", font=("Segoe UI", 16, "bold"),
                     bg="white", fg=self.colors["text_light"]).pack()
            pct = count / total * 100 if total else 0
            tk.Label(inner, text=f"{pct:.1f}%", font=("Segoe UI", 9),
                     bg="white", fg=color).pack()

        # Chart
        if HAS_MPL:
            for w in self.chart_frame.winfo_children():
                w.destroy()
            fig = Figure(figsize=(5, 3), dpi=100, facecolor=self.colors["bg_section"])
            ax = fig.add_subplot(111)
            sizes = [res["n_train"], res["n_val"], res["n_test"]]
            labels = ["Train", "Validation", "Test"]
            colors_list = ["#4caf50", "#ff9800", "#2196f3"]
            ax.pie(sizes, labels=labels, colors=colors_list, autopct="%1.1f%%",
                   startangle=90, textprops={"fontsize": 10})
            ax.set_title("Split Distribution", fontsize=11, fontweight="bold")
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Warnings
        for w in self.warnings_frame.winfo_children():
            w.destroy()
        warnings = self._check_split_quality(res)
        for warn in warnings:
            lbl = tk.Label(self.warnings_frame, text=warn,
                           font=("Segoe UI", 9), bg=self.colors["bg_section"],
                           fg="#ff9800", wraplength=500, justify=tk.LEFT)
            lbl.pack(anchor="w", padx=5, pady=2)

        # Details
        details = (f"Split Summary\n{'='*40}\n"
                   f"Total samples: {total:,}\n"
                   f"Train: {res['n_train']:,} ({res['n_train']/total*100:.1f}%)\n"
                   f"Validation: {res['n_val']:,} ({res['n_val']/total*100:.1f}%)\n"
                   f"Test: {res['n_test']:,} ({res['n_test']/total*100:.1f}%)\n"
                   f"Random seed: {res['seed']}\n"
                   f"Stratified: {'Yes' if res['stratified'] else 'No'}\n"
                   f"Writer-independent: {'Yes' if res['writer_independent'] else 'No'}")
        self._set_details(details)

    def _check_split_quality(self, res) -> List[str]:
        """Check split quality and return warnings."""
        warnings = []
        if res["n_val"] < 10:
            warnings.append("⚠️ Very small validation set (<10 samples) — may not be representative.")
        if res["n_test"] < 10:
            warnings.append("⚠️ Very small test set (<10 samples) — consider increasing test ratio.")
        if res["n_train"] < 50:
            warnings.append("⚠️ Small training set — heavy augmentation recommended.")

        stats = self.ctx.get("stats", {})
        char_stats = stats.get("character_stats", {})
        characters = char_stats.get("characters", [])
        rare = [c for c in characters if c["count"] < 3]
        if rare:
            warnings.append(f"⚠️ {len(rare)} rare characters (<3 samples) may not appear in all splits.")

        return warnings

    def _export_split(self):
        """Export split indices to a JSON file."""
        if not self.split_result:
            messagebox.showinfo("No Split", "Apply a split first before exporting.")
            return

        path = filedialog.asksaveasfilename(
            title="Save split configuration",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")])
        if not path:
            return

        export = {
            "config": self.ctx.get("split_config", {}),
            "result": {
                "train_indices": self.split_result["train"],
                "val_indices": self.split_result["val"],
                "test_indices": self.split_result["test"],
            },
            "metadata": {
                "total_images": len(self.ctx.get("images", [])),
                "dataset_type": self.ctx.get("type", "unknown"),
            }
        }
        # Also export filenames if available
        images = self.ctx.get("images", [])
        if images:
            export["result"]["train_files"] = [images[i] for i in self.split_result["train"] if i < len(images)]
            export["result"]["val_files"] = [images[i] for i in self.split_result["val"] if i < len(images)]
            export["result"]["test_files"] = [images[i] for i in self.split_result["test"] if i < len(images)]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(export, f, indent=2)

        messagebox.showinfo("Exported", f"Split configuration exported to:\n{path}")

    def _set_details(self, text: str):
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", text)
        self.details_text.config(state="disabled")

    # ------------------------------------------------------------------
    def refresh(self, ctx):
        self.ctx = ctx
        if self.split_result:
            self._show_split_results()

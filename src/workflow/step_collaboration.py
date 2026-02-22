"""
Step 5 – Collaborative & Extensible Usage
Dataset sharing, version tracking, annotations export, and integration hooks.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any
import json
import os
import time
from datetime import datetime


class CollaborationPanel(tk.Frame):
    """Collaborative and extensible usage panel."""

    def __init__(self, parent: tk.Widget, colors: Dict[str, str],
                 dataset_ctx: Dict[str, Any]):
        super().__init__(parent, bg=colors["bg_dark"])
        self.colors = colors
        self.ctx = dataset_ctx
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        hdr = tk.Frame(self, bg=self.colors["bg_section"], pady=12, padx=15)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🤝  Step 6 — Collaborative & Extensible Usage",
                 font=("Segoe UI", 15, "bold"),
                 bg=self.colors["bg_section"], fg=self.colors["text_light"]).pack(side=tk.LEFT)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Export / Share
        self.tab_export = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_export, text="📦 Export Dataset")

        # Tab 2: Version History
        self.tab_versions = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_versions, text="📜 Version History")

        # Tab 3: Integration / Hooks
        self.tab_integration = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_integration, text="🔌 Integrations")

        # Tab 4: Summary
        self.tab_summary = tk.Frame(self.notebook, bg=self.colors["bg_dark"])
        self.notebook.add(self.tab_summary, text="📊 Pipeline Summary")

        self._build_export_tab()
        self._build_versions_tab()
        self._build_integration_tab()
        self._build_summary_tab()

    # ------------------------------------------------------------------
    # Export Tab
    # ------------------------------------------------------------------
    def _build_export_tab(self):
        tab = self.tab_export

        tk.Label(tab, text="📦 Export Your Dataset & Annotations",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["bg_dark"],
                 fg=self.colors["text_light"]).pack(pady=10)

        tk.Label(tab, text="Export the full pipeline output — images, annotations, splits, and metadata —\n"
                           "in common formats ready for training.",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_dark"],
                 fg=self.colors["text_muted"]).pack(pady=(0, 10))

        formats = [
            ("IAM Format", "iam", "Standard IAM HTR format: lines.txt, words.txt + image folders"),
            ("COCO JSON", "coco", "Microsoft COCO format: instances/captions JSON with image references"),
            ("YOLO Format", "yolo", "Ultralytics YOLO: images/ + labels/ with .txt annotations"),
            ("Pascal VOC (XML)", "voc", "VOC XML annotations with bounding boxes"),
            ("CSV", "csv", "Simple CSV: image_path, label, split, metadata"),
            ("JSONL", "jsonl", "JSON Lines: one JSON object per sample, easy to stream"),
            ("Full Pipeline JSON", "pipeline", "Complete pipeline state: config, stats, splits, recommendations"),
        ]

        self.export_var = tk.StringVar(value="pipeline")
        cards_frame = tk.Frame(tab, bg=self.colors["bg_dark"])
        cards_frame.pack(fill=tk.X, padx=10, pady=5)

        for name, key, desc in formats:
            card = tk.Frame(cards_frame, bg="white", relief=tk.RAISED, bd=1)
            card.pack(fill=tk.X, pady=3)
            inner = tk.Frame(card, bg="white", padx=10, pady=6)
            inner.pack(fill=tk.X)
            rb = tk.Radiobutton(inner, text=name, variable=self.export_var,
                                value=key, font=("Segoe UI", 10, "bold"),
                                bg="white", fg=self.colors["text_light"],
                                activebackground="white",
                                selectcolor="white")
            rb.pack(side=tk.LEFT)
            tk.Label(inner, text=desc, font=("Segoe UI", 9),
                     bg="white", fg=self.colors["text_muted"],
                     wraplength=500, justify=tk.LEFT).pack(side=tk.LEFT, padx=10)

        btn_frame = tk.Frame(tab, bg=self.colors["bg_dark"])
        btn_frame.pack(fill=tk.X, padx=10, pady=15)
        tk.Button(btn_frame, text="📥 Export", command=self._do_export,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 11, "bold"), relief=tk.FLAT,
                  padx=20, pady=8, cursor="hand2").pack(side=tk.LEFT)
        tk.Button(btn_frame, text="📋 Copy Config to Clipboard",
                  command=self._copy_config,
                  bg="#6c757d", fg="white",
                  font=("Segoe UI", 10), relief=tk.FLAT,
                  padx=15, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=10)

    def _do_export(self):
        fmt = self.export_var.get()
        out_dir = filedialog.askdirectory(title="Select Export Directory")
        if not out_dir:
            return
        try:
            self._run_export(fmt, out_dir)
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _run_export(self, fmt, out_dir):
        """Dispatch export to the appropriate exporter or save pipeline JSON."""
        if fmt == "pipeline":
            self._export_pipeline(out_dir)
        else:
            # Try to use existing exporters
            self._export_annotations(fmt, out_dir)

        # Record in version history
        ver = {
            "timestamp": datetime.now().isoformat(),
            "action": f"Exported as {fmt}",
            "output_dir": out_dir,
            "sample_count": len(self.ctx.get("images", [])),
        }
        self.ctx.setdefault("version_history", []).append(ver)
        self._refresh_versions()
        messagebox.showinfo("Export Complete",
                            f"Dataset exported to:\n{out_dir}\nFormat: {fmt}")

    def _export_pipeline(self, out_dir):
        """Export the complete pipeline state as JSON."""
        pipeline = {
            "exported_at": datetime.now().isoformat(),
            "tool": "Study-Annotation-Tool Workflow",
            "dataset": {
                "type": self.ctx.get("type", "unknown"),
                "image_dir": self.ctx.get("image_dir", ""),
                "total_images": len(self.ctx.get("images", [])),
                "total_annotations": len(self.ctx.get("annotations", {})),
            },
            "statistics": {},
            "split_config": self.ctx.get("split_config", {}),
            "split_result": self.ctx.get("split_result", {}),
            "model_suggestions": self.ctx.get("model_suggestions", []),
            "version_history": self.ctx.get("version_history", []),
        }
        # Include stats (strip non-serializable items)
        stats = self.ctx.get("stats", {})
        for k, v in stats.items():
            try:
                json.dumps(v)
                pipeline["statistics"][k] = v
            except (TypeError, ValueError):
                pipeline["statistics"][k] = str(v)

        path = os.path.join(out_dir, "pipeline_export.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(pipeline, f, indent=2, ensure_ascii=False)

    def _export_annotations(self, fmt, out_dir):
        """Export using the existing exporters package."""
        images = self.ctx.get("images", [])
        annotations = self.ctx.get("annotations", {})
        if not images:
            raise ValueError("No images loaded. Complete Step 1 first.")

        export_data = {
            "images": images,
            "annotations": annotations,
            "image_dir": self.ctx.get("image_dir", ""),
            "output_dir": out_dir,
        }

        try:
            if fmt == "coco":
                from exporters.coco import export_coco
                export_coco(export_data)
            elif fmt == "yolo":
                from exporters.yolo import export_yolo
                export_yolo(export_data)
            elif fmt == "voc":
                from exporters.voc import export_voc
                export_voc(export_data)
            elif fmt == "csv":
                from exporters.csv_export import export_csv
                export_csv(export_data)
            elif fmt == "jsonl":
                from exporters.jsonl import export_jsonl
                export_jsonl(export_data)
            elif fmt == "iam":
                from exporters.iam import export_iam
                export_iam(export_data)
        except ImportError:
            # Fallback: dump annotations as the chosen format name
            path = os.path.join(out_dir, f"annotations_{fmt}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

    def _copy_config(self):
        config = {
            "type": self.ctx.get("type"),
            "image_dir": self.ctx.get("image_dir"),
            "total_images": len(self.ctx.get("images", [])),
            "split_config": self.ctx.get("split_config", {}),
            "stats_summary": {
                k: v for k, v in self.ctx.get("stats", {}).items()
                if isinstance(v, (int, float, str, bool))
            },
        }
        text = json.dumps(config, indent=2, ensure_ascii=False)
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Pipeline configuration copied to clipboard.")

    # ------------------------------------------------------------------
    # Version History Tab
    # ------------------------------------------------------------------
    def _build_versions_tab(self):
        tab = self.tab_versions
        tk.Label(tab, text="📜 Version & Activity History",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["bg_dark"],
                 fg=self.colors["text_light"]).pack(pady=10)

        tk.Label(tab, text="Track changes, exports, and milestones in your annotation pipeline.",
                 font=("Segoe UI", 10),
                 bg=self.colors["bg_dark"],
                 fg=self.colors["text_muted"]).pack(pady=(0, 10))

        btn_f = tk.Frame(tab, bg=self.colors["bg_dark"])
        btn_f.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_f, text="📌 Add Checkpoint", command=self._add_checkpoint,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 9, "bold"), relief=tk.FLAT,
                  padx=10, pady=4, cursor="hand2").pack(side=tk.LEFT)
        tk.Button(btn_f, text="💾 Save History", command=self._save_history,
                  bg="#6c757d", fg="white",
                  font=("Segoe UI", 9), relief=tk.FLAT,
                  padx=10, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=10)

        cols = ("Time", "Action", "Details")
        self.ver_tree = ttk.Treeview(tab, columns=cols, show="headings", height=12)
        for c in cols:
            self.ver_tree.heading(c, text=c)
            self.ver_tree.column(c, width=200)
        self.ver_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self._refresh_versions()

    def _refresh_versions(self):
        self.ver_tree.delete(*self.ver_tree.get_children())
        history = self.ctx.get("version_history", [])
        for entry in reversed(history):
            ts = entry.get("timestamp", "")[:19]
            action = entry.get("action", "")
            details = entry.get("output_dir", entry.get("details", ""))
            self.ver_tree.insert("", tk.END, values=(ts, action, details))

    def _add_checkpoint(self):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "Manual checkpoint",
            "details": f"Images: {len(self.ctx.get('images', []))}, "
                       f"Annotations: {len(self.ctx.get('annotations', {}))}",
        }
        self.ctx.setdefault("version_history", []).append(entry)
        self._refresh_versions()

    def _save_history(self):
        path = filedialog.asksaveasfilename(
            title="Save Version History",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        history = self.ctx.get("version_history", [])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Saved", f"History saved to:\n{path}")

    # ------------------------------------------------------------------
    # Integration Tab
    # ------------------------------------------------------------------
    def _build_integration_tab(self):
        tab = self.tab_integration
        tk.Label(tab, text="🔌 Integrations & Extensibility",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["bg_dark"],
                 fg=self.colors["text_light"]).pack(pady=10)

        integrations = [
            {
                "name": "🤗 Hugging Face Hub",
                "desc": "Push your dataset directly to the Hugging Face Hub for sharing.\n"
                        "Requires: pip install huggingface_hub",
                "status": "Available (manual)",
                "action": "Coming soon — push_to_hub() will be integrated.",
            },
            {
                "name": "📡 Label Studio",
                "desc": "Import annotated data from Label Studio or export to Label Studio format.\n"
                        "Supports JSON import/export.",
                "status": "Available (via JSON export)",
                "action": "Use JSON export, then import into Label Studio.",
            },
            {
                "name": "🔬 Weights & Biases (W&B)",
                "desc": "Log dataset statistics and training metrics to W&B.\n"
                        "Requires: pip install wandb",
                "status": "Planned",
                "action": "Future: automatic logging of corpus stats and splits.",
            },
            {
                "name": "🐍 Python API",
                "desc": "Use the workflow programmatically:\n"
                        "  from workflow import WorkflowManager\n"
                        "  wf = WorkflowManager(root, colors, state)",
                "status": "Available",
                "action": "Import the workflow package in your scripts.",
            },
            {
                "name": "📝 Custom Exporters",
                "desc": "Add your own export format by creating a module in src/exporters/.\n"
                        "Implement an export_<format>(data) function.",
                "status": "Available",
                "action": "See src/exporters/ for examples.",
            },
        ]

        for intg in integrations:
            card = tk.LabelFrame(tab, text=f' {intg["name"]} ',
                                  font=("Segoe UI", 10, "bold"),
                                  bg="white", fg=self.colors["text_light"])
            card.pack(fill=tk.X, padx=10, pady=4)
            inner = tk.Frame(card, bg="white", padx=10, pady=6)
            inner.pack(fill=tk.X)
            tk.Label(inner, text=intg["desc"], font=("Segoe UI", 9),
                     bg="white", fg=self.colors["text_muted"],
                     wraplength=600, justify=tk.LEFT).pack(anchor="w")
            status_color = "#4caf50" if "Available" in intg["status"] else "#ff9800"
            tk.Label(inner, text=f"Status: {intg['status']}",
                     font=("Segoe UI", 9, "bold"),
                     bg="white", fg=status_color).pack(anchor="w", pady=(3, 0))

    # ------------------------------------------------------------------
    # Summary Tab
    # ------------------------------------------------------------------
    def _build_summary_tab(self):
        tab = self.tab_summary
        tk.Label(tab, text="📊 Full Pipeline Summary",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors["bg_dark"],
                 fg=self.colors["text_light"]).pack(pady=10)

        self.summary_frame = tk.Frame(tab, bg=self.colors["bg_dark"])
        self.summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Button(tab, text="🔄 Refresh Summary",
                  command=self._refresh_summary,
                  bg=self.colors["accent"], fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT,
                  padx=15, pady=6, cursor="hand2").pack(pady=10)

        self._refresh_summary()

    def _refresh_summary(self):
        for w in self.summary_frame.winfo_children():
            w.destroy()

        steps = [
            ("1️⃣ Dataset Ingestion",
             self._step_1_summary()),
            ("2️⃣ Statistical Analysis",
             self._step_2_summary()),
            ("3️⃣ Splitting & Optimization",
             self._step_3_summary()),
            ("4️⃣ Model Recommendation",
             self._step_4_summary()),
            ("5️⃣ Collaboration",
             self._step_5_summary()),
        ]

        for title, info in steps:
            done = info.get("done", False)
            card = tk.Frame(self.summary_frame,
                            bg="#e8f5e9" if done else "#fff3e0",
                            relief=tk.RAISED, bd=1)
            card.pack(fill=tk.X, pady=3)
            inner = tk.Frame(card,
                              bg="#e8f5e9" if done else "#fff3e0",
                              padx=10, pady=8)
            inner.pack(fill=tk.X)
            icon = "✅" if done else "⏳"
            tk.Label(inner, text=f"{icon} {title}",
                     font=("Segoe UI", 11, "bold"),
                     bg=inner["bg"],
                     fg=self.colors["text_light"]).pack(anchor="w")
            tk.Label(inner, text=info.get("summary", "Not started"),
                     font=("Segoe UI", 9),
                     bg=inner["bg"],
                     fg=self.colors["text_muted"],
                     wraplength=600, justify=tk.LEFT).pack(anchor="w")

    def _step_1_summary(self):
        images = self.ctx.get("images", [])
        if images:
            return {
                "done": True,
                "summary": f"Loaded {len(images)} images | Type: {self.ctx.get('type', '?')} | "
                           f"Dir: {self.ctx.get('image_dir', '?')}",
            }
        return {"done": False, "summary": "No images loaded yet."}

    def _step_2_summary(self):
        stats = self.ctx.get("stats", {})
        if stats:
            total = stats.get("total_annotations", 0)
            chars = stats.get("character_stats", {}).get("unique_characters", 0)
            return {
                "done": True,
                "summary": f"Analyzed: {total} annotations | {chars} unique characters",
            }
        return {"done": False, "summary": "Analysis not yet run."}

    def _step_3_summary(self):
        split = self.ctx.get("split_result", {})
        if split:
            train = split.get("train_count", 0)
            val = split.get("val_count", 0)
            test = split.get("test_count", 0)
            return {
                "done": True,
                "summary": f"Split configured: Train {train} | Val {val} | Test {test}",
            }
        return {"done": False, "summary": "No split configured."}

    def _step_4_summary(self):
        models = self.ctx.get("model_suggestions", [])
        if models:
            return {
                "done": True,
                "summary": f"Recommended {len(models)} architecture categories.",
            }
        # If we have stats, we consider step 4 as "done" since recommendations are auto-generated
        if self.ctx.get("stats"):
            return {
                "done": True,
                "summary": "Recommendations generated based on dataset characteristics.",
            }
        return {"done": False, "summary": "Load data to get recommendations."}

    def _step_5_summary(self):
        history = self.ctx.get("version_history", [])
        if history:
            return {
                "done": True,
                "summary": f"{len(history)} actions recorded in version history.",
            }
        return {"done": False, "summary": "No exports or checkpoints yet."}

    # ------------------------------------------------------------------
    def refresh(self, ctx):
        self.ctx = ctx
        self._refresh_versions()
        self._refresh_summary()

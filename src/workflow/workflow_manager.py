"""
Workflow Manager
Orchestrates the 5-step workflow with a wizard-style navigation.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional, Any

import state as S


STEP_DEFINITIONS = [
    {"id": 1, "title": "Dataset Ingestion",      "icon": "📥", "key": "ingestion"},
    {"id": 2, "title": "Annotation",              "icon": "✏️", "key": "annotation"},
    {"id": 3, "title": "Statistical Analysis",    "icon": "📊", "key": "analysis"},
    {"id": 4, "title": "Splitting & Optimization", "icon": "✂️", "key": "splitting"},
    {"id": 5, "title": "Model Recommendation",    "icon": "🤖", "key": "recommendation"},
    {"id": 6, "title": "Collaboration & Export",   "icon": "🤝", "key": "collaboration"},
]


class WorkflowManager:
    """Manages the 5-step workflow wizard."""

    def __init__(self, parent: tk.Widget, colors: Dict[str, str],
                 on_close_callback: Callable = None):
        self.parent = parent
        self.colors = colors
        self.on_close_callback = on_close_callback

        self.current_step = 0  # 0-indexed
        self.step_panels = {}  # key -> panel widget
        self.step_builders = {}  # key -> builder function
        self.step_states = {s["key"]: "not-started" for s in STEP_DEFINITIONS}

        # Dataset context shared across steps
        self.dataset_ctx: Dict[str, Any] = {
            "type": None,           # raw / synthetic / preannotated / external
            "image_dir": None,
            "annotation_file": None,
            "images": [],
            "annotations": [],
            "metadata": {},
            "stats": None,
            "split_config": None,
            "split_result": None,
            "model_suggestions": [],
            "version_history": [],
        }

        # Main outer container
        self.container = tk.Frame(parent, bg=colors["bg_dark"])

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Top bar: stepper indicator
        self._build_stepper()
        # Bottom bar: navigation buttons (packed before content so it stays fixed)
        self._build_nav_bar()
        # Content area (fills remaining space)
        self.content_frame = tk.Frame(self.container, bg=self.colors["bg_dark"])
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        # Build all step panels (lazy: build on first visit)
        self._show_step(0)

    def _build_stepper(self):
        """Horizontal step indicator across the top."""
        stepper = tk.Frame(self.container, bg=self.colors["bg_panel"], pady=8)
        stepper.pack(fill=tk.X)

        self.step_labels = []
        self.step_connectors = []

        for i, step in enumerate(STEP_DEFINITIONS):
            if i > 0:
                conn = tk.Frame(stepper, bg=self.colors["border"], height=2, width=40)
                conn.pack(side=tk.LEFT, pady=12)
                self.step_connectors.append(conn)

            frame = tk.Frame(stepper, bg=self.colors["bg_panel"], cursor="hand2")
            frame.pack(side=tk.LEFT, padx=6)

            circle = tk.Label(frame, text=str(step["id"]),
                              font=("Segoe UI", 11, "bold"),
                              width=3, height=1,
                              bg=self.colors["border"], fg=self.colors["text_muted"],
                              relief=tk.FLAT)
            circle.pack()

            lbl = tk.Label(frame, text=f'{step["icon"]} {step["title"]}',
                           font=("Segoe UI", 9),
                           bg=self.colors["bg_panel"], fg=self.colors["text_muted"])
            lbl.pack()

            # Click to jump (only to completed/current)
            frame.bind("<Button-1>", lambda e, idx=i: self._on_step_click(idx))
            circle.bind("<Button-1>", lambda e, idx=i: self._on_step_click(idx))
            lbl.bind("<Button-1>", lambda e, idx=i: self._on_step_click(idx))

            self.step_labels.append((frame, circle, lbl))

    def _build_nav_bar(self):
        nav = tk.Frame(self.container, bg=self.colors["bg_panel"], pady=8, padx=12)
        nav.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_prev = tk.Button(nav, text="◀ Previous", command=self._go_prev,
                                  bg=self.colors["secondary_bg"],
                                  fg=self.colors["text_light"],
                                  font=("Segoe UI", 10, "bold"),
                                  relief=tk.FLAT, padx=18, pady=6, cursor="hand2")
        self.btn_prev.pack(side=tk.LEFT)

        self.btn_next = tk.Button(nav, text="Next ▶", command=self._go_next,
                                  bg=self.colors["accent"],
                                  fg="white",
                                  font=("Segoe UI", 10, "bold"),
                                  relief=tk.FLAT, padx=18, pady=6, cursor="hand2")
        self.btn_next.pack(side=tk.RIGHT)

        self.nav_info = tk.Label(nav, text="", font=("Segoe UI", 9),
                                 bg=self.colors["bg_panel"],
                                 fg=self.colors["text_muted"])
        self.nav_info.pack(side=tk.RIGHT, padx=15)

    # ------------------------------------------------------------------
    # Step navigation
    # ------------------------------------------------------------------

    def _on_step_click(self, idx: int):
        """User clicked a step in the stepper bar."""
        if idx <= self.current_step or self.step_states[STEP_DEFINITIONS[idx]["key"]] == "completed":
            self._show_step(idx)

    def _go_prev(self):
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _go_next(self):
        # Mark current as completed
        key = STEP_DEFINITIONS[self.current_step]["key"]
        self.step_states[key] = "completed"
        if self.current_step < len(STEP_DEFINITIONS) - 1:
            self._show_step(self.current_step + 1)

    def _show_step(self, idx: int):
        self.current_step = idx
        key = STEP_DEFINITIONS[idx]["key"]

        # Mark current step in-progress
        if self.step_states[key] == "not-started":
            self.step_states[key] = "in-progress"

        # Update stepper UI
        self._update_stepper()

        # Hide all step panels
        for child in self.content_frame.winfo_children():
            child.pack_forget()

        # Build panel if not yet created
        if key not in self.step_panels:
            panel = self._build_step_panel(key)
            self.step_panels[key] = panel
        else:
            # Refresh panel if it has a refresh method
            panel = self.step_panels[key]
            if hasattr(panel, "refresh"):
                panel.refresh(self.dataset_ctx)

        self.step_panels[key].pack(fill=tk.BOTH, expand=True)

        # Update nav buttons
        self.btn_prev.config(state="normal" if idx > 0 else "disabled")
        step_def = STEP_DEFINITIONS[idx]
        if idx == len(STEP_DEFINITIONS) - 1:
            self.btn_next.config(text="✅ Finish")
        else:
            self.btn_next.config(text="Next ▶")

        # Disable Next on ingestion step until data is loaded
        if key == "ingestion" and self.step_states[key] != "completed":
            has_data = bool(getattr(S, 'list_of_files', None))
            self.btn_next.config(state="normal" if has_data else "disabled")
        else:
            self.btn_next.config(state="normal")
        self.nav_info.config(
            text=f"Step {idx + 1} of {len(STEP_DEFINITIONS)}:  {step_def['icon']}  {step_def['title']}"
        )

    def _update_stepper(self):
        for i, (frame, circle, lbl) in enumerate(self.step_labels):
            key = STEP_DEFINITIONS[i]["key"]
            state = self.step_states[key]
            if i == self.current_step:
                circle.config(bg=self.colors["accent"], fg="white")
                lbl.config(fg=self.colors["text_light"], font=("Segoe UI", 9, "bold"))
            elif state == "completed":
                circle.config(bg="#4caf50", fg="white")
                lbl.config(fg=self.colors["text_light"], font=("Segoe UI", 9))
            else:
                circle.config(bg=self.colors["border"], fg=self.colors["text_muted"])
                lbl.config(fg=self.colors["text_muted"], font=("Segoe UI", 9))

        for j, conn in enumerate(self.step_connectors):
            key = STEP_DEFINITIONS[j]["key"]
            if self.step_states[key] == "completed":
                conn.config(bg="#4caf50")
            else:
                conn.config(bg=self.colors["border"])

    def _build_step_panel(self, key: str) -> tk.Frame:
        """Lazy-build a step panel."""
        if key == "ingestion":
            from workflow.step_ingestion import IngestionPanel
            return IngestionPanel(self.content_frame, self.colors, self.dataset_ctx, self._notify_dataset_loaded)
        elif key == "annotation":
            from workflow.step_annotation import AnnotationPanel
            return AnnotationPanel(self.content_frame, self.colors, self.dataset_ctx)
        elif key == "analysis":
            from workflow.step_analysis import AnalysisPanel
            return AnalysisPanel(self.content_frame, self.colors, self.dataset_ctx)
        elif key == "splitting":
            from workflow.step_splitting import SplittingPanel
            return SplittingPanel(self.content_frame, self.colors, self.dataset_ctx)
        elif key == "recommendation":
            from workflow.step_recommendation import RecommendationPanel
            return RecommendationPanel(self.content_frame, self.colors, self.dataset_ctx)
        elif key == "collaboration":
            from workflow.step_collaboration import CollaborationPanel
            return CollaborationPanel(self.content_frame, self.colors, self.dataset_ctx)
        else:
            placeholder = tk.Frame(self.content_frame, bg=self.colors["bg_dark"])
            tk.Label(placeholder, text=f"Step: {key}", font=("Segoe UI", 14)).pack(expand=True)
            return placeholder

    # ------------------------------------------------------------------
    # Callbacks & helpers
    # ------------------------------------------------------------------

    def _notify_dataset_loaded(self):
        """Called by ingestion panel when dataset is loaded/configured."""
        # Auto-advance to step 2 (Annotation) after ingestion
        self.step_states["ingestion"] = "completed"
        self._show_step(1)

    def _close(self):
        self.hide()
        if self.on_close_callback:
            self.on_close_callback()

    def show(self):
        self.container.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        self.container.pack_forget()

    def get_dataset_context(self) -> Dict[str, Any]:
        return self.dataset_ctx

"""
Home Panel Module
Provides a dashboard for navigating between annotation folders and viewing corpus statistics.
Includes charts for data distribution visualization.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, Callable
import threading

# Import corpus analyzer
from corpus_stats import CorpusAnalyzer, get_annotation_paths, format_stats_summary

# Try to import matplotlib for charts
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib not available. Charts will be text-based.")


class HomePanel:
    """Home panel with folder navigation and corpus statistics dashboard."""
    
    def __init__(self, parent: tk.Widget, colors: Dict[str, str], on_close_callback: Callable = None):
        self.parent = parent
        self.colors = colors
        self.on_close_callback = on_close_callback
        
        self.analyzer = CorpusAnalyzer()
        self.current_stats = None
        self.current_folder = None
        
        # Main container
        self.container = tk.Frame(parent, bg=colors['bg_dark'])
        
        # Build UI
        self._build_header()
        self._build_main_content()
        
    def _build_header(self):
        """Build the header section with title and close button."""
        header = tk.Frame(self.container, bg=self.colors['bg_section'], pady=10, padx=15)
        header.pack(fill=tk.X)
        
        # Title
        title_frame = tk.Frame(header, bg=self.colors['bg_section'])
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(title_frame, text="🏠 Home Dashboard", 
                 font=('Segoe UI', 16, 'bold'),
                 bg=self.colors['bg_section'], fg=self.colors['text_light']).pack(side=tk.LEFT)
        
        tk.Label(title_frame, text="  |  Corpus Statistics & Analysis", 
                 font=('Segoe UI', 11),
                 bg=self.colors['bg_section'], fg=self.colors['text_muted']).pack(side=tk.LEFT, padx=10)
        
        # Close button
        close_btn = tk.Button(header, text="✖ Close", 
                              command=self._close_panel,
                              bg=self.colors['bg_section'], fg=self.colors['text_light'],
                              font=('Segoe UI', 10), relief=tk.FLAT, padx=10, cursor='hand2')
        close_btn.pack(side=tk.RIGHT)
        
    def _build_main_content(self):
        """Build the main content area with folder list and stats panel."""
        main_frame = tk.Frame(self.container, bg=self.colors['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Folder Navigation (fixed width)
        left_panel = tk.Frame(main_frame, bg=self.colors['bg_section'], width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        self._build_folder_list(left_panel)
        
        # Right panel - Statistics Dashboard (expandable)
        right_panel = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self._build_stats_panel(right_panel)
        
    def _build_folder_list(self, parent):
        """Build the folder navigation list."""
        # Section header
        header = tk.Label(parent, text="📁 Annotation Folders",
                          font=('Segoe UI', 12, 'bold'),
                          bg=self.colors['bg_section'], fg=self.colors['text_light'],
                          anchor='w', padx=10, pady=10)
        header.pack(fill=tk.X)
        
        # Separator
        tk.Frame(parent, height=1, bg=self.colors['border']).pack(fill=tk.X, padx=10)
        
        # Scrollable folder list
        list_frame = tk.Frame(parent, bg=self.colors['bg_section'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Get annotation paths
        paths = get_annotation_paths()
        
        if not paths:
            tk.Label(list_frame, text="No annotation folders found.\n\nCreate annotations using:\n• GAN Generator\n• Image Folder Load",
                     font=('Segoe UI', 10), bg=self.colors['bg_section'], 
                     fg=self.colors['text_muted'], justify=tk.LEFT).pack(padx=10, pady=20)
        else:
            for path_info in paths:
                self._create_folder_item(list_frame, path_info)
        
        # Separator
        tk.Frame(parent, height=1, bg=self.colors['border']).pack(fill=tk.X, padx=10, pady=5)
        
        # Add custom folder button
        btn_frame = tk.Frame(parent, bg=self.colors['bg_section'], pady=10)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="➕ Add Custom Folder",
                  command=self._browse_custom_folder,
                  bg=self.colors['accent'], fg='white',
                  font=('Segoe UI', 10, 'bold'),
                  relief=tk.FLAT, padx=15, pady=6, cursor='hand2').pack(padx=10)
        
        # Quick stats summary
        self.quick_stats_label = tk.Label(parent, text="Select a folder to view statistics",
                                          font=('Segoe UI', 9),
                                          bg=self.colors['bg_section'], fg=self.colors['text_muted'],
                                          anchor='w', wraplength=250, justify=tk.LEFT)
        self.quick_stats_label.pack(fill=tk.X, padx=10, pady=10)
        
    def _create_folder_item(self, parent, path_info: Dict):
        """Create a clickable folder item."""
        item_frame = tk.Frame(parent, bg=self.colors['bg_section'], cursor='hand2')
        item_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # Icon and name
        icon_label = tk.Label(item_frame, text=path_info.get('icon', '📁'),
                              font=('Segoe UI', 14), bg=self.colors['bg_section'])
        icon_label.pack(side=tk.LEFT, padx=(5, 8))
        
        text_frame = tk.Frame(item_frame, bg=self.colors['bg_section'])
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        name_label = tk.Label(text_frame, text=path_info.get('name', 'Unknown'),
                              font=('Segoe UI', 10, 'bold'),
                              bg=self.colors['bg_section'], fg=self.colors['text_light'],
                              anchor='w')
        name_label.pack(fill=tk.X)
        
        desc_label = tk.Label(text_frame, text=path_info.get('description', ''),
                              font=('Segoe UI', 8),
                              bg=self.colors['bg_section'], fg=self.colors['text_muted'],
                              anchor='w')
        desc_label.pack(fill=tk.X)
        
        # Hover effects
        def on_enter(e):
            item_frame.config(bg=self.colors['secondary_bg'])
            icon_label.config(bg=self.colors['secondary_bg'])
            text_frame.config(bg=self.colors['secondary_bg'])
            name_label.config(bg=self.colors['secondary_bg'])
            desc_label.config(bg=self.colors['secondary_bg'])
            
        def on_leave(e):
            item_frame.config(bg=self.colors['bg_section'])
            icon_label.config(bg=self.colors['bg_section'])
            text_frame.config(bg=self.colors['bg_section'])
            name_label.config(bg=self.colors['bg_section'])
            desc_label.config(bg=self.colors['bg_section'])
        
        def on_click(e):
            self._select_folder(path_info['path'])
        
        for widget in [item_frame, icon_label, text_frame, name_label, desc_label]:
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
            widget.bind('<Button-1>', on_click)
            
    def _build_stats_panel(self, parent):
        """Build the statistics dashboard panel."""
        # Create notebook for tabbed view
        self.stats_notebook = ttk.Notebook(parent)
        self.stats_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Overview
        self.overview_tab = tk.Frame(self.stats_notebook, bg=self.colors['bg_dark'])
        self.stats_notebook.add(self.overview_tab, text="📊 Overview")
        self._build_overview_tab()
        
        # Tab 2: Preview (Annotation Browser)
        self.preview_tab = tk.Frame(self.stats_notebook, bg=self.colors['bg_dark'])
        self.stats_notebook.add(self.preview_tab, text="👁️ Preview")
        self._build_preview_tab()
        
        # Tab 3: Character Analysis
        self.char_tab = tk.Frame(self.stats_notebook, bg=self.colors['bg_dark'])
        self.stats_notebook.add(self.char_tab, text="🔤 Characters")
        self._build_char_tab()
        
        # Tab 4: N-grams & Sequences
        self.ngram_tab = tk.Frame(self.stats_notebook, bg=self.colors['bg_dark'])
        self.stats_notebook.add(self.ngram_tab, text="📈 N-grams")
        self._build_ngram_tab()
        
        # Tab 5: Word Dictionary
        self.word_tab = tk.Frame(self.stats_notebook, bg=self.colors['bg_dark'])
        self.stats_notebook.add(self.word_tab, text="📖 Dictionary")
        self._build_word_tab()
        
        # Tab 6: Data Splitting Suggestions
        self.split_tab = tk.Frame(self.stats_notebook, bg=self.colors['bg_dark'])
        self.stats_notebook.add(self.split_tab, text="✂️ Data Split")
        self._build_split_tab()
        
        # Tab 7: Recommended Architectures
        self.arch_tab = tk.Frame(self.stats_notebook, bg=self.colors['bg_dark'])
        self.stats_notebook.add(self.arch_tab, text="🏗️ Architectures")
        self._build_architecture_tab()
    
    def _build_preview_tab(self):
        """Build the annotation preview tab with image display and navigation."""
        # Initialize preview data
        self.preview_annotations = []
        self.preview_images = {}  # Map annotation index to image path
        self.preview_current_index = 0
        
        # Main container with two panels
        preview_main = tk.Frame(self.preview_tab, bg=self.colors['bg_dark'])
        preview_main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Annotation list
        left_frame = tk.Frame(preview_main, bg=self.colors['bg_section'], width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        # List header
        list_header = tk.Frame(left_frame, bg=self.colors['bg_section'])
        list_header.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(list_header, text="📋 Annotations",
                 font=('Segoe UI', 11, 'bold'),
                 bg=self.colors['bg_section'], fg=self.colors['text_light']).pack(side=tk.LEFT)
        
        self.preview_count_label = tk.Label(list_header, text="(0 items)",
                                            font=('Segoe UI', 9),
                                            bg=self.colors['bg_section'], fg=self.colors['text_muted'])
        self.preview_count_label.pack(side=tk.RIGHT)
        
        # Search box
        search_frame = tk.Frame(left_frame, bg=self.colors['bg_section'])
        search_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        tk.Label(search_frame, text="🔍",
                 font=('Segoe UI', 10), bg=self.colors['bg_section']).pack(side=tk.LEFT)
        
        self.preview_search_var = tk.StringVar()
        self.preview_search_var.trace('w', self._filter_preview_list)
        search_entry = tk.Entry(search_frame, textvariable=self.preview_search_var,
                               font=('Segoe UI', 10), width=25)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Annotation listbox with scrollbar
        list_container = tk.Frame(left_frame, bg=self.colors['bg_section'])
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        list_scroll = tk.Scrollbar(list_container)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.preview_listbox = tk.Listbox(list_container, font=('Segoe UI', 10),
                                          bg='white', fg=self.colors['text_light'],
                                          selectbackground=self.colors['accent'],
                                          selectforeground='white',
                                          yscrollcommand=list_scroll.set)
        self.preview_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.preview_listbox.yview)
        
        self.preview_listbox.bind('<<ListboxSelect>>', self._on_preview_select)
        
        # Right panel - Image preview and details
        right_frame = tk.Frame(preview_main, bg=self.colors['bg_section'])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Navigation bar
        nav_frame = tk.Frame(right_frame, bg=self.colors['bg_section'])
        nav_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.preview_prev_btn = tk.Button(nav_frame, text="◀ Previous",
                                          command=self._preview_prev,
                                          bg=self.colors['accent'], fg='white',
                                          font=('Segoe UI', 10, 'bold'),
                                          relief=tk.FLAT, padx=15, pady=5, cursor='hand2')
        self.preview_prev_btn.pack(side=tk.LEFT)
        
        self.preview_index_label = tk.Label(nav_frame, text="0 / 0",
                                            font=('Segoe UI', 11, 'bold'),
                                            bg=self.colors['bg_section'], fg=self.colors['text_light'])
        self.preview_index_label.pack(side=tk.LEFT, expand=True)
        
        self.preview_next_btn = tk.Button(nav_frame, text="Next ▶",
                                          command=self._preview_next,
                                          bg=self.colors['accent'], fg='white',
                                          font=('Segoe UI', 10, 'bold'),
                                          relief=tk.FLAT, padx=15, pady=5, cursor='hand2')
        self.preview_next_btn.pack(side=tk.RIGHT)
        
        # Image display area
        image_frame = tk.LabelFrame(right_frame, text=" 🖼️ Image Preview ",
                                    font=('Segoe UI', 10, 'bold'),
                                    bg=self.colors['bg_section'], fg=self.colors['text_light'])
        image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        
        self.preview_canvas = tk.Canvas(image_frame, bg='#f0f0f0',
                                        highlightthickness=1,
                                        highlightbackground=self.colors['border'])
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Placeholder text
        self.preview_canvas.create_text(250, 150, 
                                        text="Select an annotation to preview image",
                                        fill=self.colors['text_muted'],
                                        font=('Segoe UI', 12))
        
        # Annotation details
        details_frame = tk.LabelFrame(right_frame, text=" 📝 Annotation Details ",
                                      font=('Segoe UI', 10, 'bold'),
                                      bg=self.colors['bg_section'], fg=self.colors['text_light'])
        details_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.preview_details_text = tk.Text(details_frame, font=('Segoe UI', 10),
                                            bg='white', fg=self.colors['text_light'],
                                            height=4, wrap=tk.WORD)
        self.preview_details_text.pack(fill=tk.X, padx=5, pady=5)
        self.preview_details_text.insert('1.0', "No annotation selected")
        self.preview_details_text.config(state='disabled')
        
        # Store image reference to prevent garbage collection
        self.preview_photo = None
        
    def _load_preview_annotations(self):
        """Load annotations for preview from current folder."""
        self.preview_annotations = []
        self.preview_images = {}
        
        if not self.current_folder:
            return
        
        import glob
        import json
        
        # Try to load IAM-style annotations (annotation.txt)
        ann_file = os.path.join(self.current_folder, "annotation.txt")
        if os.path.exists(ann_file):
            try:
                with open(ann_file, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split()
                        if len(parts) >= 8:
                            img_id = parts[0]
                            status = parts[1]
                            writer = parts[2]
                            x, y, w, h = parts[3:7]
                            grayed = parts[7]
                            text = ' '.join(parts[8:]) if len(parts) > 8 else ""
                            
                            self.preview_annotations.append({
                                'index': i,
                                'image_id': img_id,
                                'status': status,
                                'writer': writer,
                                'bbox': f"{x},{y},{w},{h}",
                                'text': text,
                                'raw': line
                            })
                            
                            # Try to find corresponding image
                            for ext in ['.png', '.jpg', '.jpeg']:
                                img_path = os.path.join(self.current_folder, 'batch', f"{img_id}{ext}")
                                if os.path.exists(img_path):
                                    self.preview_images[i] = img_path
                                    break
                                # Also try out_data folder
                                img_path = os.path.join(self.current_folder, 'out_data', f"{img_id}{ext}")
                                if os.path.exists(img_path):
                                    self.preview_images[i] = img_path
                                    break
            except Exception as e:
                print(f"Error loading annotations: {e}")
        
        # Try to load COCO-style JSON annotations
        json_files = glob.glob(os.path.join(self.current_folder, "*.json"))
        for jf in json_files:
            try:
                with open(jf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and 'annotations' in data:
                    # Build image map
                    img_map = {}
                    for img in data.get('images', []):
                        img_map[img['id']] = img.get('file_name', '')
                    
                    # Build category map
                    cat_map = {}
                    for cat in data.get('categories', []):
                        cat_map[cat['id']] = cat.get('name', '')
                    
                    for i, ann in enumerate(data['annotations']):
                        img_id = ann.get('image_id', 0)
                        cat_id = ann.get('category_id', 0)
                        bbox = ann.get('bbox', [0, 0, 0, 0])
                        
                        self.preview_annotations.append({
                            'index': len(self.preview_annotations),
                            'image_id': img_id,
                            'category': cat_map.get(cat_id, '?'),
                            'bbox': f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
                            'text': cat_map.get(cat_id, ''),
                            'raw': str(ann)
                        })
                        
                        # Find image path
                        img_name = img_map.get(img_id, '')
                        if img_name:
                            img_path = os.path.join(self.current_folder, img_name)
                            if os.path.exists(img_path):
                                self.preview_images[len(self.preview_annotations) - 1] = img_path
                            else:
                                # Try parent folder
                                img_path = os.path.join(os.path.dirname(self.current_folder), img_name)
                                if os.path.exists(img_path):
                                    self.preview_images[len(self.preview_annotations) - 1] = img_path
            except Exception as e:
                print(f"Error loading JSON: {e}")
        
        # Update listbox
        self._refresh_preview_listbox()
        
    def _refresh_preview_listbox(self):
        """Refresh the annotation listbox."""
        self.preview_listbox.delete(0, tk.END)
        
        filter_text = self.preview_search_var.get().lower() if hasattr(self, 'preview_search_var') else ""
        
        for ann in self.preview_annotations:
            text = ann.get('text', '')
            display = f"{ann['index']+1}. {text[:40]}{'...' if len(text) > 40 else ''}"
            
            if not filter_text or filter_text in text.lower() or filter_text in str(ann.get('image_id', '')).lower():
                self.preview_listbox.insert(tk.END, display)
        
        # Update count
        total = len(self.preview_annotations)
        filtered = self.preview_listbox.size()
        if filter_text:
            self.preview_count_label.config(text=f"({filtered}/{total} items)")
        else:
            self.preview_count_label.config(text=f"({total} items)")
            
    def _filter_preview_list(self, *args):
        """Filter preview list based on search."""
        self._refresh_preview_listbox()
        
    def _on_preview_select(self, event):
        """Handle selection in preview listbox."""
        selection = self.preview_listbox.curselection()
        if not selection:
            return
        
        # Get actual index from display
        display_text = self.preview_listbox.get(selection[0])
        try:
            idx = int(display_text.split('.')[0]) - 1
            self.preview_current_index = idx
            self._show_preview(idx)
        except (ValueError, IndexError):
            pass
            
    def _preview_prev(self):
        """Show previous annotation."""
        if self.preview_annotations and self.preview_current_index > 0:
            self.preview_current_index -= 1
            self._show_preview(self.preview_current_index)
            # Update listbox selection
            self._select_listbox_item(self.preview_current_index)
            
    def _preview_next(self):
        """Show next annotation."""
        if self.preview_annotations and self.preview_current_index < len(self.preview_annotations) - 1:
            self.preview_current_index += 1
            self._show_preview(self.preview_current_index)
            # Update listbox selection
            self._select_listbox_item(self.preview_current_index)
            
    def _select_listbox_item(self, idx):
        """Select an item in listbox by annotation index."""
        # Find the item in listbox
        for i in range(self.preview_listbox.size()):
            display = self.preview_listbox.get(i)
            try:
                list_idx = int(display.split('.')[0]) - 1
                if list_idx == idx:
                    self.preview_listbox.selection_clear(0, tk.END)
                    self.preview_listbox.selection_set(i)
                    self.preview_listbox.see(i)
                    break
            except (ValueError, IndexError):
                pass
            
    def _show_preview(self, idx: int):
        """Show preview for annotation at given index."""
        if idx < 0 or idx >= len(self.preview_annotations):
            return
        
        ann = self.preview_annotations[idx]
        
        # Update index label
        self.preview_index_label.config(text=f"{idx + 1} / {len(self.preview_annotations)}")
        
        # Update details
        self.preview_details_text.config(state='normal')
        self.preview_details_text.delete('1.0', tk.END)
        
        details = f"📋 Index: {ann.get('index', idx) + 1}\n"
        details += f"🖼️ Image ID: {ann.get('image_id', 'N/A')}\n"
        details += f"📝 Text: {ann.get('text', 'N/A')}\n"
        details += f"📐 BBox: {ann.get('bbox', 'N/A')}"
        if 'writer' in ann:
            details += f"\n✍️ Writer: {ann.get('writer', 'N/A')}"
        if 'category' in ann:
            details += f"\n🏷️ Category: {ann.get('category', 'N/A')}"
        
        self.preview_details_text.insert('1.0', details)
        self.preview_details_text.config(state='disabled')
        
        # Show image
        self._show_preview_image(idx)
        
    def _show_preview_image(self, idx: int):
        """Display the image for given annotation index."""
        self.preview_canvas.delete('all')
        
        img_path = self.preview_images.get(idx)
        
        if not img_path or not os.path.exists(img_path):
            self.preview_canvas.create_text(
                self.preview_canvas.winfo_width() // 2 or 250,
                self.preview_canvas.winfo_height() // 2 or 150,
                text="Image not found",
                fill=self.colors['text_muted'],
                font=('Segoe UI', 12)
            )
            return
        
        try:
            from PIL import Image, ImageTk
            
            img = Image.open(img_path)
            
            # Get canvas size
            canvas_w = self.preview_canvas.winfo_width() or 500
            canvas_h = self.preview_canvas.winfo_height() or 300
            
            # Resize to fit
            img_w, img_h = img.size
            scale = min(canvas_w / img_w, canvas_h / img_h, 1.5)
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(img_resized)
            
            # Center on canvas
            x = (canvas_w - new_w) // 2
            y = (canvas_h - new_h) // 2
            
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_photo)
            
            # Draw bounding box if available
            ann = self.preview_annotations[idx]
            bbox_str = ann.get('bbox', '')
            if bbox_str:
                try:
                    parts = bbox_str.split(',')
                    if len(parts) == 4:
                        bx, by, bw, bh = map(float, parts)
                        # Scale bbox to display size
                        bx = x + bx * scale
                        by = y + by * scale
                        bw = bw * scale
                        bh = bh * scale
                        self.preview_canvas.create_rectangle(
                            bx, by, bx + bw, by + bh,
                            outline='red', width=2
                        )
                except (ValueError, TypeError):
                    pass
                    
        except Exception as e:
            self.preview_canvas.create_text(
                self.preview_canvas.winfo_width() // 2 or 250,
                self.preview_canvas.winfo_height() // 2 or 150,
                text=f"Error loading image:\n{str(e)}",
                fill='red',
                font=('Segoe UI', 10)
            )
        
    def _build_overview_tab(self):
        """Build the overview statistics tab."""
        # Placeholder until folder is selected
        self.overview_placeholder = tk.Label(self.overview_tab, 
                                             text="📊 Select an annotation folder to view statistics\n\n"
                                                  "Statistics include:\n"
                                                  "• Character frequency distribution\n"
                                                  "• Word vocabulary analysis\n"
                                                  "• Sequence length distribution\n"
                                                  "• N-gram patterns\n"
                                                  "• Handwriting style count",
                                             font=('Segoe UI', 12),
                                             bg=self.colors['bg_dark'], fg=self.colors['text_muted'],
                                             justify=tk.CENTER)
        self.overview_placeholder.pack(expand=True)
        
        # Stats display frame (hidden initially)
        self.overview_content = tk.Frame(self.overview_tab, bg=self.colors['bg_dark'])
        
    def _build_char_tab(self):
        """Build the character analysis tab."""
        # Top: Chart area
        self.char_chart_frame = tk.Frame(self.char_tab, bg=self.colors['bg_section'])
        self.char_chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Placeholder for chart
        self.char_chart_placeholder = tk.Label(self.char_chart_frame,
                                               text="Character frequency chart will appear here",
                                               font=('Segoe UI', 11),
                                               bg=self.colors['bg_section'], fg=self.colors['text_muted'])
        self.char_chart_placeholder.pack(expand=True, fill=tk.BOTH, pady=50)
        
        # Bottom: Character table
        self.char_table_frame = tk.Frame(self.char_tab, bg=self.colors['bg_section'], height=200)
        self.char_table_frame.pack(fill=tk.X, padx=5, pady=5)
        self.char_table_frame.pack_propagate(False)
        
        tk.Label(self.char_table_frame, text="📋 Character Details",
                 font=('Segoe UI', 10, 'bold'),
                 bg=self.colors['bg_section'], fg=self.colors['text_light']).pack(anchor='w', padx=10, pady=5)
        
        # Create treeview for character data
        columns = ('char', 'count', 'frequency', 'avg_position')
        self.char_tree = ttk.Treeview(self.char_table_frame, columns=columns, show='headings', height=6)
        
        self.char_tree.heading('char', text='Character')
        self.char_tree.heading('count', text='Count')
        self.char_tree.heading('frequency', text='Frequency %')
        self.char_tree.heading('avg_position', text='Avg Position')
        
        self.char_tree.column('char', width=80, anchor='center')
        self.char_tree.column('count', width=100, anchor='center')
        self.char_tree.column('frequency', width=100, anchor='center')
        self.char_tree.column('avg_position', width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(self.char_table_frame, orient=tk.VERTICAL, command=self.char_tree.yview)
        self.char_tree.configure(yscrollcommand=scrollbar.set)
        
        self.char_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
    def _build_ngram_tab(self):
        """Build the n-gram analysis tab."""
        # Split into bigram and trigram sections
        paned = tk.PanedWindow(self.ngram_tab, orient=tk.HORIZONTAL, bg=self.colors['bg_dark'])
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bigram frame
        bigram_frame = tk.LabelFrame(paned, text="📊 Bigrams (2-char sequences)",
                                     font=('Segoe UI', 10, 'bold'),
                                     bg=self.colors['bg_section'], fg=self.colors['text_light'])
        paned.add(bigram_frame, width=350)
        
        self.bigram_list = tk.Listbox(bigram_frame, font=('Segoe UI', 10),
                                      bg='white', fg=self.colors['text_light'],
                                      selectbackground=self.colors['accent'])
        self.bigram_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Trigram frame
        trigram_frame = tk.LabelFrame(paned, text="📊 Trigrams (3-char sequences)",
                                      font=('Segoe UI', 10, 'bold'),
                                      bg=self.colors['bg_section'], fg=self.colors['text_light'])
        paned.add(trigram_frame, width=350)
        
        self.trigram_list = tk.Listbox(trigram_frame, font=('Segoe UI', 10),
                                       bg='white', fg=self.colors['text_light'],
                                       selectbackground=self.colors['accent'])
        self.trigram_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sequence length distribution
        seq_frame = tk.LabelFrame(self.ngram_tab, text="📏 Sequence Length Distribution",
                                  font=('Segoe UI', 10, 'bold'),
                                  bg=self.colors['bg_section'], fg=self.colors['text_light'])
        seq_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.seq_chart_frame = tk.Frame(seq_frame, bg=self.colors['bg_section'], height=150)
        self.seq_chart_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.seq_stats_label = tk.Label(seq_frame, text="",
                                        font=('Segoe UI', 10),
                                        bg=self.colors['bg_section'], fg=self.colors['text_light'],
                                        justify=tk.LEFT)
        self.seq_stats_label.pack(anchor='w', padx=10, pady=5)
        
    def _build_word_tab(self):
        """Build the word dictionary tab."""
        # Top stats
        stats_frame = tk.Frame(self.word_tab, bg=self.colors['bg_section'])
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.word_stats_label = tk.Label(stats_frame, text="Word Statistics: Select a folder",
                                         font=('Segoe UI', 11),
                                         bg=self.colors['bg_section'], fg=self.colors['text_light'])
        self.word_stats_label.pack(padx=10, pady=10)
        
        # Word list with search
        search_frame = tk.Frame(self.word_tab, bg=self.colors['bg_dark'])
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(search_frame, text="🔍 Search:",
                 font=('Segoe UI', 10), bg=self.colors['bg_dark'], 
                 fg=self.colors['text_light']).pack(side=tk.LEFT, padx=5)
        
        self.word_search_var = tk.StringVar()
        self.word_search_var.trace('w', self._filter_words)
        search_entry = tk.Entry(search_frame, textvariable=self.word_search_var,
                               font=('Segoe UI', 10), width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Word list
        list_frame = tk.Frame(self.word_tab, bg=self.colors['bg_section'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ('word', 'count')
        self.word_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        self.word_tree.heading('word', text='Word')
        self.word_tree.heading('count', text='Count')
        
        self.word_tree.column('word', width=250)
        self.word_tree.column('count', width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.word_tree.yview)
        self.word_tree.configure(yscrollcommand=scrollbar.set)
        
        self.word_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store all words for filtering
        self.all_words = []
        
    def _build_split_tab(self):
        """Build the data splitting suggestions tab."""
        # Header
        header = tk.Label(self.split_tab, text="✂️ Data Splitting & Augmentation Suggestions",
                          font=('Segoe UI', 14, 'bold'),
                          bg=self.colors['bg_dark'], fg=self.colors['text_light'])
        header.pack(pady=15)
        
        # Content frame
        content = tk.Frame(self.split_tab, bg=self.colors['bg_section'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.split_text = tk.Text(content, font=('Segoe UI', 10),
                                  bg='white', fg=self.colors['text_light'],
                                  wrap=tk.WORD, height=20)
        self.split_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Default text
        default_split_text = """📊 Data Splitting Recommendations

Select an annotation folder to get personalized recommendations for:

1. Train/Validation/Test Split Ratios
   • Based on your corpus size and diversity

2. Stratification Strategies
   • Character coverage across splits
   • Writer/style distribution

3. Data Augmentation Suggestions
   • Underrepresented characters
   • Rare n-grams to synthesize

4. Quality Checks
   • Class imbalance detection
   • Outlier sequences

5. Export Options
   • Compatible with common HTR frameworks
   • Multiple format support
"""
        self.split_text.insert('1.0', default_split_text)
        self.split_text.config(state='disabled')
    
    def _build_architecture_tab(self):
        """Build the recommended architectures tab with papers and GitHub links."""
        import webbrowser
        self.webbrowser = webbrowser  # Store for later use
        
        # Define architecture recommendations by dataset type
        self.architectures = {
            'character_detection': [
                {
                    'name': 'YOLOv8 for Character Detection',
                    'description': 'State-of-the-art real-time object detector. Excellent for character-level detection with high speed and accuracy.',
                    'paper': 'https://arxiv.org/abs/2305.09972',
                    'paper_title': 'YOLOv8: A New State-of-the-Art in Real-Time Object Detection (Jocher et al., 2023)',
                    'github': 'https://github.com/ultralytics/ultralytics',
                    'dataset_types': ['Character detection', 'Real-time'],
                    'pros': ['Fast inference', 'Easy training', 'Pre-trained weights'],
                    'annotation_types': ['character'],
                },
                {
                    'name': 'Faster R-CNN',
                    'description': 'Two-stage detector with Region Proposal Network. High accuracy for character bounding box detection.',
                    'paper': 'https://arxiv.org/abs/1506.01497',
                    'paper_title': 'Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks (Ren et al., 2015)',
                    'github': 'https://github.com/facebookresearch/detectron2',
                    'dataset_types': ['Character detection', 'High accuracy'],
                    'pros': ['High precision', 'Well-established', 'Detectron2 support'],
                    'annotation_types': ['character'],
                },
                {
                    'name': 'FCOS (Fully Convolutional One-Stage)',
                    'description': 'Anchor-free detector that predicts bounding boxes at each spatial location. Good for dense character detection.',
                    'paper': 'https://arxiv.org/abs/1904.01355',
                    'paper_title': 'FCOS: Fully Convolutional One-Stage Object Detection (Tian et al., 2019)',
                    'github': 'https://github.com/tianzhi0549/FCOS',
                    'dataset_types': ['Character detection', 'Anchor-free'],
                    'pros': ['No anchor tuning', 'Dense prediction', 'Simple design'],
                    'annotation_types': ['character'],
                },
                {
                    'name': 'RetinaNet with Focal Loss',
                    'description': 'Single-stage detector addressing class imbalance with focal loss. Effective for character datasets with imbalanced classes.',
                    'paper': 'https://arxiv.org/abs/1708.02002',
                    'paper_title': 'Focal Loss for Dense Object Detection (Lin et al., 2017)',
                    'github': 'https://github.com/facebookresearch/detectron2',
                    'dataset_types': ['Character detection', 'Imbalanced data'],
                    'pros': ['Handles class imbalance', 'Single-stage', 'Good for rare characters'],
                    'annotation_types': ['character'],
                },
                {
                    'name': 'EfficientDet',
                    'description': 'Scalable and efficient object detector with compound scaling. Balance between speed and accuracy.',
                    'paper': 'https://arxiv.org/abs/1911.09070',
                    'paper_title': 'EfficientDet: Scalable and Efficient Object Detection (Tan et al., 2020)',
                    'github': 'https://github.com/google/automl/tree/master/efficientdet',
                    'dataset_types': ['Character detection', 'Efficient'],
                    'pros': ['Scalable', 'Resource-efficient', 'Multiple model sizes'],
                    'annotation_types': ['character'],
                },
                {
                    'name': 'DETR (Detection Transformer)',
                    'description': 'End-to-end transformer-based detector. No NMS needed, good for character recognition pipelines.',
                    'paper': 'https://arxiv.org/abs/2005.12872',
                    'paper_title': 'End-to-End Object Detection with Transformers (Carion et al., 2020)',
                    'github': 'https://github.com/facebookresearch/detr',
                    'dataset_types': ['Character detection', 'Transformer'],
                    'pros': ['End-to-end', 'No NMS', 'Set-based prediction'],
                    'annotation_types': ['character'],
                },
                {
                    'name': 'CenterNet',
                    'description': 'Anchor-free detector using keypoint estimation. Predicts center points of characters.',
                    'paper': 'https://arxiv.org/abs/1904.07850',
                    'paper_title': 'Objects as Points (Zhou et al., 2019)',
                    'github': 'https://github.com/xingyizhou/CenterNet',
                    'dataset_types': ['Character detection', 'Keypoint-based'],
                    'pros': ['Simple', 'Fast', 'No anchor boxes'],
                    'annotation_types': ['character'],
                },
                {
                    'name': 'SSD (Single Shot Detector)',
                    'description': 'Classic single-shot detector with multi-scale feature maps. Fast and suitable for character detection.',
                    'paper': 'https://arxiv.org/abs/1512.02325',
                    'paper_title': 'SSD: Single Shot MultiBox Detector (Liu et al., 2016)',
                    'github': 'https://github.com/weiliu89/caffe/tree/ssd',
                    'dataset_types': ['Character detection', 'Multi-scale'],
                    'pros': ['Real-time', 'Multi-scale detection', 'Well-documented'],
                    'annotation_types': ['character'],
                },
            ],
            'word_level': [
                {
                    'name': 'CRNN (CNN + RNN + CTC)',
                    'description': 'Classic architecture combining CNN feature extraction with bidirectional LSTM and CTC loss. Best for word-level recognition.',
                    'paper': 'https://arxiv.org/abs/1507.05717',
                    'paper_title': 'An End-to-End Trainable Neural Network for Image-based Sequence Recognition (Shi et al., 2015)',
                    'github': 'https://github.com/bgshih/crnn',
                    'dataset_types': ['Word-level', 'Short sequences'],
                    'pros': ['Fast training', 'Good baseline', 'Well-documented'],
                    'annotation_types': ['word', 'word/line'],
                },
                {
                    'name': 'Attention-based Seq2Seq',
                    'description': 'Encoder-decoder with attention mechanism. Better at handling variable-length outputs.',
                    'paper': 'https://arxiv.org/abs/1603.03101',
                    'paper_title': 'Recursive Recurrent Nets with Attention Modeling for OCR (Lee & Osindero, 2016)',
                    'github': 'https://github.com/emedvedev/attention-ocr',
                    'dataset_types': ['Word-level', 'Handwriting'],
                    'pros': ['Handles irregular text', 'Interpretable attention maps'],
                    'annotation_types': ['word', 'word/line'],
                },
                {
                    'name': 'STN + CRNN',
                    'description': 'Spatial Transformer Network for geometric correction before CRNN recognition.',
                    'paper': 'https://arxiv.org/abs/1603.03915',
                    'paper_title': 'Robust Scene Text Recognition with Automatic Rectification (Shi et al., 2016)',
                    'github': 'https://github.com/clovaai/deep-text-recognition-benchmark',
                    'dataset_types': ['Word-level', 'Scene text', 'Distorted text'],
                    'pros': ['Handles perspective distortion', 'Robust to rotation'],
                    'annotation_types': ['word', 'word/line'],
                },
            ],
            'line_level': [
                {
                    'name': 'TrOCR',
                    'description': 'Transformer-based OCR using pre-trained image and text transformers (ViT + GPT-2/RoBERTa).',
                    'paper': 'https://arxiv.org/abs/2109.10282',
                    'paper_title': 'TrOCR: Transformer-based Optical Character Recognition with Pre-trained Models (Li et al., 2021)',
                    'github': 'https://github.com/microsoft/unilm/tree/master/trocr',
                    'dataset_types': ['Line-level', 'Document OCR', 'Handwriting'],
                    'pros': ['State-of-the-art performance', 'Pre-trained models available', 'Handles long sequences'],
                    'annotation_types': ['line', 'word/line'],
                },
                {
                    'name': 'FLOR / PyLaia',
                    'description': 'Flexible line-level OCR with CRNN backbone. Widely used for historical documents.',
                    'paper': 'https://arxiv.org/abs/1604.01949',
                    'paper_title': 'Are Multidimensional Recurrent Layers Really Necessary for Handwritten Text Recognition? (Puigcerver, 2017)',
                    'github': 'https://github.com/jpuigcerver/PyLaia',
                    'dataset_types': ['Line-level', 'Historical documents', 'IAM dataset'],
                    'pros': ['Efficient', 'Good for historical HTR', 'Easy to train'],
                    'annotation_types': ['line', 'word/line'],
                },
                {
                    'name': 'Transformer HTR',
                    'description': 'Pure transformer architecture for handwritten text recognition.',
                    'paper': 'https://arxiv.org/abs/2003.12136',
                    'paper_title': 'Handwriting Recognition with Large Multidimensional LSTM Recurrent Neural Networks (Wick et al., 2021)',
                    'github': 'https://github.com/arthurflor23/handwritten-text-recognition',
                    'dataset_types': ['Line-level', 'Paragraph-level'],
                    'pros': ['Parallel training', 'Long-range dependencies'],
                    'annotation_types': ['line', 'word/line'],
                },
                {
                    'name': 'Start-Follow-Read',
                    'description': 'Neural network system for full page handwriting recognition without explicit segmentation.',
                    'paper': 'https://arxiv.org/abs/1812.07688',
                    'paper_title': 'Start, Follow, Read: End-to-End Full-Page Handwriting Recognition (Wigington et al., 2018)',
                    'github': 'https://github.com/cwig/start_follow_read',
                    'dataset_types': ['Full page', 'No segmentation needed'],
                    'pros': ['End-to-end', 'No line segmentation required'],
                    'annotation_types': ['line'],
                },
            ],
            'page_level': [
                {
                    'name': 'Donut (Document Understanding Transformer)',
                    'description': 'OCR-free document understanding model using image-to-text generation without OCR.',
                    'paper': 'https://arxiv.org/abs/2111.15664',
                    'paper_title': 'OCR-free Document Understanding Transformer (Kim et al., 2022)',
                    'github': 'https://github.com/clovaai/donut',
                    'dataset_types': ['Document-level', 'Structured documents', 'Forms'],
                    'pros': ['No OCR pipeline needed', 'Handles complex layouts'],
                    'annotation_types': ['line', 'word/line', 'unknown'],
                },
                {
                    'name': 'LayoutLMv3',
                    'description': 'Pre-trained multimodal model for document AI combining text, layout, and image.',
                    'paper': 'https://arxiv.org/abs/2204.08387',
                    'paper_title': 'LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking (Huang et al., 2022)',
                    'github': 'https://github.com/microsoft/unilm/tree/master/layoutlmv3',
                    'dataset_types': ['Document understanding', 'Form extraction', 'Table detection'],
                    'pros': ['Multi-modal', 'Pre-trained', 'Layout-aware'],
                    'annotation_types': ['line', 'word/line', 'unknown'],
                },
                {
                    'name': 'DTLR (Document Text Line Recognition)',
                    'description': 'Full-page document recognition with text line detection and recognition.',
                    'paper': 'https://arxiv.org/abs/2102.09484',
                    'paper_title': 'Rethinking Text Line Recognition Models (Diaz et al., 2021)',
                    'github': 'https://github.com/facebookresearch/DTLR',
                    'dataset_types': ['Full page', 'Multi-line'],
                    'pros': ['Joint detection and recognition', 'Handles full pages'],
                    'annotation_types': ['line', 'word/line'],
                },
            ],
            'segmentation': [
                {
                    'name': 'ARU-Net',
                    'description': 'Attention-based Residual U-Net for document layout analysis and text line segmentation.',
                    'paper': 'https://arxiv.org/abs/1802.03345',
                    'paper_title': 'ARU-Net: A Neural Pixel Labeler for Layout Analysis of Historical Documents (Gruning et al., 2018)',
                    'github': 'https://github.com/TobiasGruworking/ARU-Net',
                    'dataset_types': ['Layout analysis', 'Segmentation', 'Historical documents'],
                    'pros': ['Pixel-level segmentation', 'Handles complex layouts'],
                    'annotation_types': ['line', 'character', 'unknown'],
                },
                {
                    'name': 'dhSegment',
                    'description': 'Deep learning approach for historical document segmentation using encoder-decoder.',
                    'paper': 'https://arxiv.org/abs/1812.00490',
                    'paper_title': 'dhSegment: A Generic Deep-Learning Approach for Document Segmentation (Oliveira et al., 2018)',
                    'github': 'https://github.com/dhlab-epfl/dhSegment',
                    'dataset_types': ['Historical documents', 'Layout segmentation'],
                    'pros': ['Versatile', 'Easy to fine-tune', 'Pre-trained models'],
                    'annotation_types': ['line', 'character', 'unknown'],
                },
                {
                    'name': 'P2PaLA',
                    'description': 'Page to PAGE Layout Analysis. Neural network for document layout analysis.',
                    'paper': 'https://arxiv.org/abs/1808.10254',
                    'paper_title': 'P2PaLA: Page to PAGE Layout Analysis System (Quirós, 2018)',
                    'github': 'https://github.com/lquirosd/P2PaLA',
                    'dataset_types': ['Layout analysis', 'Text regions', 'Baselines'],
                    'pros': ['PAGE XML output', 'Baseline detection'],
                    'annotation_types': ['line', 'unknown'],
                },
            ],
            'synthetic_data': [
                {
                    'name': 'Handwriting Synthesis (Graves)',
                    'description': 'LSTM-based handwriting generation that can produce realistic synthetic samples.',
                    'paper': 'https://arxiv.org/abs/1308.0850',
                    'paper_title': 'Generating Sequences With Recurrent Neural Networks (Graves, 2013)',
                    'github': 'https://github.com/sjvasquez/handwriting-synthesis',
                    'dataset_types': ['Synthetic data', 'Data augmentation'],
                    'pros': ['Style transfer', 'Unlimited synthetic samples'],
                    'annotation_types': ['gan_generated', 'word', 'line'],
                },
                {
                    'name': 'GANwriting',
                    'description': 'GAN-based handwriting generation for style-conditioned text synthesis.',
                    'paper': 'https://arxiv.org/abs/2003.02567',
                    'paper_title': 'GANwriting: Content-Conditioned Generation of Styled Handwritten Word Images (Kang et al., 2020)',
                    'github': 'https://github.com/omni-us/research-GANwriting',
                    'dataset_types': ['Synthetic data', 'Style-conditioned'],
                    'pros': ['High-quality synthesis', 'Writer style control'],
                    'annotation_types': ['gan_generated', 'word'],
                },
                {
                    'name': 'ScrabbleGAN',
                    'description': 'Semi-supervised handwriting generation that learns from both labeled and unlabeled data.',
                    'paper': 'https://arxiv.org/abs/2003.10557',
                    'paper_title': 'ScrabbleGAN: Semi-Supervised Varying Length Handwritten Text Generation (Fogel et al., 2020)',
                    'github': 'https://github.com/AmmieQi/ScrabbleGAN',
                    'dataset_types': ['Synthetic data', 'Variable length'],
                    'pros': ['Semi-supervised', 'Variable length output'],
                    'annotation_types': ['gan_generated', 'word'],
                },
            ],
        }
        
        # Section display order with metadata
        self.section_metadata = {
            'character_detection': ('🔍 Character Detection (Object Detection)', 'Object detection models for character-level bounding box detection', ['character']),
            'word_level': ('📝 Word-Level Recognition', 'Best for recognizing individual words or short text segments', ['word', 'word/line']),
            'line_level': ('📄 Line-Level Recognition', 'For recognizing full text lines, most common for HTR', ['line', 'word/line']),
            'page_level': ('📰 Page/Document-Level', 'End-to-end document understanding without segmentation', ['line', 'word/line', 'unknown']),
            'segmentation': ('✂️ Layout & Segmentation', 'For text detection, line segmentation, and layout analysis', ['line', 'character', 'unknown']),
            'synthetic_data': ('🎨 Synthetic Data Generation', 'For creating synthetic training data and augmentation', ['gan_generated', 'word', 'line']),
        }
        
        # Main container for architecture content
        self.arch_content_frame = tk.Frame(self.arch_tab, bg=self.colors['bg_dark'])
        self.arch_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Build initial view (no dataset selected)
        self._refresh_architecture_display()
    
    def _refresh_architecture_display(self):
        """Refresh architecture display based on current annotation type."""
        # Clear existing content
        for widget in self.arch_content_frame.winfo_children():
            widget.destroy()
        
        # Get current annotation type
        current_type = None
        if self.current_stats:
            current_type = self.current_stats.get('annotation_type', 'unknown')
        
        # Main scrollable frame
        main_canvas = tk.Canvas(self.arch_content_frame, bg=self.colors['bg_dark'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.arch_content_frame, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=self.colors['bg_dark'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Header
        header_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_section'], pady=15)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(header_frame, text="🏗️ Recommended HTR/OCR Architectures from Literature",
                 font=('Segoe UI', 14, 'bold'),
                 bg=self.colors['bg_section'], fg=self.colors['text_light']).pack()
        
        # Show current dataset type if available
        if current_type and current_type != 'unknown':
            type_badge = tk.Label(header_frame, text=f"📊 Showing models for: {current_type.upper()} dataset",
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=self.colors['accent'], fg='white',
                                  padx=15, pady=5)
            type_badge.pack(pady=(10, 0))
            
            tk.Label(header_frame, text="Models filtered based on your loaded dataset type",
                     font=('Segoe UI', 9, 'italic'),
                     bg=self.colors['bg_section'], fg=self.colors['text_muted']).pack(pady=(5, 0))
        else:
            tk.Label(header_frame, text="Load a dataset in Overview tab to see relevant architectures",
                     font=('Segoe UI', 10),
                     bg=self.colors['bg_section'], fg=self.colors['text_muted']).pack(pady=(5, 0))
        
        # Determine which sections to show
        sections_to_show = []
        if current_type and current_type != 'unknown':
            # Filter sections based on annotation type
            for section_key, (title, desc, applicable_types) in self.section_metadata.items():
                if current_type in applicable_types:
                    sections_to_show.append((section_key, title, desc))
        else:
            # Show placeholder message
            placeholder_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_section'])
            placeholder_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=20)
            
            tk.Label(placeholder_frame, 
                     text="📋 No Dataset Loaded\n\n"
                          "To see recommended architectures:\n\n"
                          "1. Go to the Overview tab\n"
                          "2. Select an annotation folder\n"
                          "3. Return here to see models matching your dataset type\n\n"
                          "Supported dataset types:\n"
                          "• Character - Object detection models for character bounding boxes\n"
                          "• Word - Word-level recognition models\n"
                          "• Line - Line-level HTR models\n"
                          "• GAN Generated - Synthetic data models",
                     font=('Segoe UI', 11),
                     bg=self.colors['bg_section'], fg=self.colors['text_muted'],
                     justify=tk.CENTER, pady=30).pack(fill=tk.BOTH, expand=True)
        
        # Create filtered sections
        shown_count = 0
        for section_key, title, desc in sections_to_show:
            # Filter architectures within section by annotation type
            filtered_archs = [
                arch for arch in self.architectures.get(section_key, [])
                if current_type in arch.get('annotation_types', [])
            ]
            
            if filtered_archs:
                self._create_filtered_architecture_section(
                    scrollable_frame, section_key, title, desc, filtered_archs
                )
                shown_count += 1
        
        # Show count of models
        if shown_count > 0:
            total_models = sum(
                len([a for a in self.architectures.get(sk, []) if current_type in a.get('annotation_types', [])])
                for sk, _, _ in sections_to_show
            )
            
            count_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_section'])
            count_frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(count_frame, text=f"✅ Showing {total_models} recommended models in {shown_count} categories",
                     font=('Segoe UI', 10, 'bold'),
                     bg=self.colors['bg_section'], fg=self.colors['success']).pack(pady=5)
        
        # Footer with additional resources (always show)
        if current_type:
            footer_frame = tk.LabelFrame(scrollable_frame, text=" 📚 Additional Resources ",
                                         font=('Segoe UI', 10, 'bold'),
                                         bg=self.colors['bg_section'], fg=self.colors['text_light'])
            footer_frame.pack(fill=tk.X, padx=10, pady=10)
            
            resources = [
                ("HTR-United Catalog", "https://htr-united.github.io/", "Collection of HTR datasets and ground truth"),
                ("Awesome OCR GitHub", "https://github.com/kba/awesome-ocr", "Curated list of OCR resources"),
                ("READ-COOP Transkribus", "https://readcoop.eu/transkribus/", "Platform for HTR with pre-trained models"),
                ("IAM Handwriting Database", "https://fki.tic.heia-fr.ch/databases/iam-handwriting-database", "Standard benchmark dataset"),
            ]
            
            for res_name, res_url, res_desc in resources:
                res_frame = tk.Frame(footer_frame, bg=self.colors['bg_section'])
                res_frame.pack(fill=tk.X, padx=10, pady=3)
                
                link_label = tk.Label(res_frame, text=f"🔗 {res_name}",
                                      font=('Segoe UI', 10, 'underline'),
                                      bg=self.colors['bg_section'], fg=self.colors['accent'],
                                      cursor='hand2')
                link_label.pack(side=tk.LEFT)
                link_label.bind("<Button-1>", lambda e, url=res_url: self.webbrowser.open(url))
                
                tk.Label(res_frame, text=f" - {res_desc}",
                         font=('Segoe UI', 9),
                         bg=self.colors['bg_section'], fg=self.colors['text_muted']).pack(side=tk.LEFT)
        
        # Pack canvas and scrollbar
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_filtered_architecture_section(self, parent, section_key: str, title: str, description: str, architectures: list):
        """Create a section for filtered architecture category."""
        section_frame = tk.LabelFrame(parent, text=f" {title} ",
                                      font=('Segoe UI', 11, 'bold'),
                                      bg=self.colors['bg_section'], fg=self.colors['text_light'])
        section_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Section description
        tk.Label(section_frame, text=description,
                 font=('Segoe UI', 9, 'italic'),
                 bg=self.colors['bg_section'], fg=self.colors['text_muted']).pack(anchor='w', padx=10, pady=(5, 10))
        
        # Architecture cards
        for arch in architectures:
            self._create_architecture_card(section_frame, arch, self.webbrowser)
    
    def _create_architecture_section(self, parent, section_key: str, title: str, description: str, webbrowser):
        """Create a collapsible section for architecture category."""
        section_frame = tk.LabelFrame(parent, text=f" {title} ",
                                      font=('Segoe UI', 11, 'bold'),
                                      bg=self.colors['bg_section'], fg=self.colors['text_light'])
        section_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Section description
        tk.Label(section_frame, text=description,
                 font=('Segoe UI', 9, 'italic'),
                 bg=self.colors['bg_section'], fg=self.colors['text_muted']).pack(anchor='w', padx=10, pady=(5, 10))
        
        # Architecture cards
        for arch in self.architectures.get(section_key, []):
            self._create_architecture_card(section_frame, arch, webbrowser)
    
    def _create_architecture_card(self, parent, arch: dict, webbrowser):
        """Create a card for a single architecture."""
        card = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=1)
        card.pack(fill=tk.X, padx=10, pady=5)
        
        # Header with name
        header = tk.Frame(card, bg='white')
        header.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(header, text=f"🔬 {arch['name']}",
                 font=('Segoe UI', 11, 'bold'),
                 bg='white', fg=self.colors['text_light']).pack(side=tk.LEFT)
        
        # Dataset type badges
        badge_frame = tk.Frame(header, bg='white')
        badge_frame.pack(side=tk.RIGHT)
        for dtype in arch.get('dataset_types', []):
            badge = tk.Label(badge_frame, text=dtype,
                           font=('Segoe UI', 8),
                           bg=self.colors['accent'], fg='white',
                           padx=6, pady=2)
            badge.pack(side=tk.LEFT, padx=2)
        
        # Description
        tk.Label(card, text=arch['description'],
                 font=('Segoe UI', 10),
                 bg='white', fg=self.colors['text_light'],
                 wraplength=700, justify=tk.LEFT).pack(anchor='w', padx=10, pady=5)
        
        # Paper title
        tk.Label(card, text=f"📄 {arch['paper_title']}",
                 font=('Segoe UI', 9, 'italic'),
                 bg='white', fg=self.colors['text_muted'],
                 wraplength=700, justify=tk.LEFT).pack(anchor='w', padx=10)
        
        # Links frame
        links_frame = tk.Frame(card, bg='white')
        links_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # Paper link
        paper_link = tk.Label(links_frame, text="📖 Paper (arXiv)",
                              font=('Segoe UI', 10, 'underline'),
                              bg='white', fg='#2980b9', cursor='hand2')
        paper_link.pack(side=tk.LEFT, padx=(0, 15))
        paper_link.bind("<Button-1>", lambda e, url=arch['paper']: webbrowser.open(url))
        
        # GitHub link
        github_link = tk.Label(links_frame, text="💻 GitHub Repository",
                               font=('Segoe UI', 10, 'underline'),
                               bg='white', fg='#27ae60', cursor='hand2')
        github_link.pack(side=tk.LEFT, padx=(0, 15))
        github_link.bind("<Button-1>", lambda e, url=arch['github']: webbrowser.open(url))
        
        # Pros
        pros_text = " • ".join(arch.get('pros', []))
        if pros_text:
            tk.Label(links_frame, text=f"✅ {pros_text}",
                     font=('Segoe UI', 9),
                     bg='white', fg=self.colors['success']).pack(side=tk.RIGHT)
        
    def _select_folder(self, folder_path: str):
        """Handle folder selection and load statistics."""
        self.current_folder = folder_path
        self.quick_stats_label.config(text="⏳ Loading statistics...")
        
        # Run analysis in background thread
        def analyze():
            try:
                stats = self.analyzer.analyze_folder(folder_path)
                self.current_stats = stats
                # Update UI on main thread
                self.container.after(0, lambda: self._update_stats_display(stats))
            except Exception as e:
                self.container.after(0, lambda: self._show_error(str(e)))
        
        thread = threading.Thread(target=analyze)
        thread.start()
        
    def _update_stats_display(self, stats: Dict):
        """Update all statistics displays with new data."""
        if "error" in stats:
            self._show_error(stats["error"])
            return
        
        # Update quick stats
        quick_text = f"📊 {stats.get('annotation_type', 'Unknown').title()} Annotations\n"
        quick_text += f"📝 {stats.get('total_annotations', 0):,} samples\n"
        quick_text += f"🖼️ {stats.get('total_images', 0):,} images"
        self.quick_stats_label.config(text=quick_text)
        
        # Update overview tab
        self._update_overview(stats)
        
        # Update preview tab (load annotations for browsing)
        self._load_preview_annotations()
        
        # Update character tab
        self._update_char_analysis(stats)
        
        # Update n-gram tab
        self._update_ngram_analysis(stats)
        
        # Update word tab
        self._update_word_dict(stats)
        
        # Update split suggestions
        self._update_split_suggestions(stats)
        
        # Update architecture recommendations based on dataset type
        self._refresh_architecture_display()
        
    def _update_overview(self, stats: Dict):
        """Update the overview tab with statistics."""
        # Hide placeholder, show content
        self.overview_placeholder.pack_forget()
        self.overview_content.pack(fill=tk.BOTH, expand=True)
        
        # Clear previous content
        for widget in self.overview_content.winfo_children():
            widget.destroy()
        
        # Create stats cards
        cards_frame = tk.Frame(self.overview_content, bg=self.colors['bg_dark'])
        cards_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Row 1: Basic stats
        row1 = tk.Frame(cards_frame, bg=self.colors['bg_dark'])
        row1.pack(fill=tk.X, pady=5)
        
        self._create_stat_card(row1, "📋 Annotation Type", 
                              stats.get('annotation_type', 'Unknown').title(), 
                              self.colors['accent'])
        self._create_stat_card(row1, "📝 Total Samples", 
                              f"{stats.get('total_annotations', 0):,}", 
                              self.colors['success'])
        self._create_stat_card(row1, "🖼️ Images", 
                              f"{stats.get('total_images', 0):,}", 
                              self.colors['warning'])
        
        # Row 2: Character stats
        char_stats = stats.get('character_stats', {})
        row2 = tk.Frame(cards_frame, bg=self.colors['bg_dark'])
        row2.pack(fill=tk.X, pady=5)
        
        self._create_stat_card(row2, "🔤 Unique Characters", 
                              str(char_stats.get('unique_characters', 0)), 
                              '#9b59b6')
        self._create_stat_card(row2, "📖 Total Characters", 
                              f"{char_stats.get('total_characters', 0):,}", 
                              '#1abc9c')
        
        style_stats = stats.get('style_stats', {})
        self._create_stat_card(row2, "✍️ Handwriting Styles", 
                              str(style_stats.get('total_styles', 0)), 
                              '#e67e22')
        
        # Row 3: Sequence stats
        seq_stats = stats.get('sequence_stats', {})
        row3 = tk.Frame(cards_frame, bg=self.colors['bg_dark'])
        row3.pack(fill=tk.X, pady=5)
        
        self._create_stat_card(row3, "📏 Min Length", 
                              str(seq_stats.get('min_length', 0)), 
                              '#3498db')
        self._create_stat_card(row3, "📏 Max Length", 
                              str(seq_stats.get('max_length', 0)), 
                              '#e74c3c')
        self._create_stat_card(row3, "📊 Avg Length", 
                              f"{seq_stats.get('avg_length', 0):.1f}", 
                              '#2ecc71')
        
        # Word stats
        word_stats = stats.get('word_stats', {})
        row4 = tk.Frame(cards_frame, bg=self.colors['bg_dark'])
        row4.pack(fill=tk.X, pady=5)
        
        self._create_stat_card(row4, "📖 Vocabulary Size", 
                              f"{word_stats.get('unique_words', 0):,}", 
                              '#8e44ad')
        self._create_stat_card(row4, "📝 Total Words", 
                              f"{word_stats.get('total_words', 0):,}", 
                              '#16a085')
        
        ngram_stats = stats.get('ngram_stats', {})
        self._create_stat_card(row4, "🔢 Unique Bigrams", 
                              f"{ngram_stats.get('bigrams', {}).get('unique', 0):,}", 
                              '#d35400')
        
        # Alphabet display
        alphabet_frame = tk.LabelFrame(self.overview_content, text=" 🔤 Character Alphabet ",
                                       font=('Segoe UI', 10, 'bold'),
                                       bg=self.colors['bg_section'], fg=self.colors['text_light'])
        alphabet_frame.pack(fill=tk.X, padx=10, pady=10)
        
        alphabet = char_stats.get('alphabet', [])
        if alphabet:
            alphabet_text = ' '.join(alphabet[:100])
            if len(alphabet) > 100:
                alphabet_text += f" ... (+{len(alphabet) - 100} more)"
            tk.Label(alphabet_frame, text=alphabet_text,
                    font=('Segoe UI', 11), bg=self.colors['bg_section'], 
                    fg=self.colors['text_light'], wraplength=600).pack(padx=10, pady=10)
        
    def _create_stat_card(self, parent, title: str, value: str, color: str):
        """Create a statistics card widget."""
        card = tk.Frame(parent, bg=self.colors['bg_section'], relief=tk.RAISED, bd=1)
        card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=3)
        
        # Color bar
        tk.Frame(card, bg=color, width=4).pack(side=tk.LEFT, fill=tk.Y)
        
        content = tk.Frame(card, bg=self.colors['bg_section'])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=8)
        
        tk.Label(content, text=title, font=('Segoe UI', 9),
                bg=self.colors['bg_section'], fg=self.colors['text_muted']).pack(anchor='w')
        tk.Label(content, text=value, font=('Segoe UI', 16, 'bold'),
                bg=self.colors['bg_section'], fg=self.colors['text_light']).pack(anchor='w')
        
    def _update_char_analysis(self, stats: Dict):
        """Update character analysis tab."""
        char_stats = stats.get('character_stats', {})
        characters = char_stats.get('characters', [])
        
        # Update table
        self.char_tree.delete(*self.char_tree.get_children())
        for char_data in characters[:100]:  # Limit to top 100
            char = char_data['char']
            if char == ' ':
                char = '⎵ (space)'
            elif char == '\n':
                char = '↵ (newline)'
            elif char == '\t':
                char = '→ (tab)'
            
            self.char_tree.insert('', tk.END, values=(
                char,
                f"{char_data['count']:,}",
                f"{char_data['frequency']*100:.2f}%",
                f"{char_data['avg_position']:.1f}"
            ))
        
        # Update chart if matplotlib available
        if MATPLOTLIB_AVAILABLE and characters:
            self._draw_char_chart(characters[:30])
        else:
            self.char_chart_placeholder.config(
                text="Top characters by frequency:\n\n" + 
                "\n".join([f"{c['char']}: {c['count']:,}" for c in characters[:20]])
            )
            
    def _draw_char_chart(self, characters: list):
        """Draw character frequency bar chart."""
        # Clear previous chart
        for widget in self.char_chart_frame.winfo_children():
            widget.destroy()
        
        fig = Figure(figsize=(8, 4), dpi=100, facecolor=self.colors['bg_section'])
        ax = fig.add_subplot(111)
        
        chars = [c['char'] if c['char'] != ' ' else '⎵' for c in characters]
        counts = [c['count'] for c in characters]
        
        bars = ax.bar(range(len(chars)), counts, color=self.colors['accent'])
        ax.set_xticks(range(len(chars)))
        ax.set_xticklabels(chars, fontsize=9)
        ax.set_ylabel('Frequency')
        ax.set_title('Character Frequency Distribution', fontsize=11, fontweight='bold')
        ax.set_facecolor(self.colors['bg_section'])
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.char_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def _update_ngram_analysis(self, stats: Dict):
        """Update n-gram analysis tab."""
        ngram_stats = stats.get('ngram_stats', {})
        
        # Update bigrams
        self.bigram_list.delete(0, tk.END)
        bigrams = ngram_stats.get('bigrams', {}).get('top_30', {})
        for ngram, count in sorted(bigrams.items(), key=lambda x: -x[1]):
            display = ngram.replace(' ', '⎵')
            self.bigram_list.insert(tk.END, f"'{display}': {count:,}")
        
        # Update trigrams
        self.trigram_list.delete(0, tk.END)
        trigrams = ngram_stats.get('trigrams', {}).get('top_30', {})
        for ngram, count in sorted(trigrams.items(), key=lambda x: -x[1]):
            display = ngram.replace(' ', '⎵')
            self.trigram_list.insert(tk.END, f"'{display}': {count:,}")
        
        # Update sequence stats
        seq_stats = stats.get('sequence_stats', {})
        if seq_stats:
            percentiles = seq_stats.get('percentiles', {})
            seq_text = f"📊 Sequence Statistics:\n"
            seq_text += f"• Min: {seq_stats.get('min_length', 0)} | Max: {seq_stats.get('max_length', 0)}\n"
            seq_text += f"• Average: {seq_stats.get('avg_length', 0):.1f} | Median: {seq_stats.get('median_length', 0)}\n"
            seq_text += f"• 10th percentile: {percentiles.get('10th', 0)} | 90th: {percentiles.get('90th', 0)}"
            self.seq_stats_label.config(text=seq_text)
            
    def _update_word_dict(self, stats: Dict):
        """Update word dictionary tab."""
        word_stats = stats.get('word_stats', {})
        
        # Update stats label
        self.word_stats_label.config(
            text=f"📖 Vocabulary: {word_stats.get('unique_words', 0):,} unique words | "
                 f"📝 Total: {word_stats.get('total_words', 0):,} words"
        )
        
        # Store all words for filtering
        vocab = word_stats.get('vocabulary', [])
        self.all_words = [(w['word'], w['count']) for w in vocab]
        
        # Update table
        self._refresh_word_table()
        
    def _refresh_word_table(self):
        """Refresh word table with current filter."""
        self.word_tree.delete(*self.word_tree.get_children())
        
        filter_text = self.word_search_var.get().lower()
        
        for word, count in self.all_words:
            if not filter_text or filter_text in word.lower():
                self.word_tree.insert('', tk.END, values=(word, f"{count:,}"))
                
    def _filter_words(self, *args):
        """Filter word list based on search."""
        self._refresh_word_table()
        
    def _update_split_suggestions(self, stats: Dict):
        """Update data splitting suggestions."""
        self.split_text.config(state='normal')
        self.split_text.delete('1.0', tk.END)
        
        suggestions = self._generate_split_suggestions(stats)
        self.split_text.insert('1.0', suggestions)
        self.split_text.config(state='disabled')
        
    def _generate_split_suggestions(self, stats: Dict) -> str:
        """Generate personalized data splitting suggestions."""
        text = "📊 Data Splitting & Augmentation Recommendations\n"
        text += "=" * 50 + "\n\n"
        
        total = stats.get('total_annotations', 0)
        
        # Split recommendations
        text += "1️⃣ RECOMMENDED SPLIT RATIOS\n"
        text += "-" * 30 + "\n"
        
        if total < 100:
            text += "⚠️ Small dataset detected. Consider:\n"
            text += "   • Train: 60% | Val: 20% | Test: 20%\n"
            text += "   • Use k-fold cross-validation (k=5)\n"
            text += "   • Heavy data augmentation recommended\n\n"
        elif total < 1000:
            text += "📊 Medium dataset. Suggested split:\n"
            text += "   • Train: 70% | Val: 15% | Test: 15%\n"
            text += f"   • Train: ~{int(total*0.7):,} samples\n"
            text += f"   • Val: ~{int(total*0.15):,} samples\n"
            text += f"   • Test: ~{int(total*0.15):,} samples\n\n"
        else:
            text += "✅ Large dataset. Suggested split:\n"
            text += "   • Train: 80% | Val: 10% | Test: 10%\n"
            text += f"   • Train: ~{int(total*0.8):,} samples\n"
            text += f"   • Val: ~{int(total*0.1):,} samples\n"
            text += f"   • Test: ~{int(total*0.1):,} samples\n\n"
        
        # Character coverage
        char_stats = stats.get('character_stats', {})
        if char_stats:
            text += "2️⃣ CHARACTER COVERAGE ANALYSIS\n"
            text += "-" * 30 + "\n"
            
            unique_chars = char_stats.get('unique_characters', 0)
            characters = char_stats.get('characters', [])
            
            text += f"   • Total unique characters: {unique_chars}\n"
            
            # Find rare characters (less than 5 occurrences)
            rare_chars = [c for c in characters if c['count'] < 5]
            if rare_chars:
                text += f"   ⚠️ Rare characters (<5 samples): {len(rare_chars)}\n"
                text += f"      {', '.join([c['char'] for c in rare_chars[:10]])}\n"
                text += "   💡 Consider augmentation for these characters\n"
            
            # Check for class imbalance
            if characters:
                max_count = characters[0]['count']
                min_count = characters[-1]['count'] if len(characters) > 1 else max_count
                imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')
                
                if imbalance_ratio > 100:
                    text += f"   ⚠️ High class imbalance detected (ratio: {imbalance_ratio:.0f}:1)\n"
                    text += "   💡 Use weighted sampling or oversampling\n"
            text += "\n"
        
        # Style distribution
        style_stats = stats.get('style_stats', {})
        if style_stats and style_stats.get('total_styles', 0) > 0:
            text += "3️⃣ HANDWRITING STYLE DISTRIBUTION\n"
            text += "-" * 30 + "\n"
            text += f"   • Total styles/writers: {style_stats.get('total_styles', 0)}\n"
            text += "   💡 Ensure writer-independent split:\n"
            text += "      - Don't mix same writer across train/test\n"
            text += "      - Stratify by writer ID if possible\n\n"
        
        # Augmentation suggestions
        text += "4️⃣ DATA AUGMENTATION SUGGESTIONS\n"
        text += "-" * 30 + "\n"
        text += "   Recommended augmentations for HTR:\n"
        text += "   • Elastic distortion (simulate handwriting variation)\n"
        text += "   • Random rotation (±5°)\n"
        text += "   • Gaussian noise\n"
        text += "   • Brightness/contrast variation\n"
        text += "   • Horizontal stretch (±10%)\n"
        
        if total < 500:
            text += "\n   ⚠️ Small dataset - use aggressive augmentation:\n"
            text += "   • 5-10x augmentation multiplier\n"
            text += "   • Synthetic data generation (GAN)\n"
        
        text += "\n"
        
        # Sequence length considerations
        seq_stats = stats.get('sequence_stats', {})
        if seq_stats:
            text += "5️⃣ SEQUENCE LENGTH CONSIDERATIONS\n"
            text += "-" * 30 + "\n"
            max_len = seq_stats.get('max_length', 0)
            avg_len = seq_stats.get('avg_length', 0)
            
            text += f"   • Max sequence length: {max_len}\n"
            text += f"   • Average length: {avg_len:.1f}\n"
            
            if max_len > 100:
                text += "   💡 Consider chunking long sequences\n"
            
            text += f"   💡 Suggested model max_length: {min(max_len + 10, 256)}\n"
        
        return text
        
    def _browse_custom_folder(self):
        """Open file dialog to select custom annotation folder."""
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Select Annotation Folder")
        if folder:
            self._select_folder(folder)
            
    def _show_error(self, message: str):
        """Display error message."""
        self.quick_stats_label.config(text=f"❌ Error: {message}")
        messagebox.showerror("Error", message)
        
    def _close_panel(self):
        """Close the home panel."""
        if self.on_close_callback:
            self.on_close_callback()
        self.container.pack_forget()
        
    def show(self):
        """Show the home panel."""
        self.container.pack(fill=tk.BOTH, expand=True)
        
    def hide(self):
        """Hide the home panel."""
        self.container.pack_forget()


def create_home_button(parent, colors: Dict[str, str], command: callable) -> tk.Button:
    """Create a home button for the sidebar."""
    btn = tk.Button(parent, text="🏠 Home Dashboard",
                    command=command,
                    bg=colors['accent'], fg='white',
                    activebackground=colors['accent_hover'],
                    font=('Segoe UI', 10, 'bold'),
                    relief=tk.FLAT, cursor='hand2',
                    width=18, pady=8)
    
    def on_enter(e):
        btn['bg'] = colors['accent_hover']
    def on_leave(e):
        btn['bg'] = colors['accent']
    
    btn.bind('<Enter>', on_enter)
    btn.bind('<Leave>', on_leave)
    
    return btn
